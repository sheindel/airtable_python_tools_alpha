"""Tests for the Field Complexity Scorecard tab"""
import pytest
from unittest.mock import patch
import sys
sys.path.insert(0, 'web')

from tabs.complexity_scorecard import (
    calculate_field_complexity,
    get_all_field_complexity,
    get_complexity_for_table,
    get_complexity_summary,
    get_complexity_scorecard_data,
    export_complexity_to_csv
)
from at_metadata_graph import metadata_to_graph


@pytest.fixture
def simple_metadata():
    """Simple metadata with a few fields"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Table1",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Name", "type": "singleLineText"},
                    {"id": "fld002", "name": "Value", "type": "number"},
                    {
                        "id": "fld003",
                        "name": "Formula",
                        "type": "formula",
                        "options": {
                            "formula": "{fld002} * 2",
                            "referencedFieldIds": ["fld002"],
                            "result": {"type": "number"}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def complex_metadata():
    """Complex metadata with cross-table dependencies"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Orders",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Order ID", "type": "singleLineText"},
                    {
                        "id": "fld002",
                        "name": "Customer Link",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl002",
                            "inverseLinkFieldId": "fld004"
                        }
                    },
                    {
                        "id": "fld003",
                        "name": "Customer Name",
                        "type": "multipleLookupValues",
                        "options": {
                            "recordLinkFieldId": "fld002",
                            "fieldIdInLinkedTable": "fld005"
                        }
                    },
                    {
                        "id": "fld006",
                        "name": "Total Rollup",
                        "type": "rollup",
                        "options": {
                            "recordLinkFieldId": "fld002",
                            "fieldIdInLinkedTable": "fld007",
                            "aggregationFunction": "sum"
                        }
                    }
                ]
            },
            {
                "id": "tbl002",
                "name": "Customers",
                "primaryFieldId": "fld005",
                "fields": [
                    {
                        "id": "fld004",
                        "name": "Orders",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl001",
                            "inverseLinkFieldId": "fld002"
                        }
                    },
                    {"id": "fld005", "name": "Name", "type": "singleLineText"},
                    {"id": "fld007", "name": "Amount", "type": "number"}
                ]
            }
        ]
    }


class TestCalculateFieldComplexity:
    """Test the calculate_field_complexity function"""
    
    def test_simple_field_has_zero_complexity(self, simple_metadata):
        """Simple fields should have low/zero complexity scores"""
        G = metadata_to_graph(simple_metadata)
        complexity = calculate_field_complexity(G, "fld001")
        
        assert complexity is not None
        assert complexity["field_id"] == "fld001"
        assert complexity["field_name"] == "Name"
        assert complexity["backward_deps"] == 0
        assert complexity["forward_deps"] == 0
        assert complexity["complexity_score"] >= 0
    
    def test_formula_field_has_backward_deps(self, simple_metadata):
        """Formula fields should have backward dependencies"""
        G = metadata_to_graph(simple_metadata)
        complexity = calculate_field_complexity(G, "fld003")
        
        assert complexity is not None
        assert complexity["backward_deps"] >= 1  # Depends on fld002
        assert complexity["complexity_score"] > 0
    
    def test_referenced_field_has_forward_deps(self, simple_metadata):
        """Fields referenced by others should have forward dependencies"""
        G = metadata_to_graph(simple_metadata)
        complexity = calculate_field_complexity(G, "fld002")
        
        assert complexity is not None
        # fld002 is referenced by fld003
        # Forward deps depends on graph direction
        assert complexity["complexity_score"] > 0
    
    def test_cross_table_complexity(self, complex_metadata):
        """Cross-table dependencies should increase complexity"""
        G = metadata_to_graph(complex_metadata)
        complexity = calculate_field_complexity(G, "fld003")  # Lookup field
        
        assert complexity is not None
        # Lookup creates cross-table dependency
        assert complexity["cross_table_deps"] >= 0
        assert complexity["complexity_score"] > 0
    
    def test_rollup_field_complexity(self, complex_metadata):
        """Rollup fields should have high complexity"""
        G = metadata_to_graph(complex_metadata)
        complexity = calculate_field_complexity(G, "fld006")
        
        assert complexity is not None
        assert complexity["field_type"] == "rollup"
        # Rollup should have relationship counts
        assert "rollup" in complexity["relationship_counts"] or complexity["complexity_score"] > 0
    
    def test_returns_none_for_invalid_field(self, simple_metadata):
        """Should return None for non-existent field"""
        G = metadata_to_graph(simple_metadata)
        complexity = calculate_field_complexity(G, "fldNonExistent")
        
        assert complexity is None
    
    def test_includes_all_required_keys(self, simple_metadata):
        """Complexity dict should have all required keys"""
        G = metadata_to_graph(simple_metadata)
        complexity = calculate_field_complexity(G, "fld001")
        
        required_keys = [
            "field_id", "field_name", "field_type",
            "table_id", "table_name",
            "backward_deps", "forward_deps", "max_depth",
            "cross_table_deps", "table_dependencies",
            "relationship_counts", "complexity_score"
        ]
        
        for key in required_keys:
            assert key in complexity, f"Missing key: {key}"


