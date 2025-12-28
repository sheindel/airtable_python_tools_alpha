"""
Airtable Formula Evaluator

Evaluates Airtable formulas by parsing and executing them in Python.
Can be used both in CLI and web (PyScript) environments.
"""

import re
import math
from typing import Any, Union


class FormulaEvaluationError(Exception):
    """Raised when formula evaluation fails"""
    pass


class AirtableFunctions:
    """Implementation of Airtable formula functions"""
    
    # Logical functions
    @staticmethod
    def IF(condition: Any, true_value: Any, false_value: Any) -> Any:
        return true_value if condition else false_value
    
    @staticmethod
    def AND(*args) -> bool:
        return all(args)
    
    @staticmethod
    def OR(*args) -> bool:
        return any(args)
    
    @staticmethod
    def NOT(value: Any) -> bool:
        return not value
    
    @staticmethod
    def XOR(*args) -> bool:
        return sum(bool(arg) for arg in args) == 1
    
    # Comparison functions
    @staticmethod
    def ISEMAIL(value: str) -> bool:
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def ISURL(value: str) -> bool:
        try:
            from urllib.parse import urlparse
            result = urlparse(str(value))
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    # Numeric functions
    @staticmethod
    def ABS(value: float) -> float:
        return abs(float(value))
    
    @staticmethod
    def ROUND(value: float, precision: int = 0) -> float:
        return round(float(value), int(precision))
    
    @staticmethod
    def ROUNDUP(value: float, precision: int = 0) -> float:
        multiplier = 10 ** int(precision)
        return math.ceil(float(value) * multiplier) / multiplier
    
    @staticmethod
    def ROUNDDOWN(value: float, precision: int = 0) -> float:
        multiplier = 10 ** int(precision)
        return math.floor(float(value) * multiplier) / multiplier
    
    @staticmethod
    def INT(value: float) -> int:
        return int(math.floor(float(value)))
    
    @staticmethod
    def CEILING(value: float) -> int:
        return math.ceil(float(value))
    
    @staticmethod
    def FLOOR(value: float) -> int:
        return math.floor(float(value))
    
    @staticmethod
    def SQRT(value: float) -> float:
        return math.sqrt(float(value))
    
    @staticmethod
    def POWER(base: float, exponent: float) -> float:
        return float(base) ** float(exponent)
    
    @staticmethod
    def EXP(value: float) -> float:
        return math.exp(float(value))
    
    @staticmethod
    def LOG(value: float) -> float:
        return math.log(float(value))
    
    @staticmethod
    def LOG10(value: float) -> float:
        return math.log10(float(value))
    
    @staticmethod
    def MOD(n: float, d: float) -> float:
        return float(n) % float(d)
    
    # Statistical functions
    @staticmethod
    def SUM(*args) -> float:
        return sum(float(arg) for arg in args)
    
    @staticmethod
    def AVERAGE(*args) -> float:
        return sum(float(arg) for arg in args) / len(args)
    
    @staticmethod
    def MIN(*args) -> float:
        return min(float(arg) for arg in args)
    
    @staticmethod
    def MAX(*args) -> float:
        return max(float(arg) for arg in args)
    
    @staticmethod
    def COUNT(*args) -> int:
        return len(args)
    
    @staticmethod
    def COUNTA(*args) -> int:
        return sum(1 for arg in args if arg not in (None, '', []))
    
    # String functions
    @staticmethod
    def CONCATENATE(*args) -> str:
        return ''.join(str(arg) for arg in args)
    
    @staticmethod
    def LEFT(text: str, num_chars: int) -> str:
        return str(text)[:int(num_chars)]
    
    @staticmethod
    def RIGHT(text: str, num_chars: int) -> str:
        return str(text)[-int(num_chars):]
    
    @staticmethod
    def MID(text: str, start: int, count: int) -> str:
        start_idx = int(start) - 1  # Airtable uses 1-based indexing
        return str(text)[start_idx:start_idx + int(count)]
    
    @staticmethod
    def LEN(text: str) -> int:
        return len(str(text))
    
    @staticmethod
    def LOWER(text: str) -> str:
        return str(text).lower()
    
    @staticmethod
    def UPPER(text: str) -> str:
        return str(text).upper()
    
    @staticmethod
    def TRIM(text: str) -> str:
        return str(text).strip()
    
    @staticmethod
    def SUBSTITUTE(text: str, old_text: str, new_text: str, instance_num: int = None) -> str:
        text = str(text)
        old = str(old_text)
        new = str(new_text)
        
        if instance_num is None:
            return text.replace(old, new)
        else:
            parts = text.split(old)
            if int(instance_num) <= len(parts) - 1:
                parts[int(instance_num)] = new + parts[int(instance_num)]
                return old.join(parts)
            return text
    
    @staticmethod
    def REPLACE(text: str, start: int, count: int, new_text: str) -> str:
        text = str(text)
        start_idx = int(start) - 1
        return text[:start_idx] + str(new_text) + text[start_idx + int(count):]
    
    @staticmethod
    def FIND(search_text: str, text: str, start_pos: int = 1) -> int:
        text = str(text)
        search = str(search_text)
        start = int(start_pos) - 1
        
        idx = text.find(search, start)
        return idx + 1 if idx != -1 else 0  # Airtable returns 0 for not found
    
    @staticmethod
    def SEARCH(search_text: str, text: str, start_pos: int = 1) -> int:
        # Case-insensitive version of FIND
        text = str(text).lower()
        search = str(search_text).lower()
        start = int(start_pos) - 1
        
        idx = text.find(search, start)
        return idx + 1 if idx != -1 else 0
    
    @staticmethod
    def REPT(text: str, times: int) -> str:
        return str(text) * int(times)
    
    @staticmethod
    def VALUE(text: str) -> float:
        return float(text)
    
    @staticmethod
    def T(value: Any) -> str:
        return str(value) if isinstance(value, str) else ""
    
    # Date/Time functions
    @staticmethod
    def DATETIME_FORMAT(date_value: Any, format_string: str = None) -> str:
        """
        Format a datetime value according to a format string.
        
        Note: This is a simplified implementation. Full Airtable format string
        support would require comprehensive datetime formatting logic.
        For now, returns ISO format or string representation.
        """
        from datetime import datetime
        
        # If no format string provided, return ISO format
        if format_string is None:
            if isinstance(date_value, datetime):
                return date_value.isoformat()
            return str(date_value)
        
        # Convert to datetime if string
        if isinstance(date_value, str):
            try:
                date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except Exception:
                return str(date_value)
        
        if isinstance(date_value, datetime):
            # Basic format string mapping (simplified)
            # Airtable uses moment.js-style format strings
            # This is a basic implementation for common cases
            try:
                # Map some common Airtable format tokens to Python strftime
                format_map = {
                    'YYYY': '%Y',
                    'MM': '%m',
                    'DD': '%d',
                    'HH': '%H',
                    'mm': '%M',
                    'ss': '%S',
                    'M': '%-m',
                    'D': '%-d',
                    'H': '%-H',
                }
                
                python_format = format_string
                for at_token, py_token in format_map.items():
                    python_format = python_format.replace(at_token, py_token)
                
                return date_value.strftime(python_format)
            except Exception:
                # If formatting fails, return ISO format
                return date_value.isoformat()
        
        return str(date_value)
    
    # Special functions
    @staticmethod
    def BLANK() -> str:
        return ""
    
    @staticmethod
    def ISERROR(value: Any) -> bool:
        return isinstance(value, Exception)
    
    @staticmethod
    def ERROR(message: str = "ERROR") -> Exception:
        return FormulaEvaluationError(message)
    
    @staticmethod
    def SWITCH(expression: Any, *args) -> Any:
        """SWITCH(expr, pattern1, result1, pattern2, result2, ..., [default])"""
        for i in range(0, len(args) - 1, 2):
            if expression == args[i]:
                return args[i + 1]
        # Return default if odd number of args, otherwise raise error
        if len(args) % 2 == 1:
            return args[-1]
        raise FormulaEvaluationError("No match found in SWITCH")
    
    # Array functions
    @staticmethod
    def ARRAYJOIN(array: Any, separator: str = ", ") -> str:
        if isinstance(array, (list, tuple)):
            return separator.join(str(item) for item in array)
        return str(array)
    
    @staticmethod
    def ARRAYCOMPACT(array: Any) -> list:
        if isinstance(array, (list, tuple)):
            return [item for item in array if item not in (None, '', [])]
        return [array]
    
    @staticmethod
    def ARRAYUNIQUE(array: Any) -> list:
        if isinstance(array, (list, tuple)):
            seen = set()
            result = []
            for item in array:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        return [array]
    
    @staticmethod
    def ARRAYFLATTEN(array: Any) -> list:
        def flatten(lst):
            result = []
            for item in lst:
                if isinstance(item, (list, tuple)):
                    result.extend(flatten(item))
                else:
                    result.append(item)
            return result
        
        if isinstance(array, (list, tuple)):
            return flatten(array)
        return [array]


