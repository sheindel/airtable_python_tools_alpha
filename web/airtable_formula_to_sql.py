"""Airtable Formula to PostgreSQL SQL Converter

Converts Airtable formula syntax to PostgreSQL SQL expressions for use in generated columns.

WARNING: This is experimental and has limited support. Many Airtable functions don't have
direct SQL equivalents or require complex conversion logic.
"""

import re
from typing import Dict, Optional
from at_types import AirtableMetadata


# Mapping of Airtable functions to PostgreSQL equivalents
# Format: "AIRTABLE_FUNC" -> ("postgres_func", num_args, custom_handler_func)
FUNCTION_MAPPINGS = {
    # String functions
    "CONCATENATE": ("CONCAT", None, None),
    "LOWER": ("LOWER", 1, None),
    "UPPER": ("UPPER", 1, None),
    "TRIM": ("TRIM", 1, None),
    "LEFT": ("LEFT", 2, None),
    "RIGHT": ("RIGHT", 2, None),
    "MID": ("SUBSTRING", 3, lambda args: f"SUBSTRING({args[0]} FROM {args[1]} FOR {args[2]})"),
    "LEN": ("LENGTH", 1, None),
    "FIND": ("POSITION", 2, lambda args: f"POSITION({args[0]} IN {args[1]})"),
    "SUBSTITUTE": ("REPLACE", 3, None),
    "REPLACE": ("REPLACE", 3, None),
    
    # Math functions
    "ABS": ("ABS", 1, None),
    "ROUND": ("ROUND", 2, None),
    "ROUNDUP": ("CEIL", 1, None),
    "ROUNDDOWN": ("FLOOR", 1, None),
    "SQRT": ("SQRT", 1, None),
    "POWER": ("POWER", 2, None),
    "EXP": ("EXP", 1, None),
    "LOG": ("LN", 1, None),  # Natural log
    "LOG10": ("LOG", 1, None),  # Base 10 log
    "MOD": ("MOD", 2, None),
    "SUM": ("", None, lambda args: " + ".join(args)),  # Convert to addition
    "AVERAGE": ("", None, lambda args: f"({' + '.join(args)}) / {len(args)}"),
    "MIN": ("LEAST", None, None),
    "MAX": ("GREATEST", None, None),
    
    # Logical functions
    "IF": ("CASE", 3, lambda args: f"CASE WHEN {_convert_truthiness_check(args[0])} THEN {args[1]} ELSE {args[2]} END"),
    "AND": ("", None, lambda args: f"({' AND '.join(args)})"),
    "OR": ("", None, lambda args: f"({' OR '.join(args)})"),
    "NOT": ("NOT", 1, None),
    "BLANK": ("NULL", 0, lambda args: "NULL"),
    
    # Date functions
    "TODAY": ("CURRENT_DATE", 0, lambda args: "CURRENT_DATE"),
    "NOW": ("CURRENT_TIMESTAMP", 0, lambda args: "CURRENT_TIMESTAMP"),
    "YEAR": ("EXTRACT", 1, lambda args: f"EXTRACT(YEAR FROM {args[0]})"),
    "MONTH": ("EXTRACT", 1, lambda args: f"EXTRACT(MONTH FROM {args[0]})"),
    "DAY": ("EXTRACT", 1, lambda args: f"EXTRACT(DAY FROM {args[0]})"),
    "HOUR": ("EXTRACT", 1, lambda args: f"EXTRACT(HOUR FROM {args[0]})"),
    "MINUTE": ("EXTRACT", 1, lambda args: f"EXTRACT(MINUTE FROM {args[0]})"),
    "SECOND": ("EXTRACT", 1, lambda args: f"EXTRACT(SECOND FROM {args[0]})"),
    "WEEKDAY": ("EXTRACT", 1, lambda args: f"EXTRACT(DOW FROM {args[0]})"),
    "WEEKNUM": ("EXTRACT", 1, lambda args: f"EXTRACT(WEEK FROM {args[0]})"),
    
    # Type conversion
    "VALUE": ("CAST", 1, lambda args: f"CAST({args[0]} AS NUMERIC)"),
    "INT": ("FLOOR", 1, lambda args: f"FLOOR({args[0]})"),
    
    # Text functions
    "T": ("", 1, lambda args: f"COALESCE(CAST({args[0]} AS TEXT), '')"),
    "REPT": ("REPEAT", 2, None),
}