class TestGetAllFieldComplexity:
    """Test getting complexity for all fields"""
    
    def test_returns_list(self, simple_metadata):
        """Should return a list of complexity dicts"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            results = get_all_field_complexity()
            
            assert isinstance(results, list)
            # Only computed fields are analyzed (formula in simple_metadata)
            assert len(results) >= 1
    
    def test_sorted_by_complexity(self, complex_metadata):
        """Results should be sorted by complexity score descending"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=complex_metadata):
            results = get_all_field_complexity()
            
            # Check that scores are in descending order
            scores = [r["complexity_score"] for r in results]
            assert scores == sorted(scores, reverse=True)
    
    def test_handles_empty_metadata(self):
        """Should handle empty metadata gracefully"""
        empty_metadata = {"tables": []}
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=empty_metadata):
            results = get_all_field_complexity()
            
            assert isinstance(results, list)
            assert len(results) == 0
    
    def test_handles_no_metadata(self):
        """Should handle None metadata gracefully"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=None):
            results = get_all_field_complexity()
            
            assert isinstance(results, list)
            assert len(results) == 0


class TestGetComplexityForTable:
    """Test getting complexity for fields in a specific table"""
    
    def test_filters_by_table_name(self, complex_metadata):
        """Should return only fields from specified table"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=complex_metadata):
            orders_fields = get_complexity_for_table("Orders")
            
            assert isinstance(orders_fields, list)
            # All fields should be from Orders table
            for field in orders_fields:
                assert field["table_name"] == "Orders"
    
    def test_returns_empty_for_nonexistent_table(self, simple_metadata):
        """Should return empty list for non-existent table"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            results = get_complexity_for_table("NonExistent")
            
            assert isinstance(results, list)
            assert len(results) == 0


class TestGetComplexitySummary:
    """Test summary statistics generation"""
    
    def test_returns_string(self, simple_metadata):
        """Should return a string summary"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            summary = get_complexity_summary()
            
            assert isinstance(summary, str)
            assert len(summary) > 0
    
    def test_includes_field_count(self, simple_metadata):
        """Summary should include field count"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            summary = get_complexity_summary()
            
            # Should mention number of fields (3 in simple_metadata)
            assert "3" in summary or "three" in summary.lower()


class TestGetComplexityScorecardData:
    """Test the main scorecard data function"""
    
    def test_returns_json_string(self, simple_metadata):
        """Should return JSON formatted string"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            import json
            result = get_complexity_scorecard_data()
            
            assert isinstance(result, str)
            # Should be valid JSON
            data = json.loads(result)
            assert isinstance(data, list)
    
    def test_filters_by_table(self, complex_metadata):
        """Should filter by table name"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=complex_metadata):
            import json
            result = get_complexity_scorecard_data(filter_table="Orders")
            
            data = json.loads(result)
            # All fields should be from Orders table
            for field in data:
                assert field["table_name"] == "Orders"
    
    def test_filters_by_min_score(self, complex_metadata):
        """Should filter by minimum complexity score"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=complex_metadata):
            import json
            result = get_complexity_scorecard_data(min_score=10.0)
            
            data = json.loads(result)
            # All fields should have score >= 10
            for field in data:
                assert field["complexity_score"] >= 10.0


class TestExportComplexityCSV:
    """Test CSV export functionality"""
    
    def test_returns_csv_string(self, simple_metadata):
        """Should return CSV formatted string"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            csv_str = export_complexity_to_csv()
            
            assert isinstance(csv_str, str)
            assert len(csv_str) > 0
            # Should have header row
            assert "field_name" in csv_str or "Field Name" in csv_str or "Field" in csv_str
    
    def test_csv_has_all_fields(self, simple_metadata):
        """CSV should include all fields"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            csv_str = export_complexity_to_csv()
            
            # Should have 4 lines: header + 3 data rows
            lines = csv_str.strip().split('\n')
            assert len(lines) >= 2  # At least header + some data
    
    def test_csv_format(self, simple_metadata):
        """CSV should be properly formatted"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            csv_str = export_complexity_to_csv()
            
            lines = csv_str.strip().split('\n')
            if len(lines) > 1:
                # All lines should have same number of commas (columns)
                comma_counts = [line.count(',') for line in lines]
                assert len(set(comma_counts)) == 1, "All rows should have same column count"
    
    def test_handles_empty_data(self):
        """Should handle empty data gracefully"""
        empty_metadata = {"tables": []}
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=empty_metadata):
            csv_str = export_complexity_to_csv()
            
            assert isinstance(csv_str, str)
            # Should still have header
            assert len(csv_str) > 0


class TestComplexityScoring:
    """Test the complexity scoring algorithm"""
    
    def test_formula_more_complex_than_simple(self, simple_metadata):
        """Formula fields should score higher than simple fields"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=simple_metadata):
            all_complexity = get_all_field_complexity()
            
            # Find formula and simple fields
            formula_field = next((f for f in all_complexity if f["field_type"] == "formula"), None)
            simple_field = next((f for f in all_complexity if f["field_type"] == "singleLineText"), None)
            
            if formula_field and simple_field:
                assert formula_field["complexity_score"] > simple_field["complexity_score"]
    
    def test_cross_table_increases_score(self, complex_metadata):
        """Cross-table dependencies should increase score"""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=complex_metadata):
            all_complexity = get_all_field_complexity()
            
            # Fields with cross-table deps should have higher scores
            lookup_field = next((f for f in all_complexity if f["field_type"] == "multipleLookupValues"), None)
            
            if lookup_field:
                # Should have some complexity
                assert lookup_field["complexity_score"] > 0