def tokenize_formula(formula: str) -> list:
    """Tokenize an Airtable formula into processable tokens"""
    tokens = []
    i = 0
    
    while i < len(formula):
        char = formula[i]
        
        # Skip whitespace
        if char.isspace():
            i += 1
            continue
        
        # Field references {fldXXXXXXXXXXXXXX}
        if char == '{':
            # Check if this looks like a field reference
            match = re.match(r'\{(fld[a-zA-Z0-9]{14})\}', formula[i:])
            if match:
                field_id = match.group(1)
                tokens.append({'type': 'field_ref', 'value': field_id})
                i += len(match.group(0))
                continue
        
        # String literals (both double and single quotes)
        if char in ('"', "'"):
            quote_char = char
            value = ''
            i += 1
            while i < len(formula) and formula[i] != quote_char:
                value += formula[i]
                i += 1
            i += 1  # Skip closing quote
            tokens.append({'type': 'string', 'value': value})
            continue
        
        # Numbers
        if char.isdigit() or (char == '.' and i + 1 < len(formula) and formula[i + 1].isdigit()):
            value = ''
            while i < len(formula) and (formula[i].isdigit() or formula[i] == '.'):
                value += formula[i]
                i += 1
            tokens.append({'type': 'number', 'value': float(value)})
            continue
        
        # Function names and identifiers
        if char.isupper() or char == '_':
            value = ''
            while i < len(formula) and (formula[i].isupper() or formula[i].isdigit() or formula[i] == '_'):
                value += formula[i]
                i += 1
            
            # Check for special values
            if value == 'TRUE':
                tokens.append({'type': 'boolean', 'value': True})
            elif value == 'FALSE':
                tokens.append({'type': 'boolean', 'value': False})
            elif value == 'BLANK':
                tokens.append({'type': 'function', 'value': 'BLANK'})
            else:
                tokens.append({'type': 'function', 'value': value})
            continue
        
        # Operators
        if char in '()+-*/%,<>=!&':
            # Check for multi-char operators
            if i + 1 < len(formula):
                two_char = char + formula[i + 1]
                if two_char in ('<=', '>=', '!=', '=='):
                    tokens.append({'type': 'operator', 'value': two_char})
                    i += 2
                    continue
            
            tokens.append({'type': 'operator', 'value': char})
            i += 1
            continue
        
        # Unknown character - skip it
        i += 1
    
    return tokens


