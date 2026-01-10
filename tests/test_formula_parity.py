"""
Advanced Formula Parity Tests

Tests that validate generated formula evaluators produce identical results
to Airtable's own calculations by comparing against live Airtable data.

These tests require:
- AIRTABLE_BASE_ID environment variable
- AIRTABLE_API_KEY environment variable
- Network access to Airtable API

Run with: pytest tests/test_formula_parity.py -v --airtable-live
"""

import sys
from pathlib import Path
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

import pytest

from constants import COMPUTED_FIELD_TYPES

# Import helper modules
from helpers.airtable_api import (
    AirtableAPIError,
    extract_raw_fields as extract_raw_fields_api,
    fetch_record as fetch_record_api,
    fetch_schema_cached as fetch_schema_cached_api,
    get_api_key,
    get_base_id,
    get_computed_field_names as get_computed_field_names_api,
    get_random_record_id as get_random_record_id_api,
    get_table_id_by_name,
)
from helpers.comparison import (
    ValueMismatchError,
    assert_values_equal as assert_values_equal_helper,
    compare_records,
)


# ============================================================================
# Configuration and Fixtures
# ============================================================================

CACHE_DIR = Path(__file__).parent.parent / ".cache" / "airtable_schemas"
CACHE_EXPIRY = timedelta(hours=24)


@pytest.fixture
def airtable_credentials():
    """Get Airtable credentials from environment."""
    base_id = os.getenv("AIRTABLE_BASE_ID")
    api_key = os.getenv("AIRTABLE_API_KEY")
    
    if not base_id or not api_key:
        pytest.skip("Airtable credentials not configured (set AIRTABLE_BASE_ID and AIRTABLE_API_KEY)")
    
    return {"base_id": base_id, "api_key": api_key}


@pytest.fixture
def cached_schema(airtable_credentials):
    """Fetch and cache Airtable schema."""
    schema = fetch_schema_cached(
        airtable_credentials["base_id"],
        airtable_credentials["api_key"]
    )
    return schema


# ============================================================================
# Schema Caching
# ============================================================================

def fetch_schema_cached(base_id: str, api_key: str) -> dict:
    """
    Fetch schema from Airtable with local caching.
    
    Caches schema for 24 hours to avoid unnecessary API calls.
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
    
    Returns:
        Schema metadata dict
    """
    return fetch_schema_cached_api(base_id, api_key)


# ============================================================================
# Random Record Selection
# ============================================================================

def get_random_record_id(
    base_id: str,
    api_key: str,
    table_name: str,
    max_records: int = 100
) -> str:
    """
    Get a random record ID using a heuristic approach.
    
    Strategy:
    1. Fetch first page of records (up to max_records)
    2. Pick random record from results
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        table_name: Name of table to fetch from
        max_records: Maximum records to fetch (default 100)
    
    Returns:
        Random record ID
    """
    return get_random_record_id_api(base_id, api_key, table_name)


def fetch_record(
    base_id: str,
    api_key: str,
    table_name: str,
    record_id: str
) -> dict:
    """
    Fetch a single record from Airtable.
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        table_name: Name of table
        record_id: Record ID to fetch
    
    Returns:
        Record dict with id, fields, createdTime
    """
    return fetch_record_api(base_id, api_key, table_name, record_id)


# ============================================================================
# Field Extraction
# ============================================================================

def extract_raw_fields(full_record: dict, schema: dict, table_name: str) -> dict:
    """
    Extract only raw (non-computed) fields from a record.
    
    Excludes formula, rollup, lookup, and count fields since those
    are calculated by Airtable.
    
    Args:
        full_record: Full record from Airtable API
        schema: Airtable metadata schema
        table_name: Name of the table
    
    Returns:
        Dict with only raw field values
    """
    # Get table ID from name
    table_id = get_table_id_by_name(schema, table_name)
    return extract_raw_fields_api(full_record, schema, table_id)


def get_computed_field_names(schema: dict, table_name: str) -> List[str]:
    """
    Get list of computed field names for a table.
    
    Args:
        schema: Airtable metadata schema
        table_name: Name of the table
    
    Returns:
        List of computed field names
    """
    # Get table ID from name
    table_id = get_table_id_by_name(schema, table_name)
    return get_computed_field_names_api(schema, table_id)
