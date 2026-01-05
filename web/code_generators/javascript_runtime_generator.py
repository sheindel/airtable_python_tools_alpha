"""JavaScript runtime code generator for Airtable formulas.

This module converts Airtable formula ASTs into executable JavaScript code.
Supports formulas, lookups, rollups, and generates complete JavaScript libraries.
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


class JavaScriptFormulaTranspiler:
    """Convert FormulaNode AST to JavaScript code."""
    
    # Mapping of Airtable operators to JavaScript operators
    OPERATOR_MAP = {
        '+': '+',
        '-': '-',
        '*': '*',
        '/': '/',
        '&': '+',  # String concatenation
        '=': '===',
        '!=': '!==',
        '<': '<',
        '>': '>',
        '<=': '<=',
        '>=': '>=',
    }
    
    def __init__(self, data_access_mode: str = "object", include_null_checks: bool = True, use_typescript: bool = False):
        """
        Initialize the transpiler.
        
        Args:
            data_access_mode: How to access record fields
                - "object": record.fieldName
                - "dict": record["fieldName"]
                - "camelCase": record.fieldName (with camelCase conversion)
            include_null_checks: Whether to add null safety checks
            use_typescript: Whether to include TypeScript type annotations
        """
        self.data_access_mode = data_access_mode
        self.include_null_checks = include_null_checks
        self.use_typescript = use_typescript
    
    def transpile(self, node: FormulaNode) -> str:
        """
        Convert AST node to JavaScript expression.
        
        Args:
            node: AST node to transpile
            
        Returns:
            JavaScript code string
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
            # Escape single quotes and use single quotes for JavaScript
            escaped = str(node.value).replace("'", "\\'").replace('\n', '\\n')
            return f"'{escaped}'"
        elif node.data_type == "boolean":
            return "true" if node.value else "false"
        elif node.data_type == "number":
            return str(node.value)
        else:
            return str(node.value)
    
    def _transpile_field_reference(self, node: FieldReferenceNode) -> str:
        """
        Convert field reference to data access pattern.
        
        Returns code like:
        - object: record.customerName
        - dict: record["customerName"]
        - camelCase: record.customerName (with camelCase conversion)
        """
        if self.data_access_mode == "camelCase":
            field_name = self._to_camel_case(node.field_name)
        else:
            field_name = self._sanitize_field_name(node.field_name)
        
        if self.data_access_mode == "dict":
            return f'record["{field_name}"]'
        else:  # object or camelCase
            return f"record.{field_name}"
    
    def _transpile_function_call(self, node: FunctionCallNode) -> str:
        """
        Map Airtable functions to JavaScript equivalents.
        
        Handles 30+ common Airtable functions.
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
            return f"(!{args[0]})"
        elif func_name == "BLANK":
            return self._transpile_blank(args)
        elif func_name == "XOR":
            return self._transpile_xor(args)
        
        # String functions
        elif func_name == "CONCATENATE":
            return self._transpile_concatenate(args)
        elif func_name == "LEN":
            return f"(String({args[0]} ?? '')).length"
        elif func_name == "UPPER":
            return f"(String({args[0]} ?? '')).toUpperCase()"
        elif func_name == "LOWER":
            return f"(String({args[0]} ?? '')).toLowerCase()"
        elif func_name == "TRIM":
            return f"(String({args[0]} ?? '')).trim()"
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
            return f"Math.abs({args[0]})"
        elif func_name == "MOD":
            return f"({args[0]} % {args[1]})"
        elif func_name == "CEILING":
            return f"Math.ceil({args[0]})"
        elif func_name == "FLOOR":
            return f"Math.floor({args[0]})"
        elif func_name == "SQRT":
            return f"Math.sqrt({args[0]})"
        elif func_name == "POWER":
            return f"Math.pow({args[0]}, {args[1]})"
        elif func_name == "EXP":
            return f"Math.exp({args[0]})"
        elif func_name == "LOG":
            return self._transpile_log(args)
        elif func_name == "MAX":
            return self._transpile_max(args)
        elif func_name == "MIN":
            return self._transpile_min(args)
        
        # Date functions
        elif func_name == "NOW":
            return "new Date()"
        elif func_name == "TODAY":
            return "new Date(new Date().setHours(0, 0, 0, 0))"
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
            return f"_unsupportedFunction{func_name.title()}({args_str})"
    
    def _transpile_if(self, args: List[str]) -> str:
        """Transpile IF(condition, true_val, false_val)."""
        if len(args) == 2:
            # IF with only condition and true value (false defaults to null)
            return f"({args[0]} ? {args[1]} : null)"
        elif len(args) == 3:
            return f"({args[0]} ? {args[1]} : {args[2]})"
        else:
            raise ValueError(f"IF requires 2 or 3 arguments, got {len(args)}")
    
    def _transpile_and(self, args: List[str]) -> str:
        """Transpile AND(arg1, arg2, ...)."""
        return f"({' && '.join(args)})"
    
    def _transpile_or(self, args: List[str]) -> str:
        """Transpile OR(arg1, arg2, ...)."""
        return f"({' || '.join(args)})"
    
    def _transpile_blank(self, args: List[str]) -> str:
        """Transpile BLANK() - returns if value is empty/null."""
        if len(args) == 0:
            return "null"
        else:
            # BLANK(value) checks if value is blank
            return f"({args[0]} == null || {args[0]} === '')"
    
    def _transpile_xor(self, args: List[str]) -> str:
        """Transpile XOR(arg1, arg2)."""
        if len(args) != 2:
            raise ValueError(f"XOR requires exactly 2 arguments, got {len(args)}")
        return f"(!!(({args[0]}) ^ ({args[1]})))"
    
    def _transpile_concatenate(self, args: List[str]) -> str:
        """Transpile CONCATENATE(str1, str2, ...)."""
        # Convert all arguments to strings and concatenate
        str_args = [f"String({arg} ?? '')" for arg in args]
        return f"({' + '.join(str_args)})"
    
    def _transpile_left(self, args: List[str]) -> str:
        """Transpile LEFT(string, count)."""
        if len(args) != 2:
            raise ValueError(f"LEFT requires 2 arguments, got {len(args)}")
        return f"(String({args[0]} ?? '')).substring(0, {args[1]})"
    
    def _transpile_right(self, args: List[str]) -> str:
        """Transpile RIGHT(string, count)."""
        if len(args) != 2:
            raise ValueError(f"RIGHT requires 2 arguments, got {len(args)}")
        return f"(String({args[0]} ?? '')).slice(-{args[1]})"
    
    def _transpile_mid(self, args: List[str]) -> str:
        """Transpile MID(string, start, count) - Airtable uses 1-based indexing."""
        if len(args) != 3:
            raise ValueError(f"MID requires 3 arguments, got {len(args)}")
        # Convert from 1-based to 0-based indexing
        return f"(String({args[0]} ?? '')).substring({args[1]} - 1, ({args[1]} - 1) + {args[2]})"
    
    def _transpile_find(self, args: List[str]) -> str:
        """Transpile FIND(search, text) - Returns 1-based index or 0 if not found."""
        if len(args) < 2:
            raise ValueError(f"FIND requires at least 2 arguments, got {len(args)}")
        
        if len(args) == 2:
            # FIND(search, text)
            return f"((String({args[1]} ?? '')).indexOf(String({args[0]} ?? '')) + 1)"
        else:
            # FIND(search, text, start_pos) - start_pos is 1-based
            return f"((String({args[1]} ?? '')).indexOf(String({args[0]} ?? ''), {args[2]} - 1) + 1)"
    
    def _transpile_substitute(self, args: List[str]) -> str:
        """Transpile SUBSTITUTE(text, old, new, [index])."""
        if len(args) < 3:
            raise ValueError(f"SUBSTITUTE requires at least 3 arguments, got {len(args)}")
        
        if len(args) == 3:
            # Replace all occurrences
            return f"_substituteAll(String({args[0]} ?? ''), String({args[1]} ?? ''), String({args[2]} ?? ''))"
        else:
            # Replace nth occurrence (1-based)
            return f"_substituteNth(String({args[0]} ?? ''), String({args[1]} ?? ''), String({args[2]} ?? ''), {args[3]})"
    
    def _transpile_replace(self, args: List[str]) -> str:
        """Transpile REPLACE(text, start, count, replacement) - Airtable uses 1-based indexing."""
        if len(args) != 4:
            raise ValueError(f"REPLACE requires 4 arguments, got {len(args)}")
        
        # Convert from 1-based to 0-based indexing
        return f"(String({args[0]} ?? '')).substring(0, {args[1]} - 1) + String({args[3]} ?? '') + (String({args[0]} ?? '')).substring(({args[1]} - 1) + {args[2]})"
    
    def _transpile_rept(self, args: List[str]) -> str:
        """Transpile REPT(text, count)."""
        if len(args) != 2:
            raise ValueError(f"REPT requires 2 arguments, got {len(args)}")
        return f"(String({args[0]} ?? '')).repeat({args[1]})"
    
    def _transpile_round(self, args: List[str]) -> str:
        """Transpile ROUND(value, [precision])."""
        if len(args) == 1:
            return f"Math.round({args[0]})"
        elif len(args) == 2:
            # Round to specified decimal places
            return f"(Math.round({args[0]} * Math.pow(10, {args[1]})) / Math.pow(10, {args[1]}))"
        else:
            raise ValueError(f"ROUND requires 1 or 2 arguments, got {len(args)}")
    
    def _transpile_log(self, args: List[str]) -> str:
        """Transpile LOG(value, [base])."""
        if len(args) == 1:
            # Natural log
            return f"Math.log({args[0]})"
        elif len(args) == 2:
            # Log with custom base
            return f"(Math.log({args[0]}) / Math.log({args[1]}))"
        else:
            raise ValueError(f"LOG requires 1 or 2 arguments, got {len(args)}")
    
    def _transpile_max(self, args: List[str]) -> str:
        """Transpile MAX(val1, val2, ...)."""
        if len(args) == 0:
            raise ValueError("MAX requires at least 1 argument")
        return f"Math.max({', '.join(args)})"
    
    def _transpile_min(self, args: List[str]) -> str:
        """Transpile MIN(val1, val2, ...)."""
        if len(args) == 0:
            raise ValueError("MIN requires at least 1 argument")
        return f"Math.min({', '.join(args)})"
    
    def _transpile_year(self, args: List[str]) -> str:
        """Transpile YEAR(date)."""
        if len(args) != 1:
            raise ValueError(f"YEAR requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getFullYear()"
    
    def _transpile_month(self, args: List[str]) -> str:
        """Transpile MONTH(date) - Returns 1-12 (Airtable convention)."""
        if len(args) != 1:
            raise ValueError(f"MONTH requires 1 argument, got {len(args)}")
        return f"((new Date({args[0]})).getMonth() + 1)"
    
    def _transpile_day(self, args: List[str]) -> str:
        """Transpile DAY(date)."""
        if len(args) != 1:
            raise ValueError(f"DAY requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getDate()"
    
    def _transpile_hour(self, args: List[str]) -> str:
        """Transpile HOUR(datetime)."""
        if len(args) != 1:
            raise ValueError(f"HOUR requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getHours()"
    
    def _transpile_minute(self, args: List[str]) -> str:
        """Transpile MINUTE(datetime)."""
        if len(args) != 1:
            raise ValueError(f"MINUTE requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getMinutes()"
    
    def _transpile_second(self, args: List[str]) -> str:
        """Transpile SECOND(datetime)."""
        if len(args) != 1:
            raise ValueError(f"SECOND requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getSeconds()"
    
    def _transpile_weekday(self, args: List[str]) -> str:
        """
        Transpile WEEKDAY(date) - Returns 0-6 where Sunday is 0.
        
        Note: JavaScript getDay() returns 0 for Sunday, which matches Airtable.
        """
        if len(args) != 1:
            raise ValueError(f"WEEKDAY requires 1 argument, got {len(args)}")
        return f"(new Date({args[0]})).getDay()"
    
    def _transpile_arraycompact(self, args: List[str]) -> str:
        """Transpile ARRAYCOMPACT(array) - Remove null/undefined/empty values."""
        if len(args) != 1:
            raise ValueError(f"ARRAYCOMPACT requires 1 argument, got {len(args)}")
        return f"({args[0]}).filter(x => x != null && x !== '')"
    
    def _transpile_arrayflatten(self, args: List[str]) -> str:
        """Transpile ARRAYFLATTEN(array) - Flatten nested arrays."""
        if len(args) != 1:
            raise ValueError(f"ARRAYFLATTEN requires 1 argument, got {len(args)}")
        return f"_flattenArray({args[0]})"
    
    def _transpile_arrayunique(self, args: List[str]) -> str:
        """Transpile ARRAYUNIQUE(array) - Remove duplicates."""
        if len(args) != 1:
            raise ValueError(f"ARRAYUNIQUE requires 1 argument, got {len(args)}")
        return f"[...new Set({args[0]})]"
    
    def _transpile_binary_op(self, node: BinaryOpNode) -> str:
        """Transpile binary operations."""
        left = self.transpile(node.left)
        right = self.transpile(node.right)
        operator = self.OPERATOR_MAP.get(node.operator, node.operator)
        
        # Special handling for string concatenation
        if node.operator == "&":
            # Convert both sides to strings
            left = f"String({left} ?? '')"
            right = f"String({right} ?? '')"
        
        return f"({left} {operator} {right})"
    
    def _transpile_unary_op(self, node: UnaryOpNode) -> str:
        """Transpile unary operations."""
        operand = self.transpile(node.operand)
        
        if node.operator == "-":
            return f"(-{operand})"
        elif node.operator.upper() == "NOT":
            return f"(!{operand})"
        else:
            raise ValueError(f"Unknown unary operator: {node.operator}")
    
    def _sanitize_field_name(self, field_name: str) -> str:
        """
        Convert field name to valid JavaScript identifier.
        
        Handles:
        - Spaces → underscores
        - Special characters → underscores
        - Leading numbers → prefix with underscore
        """
        # Replace spaces and special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        
        # Remove consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # If starts with a number, prefix with underscore
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
        
        # Remove trailing underscores
        sanitized = sanitized.rstrip('_')
        
        return sanitized or "field"
    
    def _to_camel_case(self, field_name: str) -> str:
        """
        Convert field name to camelCase.
        
        Example: "Customer Name" → "customerName"
        """
        # First sanitize
        sanitized = self._sanitize_field_name(field_name)
        
        # Split by underscores
        parts = sanitized.split('_')
        
        # First part lowercase, rest title case
        if parts:
            return parts[0].lower() + ''.join(p.title() for p in parts[1:])
        return sanitized


class JavaScriptLookupRollupGenerator:
    """Generate JavaScript code for lookup and rollup fields."""
    
    def __init__(self, data_access_mode: str = "object", use_typescript: bool = False):
        """
        Initialize the generator.
        
        Args:
            data_access_mode: How to access record fields
            use_typescript: Whether to include TypeScript type annotations
        """
        self.data_access_mode = data_access_mode
        self.use_typescript = use_typescript
    
    def generate_lookup_getter(
        self,
        field: Dict[str, Any],
        metadata: Dict[str, Any],
        table_name: str
    ) -> str:
        """
        Generate getter for lookup field.
        
        Returns async function that looks up related record and returns field value.
        """
        field_name = self._sanitize_field_name(field["name"])
        method_name = f"get{self._to_pascal_case(field_name)}"
        
        options = field.get("options", {})
        link_field_id = options.get("recordLinkFieldId")
        field_id_in_linked_table = options.get("fieldIdInLinkedTable")
        
        if not link_field_id or not field_id_in_linked_table:
            raise ValueError(f"Lookup field {field['name']} missing required options")
        
        # Find the link field
        current_table = next(
            (t for t in metadata["tables"] if any(f["id"] == field["id"] for f in t["fields"])),
            None
        )
        if not current_table:
            raise ValueError(f"Could not find table for field {field['name']}")
        
        link_field = next(
            (f for f in current_table["fields"] if f["id"] == link_field_id),
            None
        )
        if not link_field:
            raise ValueError(f"Could not find link field {link_field_id}")
        
        link_field_name = self._sanitize_field_name(link_field["name"])
        
        # Find the linked table
        link_options = link_field.get("options", {})
        linked_table_id = link_options.get("linkedTableId")
        linked_table = next(
            (t for t in metadata["tables"] if t["id"] == linked_table_id),
            None
        )
        if not linked_table:
            raise ValueError(f"Could not find linked table {linked_table_id}")
        
        linked_table_name = linked_table["name"]
        linked_table_method = self._to_camel_case(linked_table_name)
        
        # Find the field to lookup in the linked table
        lookup_field = next(
            (f for f in linked_table["fields"] if f["id"] == field_id_in_linked_table),
            None
        )
        if not lookup_field:
            raise ValueError(f"Could not find lookup field {field_id_in_linked_table}")
        
        lookup_field_name = self._sanitize_field_name(lookup_field["name"])
        
        # Check if this is a multi-value lookup
        is_multiple = link_field.get("type") == FIELD_TYPE_RECORD_LINKS
        
        # Generate the getter
        return_type = " any" if self.use_typescript else ""
        
        if is_multiple:
            # Multi-value lookup
            return f"""
  async {method_name}(record){return_type} {{
    const linkedIds = record.{link_field_name} || [];
    if (linkedIds.length === 0) return [];
    
    const linkedRecords = await this.dataAccess.get{self._to_pascal_case(linked_table_method)}Batch(linkedIds);
    return linkedRecords.map(r => r.{lookup_field_name});
  }}"""
        else:
            # Single-value lookup
            return f"""
  async {method_name}(record){return_type} {{
    const linkedId = record.{link_field_name};
    if (!linkedId) return null;
    
    const linkedRecord = await this.dataAccess.get{self._to_pascal_case(linked_table_method)}(linkedId);
    return linkedRecord ? linkedRecord.{lookup_field_name} : null;
  }}"""
    
    def generate_rollup_getter(
        self,
        field: Dict[str, Any],
        metadata: Dict[str, Any],
        table_name: str
    ) -> str:
        """
        Generate getter for rollup field.
        
        Returns async function that aggregates values from related records.
        """
        field_name = self._sanitize_field_name(field["name"])
        method_name = f"get{self._to_pascal_case(field_name)}"
        
        options = field.get("options", {})
        link_field_id = options.get("recordLinkFieldId")
        field_id_in_linked_table = options.get("fieldIdInLinkedTable")
        aggregation_function = options.get("aggregationFunction", "SUM")
        
        if not link_field_id or not field_id_in_linked_table:
            raise ValueError(f"Rollup field {field['name']} missing required options")
        
        # Find the link field and linked table (same as lookup)
        current_table = next(
            (t for t in metadata["tables"] if any(f["id"] == field["id"] for f in t["fields"])),
            None
        )
        if not current_table:
            raise ValueError(f"Could not find table for field {field['name']}")
        
        link_field = next(
            (f for f in current_table["fields"] if f["id"] == link_field_id),
            None
        )
        if not link_field:
            raise ValueError(f"Could not find link field {link_field_id}")
        
        link_field_name = self._sanitize_field_name(link_field["name"])
        
        link_options = link_field.get("options", {})
        linked_table_id = link_options.get("linkedTableId")
        linked_table = next(
            (t for t in metadata["tables"] if t["id"] == linked_table_id),
            None
        )
        if not linked_table:
            raise ValueError(f"Could not find linked table {linked_table_id}")
        
        linked_table_name = linked_table["name"]
        linked_table_method = self._to_camel_case(linked_table_name)
        
        rollup_field = next(
            (f for f in linked_table["fields"] if f["id"] == field_id_in_linked_table),
            None
        )
        if not rollup_field:
            raise ValueError(f"Could not find rollup field {field_id_in_linked_table}")
        
        rollup_field_name = self._sanitize_field_name(rollup_field["name"])
        
        # Generate aggregation code
        return_type = " any" if self.use_typescript else ""
        aggregation_code = self._generate_aggregation_code(
            aggregation_function,
            rollup_field_name
        )
        
        return f"""
  async {method_name}(record){return_type} {{
    const linkedIds = record.{link_field_name} || [];
    if (linkedIds.length === 0) {aggregation_code['default']};
    
    const linkedRecords = await this.dataAccess.get{self._to_pascal_case(linked_table_method)}Batch(linkedIds);
    {aggregation_code['computation']}
  }}"""
    
    def generate_count_getter(
        self,
        field: Dict[str, Any],
        metadata: Dict[str, Any],
        table_name: str
    ) -> str:
        """
        Generate getter for count field.
        
        Simply counts the number of linked records.
        """
        field_name = self._sanitize_field_name(field["name"])
        method_name = f"get{self._to_pascal_case(field_name)}"
        
        options = field.get("options", {})
        link_field_id = options.get("recordLinkFieldId")
        
        if not link_field_id:
            raise ValueError(f"Count field {field['name']} missing recordLinkFieldId")
        
        # Find the link field
        current_table = next(
            (t for t in metadata["tables"] if any(f["id"] == field["id"] for f in t["fields"])),
            None
        )
        if not current_table:
            raise ValueError(f"Could not find table for field {field['name']}")
        
        link_field = next(
            (f for f in current_table["fields"] if f["id"] == link_field_id),
            None
        )
        if not link_field:
            raise ValueError(f"Could not find link field {link_field_id}")
        
        link_field_name = self._sanitize_field_name(link_field["name"])
        
        return_type = " number" if self.use_typescript else ""
        
        return f"""
  {method_name}(record){return_type} {{
    const linkedIds = record.{link_field_name} || [];
    return linkedIds.length;
  }}"""
    
    def _generate_aggregation_code(self, function: str, field_name: str) -> Dict[str, str]:
        """
        Generate JavaScript aggregation code for different functions.
        
        Returns dict with 'default' and 'computation' keys.
        """
        function = function.upper()
        
        if function == "SUM":
            return {
                'default': 'return 0',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    if (values.length === 0) return 0;
    return values.reduce((a, b) => a + b, 0);'''
            }
        elif function == "COUNT":
            return {
                'default': 'return 0',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    return values.length;'''
            }
        elif function == "COUNTALL":
            return {
                'default': 'return 0',
                'computation': 'return linkedRecords.length;'
            }
        elif function == "MAX":
            return {
                'default': 'return null',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    if (values.length === 0) return null;
    return Math.max(...values);'''
            }
        elif function == "MIN":
            return {
                'default': 'return null',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    if (values.length === 0) return null;
    return Math.min(...values);'''
            }
        elif function == "AVERAGE" or function == "AVG":
            return {
                'default': 'return 0',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    if (values.length === 0) return 0;
    return values.reduce((a, b) => a + b, 0) / values.length;'''
            }
        elif function == "ARRAYUNIQUE":
            return {
                'default': 'return []',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    return [...new Set(values)];'''
            }
        elif function == "ARRAYFLATTEN":
            return {
                'default': 'return []',
                'computation': f'''const values = linkedRecords.map(r => r.{field_name}).filter(v => v != null);
    return _flattenArray(values);'''
            }
        else:
            return {
                'default': 'return null',
                'computation': f'return linkedRecords.map(r => r.{field_name}); // Unsupported aggregation: {function}'
            }
    
    def _sanitize_field_name(self, field_name: str) -> str:
        """Convert field name to valid JavaScript identifier."""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        sanitized = re.sub(r'_+', '_', sanitized)
        if sanitized and sanitized[0].isdigit():
            sanitized = f"_{sanitized}"
        sanitized = sanitized.rstrip('_')
        return sanitized or "field"
    
    def _to_camel_case(self, field_name: str) -> str:
        """Convert field name to camelCase."""
        sanitized = self._sanitize_field_name(field_name)
        parts = sanitized.split('_')
        if parts:
            return parts[0].lower() + ''.join(p.title() for p in parts[1:])
        return sanitized
    
    def _to_pascal_case(self, field_name: str) -> str:
        """Convert field name to PascalCase."""
        camel = self._to_camel_case(field_name)
        return camel[0].upper() + camel[1:] if camel else ""


def generate_javascript_library(
    metadata: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generate complete JavaScript module with computed field getters.
    
    Args:
        metadata: Airtable metadata dictionary
        options: Generation options
            - data_access_mode: "object" | "dict" | "camelCase" (default: "object")
            - use_typescript: Include TypeScript annotations (default: False)
            - module_format: "esm" | "cjs" | "browser" (default: "esm")
            - include_helpers: Include runtime helper functions (default: True)
            - include_comments: Include computation depth comments (default: True)
    
    Returns:
        Complete JavaScript/TypeScript module as string
    """
    options = options or {}
    data_access_mode = options.get("data_access_mode", "object")
    use_typescript = options.get("use_typescript", False)
    module_format = options.get("module_format", "esm")
    include_helpers = options.get("include_helpers", True)
    include_comments = options.get("include_comments", True)
    
    transpiler = JavaScriptFormulaTranspiler(
        data_access_mode=data_access_mode,
        use_typescript=use_typescript
    )
    lookup_rollup_gen = JavaScriptLookupRollupGenerator(
        data_access_mode=data_access_mode,
        use_typescript=use_typescript
    )
    
    # Start building the library
    lines = []
    
    # Header
    file_extension = "ts" if use_typescript else "js"
    lines.append(f"// Auto-generated from Airtable metadata")
    lines.append(f"// Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"// DO NOT EDIT THIS FILE MANUALLY")
    lines.append("")
    
    # Helper functions
    if include_helpers:
        lines.append("// Runtime helper functions")
        lines.append("")
        lines.append("function _substituteAll(text, oldStr, newStr) {")
        lines.append("  return text.split(oldStr).join(newStr);")
        lines.append("}")
        lines.append("")
        lines.append("function _substituteNth(text, oldStr, newStr, nth) {")
        lines.append("  const parts = text.split(oldStr);")
        lines.append("  if (nth <= 0 || nth > parts.length - 1) return text;")
        lines.append("  parts[nth] = newStr + parts[nth];")
        lines.append("  return parts.slice(0, nth).join(oldStr) + parts[nth];")
        lines.append("}")
        lines.append("")
        lines.append("function _flattenArray(arr) {")
        lines.append("  const result = [];")
        lines.append("  for (const item of arr) {")
        lines.append("    if (Array.isArray(item)) {")
        lines.append("      result.push(..._flattenArray(item));")
        lines.append("    } else {")
        lines.append("      result.push(item);")
        lines.append("    }")
        lines.append("  }")
        lines.append("  return result;")
        lines.append("}")
        lines.append("")
    
    # Get computation order
    computation_order = get_computation_order_with_metadata(metadata)
    
    # Generate class for each table
    for table in metadata["tables"]:
        table_name = table["name"]
        class_name = f"{_to_pascal_case(_sanitize_field_name(table_name))}ComputedFields"
        
        lines.append(f"// Computed fields for {table_name}")
        if use_typescript:
            lines.append(f"export class {class_name} {{")
            lines.append(f"  private dataAccess: any;")
            lines.append("")
            lines.append(f"  constructor(dataAccess: any) {{")
        else:
            lines.append(f"export class {class_name} {{")
            lines.append(f"  constructor(dataAccess) {{")
        lines.append(f"    this.dataAccess = dataAccess;")
        lines.append(f"  }}")
        lines.append("")
        
        # Get fields for this table
        table_fields = table["fields"]
        
        # Group fields by computation depth
        fields_by_depth = {}
        for field in table_fields:
            field_id = field["id"]
            field_type = field["type"]
            
            # Only process computed fields
            if field_type in [FIELD_TYPE_FORMULA, FIELD_TYPE_LOOKUP, FIELD_TYPE_ROLLUP, FIELD_TYPE_COUNT]:
                depth = 0
                for depth_idx, depth_fields in enumerate(computation_order):
                    if field_id in depth_fields:
                        depth = depth_idx
                        break
                
                if depth not in fields_by_depth:
                    fields_by_depth[depth] = []
                fields_by_depth[depth].append(field)
        
        # Generate getters by depth
        for depth in sorted(fields_by_depth.keys()):
            if include_comments:
                lines.append(f"  // Depth {depth} computed fields")
                lines.append("")
            
            for field in fields_by_depth[depth]:
                field_type = field["type"]
                
                try:
                    if field_type == FIELD_TYPE_FORMULA:
                        # Parse and transpile formula
                        formula_text = field.get("options", {}).get("formula", "")
                        if formula_text:
                            ast = parse_airtable_formula(formula_text, metadata)
                            js_expr = transpiler.transpile(ast)
                            
                            field_name = _sanitize_field_name(field["name"])
                            method_name = f"get{_to_pascal_case(field_name)}"
                            comment = field.get("description", f"Computed: {field['name']}")
                            return_type = " any" if use_typescript else ""
                            
                            lines.append(f"  // {comment}")
                            lines.append(f"  {method_name}(record){return_type} {{")
                            lines.append(f"    try {{")
                            lines.append(f"      return {js_expr};")
                            lines.append(f"    }} catch (error) {{")
                            lines.append(f"      return null;")
                            lines.append(f"    }}")
                            lines.append(f"  }}")
                            lines.append("")
                    
                    elif field_type == FIELD_TYPE_LOOKUP:
                        getter_code = lookup_rollup_gen.generate_lookup_getter(field, metadata, table_name)
                        lines.append(getter_code.strip())
                        lines.append("")
                    
                    elif field_type == FIELD_TYPE_ROLLUP:
                        getter_code = lookup_rollup_gen.generate_rollup_getter(field, metadata, table_name)
                        lines.append(getter_code.strip())
                        lines.append("")
                    
                    elif field_type == FIELD_TYPE_COUNT:
                        getter_code = lookup_rollup_gen.generate_count_getter(field, metadata, table_name)
                        lines.append(getter_code.strip())
                        lines.append("")
                
                except Exception as e:
                    # Generate placeholder for unsupported fields
                    field_name = _sanitize_field_name(field["name"])
                    method_name = f"get{_to_pascal_case(field_name)}"
                    return_type = " any" if use_typescript else ""
                    lines.append(f"  // Error generating {field['name']}: {str(e)}")
                    lines.append(f"  {method_name}(record){return_type} {{")
                    lines.append(f"    throw new Error('Unsupported field: {field['name']}');")
                    lines.append(f"  }}")
                    lines.append("")
        
        lines.append("}")
        lines.append("")
    
    return "\n".join(lines)


def _sanitize_field_name(field_name: str) -> str:
    """Convert field name to valid JavaScript identifier."""
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
    sanitized = re.sub(r'_+', '_', sanitized)
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    sanitized = sanitized.rstrip('_')
    return sanitized or "field"


def _to_camel_case(field_name: str) -> str:
    """Convert field name to camelCase."""
    sanitized = _sanitize_field_name(field_name)
    parts = sanitized.split('_')
    if parts:
        return parts[0].lower() + ''.join(p.title() for p in parts[1:])
    return sanitized


def _to_pascal_case(field_name: str) -> str:
    """Convert field name to PascalCase."""
    camel = _to_camel_case(field_name)
    return camel[0].upper() + camel[1:] if camel else ""
