"""Tests for Python runtime code generator."""

import sys
from pathlib import Path

# Add web directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

import pytest
from code_generators.python_runtime_generator import (
    PythonFormulaTranspiler,
    PythonLookupRollupGenerator,
    generate_python_library,
)
from at_formula_parser import (
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode,
    parse_airtable_formula,
)


class TestPythonFormulaTranspiler:
    """Test the PythonFormulaTranspiler class."""
    
    def test_transpile_literal_string(self):
        """Test transpiling string literals."""
        transpiler = PythonFormulaTranspiler()
        node = LiteralNode("hello", "string")
        result = transpiler.transpile(node)
        assert result == '"hello"'
    
    def test_transpile_literal_number(self):
        """Test transpiling number literals."""
        transpiler = PythonFormulaTranspiler()
        node = LiteralNode(42, "number")
        result = transpiler.transpile(node)
        assert result == '42'
    
    def test_transpile_literal_boolean(self):
        """Test transpiling boolean literals."""
        transpiler = PythonFormulaTranspiler()
        node_true = LiteralNode(True, "boolean")
        node_false = LiteralNode(False, "boolean")
        
        assert transpiler.transpile(node_true) == 'True'
        assert transpiler.transpile(node_false) == 'False'
    
    def test_transpile_field_reference_dataclass(self):
        """Test transpiling field references with dataclass mode."""
        transpiler = PythonFormulaTranspiler(data_access_mode="dataclass")
        node = FieldReferenceNode("fld123", "Customer Name", "singleLineText")
        result = transpiler.transpile(node)
        assert result == 'record.customer_name'
    
    def test_transpile_field_reference_dict(self):
        """Test transpiling field references with dict mode."""
        transpiler = PythonFormulaTranspiler(data_access_mode="dict")
        node = FieldReferenceNode("fld123", "Customer Name", "singleLineText")
        result = transpiler.transpile(node)
        # Dict mode uses .get() to avoid KeyError for missing fields
        assert result == 'record.get("customer_name")'
    
    def test_transpile_binary_op_addition(self):
        """Test transpiling addition operation."""
        transpiler = PythonFormulaTranspiler()
        node = BinaryOpNode("+",
            LiteralNode(1, "number"),
            LiteralNode(2, "number")
        )
        result = transpiler.transpile(node)
        assert result == '(1 + 2)'
    
    def test_transpile_binary_op_string_concat(self):
        """Test transpiling string concatenation (&)."""
        transpiler = PythonFormulaTranspiler()
        node = BinaryOpNode("&",
            LiteralNode("hello", "string"),
            LiteralNode("world", "string")
        )
        result = transpiler.transpile(node)
        assert 'str("hello")' in result
        assert 'str("world")' in result
        assert '+' in result
    
    def test_transpile_binary_op_comparison(self):
        """Test transpiling comparison operations."""
        transpiler = PythonFormulaTranspiler()
        
        # Equals
        node = BinaryOpNode("=",
            LiteralNode(1, "number"),
            LiteralNode(2, "number")
        )
        assert transpiler.transpile(node) == '(1 == 2)'
        
        # Not equals
        node = BinaryOpNode("!=",
            LiteralNode(1, "number"),
            LiteralNode(2, "number")
        )
        assert transpiler.transpile(node) == '(1 != 2)'
    
    def test_transpile_unary_op_negation(self):
        """Test transpiling unary negation."""
        transpiler = PythonFormulaTranspiler()
        node = UnaryOpNode("-",
            LiteralNode(5, "number")
        )
        result = transpiler.transpile(node)
        assert result == '(-5)'
    
    def test_transpile_unary_op_not(self):
        """Test transpiling NOT operation."""
        transpiler = PythonFormulaTranspiler()
        node = UnaryOpNode("NOT",
            LiteralNode(True, "boolean")
        )
        result = transpiler.transpile(node)
        assert result == '(not True)'
    
    def test_transpile_if_function(self):
        """Test transpiling IF function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("IF",
            [
                LiteralNode(True, "boolean"),
                LiteralNode("yes", "string"),
                LiteralNode("no", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert '("yes" if True else "no")' == result
    
    def test_transpile_and_function(self):
        """Test transpiling AND function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("AND",
            [
                LiteralNode(True, "boolean"),
                LiteralNode(False, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == '(True and False)'
    
    def test_transpile_or_function(self):
        """Test transpiling OR function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("OR",
            [
                LiteralNode(True, "boolean"),
                LiteralNode(False, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == '(True or False)'
    
    def test_transpile_concatenate_function(self):
        """Test transpiling CONCATENATE function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("CONCATENATE",
            [
                LiteralNode("hello", "string"),
                LiteralNode("world", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert 'str("hello")' in result
        assert 'str("world")' in result
        assert '+' in result
    
    def test_transpile_len_function(self):
        """Test transpiling LEN function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("LEN",
            [LiteralNode("hello", "string")]
        )
        result = transpiler.transpile(node)
        assert 'len(str("hello")' in result
    
    def test_transpile_upper_function(self):
        """Test transpiling UPPER function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("UPPER",
            [LiteralNode("hello", "string")]
        )
        result = transpiler.transpile(node)
        assert '.upper()' in result
    
    def test_transpile_lower_function(self):
        """Test transpiling LOWER function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("LOWER",
            [LiteralNode("HELLO", "string")]
        )
        result = transpiler.transpile(node)
        assert '.lower()' in result
    
    def test_transpile_round_function(self):
        """Test transpiling ROUND function."""
        transpiler = PythonFormulaTranspiler()
        
        # Round with precision
        node = FunctionCallNode("ROUND",
            [
                LiteralNode(3.14159, "number"),
                LiteralNode(2, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == 'round(3.14159, int(2))'
        
        # Round without precision
        node = FunctionCallNode("ROUND",
            [LiteralNode(3.7, "number")]
        )
        result = transpiler.transpile(node)
        assert result == 'round(3.7)'
    
    def test_transpile_abs_function(self):
        """Test transpiling ABS function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("ABS",
            [LiteralNode(-5, "number")]
        )
        result = transpiler.transpile(node)
        assert result == 'abs(-5)'
    
    def test_transpile_mod_function(self):
        """Test transpiling MOD function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("MOD",
            [
                LiteralNode(10, "number"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == '(10 % 3)'
    
    def test_transpile_max_function(self):
        """Test transpiling MAX function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("MAX",
            [
                LiteralNode(10, "number"),
                LiteralNode(20, "number"),
                LiteralNode(15, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == 'max(10, 20, 15)'
    
    def test_transpile_min_function(self):
        """Test transpiling MIN function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("MIN",
            [
                LiteralNode(10, "number"),
                LiteralNode(20, "number"),
                LiteralNode(15, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == 'min(10, 20, 15)'
    
    def test_transpile_left_function(self):
        """Test transpiling LEFT function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("LEFT",
            [
                LiteralNode("hello", "string"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert 'str("hello")[:int(3)]' in result
    
    def test_transpile_right_function(self):
        """Test transpiling RIGHT function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("RIGHT",
            [
                LiteralNode("hello", "string"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert 'str("hello")[-int(3):]' in result
    
    def test_transpile_find_function(self):
        """Test transpiling FIND function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("FIND",
            [
                LiteralNode("l", "string"),
                LiteralNode("hello", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert '.find(' in result
        assert '+ 1' in result  # Airtable uses 1-based indexing
    
    def test_transpile_year_function(self):
        """Test transpiling YEAR function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("YEAR",
            [FieldReferenceNode("fld123", "date_field", "date")]
        )
        result = transpiler.transpile(node)
        assert '.year' in result
    
    def test_transpile_month_function(self):
        """Test transpiling MONTH function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("MONTH",
            [FieldReferenceNode("fld123", "date_field", "date")]
        )
        result = transpiler.transpile(node)
        assert '.month' in result
    
    def test_transpile_day_function(self):
        """Test transpiling DAY function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("DAY",
            [FieldReferenceNode("fld123", "date_field", "date")]
        )
        result = transpiler.transpile(node)
        assert '.day' in result
    
    def test_transpile_now_function(self):
        """Test transpiling NOW function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("NOW", [])
        result = transpiler.transpile(node)
        assert result == 'datetime.datetime.now()'
    
    def test_transpile_today_function(self):
        """Test transpiling TODAY function."""
        transpiler = PythonFormulaTranspiler()
        node = FunctionCallNode("TODAY", [])
        result = transpiler.transpile(node)
        assert result == 'datetime.date.today()'
    
    def test_transpile_nested_formula(self):
        """Test transpiling nested formulas."""
        transpiler = PythonFormulaTranspiler()
        # IF(amount > 100, UPPER("big"), LOWER("SMALL"))
        node = FunctionCallNode("IF",
            [
                BinaryOpNode(">",
                    FieldReferenceNode("fld123", "amount", "number"),
                    LiteralNode(100, "number")
                ),
                FunctionCallNode("UPPER",
                    [LiteralNode("big", "string")]
                ),
                FunctionCallNode("LOWER",
                    [LiteralNode("SMALL", "string")]
                )
            ]
        )
        result = transpiler.transpile(node)
        assert 'if' in result
        assert 'record.amount' in result
        assert '100' in result
        assert '.upper()' in result
        assert '.lower()' in result
    
    def test_sanitize_field_name(self):
        """Test field name sanitization."""
        transpiler = PythonFormulaTranspiler()
        
        assert transpiler._sanitize_field_name("Customer Name") == "customer_name"
        assert transpiler._sanitize_field_name("Total $ Value") == "total_value"
        assert transpiler._sanitize_field_name("2023 Revenue") == "_2023_revenue"
        assert transpiler._sanitize_field_name("Email-Address") == "email_address"
        assert transpiler._sanitize_field_name("Multiple___Underscores") == "multiple_underscores"


class TestPythonLookupRollupGenerator:
    """Test the PythonLookupRollupGenerator class."""
    
    def test_generate_lookup_getter_single(self):
        """Test generating lookup getter for single-value lookup."""
        generator = PythonLookupRollupGenerator()
        
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldLink",
                            "name": "Customer",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tbl2"}
                        },
                        {
                            "id": "fldLookup",
                            "name": "Customer Email",
                            "type": "multipleLookupValues",
                            "options": {
                                "recordLinkFieldId": "fldLink",
                                "fieldIdInLinkedTable": "fldEmail"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldEmail",
                            "name": "Email",
                            "type": "email"
                        }
                    ]
                }
            ]
        }
        
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_lookup_getter(field, metadata, "Orders")
        
        assert "def get_customer_email" in result
        assert "Lookup Customer Email" in result
        assert "data_access.get_customers" in result
        assert "return" in result
    
    def test_generate_rollup_getter_sum(self):
        """Test generating rollup getter with SUM aggregation."""
        generator = PythonLookupRollupGenerator()
        
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldLink",
                            "name": "Orders",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tbl2"}
                        },
                        {
                            "id": "fldRollup",
                            "name": "Total Revenue",
                            "type": "rollup",
                            "options": {
                                "recordLinkFieldId": "fldLink",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "SUM"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_rollup_getter(field, metadata, "Customers")
        
        assert "def get_total_revenue" in result
        assert "Rollup Total Revenue" in result
        assert "SUM" in result
        assert "sum(values)" in result
        assert "data_access.get_orders_batch" in result
    
    def test_generate_rollup_getter_count(self):
        """Test generating rollup getter with COUNT aggregation."""
        generator = PythonLookupRollupGenerator()
        
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldLink",
                            "name": "Orders",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tbl2"}
                        },
                        {
                            "id": "fldRollup",
                            "name": "Order Count",
                            "type": "rollup",
                            "options": {
                                "recordLinkFieldId": "fldLink",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "COUNT"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_rollup_getter(field, metadata, "Customers")
        
        assert "def get_order_count" in result
        assert "COUNT" in result
        assert "len(values)" in result


class TestGeneratePythonLibrary:
    """Test the generate_python_library function."""
    
    def test_generate_library_basic(self):
        """Test generating a basic Python library."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fld2",
                            "name": "Tax Amount",
                            "type": "formula",
                            "options": {
                                "formula": "{fld1} * 1.08",
                                "referencedFieldIds": ["fld1"]
                            }
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata)
        
        # Check header
        assert "Auto-generated from Airtable metadata" in result
        assert "DO NOT EDIT THIS FILE MANUALLY" in result
        
        # Check imports
        assert "from typing import" in result
        assert "import datetime" in result
        assert "import math" in result
        
        # Check DataAccess protocol
        assert "class DataAccess(Protocol):" in result
        assert "def get_orders(" in result
        
        # Check type definitions
        assert "@dataclass" in result
        assert "class Orders:" in result
        
        # Check computed fields class
        assert "class OrdersComputedFields:" in result
        assert "def get_tax_amount" in result
    
    def test_generate_library_with_lookups(self):
        """Test generating library with lookup fields."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldLink",
                            "name": "Customer",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tbl2"}
                        },
                        {
                            "id": "fldLookup",
                            "name": "Customer Email",
                            "type": "multipleLookupValues",
                            "options": {
                                "recordLinkFieldId": "fldLink",
                                "fieldIdInLinkedTable": "fldEmail"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldEmail",
                            "name": "Email",
                            "type": "email"
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata)
        
        assert "class OrdersComputedFields:" in result
        assert "def get_customer_email" in result
        assert "data_access" in result
    
    def test_generate_library_dict_mode(self):
        """Test generating library with dict data access mode."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fld2",
                            "name": "Tax Amount",
                            "type": "formula",
                            "options": {
                                "formula": "{fld1} * 0.08",
                                "referencedFieldIds": ["fld1"]
                            }
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata, {"data_access_mode": "dict"})
        
        # Should use dict-style field access with .get() to avoid KeyError
        assert 'record.get("amount")' in result
    
    def test_generate_library_no_types(self):
        """Test generating library without type definitions."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata, {"include_types": False})
        
        # Should not include dataclass definitions
        assert "@dataclass" not in result or "class Orders:" not in result
    
    def test_generate_library_no_helpers(self):
        """Test generating library without helper functions."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata, {"include_helpers": False})
        
        # Should not include helper functions
        assert "_substitute_nth" not in result
        assert "_flatten_array" not in result
    

    def test_generate_library_complex_formula(self):
        """Test generating library with complex nested formula."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Products",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Price",
                            "type": "number"
                        },
                        {
                            "id": "fld2",
                            "name": "Quantity",
                            "type": "number"
                        },
                        {
                            "id": "fld3",
                            "name": "Total",
                            "type": "formula",
                            "options": {
                                "formula": "IF({fld2} > 10, {fld1} * {fld2} * 0.9, {fld1} * {fld2})",
                                "referencedFieldIds": ["fld1", "fld2"]
                            }
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata)
        
        assert "def get_total" in result
        assert "if" in result
        assert "record.quantity" in result
        assert "record.price" in result
    
    def test_library_is_valid_python(self):
        """Test that generated library is valid Python code."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fld2",
                            "name": "Tax",
                            "type": "formula",
                            "options": {
                                "formula": "ROUND({fld1} * 0.08, 2)",
                                "referencedFieldIds": ["fld1"]
                            }
                        }
                    ]
                }
            ]
        }
        
        result = generate_python_library(metadata)
        
        # Should compile without errors
        compile(result, "<generated>", "exec")


class TestIntegration:
    """Integration tests with real formula parsing."""
    
    def test_parse_and_transpile_simple(self):
        """Test parsing and transpiling a simple formula."""
        formula = "1 + 2"
        ast = parse_airtable_formula(formula)
        
        transpiler = PythonFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert result == "(1 + 2)"
        assert eval(result) == 3
    

    def test_parse_and_transpile_with_field(self):
        """Test parsing and transpiling formula with field reference."""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Amount",
                            "type": "number"
                        }
                    ]
                }
            ]
        }
        
        formula = "{fld1} * 1.08"
        ast = parse_airtable_formula(formula, metadata)
        
        transpiler = PythonFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert "record.amount" in result
        assert "* 1.08" in result
    
    def test_parse_and_transpile_string_function(self):
        """Test parsing and transpiling string functions."""
        formula = 'UPPER("hello")'
        ast = parse_airtable_formula(formula)
        
        transpiler = PythonFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert ".upper()" in result
    
    def test_parse_and_transpile_if_function(self):
        """Test parsing and transpiling IF function."""
        formula = 'IF(TRUE, "yes", "no")'
        ast = parse_airtable_formula(formula)
        
        transpiler = PythonFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert 'if' in result
        assert 'else' in result
