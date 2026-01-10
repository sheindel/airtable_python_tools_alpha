# Phase 5B Debugging Guide

**Date**: January 9, 2026  
**Status**: Living Document  
**Related**: [phase5b-incremental-parity-plan.md](phase5b-incremental-parity-plan.md)

## Overview

This document captures lessons learned while debugging Phase 5B (Advanced Parity Tests) of the Formula Evaluator with Incremental Computation project. It serves as a troubleshooting guide for future developers.

---

## Critical Bugs Found and Fixed

### Bug #1: Table Filtering in build_computation_graph() ⚠️ CRITICAL

**Symptom**: Generated evaluators had 0 compute functions when filtering by table_id

**File**: `web/code_generators/incremental_runtime_generator.py`  
**Line**: ~140

**Root Cause**:
```python
# ❌ WRONG - field_info_dict doesn't have table_id key
if table_id and field_info_dict.get("table_id") != table_id:
    continue
```

The `field_info_dict` returned by `get_computation_order_with_metadata()` contains these keys:
- `id` - Field ID
- `name` - Field name
- `type` - Field type
- `table_name` - Table name (not table_id!)
- `depth` - Computation depth

**Fix**:
```python
# ✅ CORRECT - Look up table_id from table_name
if table_id:
    field_table_id = None
    for table in metadata.get("tables", []):
        if table["name"] == table_name:
            field_table_id = table["id"]
            break
    
    if field_table_id != table_id:
        continue
```

**Impact**: 
- Before fix: 0 computed fields in graph
- After fix: 22 computed fields in graph ✅
- This was the #1 blocker preventing any formula evaluation

**How to Detect**:
1. Generate evaluator code for a specific table
2. Check if `# No computed fields` appears in output
3. Run debug script to check `graph.get_computed_fields()` returns empty list

**Prevention**:
- Always verify the structure of dicts returned from helper functions
- Add type hints and docstrings documenting exact dict keys
- Consider adding `table_id` to `get_computation_order_with_metadata()` output

---

### Bug #2: Field Name Mismatch (Snake Case Conversion) ⚠️ HIGH

**Symptom**: All formulas returned None despite being generated correctly

**Files**: 
- `tests/test_formula_parity.py`
- `test_parity_quick.py`

**Root Cause**:
- Generated Python code uses snake_case field names: `first_name`, `last_name`
- Raw Airtable records use original field names: `First Name`, `Last Name`
- When code tried to access `record["first_name"]`, the key didn't exist

**Example**:
```python
# Generated code expects:
def compute_name(record, context):
    return record["first_name"] + " " + record["last_name"]

# But raw_fields contains:
raw_fields = {
    "First Name": "John",
    "Last Name": "Doe"
}

# Result: KeyError or None
```

**Fix**: Added helper functions in `tests/helpers/airtable_api.py`:

```python
def to_snake_case(name: str) -> str:
    """Convert field name to snake_case matching code generator."""
    import re
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    name = name.lower()
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name

def convert_record_to_snake_case(record: dict) -> dict:
    """Convert all field names in record to snake_case."""
    return {to_snake_case(k): v for k, v in record.items()}
```

**Usage in tests**:
```python
# Extract raw fields (original Airtable names)
raw_fields = extract_raw_fields(full_record, schema, table_name)

# Convert to snake_case for evaluator
raw_fields_snake = convert_record_to_snake_case(raw_fields)

# Now the evaluator can access fields correctly
local_record = {"id": record_id, **raw_fields_snake}
```

**Impact**:
- Before fix: All formulas returned None (field access failed)
- After fix: Formulas execute and some return correct values

**How to Detect**:
1. Generated code runs without errors
2. But all computed fields return None
3. Check field names in raw_fields vs generated code
4. Debug: print `list(raw_fields.keys())` vs expected field names

**Prevention**:
- Document the snake_case convention clearly
- Add conversion function to shared utilities
- Consider generating a field name mapping in the evaluator code

---

### Bug #3: Formula Transpilation Error (String Concatenation) ✅ FIXED

**Symptom**: Simple formulas like `{First Name} & " " & {Last Name}` generate completely broken Python code

**File**: `web/code_generators/python_runtime_generator.py` (PythonFormulaTranspiler)

**Root Cause**: The transpiler was double-wrapping null safety checks when handling chained `&` operations

**Example**:

Airtable formula:
```
{First Name} & " " & {Last Name}
```