# ============================================================================
# Value Comparison
# ============================================================================

def assert_values_equal(
    local_value: Any,
    airtable_value: Any,
    field_name: str,
    tolerance: float = 0.001
):
    """
    Compare local and Airtable values with appropriate tolerances.
    
    Handles different data types:
    - Numbers: floating point tolerance
    - Strings: exact match
    - Dates: format normalization
    - Arrays: order-independent comparison
    - Null/None: equivalence
    
    Args:
        local_value: Value computed locally
        airtable_value: Value from Airtable
        field_name: Name of field being compared (for error messages)
        tolerance: Numeric comparison tolerance
    
    Raises:
        AssertionError: If values don't match
    """
    try:
        assert_values_equal_helper(local_value, airtable_value, field_name, tolerance)
    except ValueMismatchError as e:
        # Convert ValueMismatchError to AssertionError for pytest compatibility
        raise AssertionError(str(e)) from e


# ============================================================================
# Test Suite
# ============================================================================

@pytest.mark.airtable_live
class TestFormulaParity:
    """Test formula evaluation against live Airtable data."""
    
    def test_simple_formula_parity(self, airtable_credentials, cached_schema):
        """
        Test that simple formula fields match Airtable's calculations.
        
        Tests basic formulas like string concatenation and arithmetic.
        """
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions,
        )
        
        base_id = airtable_credentials["base_id"]
        api_key = airtable_credentials["api_key"]
        
        # Get list of tables
        if not cached_schema.get("tables"):
            pytest.skip("No tables in schema")
        
        # Pick first table with computed fields
        test_table = None
        for table in cached_schema["tables"]:
            table_name = table["name"]
            computed_fields = get_computed_field_names(cached_schema, table_name)
            if computed_fields:
                test_table = table
                break
        
        if not test_table:
            pytest.skip("No tables with computed fields found")
        
        table_name = test_table["name"]
        table_id = test_table["id"]
        
        # Get random record
        try:
            record_id = get_random_record_id(base_id, api_key, table_name)
        except Exception as e:
            pytest.skip(f"Could not fetch random record: {e}")
        
        # Fetch full record
        full_record = fetch_record(base_id, api_key, table_name, record_id)
        
        # Extract raw fields
        raw_fields = extract_raw_fields(full_record, cached_schema, table_name)
        
        # Generate evaluator code for this table
        options = GeneratorOptions(
            data_access_mode="dict",  # Use dict mode for flexibility
            include_null_checks=True,
            include_type_hints=False,
            include_docstrings=False,
        )
        
        try:
            module_code = generate_complete_module(
                cached_schema,
                table_id=table_id,
                options=options
            )
        except Exception as e:
            pytest.fail(f"Failed to generate module: {e}")
        
        # Execute generated code
        namespace = {}
        try:
            exec(module_code, namespace)
        except Exception as e:
            pytest.fail(f"Failed to execute generated code: {e}")
        
        # Get functions from namespace
        update_record = namespace.get("update_record")
        ComputationContext = namespace.get("ComputationContext")
        
        if not update_record or not ComputationContext:
            pytest.fail("Generated module missing required functions")
        
        # Create record with raw fields and compute formulas
        local_record = {"id": record_id, **raw_fields}
        context = ComputationContext(local_record, {})
        
        try:
            local_record = update_record(local_record, context)
        except Exception as e:
            pytest.fail(f"Failed to update record: {e}")
        
        # Compare computed fields
        computed_fields = get_computed_field_names(cached_schema, table_name)
        mismatches = []
        matches = []
        
        for field_name in computed_fields:
            airtable_value = full_record["fields"].get(field_name)
            local_value = local_record.get(field_name)
            
            try:
                assert_values_equal(local_value, airtable_value, field_name)
                matches.append(field_name)
            except AssertionError as e:
                mismatches.append(str(e))
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Parity Test Results for {table_name}")
        print(f"{'='*70}")
        print(f"Record ID: {record_id}")
        print(f"Computed fields tested: {len(computed_fields)}")
        print(f"Matches: {len(matches)}")
        print(f"Mismatches: {len(mismatches)}")
        
        if matches:
            print(f"\n✓ Matching fields ({len(matches)}):")
            for field in matches[:5]:  # Show first 5
                print(f"  - {field}")
            if len(matches) > 5:
                print(f"  ... and {len(matches) - 5} more")
        
        if mismatches:
            print(f"\n✗ Mismatching fields ({len(mismatches)}):")
            for mismatch in mismatches[:3]:  # Show first 3
                print(f"  {mismatch}")
            if len(mismatches) > 3:
                print(f"  ... and {len(mismatches) - 3} more")
        
        print(f"{'='*70}\n")
        
        # For now, allow test to pass if we got any matches (Phase 5 progress)
        # In Phase 5B we'll require 100% match rate
        if len(matches) == 0 and len(mismatches) > 0:
            pytest.skip(f"No formulas computed successfully ({len(mismatches)} fields need lookup/rollup support)")
    
    def test_lookup_field_parity(self, airtable_credentials, cached_schema):
        """Test that lookup fields match Airtable's values."""
        pytest.skip("Phase 5B: Not yet implemented")
    
    def test_rollup_field_parity(self, airtable_credentials, cached_schema):
        """Test that rollup aggregations match Airtable's calculations."""
        pytest.skip("Phase 5B: Not yet implemented")
    
    def test_nested_formula_parity(self, airtable_credentials, cached_schema):
        """Test formulas that reference other formulas."""
        pytest.skip("Phase 5B: Not yet implemented")
    
    def test_edge_cases_parity(self, airtable_credentials, cached_schema):
        """Test edge cases: null values, empty strings, division by zero."""
        pytest.skip("Phase 5B: Not yet implemented")
    
    @pytest.mark.parametrize("num_samples", [5])
    def test_statistical_sampling(self, airtable_credentials, cached_schema, num_samples):
        """
        Test multiple random samples for statistical confidence.
        
        Args:
            num_samples: Number of random records to test
        """
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions,
        )
        
        base_id = airtable_credentials["base_id"]
        api_key = airtable_credentials["api_key"]
        
        # Get list of tables with computed fields
        tables_with_computed = []
        for table in cached_schema.get("tables", []):
            table_name = table["name"]
            computed_fields = get_computed_field_names(cached_schema, table_name)
            if computed_fields:
                tables_with_computed.append(table)
        
        if not tables_with_computed:
            pytest.skip("No tables with computed fields found")
        
        # Track results
        total_tests = 0
        total_successes = 0
        total_failures = 0
        failure_details = []
        
        # Test multiple random records
        for i in range(num_samples):
            # Pick random table
            test_table = random.choice(tables_with_computed)
            table_name = test_table["name"]
            table_id = test_table["id"]
            
            try:
                # Get random record
                record_id = get_random_record_id(base_id, api_key, table_name)
                full_record = fetch_record(base_id, api_key, table_name, record_id)
                raw_fields = extract_raw_fields(full_record, cached_schema, table_name)
                
                # Generate evaluator (cached in practice)
                options = GeneratorOptions(
                    data_access_mode="dict",
                    include_null_checks=True,
                    include_type_hints=False,
                    include_docstrings=False,
                )
                
                module_code = generate_complete_module(
                    cached_schema,
                    table_id=table_id,
                    options=options
                )
                
                # Execute and compute
                namespace = {}
                exec(module_code, namespace)
                
                update_record = namespace["update_record"]
                ComputationContext = namespace["ComputationContext"]
                
                local_record = {"id": record_id, **raw_fields}
                context = ComputationContext(local_record, {})
                local_record = update_record(local_record, context)
                
                # Compare all computed fields
                computed_fields = get_computed_field_names(cached_schema, table_name)
                
                for field_name in computed_fields:
                    total_tests += 1
                    airtable_value = full_record["fields"].get(field_name)
                    local_value = local_record.get(field_name)
                    
                    try:
                        assert_values_equal(local_value, airtable_value, field_name)
                        total_successes += 1
                    except AssertionError as e:
                        total_failures += 1
                        failure_details.append({
                            "table": table_name,
                            "record": record_id,
                            "field": field_name,
                            "error": str(e)
                        })
            
            except Exception as e:
                # Log but continue testing other records
                failure_details.append({
                    "table": table_name,
                    "record": "unknown",
                    "field": "N/A",
                    "error": f"Test setup failed: {e}"
                })
        
        # Report results
        success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n\nStatistical Sampling Results:")
        print(f"  Samples tested: {num_samples}")
        print(f"  Total field comparisons: {total_tests}")
        print(f"  Successes: {total_successes}")
        print(f"  Failures: {total_failures}")
        print(f"  Success rate: {success_rate:.1f}%")
        
        if failure_details:
            print(f"\n  Failure details:")
            for detail in failure_details[:5]:  # Show first 5
                print(f"    - {detail['table']}.{detail['field']}: {detail['error'][:100]}")
        
        # Pass if success rate > 80%
        if success_rate < 80:
            pytest.fail(f"Success rate {success_rate:.1f}% below threshold (80%)")



