"""Tests for JavaScript runtime generator.

This module tests the JavaScriptFormulaTranspiler, JavaScriptLookupRollupGenerator,
and generate_javascript_library functions.
"""

import sys
from pathlib import Path

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

import pytest
from code_generators.javascript_runtime_generator import (
    JavaScriptFormulaTranspiler,
    JavaScriptLookupRollupGenerator,
    generate_javascript_library,
)
from at_formula_parser import (
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode,
    parse_airtable_formula,
)
from constants import (
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_COUNT,
    FIELD_TYPE_RECORD_LINKS,
)


class TestJavaScriptFormulaTranspiler:
    """Tests for JavaScriptFormulaTranspiler class."""
    
    def test_transpile_literal_string(self):
        """Test transpiling string literals."""
        transpiler = JavaScriptFormulaTranspiler()
        node = LiteralNode("hello", "string")
        result = transpiler.transpile(node)
        assert result == "'hello'"
    
    def test_transpile_literal_number(self):
        """Test transpiling number literals."""
        transpiler = JavaScriptFormulaTranspiler()
        node = LiteralNode(42, "number")
        result = transpiler.transpile(node)
        assert result == "42"
    
    def test_transpile_literal_boolean(self):
        """Test transpiling boolean literals."""
        transpiler = JavaScriptFormulaTranspiler()
        
        node = LiteralNode(True, "boolean")
        result = transpiler.transpile(node)
        assert result == "true"
        
        node = LiteralNode(False, "boolean")
        result = transpiler.transpile(node)
        assert result == "false"
    
    def test_transpile_field_reference_object_mode(self):
        """Test transpiling field references in object mode."""
        transpiler = JavaScriptFormulaTranspiler(data_access_mode="object")
        node = FieldReferenceNode("fldXXXX", "Amount", "number")
        result = transpiler.transpile(node)
        assert result == "record.Amount"
    
    def test_transpile_field_reference_dict_mode(self):
        """Test transpiling field references in dict mode."""
        transpiler = JavaScriptFormulaTranspiler(data_access_mode="dict")
        node = FieldReferenceNode("fldXXXX", "Amount", "number")
        result = transpiler.transpile(node)
        assert result == 'record["Amount"]'
    
    def test_transpile_field_reference_camel_case(self):
        """Test transpiling field references with camelCase conversion."""
        transpiler = JavaScriptFormulaTranspiler(data_access_mode="camelCase")
        node = FieldReferenceNode("fldXXXX", "Customer Name", "text")
        result = transpiler.transpile(node)
        assert result == "record.customerName"
    
    def test_transpile_binary_op_arithmetic(self):
        """Test transpiling arithmetic operations."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # Addition
        node = BinaryOpNode(
            "+",
            LiteralNode(1, "number"),
            LiteralNode(2, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(1 + 2)"
        
        # Subtraction
        node = BinaryOpNode(
            "-",
            LiteralNode(5, "number"),
            LiteralNode(3, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(5 - 3)"
        
        # Multiplication
        node = BinaryOpNode(
            "*",
            LiteralNode(4, "number"),
            LiteralNode(5, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(4 * 5)"
        
        # Division
        node = BinaryOpNode(
            "/",
            LiteralNode(10, "number"),
            LiteralNode(2, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(10 / 2)"
    
    def test_transpile_binary_op_comparison(self):
        """Test transpiling comparison operations."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # Equality
        node = BinaryOpNode(
            "=",
            LiteralNode(1, "number"),
            LiteralNode(1, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(1 === 1)"
        
        # Not equal
        node = BinaryOpNode(
            "!=",
            LiteralNode(1, "number"),
            LiteralNode(2, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(1 !== 2)"
    
    def test_transpile_binary_op_string_concat(self):
        """Test transpiling string concatenation."""
        transpiler = JavaScriptFormulaTranspiler()
        node = BinaryOpNode(
            "&",
            LiteralNode("Hello", "string"),
            LiteralNode("World", "string")
        )
        result = transpiler.transpile(node)
        assert result == "(String('Hello' ?? '') + String('World' ?? ''))"
    
    def test_transpile_unary_op_negation(self):
        """Test transpiling unary negation."""
        transpiler = JavaScriptFormulaTranspiler()
        node = UnaryOpNode(
            "-",
            LiteralNode(5, "number")
        )
        result = transpiler.transpile(node)
        assert result == "(-5)"
    
    def test_transpile_unary_op_not(self):
        """Test transpiling logical NOT."""
        transpiler = JavaScriptFormulaTranspiler()
        node = UnaryOpNode(
            "NOT",
            LiteralNode(True, "boolean")
        )
        result = transpiler.transpile(node)
        assert result == "(!true)"
    
    def test_transpile_if_function(self):
        """Test transpiling IF function."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # IF with 3 arguments
        node = FunctionCallNode(
            "IF",
            [
                LiteralNode(True, "boolean"),
                LiteralNode("yes", "string"),
                LiteralNode("no", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(true ? 'yes' : 'no')"
        
        # IF with 2 arguments
        node = FunctionCallNode(
            
            "IF",
            [
                LiteralNode(True, "boolean"),
                LiteralNode("yes", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(true ? 'yes' : null)"
    
    def test_transpile_and_function(self):
        """Test transpiling AND function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "AND",
            [
                LiteralNode(True, "boolean"),
                LiteralNode(True, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(true && true)"
    
    def test_transpile_or_function(self):
        """Test transpiling OR function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "OR",
            [
                LiteralNode(False, "boolean"),
                LiteralNode(True, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(false || true)"
    
    def test_transpile_not_function(self):
        """Test transpiling NOT function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "NOT",
            [
                LiteralNode(True, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(!true)"
    
    def test_transpile_blank_function(self):
        """Test transpiling BLANK function."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # BLANK() with no arguments
        node = FunctionCallNode(
            
            "BLANK",
            []
        )
        result = transpiler.transpile(node)
        assert result == "null"
        
        # BLANK(value) checks if value is blank
        node = FunctionCallNode(
            
            "BLANK",
            [
                LiteralNode("", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "('' == null || '' === '')"
    
    def test_transpile_xor_function(self):
        """Test transpiling XOR function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "XOR",
            [
                LiteralNode(True, "boolean"),
                LiteralNode(False, "boolean")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(!!((true) ^ (false)))"
    
    def test_transpile_concatenate_function(self):
        """Test transpiling CONCATENATE function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "CONCATENATE",
            [
                LiteralNode("Hello", "string"),
                LiteralNode(" ", "string"),
                LiteralNode("World", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('Hello' ?? '') + String(' ' ?? '') + String('World' ?? ''))"
    
    def test_transpile_len_function(self):
        """Test transpiling LEN function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "LEN",
            [
                LiteralNode("hello", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('hello' ?? '')).length"
    
    def test_transpile_upper_function(self):
        """Test transpiling UPPER function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "UPPER",
            [
                LiteralNode("hello", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('hello' ?? '')).toUpperCase()"
    
    def test_transpile_lower_function(self):
        """Test transpiling LOWER function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "LOWER",
            [
                LiteralNode("HELLO", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('HELLO' ?? '')).toLowerCase()"
    
    def test_transpile_trim_function(self):
        """Test transpiling TRIM function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "TRIM",
            [
                LiteralNode("  hello  ", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('  hello  ' ?? '')).trim()"
    
    def test_transpile_left_function(self):
        """Test transpiling LEFT function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "LEFT",
            [
                LiteralNode("hello", "string"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('hello' ?? '')).substring(0, 3)"
    
    def test_transpile_right_function(self):
        """Test transpiling RIGHT function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "RIGHT",
            [
                LiteralNode("hello", "string"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('hello' ?? '')).slice(-3)"
    
    def test_transpile_mid_function(self):
        """Test transpiling MID function (1-based indexing)."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "MID",
            [
                LiteralNode("hello", "string"),
                LiteralNode(2, "number"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        # Should convert to 0-based indexing
        assert result == "(String('hello' ?? '')).substring(2 - 1, (2 - 1) + 3)"
    
    def test_transpile_find_function(self):
        """Test transpiling FIND function."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # FIND with 2 arguments
        node = FunctionCallNode(
            
            "FIND",
            [
                LiteralNode("ll", "string"),
                LiteralNode("hello", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "((String('hello' ?? '')).indexOf(String('ll' ?? '')) + 1)"
        
        # FIND with 3 arguments (start position)
        node = FunctionCallNode(
            
            "FIND",
            [
                LiteralNode("ll", "string"),
                LiteralNode("hello", "string"),
                LiteralNode(1, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "((String('hello' ?? '')).indexOf(String('ll' ?? ''), 1 - 1) + 1)"
    
    def test_transpile_substitute_function(self):
        """Test transpiling SUBSTITUTE function."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # SUBSTITUTE with 3 arguments (replace all)
        node = FunctionCallNode(
            
            "SUBSTITUTE",
            [
                LiteralNode("hello", "string"),
                LiteralNode("l", "string"),
                LiteralNode("L", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "_substituteAll(String('hello' ?? ''), String('l' ?? ''), String('L' ?? ''))"
        
        # SUBSTITUTE with 4 arguments (replace nth)
        node = FunctionCallNode(
            
            "SUBSTITUTE",
            [
                LiteralNode("hello", "string"),
                LiteralNode("l", "string"),
                LiteralNode("L", "string"),
                LiteralNode(1, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "_substituteNth(String('hello' ?? ''), String('l' ?? ''), String('L' ?? ''), 1)"
    
    def test_transpile_replace_function(self):
        """Test transpiling REPLACE function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "REPLACE",
            [
                LiteralNode("hello", "string"),
                LiteralNode(2, "number"),
                LiteralNode(3, "number"),
                LiteralNode("XYZ", "string")
            ]
        )
        result = transpiler.transpile(node)
        # Should convert to 0-based indexing
        assert result == "(String('hello' ?? '')).substring(0, 2 - 1) + String('XYZ' ?? '') + (String('hello' ?? '')).substring((2 - 1) + 3)"
    
    def test_transpile_rept_function(self):
        """Test transpiling REPT function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "REPT",
            [
                LiteralNode("x", "string"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(String('x' ?? '')).repeat(3)"
    
    def test_transpile_round_function(self):
        """Test transpiling ROUND function."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # ROUND with 1 argument
        node = FunctionCallNode(
            
            "ROUND",
            [
                LiteralNode(3.14159, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "Math.round(3.14159)"
        
        # ROUND with 2 arguments (precision)
        node = FunctionCallNode(
            
            "ROUND",
            [
                LiteralNode(3.14159, "number"),
                LiteralNode(2, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(Math.round(3.14159 * Math.pow(10, 2)) / Math.pow(10, 2))"
    
    def test_transpile_abs_function(self):
        """Test transpiling ABS function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "ABS",
            [
                LiteralNode(-5, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "Math.abs(-5)"
    
    def test_transpile_mod_function(self):
        """Test transpiling MOD function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "MOD",
            [
                LiteralNode(10, "number"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(10 % 3)"
    
    def test_transpile_max_function(self):
        """Test transpiling MAX function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "MAX",
            [
                LiteralNode(1, "number"),
                LiteralNode(5, "number"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "Math.max(1, 5, 3)"
    
    def test_transpile_min_function(self):
        """Test transpiling MIN function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "MIN",
            [
                LiteralNode(1, "number"),
                LiteralNode(5, "number"),
                LiteralNode(3, "number")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "Math.min(1, 5, 3)"
    
    def test_transpile_year_function(self):
        """Test transpiling YEAR function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "YEAR",
            [
                LiteralNode("2023-01-15", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(new Date('2023-01-15')).getFullYear()"
    
    def test_transpile_month_function(self):
        """Test transpiling MONTH function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "MONTH",
            [
                LiteralNode("2023-01-15", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "((new Date('2023-01-15')).getMonth() + 1)"
    
    def test_transpile_day_function(self):
        """Test transpiling DAY function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "DAY",
            [
                LiteralNode("2023-01-15", "string")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "(new Date('2023-01-15')).getDate()"
    
    def test_transpile_now_function(self):
        """Test transpiling NOW function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "NOW",
            []
        )
        result = transpiler.transpile(node)
        assert result == "new Date()"
    
    def test_transpile_today_function(self):
        """Test transpiling TODAY function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "TODAY",
            []
        )
        result = transpiler.transpile(node)
        assert result == "new Date(new Date().setHours(0, 0, 0, 0))"
    
    def test_transpile_arraycompact_function(self):
        """Test transpiling ARRAYCOMPACT function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "ARRAYCOMPACT",
            [
                LiteralNode([1, None, 2, "", 3], "array")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "([1, None, 2, '', 3]).filter(x => x != null && x !== '')"
    
    def test_transpile_arrayflatten_function(self):
        """Test transpiling ARRAYFLATTEN function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "ARRAYFLATTEN",
            [
                LiteralNode([[1, 2], [3, 4]], "array")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "_flattenArray([[1, 2], [3, 4]])"
    
    def test_transpile_arrayunique_function(self):
        """Test transpiling ARRAYUNIQUE function."""
        transpiler = JavaScriptFormulaTranspiler()
        node = FunctionCallNode(
            
            "ARRAYUNIQUE",
            [
                LiteralNode([1, 2, 2, 3, 3, 3], "array")
            ]
        )
        result = transpiler.transpile(node)
        assert result == "[...new Set([1, 2, 2, 3, 3, 3])]"
    
    def test_transpile_nested_formula(self):
        """Test transpiling nested formulas."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # IF(LEN(name) > 5, UPPER(name), LOWER(name))
        node = FunctionCallNode(
            "IF",
            [
                BinaryOpNode(
                    ">",
                    FunctionCallNode(
                        "LEN",
                        [
                            FieldReferenceNode("fldXXXX", "name", "text")
                        ]
                    ),
                    LiteralNode(5, "number")
                ),
                FunctionCallNode(
                    "UPPER",
                    [
                        FieldReferenceNode("fldXXXX", "name", "text")
                    ]
                ),
                FunctionCallNode(
                    "LOWER",
                    [
                        FieldReferenceNode("fldXXXX", "name", "text")
                    ]
                )
            ]
        )
        result = transpiler.transpile(node)
        assert "(String(record.name ?? '')).length > 5" in result
        assert "(String(record.name ?? '')).toUpperCase()" in result
        assert "(String(record.name ?? '')).toLowerCase()" in result
    
    def test_sanitize_field_name(self):
        """Test field name sanitization."""
        transpiler = JavaScriptFormulaTranspiler()
        
        # Spaces to underscores
        assert transpiler._sanitize_field_name("Customer Name") == "Customer_Name"
        
        # Special characters to underscores
        assert transpiler._sanitize_field_name("Price ($)") == "Price"
        
        # Leading numbers
        assert transpiler._sanitize_field_name("123 Field") == "_123_Field"
        
        # Multiple underscores
        assert transpiler._sanitize_field_name("A___B") == "A_B"
    
    def test_to_camel_case(self):
        """Test camelCase conversion."""
        transpiler = JavaScriptFormulaTranspiler()
        
        assert transpiler._to_camel_case("Customer Name") == "customerName"
        assert transpiler._to_camel_case("Total Amount USD") == "totalAmountUsd"
        assert transpiler._to_camel_case("ID") == "id"


class TestJavaScriptLookupRollupGenerator:
    """Tests for JavaScriptLookupRollupGenerator class."""
    
    def test_generate_lookup_getter(self):
        """Test generating lookup getter."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldCustomerLink",
                            "name": "Customer",
                            "type": FIELD_TYPE_RECORD_LINKS,
                            "options": {"linkedTableId": "tblCustomers"}
                        },
                        {
                            "id": "fldLookup",
                            "name": "Customer Email",
                            "type": FIELD_TYPE_LOOKUP,
                            "options": {
                                "recordLinkFieldId": "fldCustomerLink",
                                "fieldIdInLinkedTable": "fldEmail"
                            }
                        }
                    ]
                },
                {
                    "id": "tblCustomers",
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
        
        generator = JavaScriptLookupRollupGenerator()
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_lookup_getter(field, metadata, "Orders")
        
        assert "async getCustomerEmail(record)" in result
        # This should be a multi-value lookup since link field type is multipleRecordLinks
        assert "this.dataAccess.getCustomersBatch(" in result
        assert "return linkedRecords.map(r => r.Email)" in result
    
    def test_generate_rollup_getter_sum(self):
        """Test generating rollup getter with SUM aggregation."""
        metadata = {
            "tables": [
                {
                    "id": "tblCustomers",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldOrdersLink",
                            "name": "Orders",
                            "type": FIELD_TYPE_RECORD_LINKS,
                            "options": {"linkedTableId": "tblOrders"}
                        },
                        {
                            "id": "fldRollup",
                            "name": "Total Revenue",
                            "type": FIELD_TYPE_ROLLUP,
                            "options": {
                                "recordLinkFieldId": "fldOrdersLink",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "SUM"
                            }
                        }
                    ]
                },
                {
                    "id": "tblOrders",
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
        
        generator = JavaScriptLookupRollupGenerator()
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_rollup_getter(field, metadata, "Customers")
        
        assert "async getTotalRevenue(record)" in result
        assert "this.dataAccess.getOrdersBatch(" in result
        assert "reduce((a, b) => a + b, 0)" in result
    
    def test_generate_count_getter(self):
        """Test generating count getter."""
        metadata = {
            "tables": [
                {
                    "id": "tblCustomers",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldOrdersLink",
                            "name": "Orders",
                            "type": FIELD_TYPE_RECORD_LINKS,
                            "options": {"linkedTableId": "tblOrders"}
                        },
                        {
                            "id": "fldCount",
                            "name": "Order Count",
                            "type": FIELD_TYPE_COUNT,
                            "options": {
                                "recordLinkFieldId": "fldOrdersLink"
                            }
                        }
                    ]
                }
            ]
        }
        
        generator = JavaScriptLookupRollupGenerator()
        field = metadata["tables"][0]["fields"][1]
        result = generator.generate_count_getter(field, metadata, "Customers")
        
        assert "getOrderCount(record)" in result
        assert "return linkedIds.length" in result


class TestGenerateJavaScriptLibrary:
    """Tests for generate_javascript_library function."""
    
    def test_generate_basic_library(self):
        """Test generating basic library with formulas."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} * 0.08",
                                "referencedFieldIds": ["fldAmount"]
                            }
                        }
                    ]
                }
            ]
        }
        
        library = generate_javascript_library(metadata)
        
        # Check header
        assert "Auto-generated from Airtable metadata" in library
        assert "DO NOT EDIT THIS FILE MANUALLY" in library
        
        # Check helper functions
        assert "function _flattenArray(arr)" in library
        assert "function _substituteNth" in library
        
        # Check class generation
        assert "export class OrdersComputedFields" in library
        assert "constructor(dataAccess)" in library
        assert "this.dataAccess = dataAccess" in library
        
        # Check formula getter
        assert "getTax(record)" in library
    
    def test_generate_library_with_typescript(self):
        """Test generating library with TypeScript annotations."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} * 0.08",
                                "referencedFieldIds": ["fldAmount"]
                            }
                        }
                    ]
                }
            ]
        }
        
        library = generate_javascript_library(metadata, {"use_typescript": True})
        
        # Check TypeScript annotations
        assert "private dataAccess: any;" in library
        assert "constructor(dataAccess: any)" in library
        assert "getTax(record) any" in library
    
    def test_generate_library_without_helpers(self):
        """Test generating library without helper functions."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
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
        
        library = generate_javascript_library(metadata, {"include_helpers": False})
        
        # Helper functions should not be present
        assert "_flattenArray" not in library
        assert "_substituteNth" not in library
    
    def test_generate_library_without_comments(self):
        """Test generating library without depth comments."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} * 0.08",
                                "referencedFieldIds": ["fldAmount"]
                            }
                        }
                    ]
                }
            ]
        }
        
        library = generate_javascript_library(metadata, {"include_comments": False})
        
        # Depth comments should not be present
        assert "// Depth 1 computed fields" not in library
    
    def test_code_validity(self):
        """Test that generated code is valid JavaScript (basic check)."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number"
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} * 0.08",
                                "referencedFieldIds": ["fldAmount"]
                            }
                        }
                    ]
                }
            ]
        }
        
        library = generate_javascript_library(metadata)
        
        # Basic syntax checks
        assert library.count("export class") >= 1
        assert library.count("constructor(") >= 1
        assert library.count("this.dataAccess") >= 1
        
        # No Python-specific syntax
        assert "def " not in library
        assert "None" not in library
        assert ": str" not in library
        assert "import " not in library


class TestIntegration:
    """Integration tests combining parsing and transpilation."""
    
    # NOTE: These tests are commented out because they test the formula parser
    # which has some issues with certain patterns. The transpiler itself works correctly.
    
    def test_parse_and_transpile_simple_formula(self):
        """Test parsing and transpiling a simple formula."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
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
        
        formula = "{fldAmount} * 1.08"
        ast = parse_airtable_formula(formula, metadata)
        
        transpiler = JavaScriptFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert "record.Amount" in result
        assert "1.08" in result
        assert "*" in result
    
    def test_parse_and_transpile_if_formula(self):
        """Test parsing and transpiling IF formula."""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
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
        
        formula = 'IF({fldAmount} > 100, "Large", "Small")'
        ast = parse_airtable_formula(formula, metadata)
        
        transpiler = JavaScriptFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert "record.Amount" in result
        assert "?" in result  # Ternary operator
        assert ":" in result
        assert "'Large'" in result
        assert "'Small'" in result
    
    def test_parse_and_transpile_string_functions(self):
        """Test parsing and transpiling string functions."""
        metadata = {
            "tables": [
                {
                    "id": "tblCustomers",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldName",
                            "name": "Name",
                            "type": "text"
                        }
                    ]
                }
            ]
        }
        
        formula = 'UPPER(LEFT({fldName}, 1)) & LOWER(MID({fldName}, 2, 100))'
        ast = parse_airtable_formula(formula, metadata)
        
        transpiler = JavaScriptFormulaTranspiler()
        result = transpiler.transpile(ast)
        
        assert "toUpperCase()" in result
        assert "toLowerCase()" in result
        assert "substring" in result
        assert "record.Name" in result
