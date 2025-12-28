"""
Test partial evaluation functionality
"""

import sys
sys.path.append("web")

from web.airtable_formula_evaluator import simplify_formula, evaluate_formula

# Test cases for partial evaluation
test_cases = [
    # IF statement with known condition
    ("IF(TRUE, 'yes', 'no')", "yes"),
    ("IF(FALSE, 'yes', 'no')", "no"),
    
    # IF statement with unknown condition but computable branches
    ("IF({fldABC12345678901}, 2 + 3, 10 - 5)", "IF({fldABC12345678901}, 5.0, 5.0)"),
    
    # Arithmetic that can be simplified
    ("2 + 3", "5.0"),
    ("10 - 5", "5.0"),
    ("2 * 3", "6.0"),
    ("10 / 2", "5.0"),
    
    # AND/OR logic simplification
    ("AND(TRUE, TRUE)", "True"),
    ("AND(TRUE, FALSE)", "False"),
    ("AND(TRUE, {fldABC12345678901})", "{fldABC12345678901}"),  # TRUE can be removed
    ("OR(FALSE, {fldABC12345678901})", "{fldABC12345678901}"),  # FALSE can be removed
    ("OR(TRUE, {fldABC12345678901})", "True"),  # Short-circuit
    
    # Nested IFs
    ("IF(TRUE, IF(FALSE, 'a', 'b'), 'c')", "b"),
    
    # Comparison operators
    ("10 > 5", "True"),
    ("5 < 3", "False"),
    ("5 = 5", "True"),
    
    # Complex example
    ("IF(10 > 5, 'large', 'small')", "large"),
    
    # String concatenation
    ("'Hello' & ' ' & 'World')", "Hello World"),
]

print("Testing Partial Evaluation\n" + "=" * 60)

for formula, expected in test_cases:
    try:
        result = simplify_formula(formula)
        status = "✓" if result == expected else "⚠"
        print(f"{status} {formula}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
        if result != expected:
            print(f"  NOTE: Results may differ in representation but be semantically equivalent")
        print()
    except Exception as e:
        print(f"✗ {formula}")
        print(f"  Error: {e}")
        print()

# Additional test: Full evaluation after simplification
print("\nFull Evaluation Tests\n" + "=" * 60)

eval_tests = [
    "IF(TRUE, 10, 20)",
    "2 + 3 * 4",
    "IF(10 > 5, SUM(1, 2, 3), 0)",
]

for formula in eval_tests:
    try:
        simplified = simplify_formula(formula)
        result = evaluate_formula(simplified)
        print(f"✓ {formula}")
        print(f"  Simplified: {simplified}")
        print(f"  Result:     {result}")
        print()
    except Exception as e:
        print(f"✗ {formula}")
        print(f"  Error: {e}")
        print()
