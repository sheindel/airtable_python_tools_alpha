"""Tests for SQL Runtime Generator"""

import sys
from pathlib import Path

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

import pytest
from code_generators.sql_runtime_generator import (
    SQLFormulaTranspiler,
    SQLRuntimeGenerator,
    generate_sql_runtime,
)
from at_formula_parser import (
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode,
)
from constants import FIELD_TYPE_FORMULA, FIELD_TYPE_LOOKUP, FIELD_TYPE_ROLLUP


class TestSQLFormulaTranspiler:
    """Test SQL formula transpilation"""

    def test_transpile_literal_string(self):
        """Test string literal transpilation"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = LiteralNode(value="hello", data_type="string")
        result = transpiler.transpile(node)
        assert result == "'hello'"

    def test_transpile_literal_number(self):
        """Test number literal transpilation"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = LiteralNode(value=42, data_type="number")
        result = transpiler.transpile(node)
        assert result == "42"

    def test_transpile_literal_boolean(self):
        """Test boolean literal transpilation"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node_true = LiteralNode(value=True, data_type="boolean")
        node_false = LiteralNode(value=False, data_type="boolean")
        assert transpiler.transpile(node_true) == "TRUE"
        assert transpiler.transpile(node_false) == "FALSE"

    def test_transpile_field_reference(self):
        """Test field reference transpilation"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FieldReferenceNode(
            field_id="fldXXX",
            field_name="Order Amount",
            field_type="number",
        )
        result = transpiler.transpile(node)
        assert result == "order_amount"

    def test_transpile_binary_op_addition(self):
        """Test addition operator"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = BinaryOpNode(
            operator="+",
            left=LiteralNode(value=10, data_type="number"),
            right=LiteralNode(value=20, data_type="number"),
        )
        result = transpiler.transpile(node)
        assert result == "(10 + 20)"

    def test_transpile_binary_op_concatenation(self):
        """Test string concatenation with &"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = BinaryOpNode(
            operator="&",
            left=LiteralNode(value="Hello", data_type="string"),
            right=LiteralNode(value="World", data_type="string"),
        )
        result = transpiler.transpile(node)
        assert result == "('Hello' || 'World')"

    def test_transpile_binary_op_not_equal(self):
        """Test != operator converts to <>"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = BinaryOpNode(
            operator="!=",
            left=LiteralNode(value=1, data_type="number"),
            right=LiteralNode(value=2, data_type="number"),
        )
        result = transpiler.transpile(node)
        assert result == "(1 <> 2)"

    def test_transpile_unary_op_negation(self):
        """Test unary negation"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = UnaryOpNode(
            operator="-",
            operand=LiteralNode(value=42, data_type="number"),
        )
        result = transpiler.transpile(node)
        assert result == "(-42)"

    def test_transpile_unary_op_not(self):
        """Test logical NOT"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = UnaryOpNode(
            operator="NOT",
            operand=LiteralNode(value=True, data_type="boolean"),
        )
        result = transpiler.transpile(node)
        assert result == "NOT (TRUE)"

    def test_transpile_function_round(self):
        """Test ROUND function"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="ROUND",
            arguments=[
                LiteralNode(value=3.14159, data_type="number"),
                LiteralNode(value=2, data_type="number"),
            ],
        )
        result = transpiler.transpile(node)
        assert result == "ROUND(3.14159, 2)"

    def test_transpile_function_if(self):
        """Test IF function converts to CASE"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="IF",
            arguments=[
                BinaryOpNode(
                    operator=">",
                    left=LiteralNode(value=100, data_type="number"),
                    right=LiteralNode(value=50, data_type="number"),
                ),
                LiteralNode(value="High", data_type="string"),
                LiteralNode(value="Low", data_type="string"),
            ],
        )
        result = transpiler.transpile(node)
        assert "CASE WHEN" in result
        assert "THEN 'High'" in result
        assert "ELSE 'Low'" in result

    def test_transpile_function_concatenate(self):
        """Test CONCATENATE function"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="CONCATENATE",
            arguments=[
                LiteralNode(value="Hello", data_type="string"),
                LiteralNode(value=" ", data_type="string"),
                LiteralNode(value="World", data_type="string"),
            ],
        )
        result = transpiler.transpile(node)
        assert result == "('Hello' || ' ' || 'World')"

    def test_transpile_function_len(self):
        """Test LEN function converts to LENGTH"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="LEN",
            arguments=[LiteralNode(value="hello", data_type="string")],
        )
        result = transpiler.transpile(node)
        assert result == "LENGTH('hello')"

    def test_transpile_function_upper_lower(self):
        """Test UPPER and LOWER functions"""
        transpiler = SQLFormulaTranspiler("orders", {})

        upper_node = FunctionCallNode(
            function_name="UPPER",
            arguments=[LiteralNode(value="hello", data_type="string")],
        )
        assert transpiler.transpile(upper_node) == "UPPER('hello')"

        lower_node = FunctionCallNode(
            function_name="LOWER",
            arguments=[LiteralNode(value="HELLO", data_type="string")],
        )
        assert transpiler.transpile(lower_node) == "LOWER('HELLO')"

    def test_transpile_function_and_or(self):
        """Test AND and OR functions"""
        transpiler = SQLFormulaTranspiler("orders", {})

        and_node = FunctionCallNode(
            function_name="AND",
            arguments=[
                LiteralNode(value=True, data_type="boolean"),
                LiteralNode(value=False, data_type="boolean"),
            ],
        )
        result = transpiler.transpile(and_node)
        assert "(TRUE) AND (FALSE)" in result

        or_node = FunctionCallNode(
            function_name="OR",
            arguments=[
                LiteralNode(value=True, data_type="boolean"),
                LiteralNode(value=False, data_type="boolean"),
            ],
        )
        result = transpiler.transpile(or_node)
        assert "(TRUE) OR (FALSE)" in result

    def test_transpile_function_mod(self):
        """Test MOD function converts to %"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="MOD",
            arguments=[
                LiteralNode(value=10, data_type="number"),
                LiteralNode(value=3, data_type="number"),
            ],
        )
        result = transpiler.transpile(node)
        assert result == "(10 % 3)"

    def test_transpile_function_substitute(self):
        """Test SUBSTITUTE converts to REPLACE"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="SUBSTITUTE",
            arguments=[
                LiteralNode(value="hello world", data_type="string"),
                LiteralNode(value="world", data_type="string"),
                LiteralNode(value="SQL", data_type="string"),
            ],
        )
        result = transpiler.transpile(node)
        assert result == "REPLACE('hello world', 'world', 'SQL')"

    def test_transpile_function_switch(self):
        """Test SWITCH function converts to CASE"""
        transpiler = SQLFormulaTranspiler("orders", {})
        node = FunctionCallNode(
            function_name="SWITCH",
            arguments=[
                LiteralNode(value="status", data_type="string"),
                LiteralNode(value="active", data_type="string"),
                LiteralNode(value=1, data_type="number"),
                LiteralNode(value="inactive", data_type="string"),
                LiteralNode(value=0, data_type="number"),
                LiteralNode(value=-1, data_type="number"),
            ],
        )
        result = transpiler.transpile(node)
        assert "CASE" in result
        assert "WHEN 'status' = 'active' THEN 1" in result
        assert "ELSE -1" in result

    def test_transpile_date_functions(self):
        """Test date extraction functions"""
        transpiler = SQLFormulaTranspiler("orders", {})

        # NOW and TODAY
        now_node = FunctionCallNode(
            function_name="NOW", arguments=[]
        )
        assert transpiler.transpile(now_node) == "NOW()"

        today_node = FunctionCallNode(
            function_name="TODAY", arguments=[]
        )
        assert transpiler.transpile(today_node) == "CURRENT_DATE"

    def test_to_snake_case(self):
        """Test snake_case conversion"""
        transpiler = SQLFormulaTranspiler("orders", {})

        assert transpiler._to_snake_case("OrderAmount") == "order_amount"
        assert transpiler._to_snake_case("Total Revenue") == "total_revenue"
        assert transpiler._to_snake_case("Customer ID") == "customer_id"
        assert transpiler._to_snake_case("email-address") == "email_address"


class TestSQLRuntimeGenerator:
    """Test SQL runtime generator"""

    @pytest.fixture
    def simple_metadata(self):
        """Simple metadata with a formula field"""
        return {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number",
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} * 0.08",
                            },
                        },
                        {
                            "id": "fldTotal",
                            "name": "Total",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": "{fldAmount} + {fldTax}",
                            },
                        },
                    ],
                }
            ]
        }

    @pytest.fixture
    def lookup_metadata(self):
        """Metadata with lookup field"""
        return {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldCustomer",
                            "name": "Customer",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tblCustomers",
                            },
                        },
                        {
                            "id": "fldCustomerEmail",
                            "name": "Customer Email",
                            "type": FIELD_TYPE_LOOKUP,
                            "options": {
                                "recordLinkFieldId": "fldCustomer",
                                "fieldIdInLinkedTable": "fldEmail",
                            },
                        },
                    ],
                },
                {
                    "id": "tblCustomers",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldEmail",
                            "name": "Email",
                            "type": "email",
                        },
                    ],
                },
            ]
        }

    @pytest.fixture
    def rollup_metadata(self):
        """Metadata with rollup field"""
        return {
            "tables": [
                {
                    "id": "tblCustomers",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fldOrders",
                            "name": "Orders",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tblOrders",
                            },
                        },
                        {
                            "id": "fldTotalRevenue",
                            "name": "Total Revenue",
                            "type": FIELD_TYPE_ROLLUP,
                            "options": {
                                "recordLinkFieldId": "fldOrders",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "SUM",
                            },
                        },
                    ],
                },
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "number",
                        },
                    ],
                },
            ]
        }

    def test_generate_header(self, simple_metadata):
        """Test SQL header generation"""
        generator = SQLRuntimeGenerator(simple_metadata)
        header = generator._generate_header()

        assert "Auto-generated SQL runtime" in header
        assert "Generated:" in header
        assert "Mode: functions" in header

    def test_generate_formula_function(self, simple_metadata):
        """Test formula function generation"""
        generator = SQLRuntimeGenerator(simple_metadata, {"mode": "functions"})
        table = simple_metadata["tables"][0]
        field = table["fields"][1]  # Tax field

        result = generator._generate_formula_function(table, field)

        assert result is not None
        assert "CREATE OR REPLACE FUNCTION" in result
        assert "get_orders_tax" in result
        assert "RETURNS" in result
        assert "amount * 0.08" in result.lower()

    def test_generate_lookup_function(self, lookup_metadata):
        """Test lookup function generation"""
        generator = SQLRuntimeGenerator(lookup_metadata, {"mode": "functions"})
        table = lookup_metadata["tables"][0]
        field = table["fields"][1]  # Customer Email lookup

        result = generator._generate_lookup_function(table, field)

        assert result is not None
        assert "CREATE OR REPLACE FUNCTION" in result
        assert "get_orders_customer_email" in result
        assert "JOIN" in result
        assert "customers" in result

    def test_generate_rollup_function(self, rollup_metadata):
        """Test rollup function generation"""
        generator = SQLRuntimeGenerator(rollup_metadata, {"mode": "functions"})
        table = rollup_metadata["tables"][0]
        field = table["fields"][1]  # Total Revenue rollup

        result = generator._generate_rollup_function(table, field)

        assert result is not None
        assert "CREATE OR REPLACE FUNCTION" in result
        assert "get_customers_total_revenue" in result
        assert "SUM" in result
        assert "GROUP BY" in result

    def test_generate_view(self, simple_metadata):
        """Test view generation"""
        generator = SQLRuntimeGenerator(simple_metadata, {"mode": "functions", "include_views": True})
        views = generator._generate_views()

        assert "CREATE OR REPLACE VIEW" in views
        assert "orders_with_computed" in views
        assert "get_orders_tax" in views
        assert "get_orders_total" in views

    def test_get_sql_type(self, simple_metadata):
        """Test SQL type mapping"""
        generator = SQLRuntimeGenerator(simple_metadata)

        # Number field
        number_field = {"type": "number", "options": {"precision": 0}}
        assert generator._get_sql_type(number_field) == "INTEGER"

        # Decimal field
        decimal_field = {"type": "number", "options": {"precision": 2}}
        assert generator._get_sql_type(decimal_field) == "DECIMAL(18, 6)"

        # Text field
        text_field = {"type": "singleLineText"}
        assert generator._get_sql_type(text_field) == "TEXT"

        # Boolean field
        bool_field = {"type": "checkbox"}
        assert generator._get_sql_type(bool_field) == "BOOLEAN"

    def test_map_aggregation(self, simple_metadata):
        """Test aggregation function mapping"""
        generator = SQLRuntimeGenerator(simple_metadata)

        assert "SUM(amount)" in generator._map_aggregation("SUM", "amount")
        assert "COUNT(amount)" in generator._map_aggregation("COUNT", "amount")
        assert "MAX(amount)" in generator._map_aggregation("MAX", "amount")
        assert "AVG(amount)" in generator._map_aggregation("AVERAGE", "amount")

    def test_generate_full_functions_script(self, simple_metadata):
        """Test full SQL script generation in functions mode"""
        result = generate_sql_runtime(simple_metadata, {"mode": "functions", "include_views": True})

        # Should contain header
        assert "Auto-generated SQL runtime" in result

        # Should contain formula functions
        assert "get_orders_tax" in result
        assert "get_orders_total" in result

        # Should contain view
        assert "orders_with_computed" in result

    def test_generate_with_custom_schema(self, simple_metadata):
        """Test generation with custom schema name"""
        result = generate_sql_runtime(simple_metadata, {"schema_name": "analytics"})

        assert "analytics.get_orders_tax" in result
        assert "analytics.orders" in result

    def test_to_snake_case(self, simple_metadata):
        """Test snake_case conversion"""
        generator = SQLRuntimeGenerator(simple_metadata)

        assert generator._to_snake_case("OrderAmount") == "order_amount"
        assert generator._to_snake_case("Total Revenue") == "total_revenue"
        assert generator._to_snake_case("customer-id") == "customer_id"

    def test_find_field_by_id(self, simple_metadata):
        """Test finding field by ID"""
        generator = SQLRuntimeGenerator(simple_metadata)

        field = generator._find_field_by_id("fldAmount")
        assert field is not None
        assert field["name"] == "Amount"
        assert field["table_name"] == "Orders"

        # Non-existent field
        assert generator._find_field_by_id("fldNonExistent") is None


class TestSQLIntegration:
    """Integration tests with real-world-like metadata"""

    def test_complex_formula_chain(self):
        """Test complex formula dependencies"""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {"id": "fldQty", "name": "Quantity", "type": "number"},
                        {"id": "fldPrice", "name": "Price", "type": "number"},
                        {
                            "id": "fldSubtotal",
                            "name": "Subtotal",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {"formula": "{fldQty} * {fldPrice}"},
                        },
                        {
                            "id": "fldTax",
                            "name": "Tax",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {"formula": "{fldSubtotal} * 0.08"},
                        },
                        {
                            "id": "fldTotal",
                            "name": "Total",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {"formula": "{fldSubtotal} + {fldTax}"},
                        },
                    ],
                }
            ]
        }

        result = generate_sql_runtime(metadata, {"mode": "functions"})

        # All three computed fields should be generated
        assert "get_orders_subtotal" in result
        assert "get_orders_tax" in result
        assert "get_orders_total" in result

        # Check formulas are correct
        assert "quantity * price" in result
        # Note: tax and total will reference column names directly in functions mode

    def test_if_function_with_comparison(self):
        """Test IF function with comparison operators"""
        metadata = {
            "tables": [
                {
                    "id": "tblOrders",
                    "name": "Orders",
                    "fields": [
                        {"id": "fldAmount", "name": "Amount", "type": "number"},
                        {
                            "id": "fldStatus",
                            "name": "Status",
                            "type": FIELD_TYPE_FORMULA,
                            "options": {
                                "formula": 'IF({fldAmount} > 100, "High", "Low")',
                            },
                        },
                    ],
                }
            ]
        }

        result = generate_sql_runtime(metadata, {"mode": "functions"})

        assert "CASE WHEN" in result
        assert "amount > 100" in result
        assert "'High'" in result
        assert "'Low'" in result
