"""Python runtime code generator for Airtable formulas.

This module converts Airtable formula ASTs into executable Python code.
Supports formulas, lookups, rollups, and generates complete Python libraries.
"""

import sys
sys.path.append("web")

from typing import Optional, List, Dict, Any
from datetime import datetime
import re

from at_formula_parser import (
    FormulaNode,
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode,
    parse_airtable_formula,
)
from at_metadata_graph import (
    get_computation_order_with_metadata,
)
from constants import (
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_COUNT,
    FIELD_TYPE_RECORD_LINKS,
)


class PythonFormulaTranspiler:
    """Convert FormulaNode AST to Python code."""
    
    # Mapping of Airtable operators to Python operators
    OPERATOR_MAP = {
        '+': '+',
        '-': '-',
        '*': '*',
        '/': '/',
        '&': '+',  # String concatenation
        '=': '==',
        '!=': '!=',
        '<': '<',
        '>': '>',
        '<=': '<=',
        '>=': '>=',
    }
    
    def __init__(self, data_access_mode: str = "dataclass", include_null_checks: bool = True):
        """
        Initialize the transpiler.
        
        Args:
            data_access_mode: How to access record fields
                - "dataclass": record.field_name
                - "dict": record["field_name"]
                - "orm": record.field_name (SQLAlchemy-style)
            include_null_checks: Whether to add null safety checks
        """
        self.data_access_mode = data_access_mode
        self.include_null_checks = include_null_checks
    
    def transpile(self, node: FormulaNode) -> str:
        """
        Convert AST node to Python expression.
        
        Args:
            node: AST node to transpile
            
        Returns:
            Python code string
        """
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
        """Transpile literal values."""
        if node.data_type == "string":
            # Escape single quotes and wrap in double quotes for consistency
            escaped = str(node.value).replace('"', '\\"')
            return f'"{escaped}"'
        elif node.data_type == "boolean":
            return "True" if node.value else "False"
        elif node.data_type == "number":
            return str(node.value)
        else:
            return str(node.value)
    
    def _transpile_field_reference(self, node: FieldReferenceNode) -> str:
        """
        Convert field reference to data access pattern.
        
        Returns code like:
        - dataclass: record.customer_name
        - dict: record["customer_name"]
        - orm: record.customer_name
        """
        field_name = self._sanitize_field_name(node.field_name)
        
        if self.data_access_mode == "dict":
            return f'record["{field_name}"]'
        else:  # dataclass or orm
            return f"record.{field_name}"
    
    def _transpile_function_call(self, node: FunctionCallNode) -> str:
        """
        Map Airtable functions to Python equivalents.
        
        Handles 20+ common Airtable functions.
        """
        func_name = node.function_name.upper()
        args = [self.transpile(arg) for arg in node.arguments]
        
        # Logic functions
        if func_name == "IF":
            return self._transpile_if(args)
        elif func_name == "AND":
            return self._transpile_and(args)
        elif func_name == "OR":
            return self._transpile_or(args)
        elif func_name == "NOT":
            return f"(not {args[0]})"
        elif func_name == "BLANK":
            return self._transpile_blank(args)
        elif func_name == "XOR":
            return self._transpile_xor(args)
        
        # String functions
        elif func_name == "CONCATENATE":
            return self._transpile_concatenate(args)
        elif func_name == "LEN":
            return f"len(str({args[0]}) if {args[0]} is not None else '')"
        elif func_name == "UPPER":
            return f"(str({args[0]}).upper() if {args[0]} is not None else '')"
        elif func_name == "LOWER":
            return f"(str({args[0]}).lower() if {args[0]} is not None else '')"
        elif func_name == "TRIM":
            return f"(str({args[0]}).strip() if {args[0]} is not None else '')"
        elif func_name == "LEFT":
            return self._transpile_left(args)
        elif func_name == "RIGHT":
            return self._transpile_right(args)
        elif func_name == "MID":
            return self._transpile_mid(args)
        elif func_name == "FIND":
            return self._transpile_find(args)
        elif func_name == "SUBSTITUTE":
            return self._transpile_substitute(args)
        elif func_name == "REPLACE":
            return self._transpile_replace(args)
        elif func_name == "REPT":
            return self._transpile_rept(args)
        
        # Math functions
        elif func_name == "ROUND":
            return self._transpile_round(args)
        elif func_name == "ABS":
            return f"abs({args[0]})"
        elif func_name == "MOD":
            return f"({args[0]} % {args[1]})"
        elif func_name == "CEILING":
            return f"math.ceil({args[0]})"
        elif func_name == "FLOOR":
            return f"math.floor({args[0]})"
        elif func_name == "SQRT":
            return f"math.sqrt({args[0]})"
        elif func_name == "POWER":
            return f"pow({args[0]}, {args[1]})"
        elif func_name == "EXP":
            return f"math.exp({args[0]})"
        elif func_name == "LOG":
            return self._transpile_log(args)
        elif func_name == "MAX":
            return self._transpile_max(args)
        elif func_name == "MIN":
            return self._transpile_min(args)
        
        # Date functions
        elif func_name == "NOW":
            return "datetime.datetime.now()"
        elif func_name == "TODAY":
            return "datetime.date.today()"
        elif func_name == "YEAR":
            return self._transpile_year(args)
        elif func_name == "MONTH":
            return self._transpile_month(args)
        elif func_name == "DAY":
            return self._transpile_day(args)
        elif func_name == "HOUR":
            return self._transpile_hour(args)
        elif func_name == "MINUTE":
            return self._transpile_minute(args)
        elif func_name == "SECOND":
            return self._transpile_second(args)
        elif func_name == "WEEKDAY":
            return self._transpile_weekday(args)
        
        # Array functions
        elif func_name == "ARRAYCOMPACT":
            return self._transpile_arraycompact(args)
        elif func_name == "ARRAYFLATTEN":
            return self._transpile_arrayflatten(args)
        elif func_name == "ARRAYUNIQUE":
            return self._transpile_arrayunique(args)
        
        else:
            # Fallback: generate function call with warning comment
            args_str = ", ".join(args)
            return f"_unsupported_function_{func_name.lower()}({args_str})"
    
    def _transpile_if(self, args: List[str]) -> str:
        """Transpile IF(condition, true_val, false_val)."""
        if len(args) == 2:
            # IF with only condition and true value (false defaults to None/empty)
            return f"({args[1]} if {args[0]} else None)"
        elif len(args) == 3:
            return f"({args[1]} if {args[0]} else {args[2]})"
        else:
            raise ValueError(f"IF requires 2 or 3 arguments, got {len(args)}")
    
    def _transpile_and(self, args: List[str]) -> str:
        """Transpile AND(arg1, arg2, ...)."""
        return f"({' and '.join(args)})"
    
    def _transpile_or(self, args: List[str]) -> str:
        """Transpile OR(arg1, arg2, ...)."""
        return f"({' or '.join(args)})"
    
    def _transpile_blank(self, args: List[str]) -> str:
        """Transpile BLANK() - returns if value is empty/None."""
        if len(args) == 0:
            return "None"
        else:
            # BLANK(value) checks if value is blank
            return f"({args[0]} is None or {args[0]} == '')"
    
    def _transpile_xor(self, args: List[str]) -> str:
        """Transpile XOR(arg1, arg2)."""
        if len(args) == 2:
            return f"(bool({args[0]}) != bool({args[1]}))"
        else:
            # Multiple args: chain XOR operations
            result = f"bool({args[0]})"
            for arg in args[1:]:
                result = f"({result} != bool({arg}))"
            return result
    
    def _transpile_concatenate(self, args: List[str]) -> str:
        """Transpile CONCATENATE(str1, str2, ...)."""
        # Convert all args to strings and concatenate
        str_args = [f"str({arg}) if {arg} is not None else ''" for arg in args]
        return f"({' + '.join(str_args)})"
    
    def _transpile_left(self, args: List[str]) -> str:
        """Transpile LEFT(string, count)."""
        if len(args) == 2:
            return f"(str({args[0]})[:int({args[1]})] if {args[0]} is not None else '')"
        else:
            raise ValueError(f"LEFT requires 2 arguments, got {len(args)}")
    
    def _transpile_right(self, args: List[str]) -> str:
        """Transpile RIGHT(string, count)."""
        if len(args) == 2:
            return f"(str({args[0]})[-int({args[1]}):] if {args[0]} is not None else '')"
        else:
            raise ValueError(f"RIGHT requires 2 arguments, got {len(args)}")
    
    def _transpile_mid(self, args: List[str]) -> str:
        """Transpile MID(string, start, count)."""
        if len(args) == 3:
            # Airtable uses 1-based indexing, Python uses 0-based
            return f"(str({args[0]})[int({args[1]})-1:int({args[1]})-1+int({args[2]})] if {args[0]} is not None else '')"
        else:
            raise ValueError(f"MID requires 3 arguments, got {len(args)}")
    
    def _transpile_find(self, args: List[str]) -> str:
        """Transpile FIND(search_for, where_to_search, [start_from])."""
        if len(args) == 2:
            # Returns 1-based position or 0 if not found (Airtable convention)
            return f"(str({args[1]}).find(str({args[0]})) + 1 if {args[1]} is not None else 0)"
        elif len(args) == 3:
            # With start position (convert from 1-based to 0-based)
            return f"(str({args[1]}).find(str({args[0]}), int({args[2]})-1) + 1 if {args[1]} is not None else 0)"
        else:
            raise ValueError(f"FIND requires 2 or 3 arguments, got {len(args)}")
    
    def _transpile_substitute(self, args: List[str]) -> str:
        """Transpile SUBSTITUTE(text, old_text, new_text, [index])."""
        if len(args) == 3:
            return f"(str({args[0]}).replace(str({args[1]}), str({args[2]})) if {args[0]} is not None else '')"
        elif len(args) == 4:
            # With index - replace only the nth occurrence
            return f"_substitute_nth(str({args[0]}) if {args[0]} is not None else '', str({args[1]}), str({args[2]}), int({args[3]}))"
        else:
            raise ValueError(f"SUBSTITUTE requires 3 or 4 arguments, got {len(args)}")
    
    def _transpile_replace(self, args: List[str]) -> str:
        """Transpile REPLACE(text, start, length, replacement)."""
        if len(args) == 4:
            # Airtable uses 1-based indexing
            return f"(str({args[0]})[:int({args[1]})-1] + str({args[3]}) + str({args[0]})[int({args[1]})-1+int({args[2]}):] if {args[0]} is not None else '')"
        else:
            raise ValueError(f"REPLACE requires 4 arguments, got {len(args)}")
    
    def _transpile_rept(self, args: List[str]) -> str:
        """Transpile REPT(text, count)."""
        if len(args) == 2:
            return f"(str({args[0]}) * int({args[1]}) if {args[0]} is not None else '')"
        else:
            raise ValueError(f"REPT requires 2 arguments, got {len(args)}")
    
    def _transpile_round(self, args: List[str]) -> str:
        """Transpile ROUND(number, [precision])."""
        if len(args) == 1:
            return f"round({args[0]})"
        elif len(args) == 2:
            return f"round({args[0]}, int({args[1]}))"
        else:
            raise ValueError(f"ROUND requires 1 or 2 arguments, got {len(args)}")
    
    def _transpile_log(self, args: List[str]) -> str:
        """Transpile LOG(number, [base])."""
        if len(args) == 1:
            return f"math.log({args[0]})"  # Natural log
        elif len(args) == 2:
            return f"math.log({args[0]}, {args[1]})"
        else:
            raise ValueError(f"LOG requires 1 or 2 arguments, got {len(args)}")
    
    def _transpile_max(self, args: List[str]) -> str:
        """Transpile MAX(num1, num2, ...)."""
        return f"max({', '.join(args)})"
    
    def _transpile_min(self, args: List[str]) -> str:
        """Transpile MIN(num1, num2, ...)."""
        return f"min({', '.join(args)})"
    
    def _transpile_year(self, args: List[str]) -> str:
        """Transpile YEAR(date)."""
        if len(args) == 1:
            return f"({args[0]}.year if {args[0]} is not None else None)"
        else:
            raise ValueError(f"YEAR requires 1 argument, got {len(args)}")
    
    def _transpile_month(self, args: List[str]) -> str:
        """Transpile MONTH(date)."""
        if len(args) == 1:
            return f"({args[0]}.month if {args[0]} is not None else None)"
        else:
            raise ValueError(f"MONTH requires 1 argument, got {len(args)}")
    
    def _transpile_day(self, args: List[str]) -> str:
        """Transpile DAY(date)."""
        if len(args) == 1:
            return f"({args[0]}.day if {args[0]} is not None else None)"
        else:
            raise ValueError(f"DAY requires 1 argument, got {len(args)}")
    
    def _transpile_hour(self, args: List[str]) -> str:
        """Transpile HOUR(datetime)."""
        if len(args) == 1:
            return f"({args[0]}.hour if {args[0]} is not None else None)"
        else:
            raise ValueError(f"HOUR requires 1 argument, got {len(args)}")
    
    def _transpile_minute(self, args: List[str]) -> str:
        """Transpile MINUTE(datetime)."""
        if len(args) == 1:
            return f"({args[0]}.minute if {args[0]} is not None else None)"
        else:
            raise ValueError(f"MINUTE requires 1 argument, got {len(args)}")
    
    def _transpile_second(self, args: List[str]) -> str:
        """Transpile SECOND(datetime)."""
        if len(args) == 1:
            return f"({args[0]}.second if {args[0]} is not None else None)"
        else:
            raise ValueError(f"SECOND requires 1 argument, got {len(args)}")
    
    def _transpile_weekday(self, args: List[str]) -> str:
        """Transpile WEEKDAY(date)."""
        if len(args) == 1:
            # Airtable: Sunday=0, Python: Monday=0
            # Convert Python's weekday to Airtable's format
            return f"(({args[0]}.weekday() + 1) % 7 if {args[0]} is not None else None)"
        else:
            raise ValueError(f"WEEKDAY requires 1 argument, got {len(args)}")
    
    def _transpile_arraycompact(self, args: List[str]) -> str:
        """Transpile ARRAYCOMPACT(array) - removes empty values."""
        if len(args) == 1:
            return f"[x for x in {args[0]} if x is not None and x != '']"
        else:
            raise ValueError(f"ARRAYCOMPACT requires 1 argument, got {len(args)}")
    
    def _transpile_arrayflatten(self, args: List[str]) -> str:
        """Transpile ARRAYFLATTEN(array) - flattens nested arrays."""
        if len(args) == 1:
            return f"_flatten_array({args[0]})"
        else:
            raise ValueError(f"ARRAYFLATTEN requires 1 argument, got {len(args)}")
    
    def _transpile_arrayunique(self, args: List[str]) -> str:
        """Transpile ARRAYUNIQUE(array) - removes duplicates."""
        if len(args) == 1:
            return f"list(dict.fromkeys({args[0]}))"  # Preserves order
        else:
            raise ValueError(f"ARRAYUNIQUE requires 1 argument, got {len(args)}")
    
    def _transpile_binary_op(self, node: BinaryOpNode) -> str:
        """Transpile binary operations."""
        left = self.transpile(node.left)
        right = self.transpile(node.right)
        op = self.OPERATOR_MAP.get(node.operator, node.operator)
        
        # Handle string concatenation (&)
        if node.operator == '&':
            # Convert to strings before concatenation
            left = f"str({left}) if {left} is not None else ''"
            right = f"str({right}) if {right} is not None else ''"
        
        return f"({left} {op} {right})"
    
    def _transpile_unary_op(self, node: UnaryOpNode) -> str:
        """Transpile unary operations."""
        operand = self.transpile(node.operand)
        
        if node.operator == '-':
            return f"(-{operand})"
        elif node.operator.upper() == 'NOT':
            return f"(not {operand})"
        else:
            raise ValueError(f"Unknown unary operator: {node.operator}")
    
    @staticmethod
    def _sanitize_field_name(field_name: str) -> str:
        """
        Convert field name to valid Python identifier.
        
        Examples:
        - "Customer Name" -> "customer_name"
        - "Total $ Value" -> "total_value"
        - "2023 Revenue" -> "_2023_revenue"
        """
        # Convert to lowercase and replace spaces/special chars with underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        name = re.sub(r'_+', '_', name)  # Collapse multiple underscores
        name = name.strip('_').lower()
        
        # Ensure it starts with letter or underscore
        if name and name[0].isdigit():
            name = '_' + name
        
        # Handle empty names
        if not name:
            name = 'field'
        
        return name


