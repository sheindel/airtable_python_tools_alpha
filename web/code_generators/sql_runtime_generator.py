"""
SQL Runtime Generator

Generates PostgreSQL functions, views, and triggers for Airtable computed fields.
Supports two modes:
1. Read-time calculation (functions/views)
2. Write-time calculation (triggers with computed columns)
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.append("web")

from at_formula_parser import (
    FormulaNode,
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode,
    parse_airtable_formula,
)
from at_metadata_graph import get_computation_order, metadata_to_graph
from constants import (
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_RECORD_LINKS,
    COMPUTED_FIELD_TYPES,
)


class SQLFormulaTranspiler:
    """Convert FormulaNode AST to SQL expressions"""

    def __init__(self, table_name: str, metadata: dict):
        """
        Args:
            table_name: Current table being processed
            metadata: Full Airtable metadata
        """
        self.table_name = table_name
        self.metadata = metadata

    def transpile(self, node: FormulaNode) -> str:
        """Convert AST node to SQL expression"""
        if isinstance(node, LiteralNode):
            return self._transpile_literal(node)
        elif isinstance(node, FieldReferenceNode):
            return self._transpile_field_reference(node)
        elif isinstance(node, FunctionCallNode):
            return self._transpile_function_call(node)
        elif isinstance(node, BinaryOpNode):
            return self._transpile_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._transpile_unary_op(node)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")

    def _transpile_literal(self, node: LiteralNode) -> str:
        """Convert literal value to SQL"""
        if node.data_type == "string":
            # Escape single quotes
            escaped = str(node.value).replace("'", "''")
            return f"'{escaped}'"
        elif node.data_type == "boolean":
            return "TRUE" if node.value else "FALSE"
        elif node.data_type == "number":
            return str(node.value)
        elif node.data_type == "null":
            return "NULL"
        else:
            return str(node.value)

    def _transpile_field_reference(self, node: FieldReferenceNode) -> str:
        """
        Convert field reference to SQL column access.
        Uses snake_case column names.
        """
        # Convert field name to snake_case for SQL
        col_name = self._to_snake_case(node.field_name)
        return col_name

    def _transpile_function_call(self, node: FunctionCallNode) -> str:
        """Map Airtable functions to SQL equivalents"""
        func_name = node.function_name.upper()

        # Math functions
        if func_name in ("ROUND", "ABS", "CEILING", "FLOOR", "SQRT", "EXP", "LN", "LOG"):
            args = ", ".join(self.transpile(arg) for arg in node.arguments)
            return f"{func_name}({args})"

        elif func_name == "MOD":
            left = self.transpile(node.arguments[0])
            right = self.transpile(node.arguments[1])
            return f"({left} % {right})"

        elif func_name == "POWER":
            base = self.transpile(node.arguments[0])
            exp = self.transpile(node.arguments[1])
            return f"POWER({base}, {exp})"

        # String functions
        elif func_name in ("CONCATENATE", "&"):
            args = " || ".join(self.transpile(arg) for arg in node.arguments)
            return f"({args})"

        elif func_name == "LEN":
            arg = self.transpile(node.arguments[0])
            return f"LENGTH({arg})"

        elif func_name == "UPPER":
            arg = self.transpile(node.arguments[0])
            return f"UPPER({arg})"

        elif func_name == "LOWER":
            arg = self.transpile(node.arguments[0])
            return f"LOWER({arg})"

        elif func_name == "TRIM":
            arg = self.transpile(node.arguments[0])
            return f"TRIM({arg})"

        elif func_name == "LEFT":
            text = self.transpile(node.arguments[0])
            count = self.transpile(node.arguments[1])
            return f"LEFT({text}, {count})"

        elif func_name == "RIGHT":
            text = self.transpile(node.arguments[0])
            count = self.transpile(node.arguments[1])
            return f"RIGHT({text}, {count})"

        elif func_name == "MID":
            text = self.transpile(node.arguments[0])
            start = self.transpile(node.arguments[1])
            count = self.transpile(node.arguments[2])
            return f"SUBSTRING({text}, {start}, {count})"

        elif func_name == "FIND":
            search = self.transpile(node.arguments[0])
            text = self.transpile(node.arguments[1])
            return f"POSITION({search} IN {text})"

        elif func_name == "SUBSTITUTE":
            text = self.transpile(node.arguments[0])
            old = self.transpile(node.arguments[1])
            new = self.transpile(node.arguments[2])
            return f"REPLACE({text}, {old}, {new})"

        elif func_name == "REPT":
            text = self.transpile(node.arguments[0])
            count = self.transpile(node.arguments[1])
            return f"REPEAT({text}, {count})"

        # Logic functions
        elif func_name == "IF":
            condition = self.transpile(node.arguments[0])
            true_val = self.transpile(node.arguments[1])
            false_val = self.transpile(node.arguments[2]) if len(node.arguments) > 2 else "NULL"
            return f"CASE WHEN {condition} THEN {true_val} ELSE {false_val} END"

        elif func_name == "AND":
            conditions = " AND ".join(f"({self.transpile(arg)})" for arg in node.arguments)
            return f"({conditions})"

        elif func_name == "OR":
            conditions = " OR ".join(f"({self.transpile(arg)})" for arg in node.arguments)
            return f"({conditions})"

        elif func_name == "NOT":
            arg = self.transpile(node.arguments[0])
            return f"NOT ({arg})"

        elif func_name == "BLANK":
            return "NULL"

        elif func_name == "SWITCH":
            # SWITCH(expr, pattern1, result1, pattern2, result2, ..., default)
            expr = self.transpile(node.arguments[0])
            cases = []
            for i in range(1, len(node.arguments) - 1, 2):
                pattern = self.transpile(node.arguments[i])
                result = self.transpile(node.arguments[i + 1])
                cases.append(f"WHEN {expr} = {pattern} THEN {result}")
            default = self.transpile(node.arguments[-1]) if len(node.arguments) % 2 == 0 else "NULL"
            cases_str = " ".join(cases)
            return f"CASE {cases_str} ELSE {default} END"

        # Date functions
        elif func_name == "NOW":
            return "NOW()"

        elif func_name == "TODAY":
            return "CURRENT_DATE"

        elif func_name == "YEAR":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(YEAR FROM {arg})"

        elif func_name == "MONTH":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(MONTH FROM {arg})"

        elif func_name == "DAY":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(DAY FROM {arg})"

        elif func_name == "HOUR":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(HOUR FROM {arg})"

        elif func_name == "MINUTE":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(MINUTE FROM {arg})"

        elif func_name == "SECOND":
            arg = self.transpile(node.arguments[0])
            return f"EXTRACT(SECOND FROM {arg})"

        elif func_name == "DATEADD":
            date = self.transpile(node.arguments[0])
            count = self.transpile(node.arguments[1])
            unit = node.arguments[2].value if isinstance(node.arguments[2], LiteralNode) else "days"
            return f"({date} + INTERVAL '{{{count}}} {unit}')"

        elif func_name == "DATETIME_DIFF":
            date1 = self.transpile(node.arguments[0])
            date2 = self.transpile(node.arguments[1])
            unit = node.arguments[2].value if len(node.arguments) > 2 else "days"
            return f"EXTRACT(EPOCH FROM ({date1} - {date2})) / CASE '{unit}' WHEN 'seconds' THEN 1 WHEN 'minutes' THEN 60 WHEN 'hours' THEN 3600 WHEN 'days' THEN 86400 END"

        # Aggregation functions (for use in subqueries)
        elif func_name in ("SUM", "COUNT", "MAX", "MIN", "AVG"):
            arg = self.transpile(node.arguments[0])
            return f"{func_name}({arg})"

        else:
            # Unknown function - output as comment
            return f"/* Unsupported function: {func_name} */"

    def _transpile_binary_op(self, node: BinaryOpNode) -> str:
        """Convert binary operations to SQL"""
        left = self.transpile(node.left)
        right = self.transpile(node.right)
        op = node.operator

        # Airtable uses & for string concatenation
        if op == "&":
            return f"({left} || {right})"

        # Standard operators
        elif op in ("+", "-", "*", "/", "%", "=", "!=", "<", ">", "<=", ">="):
            sql_op = op if op != "!=" else "<>"
            return f"({left} {sql_op} {right})"

        else:
            return f"({left} {op} {right})"

    def _transpile_unary_op(self, node: UnaryOpNode) -> str:
        """Convert unary operations to SQL"""
        operand = self.transpile(node.operand)

        if node.operator == "-":
            return f"(-{operand})"
        elif node.operator == "NOT":
            return f"NOT ({operand})"
        else:
            return f"{node.operator} {operand}"

    def _to_snake_case(self, name: str) -> str:
        """Convert field name to snake_case for SQL column names"""
        import re

        # Replace spaces and special chars with underscores
        name = re.sub(r"[^\w]+", "_", name)
        # Insert underscore before caps
        name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
        # Convert to lowercase
        return name.lower().strip("_")


class SQLRuntimeGenerator:
    """Generate SQL functions, views, and triggers for computed fields"""

    def __init__(self, metadata: dict, options: Optional[dict] = None):
        """
        Args:
            metadata: Airtable metadata
            options:
                - mode: "functions" | "triggers" (default: "functions")
                - include_views: bool (default: True)
                - schema_name: str (default: "public")
                - null_handling: "strict" | "lenient" (default: "lenient")
        """
        self.metadata = metadata
        self.options = options or {}
        self.mode = self.options.get("mode", "functions")
        self.include_views = self.options.get("include_views", True)
        self.schema_name = self.options.get("schema_name", "public")
        self.null_handling = self.options.get("null_handling", "lenient")

    def generate(self) -> str:
        """Generate complete SQL script"""
        sections = []

        sections.append(self._generate_header())

        if self.mode == "functions":
            sections.append(self._generate_functions())
            if self.include_views:
                sections.append(self._generate_views())
        elif self.mode == "triggers":
            sections.append(self._generate_triggers())

        return "\n\n".join(sections)

    def _generate_header(self) -> str:
        """Generate SQL header comment"""
        from datetime import datetime

        return f"""-- Auto-generated SQL runtime for Airtable computed fields
-- Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
-- Mode: {self.mode}
-- Schema: {self.schema_name}
--
-- This script creates {'functions and views' if self.mode == 'functions' else 'triggers'} for computed fields
-- based on Airtable metadata."""

    def _generate_functions(self) -> str:
        """Generate SQL functions for each computed field"""
        functions = []

        for table in self.metadata.get("tables", []):
            table_name = self._to_snake_case(table["name"])

            for field in table.get("fields", []):
                if field["type"] == FIELD_TYPE_FORMULA:
                    func = self._generate_formula_function(table, field)
                    if func:
                        functions.append(func)
                elif field["type"] == FIELD_TYPE_LOOKUP:
                    func = self._generate_lookup_function(table, field)
                    if func:
                        functions.append(func)
                elif field["type"] == FIELD_TYPE_ROLLUP:
                    func = self._generate_rollup_function(table, field)
                    if func:
                        functions.append(func)

        return "\n\n".join(functions)

    def _generate_formula_function(self, table: dict, field: dict) -> Optional[str]:
        """Generate SQL function for a formula field"""
        try:
            formula = field.get("options", {}).get("formula", "")
            if not formula:
                return None

            table_name = self._to_snake_case(table["name"])
            field_name = self._to_snake_case(field["name"])
            func_name = f"get_{table_name}_{field_name}"

            # Parse formula
            ast = parse_airtable_formula(formula, self.metadata)

            # Transpile to SQL
            transpiler = SQLFormulaTranspiler(table_name, self.metadata)
            sql_expr = transpiler.transpile(ast)

            # Determine return type
            return_type = self._get_sql_type(field)

            # Generate function
            return f"""CREATE OR REPLACE FUNCTION {self.schema_name}.{func_name}(record_id UUID)
