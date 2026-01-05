import re
from dataclasses import dataclass
from typing import Any, List, Optional


# ============================================================================
# AST Node Definitions (Phase 1)
# ============================================================================

@dataclass
class FormulaNode:
    """Base class for all formula AST nodes"""
    node_type: str
    
@dataclass
class LiteralNode(FormulaNode):
    """Represents a literal value: 42, "hello", true"""
    value: Any
    data_type: str  # "number", "string", "boolean"
    
    def __init__(self, value: Any, data_type: str):
        super().__init__("literal")
        self.value = value
        self.data_type = data_type
    
@dataclass
class FieldReferenceNode(FormulaNode):
    """Reference to another field: {fldXXXXXXXXXXXXXX}"""
    field_id: str
    field_name: Optional[str] = None
    field_type: Optional[str] = None
    
    def __init__(self, field_id: str, field_name: Optional[str] = None, field_type: Optional[str] = None):
        super().__init__("field_reference")
        self.field_id = field_id
        self.field_name = field_name
        self.field_type = field_type
    
@dataclass
class FunctionCallNode(FormulaNode):
    """Function invocation: IF(condition, true_val, false_val)"""
    function_name: str
    arguments: List[FormulaNode]
    
    def __init__(self, function_name: str, arguments: List[FormulaNode]):
        super().__init__("function_call")
        self.function_name = function_name
        self.arguments = arguments
    
@dataclass
class BinaryOpNode(FormulaNode):
    """Binary operations: +, -, *, /, &, =, !=, <, >, etc."""
    operator: str
    left: FormulaNode
    right: FormulaNode
    
    def __init__(self, operator: str, left: FormulaNode, right: FormulaNode):
        super().__init__("binary_op")
        self.operator = operator
        self.left = left
        self.right = right
    
@dataclass
class UnaryOpNode(FormulaNode):
    """Unary operations: -, NOT"""
    operator: str
    operand: FormulaNode
    
    def __init__(self, operator: str, operand: FormulaNode):
        super().__init__("unary_op")
        self.operator = operator
        self.operand = operand


# ============================================================================
# Legacy Tokenizer (kept for backwards compatibility)
# ============================================================================

sample_formulas = [
    "IF({flddfGHN4ToYguiGj}, \r\n  IF(FIND(\"lost\",LOWER({flddUMM1OtEqyriCs})),\r\n    \"Previous\",\r\n    \"Current\"),\r\n  \"New\")",
    "FIND({fld6jAxjTe0g2LAgm},{fldaSAveZtp0ITolx}&\"\")>0",
    "{fldhj47fcAadgdADP}*(1-{fldjd2tXiXHAL5mGa})",
    "{fldSPNCyipj4ryWP6}&IF({fldgvPoP0MiEqrp1R},IF({fldSPNCyipj4ryWP6},\",\")&ARRAYJOIN({fldgvPoP0MiEqrp1R}))",
    "IF({fldK3mT15Iq25srUo}>0,IF({fldsgw7sX1Eedimx0}!=BLANK(),{fldK3mT15Iq25srUo}/{fldsgw7sX1Eedimx0},{fldK3mT15Iq25srUo}/{fldzBeDVJqyaIBcwl}))",
    "TRIM(RIGHT(CONCATENATE({fldvYGwZBESyjyp4g}),(LEN(CONCATENATE({fldvYGwZBESyjyp4g}))- FIND(\",\",CONCATENATE({fldvYGwZBESyjyp4g}))-1)))",
    "SWITCH(   LEFT({fldM8FrSyhBOj6HKA},1),\n  \"0\",\"0. Unready\",\n  \"1\",\"1. Ready\",\n  \"2\",\"2. Sampled\",\n  \"3\",\"3. Sent to Lab\",\n  \"4\",\"3. Sent to Lab\",\n  \"5\",\"3. Sent to Lab\",\n  \"6\",\"3. Sent to Lab\",\n  \"7\",\"7. Completed\",\n  \"8\",\"8. Costs Finalized\",\n  \"9\",\"9. Invoiced\",\n  \"Y\",\"Y. Cancelled\",\n  \"X\",\"X. Error\")"
]

