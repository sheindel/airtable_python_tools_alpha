"""Tests for the Formula Evaluator tab"""
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, 'web')

from tabs.formula_evaluator import (
    _convert_field_references,
    get_formula_dependencies,
    convert_evaluator_formula_display
)


@pytest.fixture
def simple_metadata():
    """Simple metadata with formula field"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Table1",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Base", "type": "number"},
                    {"id": "fld002", "name": "Rate", "type": "number"},
                    {
                        "id": "fld003",
                        "name": "Total",
                        "type": "formula",
                        "options": {
                            "formula": "{fld001} * {fld002}",
                            "referencedFieldIds": ["fld001", "fld002"],
                            "result": {"type": "number"}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def nested_formula_metadata():
    """Metadata with nested formula dependencies"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Table1",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "A", "type": "number"},
                    {
                        "id": "fld002",
                        "name": "B",
                        "type": "formula",
                        "options": {
                            "formula": "{fld001} * 2",
                            "referencedFieldIds": ["fld001"],
                            "result": {"type": "number"}
                        }
                    },
                    {
                        "id": "fld003",
                        "name": "C",
                        "type": "formula",
                        "options": {
                            "formula": "{fld002} + 10",
                            "referencedFieldIds": ["fld002"],
                            "result": {"type": "number"}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def cross_table_metadata():
    """Metadata with cross-table dependencies"""
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
                        "name": "Customer",
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
                    {"id": "fld005", "name": "Name", "type": "singleLineText"}
                ]
            }
        ]
    }


class TestConvertFieldReferences:
    """Test field reference conversion"""
    
    def test_convert_to_field_names(self, simple_metadata):
        """Should convert field IDs to field names"""
        formula = "{fld001} * {fld002}"
        result = _convert_field_references(formula, simple_metadata, "field_names")
        
        assert "{Base}" in result
        assert "{Rate}" in result
        assert "fld001" not in result
        assert "fld002" not in result
    
    def test_keep_field_ids(self, simple_metadata):
        """Should keep field IDs when output_format is field_ids"""
        formula = "{fld001} * {fld002}"
        result = _convert_field_references(formula, simple_metadata, "field_ids")
        
        assert result == formula
        assert "fld001" in result
        assert "fld002" in result
    
    def test_handles_nonexistent_field(self, simple_metadata):
        """Should preserve reference if field not found"""
        formula = "{fldNonExistent}"
        result = _convert_field_references(formula, simple_metadata, "field_names")
        
        # Should keep the original reference
        assert "fldNonExistent" in result
    
    def test_multiple_references(self, simple_metadata):
        """Should convert all field references"""
        formula = "IF({fld001} > 0, {fld002}, 0)"
        result = _convert_field_references(formula, simple_metadata, "field_names")
        
        assert "{Base}" in result
        assert "{Rate}" in result
        assert "fld001" not in result
        assert "fld002" not in result
    
    def test_preserves_non_field_content(self, simple_metadata):
        """Should preserve operators and functions"""
        formula = "SUM({fld001}, {fld002})"
        result = _convert_field_references(formula, simple_metadata, "field_names")
        
        assert "SUM(" in result
        assert ")" in result
        assert "," in result


class TestGetFormulaDependencies:
    """Test dependency discovery"""
    
    def test_simple_formula_dependencies(self, simple_metadata):
        """Should find direct dependencies"""
        deps = get_formula_dependencies("fld003", simple_metadata)
        
        assert isinstance(deps, list)
        # Should have 2 leaf dependencies (fld001 and fld002)
        assert len(deps) >= 2
        
        # Check structure
        for dep in deps:
            assert "id" in dep
            assert "name" in dep
            assert "type" in dep
            assert "table_name" in dep
    
    def test_nested_formula_finds_root_dependencies(self, nested_formula_metadata):
        """Nested formula should find root dependencies, not intermediates"""
        deps = get_formula_dependencies("fld003", nested_formula_metadata)
        
        # Should find fld001 (the root), not fld002 (intermediate formula)
        dep_ids = [d["id"] for d in deps]
        assert "fld001" in dep_ids
        # Should not include fld002 since it's a formula
        assert "fld002" not in dep_ids
    
    def test_excludes_computed_fields(self, nested_formula_metadata):
        """Should only return leaf (non-computed) fields"""
        deps = get_formula_dependencies("fld003", nested_formula_metadata)
        
        # All dependencies should be non-computed types
        for dep in deps:
            assert dep["type"] not in ["formula", "rollup", "multipleLookupValues", "count"]
    
    def test_cross_table_lookup_dependencies(self, cross_table_metadata):
        """Should find dependencies across tables for lookups"""
        deps = get_formula_dependencies("fld003", cross_table_metadata)
        
        # Should find the underlying field (fld005 from Customers table)
        dep_ids = [d["id"] for d in deps]
        assert "fld005" in dep_ids
        
        # Check that table name is included
        for dep in deps:
            if dep["id"] == "fld005":
                assert dep["table_name"] == "Customers"
    
    def test_sorted_by_table_and_name(self, simple_metadata):
        """Dependencies should be sorted by table name, then field name"""
        deps = get_formula_dependencies("fld003", simple_metadata)
        
        # Should be sorted
        if len(deps) > 1:
            for i in range(len(deps) - 1):
                current = (deps[i]["table_name"], deps[i]["name"])
                next_dep = (deps[i + 1]["table_name"], deps[i + 1]["name"])
                assert current <= next_dep
    
    def test_empty_dependencies_for_leaf_field(self, simple_metadata):
        """Leaf field should have no dependencies"""
        deps = get_formula_dependencies("fld001", simple_metadata)
        
        # Number field has no dependencies
        assert len(deps) == 0
    
    def test_handles_nonexistent_field(self, simple_metadata):
        """Should raise error for non-existent field"""
        # The implementation doesn't check if field exists in graph
        # so it will raise NetworkXError
        from networkx.exception import NetworkXError
        
        with pytest.raises(NetworkXError):
            get_formula_dependencies("fldNonExistent", simple_metadata)