RETURNS {return_type} AS $$
  SELECT {sql_expr}
  FROM {self.schema_name}.{table_name}
  WHERE id = record_id;
$$ LANGUAGE SQL IMMUTABLE;"""

        except Exception as e:
            # Return commented error
            return f"""-- Error generating function for {table['name']}.{field['name']}: {str(e)}
-- Formula: {field.get('options', {}).get('formula', 'N/A')}"""

    def _generate_lookup_function(self, table: dict, field: dict) -> Optional[str]:
        """Generate SQL function for a lookup field"""
        try:
            options = field.get("options", {})
            link_field_id = options.get("recordLinkFieldId")
            lookup_field_id = options.get("fieldIdInLinkedTable")

            if not link_field_id or not lookup_field_id:
                return None

            # Find link field
            link_field = next((f for f in table["fields"] if f["id"] == link_field_id), None)
            if not link_field:
                return None

            # Find linked table
            linked_table_id = link_field.get("options", {}).get("linkedTableId")
            linked_table = next((t for t in self.metadata["tables"] if t["id"] == linked_table_id), None)
            if not linked_table:
                return None

            # Find lookup field in linked table
            lookup_field = next((f for f in linked_table["fields"] if f["id"] == lookup_field_id), None)
            if not lookup_field:
                return None

            table_name = self._to_snake_case(table["name"])
            field_name = self._to_snake_case(field["name"])
            func_name = f"get_{table_name}_{field_name}"

            link_col = self._to_snake_case(link_field["name"])
            linked_table_name = self._to_snake_case(linked_table["name"])
            lookup_col = self._to_snake_case(lookup_field["name"])

            return_type = self._get_sql_type(lookup_field)

            return f"""CREATE OR REPLACE FUNCTION {self.schema_name}.{func_name}(record_id UUID)
