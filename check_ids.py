test_ids = [
    "fldVerified00001",  # 13 chars
    "fldCondA0000001",   # 12 chars 
    "fldCondC0000001",   # 12 chars
]

for tid in test_ids:
    print(f"{tid}: {len(tid[3:])} chars after 'fld'")