# Operator mappings
OPERATOR_MAPPINGS = {
    "&": "||",  # String concatenation
    "=": "=",
    "!=": "!=",
    "<": "<",
    ">": ">",
    "<=": "<=",
    ">=": ">=",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
}


class FormulaConversionError(Exception):
    """Raised when a formula cannot be converted to SQL"""
    pass


def _validate_no_unknown_functions(formula: str) -> None:
    """Validate that the formula doesn't contain unknown function calls.
    
    Args:
        formula: The formula string to validate
        
    Raises:
        FormulaConversionError: If unknown functions are found
    """
    # Pattern to match function calls: WORD(
    func_pattern = r'\b([A-Z_][A-Z0-9_]*)\s*\('
    
    for match in re.finditer(func_pattern, formula, re.IGNORECASE):
        func_name = match.group(1).upper()
        if func_name not in FUNCTION_MAPPINGS:
            raise FormulaConversionError(f"Unsupported function: {func_name}")


def convert_airtable_formula_to_sql(
    formula: str,
    field_name_map: Dict[str, str],
    field_type_map: Optional[Dict[str, str]] = None,
    _depth: int = 0,
    _max_depth: int = 50
) -> str:
    """Convert an Airtable formula to PostgreSQL SQL expression.
    
    Args:
        formula: The Airtable formula string
        field_name_map: Mapping of field IDs to PostgreSQL column names
        field_type_map: Mapping of field IDs to PostgreSQL types (optional)
        _depth: Internal recursion depth counter (for future recursive expansion)
        _max_depth: Maximum recursion depth allowed
        
    Returns:
        PostgreSQL SQL expression
        
    Raises:
        FormulaConversionError: If the formula cannot be converted
        
    Examples:
        >>> convert_airtable_formula_to_sql(
        ...     "IF({fld123} > 10, \"High\", \"Low\")",
        ...     {"fld123": "amount"}
        ... )
        "CASE WHEN amount > 10 THEN 'High' ELSE 'Low' END"
    """
    # Recursion depth check (protection for future recursive formula expansion)
    if _depth > _max_depth:
        raise FormulaConversionError(f"Maximum recursion depth ({_max_depth}) exceeded - possible circular reference")
    
    try:
        # Replace field references first
        sql = _replace_field_references(formula, field_name_map)
        
        # Check for unknown functions before conversion
        _validate_no_unknown_functions(sql)
        
        # Convert functions
        sql = _convert_functions(sql)
        
        # Convert operators (pass field_type_map for array handling)
        sql = _convert_operators(sql, field_type_map)
        
        # Convert double-quoted string literals to single quotes for PostgreSQL
        sql = _convert_string_literals(sql)
        
        # Convert boolean literals
        sql = sql.replace("TRUE", "true").replace("FALSE", "false")
        
        return sql
        
    except FormulaConversionError:
        # Re-raise our own errors without wrapping
        raise
    except Exception as e:
        raise FormulaConversionError(f"Failed to convert formula: {str(e)}")


def _replace_field_references(formula: str, field_name_map: Dict[str, str]) -> str:
    """Replace Airtable field references {fldXXX} with PostgreSQL column names.
    
    Args:
        formula: The formula string
        field_name_map: Mapping of field IDs to column names
        
    Returns:
        Formula with field references replaced
    """
    def replace_field(match):
        field_id = match.group(1)
        if field_id in field_name_map:
            return field_name_map[field_id]
        else:
            # Keep the original reference if not in map
            return match.group(0)
    
    # Match field references: {fldXXXXXXXXXXXXXX}
    return re.sub(r'\{(fld[a-zA-Z0-9]+)\}', replace_field, formula)