RETURNS {return_type} AS $$
  SELECT lt.{lookup_col}
  FROM {self.schema_name}.{table_name} t
  JOIN {self.schema_name}.{linked_table_name} lt ON t.{link_col} = lt.id
  WHERE t.id = record_id;
$$ LANGUAGE SQL STABLE;"""

        except Exception as e:
            return f"""-- Error generating lookup function for {table['name']}.{field['name']}: {str(e)}"""

    def _generate_rollup_function(self, table: dict, field: dict) -> Optional[str]:
        """Generate SQL function for a rollup field"""
        try:
            options = field.get("options", {})
            link_field_id = options.get("recordLinkFieldId")
            rollup_field_id = options.get("fieldIdInLinkedTable")
            aggregation = options.get("aggregationFunction", "").upper()

            if not link_field_id or not rollup_field_id:
                return None

            # Find link field
            link_field = next((f for f in table["fields"] if f["id"] == link_field_id), None)
            if not link_field:
                return None

            # Find linked table
            linked_table_id = link_field.get("options", {}).get("linkedTableId")
            linked_table = next((t for t in self.metadata["tables"] if t["id"] == linked_table_id), None)
            if not linked_table:
                return None

            # Find rollup field in linked table
            rollup_field = next((f for f in linked_table["fields"] if f["id"] == rollup_field_id), None)
            if not rollup_field:
                return None

            table_name = self._to_snake_case(table["name"])
            field_name = self._to_snake_case(field["name"])
            func_name = f"get_{table_name}_{field_name}"

            link_col = self._to_snake_case(link_field["name"])
            linked_table_name = self._to_snake_case(linked_table["name"])
            rollup_col = self._to_snake_case(rollup_field["name"])

            # Map Airtable aggregation to SQL
            sql_agg = self._map_aggregation(aggregation, rollup_col)

            return_type = self._get_sql_type(field)

            # Handle multiple record links (array field)
            return f"""CREATE OR REPLACE FUNCTION {self.schema_name}.{func_name}(record_id UUID)
