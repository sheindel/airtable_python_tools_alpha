import re

formula = "AND(TRUE, {fldTest01234567})"
pattern = r'\{(fld[a-zA-Z0-9]{14})\}'

matches = list(re.finditer(pattern, formula))
print(f"Formula: {formula}")
print(f"Matches: {matches}")

for m in matches:
    print(f"  Match: {m.group(0)} at {m.start()}-{m.end()}")
    print(f"  Field ID: {m.group(1)}")