def parse_expression(tokens: list, start: int = 0) -> tuple:
    """Parse tokens into an expression tree"""
    pos = start
    
    def parse_value():
        nonlocal pos
        
        if pos >= len(tokens):
            raise FormulaEvaluationError('Unexpected end of expression')
        
        token = tokens[pos]
        
        # Literal values
        if token['type'] in ('string', 'number', 'boolean'):
            pos += 1
            return {'type': 'literal', 'value': token['value']}
        
        # Field references (unresolved)
        if token['type'] == 'field_ref':
            pos += 1
            return {'type': 'field_ref', 'value': token['value']}
        
        # Function calls
        if token['type'] == 'function':
            func_name = token['value']
            pos += 1
            
            # BLANK() is special - no parens needed sometimes
            if func_name == 'BLANK' and (pos >= len(tokens) or tokens[pos]['value'] != '('):
                return {'type': 'call', 'function': func_name, 'args': []}
            
            if pos >= len(tokens) or tokens[pos]['value'] != '(':
                raise FormulaEvaluationError(f"Expected '(' after function {func_name}")
            pos += 1  # Skip '('
            
            args = []
            while pos < len(tokens) and tokens[pos]['value'] != ')':
                arg_expr, pos = parse_expression(tokens, pos)
                args.append(arg_expr)
                
                if pos < len(tokens) and tokens[pos]['value'] == ',':
                    pos += 1  # Skip comma
            
            if pos >= len(tokens) or tokens[pos]['value'] != ')':
                raise FormulaEvaluationError(f"Expected ')' after function arguments")
            pos += 1  # Skip ')'
            
            return {'type': 'call', 'function': func_name, 'args': args}
        
        # Parenthesized expressions
        if token['value'] == '(':
            pos += 1  # Skip '('
            expr, pos = parse_expression(tokens, pos)
            
            if pos >= len(tokens) or tokens[pos]['value'] != ')':
                raise FormulaEvaluationError('Expected closing parenthesis')
            pos += 1  # Skip ')'
            return expr
        
        raise FormulaEvaluationError(f'Unexpected token: {token}')
    
    # Parse left side
    left = parse_value()
    
    # Handle operators
    while pos < len(tokens) and tokens[pos]['type'] == 'operator':
        operator = tokens[pos]['value']
        
        # Stop at commas and closing parens
        if operator in (',', ')'):
            break
        
        pos += 1  # Move past operator
        right = parse_value()
        
        left = {
            'type': 'binary',
            'operator': operator,
            'left': left,
            'right': right,
        }
    
    return left, pos