RETURNS {return_type} AS $$
  SELECT {sql_agg}
  FROM {self.schema_name}.{table_name} t
  JOIN {self.schema_name}.{linked_table_name} lt ON lt.id = ANY(t.{link_col})
  WHERE t.id = record_id
  GROUP BY t.id;
$$ LANGUAGE SQL STABLE;"""

        except Exception as e:
            return f"""-- Error generating rollup function for {table['name']}.{field['name']}: {str(e)}"""

    def _generate_views(self) -> str:
        """Generate views that combine base tables with computed fields"""
        views = []

        for table in self.metadata.get("tables", []):
            table_name = self._to_snake_case(table["name"])
            computed_fields = [f for f in table["fields"] if f["type"] in COMPUTED_FIELD_TYPES]

            if not computed_fields:
                continue

            # Build SELECT clause
            select_items = [f"t.*"]

            for field in computed_fields:
                field_name = self._to_snake_case(field["name"])
                func_name = f"get_{table_name}_{field_name}"
                select_items.append(f"{self.schema_name}.{func_name}(t.id) AS {field_name}")

            select_clause = ",\n  ".join(select_items)

            view = f"""CREATE OR REPLACE VIEW {self.schema_name}.{table_name}_with_computed AS
SELECT
  {select_clause}
FROM {self.schema_name}.{table_name} t;"""

            views.append(view)

        return "\n\n".join(views)

    def _generate_triggers(self) -> str:
        """Generate triggers that populate computed columns on INSERT/UPDATE"""
        triggers = []

        # Get computation order
        G = metadata_to_graph(self.metadata)
        computation_order = get_computation_order(self.metadata)

        for table in self.metadata.get("tables", []):
            table_name = self._to_snake_case(table["name"])
            computed_fields = [f for f in table["fields"] if f["type"] in COMPUTED_FIELD_TYPES]

            if not computed_fields:
                continue

            # Generate trigger function
            func_body = []
            func_body.append("BEGIN")

            # Sort fields by depth for correct computation order
            for depth_fields in computation_order:
                for field_id in depth_fields:
                    field = self._find_field_by_id(field_id)
                    if not field or field.get("table_name") != table["name"]:
                        continue

                    if field["type"] == FIELD_TYPE_FORMULA:
                        assignment = self._generate_formula_assignment(table, field)
                        if assignment:
                            func_body.append(f"  {assignment}")

            func_body.append("  RETURN NEW;")
            func_body.append("END;")

            func_name = f"update_{table_name}_computed_fields"
            trigger_name = f"{table_name}_computed_fields_trigger"

            trigger = f"""CREATE OR REPLACE FUNCTION {self.schema_name}.{func_name}()
RETURNS TRIGGER AS $$
{chr(10).join(func_body)}
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS {trigger_name} ON {self.schema_name}.{table_name};

