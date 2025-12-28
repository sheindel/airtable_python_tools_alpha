import sys
sys.path.append("web")

from web.airtable_formula_evaluator import tokenize_formula, parse_expression, partial_evaluate_node, node_to_string

formula = "AND(TRUE, TRUE, {fldABC12345678901})"
print(f"Testing: {formula}\n")

tokens = tokenize_formula(formula)
print(f"Tokens:")
for t in tokens:
    print(f"  {t}")
print()

ast, _ = parse_expression(tokens, 0)
print(f"AST: {ast}\n")

simplified, was_eval = partial_evaluate_node(ast)
print(f"Simplified: {simplified}")
print(f"Was evaluated: {was_eval}\n")

result = node_to_string(simplified) if not was_eval else str(simplified['value'])
print(f"Result: {result}")