# Find field IDs (supports both real IDs like fld12345678901234 and test IDs like fldAmount)
field_id_regex = r"{(fld[a-zA-Z0-9]+)}"

# Find boolean values (must come before function_name_regex to match TRUE/FALSE correctly)
boolean_regex = r"(\b(TRUE|FALSE)\b)"

# Find function names
function_name_regex = r"(\b[A-Z]+\b)"

# Find operators (including comma, comparison operators, and & for concatenation)
operator_regex = r"(!=|>=|<=|[,\+\-\*\/\(\)=<>&])"

# Find string literals
string_literal_regex = r"(\"[^\"]*\")"

# Find numbers
number_regex = r"(\b\d+(\.\d+)?\b)"

# Find whitespace
whitespace_regex = r"(\s+)"

patterns = [
    (field_id_regex, "FIELD_ID"),
    (boolean_regex, "BOOLEAN"),  # Must come before FUNCTION_NAME
    (function_name_regex, "FUNCTION_NAME"),
    (operator_regex, "OPERATOR"),
    (string_literal_regex, "STRING_LITERAL"),
    (number_regex, "NUMBER"),
    (whitespace_regex, "WHITESPACE"),
]

# Combine all regex into a single pattern
combined_regex = (
    "|".join(pattern for pattern, type in patterns)
)


class ParseError(Exception):
    def __init__(self, pos, msg, *args):
        self.pos = pos
        self.msg = msg
        self.args = args

    def __str__(self):
        return '%s at position %s' % (self.msg % self.args, self.pos)
    
class FormulaTokenNode:
    def __init__(self, token_type: str, value: str, start: int, end: int):
        self.token_type = token_type
        self.value = value
        self.start = start
        self.end = end
        self.children = []


    def add_child(self, child: 'FormulaTokenNode'):
        """
        Adds a child token to the current token.
        """
        self.children.append(child)

    def __repr__(self):
        return f"Token(type={self.token_type}, value={self.value}, start={self.start}, end={self.end})"
    
    def overlaps_token(self, other: 'FormulaTokenNode'):
        """
        Checks if this token overlaps with another token.
        """
        return (
            self.start < other.end and
            self.end > other.start
        )

    def __str__(self):
        """
        Returns a string representation of the token.
        """
        return f"{self.token_type}: {self.value} ({self.start}, {self.end})"
    

    def print_tree(self, depth=0, debug=False):
        """
        Prints the token and its children in a tree-like format.
        """

        if debug:
            print(f'{" " * depth}{self.value} ({len(self.children)})')
        else:
            print(f'{" " * depth}{self.value}')
        for child in self.children:
            child.print_tree(depth+1)


TokenList = list[FormulaTokenNode]


def tokenize(expression):
    """
    Tokenizes the given Airtable formula expression into a list of tokens.
    """

    tokens: TokenList = []
    # Find all matches for each regex pattern

    matches = re.finditer(combined_regex, expression)
    for match in matches:
        # Match the token type based on the regex pattern
        token_type = next((t for pattern, t in patterns if re.match(pattern, match.group(0))), None)
        if token_type is None:
            print("Warning: Unknown token type for match:", match.group(0))
            continue

        tokens.append(
            FormulaTokenNode(
                token_type,
                match.group(1) if match.group(1) else match.group(0),
                match.start(),
                match.end()
            )
        )

    # Sort tokens by their start position
    tokens.sort(key=lambda x: x.start)

    token_stack: TokenList = []
    last_token = None
    root_node = FormulaTokenNode("ROOT", "", 0, 0)
    token_stack.append(root_node)
    
    for token in tokens:
        if token.token_type == "WHITESPACE":
            continue

        if token.token_type == "OPERATOR" and token.value == ")":
            # Remove the last parent token once we close a paranthesis
            # TODO this could be our check for unmatched paranthesis
            if len(token_stack) <= 1:  # Can't pop root node
                raise ParseError(token.start, "Unmatched closing parenthesis")
            token_stack.pop()
        
        if token.token_type == "OPERATOR" and token.value == "(":
            # if we've hit a start operator, whatever came before is now the new parent
            # If last_token is None (standalone parenthesis), keep current parent
            if last_token is not None:
                token_stack.append(last_token)
            else:
                # Create a placeholder node for standalone parentheses
                paren_node = FormulaTokenNode("PAREN_GROUP", "(", token.start, token.end)
                token_stack[-1].add_child(paren_node)
                token_stack.append(paren_node)
        
        if len(token_stack) > 0 and token_stack[-1] is not None:
            token_stack[-1].add_child(token)
        
        last_token = token

    return root_node,tokens