def evaluate_node(node: dict, functions: AirtableFunctions = None) -> Any:
    """Evaluate an expression tree node"""
    if functions is None:
        functions = AirtableFunctions()
    
    if node['type'] == 'literal':
        return node['value']
    
    if node['type'] == 'call':
        func_name = node['function']
        func = getattr(functions, func_name, None)
        
        if not func:
            raise FormulaEvaluationError(f"Unknown function: {func_name}")
        
        args = [evaluate_node(arg, functions) for arg in node['args']]
        return func(*args)
    
    if node['type'] == 'binary':
        left = evaluate_node(node['left'], functions)
        right = evaluate_node(node['right'], functions)
        operator = node['operator']
        
        if operator == '+':
            return left + right
        elif operator == '-':
            return left - right
        elif operator == '*':
            return left * right
        elif operator == '/':
            if right == 0:
                raise FormulaEvaluationError("Division by zero")
            return left / right
        elif operator == '%':
            return left % right
        elif operator == '<':
            return left < right
        elif operator == '>':
            return left > right
        elif operator == '<=':
            return left <= right
        elif operator == '>=':
            return left >= right
        elif operator in ('=', '=='):
            return left == right
        elif operator == '!=':
            return left != right
        elif operator == '&':
            return str(left) + str(right)
        else:
            raise FormulaEvaluationError(f"Unknown operator: {operator}")
    
    raise FormulaEvaluationError(f"Unknown node type: {node['type']}")


def node_to_string(node: dict) -> str:
    """Convert an AST node back to formula string"""
    if node['type'] == 'literal':
        value = node['value']
        if isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, bool):
            return 'TRUE' if value else 'FALSE'
        else:
            return str(value)
    
    if node['type'] == 'field_ref':
        # Keep field references as-is
        return '{' + node['value'] + '}'
    
    if node['type'] == 'call':
        func_name = node['function']
        if not node['args']:
            return f"{func_name}()"
        args_str = ', '.join(node_to_string(arg) for arg in node['args'])
        return f"{func_name}({args_str})"
    
    if node['type'] == 'binary':
        left_str = node_to_string(node['left'])
        right_str = node_to_string(node['right'])
        operator = node['operator']
        
        # Add parentheses for nested expressions to preserve precedence
        if node['left']['type'] == 'binary':
            left_str = f"({left_str})"
        if node['right']['type'] == 'binary':
            right_str = f"({right_str})"
        
        return f"{left_str} {operator} {right_str}"
    
    return str(node)