def _convert_truthiness_check(condition: str) -> str:
    """Convert a simple field reference to a proper SQL boolean condition.
    
    In Airtable, you can use IF(field, ...) where field is any type.
    In SQL, CASE WHEN requires explicit boolean conditions.
    This converts a field name to a proper NULL/empty check.
    
    Args:
        condition: The condition expression (may be a simple field name)
        
    Returns:
        A proper boolean SQL expression
    """
    # Strip whitespace
    condition = condition.strip()
    
    # Check if it's a simple field reference (alphanumeric/underscore only, no operators)
    # This catches converted field names like "company_type_dm_link"
    if re.match(r'^[a-z_][a-z0-9_]*$', condition, re.IGNORECASE):
        # It's a simple field reference - convert to explicit NULL/empty check
        # This works for TEXT and most scalar types
        return f"({condition} IS NOT NULL AND {condition} != '')"
    
    # Otherwise assume it's already a boolean expression
    return condition


def _convert_functions(formula: str) -> str:
    """Convert Airtable functions to PostgreSQL equivalents.
    
    Args:
        formula: The formula string with field references already replaced
        
    Returns:
        Formula with functions converted
    """
    # Build a pattern that matches any supported function
    # This is more efficient than checking each function separately
    func_names = '|'.join(re.escape(func) for func in FUNCTION_MAPPINGS.keys())
    pattern = rf'\b({func_names})\s*\('
    
    # Collect all matches first, then process in reverse order
    # This prevents position shifting issues with nested functions
    matches = list(re.finditer(pattern, formula, re.IGNORECASE))
    
    # Process matches from end to beginning to maintain correct positions
    result = formula
    for match in reversed(matches):
        airtable_func = match.group(1).upper()
        
        # Check if function is in mapping
        if airtable_func not in FUNCTION_MAPPINGS:
            raise FormulaConversionError(f"Function {airtable_func} not supported")
        
        postgres_func, expected_args, custom_handler = FUNCTION_MAPPINGS[airtable_func]
        
        start = match.start()
        func_start = match.end() - 1  # Position of opening paren
        
        # Find matching closing paren
        paren_count = 1
        i = func_start + 1
        in_string = False
        escape_next = False
        
        while i < len(result) and paren_count > 0:
            char = result[i]
            
            if escape_next:
                escape_next = False
                i += 1
                continue
            
            if char == '\\':
                escape_next = True
            elif char == '"' and not escape_next:
                in_string = not in_string
            elif not in_string:
                if char == '(':
                    paren_count += 1
                elif char == ')':
                    paren_count -= 1
            
            i += 1
        
        if paren_count != 0:
            raise FormulaConversionError(f"Unmatched parentheses in function {airtable_func}")
        
        # Extract arguments
        args_str = result[func_start + 1:i - 1]
        args = _parse_function_args(args_str)
        
        # Apply custom handler or default conversion
        if custom_handler:
            replacement = custom_handler(args)
        elif postgres_func:
            replacement = f"{postgres_func}({', '.join(args)})"
        else:
            # No direct equivalent
            raise FormulaConversionError(f"Function {airtable_func} not supported")
        
        # Replace this function call in the result
        result = result[:start] + replacement + result[i:]
    
    return result


def _parse_function_args(args_str: str) -> list:
    """Parse function arguments, respecting nested parentheses and quotes.
    
    Args:
        args_str: The arguments string (without outer parentheses)
        
    Returns:
        List of argument strings
    """
    args = []
    current_arg = []
    paren_depth = 0
    in_string = False
    escape_next = False
    
    for char in args_str:
        if escape_next:
            current_arg.append(char)
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            current_arg.append(char)
            continue
        
        if char == '"' and not escape_next:
            in_string = not in_string
            current_arg.append(char)
            continue
        
        if not in_string:
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
            elif char == ',' and paren_depth == 0:
                # End of this argument
                args.append(''.join(current_arg).strip())
                current_arg = []
                continue
        
        current_arg.append(char)
    
    # Add last argument
    if current_arg:
        args.append(''.join(current_arg).strip())
    
    return args