# ============================================================================
# New AST Parser (Phase 1)
# ============================================================================

def parse_airtable_formula(formula: str, metadata: dict = None) -> FormulaNode:
    """
    Parse Airtable formula string into AST.
    
    Handles:
    - Field references: {fldXXXXXXXXXXXXXX}
    - String literals: "hello"
    - Number literals: 42, 3.14
    - Boolean literals: true, false
    - Function calls: IF(...), CONCATENATE(...), SUM(...)
    - Operators: +, -, *, /, &, =, !=, <, >, <=, >=
    - Parentheses for grouping
    
    Args:
        formula: Airtable formula string
        metadata: Optional AirtableMetadata dict for resolving field names/types
        
    Returns:
        FormulaNode: Root node of the AST
        
    Raises:
        ParseError: If formula has invalid syntax
    """
    # Tokenize first
    root_node, tokens = tokenize(formula)
    
    # Filter out whitespace tokens
    tokens = [t for t in tokens if t.token_type != "WHITESPACE"]
    
    # Convert tokens to AST
    ast = _parse_expression(tokens, 0, metadata)
    return ast[0]


def _parse_expression(tokens: TokenList, pos: int, metadata: dict = None) -> tuple[FormulaNode, int]:
    """
    Parse an expression from tokens starting at position pos.
    
    Returns:
        tuple: (FormulaNode, next_position)
    """
    if pos >= len(tokens):
        raise ParseError(pos, "Unexpected end of formula")
    
    # Parse primary expression (literal, field ref, function call, or parenthesized expr)
    node, pos = _parse_primary(tokens, pos, metadata)
    
    # Check for binary operators
    while pos < len(tokens):
        token = tokens[pos]
        
        # Stop at closing parenthesis or comma (handled by caller)
        if token.token_type == "OPERATOR" and token.value in [")", ","]:
            break
        
        # Check for binary operator
        if token.token_type == "OPERATOR" and token.value in ["+", "-", "*", "/", "&", "=", "!=", "<", ">", "<=", ">="]:
            operator = token.value
            pos += 1
            
            # Parse right operand
            right, pos = _parse_primary(tokens, pos, metadata)
            
            # Create binary operation node
            node = BinaryOpNode(operator, node, right)
        else:
            # Not an operator we recognize, stop parsing
            break
    
    return node, pos