class PythonLookupRollupGenerator:
    """Generate code for lookup and rollup fields."""
    
    def __init__(self, data_access_mode: str = "dataclass"):
        """
        Initialize the generator.
        
        Args:
            data_access_mode: How to access record fields
        """
        self.data_access_mode = data_access_mode
        self.transpiler = PythonFormulaTranspiler(data_access_mode)
    
    def generate_lookup_getter(
        self,
        field: Dict[str, Any],
        metadata: Dict[str, Any],
        table_name: str
    ) -> str:
        """
        Generate getter for lookup field.
        
        Args:
            field: Lookup field metadata
            metadata: Full Airtable metadata
            table_name: Name of the table containing this field
            
        Returns:
            Python function code as string
        """
        field_name = self.transpiler._sanitize_field_name(field["name"])
        
        # Get the link field and target field
        options = field.get("options", {})
        link_field_id = options.get("recordLinkFieldId")
        target_field_id = options.get("fieldIdInLinkedTable")
        
        if not link_field_id or not target_field_id:
            return f"    def get_{field_name}(self, record) -> None:\n        return None  # Lookup configuration missing"
        
        # Find link field and target field details
        link_field = self._find_field_by_id(metadata, link_field_id)
        target_field = self._find_field_by_id(metadata, target_field_id)
        
        if not link_field or not target_field:
            return f"    def get_{field_name}(self, record) -> None:\n        return None  # Field not found"
        
        link_field_name = self.transpiler._sanitize_field_name(link_field["name"])
        target_field_name = self.transpiler._sanitize_field_name(target_field["name"])
        
        # Determine if link field is single or multiple
        is_multiple = link_field.get("type") == FIELD_TYPE_RECORD_LINKS
        
        # Find target table name
        target_table_id = link_field.get("options", {}).get("linkedTableId")
        target_table = self._find_table_by_id(metadata, target_table_id)
        target_table_name = self.transpiler._sanitize_field_name(target_table["name"]) if target_table else "unknown"
        
        if is_multiple:
            # Multiple lookups - return list
            return f"""    def get_{field_name}(self, record) -> List[Any]:
        \"\"\"Lookup {field["name"]} via {link_field["name"]}.\"\"\"
        linked_ids = {self._get_field_access("record", link_field_name)} or []
        if not linked_ids:
            return []
        linked_records = self.data_access.get_{target_table_name}_batch(linked_ids)
        return [{self._get_field_access("r", target_field_name)} for r in linked_records]"""
        else:
            # Single lookup
            return f"""    def get_{field_name}(self, record) -> Optional[Any]:
        \"\"\"Lookup {field["name"]} via {link_field["name"]}.\"\"\"
        linked_id = {self._get_field_access("record", link_field_name)}
        if not linked_id:
            return None
        linked_record = self.data_access.get_{target_table_name}(linked_id)
        return {self._get_field_access("linked_record", target_field_name)} if linked_record else None"""
    
    def generate_rollup_getter(
        self,
        field: Dict[str, Any],
        metadata: Dict[str, Any],
        table_name: str
    ) -> str:
        """
        Generate getter for rollup field.
        
        Args:
            field: Rollup field metadata
            metadata: Full Airtable metadata
            table_name: Name of the table containing this field
            
        Returns:
            Python function code as string
        """
        field_name = self.transpiler._sanitize_field_name(field["name"])
        
        # Get the link field and target field
        options = field.get("options", {})
        link_field_id = options.get("recordLinkFieldId")
        target_field_id = options.get("fieldIdInLinkedTable")
        agg_function = options.get("aggregationFunction", "SUM")
        
        if not link_field_id or not target_field_id:
            return f"    def get_{field_name}(self, record) -> None:\n        return None  # Rollup configuration missing"
        
        # Find link field and target field details
        link_field = self._find_field_by_id(metadata, link_field_id)
        target_field = self._find_field_by_id(metadata, target_field_id)
        
        if not link_field or not target_field:
            return f"    def get_{field_name}(self, record) -> None:\n        return None  # Field not found"
        
        link_field_name = self.transpiler._sanitize_field_name(link_field["name"])
        target_field_name = self.transpiler._sanitize_field_name(target_field["name"])
        
        # Find target table name
        target_table_id = link_field.get("options", {}).get("linkedTableId")
        target_table = self._find_table_by_id(metadata, target_table_id)
        target_table_name = self.transpiler._sanitize_field_name(target_table["name"]) if target_table else "unknown"
        
        # Generate aggregation logic
        agg_code = self._generate_aggregation_code(agg_function, target_field_name)
        
        return f"""    def get_{field_name}(self, record) -> Any:
        \"\"\"Rollup {field["name"]} via {link_field["name"]} using {agg_function}.\"\"\"
        linked_ids = {self._get_field_access("record", link_field_name)} or []
        if not linked_ids:
            return {self._get_default_value(agg_function)}
        linked_records = self.data_access.get_{target_table_name}_batch(linked_ids)
        values = [{self._get_field_access("r", target_field_name)} for r in linked_records if {self._get_field_access("r", target_field_name)} is not None]
        if not values:
            return {self._get_default_value(agg_function)}
        return {agg_code}"""
    
    def _get_field_access(self, record_var: str, field_name: str) -> str:
        """Generate field access code based on data access mode."""
        if self.data_access_mode == "dict":
            return f'{record_var}["{field_name}"]'
        else:
            return f"{record_var}.{field_name}"
    
    def _generate_aggregation_code(self, agg_function: str, field_name: str) -> str:
        """Generate aggregation code for rollup."""
        agg_upper = agg_function.upper()
        
        if agg_upper == "SUM":
            return "sum(values)"
        elif agg_upper == "COUNT":
            return "len(values)"
        elif agg_upper == "COUNTALL":
            return "len(values)"
        elif agg_upper == "MAX":
            return "max(values)"
        elif agg_upper == "MIN":
            return "min(values)"
        elif agg_upper in ("AVERAGE", "AVG"):
            return "sum(values) / len(values) if values else 0"
        elif agg_upper == "ARRAYUNIQUE":
            return "list(dict.fromkeys(values))"
        elif agg_upper == "ARRAYFLATTEN":
            return "_flatten_array(values)"
        else:
            return f"_unsupported_aggregation_{agg_function.lower()}(values)"
    
    def _get_default_value(self, agg_function: str) -> str:
        """Get default value for aggregation when no records."""
        agg_upper = agg_function.upper()
        
        if agg_upper in ("SUM", "COUNT", "COUNTALL", "AVERAGE", "AVG"):
            return "0"
        elif agg_upper in ("MAX", "MIN"):
            return "None"
        elif agg_upper in ("ARRAYUNIQUE", "ARRAYFLATTEN"):
            return "[]"
        else:
            return "None"
    
    @staticmethod
    def _find_field_by_id(metadata: Dict[str, Any], field_id: str) -> Optional[Dict[str, Any]]:
        """Find field in metadata by ID."""
        for table in metadata.get("tables", []):
            for field in table.get("fields", []):
                if field["id"] == field_id:
                    return field
        return None
    
    @staticmethod
    def _find_table_by_id(metadata: Dict[str, Any], table_id: str) -> Optional[Dict[str, Any]]:
        """Find table in metadata by ID."""
        for table in metadata.get("tables", []):
            if table["id"] == table_id:
                return table
        return None


