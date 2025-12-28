"""Debug field reference handling"""

import sys
sys.path.append("web")

from web.airtable_formula_evaluator import tokenize_formula, parse_expression, partial_evaluate_node, node_to_string

formula = "AND(TRUE, {fldABC12345678901})"
print(f"Formula: {formula}\n")

# Step 1: Tokenize
tokens = tokenize_formula(formula)
print("Tokens:")
for t in tokens:
    print(f"  {t}")
print()

# Step 2: Parse
ast, _ = parse_expression(tokens, 0)
print(f"AST: {ast}\n")

# Step 3: Partial evaluate
simplified, is_literal = partial_evaluate_node(ast)
print(f"Simplified AST: {simplified}")
print(f"Is literal: {is_literal}\n")

# Step 4: Convert to string
result = node_to_string(simplified)
print(f"Result: {result}")
