"""Tests for Airtable Formula to PostgreSQL SQL converter"""

import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from airtable_formula_to_sql import convert_airtable_formula_to_sql, FormulaConversionError


class TestBasicConversions:
    """Test basic formula conversions"""
    
    def test_simple_field_reference(self):
        """Test simple field reference conversion"""
        formula = "{fld123}"
        field_map = {"fld123": "company_name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "company_name"
    
    def test_arithmetic_operators(self):
        """Test arithmetic operator conversion"""
        formula = "{fld1} + {fld2} * {fld3}"
        field_map = {"fld1": "a", "fld2": "b", "fld3": "c"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "a + b * c"
    
    def test_string_concatenation(self):
        """Test string concatenation with & operator"""
        formula = '{fld1} & " - " & {fld2}'
        field_map = {"fld1": "first_name", "fld2": "last_name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "first_name || ' - ' || last_name"
    
    def test_if_function(self):
        """Test IF function conversion"""
        formula = 'IF({fld1} > 10, "High", "Low")'
        field_map = {"fld1": "amount"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "CASE WHEN" in result
        assert "THEN 'High'" in result
        assert "ELSE 'Low'" in result


class TestTruthinessAndNullChecks:
    """Test SQL conversion fixes for truthiness and NULL comparisons"""
    
    def test_if_with_field_reference_truthiness(self):
        """Test that IF with field reference uses proper boolean check (IS NOT NULL)"""
        formula = "IF({fldCompanyType}, {fldCompanyType}, {fldContactLink})"
        field_map = {
            "fldCompanyType": "company_type_dm_link",
            "fldContactLink": "company_type_contact_link"
        }
        result = convert_airtable_formula_to_sql(formula, field_map)
        
        # Should use IS NOT NULL or similar boolean check, not just field name
        assert "IS NOT NULL" in result or "IS NULL" in result or "!=" in result
        assert "CASE WHEN" in result
    
    def test_null_comparison_with_is_null(self):
        """Test that NULL comparisons use IS NULL syntax"""
        formula = "IF({fldOverride}=NULL, {fldCreate}, {fldOverride})"
        field_map = {
            "fldOverride": "ovrd_source_time",
            "fldCreate": "create_date"
        }
        result = convert_airtable_formula_to_sql(formula, field_map)
        
        # Should use IS NULL, not =NULL
        assert "IS NULL" in result
        assert "=NULL" not in result
    
    def test_nested_if_with_field_truthiness(self):
        """Test nested IF statements with field reference truthiness"""
        formula = "IF({fldA}, {fldA}, IF({fldB}, {fldB}, {fldC}))"
        field_map = {
            "fldA": "company",
            "fldB": "dm_for",
            "fldC": "billing_for"
        }
        result = convert_airtable_formula_to_sql(formula, field_map)
        
        # Multiple CASE WHEN with proper boolean checks
        assert result.count("CASE WHEN") >= 1
        assert "IS NOT NULL" in result or "IS NULL" in result


class TestArrayConcatenationFix:
    """Test fix for array concatenation with delimiters"""
    
    def test_array_concat_with_comma_delimiter(self):
        """Test that array concatenation with comma delimiter is converted properly"""
        formula = '{fld1}&","&{fld2}&","&{fld3}'
        field_map = {
            "fld1": "company",
            "fld2": "dm_for",
            "fld3": "billing_for",
        }
        field_type_map = {
            "company": "TEXT[]",
            "dm_for": "TEXT[]",
            "billing_for": "TEXT[]",
        }
        result = convert_airtable_formula_to_sql(formula, field_map, field_type_map)
        
        # Should be converted to array_to_string
        assert result == "array_to_string(company||dm_for||billing_for, ',')"
    
    def test_array_concat_with_spaces(self):
        """Test array concatenation with spaces in formula"""
        formula = '{fld1}&","& {fld2} &","&{fld3}'
        field_map = {
            "fld1": "company",
            "fld2": "dm_for",
            "fld3": "billing_for",
        }
        field_type_map = {
            "company": "TEXT[]",
            "dm_for": "TEXT[]",
            "billing_for": "TEXT[]",
        }
        result = convert_airtable_formula_to_sql(formula, field_map, field_type_map)
        
        # Should be converted to array_to_string (spaces preserved around field names)
        assert "array_to_string(" in result
        assert "',')" in result
    
    def test_array_concat_multiple_fields(self):
        """Test array concatenation with many fields (real-world example)"""
        formula = '{fld1}&","&{fld2}&","&{fld3}&","&{fld4}&","&{fld5}&","&{fld6}&","&{fld7}'
        field_map = {
            "fld1": "company",
            "fld2": "dm_for",
            "fld3": "billing_for",
            "fld4": "maps_source_contact_for",
            "fld5": "branches_as_main_contact",
            "fld6": "master_contact_for_deal",
            "fld7": "backup_contact_for_deal",
        }
        field_type_map = {field: "TEXT[]" for field in field_map.values()}
        
        result = convert_airtable_formula_to_sql(formula, field_map, field_type_map)
        
        # Should be converted to array_to_string
        assert result.startswith("array_to_string(")
        assert result.endswith(", ',')")
        
        # All field names should be in the result
        for field_name in field_map.values():
            assert field_name in result
        
        # Should NOT contain any ||","|| patterns
        assert '||","||' not in result
        assert "||','||" not in result
    
    def test_non_array_concat_unchanged(self):
        """Test that non-array string concatenation is not affected"""
        formula = '{fld1}&"-"&{fld2}'
        field_map = {
            "fld1": "first_name",
            "fld2": "last_name",
        }
        # No field type map provided - should not trigger array fix
        result = convert_airtable_formula_to_sql(formula, field_map)
        
        # Should be regular string concatenation
        assert result == "first_name||'-'||last_name"
        assert "array_to_string" not in result
    
    def test_single_delimiter_not_converted(self):
        """Test that single delimiter occurrence is not converted"""
        formula = '{fld1}&","&{fld2}'
        field_map = {
            "fld1": "field1",
            "fld2": "field2",
        }
        result = convert_airtable_formula_to_sql(formula, field_map)
        
        # Only one ||','|| pattern - should not trigger the fix (needs >= 2)
        # This is a conservative approach to avoid false positives
        assert result == "field1||','||field2"
        assert "array_to_string" not in result


class TestStringLiterals:
    """Test string literal conversion"""
    
    def test_double_to_single_quotes(self):
        """Test that double quotes are converted to single quotes"""
        formula = '"Hello World"'
        result = convert_airtable_formula_to_sql(formula, {})
        assert result == "'Hello World'"
    
    def test_quotes_in_strings(self):
        """Test escaping of quotes inside strings"""
        formula = '"It\'s a test"'
        result = convert_airtable_formula_to_sql(formula, {})
        # Single quotes inside the string should be escaped
        assert "''" in result


class TestFunctionConversions:
    """Test function conversions"""
    
    def test_concatenate_function(self):
        """Test CONCATENATE function"""
        formula = 'CONCATENATE({fld1}, " ", {fld2})'
        field_map = {"fld1": "first_name", "fld2": "last_name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "CONCAT(" in result
    
    def test_lower_function(self):
        """Test LOWER function"""
        formula = "LOWER({fld1})"
        field_map = {"fld1": "name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "LOWER(name)"
    
    def test_nested_functions(self):
        """Test nested function calls"""
        formula = "UPPER(TRIM({fld1}))"
        field_map = {"fld1": "name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "UPPER(TRIM(name))"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