def generate_python_library(
    metadata: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate complete Python module with computed field getters.
    
    Args:
        metadata: Airtable metadata
        options: Generation options
            - data_access_mode: "dataclass" | "dict" | "orm" (default: "dataclass")
            - include_types: bool (generate dataclass definitions) (default: True)
            - include_helpers: bool (include runtime helper functions) (default: True)
            - include_comments: bool (include dependency depth comments) (default: True)
    
    Returns:
        Complete Python module as string
    """
    if options is None:
        options = {}
    
    data_access_mode = options.get("data_access_mode", "dataclass")
    include_types = options.get("include_types", True)
    include_helpers = options.get("include_helpers", True)
    include_comments = options.get("include_comments", True)
    
    transpiler = PythonFormulaTranspiler(data_access_mode)
    lookup_generator = PythonLookupRollupGenerator(data_access_mode)
    
    # Get computation order
    computation_order = get_computation_order_with_metadata(metadata)
    
    # Generate code sections
    sections = []
    
    # Header
    sections.append(_generate_header())
    
    # Imports
    sections.append(_generate_imports(include_helpers))
    
    # Helper functions
    if include_helpers:
        sections.append(_generate_helper_functions())
    
    # Data access protocol
    sections.append(_generate_data_access_protocol(metadata, data_access_mode))
    
    # Type definitions (if requested)
    if include_types:
        sections.append(_generate_type_definitions(metadata, data_access_mode))
    
    # Computed field classes (one per table)
    for table in metadata.get("tables", []):
        table_class = _generate_table_computed_class(
            table,
            metadata,
            computation_order,
            transpiler,
            lookup_generator,
            include_comments
        )
        sections.append(table_class)
    
    return "\n\n".join(sections)


def _generate_header() -> str:
    """Generate file header."""
    return f"""# Auto-generated from Airtable metadata
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# DO NOT EDIT THIS FILE MANUALLY"""


def _generate_imports(include_helpers: bool) -> str:
    """Generate import statements."""
    imports = [
        "from typing import Optional, List, Any, Protocol",
        "from dataclasses import dataclass",
        "import datetime",
        "import math",
    ]
    
    return "\n".join(imports)


def _generate_helper_functions() -> str:
    """Generate runtime helper functions."""
    return '''# Runtime helper functions

def _substitute_nth(text: str, old: str, new: str, nth: int) -> str:
    """Replace the nth occurrence of old with new in text."""
    parts = text.split(old)
    if nth <= 0 or nth > len(parts) - 1:
        return text
    parts[nth] = new + parts[nth]
    return old.join(parts[:nth]) + parts[nth]


def _flatten_array(arr: Any) -> List[Any]:
    """Flatten nested arrays."""
    result = []
    for item in arr:
        if isinstance(item, list):
            result.extend(_flatten_array(item))
        else:
            result.append(item)
    return result'''


def _generate_data_access_protocol(metadata: Dict[str, Any], data_access_mode: str) -> str:
    """Generate DataAccess protocol interface."""
    transpiler = PythonFormulaTranspiler(data_access_mode)
    
    lines = [
        "# Data access interface - implement this for your data source",
        "class DataAccess(Protocol):",
        '    """Protocol for accessing Airtable data from your data source."""',
        ""
    ]
    
    # Generate methods for each table
    for table in metadata.get("tables", []):
        table_name = transpiler._sanitize_field_name(table["name"])
        
        lines.append(f"    def get_{table_name}(self, record_id: str) -> Optional[Any]:")
        lines.append(f'        """Fetch single {table["name"]} record by ID."""')
        lines.append("        ...")
        lines.append("")
        
        lines.append(f"    def get_{table_name}_batch(self, record_ids: List[str]) -> List[Any]:")
        lines.append(f'        """Fetch multiple {table["name"]} records by IDs."""')
        lines.append("        ...")
        lines.append("")
    
    return "\n".join(lines)


def _generate_type_definitions(metadata: Dict[str, Any], data_access_mode: str) -> str:
    """Generate dataclass type definitions for tables."""
    transpiler = PythonFormulaTranspiler(data_access_mode)
    
    lines = ["# Type definitions"]
    
    for table in metadata.get("tables", []):
        table_name = transpiler._sanitize_field_name(table["name"])
        class_name = "".join(word.capitalize() for word in table_name.split("_"))
        
        lines.append("")
        lines.append("@dataclass")
        lines.append(f"class {class_name}:")
        lines.append(f'    """{table["name"]} record."""')
        lines.append("    id: str")
        
        # Only include basic (non-computed) fields
        for field in table.get("fields", []):
            if field["type"] not in [FIELD_TYPE_FORMULA, FIELD_TYPE_ROLLUP, FIELD_TYPE_LOOKUP, FIELD_TYPE_COUNT]:
                field_name = transpiler._sanitize_field_name(field["name"])
                field_type = _get_python_type(field["type"])
                lines.append(f"    {field_name}: {field_type}")
    
    return "\n".join(lines)


def _generate_table_computed_class(
    table: Dict[str, Any],
    metadata: Dict[str, Any],
    computation_order: List[List[Dict[str, Any]]],
    transpiler: PythonFormulaTranspiler,
    lookup_generator: PythonLookupRollupGenerator,
    include_comments: bool
) -> str:
    """Generate computed fields class for a table."""
    table_name = transpiler._sanitize_field_name(table["name"])
    class_name = "".join(word.capitalize() for word in table_name.split("_")) + "ComputedFields"
    
    lines = [
        f"class {class_name}:",
        f'    """{table["name"]} computed field getters."""',
        "",
        "    def __init__(self, data_access: DataAccess):",
        "        self.data_access = data_access",
        ""
    ]
    
    # Group fields by depth
    fields_by_depth = {}
    for depth_level, fields_at_depth in enumerate(computation_order):
        for field_info in fields_at_depth:
            if field_info["table_name"] == table["name"]:
                if depth_level not in fields_by_depth:
                    fields_by_depth[depth_level] = []
                fields_by_depth[depth_level].append(field_info)
    
    # Generate getters organized by depth
    for depth in sorted(fields_by_depth.keys()):
        if depth == 0:
            continue  # Skip basic fields
        
        if include_comments:
            lines.append(f"    # Depth {depth} computed fields")
            lines.append("")
        
        for field_info in fields_by_depth[depth]:
            # Find full field metadata
            field = None
            for f in table.get("fields", []):
                if f["id"] == field_info["id"]:
                    field = f
                    break
            
            if not field:
                continue
            
            # Generate getter based on field type
            if field["type"] == FIELD_TYPE_FORMULA:
                getter = _generate_formula_getter(field, metadata, transpiler)
            elif field["type"] == FIELD_TYPE_LOOKUP:
                getter = lookup_generator.generate_lookup_getter(field, metadata, table["name"])
            elif field["type"] == FIELD_TYPE_ROLLUP:
                getter = lookup_generator.generate_rollup_getter(field, metadata, table["name"])
            elif field["type"] == FIELD_TYPE_COUNT:
                # Count is a special case of rollup
                getter = _generate_count_getter(field, metadata, transpiler, lookup_generator)
            else:
                continue
            
            lines.append(getter)
            lines.append("")
    
    return "\n".join(lines)


def _generate_formula_getter(
    field: Dict[str, Any],
    metadata: Dict[str, Any],
    transpiler: PythonFormulaTranspiler
) -> str:
    """Generate getter for formula field."""
    field_name = transpiler._sanitize_field_name(field["name"])
    formula = field.get("options", {}).get("formula", "")
    
    if not formula:
        return f"    def get_{field_name}(self, record) -> None:\n        return None  # Formula missing"
    
    try:
        # Parse and transpile formula
        ast = parse_airtable_formula(formula, metadata)
        python_code = transpiler.transpile(ast)
        
        # Determine return type
        return_type = _get_formula_return_type(field)
        
        return f"""    def get_{field_name}(self, record) -> {return_type}:
        \"\"\"Computed: {field["name"]}\"\"\"
        try:
            return {python_code}
        except (AttributeError, TypeError, ValueError, ZeroDivisionError):
            return None"""
    
    except Exception as e:
        # If parsing fails, generate stub with error comment
        return f"""    def get_{field_name}(self, record) -> None:
        \"\"\"Computed: {field["name"]}\"\"\"
        # Error parsing formula: {str(e)}
        return None"""


def _generate_count_getter(
    field: Dict[str, Any],
    metadata: Dict[str, Any],
    transpiler: PythonFormulaTranspiler,
    lookup_generator: PythonLookupRollupGenerator
) -> str:
    """Generate getter for count field."""
    field_name = transpiler._sanitize_field_name(field["name"])
    
    # Count is essentially a rollup with COUNT aggregation
    # Create a temporary rollup field config
    options = field.get("options", {})
    link_field_id = options.get("recordLinkFieldId")
    
    if not link_field_id:
        return f"    def get_{field_name}(self, record) -> int:\n        return 0  # Count configuration missing"
    
    # Find link field
    link_field = lookup_generator._find_field_by_id(metadata, link_field_id)
    if not link_field:
        return f"    def get_{field_name}(self, record) -> int:\n        return 0  # Link field not found"
    
    link_field_name = transpiler._sanitize_field_name(link_field["name"])
    field_access = lookup_generator._get_field_access("record", link_field_name)
    
    return f"""    def get_{field_name}(self, record) -> int:
        \"\"\"Count of {field["name"]} via {link_field["name"]}.\"\"\"
        linked_ids = {field_access} or []
        return len(linked_ids)"""


def _get_python_type(airtable_type: str) -> str:
    """Map Airtable field type to Python type hint."""
    type_map = {
        "singleLineText": "Optional[str]",
        "multilineText": "Optional[str]",
        "email": "Optional[str]",
        "url": "Optional[str]",
        "phoneNumber": "Optional[str]",
        "number": "Optional[float]",
        "currency": "Optional[float]",
        "percent": "Optional[float]",
        "rating": "Optional[int]",
        "duration": "Optional[int]",
        "checkbox": "bool",
        "date": "Optional[datetime.date]",
        "dateTime": "Optional[datetime.datetime]",
        "singleSelect": "Optional[str]",
        "multipleSelects": "List[str]",
        "singleCollaborator": "Optional[str]",
        "multipleCollaborators": "List[str]",
        "multipleRecordLinks": "List[str]",
        "multipleAttachments": "List[Any]",
        "barcode": "Optional[str]",
        "button": "Optional[str]",
    }
    
    return type_map.get(airtable_type, "Any")


def _get_formula_return_type(field: Dict[str, Any]) -> str:
    """Determine return type hint for formula field."""
    # Try to infer from formula result type if available
    result_type = field.get("options", {}).get("result", {}).get("type")
    
    if result_type:
        return _get_python_type(result_type)
    
    # Default to Any if unknown
    return "Any"