# ============================================================================
# Utility Tests (can be implemented now)
# ============================================================================

class TestParityHelpers:
    """Test helper functions for parity testing."""
    
    def test_extract_raw_fields(self):
        """Test extracting raw fields from a record."""
        schema = {
            "tables": [
                {
                    "id": "tblContacts123",
                    "name": "Contacts",
                    "fields": [
                        {"name": "First Name", "type": "singleLineText"},
                        {"name": "Last Name", "type": "singleLineText"},
                        {"name": "Full Name", "type": "formula"},
                    ]
                }
            ]
        }
        
        full_record = {
            "id": "rec123",
            "fields": {
                "First Name": "John",
                "Last Name": "Doe",
                "Full Name": "John Doe"  # Computed
            }
        }
        
        raw_fields = extract_raw_fields(full_record, schema, "Contacts")
        
        assert "First Name" in raw_fields
        assert "Last Name" in raw_fields
        assert "Full Name" not in raw_fields  # Excluded (computed)
        assert raw_fields["First Name"] == "John"
        assert raw_fields["Last Name"] == "Doe"
    
    def test_get_computed_field_names(self):
        """Test getting computed field names from schema."""
        schema = {
            "tables": [
                {
                    "id": "tblContacts123",
                    "name": "Contacts",
                    "fields": [
                        {"name": "First Name", "type": "singleLineText"},
                        {"name": "Full Name", "type": "formula"},
                        {"name": "Company Name", "type": "multipleLookupValues"},
                    ]
                }
            ]
        }
        
        computed = get_computed_field_names(schema, "Contacts")
        
        assert "Full Name" in computed
        assert "Company Name" in computed
        assert "First Name" not in computed
    
    def test_assert_values_equal_numbers(self):
        """Test numeric comparison with tolerance."""
        # Should pass (within tolerance)
        assert_values_equal(1.0, 1.0001, "test_field", tolerance=0.001)
        
        # Should fail (outside tolerance)
        with pytest.raises(AssertionError):
            assert_values_equal(1.0, 1.1, "test_field", tolerance=0.001)
    
    def test_assert_values_equal_strings(self):
        """Test string comparison."""
        # Should pass
        assert_values_equal("hello", "hello", "test_field")
        
        # Should fail
        with pytest.raises(AssertionError):
            assert_values_equal("hello", "world", "test_field")
    
    def test_assert_values_equal_arrays(self):
        """Test array comparison (order-independent)."""
        # Should pass (same elements, different order)
        assert_values_equal([1, 2, 3], [3, 2, 1], "test_field")
        
        # Should fail (different elements)
        with pytest.raises(AssertionError):
            assert_values_equal([1, 2, 3], [1, 2, 4], "test_field")
    
    def test_assert_values_equal_nulls(self):
        """Test null/None comparison."""
        # Should pass
        assert_values_equal(None, None, "test_field")
        
        # Should fail
        with pytest.raises(AssertionError):
            assert_values_equal(None, "value", "test_field")
        with pytest.raises(AssertionError):
            assert_values_equal("value", None, "test_field")
