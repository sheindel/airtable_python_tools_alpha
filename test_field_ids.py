import re

field_ids = [
    "fldStatus000000001",  # 15 chars after fld
    "fldPrice00000000001",  # 16 chars after fld  
]

pattern = r'fld[a-zA-Z0-9]{14}'

for fid in field_ids:
    match = re.match(pattern, fid)
    print(f"{fid}: {len(fid[3:])} chars after 'fld', matches: {match is not None}")
    if match:
        print(f"  Matched: {match.group(0)}")
