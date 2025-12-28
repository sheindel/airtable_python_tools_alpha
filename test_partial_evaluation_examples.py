"""
Example demonstrating partial evaluation with realistic formulas
"""

import sys
sys.path.append("web")

from web.airtable_formula_evaluator import substitute_field_values, simplify_formula

print("Partial Evaluation Examples")
print("=" * 70)
print()

# Example 1: Conditional simplification
print("Example 1: IF statement with known condition")
print("-" * 70)
formula = "IF({fldStatus0000001} = 'active', {fldPrice000000001} * 1.2, {fldPrice000000001})"
print(f"Original: {formula}")
print()

# User provides status value
values = {'fldStatus0000001': 'active'}
with_values = substitute_field_values(formula, values)
print(f"After substitution: {with_values}")

simplified = simplify_formula(with_values)
print(f"After simplification: {simplified}")
print()
print()

# Example 2: Nested IFs with partial information
print("Example 2: Nested conditionals")
print("-" * 70)
formula = "IF({fldType00000001} = 'premium', IF({fldQty000000001} > 10, 100, 50), 25)"
print(f"Original: {formula}")
print()

# User knows type but not quantity yet
values = {'fldType00000001': 'premium'}
with_values = substitute_field_values(formula, values)
print(f"After substitution: {with_values}")

simplified = simplify_formula(with_values)
print(f"After simplification: {simplified}")
print("  → Outer IF removed, inner IF remains")
print()
print()

# Example 3: Boolean logic optimization
print("Example 3: AND/OR simplification")
print("-" * 70)
formula = "AND({fldActive0000001}, TRUE, {fldVerified00001})"
print(f"Original: {formula}")
print()

# One field is known
values = {'fldActive0000001': 'TRUE'}
with_values = substitute_field_values(formula, values)
print(f"After substitution: {with_values}")

simplified = simplify_formula(with_values)
print(f"After simplification: {simplified}")
print("  → TRUE literals removed from AND")
print()
print()

# Example 4: Short-circuit evaluation
print("Example 4: Short-circuit OR")
print("-" * 70)
formula = "OR({fldCondA0000001}, {fldCondB0000001}, {fldCondC0000001})"
print(f"Original: {formula}")
print()

# One condition is true
values = {'fldCondB0000001': 'TRUE'}
with_values = substitute_field_values(formula, values)
print(f"After substitution: {with_values}")

simplified = simplify_formula(with_values)
print(f"After simplification: {simplified}")
print("  → Entire OR evaluates to TRUE (short-circuit)")
print()
print()

# Example 5: Arithmetic pre-computation
print("Example 5: Arithmetic simplification")
print("-" * 70)
formula = "{fldQuantity00001} * (100 + 50) / 2"
print(f"Original: {formula}")
print()

# Field value not provided yet, but arithmetic can be simplified
simplified = simplify_formula(formula)
print(f"After simplification: {simplified}")
print("  → Constant arithmetic computed")
print()
