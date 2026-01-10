# Debug Tools

Developer utilities for inspecting AST, graphs, evaluators, and transpiler output.

## Available Tools

### inspect_ast.py
Inspect the Abstract Syntax Tree (AST) structure of Airtable formulas.

**Usage:**
```bash
# Basic formula
uv run python scripts/debug/inspect_ast.py 'IF({fldA}, "Yes", "No")'

# String concatenation
uv run python scripts/debug/inspect_ast.py '{fldA} & " " & {fldB}'

# Complex nested formula
uv run python scripts/debug/inspect_ast.py 'IF({fldActive}, {fldQty} * {fldPrice}, 0)'
```

**Output:** Pretty-printed AST tree structure showing node types and relationships.

### inspect_graph.py
Inspect the computation graph for a specific table.

**Usage:**
```bash
# Set credentials
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Inspect a table
uv run python scripts/debug/inspect_graph.py --table Contacts

# With inline credentials
uv run python scripts/debug/inspect_graph.py \
  --table Contacts \
  --base-id appXXX \
  --api-key keyXXX
```

**Output:** 
- Table metadata
- Computed field count
- Computation graph statistics
- Fields organized by depth level

### inspect_evaluator.py
Generate and inspect evaluator code for a table.

**Usage:**
```bash
# Set credentials
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Print to stdout
uv run python scripts/debug/inspect_evaluator.py --table Contacts

# Save to file
uv run python scripts/debug/inspect_evaluator.py \
  --table Contacts \
  --output generated_evaluator.py

# Use dataclass mode instead of dict
uv run python scripts/debug/inspect_evaluator.py \
  --table Contacts \
  --data-access dataclass
```

**Output:** Complete Python evaluator module with all formula computation functions.

### inspect_transpiler.py
Inspect transpiler output for formulas (Python code generation).

**Usage:**
```bash
# Simple formula
uv run python scripts/debug/inspect_transpiler.py 'IF({fldA}, "Yes", "No")'

# Field concatenation
uv run python scripts/debug/inspect_transpiler.py '{fldA} & " " & {fldB}'

# Arithmetic
uv run python scripts/debug/inspect_transpiler.py '{fldQty} * {fldPrice}'
```

**Output:** 
- Generated Python code (both dict and dataclass modes)
- Code length and line count statistics

### inspect_formula.py
Debug a specific formula field in detail by comparing Airtable vs. local evaluation.

**Usage:**
```bash
# Set credentials
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Debug specific field with random record
uv run python scripts/debug/inspect_formula.py \
  --table Contacts \
  --field Name

# Debug with specific record
uv run python scripts/debug/inspect_formula.py \
  --table Contacts \
  --field Name \
  --record recXXXXXXXXXXXXXX
```

**Output:**
- Field metadata (type, ID, formula)
- Referenced fields
- Airtable value vs. local computed value
- Comparison result (match/mismatch)

## Common Workflows

### Debug a formula that's not computing correctly
```bash
# 1. First inspect the formula structure
uv run python scripts/debug/inspect_formula.py --table Orders --field Total

# 2. If needed, check the AST
uv run python scripts/debug/inspect_ast.py '{fldQuantity} * {fldPrice}'

# 3. Look at the generated Python code
uv run python scripts/debug/inspect_transpiler.py '{fldQuantity} * {fldPrice}'
```

### Debug computation graph issues
```bash
# 1. Inspect the full graph
uv run python scripts/debug/inspect_graph.py --table Orders

# 2. Generate and save the evaluator
uv run python scripts/debug/inspect_evaluator.py \
  --table Orders \
  --output debug_orders.py

# 3. Review the generated code in your editor
code debug_orders.py
```

### Find circular dependencies
```bash
# Inspect graph will show depth levels
# If max_depth is very high, check for circular refs
uv run python scripts/debug/inspect_graph.py --table MyTable
```

## Tips

- **Save credentials**: Add `AIRTABLE_BASE_ID` and `AIRTABLE_API_KEY` to your shell profile
- **JSON schemas**: Use these tools with any Airtable base by changing credentials
- **Generated code**: Evaluator code is fully executable Python you can import
- **Field IDs**: Tools handle both field IDs (`{fldXXX}`) and will map to names automatically

## Related

- See [../validate/README.md](../validate/README.md) for parity checking tools
- See [../../tests/README.md](../../tests/README.md) for integration tests
- See [../../TESTING_REORGANIZATION.md](../../TESTING_REORGANIZATION.md) for overall strategy