def partial_evaluate_node(node: dict, functions: AirtableFunctions = None) -> tuple[dict, bool]:
    """
    Partially evaluate an AST node, simplifying where possible
    
    Returns:
        (simplified_node, was_evaluated) - if was_evaluated is True, the node is a complete literal
    """
    if functions is None:
        functions = AirtableFunctions()
    
    # Literals are already evaluated
    if node['type'] == 'literal':
        return node, True
    
    # Field references can't be evaluated (they're unresolved)
    if node['type'] == 'field_ref':
        return node, False
    
    # Try to evaluate function calls
    if node['type'] == 'call':
        func_name = node['function']
        
        # Try to partially evaluate all arguments
        evaluated_args = []
        all_args_evaluated = True
        
        for arg in node['args']:
            eval_arg, was_evaluated = partial_evaluate_node(arg, functions)
            evaluated_args.append(eval_arg)
            if not was_evaluated:
                all_args_evaluated = False
        
        # Special handling for IF statements
        if func_name == 'IF' and len(evaluated_args) >= 3:
            condition_node = evaluated_args[0]
            cond_evaluated = (condition_node['type'] == 'literal')
            
            if cond_evaluated:
                # Condition is known, return appropriate branch
                condition_value = condition_node['value']
                if condition_value:
                    # Return true branch
                    return evaluated_args[1], (evaluated_args[1]['type'] == 'literal')
                else:
                    # Return false branch
                    return evaluated_args[2], (evaluated_args[2]['type'] == 'literal')
        
        # Special handling for AND/OR - can short-circuit
        if func_name == 'AND':
            # If any argument is FALSE, the whole thing is FALSE
            for arg in evaluated_args:
                if arg['type'] == 'literal' and not arg['value']:
                    return {'type': 'literal', 'value': False}, True
            
            # Remove all TRUE literals
            filtered_args = [arg for arg in evaluated_args if not (arg['type'] == 'literal' and arg['value'])]
            
            if not filtered_args:
                # All were TRUE
                return {'type': 'literal', 'value': True}, True
            elif len(filtered_args) == 1:
                # Only one arg left
                return filtered_args[0], (filtered_args[0]['type'] == 'literal')
            else:
                # Multiple args remain
                return {'type': 'call', 'function': 'AND', 'args': filtered_args}, False
        
        if func_name == 'OR':
            # If any argument is TRUE, the whole thing is TRUE
            for arg in evaluated_args:
                if arg['type'] == 'literal' and arg['value']:
                    return {'type': 'literal', 'value': True}, True
            
            # Remove all FALSE literals
            filtered_args = [arg for arg in evaluated_args if not (arg['type'] == 'literal' and not arg['value'])]
            
            if not filtered_args:
                # All were FALSE
                return {'type': 'literal', 'value': False}, True
            elif len(filtered_args) == 1:
                # Only one arg left
                return filtered_args[0], (filtered_args[0]['type'] == 'literal')
            else:
                # Multiple args remain
                return {'type': 'call', 'function': 'OR', 'args': filtered_args}, False
        
        # If all arguments are evaluated, try to evaluate the function
        if all_args_evaluated:
            func = getattr(functions, func_name, None)
            if func:
                try:
                    args_values = [arg['value'] for arg in evaluated_args]
                    result = func(*args_values)
                    return {'type': 'literal', 'value': result}, True
                except Exception:
                    # Evaluation failed, return the node with evaluated args
                    pass
        
        # Return function call with partially evaluated arguments
        return {'type': 'call', 'function': func_name, 'args': evaluated_args}, False
    
    # Try to evaluate binary operations
    if node['type'] == 'binary':
        left_node, left_evaluated = partial_evaluate_node(node['left'], functions)
        right_node, right_evaluated = partial_evaluate_node(node['right'], functions)
        
        # If both sides are evaluated, compute the result
        if left_evaluated and right_evaluated:
            try:
                left_val = left_node['value']
                right_val = right_node['value']
                operator = node['operator']
                
                result = None
                if operator == '+':
                    result = left_val + right_val
                elif operator == '-':
                    result = left_val - right_val
                elif operator == '*':
                    result = left_val * right_val
                elif operator == '/':
                    if right_val != 0:
                        result = left_val / right_val
                elif operator == '%':
                    result = left_val % right_val
                elif operator == '<':
                    result = left_val < right_val
                elif operator == '>':
                    result = left_val > right_val
                elif operator == '<=':
                    result = left_val <= right_val
                elif operator == '>=':
                    result = left_val >= right_val
                elif operator in ('=', '=='):
                    result = left_val == right_val
                elif operator == '!=':
                    result = left_val != right_val
                elif operator == '&':
                    result = str(left_val) + str(right_val)
                
                if result is not None:
                    return {'type': 'literal', 'value': result}, True
            except Exception:
                # Evaluation failed, return the node with evaluated children
                pass
        
        # Return binary operation with partially evaluated children
        return {
            'type': 'binary',
            'operator': node['operator'],
            'left': left_node,
            'right': right_node
        }, False
    
    # Unknown node type
    return node, False


