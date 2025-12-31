"""Tests for Airtable formula to SQL converter"""

import pytest
import sys
from pathlib import Path

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from airtable_formula_to_sql import (
    convert_airtable_formula_to_sql,
    convert_formula_to_generated_column,
    is_formula_convertible,
    FormulaConversionError,
    _replace_field_references,
    _parse_function_args,
)


class TestReplaceFieldReferences:
    """Test field reference replacement"""
    
    def test_simple_field_reference(self):
        """Test replacing a single field reference"""
        formula = "{fld123}"
        field_map = {"fld123": "amount"}
        result = _replace_field_references(formula, field_map)
        assert result == "amount"
    
    def test_multiple_field_references(self):
        """Test replacing multiple field references"""
        formula = "{fld123} + {fld456}"
        field_map = {"fld123": "price", "fld456": "quantity"}
        result = _replace_field_references(formula, field_map)
        assert result == "price + quantity"
    
    def test_missing_field_reference(self):
        """Test that missing field references are left unchanged"""
        formula = "{fld123} + {fld999}"
        field_map = {"fld123": "price"}
        result = _replace_field_references(formula, field_map)
        assert result == "price + {fld999}"
    
    def test_field_reference_in_function(self):
        """Test field references inside function calls"""
        formula = "IF({fld123} > 10, {fld456}, 0)"
        field_map = {"fld123": "amount", "fld456": "bonus"}
        result = _replace_field_references(formula, field_map)
        assert result == "IF(amount > 10, bonus, 0)"


class TestParseFunctionArgs:
    """Test function argument parsing"""
    
    def test_single_arg(self):
        """Test parsing single argument"""
        args = _parse_function_args("field1")
        assert args == ["field1"]
    
    def test_multiple_args(self):
        """Test parsing multiple arguments"""
        args = _parse_function_args("field1, field2, field3")
        assert args == ["field1", "field2", "field3"]
    
    def test_nested_function(self):
        """Test parsing arguments with nested function"""
        args = _parse_function_args("field1, UPPER(field2), 100")
        assert args == ["field1", "UPPER(field2)", "100"]
    
    def test_string_literal_with_comma(self):
        """Test that commas inside strings don't split arguments"""
        args = _parse_function_args('"Hello, World", field1')
        assert args == ['"Hello, World"', "field1"]
    
    def test_deeply_nested(self):
        """Test deeply nested parentheses"""
        args = _parse_function_args("IF(x > 0, MAX(a, b), MIN(c, d)), field2")
        assert args == ["IF(x > 0, MAX(a, b), MIN(c, d))", "field2"]