def _convert_operators(formula: str, field_type_map: Optional[Dict[str, str]] = None) -> str:
    """Convert Airtable operators to PostgreSQL equivalents.
    
    Args:
        formula: The formula string
        field_type_map: Mapping of field names to PostgreSQL types (optional)
        
    Returns:
        Formula with operators converted
    """
    # Convert & to || for string concatenation
    # Be careful not to convert inside strings
    result = []
    in_string = False
    escape_next = False
    
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if escape_next:
            result.append(char)
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            result.append(char)
            i += 1
            continue
        
        if char == '"':
            in_string = not in_string
            result.append(char)
            i += 1
            continue
        
        if not in_string and char == '&':
            # Check if it's the concatenation operator
            # (not part of a string literal)
            result.append('||')
            i += 1
            continue
        
        result.append(char)
        i += 1
    
    formula_str = ''.join(result)
    
    # Convert =NULL and !=NULL to IS NULL and IS NOT NULL
    # This handles Airtable's NULL comparison which doesn't work in SQL
    formula_str = re.sub(r'\s*=\s*NULL\b', ' IS NULL', formula_str, flags=re.IGNORECASE)
    formula_str = re.sub(r'\s*!=\s*NULL\b', ' IS NOT NULL', formula_str, flags=re.IGNORECASE)
    formula_str = re.sub(r'\s*<>\s*NULL\b', ' IS NOT NULL', formula_str, flags=re.IGNORECASE)
    
    # Fix array concatenation with string delimiters (e.g., array1||','||array2)
    # This pattern fails in PostgreSQL because ',' is interpreted as a malformed array literal
    # We need to detect this pattern and convert it properly
    formula_str = _fix_array_concatenation_with_delimiters(formula_str, field_type_map)
    
    return formula_str


def _fix_array_concatenation_with_delimiters(formula: str, field_type_map: Optional[Dict[str, str]] = None) -> str:
    """Fix array concatenation with string delimiters pattern.
    
    Airtable allows: array1 & "," & array2 & "," & array3
    After operator conversion this becomes: array1||","||array2||","||array3
    (Note: still double-quoted at this stage, single quote conversion happens later)
    
    In PostgreSQL, this fails because "," will become ',' and is interpreted as a malformed array literal.
    
    If field_type_map indicates these are arrays, we need to convert to:
    array_to_string(array1 || array2 || array3, ",")
    
    Args:
        formula: The SQL formula string with || operators
        field_type_map: Mapping of field names to PostgreSQL types
        
    Returns:
        Fixed formula
    """
    # Pattern: Look for sequences like: field1||"delim"||field2||"delim"||field3
    # where fields are array types (end with [])
    # Note: At this stage, string literals still use double quotes (before _convert_string_literals)
    
    # Pattern: multiple ||"str"|| sequences
    # This suggests someone is trying to join with a delimiter
    delimiter_pattern = r'\|\|"([^"]+)"\|\|'
    
    # Check if formula has multiple delimiter patterns
    delimiter_matches = list(re.finditer(delimiter_pattern, formula))
    
    if len(delimiter_matches) >= 2:
        # Likely array concatenation with delimiters
        # Extract the delimiter (should be consistent)
        delimiters = [m.group(1) for m in delimiter_matches]
        
        # Check if delimiters are consistent
        if len(set(delimiters)) == 1:
            delimiter = delimiters[0]
            
            # Remove all ||"delimiter"|| patterns to get clean array concatenation
            # This converts: array1||","||array2||","||array3
            # To: array1||array2||array3
            clean_formula = re.sub(delimiter_pattern, '||', formula)
            
            # Wrap in array_to_string
            # Note: This assumes the result should be TEXT not TEXT[]
            # Keep delimiter in double quotes - it will be converted to single quotes later
            return f'array_to_string({clean_formula}, "{delimiter}")'
    
    return formula


def _convert_string_literals(formula: str) -> str:
    """Convert double-quoted string literals to single quotes for PostgreSQL.
    
    PostgreSQL uses single quotes for string literals, while Airtable uses double quotes.
    This function converts all double-quoted strings to single-quoted strings.
    
    Args:
        formula: The formula string with double-quoted literals
        
    Returns:
        Formula with single-quoted string literals
    """
    result = []
    in_string = False
    escape_next = False
    
    i = 0
    while i < len(formula):
        char = formula[i]
        
        if escape_next:
            # Keep escaped characters as-is but handle quote escaping differently
            if in_string:
                # Inside a string - escape single quotes for PostgreSQL
                if char == "'":
                    result.append("''")
                elif char == '"':
                    # Escaped double quote inside double-quoted string becomes just the quote
                    result.append(char)
                else:
                    result.append(char)
            else:
                result.append(char)
            escape_next = False
            i += 1
            continue
        
        if char == '\\':
            escape_next = True
            # Don't append backslash yet, handle in next iteration
            i += 1
            continue
        
        if char == '"':
            # Convert double quotes to single quotes
            result.append("'")
            in_string = not in_string
            i += 1
            continue
        
        if in_string and char == "'":
            # Escape single quotes inside strings for PostgreSQL
            result.append("''")
            i += 1
            continue
        
        result.append(char)
        i += 1
    
    return ''.join(result)


