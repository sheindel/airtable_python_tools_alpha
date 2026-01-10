"""Tests for formula compressor functionality"""
import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from tabs.formula_compressor import (
    compress_formula,
    _compress_formula_recursive,
    _convert_field_references,
    format_formula_compact,
    format_formula_logical,
)


@pytest.fixture
def sample_metadata_for_compression():
    """Create sample Airtable metadata for compression testing"""
    return {
        "tables": [
            {
                "id": "tblTestTable1",
                "name": "Test Table",
                "primaryFieldId": "fldPrimary0000001",
                "fields": [
                    {
                        "id": "fldFieldA0000001",
                        "name": "Field A",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "AND({fldFieldB0000002}, {fldFieldC0000003})",
                            "referencedFieldIds": ["fldFieldB0000002", "fldFieldC0000003"],
                            "result": {"type": "checkbox"}
                        }
                    },
                    {
                        "id": "fldFieldB0000002",
                        "name": "Field B",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fldFieldD0000004}+{fldFieldE0000005}",
                            "referencedFieldIds": ["fldFieldD0000004", "fldFieldE0000005"],
                            "result": {"type": "number"}
                        }
                    },
                    {
                        "id": "fldFieldC0000003",
                        "name": "Field C",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "OR({fldFieldD0000004}, NOT({fldFieldE0000005}))",
                            "referencedFieldIds": ["fldFieldD0000004", "fldFieldE0000005"],
                            "result": {"type": "checkbox"}
                        }
                    },
                    {
                        "id": "fldFieldD0000004",
                        "name": "Field D",
                        "type": "number",
                        "options": {"precision": 0}
                    },
                    {
                        "id": "fldFieldE0000005",
                        "name": "Field E",
                        "type": "checkbox",
                        "options": {"icon": "check", "color": "green"}
                    }
                ]
            }
        ]
    }


@pytest.fixture
def circular_reference_metadata():
    """Metadata with circular field references"""
    return {
        "tables": [
            {
                "id": "tblCircular001",
                "name": "Circular Table",
                "primaryFieldId": "fldPrimary0000001",
                "fields": [
                    {
                        "id": "fldFieldX0000001",
                        "name": "Field X",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fldFieldY0000002} + 1",
                            "referencedFieldIds": ["fldFieldY0000002"],
                            "result": {"type": "number"}
                        }
                    },
                    {
                        "id": "fldFieldY0000002",
                        "name": "Field Y",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fldFieldX0000001} * 2",
                            "referencedFieldIds": ["fldFieldX0000001"],
                            "result": {"type": "number"}
                        }
                    }
                ]
            }
        ]
    }