Generated Python code (BROKEN - 319 characters):
```python
return (str((str(record["first_name"]) if record["first_name"] is not None else '' + str(" ") if " " is not None else '')) if (str(record["first_name"]) if record["first_name"] is not None else '' + str(" ") if " " is not None else '') is not None else '' + str(record["last_name"]) if record["last_name"] is not None else '')
```

Expected Python code (CORRECT - 153 characters):
```python
return (((str(record["first_name"]) if record["first_name"] is not None else '') + " ") + (str(record["last_name"]) if record["last_name"] is not None else ''))
```

**Problem Analysis**:

For formula `{A} & " " & {B}`, the parser creates a nested AST:
```
BinaryOp(&)
  left: BinaryOp(&)
    left: FieldRef(A)
    right: Literal(" ")
  right: FieldRef(B)
```

When `_transpile_binary_op()` was called recursively, it wrapped EVERY operand with null checks:
```python
if node.operator == '&':
    left = f"str({left}) if {left} is not None else ''"   # Wraps already-wrapped expr!
    right = f"str({right}) if {right} is not None else ''"
```

This caused already-transpiled expressions to be wrapped AGAIN, creating deeply nested malformed ternaries.

**Fix**:

Added `_ensure_string()` method that intelligently wraps only when needed:

```python
def _ensure_string(self, transpiled_code: str, original_node: FormulaNode) -> str:
    """
    Ensure a value is converted to string for concatenation.
    Only wraps with null checks if the node type requires it.
    """
    # Literals are never None and can be converted directly
    if isinstance(original_node, LiteralNode):
        if original_node.data_type == "string":
            return transpiled_code  # Already a string
        else:
            return f"str({transpiled_code})"
    
    # Binary ops with & are already wrapped - don't double-wrap
    elif isinstance(original_node, BinaryOpNode) and original_node.operator == '&':
        return transpiled_code  # Already returns a string
    
    # Field references and function calls need null safety
    else:
        return f"(str({transpiled_code}) if {transpiled_code} is not None else '')"
```

**Impact**:
- String concatenation formulas now work correctly
- Code size reduced from 319 to 153 characters for simple concat
- Syntax is valid and produces correct results
- Tested: `"John" + " " + "Doe"` = `"John Doe"` ✅
- Tested with None: `None + " " + "Doe"` = `" Doe"` ✅

**Status**: ✅ FIXED

---

### Bug #4: Overly Aggressive Null Safety Checks ✅ FIXED

**Symptom**: Formulas return None even when they can handle None inputs

**File**: `web/code_generators/incremental_runtime_generator.py` (line ~450)

**Root Cause**: The code generator adds upfront null checks that return None if ANY dependency is None

**Example**:

Generated code:
```python
def compute_name(record, context) -> Optional[Any]:
    """Compute Name field"""
    # Null safety check
    if record.get("first_name") is None or record.get("last_name") is None:
        return None
    
    return (((str(record["first_name"]) if record["first_name"] is not None else '') + " ") + 
            (str(record["last_name"]) if record["last_name"] is not None else ''))
```

**Problem**:
- The upfront check returns None if first_name OR last_name is None
- But the formula code ALREADY handles None: `if record["first_name"] is not None else ''`
- So a record with `first_name=None, last_name="Doe"` returns `None` instead of `" Doe"`
- This breaks Airtable parity (Airtable lets formulas handle their own None values)

**Fix**:

Modified the null check generation to skip formulas:

```python
# Generate null checks if enabled
# NOTE: For formula fields, we DON'T add upfront null checks because the 
# transpiled formula code already handles None values appropriately (e.g.,
# string concatenation converts None to empty string).
null_check_code = ""
if options.include_null_checks and dep_names and field_info.field_type != FIELD_TYPE_FORMULA:
    # ... generate null checks for lookups/rollups only
```

**Impact**:
- Formula fields now handle None values correctly
- String concatenation with None inputs works
- Parity improved from 1/22 matches to 6/22 matches (27% → 27%+)

**Status**: ✅ FIXED

---

### Bug #5: Missing Fields in Raw Data ✅ FIXED

**Symptom**: KeyError when generated code accesses fields not in the record

**File**: `tests/helpers/airtable_api.py` (extract_raw_fields)

**Root Cause**: Airtable API doesn't include fields with empty/None values in responses

**Example**:

Airtable returns:
```json
{
  "id": "rec123",
  "fields": {
    "First Name": "John",
    "Last Name": "Doe"
    // "Middle Name" is missing (empty in Airtable)
  }
}
```

Generated code tries to access:
```python
middle_name = record["middle_name"]  # KeyError!
```

**Fix**:

Updated `extract_raw_fields()` to initialize ALL raw fields with None:

```python
# Build set of all raw field names
raw_field_names = set()
for field in table.get("fields", []):
    if field["type"] not in computed_types:
        raw_field_names.add(field["name"])

# Initialize all raw fields with None
raw_fields = {"id": full_record["id"]}
for field_name in raw_field_names:
    raw_fields[field_name] = None

# Fill in actual values from record
for field_name, value in full_record.get("fields", {}).items():
    if field_name not in computed_field_names:
        raw_fields[field_name] = value
```

**Impact**:
- No more KeyErrors from missing fields
- Formulas can safely access any field (gets None if missing)
- Tests run to completion instead of crashing

**Status**: ✅ FIXED

---

## Common Issues and Solutions

### Issue: Formula Returns None Despite Valid Inputs

**Possible Causes**:

1. **Null safety check too strict**
   ```python
   # Generated code:
   if record.get("first_name") is None or record.get("last_name") is None:
       return None
   ```
   - If ANY dependency is None, formula returns None
   - Even if the formula could handle it (e.g., with IF conditions)

2. **Field reference errors in formula**
   - Formula references field by ID: `{fldXXX}`
   - If field ID doesn't exist in graph, reference fails
   - Check `referencedFieldIds` in formula options

3. **Complex formula transpilation errors**
   - Look at generated formula code
   - Check if string concatenation or operators look wrong
   - Might have nested `str()` calls or malformed expressions

**Debug Steps**:
```python
# 1. Check the generated formula code
grep -A 10 "def compute_name" generated_evaluator.py

# 2. Check what values are in the record
print("Record fields:", list(local_record.keys()))
print("First name:", local_record.get("first_name"))
print("Last name:", local_record.get("last_name"))

# 3. Try running the formula manually
result = compute_name(local_record, context)
print("Formula result:", result)
```

---

### Issue: Lookups/Rollups Return Empty Arrays or Wrong Values

**Cause**: These fields require linked records via `DataAccess` interface

**Current Limitation**:
- Generated code calls `context.lookup()` and `context.rollup()`
- These need `all_records` dict populated with related tables
- Tests currently pass empty dict: `ComputationContext(record, {})`

**Solution (Future)**:
1. Fetch related records from Airtable
2. Populate `all_records` dict with linked tables
3. Or mock DataAccess for testing

**Example**:
```python
# Need to implement:
all_records = {
    "tblCompanies": fetch_all_companies(base_id, api_key),
    "tblDeals": fetch_all_deals(base_id, api_key),
}
context = ComputationContext(record, all_records)
```

---

## Debugging Workflow

### Step 1: Verify Graph Building

```bash
# Create debug script
cat > debug_graph.py << 'EOF'
from code_generators.incremental_runtime_generator import build_computation_graph
graph = build_computation_graph(schema, table_id=table_id)
print(f"Computed fields: {len(graph.get_computed_fields())}")
for field in graph.get_computed_fields()[:5]:
    print(f"  {field.name} ({field.field_type})")
EOF

python debug_graph.py
```

**Expected**: Should list all computed fields (formulas, lookups, rollups)  
**If 0 fields**: Bug #1 (table filtering)

### Step 2: Verify Code Generation

```bash
# Generate evaluator
from code_generators.incremental_runtime_generator import generate_complete_module
code = generate_complete_module(schema, table_id=table_id, options=options)

# Save and inspect
with open("generated.py", "w") as f:
    f.write(code)

# Count compute functions
grep -c "def compute" generated.py
```

**Expected**: Should match number of computed fields from Step 1  
**If 0 functions**: Code generation issue

### Step 3: Verify Field Names

```bash
# Check raw field names
raw_fields = extract_raw_fields(record, schema, table_name)
print("Raw fields:", list(raw_fields.keys()))

# Check what generated code expects
grep "record\[" generated.py | head -5
```

**Expected**: Should see snake_case field names in generated code  
**If mismatch**: Bug #2 (field name conversion)

### Step 4: Test Simple Formula

```python
# Try simplest possible formula: {Field1}
# Or: {Field1} & " " & {Field2}

# Execute generated code
exec(code, namespace)
update_record = namespace["update_record"]

# Convert to snake_case
record_snake = convert_record_to_snake_case(raw_fields)
record_snake["id"] = record_id

# Compute
context = ComputationContext(record_snake, {})
result = update_record(record_snake, context)

# Check computed values
print("Name:", result.get("name"))
```

**Expected**: Simple formulas should work  
**If None**: Check null safety or field references

### Step 5: Check Formula Transpilation