class TestConvertEvaluatorFormulaDisplay:
    """Test the formula display conversion function"""
    
    def test_converts_to_field_names(self, simple_metadata):
        """Should convert formula to use field names"""
        with patch('tabs.formula_evaluator.get_local_storage_metadata', return_value=simple_metadata):
            formula = "{fld001} * {fld002}"
            result = convert_evaluator_formula_display(formula, "field_names")
            
            assert "{Base}" in result
            assert "{Rate}" in result
    
    def test_keeps_field_ids(self, simple_metadata):
        """Should keep field IDs when requested"""
        with patch('tabs.formula_evaluator.get_local_storage_metadata', return_value=simple_metadata):
            formula = "{fld001} * {fld002}"
            result = convert_evaluator_formula_display(formula, "field_ids")
            
            assert "fld001" in result
            assert "fld002" in result
    
    def test_handles_no_metadata(self):
        """Should handle missing metadata gracefully"""
        with patch('tabs.formula_evaluator.get_local_storage_metadata', return_value=None):
            formula = "{fld001}"
            result = convert_evaluator_formula_display(formula, "field_names")
            
            # Should return original or empty, but not crash
            assert isinstance(result, str)


class TestDependencyChainResolution:
    """Test complex dependency chain resolution"""
    
    def test_transitive_dependencies(self):
        """Should resolve transitive dependencies"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {"id": "fld001", "name": "A", "type": "number"},
                        {
                            "id": "fld002",
                            "name": "B",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001}",
                                "referencedFieldIds": ["fld001"],
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld003",
                            "name": "C",
                            "type": "formula",
                            "options": {
                                "formula": "{fld002}",
                                "referencedFieldIds": ["fld002"],
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld004",
                            "name": "D",
                            "type": "formula",
                            "options": {
                                "formula": "{fld003}",
                                "referencedFieldIds": ["fld003"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        deps = get_formula_dependencies("fld004", metadata)
        
        # Should find fld001 (the root) through the chain
        dep_ids = [d["id"] for d in deps]
        assert "fld001" in dep_ids
        # Should not include intermediate formulas
        assert "fld002" not in dep_ids
        assert "fld003" not in dep_ids


class TestEdgeCases:
    """Test edge cases"""
    
    def test_self_referencing_formula(self):
        """Should handle self-referencing formula without infinite loop"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Circular",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001}",
                                "referencedFieldIds": ["fld001"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        # Should not crash
        deps = get_formula_dependencies("fld001", metadata)
        assert isinstance(deps, list)
    
    def test_empty_formula(self, simple_metadata):
        """Should handle formula with empty options"""
        formula = ""
        result = _convert_field_references(formula, simple_metadata, "field_names")
        assert result == ""
    
    def test_formula_with_no_field_references(self, simple_metadata):
        """Should handle formula with no field references"""
        formula = "5 * 10"
        result = _convert_field_references(formula, simple_metadata, "field_names")
        assert result == "5 * 10"
    
    def test_dependencies_with_empty_metadata(self):
        """Should raise error when field not in empty metadata"""
        from networkx.exception import NetworkXError
        
        empty_metadata = {"tables": []}
        
        # Field won't exist in graph, so will raise error
        with pytest.raises(NetworkXError):
            get_formula_dependencies("fld001", empty_metadata)