def evaluate_formula(formula: str) -> Any:
    """
    Main evaluation function for Airtable formulas
    
    Args:
        formula: The Airtable formula to evaluate
        
    Returns:
        The result of the formula evaluation
        
    Raises:
        FormulaEvaluationError: If the formula cannot be evaluated
    """
    try:
        # Tokenize the formula
        tokens = tokenize_formula(formula)
        
        # Parse into expression tree
        ast, _ = parse_expression(tokens, 0)
        
        # Evaluate the tree
        return evaluate_node(ast)
    except Exception as e:
        if isinstance(e, FormulaEvaluationError):
            raise
        raise FormulaEvaluationError(f"Failed to evaluate formula: {str(e)}")


def simplify_formula(formula: str) -> str:
    """
    Simplify a formula by partially evaluating it
    
    This performs partial evaluation - if parts of the formula can be computed,
    they will be simplified. For example:
    - IF(TRUE, A, B) -> A
    - IF(FALSE, A, B) -> B
    - 2 + 3 -> 5
    - AND(TRUE, X) -> X
    
    Args:
        formula: The Airtable formula to simplify
        
    Returns:
        Simplified formula string
    """
    try:
        # Tokenize and parse
        tokens = tokenize_formula(formula)
        ast, _ = parse_expression(tokens, 0)
        
        # Partially evaluate
        simplified_ast, was_fully_evaluated = partial_evaluate_node(ast)
        
        # Convert back to string
        if was_fully_evaluated:
            # It's just a literal value
            return str(simplified_ast['value'])
        else:
            return node_to_string(simplified_ast)
    except Exception as e:
        # If simplification fails, return original formula
        return formula


def substitute_field_values(formula: str, field_values: dict) -> str:
    """
    Substitute field references in a formula with actual values
    
    Args:
        formula: Formula with field references like {fldXXXXXXXXXXXXXX}
        field_values: Dict mapping field IDs to values
        
    Returns:
        Formula with field references replaced by values
    """
    result = formula
    for field_id, value in field_values.items():
        pattern = f"{{{field_id}}}"
        if pattern in result:
            # Format the value appropriately
            if isinstance(value, bool):
                # Boolean values should be TRUE/FALSE keywords
                formatted_value = 'TRUE' if value else 'FALSE'
            elif isinstance(value, str):
                # Check if it's a boolean-like string
                if value.upper() == 'TRUE':
                    formatted_value = 'TRUE'
                elif value.upper() == 'FALSE':
                    formatted_value = 'FALSE'
                else:
                    # Try to parse as number first
                    try:
                        float(value)
                        # It's a numeric string, don't quote
                        formatted_value = value
                    except ValueError:
                        # It's text, quote it with single quotes (Airtable standard)
                        formatted_value = f"'{value}'"
            else:
                formatted_value = str(value)
            
            result = result.replace(pattern, formatted_value)
    return result


def get_unresolved_fields(formula: str) -> list:
    """
    Get list of unresolved field references in a formula
    
    Args:
        formula: Formula string to check
        
    Returns:
        List of field IDs that are still referenced
    """
    return re.findall(r'\{(fld[a-zA-Z0-9]{14})\}', formula)


if __name__ == "__main__":
    # Quick tests
    test_formulas = [
        "IF(TRUE, 'yes', 'no')",
        "2 + 3 * 4",
        "CONCATENATE('Hello', ' ', 'World')",
        "ROUND(3.14159, 2)",
        "IF(10 > 5, SUM(1, 2, 3), 0)",
    ]
    
    for formula in test_formulas:
        try:
            result = evaluate_formula(formula)
            print(f"✓ {formula} = {result}")
        except Exception as e:
            print(f"✗ {formula} → Error: {e}")