```python
# Look at generated formula
grep -A 20 "def compute_name" generated.py

# Check if formula looks correct
# Should NOT have syntax errors or malformed expressions
```

**Common transpilation issues**:
- Nested `str()` calls: `str(str(...))`
- Wrong operators: `+` instead of `&` for concatenation
- Missing parentheses
- Wrong field references

---

## Testing Checklist

Before declaring Phase 5B complete:

### Basic Formula Tests
- [ ] String concatenation: `{A} & " " & {B}`
- [ ] Arithmetic: `{A} + {B}`, `{A} * {B}`
- [ ] Comparison: `{A} > {B}`
- [ ] IF statement: `IF({condition}, {true}, {false})`

### Field Type Tests  
- [ ] Formula fields returning correct values
- [ ] Lookup fields (with mocked data)
- [ ] Rollup fields (with mocked data)
- [ ] Count fields

### Edge Cases
- [ ] Null values handled correctly
- [ ] Empty strings handled correctly
- [ ] Division by zero returns error/null
- [ ] Nested formulas compute in correct order

### Integration
- [ ] Simple formula parity test passes (80%+ match rate)
- [ ] Statistical sampling shows consistent results
- [ ] CI can run tests (with credentials)

---

## Key Learnings

### 1. Always Verify Data Structure Assumptions

**❌ Bad**: Assume a dict has certain keys
```python
if field_info_dict.get("table_id") != table_id:  # Assumes key exists
    continue
```

**✅ Good**: Verify structure first or handle missing keys
```python
# Check what keys actually exist
print("Keys:", list(field_info_dict.keys()))

# Or look up missing data
table_id_lookup = get_table_id_from_name(field_info_dict["table_name"])
```

### 2. Match Code Generator Conventions in Tests

Generated code uses specific conventions:
- snake_case field names
- Dict access mode (`record["field"]`) or dataclass access (`record.field`)
- Specific null handling

Tests must match these conventions exactly.

### 3. Debug with Simplest Possible Case

Don't start with complex formulas. Test with:
1. Single field reference: `{FieldName}`
2. String concatenation: `{A} & " " & {B}`  
3. Simple arithmetic: `{A} + {B}`

Once these work, move to complex cases.

### 4. Layer the Debugging

1. **Graph building**: Does it find all fields?
2. **Code generation**: Does it generate functions?
3. **Code execution**: Does the code run without errors?
4. **Field access**: Can code access record fields?
5. **Formula logic**: Does the formula compute correctly?

Fix each layer before moving to the next.

---

## Tools and Scripts

### Quick Test Script

Create `test_parity_quick.py` for rapid iteration:
- Fetches real Airtable data
- Generates evaluator
- Compares computed vs actual values
- Fast feedback loop (~5 seconds)

### Debug Graph Script

Create `debug_graph.py` to inspect computation graph:
- Shows field counts
- Lists computed fields by depth
- Verifies table filtering works

### Generated Code Inspector

After generation, inspect the output:
```bash
# Count functions
grep -c "def compute" generated.py

# Check field names
grep "record\[" generated.py | head -10

# Look at specific formula
grep -A 20 "def compute_name" generated.py
```

---

## Future Improvements

### Code Generator Enhancements

1. **Add field name mapping to generated code**:
   ```python
   # Include this in generated code for easier debugging
   FIELD_NAME_MAPPING = {
       "Name": "name",
       "First Name": "first_name",
       # ...
   }
   ```

2. **Better error messages**:
   ```python
   def compute_name(record, context):
       try:
           return formula_logic()
       except KeyError as e:
           raise ValueError(f"Field {e} not found in record. Available: {list(record.keys())}")
   ```

3. **Debug mode**:
   ```python
   options = GeneratorOptions(
       debug_mode=True  # Add logging, validation
   )
   ```

### Test Infrastructure

1. **Fixture library**: Pre-generated evaluators for common schemas
2. **Mock DataAccess**: Fake linked records for testing
3. **Formula test suite**: Library of test formulas with expected results
4. **CI integration**: Automated parity tests in GitHub Actions

---

## References

- Main design doc: [formula-evaluator-incremental-design.md](formula-evaluator-incremental-design.md)
- Implementation plan: [phase5b-incremental-parity-plan.md](phase5b-incremental-parity-plan.md)
- Test file: `tests/test_formula_parity.py`
- Quick test: `test_parity_quick.py`
- Helper modules: `tests/helpers/airtable_api.py`, `tests/helpers/comparison.py`

---

**Last Updated**: January 9, 2026  
**Maintainer**: Development Team  
**Status**: Living Document - Update as new issues are discovered
