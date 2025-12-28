"""Debug string comparison"""
import sys
sys.path.append("web")

from web.airtable_formula_evaluator import simplify_formula

# Test cases that should simplify but aren't
test_cases = [
    ("'premium' = 'premium'", "Should evaluate to TRUE"),
    ("IF('premium' = 'premium', 100, 25)", "Should become 100"),
    ("AND(TRUE, TRUE, {fldVerified00001})", "Should become {fldVerified00001}"),
    ("OR({fldCondA0000001}, TRUE, {fldCondC0000001})", "Should become TRUE"),
]

for formula, description in test_cases:
    result = simplify_formula(formula)
    print(f"Formula: {formula}")
    print(f"Result:  {result}")
    print(f"Note:    {description}")
    print()