class TestFormulaCompressionDepth:
    """Test formula compression at different depths"""
    
    def test_compress_formula_depth_0(self, sample_metadata_for_compression):
        """Depth 0 should return original formula with no compression"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=0,
                output_format="field_ids"
            )
            
            # Should be unchanged
            assert "fldFieldB0000002" in result
            assert "fldFieldC0000003" in result
            assert "fldFieldD0000004" not in result
            assert depth == 0
    
    def test_compress_formula_depth_1(self, sample_metadata_for_compression):
        """Depth 1 should expand one level only"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=1,
                output_format="field_ids"
            )
            
            # Field B and C should be expanded, but not their dependencies
            assert "fldFieldB0000002" not in result  # B was replaced
            assert "fldFieldC0000003" not in result  # C was replaced
            assert "fldFieldD0000004" in result  # D should appear (from B's expansion)
            assert "fldFieldE0000005" in result  # E should appear (from B/C expansion)
            assert depth == 1
    
    def test_compress_formula_full_depth(self, sample_metadata_for_compression):
        """None depth should fully expand until only non-formula fields remain"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Only D and E (non-formula fields) should remain
            assert "fldFieldB0000002" not in result
            assert "fldFieldC0000003" not in result
            assert "fldFieldD0000004" in result
            assert "fldFieldE0000005" in result
            assert depth == 1  # Max depth reached


class TestCircularReferenceHandling:
    """Test circular dependency detection"""
    
    def test_compress_formula_circular_reference(self, circular_reference_metadata):
        """Should detect and skip circular dependencies"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=circular_reference_metadata):
            # This should not cause infinite recursion
            result, depth = compress_formula(
                "tblCircular001",
                "fldFieldX0000001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should contain the circular reference, but not infinitely expand
            assert "fldFieldY0000002" in result or "fldFieldX0000001" in result
            # Should complete without error


class TestOutputFormats:
    """Test different output formats"""
    
    def test_compress_formula_output_format_field_names(self, sample_metadata_for_compression):
        """Should convert field IDs to names in output"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=None,
                output_format="field_names"
            )
            
            # Should contain field names, not IDs
            assert "Field D" in result
            assert "Field E" in result
            assert "fldFieldD0000004" not in result
            assert "fldFieldE0000005" not in result
    
    def test_compress_formula_output_format_field_ids(self, sample_metadata_for_compression):
        """Should keep field IDs in output"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should contain field IDs
            assert "fldFieldD0000004" in result
            assert "fldFieldE0000005" in result


class TestFormulaParenthesization:
    """Test parenthesis wrapping for operator precedence"""
    
    def test_compress_formula_parenthesization(self, sample_metadata_for_compression):
        """Should wrap replaced formulas in parens for safety"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldA0000001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should have proper parenthesization
            # Field B's formula ({D}+{E}) should be wrapped: ({D}+{E})
            assert "(" in result
            assert ")" in result
            # Count parens to verify wrapping
            assert result.count("(") >= 2  # At least AND() and wrapped subformulas


class TestReverseIteration:
    """Test that matches are processed from end to start"""
    
    def test_compress_formula_reverse_iteration(self):
        """Should process matches from end to start to avoid index shifting"""
        # This is more of an implementation detail test
        # We verify it works by checking complex formulas compress correctly
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Multi Ref",
                            "type": "formula",
                            "options": {
                                "formula": "{fld002} + {fld003} + {fld002}",  # Same field twice
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld002",
                            "name": "Val A",
                            "type": "formula",
                            "options": {
                                "formula": "{fld004} * 2",
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld003",
                            "name": "Val B",
                            "type": "formula",
                            "options": {
                                "formula": "{fld004} * 3",
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld004",
                            "name": "Base Val",
                            "type": "number",
                            "options": {"precision": 0}
                        }
                    ]
                }
            ]
        }
        
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=metadata):
            result, depth = compress_formula(
                "tbl001",
                "fld001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should successfully compress without position errors
            assert "fld004" in result
            assert "fld002" not in result  # Should be fully expanded


class TestNonFormulaFields:
    """Test handling of non-formula fields"""
    
    def test_non_formula_field_stops_recursion(self, sample_metadata_for_compression):
        """Non-formula fields should stop recursion"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            result, depth = compress_formula(
                "tblTestTable1",
                "fldFieldB0000002",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Field B references D (number) and E (checkbox)
            # These should remain as references since they're not formulas
            assert "fldFieldD0000004" in result
            assert "fldFieldE0000005" in result


class TestVisitedFieldsTracking:
    """Test visited fields tracking across branches"""
    
    def test_visited_fields_allows_same_field_in_different_branches(self):
        """Same field should be expandable in different branches"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Root",
                            "type": "formula",
                            "options": {
                                "formula": "IF({fld002}, {fld003}, {fld003})",  # fld003 appears twice
                                "result": {"type": "text"}
                            }
                        },
                        {
                            "id": "fld002",
                            "name": "Condition",
                            "type": "checkbox",
                            "options": {}
                        },
                        {
                            "id": "fld003",
                            "name": "Shared Value",
                            "type": "formula",
                            "options": {
                                "formula": "{fld004} + 1",
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld004",
                            "name": "Base",
                            "type": "number",
                            "options": {"precision": 0}
                        }
                    ]
                }
            ]
        }
        
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=metadata):
            result, depth = compress_formula(
                "tbl001",
                "fld001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # fld003 should be expanded in both branches of the IF
            # Count occurrences of fld004 (the base field)
            assert result.count("fld004") >= 2  # Should appear in both branches


class TestFormulaFormatting:
    """Test formula formatting functions"""
    
    def test_format_formula_compact_removes_whitespace(self):
        """Should remove all extra whitespace"""
        formula = """
        IF(
            {Field A},
            {Field B} + {Field C},
            {Field D}
        )
        """
        result = format_formula_compact(formula)
        
        assert "\n" not in result
        assert "  " not in result  # No double spaces
        assert result.startswith("IF(")
    
    def test_format_formula_compact_preserves_field_names(self):
        """Should preserve spaces inside field references"""
        formula = "IF({Field With Spaces}, {Another Field}, 0)"
        result = format_formula_compact(formula)
        
        assert "{Field With Spaces}" in result
        assert "{Another Field}" in result
    
    def test_format_formula_logical_adds_indentation(self):
        """Should add proper indentation for nested structures"""
        formula = "IF({A},IF({B},{C},{D}),{E})"
        result = format_formula_logical(formula)
        
        # Should have newlines and indentation
        assert "\n" in result
        lines = result.split("\n")
        # Some lines should have indentation
        assert any(line.startswith("    ") for line in lines)
    
    def test_format_formula_logical_with_nested_functions(self):
        """Should handle deeply nested functions"""
        formula = "AND(OR({A},{B}),IF({C},{D},{E}))"
        result = format_formula_logical(formula)
        
        # Should be formatted with multiple levels
        assert "\n" in result
        # Check that it doesn't break field references
        assert "{A}" in result
        assert "{B}" in result


class TestConvertFieldReferences:
    """Test field reference conversion"""
    
    def test_convert_field_references_ids_to_names(self, sample_metadata_for_compression):
        """Should convert field IDs to names"""
        formula = "AND({fldFieldD0000004}, {fldFieldE0000005})"
        result = _convert_field_references(formula, sample_metadata_for_compression, "field_names")
        
        assert "Field D" in result
        assert "Field E" in result
        assert "fldFieldD0000004" not in result
    
    def test_convert_field_references_keeps_ids_when_requested(self, sample_metadata_for_compression):
        """Should keep field IDs when format is field_ids"""
        formula = "AND({fldFieldD0000004}, {fldFieldE0000005})"
        result = _convert_field_references(formula, sample_metadata_for_compression, "field_ids")
        
        # Should be unchanged
        assert formula == result
    
    def test_convert_field_references_handles_missing_field(self, sample_metadata_for_compression):
        """Should keep original reference if field not found"""
        formula = "AND({fldNonExistent001}, {fldFieldE0000005})"
        result = _convert_field_references(formula, sample_metadata_for_compression, "field_names")
        
        # Missing field should remain as ID
        assert "{fldNonExistent001}" in result
        # Existing field should be converted
        assert "Field E" in result


class TestErrorHandling:
    """Test error handling in compression"""
    
    def test_compress_formula_field_not_found(self, sample_metadata_for_compression):
        """Should raise error if field not found"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            with pytest.raises(ValueError, match="Field .* not found"):
                compress_formula(
                    "tblTestTable1",
                    "fldNonExistent001",
                    compression_depth=None,
                    output_format="field_ids"
                )
    
    def test_compress_formula_not_a_formula_field(self, sample_metadata_for_compression):
        """Should raise error if field is not a formula"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=sample_metadata_for_compression):
            with pytest.raises(ValueError, match="not a formula field"):
                compress_formula(
                    "tblTestTable1",
                    "fldFieldD0000004",  # This is a number field, not formula
                    compression_depth=None,
                    output_format="field_ids"
                )
    
    def test_compress_formula_no_metadata(self):
        """Should raise error if no metadata available"""
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=None):
            with pytest.raises(ValueError, match="No metadata available"):
                compress_formula(
                    "tblTestTable1",
                    "fldFieldA0000001",
                    compression_depth=None,
                    output_format="field_ids"
                )


class TestComplexRealWorldScenarios:
    """Test complex real-world compression scenarios"""
    
    def test_deeply_nested_formula_chain(self):
        """Test compression of deeply nested formula chain"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Level 4",
                            "type": "formula",
                            "options": {"formula": "{fld002} + 1", "result": {"type": "number"}}
                        },
                        {
                            "id": "fld002",
                            "name": "Level 3",
                            "type": "formula",
                            "options": {"formula": "{fld003} * 2", "result": {"type": "number"}}
                        },
                        {
                            "id": "fld003",
                            "name": "Level 2",
                            "type": "formula",
                            "options": {"formula": "{fld004} - 5", "result": {"type": "number"}}
                        },
                        {
                            "id": "fld004",
                            "name": "Level 1",
                            "type": "formula",
                            "options": {"formula": "{fld005} / 3", "result": {"type": "number"}}
                        },
                        {
                            "id": "fld005",
                            "name": "Base",
                            "type": "number",
                            "options": {"precision": 0}
                        }
                    ]
                }
            ]
        }
        
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=metadata):
            result, depth = compress_formula(
                "tbl001",
                "fld001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should fully compress to: (((({fld005}/3)-5)*2)+1)
            assert "fld005" in result
            assert "fld001" not in result
            assert "fld002" not in result
            assert "fld003" not in result
            assert "fld004" not in result
            assert depth == 3  # 4 levels of formulas, but 0-indexed so max depth is 3
    
    def test_multiple_references_to_same_field(self):
        """Test formula with multiple references to the same field"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Calc",
                            "type": "formula",
                            "options": {
                                "formula": "{fld002} * {fld002}",  # Square
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld002",
                            "name": "Value",
                            "type": "formula",
                            "options": {"formula": "{fld003} + 5", "result": {"type": "number"}}
                        },
                        {
                            "id": "fld003",
                            "name": "Base",
                            "type": "number",
                            "options": {"precision": 0}
                        }
                    ]
                }
            ]
        }
        
        from unittest.mock import patch
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=metadata):
            result, depth = compress_formula(
                "tbl001",
                "fld001",
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Should expand both references
            # Result should be: ({fld003}+5)*({fld003}+5)
            assert result.count("fld003") == 2  # Should appear twice
            assert "fld002" not in result  # Should be fully expanded


# ============================================================================
# Integration Tests with Real Airtable Data
# ============================================================================

@pytest.mark.airtable_live
class TestFormulaCompressorIntegration:
    """Integration tests using real Airtable data.
    
    These tests validate formula compression with real-world formulas that have
    complex nesting, special characters, edge cases, and patterns not present
    in synthetic test data.
    """
    
    def test_compress_real_formulas(self, airtable_schema):
        """Test formula compression on real Airtable formulas."""
        from unittest.mock import patch
        
        # Find formula fields in real schema
        formula_fields = []
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                if field["type"] == "formula" and field.get("options", {}).get("formula"):
                    formula_fields.append({
                        "table_id": table["id"],
                        "field_id": field["id"],
                        "field_name": field["name"],
                        "formula": field["options"]["formula"]
                    })
        
        if not formula_fields:
            pytest.skip("No formula fields in test base")
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=airtable_schema):
            # Test compression on first few formulas
            for formula_info in formula_fields[:5]:
                try:
                    compressed, depth = compress_formula(
                        formula_info["table_id"],
                        formula_info["field_id"],
                        compression_depth=None,
                        output_format="field_ids"
                    )
                    
                    # Should return valid results
                    assert isinstance(compressed, str)
                    assert isinstance(depth, int)
                    assert depth >= 0
                    
                    # Compressed formula should not be empty (unless original was)
                    if formula_info["formula"].strip():
                        assert len(compressed) > 0
                    
                except Exception as e:
                    pytest.fail(f"Failed to compress formula '{formula_info['field_name']}': {e}")
    
    def test_compression_depth_limits_with_real_data(self, airtable_schema):
        """Test that depth limiting works with real nested formulas."""
        from unittest.mock import patch
        
        # Find a formula field with references
        formula_field = None
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                if (field["type"] == "formula" and 
                    field.get("options", {}).get("referencedFieldIds") and
                    len(field["options"]["referencedFieldIds"]) > 0):
                    formula_field = {
                        "table_id": table["id"],
                        "field_id": field["id"]
                    }
                    break
            if formula_field:
                break
        
        if not formula_field:
            pytest.skip("No formula fields with references in test base")
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=airtable_schema):
            # Test different depth limits
            result_depth_0, depth_0 = compress_formula(
                formula_field["table_id"],
                formula_field["field_id"],
                compression_depth=0,
                output_format="field_ids"
            )
            
            result_depth_5, depth_5 = compress_formula(
                formula_field["table_id"],
                formula_field["field_id"],
                compression_depth=5,
                output_format="field_ids"
            )
            
            # Depth 0 should be original or minimally expanded
            assert len(result_depth_0) > 0
            
            # Both should be valid strings
            assert isinstance(result_depth_0, str)
            assert isinstance(result_depth_5, str)
    
    def test_field_name_conversion_with_real_names(self, airtable_schema):
        """Test field ID to name conversion with real field names."""
        from unittest.mock import patch
        
        # Find a formula field
        formula_field = None
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                if field["type"] == "formula":
                    formula_field = {
                        "table_id": table["id"],
                        "field_id": field["id"]
                    }
                    break
            if formula_field:
                break
        
        if not formula_field:
            pytest.skip("No formula fields in test base")
        
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=airtable_schema):
            # Compress with field IDs
            result_ids, _ = compress_formula(
                formula_field["table_id"],
                formula_field["field_id"],
                compression_depth=None,
                output_format="field_ids"
            )
            
            # Compress with field names
            result_names, _ = compress_formula(
                formula_field["table_id"],
                formula_field["field_id"],
                compression_depth=None,
                output_format="field_names"
            )
            
            # Both should be valid
            assert isinstance(result_ids, str)
            assert isinstance(result_names, str)
            
            # Field names version should not contain field IDs
            if "fld" in result_ids:
                # If IDs version has field IDs, names version should have fewer/none
                id_count = result_ids.count("fld")
                name_count = result_names.count("fld")
                # Allow some field IDs to remain if they couldn't be converted
                assert name_count <= id_count
    
    def test_circular_reference_handling_in_real_base(self, airtable_schema):
        """Test that circular references are handled gracefully in real base."""
        from unittest.mock import patch
        
        # Try to compress all formulas - should not crash on circular refs
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=airtable_schema):
            for table in airtable_schema["tables"]:
                for field in table["fields"]:
                    if field["type"] == "formula":
                        try:
                            compressed, depth = compress_formula(
                                table["id"],
                                field["id"],
                                compression_depth=10,
                                output_format="field_ids"
                            )
                            # Should complete without infinite loops
                            assert isinstance(compressed, str)
                            assert depth <= 10, "Depth should respect limits"
                        except Exception as e:
                            # Should not crash, but may have other errors
                            assert "maximum recursion" not in str(e).lower()
