import re


sample_formulas = [
    "IF({flddfGHN4ToYguiGj}, \r\n  IF(FIND(\"lost\",LOWER({flddUMM1OtEqyriCs})),\r\n    \"Previous\",\r\n    \"Current\"),\r\n  \"New\")",
    "FIND({fld6jAxjTe0g2LAgm},{fldaSAveZtp0ITolx}&\"\")>0",
    "{fldhj47fcAadgdADP}*(1-{fldjd2tXiXHAL5mGa})",
    "{fldSPNCyipj4ryWP6}&IF({fldgvPoP0MiEqrp1R},IF({fldSPNCyipj4ryWP6},\",\")&ARRAYJOIN({fldgvPoP0MiEqrp1R}))",
    "IF({fldK3mT15Iq25srUo}>0,IF({fldsgw7sX1Eedimx0}!=BLANK(),{fldK3mT15Iq25srUo}/{fldsgw7sX1Eedimx0},{fldK3mT15Iq25srUo}/{fldzBeDVJqyaIBcwl}))",
    "TRIM(RIGHT(CONCATENATE({fldvYGwZBESyjyp4g}),(LEN(CONCATENATE({fldvYGwZBESyjyp4g}))- FIND(\",\",CONCATENATE({fldvYGwZBESyjyp4g}))-1)))",
    "SWITCH(   LEFT({fldM8FrSyhBOj6HKA},1),\n  \"0\",\"0. Unready\",\n  \"1\",\"1. Ready\",\n  \"2\",\"2. Sampled\",\n  \"3\",\"3. Sent to Lab\",\n  \"4\",\"3. Sent to Lab\",\n  \"5\",\"3. Sent to Lab\",\n  \"6\",\"3. Sent to Lab\",\n  \"7\",\"7. Completed\",\n  \"8\",\"8. Costs Finalized\",\n  \"9\",\"9. Invoiced\",\n  \"Y\",\"Y. Cancelled\",\n  \"X\",\"X. Error\")"
]

# Find field IDs
field_id_regex = r"{(fld[a-zA-Z0-9]{14})}"

# Find function names
function_name_regex = r"(\b[A-Z]+\b)"

# Find operators
operator_regex = r"([\+\-\*\/\(\)])"

# Find string literals
string_literal_regex = r"(\"[^\"]*\")"

# Find numbers
number_regex = r"(\b\d+(\.\d+)?\b)"

# Find boolean values
boolean_regex = r"(\b(TRUE|FALSE)\b)"

# Find whitespace
whitespace_regex = r"(\s+)"

patterns = [
    (field_id_regex, "FIELD_ID"),
    (function_name_regex, "FUNCTION_NAME"),
    (operator_regex, "OPERATOR"),
    (string_literal_regex, "STRING_LITERAL"),
    (number_regex, "NUMBER"),
    (boolean_regex, "BOOLEAN"),
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
            if len(token_stack) == 0:
                raise ParseError(token.start, "Unmatched closing parenthesis")
            token_stack.pop()
        
        if token.token_type == "OPERATOR" and token.value == "(":
            # if we've hit a start operator, whatever came before is now the new parent
            token_stack.append(last_token)
        
        if len(token_stack) > 0:
            token_stack[-1].add_child(token)
        
        last_token = token

    return root_node,tokens


if __name__ == "__main__":
    for formula in sample_formulas:
        root_node, tokens = tokenize(formula)
        print(f"Formula: {formula}")

        root_node.print_tree()
                
        