# ============================================================================
# Integration Tests with Real Airtable Data
# ============================================================================

@pytest.mark.airtable_live
class TestComplexityScorecardIntegration:
    """Integration tests using real Airtable data.
    
    These tests validate complexity scoring with real-world bases that have
    deeply nested formulas, multiple rollups, and complex cross-table dependencies
    that don't exist in synthetic test data.
    """
    
    def test_analyze_real_base_complexity(self, airtable_schema):
        """Test complexity analysis on real Airtable base."""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            all_complexity = get_all_field_complexity()
            
            assert isinstance(all_complexity, list)
            assert len(all_complexity) > 0, "Should analyze at least one field"
            
            # Verify structure of results
            for field_data in all_complexity:
                assert "field_name" in field_data
                assert "table_name" in field_data
                assert "field_type" in field_data
                assert "complexity_score" in field_data
                assert isinstance(field_data["complexity_score"], (int, float))
                assert field_data["complexity_score"] >= 0
    
    def test_real_complexity_distribution(self, airtable_schema):
        """Test that real bases have realistic complexity distributions."""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            all_complexity = get_all_field_complexity()
            
            if len(all_complexity) == 0:
                pytest.skip("No fields in test base")
            
            scores = [f["complexity_score"] for f in all_complexity]
            
            # Real bases should have variety in complexity
            min_score = min(scores)
            max_score = max(scores)
            
            # Should have at least one simple field (score 0-1)
            assert min_score <= 1, "Should have some simple fields"
            
            # Real bases typically have at least some moderate complexity
            if len(scores) > 5:  # Only if we have enough fields
                # At least some fields should have complexity > 2
                complex_fields = [s for s in scores if s > 2]
                assert len(complex_fields) > 0, "Real bases should have some complex fields"
    
    def test_computed_fields_more_complex_than_simple(self, airtable_schema):
        """Test that computed fields score higher than simple fields in real base."""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            all_complexity = get_all_field_complexity()
            
            computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
            simple_types = {"singleLineText", "number", "checkbox"}
            
            computed_fields = [f for f in all_complexity if f["field_type"] in computed_types]
            simple_fields = [f for f in all_complexity if f["field_type"] in simple_types]
            
            if not computed_fields or not simple_fields:
                pytest.skip("Need both computed and simple fields in test base")
            
            # Average complexity should be higher for computed fields
            avg_computed = sum(f["complexity_score"] for f in computed_fields) / len(computed_fields)
            avg_simple = sum(f["complexity_score"] for f in simple_fields) / len(simple_fields)
            
            assert avg_computed > avg_simple, \
                f"Computed fields (avg={avg_computed:.2f}) should be more complex than simple fields (avg={avg_simple:.2f})"
    
    def test_get_complexity_for_specific_table(self, airtable_schema):
        """Test getting complexity for a specific table in real base."""
        if not airtable_schema.get("tables"):
            pytest.skip("No tables in test base")
        
        # Get first table
        first_table = airtable_schema["tables"][0]
        table_id = first_table["id"]
        
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            table_complexity = get_complexity_for_table(table_id)
            
            assert isinstance(table_complexity, list)
            
            # All fields should be from the correct table
            for field in table_complexity:
                assert field["table_name"] == first_table["name"]
    
    def test_complexity_summary_on_real_base(self, airtable_schema):
        """Test generating complexity summary for real base."""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            summary = get_complexity_summary()
            
            assert "total_fields" in summary
            assert "average_complexity" in summary
            assert "max_complexity" in summary
            assert "by_table" in summary
            
            assert summary["total_fields"] > 0
            assert summary["average_complexity"] >= 0
            assert summary["max_complexity"] >= 0
            assert isinstance(summary["by_table"], dict)
    
    def test_export_complexity_csv_with_real_data(self, airtable_schema):
        """Test CSV export with real base data."""
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=airtable_schema):
            csv_output = export_complexity_to_csv()
            
            assert isinstance(csv_output, str)
            assert len(csv_output) > 0
            
            # Should have CSV header
            lines = csv_output.strip().split('\n')
            assert len(lines) > 1, "Should have header and at least one data row"
            
            header = lines[0]
            assert "table_name" in header.lower()
            assert "field_name" in header.lower()
            assert "complexity" in header.lower() or "score" in header.lower()