def convert_formula_to_generated_column(
    field_name: str,
    formula: str,
    field_name_map: Dict[str, str],
    postgres_type: str,
    field_type_map: Optional[Dict[str, str]] = None
) -> str:
    """Convert an Airtable formula to a PostgreSQL generated column definition.
    
    Args:
        field_name: The PostgreSQL column name
        formula: The Airtable formula
        field_name_map: Mapping of field IDs to PostgreSQL column names
        postgres_type: The PostgreSQL type for this column
        field_type_map: Mapping of field IDs to PostgreSQL types (optional)
        
    Returns:
        PostgreSQL column definition with GENERATED ALWAYS AS clause
        
    Example:
        >>> convert_formula_to_generated_column(
        ...     "total",
        ...     "{fld123} * {fld456}",
        ...     {"fld123": "price", "fld456": "quantity"},
        ...     "NUMERIC"
        ... )
        'total NUMERIC GENERATED ALWAYS AS (price * quantity) STORED'
    """
    try:
        sql_expr = convert_airtable_formula_to_sql(formula, field_name_map, field_type_map)
        return f"{field_name} {postgres_type} GENERATED ALWAYS AS ({sql_expr}) STORED"
    except FormulaConversionError:
        # If conversion fails, fall back to regular column
        raise


# List of Airtable functions that are NOT supported for conversion
UNSUPPORTED_FUNCTIONS = {
    # Array/aggregation functions that need record links
    "ARRAYJOIN",
    "ARRAYUNIQUE",
    "ARRAYCOMPACT",
    "ARRAYFLATTEN",
    
    # Lookup-based functions
    "COUNTALL",
    "COUNTA",
    
    # Airtable-specific functions
    "RECORD_ID",
    "CREATED_TIME",
    "LAST_MODIFIED_TIME",
    "CREATED_BY",
    "LAST_MODIFIED_BY",
    
    # Advanced functions that need complex logic
    "SWITCH",  # Could be implemented with nested CASE but complex
    "REGEX_MATCH",
    "REGEX_EXTRACT",
    "REGEX_REPLACE",
    
    # Encoding functions
    "ENCODE_URL_COMPONENT",
}


def is_formula_convertible(
    formula: str,
    field_name_map: Optional[Dict[str, str]] = None,
    field_type_map: Optional[Dict[str, str]] = None
) -> bool:
    """Check if a formula can be reasonably converted to SQL.
    
    Args:
        formula: The Airtable formula string
        field_name_map: Optional mapping of field IDs to column names
        field_type_map: Optional mapping of column names to PostgreSQL types
        
    Returns:
        True if the formula appears convertible, False otherwise
    """
    # Check for unsupported functions
    for func in UNSUPPORTED_FUNCTIONS:
        if re.search(rf'\b{func}\s*\(', formula, re.IGNORECASE):
            return False
    
    # Check if formula references array fields (array operations are not immutable in PostgreSQL)
    if field_name_map and field_type_map:
        # Find all field references in the formula
        field_refs = re.findall(r'\{([^}]+)\}', formula)
        for field_ref in field_refs:
            # Map field ID to column name
            column_name = field_name_map.get(field_ref)
            if column_name and column_name in field_type_map:
                col_type = field_type_map[column_name]
                # If it's an array type, the formula is not convertible
                if col_type and col_type.endswith('[]'):
                    return False
    
    # Check for record link references (can't be resolved in SQL)
    # These typically appear in formulas but reference linked records
    # We can't convert these without the actual data
    
    return True