class TestConvertAirtableFormula:
    """Test complete formula conversion"""
    
    def test_simple_arithmetic(self):
        """Test simple arithmetic expression"""
        formula = "{fld123} * {fld456}"
        field_map = {"fld123": "price", "fld456": "quantity"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "price * quantity"
    
    def test_if_function(self):
        """Test IF function conversion to CASE"""
        formula = "IF({fld123} > 10, \"High\", \"Low\")"
        field_map = {"fld123": "amount"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "CASE WHEN amount > 10 THEN" in result
        assert "\"High\" ELSE \"Low\" END" in result
    
    def test_concatenation(self):
        """Test string concatenation operator conversion"""
        formula = "{fld123} & \" - \" & {fld456}"
        field_map = {"fld123": "first_name", "fld456": "last_name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        # & should be converted to ||
        assert "first_name || \" - \" || last_name" in result
    
    def test_lower_function(self):
        """Test LOWER function conversion"""
        formula = "LOWER({fld123})"
        field_map = {"fld123": "name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "LOWER(name)"
    
    def test_nested_functions(self):
        """Test nested function conversion"""
        formula = "UPPER(TRIM({fld123}))"
        field_map = {"fld123": "name"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "UPPER(TRIM(name))"
    
    def test_boolean_literals(self):
        """Test boolean literal conversion"""
        formula = "IF({fld123}, TRUE, FALSE)"
        field_map = {"fld123": "is_active"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        # TRUE/FALSE should be converted to true/false
        assert "true" in result.lower()
        assert "false" in result.lower()
    
    def test_and_or_functions(self):
        """Test AND/OR logical functions"""
        formula = "AND({fld123} > 0, {fld456} < 100)"
        field_map = {"fld123": "min_val", "fld456": "max_val"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "min_val > 0 AND max_val < 100" in result
    
    def test_math_functions(self):
        """Test mathematical functions"""
        formula = "ROUND({fld123} / {fld456}, 2)"
        field_map = {"fld123": "total", "fld456": "count"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "ROUND(total / count, 2)" in result


class TestConvertFormulaToGeneratedColumn:
    """Test generated column definition creation"""
    
    def test_basic_generated_column(self):
        """Test basic generated column definition"""
        field_name = "total"
        formula = "{fld123} * {fld456}"
        field_map = {"fld123": "price", "fld456": "quantity"}
        postgres_type = "NUMERIC"
        
        result = convert_formula_to_generated_column(
            field_name, formula, field_map, postgres_type
        )
        
        assert "total NUMERIC GENERATED ALWAYS AS" in result
        assert "price * quantity" in result
        assert "STORED" in result
    
    def test_generated_column_with_if(self):
        """Test generated column with IF function"""
        field_name = "status"
        formula = "IF({fld123} > 100, \"High\", \"Low\")"
        field_map = {"fld123": "amount"}
        postgres_type = "TEXT"
        
        result = convert_formula_to_generated_column(
            field_name, formula, field_map, postgres_type
        )
        
        assert "status TEXT GENERATED ALWAYS AS" in result
        assert "CASE WHEN" in result
        assert "STORED" in result
    
    def test_generated_column_conversion_error(self):
        """Test that conversion errors are raised"""
        field_name = "total"
        formula = "INVALID_FUNCTION({fld123})"
        field_map = {"fld123": "amount"}
        postgres_type = "NUMERIC"
        
        with pytest.raises(FormulaConversionError):
            convert_formula_to_generated_column(
                field_name, formula, field_map, postgres_type
            )


class TestIsFormulaConvertible:
    """Test formula convertibility check"""
    
    def test_simple_formula_is_convertible(self):
        """Test that simple formulas are marked as convertible"""
        formula = "{fld123} + {fld456}"
        assert is_formula_convertible(formula) is True
    
    def test_if_formula_is_convertible(self):
        """Test that IF formulas are convertible"""
        formula = "IF({fld123} > 0, \"Yes\", \"No\")"
        assert is_formula_convertible(formula) is True
    
    def test_arrayjoin_not_convertible(self):
        """Test that ARRAYJOIN is marked as not convertible"""
        formula = "ARRAYJOIN({fld123}, \", \")"
        assert is_formula_convertible(formula) is False
    
    def test_switch_not_convertible(self):
        """Test that SWITCH is marked as not convertible"""
        formula = "SWITCH({fld123}, 1, \"One\", 2, \"Two\")"
        assert is_formula_convertible(formula) is False
    
    def test_record_id_not_convertible(self):
        """Test that RECORD_ID is marked as not convertible"""
        formula = "RECORD_ID()"
        assert is_formula_convertible(formula) is False
    
    def test_regex_not_convertible(self):
        """Test that REGEX functions are marked as not convertible"""
        formula = "REGEX_MATCH({fld123}, \"[0-9]+\")"
        assert is_formula_convertible(formula) is False


class TestComplexFormulas:
    """Test complex real-world formula conversions"""
    
    def test_percentage_calculation(self):
        """Test percentage calculation formula"""
        formula = "({fld123} / {fld456}) * 100"
        field_map = {"fld123": "completed", "fld456": "total"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "(completed / total) * 100"
    
    def test_nested_if_statements(self):
        """Test nested IF statements"""
        formula = "IF({fld123} > 100, \"High\", IF({fld123} > 50, \"Medium\", \"Low\"))"
        field_map = {"fld123": "score"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        # Should have nested CASE statements
        assert result.count("CASE WHEN") == 2
        assert "score > 100" in result
        assert "score > 50" in result
    
    def test_date_extraction(self):
        """Test date extraction functions"""
        formula = "YEAR({fld123})"
        field_map = {"fld123": "created_date"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "EXTRACT(YEAR FROM created_date)" in result
    
    def test_string_manipulation(self):
        """Test complex string manipulation"""
        formula = "UPPER(TRIM({fld123})) & \" (\" & LEFT({fld456}, 3) & \")\""
        field_map = {"fld123": "name", "fld456": "code"}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert "UPPER(TRIM(name))" in result
        assert "LEFT(code, 3)" in result
        assert "||" in result  # Concatenation operator


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_formula(self):
        """Test empty formula"""
        formula = ""
        field_map = {}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == ""
    
    def test_formula_with_only_literal(self):
        """Test formula that's just a literal value"""
        formula = "\"Hello World\""
        field_map = {}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "\"Hello World\""
    
    def test_formula_with_only_number(self):
        """Test formula that's just a number"""
        formula = "42"
        field_map = {}
        result = convert_airtable_formula_to_sql(formula, field_map)
        assert result == "42"
    
    def test_unmatched_parentheses(self):
        """Test that unmatched parentheses raise error"""
        formula = "IF({fld123} > 0, \"Yes\""  # Missing closing paren
        field_map = {"fld123": "amount"}
        with pytest.raises(FormulaConversionError):
            convert_airtable_formula_to_sql(formula, field_map)