def _parse_primary(tokens: TokenList, pos: int, metadata: dict = None) -> tuple[FormulaNode, int]:
    """
    Parse a primary expression (literal, field reference, function call, or parenthesized expression).
    
    Returns:
        tuple: (FormulaNode, next_position)
    """
    if pos >= len(tokens):
        raise ParseError(pos, "Unexpected end of formula")
    
    token = tokens[pos]
    
    # String literal
    if token.token_type == "STRING_LITERAL":
        # Remove quotes
        value = token.value.strip('"')
        return LiteralNode(value, "string"), pos + 1
    
    # Number literal
    if token.token_type == "NUMBER":
        value = float(token.value) if '.' in token.value else int(token.value)
        return LiteralNode(value, "number"), pos + 1
    
    # Boolean literal
    if token.token_type == "BOOLEAN":
        value = token.value.upper() == "TRUE"
        return LiteralNode(value, "boolean"), pos + 1
    
    # Field reference
    if token.token_type == "FIELD_ID":
        field_id = token.value
        field_name = None
        field_type = None
        
        # Try to resolve field name and type from metadata
        if metadata:
            field_name, field_type = _resolve_field_info(field_id, metadata)
        
        return FieldReferenceNode(field_id, field_name, field_type), pos + 1
    
    # Function call or parenthesized expression
    if token.token_type == "FUNCTION_NAME":
        function_name = token.value
        
        # Special case: NOT is a unary operator in Airtable, not a function
        if function_name == "NOT":
            pos += 1
            operand, pos = _parse_primary(tokens, pos, metadata)
            return UnaryOpNode("NOT", operand), pos
        
        pos += 1
        
        # Expect opening parenthesis
        if pos >= len(tokens) or tokens[pos].value != "(":
            raise ParseError(pos, f"Expected '(' after function name {function_name}")
        pos += 1
        
        # Parse arguments
        arguments = []
        while pos < len(tokens) and tokens[pos].value != ")":
            arg, pos = _parse_expression(tokens, pos, metadata)
            arguments.append(arg)
            
            # Check for comma separator
            if pos < len(tokens) and tokens[pos].value == ",":
                pos += 1
            elif pos < len(tokens) and tokens[pos].value != ")":
                raise ParseError(pos, f"Expected ',' or ')' in function arguments")
        
        # Expect closing parenthesis
        if pos >= len(tokens) or tokens[pos].value != ")":
            raise ParseError(pos, f"Expected ')' after function arguments")
        pos += 1
        
        return FunctionCallNode(function_name, arguments), pos
    
    # Parenthesized expression
    if token.token_type == "OPERATOR" and token.value == "(":
        pos += 1
        node, pos = _parse_expression(tokens, pos, metadata)
        
        # Expect closing parenthesis
        if pos >= len(tokens) or tokens[pos].value != ")":
            raise ParseError(pos, "Expected ')' after expression")
        pos += 1
        
        return node, pos
    
    # Unary operator (negative numbers)
    if token.token_type == "OPERATOR" and token.value == "-":
        pos += 1
        operand, pos = _parse_primary(tokens, pos, metadata)
        return UnaryOpNode("-", operand), pos
    
    raise ParseError(pos, f"Unexpected token: {token}")


def _resolve_field_info(field_id: str, metadata: dict) -> tuple[Optional[str], Optional[str]]:
    """
    Resolve field name and type from metadata.
    
    Args:
        field_id: Field ID (fldXXXXXXXXXXXXXX)
        metadata: AirtableMetadata dict
        
    Returns:
        tuple: (field_name, field_type) or (None, None) if not found
    """
    if not metadata or "tables" not in metadata:
        return None, None
    
    for table in metadata["tables"]:
        for field in table.get("fields", []):
            if field.get("id") == field_id:
                return field.get("name"), field.get("type")
    
    return None, None


if __name__ == "__main__":
    # Test legacy tokenizer
    for formula in sample_formulas:
        root_node, tokens = tokenize(formula)
        print(f"Formula: {formula}")
        root_node.print_tree()
        print()
    
    # Test new AST parser
    print("\n" + "="*80)
    print("Testing new AST parser")
    print("="*80 + "\n")
    
    test_formulas = [
        "1 + 2",
        "3 * 4 + 5",
        'CONCATENATE("Hello", " ", "World")',
        'IF({fldXXXXXXXXXXXXXX} > 100, "High", "Low")',
        "{fldYYYYYYYYYYYYYY} * 1.08",
    ]
    
    for formula in test_formulas:
        try:
            print(f"Formula: {formula}")
            ast = parse_airtable_formula(formula)
            print(f"AST: {ast}")
            print()
        except ParseError as e:
            print(f"Parse error: {e}")
            print()
                
        