CREATE TRIGGER {trigger_name}
  BEFORE INSERT OR UPDATE ON {self.schema_name}.{table_name}
  FOR EACH ROW
  EXECUTE FUNCTION {self.schema_name}.{func_name}();"""

            triggers.append(trigger)

        return "\n\n".join(triggers)

    def _generate_formula_assignment(self, table: dict, field: dict) -> Optional[str]:
        """Generate NEW.field := expression for trigger"""
        try:
            formula = field.get("options", {}).get("formula", "")
            if not formula:
                return None

            field_name = self._to_snake_case(field["name"])
            table_name = self._to_snake_case(table["name"])

            # Parse and transpile formula
            ast = parse_airtable_formula(formula, self.metadata)
            transpiler = SQLFormulaTranspiler(table_name, self.metadata)
            sql_expr = transpiler.transpile(ast)

            # Replace column references with NEW.column
            sql_expr = sql_expr.replace("record.", "NEW.")

            return f"NEW.{field_name} := {sql_expr};"

        except Exception as e:
            return f"-- Error: {str(e)}"

    def _find_field_by_id(self, field_id: str) -> Optional[dict]:
        """Find field by ID across all tables"""
        for table in self.metadata.get("tables", []):
            for field in table.get("fields", []):
                if field["id"] == field_id:
                    # Add table name for context
                    field_copy = field.copy()
                    field_copy["table_name"] = table["name"]
                    return field_copy
        return None

    def _get_sql_type(self, field: dict) -> str:
        """Map Airtable field type to SQL type"""
        field_type = field["type"]

        if field_type in ("number", "formula"):
            # Check if it's an integer or decimal
            options = field.get("options", {})
            precision = options.get("precision", 0)
            if precision == 0:
                return "INTEGER"
            else:
                return "DECIMAL(18, 6)"

        elif field_type in ("singleLineText", "multilineText", "richText", "email", "url", "phoneNumber"):
            return "TEXT"

        elif field_type == "checkbox":
            return "BOOLEAN"

        elif field_type in ("date", "dateTime", "createdTime", "lastModifiedTime"):
            return "TIMESTAMP"

        elif field_type == "singleSelect":
            return "TEXT"

        elif field_type in ("multipleSelects",):
            return "TEXT[]"

        elif field_type in ("multipleLookupValues", FIELD_TYPE_RECORD_LINKS):
            return "TEXT[]"

        else:
            return "TEXT"  # Default fallback

    def _map_aggregation(self, airtable_agg: str, column: str) -> str:
        """Map Airtable aggregation function to SQL"""
        agg_map = {
            "SUM": f"COALESCE(SUM({column}), 0)",
            "COUNT": f"COUNT({column})",
            "MAX": f"MAX({column})",
            "MIN": f"MIN({column})",
            "AVERAGE": f"AVG({column})",
            "COUNTALL": "COUNT(*)",
        }

        return agg_map.get(airtable_agg, f"/* Unsupported aggregation: {airtable_agg} */")

    def _to_snake_case(self, name: str) -> str:
        """Convert name to snake_case for SQL identifiers"""
        import re

        name = re.sub(r"[^\w]+", "_", name)
        name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
        return name.lower().strip("_")


def generate_sql_runtime(metadata: dict, options: Optional[dict] = None) -> str:
    """
    Generate SQL runtime code for Airtable computed fields.

    Args:
        metadata: Airtable metadata
        options:
            - mode: "functions" | "triggers" (default: "functions")
            - include_views: bool (default: True)
            - schema_name: str (default: "public")
            - null_handling: "strict" | "lenient" (default: "lenient")

    Returns:
        Complete SQL script
    """
    generator = SQLRuntimeGenerator(metadata, options)
    return generator.generate()


def generate_all_sql_files(
    metadata: dict,
    mode: str = "functions",
    dialect: str = "postgresql",
    include_formulas: bool = True,
    include_views: bool = True
) -> dict:
    """
    Generate SQL files for web UI integration.
    
    Args:
        metadata: Airtable metadata
        mode: "functions" or "triggers"
        dialect: SQL dialect (currently only "postgresql" supported)
        include_formulas: Whether to include computed field logic
        include_views: Whether to generate views
    
    Returns:
        Dictionary of {filename: content}
    """
    if dialect != "postgresql":
        raise ValueError(f"Unsupported SQL dialect: {dialect}. Only 'postgresql' is currently supported.")
    
    options = {
        "mode": mode,
        "include_views": include_views,
        "schema_name": "public",
        "null_handling": "lenient"
    }
    
    # Generate SQL script
    sql_content = generate_sql_runtime(metadata, options)
    
    # Determine filename based on mode
    filename = f"airtable_computed_{mode}.sql"
    
    return {filename: sql_content}
