"""Integration tests for formula evaluation parity with Airtable.

These tests verify that our locally generated evaluators produce identical
results to Airtable's computed field values. They require live Airtable API access.

Run with:
    export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
    export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
    uv run pytest tests/test_integration_parity.py --airtable-live -v
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from code_generators.incremental_runtime_generator import (
    generate_complete_module,
    GeneratorOptions,
)
from helpers.airtable_api import (
    get_random_record_id,
    fetch_record,
    extract_raw_fields,
    convert_record_to_snake_case,
    to_snake_case,
)


@pytest.mark.airtable_live
class TestFormulaParity:
    """Test that our evaluators produce identical results to Airtable."""
    
    def test_single_table_parity(self, airtable_metadata, airtable_base_id, airtable_api_key):
        """Test parity for a single table with computed fields."""
        # Find a table with computed fields
        computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
        test_table = None
        for table in airtable_metadata["tables"]:
            computed_count = sum(
                1 for field in table["fields"] if field["type"] in computed_types
            )
            if computed_count > 0:
                test_table = table
                break
        
        if not test_table:
            pytest.skip("No tables with computed fields found in schema")
        
        # Get a random record
        record_id = get_random_record_id(airtable_base_id, airtable_api_key, test_table["name"])
        full_record = fetch_record(airtable_base_id, airtable_api_key, test_table["name"], record_id)
        
        # Extract raw fields
        raw_fields = extract_raw_fields(full_record, airtable_metadata, test_table["id"])
        raw_fields_snake = convert_record_to_snake_case(raw_fields)
        
        # Generate evaluator
        options = GeneratorOptions(
            data_access_mode="dict",
            include_null_checks=True,
            include_type_hints=False,
            include_docstrings=False,
        )
        module_code = generate_complete_module(airtable_metadata, table_id=test_table["id"], options=options)
        
        # Execute evaluator
        namespace = {}
        exec(module_code, namespace)
        update_record = namespace.get("update_record")
        ComputationContext = namespace.get("ComputationContext")
        
        assert update_record is not None, "update_record function not found in generated code"
        assert ComputationContext is not None, "ComputationContext class not found in generated code"
        
        # Compute formulas locally
        local_record = {"id": record_id, **raw_fields_snake}
        context = ComputationContext(local_record, {})
        local_record = update_record(local_record, context)
        
        # Compare values for each computed field
        computed_fields = [
            field["name"] for field in test_table["fields"] 
            if field["type"] in computed_types
        ]
        
        mismatches = []
        for field_name in computed_fields:
            airtable_value = full_record["fields"].get(field_name)
            local_field_name = to_snake_case(field_name)
            local_value = local_record.get(local_field_name)
            
            if airtable_value != local_value:
                mismatches.append({
                    "field": field_name,
                    "airtable": airtable_value,
                    "local": local_value,
                })
        
        # Report results
        if mismatches:
            error_msg = f"\nParity check failed for table '{test_table['name']}' (record {record_id}):\n"
            for mismatch in mismatches:
                error_msg += f"  - {mismatch['field']}: "
                error_msg += f"expected={mismatch['airtable']}, got={mismatch['local']}\n"
            pytest.fail(error_msg)
    
    def test_contacts_table_parity(self, airtable_metadata, airtable_base_id, airtable_api_key):
        """Test parity specifically for Contacts table if it exists."""
        # Find Contacts table
        contacts_table = next(
            (t for t in airtable_metadata["tables"] if t["name"] == "Contacts"), 
            None
        )
        
        if not contacts_table:
            pytest.skip("Contacts table not found in schema")
        
        # Check if it has computed fields
        computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
        computed_fields = [
            f for f in contacts_table["fields"] if f["type"] in computed_types
        ]
        
        if not computed_fields:
            pytest.skip("Contacts table has no computed fields")
        
        # Get a random record
        record_id = get_random_record_id(airtable_base_id, airtable_api_key, "Contacts")
        full_record = fetch_record(airtable_base_id, airtable_api_key, "Contacts", record_id)
        
        # Extract and process
        raw_fields = extract_raw_fields(full_record, airtable_metadata, contacts_table["id"])
        raw_fields_snake = convert_record_to_snake_case(raw_fields)
        
        # Generate evaluator
        options = GeneratorOptions(
            data_access_mode="dict",
            include_null_checks=True,
        )
        module_code = generate_complete_module(airtable_metadata, table_id=contacts_table["id"], options=options)
        
        # Execute
        namespace = {}
        exec(module_code, namespace)
        update_record = namespace["update_record"]
        ComputationContext = namespace["ComputationContext"]
        
        local_record = {"id": record_id, **raw_fields_snake}
        context = ComputationContext(local_record, {})
        local_record = update_record(local_record, context)
        
        # Verify Name field specifically (common computed field)
        if any(f["name"] == "Name" for f in computed_fields):
            airtable_name = full_record["fields"].get("Name")
            local_name = local_record.get("name")
            
            assert local_name == airtable_name, (
                f"Name field mismatch: expected '{airtable_name}', got '{local_name}'"
            )
    
    def test_nested_formula_parity(self, airtable_metadata, airtable_base_id, airtable_api_key):
        """Test parity for tables with deeply nested formula dependencies."""
        computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
        
        # Find table with most computed fields (likely to have nesting)
        tables_by_computed = sorted(
            airtable_metadata["tables"],
            key=lambda t: sum(1 for f in t["fields"] if f["type"] in computed_types),
            reverse=True
        )
        
        if not tables_by_computed or sum(1 for f in tables_by_computed[0]["fields"] if f["type"] in computed_types) == 0:
            pytest.skip("No tables with computed fields found")
        
        test_table = tables_by_computed[0]
        
        # Get a record and test parity (similar to test_single_table_parity)
        record_id = get_random_record_id(airtable_base_id, airtable_api_key, test_table["name"])
        full_record = fetch_record(airtable_base_id, airtable_api_key, test_table["name"], record_id)
        
        raw_fields = extract_raw_fields(full_record, airtable_metadata, test_table["id"])
        raw_fields_snake = convert_record_to_snake_case(raw_fields)
        
        options = GeneratorOptions(data_access_mode="dict", include_null_checks=True)
        module_code = generate_complete_module(airtable_metadata, table_id=test_table["id"], options=options)
        
        namespace = {}
        exec(module_code, namespace)
        
        local_record = {"id": record_id, **raw_fields_snake}
        context = namespace["ComputationContext"](local_record, {})
        local_record = namespace["update_record"](local_record, context)
        
        # Check all computed fields
        computed_fields = [f for f in test_table["fields"] if f["type"] in computed_types]
        matches = 0
        for field in computed_fields:
            airtable_value = full_record["fields"].get(field["name"])
            local_value = local_record.get(to_snake_case(field["name"]))
            if airtable_value == local_value:
                matches += 1
        
        # Require at least 80% match rate for nested formulas
        match_rate = matches / len(computed_fields) if computed_fields else 0
        assert match_rate >= 0.8, (
            f"Only {matches}/{len(computed_fields)} fields matched ({match_rate:.1%}). "
            f"Expected at least 80% match rate for nested formulas."
        )


@pytest.mark.airtable_live
class TestEvaluatorStructure:
    """Test that generated evaluators have correct structure."""
    
    def test_generated_module_has_required_functions(self, airtable_metadata):
        """Verify generated module contains all required functions."""
        # Find any table
        if not airtable_metadata["tables"]:
            pytest.skip("No tables in schema")
        
        table = airtable_metadata["tables"][0]
        
        options = GeneratorOptions(data_access_mode="dict")
        module_code = generate_complete_module(airtable_metadata, table_id=table["id"], options=options)
        
        # Check for required components
        assert "def update_record" in module_code
        assert "class ComputationContext" in module_code
        assert "COMPUTATION_GRAPH" in module_code
        assert "LINKED_TABLE_MAP" in module_code
    
    def test_generated_code_is_valid_python(self, airtable_metadata):
        """Verify generated code compiles without syntax errors."""
        if not airtable_metadata["tables"]:
            pytest.skip("No tables in schema")
        
        table = airtable_metadata["tables"][0]
        
        options = GeneratorOptions(data_access_mode="dict")
        module_code = generate_complete_module(airtable_metadata, table_id=table["id"], options=options)
        
        # Should compile without errors
        try:
            compile(module_code, "<generated>", "exec")
        except SyntaxError as e:
            pytest.fail(f"Generated code has syntax error: {e}")
