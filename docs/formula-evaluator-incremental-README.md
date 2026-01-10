# Formula Evaluator with Incremental Computation - Quick Start

This document provides a quick overview and next steps for the incremental formula evaluator implementation.

## What We Built

A new code generation system that creates efficient Python formula evaluators with **incremental computation** capabilities:

1. **Smart Dependency Tracking**: Only recalculates formulas whose dependencies actually changed
2. **Depth-Based Processing**: Processes formulas in the correct order (dependencies before dependents)
3. **Efficient Updates**: Avoids duplicate work during a single update cycle

## Files Created

### 1. Design Document
**Location:** [docs/formula-evaluator-incremental-design.md](./formula-evaluator-incremental-design.md)

Comprehensive design covering:
- Architecture and data structures
- 6-phase implementation plan
- Usage examples and patterns
- Performance considerations
- Configuration options

### 2. Core Module
**Location:** `web/code_generators/incremental_runtime_generator.py`

Provides:
- `ComputationGraph`: Data structure organizing fields by dependency depth
- `build_computation_graph()`: Builds the graph from Airtable metadata
- `GeneratorOptions`: Configuration for code generation
- Foundation for generating Python formula evaluators

**Current Status:** ✅ Phase 1 Complete
- Graph building implemented
- Tests passing (87% coverage)
- Ready for Phase 2

### 3. Test Suite
**Location:** `tests/test_incremental_runtime.py`

8 tests covering:
- Graph structure validation
- Cascading formula dependencies
- Field ID/name mapping
- Function name generation
- Helper utilities

## How It Works

### Example: Simple Formula Update

```python
# Schema: Full Name = {First Name} & " " & {Last Name}
# Depth 0: First Name, Last Name (basic fields)
# Depth 1: Full Name (formula field)

# When First Name changes:
# 1. System knows Full Name depends on First Name
# 2. Only Full Name is recalculated (not other formulas)
# 3. Changes propagate to fields that depend on Full Name
```

### Example: Cascading Updates

```python
# Depth 0: First Name, Last Name
# Depth 1: Full Name = {First Name} & " " & {Last Name}
# Depth 2: Greeting = "Hello, " & {Full Name}

# When First Name changes:
update_record(contact, context, changed_fields=["first_name"])
# → Recalculates Full Name (depends on First Name)
# → Recalculates Greeting (depends on Full Name)
# → Skips other formulas (not in dependency chain)
```

## Implementation Status

### ✅ Completed (Phase 1)
- [x] Core data structures (`ComputationGraph`, `FieldInfo`)
- [x] Graph building from metadata
- [x] Dependency depth calculation
- [x] Field name/ID mappings
- [x] Unit tests (8 tests passing)
- [x] Documentation

### 📝 Next Steps (Phase 2)
**Goal:** Generate formula functions

1. Extend `python_runtime_generator.py`:
   - Add null safety checks to existing transpiler
   - Create `generate_formula_function()` for formula fields
   - Create `generate_lookup_function()` for lookup fields
   - Create `generate_rollup_function()` for rollup fields

2. Each generated function should:
   - Accept `(record, context)` parameters
   - Include docstring with formula and dependencies
   - Return properly typed value
   - Handle null/missing values gracefully

**Example Output:**
```python
def compute_full_name(record: Contact, context: ComputationContext) -> Optional[str]:
    """
    Compute Full Name field
    Formula: {First Name} & " " & {Last Name}
    Dependencies: first_name, last_name
    Depth: 1
    """
    # Null safety check
    if record.first_name is None or record.last_name is None:
        return None
    
    # Generated formula code
    return str(record.first_name) + " " + str(record.last_name)
```

### 🔮 Future Phases (3-6)
- **Phase 3:** Generate `ComputationContext` and `update_record()` function
- **Phase 4:** Type definitions (dataclass/TypedDict/dict)
- **Phase 5:** CLI integration and comprehensive testing
- **Phase 5B:** Advanced parity tests against live Airtable data
- **Phase 6:** Web UI integration

See [design document](./formula-evaluator-incremental-design.md) for full details.

## Key Concepts

### Computation Graph
Fields organized by **dependency depth**:

```python
{
    0: {  # No dependencies
        "fld001": FieldInfo(name="First Name", type="singleLineText", ...),
        "fld002": FieldInfo(name="Last Name", type="singleLineText", ...)
    },
    1: {  # Depends only on depth-0 fields
        "fld003": FieldInfo(
            name="Full Name",
            type="formula",
            dependencies=["fld001", "fld002"],
            dependents=["fld004"],  # Fields that use this one
            function_name="compute_full_name"
        )
    },
    2: { ... }  # Depends on depth-1 fields, etc.
}
```

### Incremental Update Algorithm

```python
def update_record(record, context, changed_fields=None):
    # If no fields specified, assume all changed
    if not changed_fields:
        changed_fields = all_fields
    
    fields_to_compute = set(changed_fields)
    
    # Process each depth in order
    for depth in range(max_depth + 1):
        for field in fields_at_depth[depth]:
            # Should compute if:
            # 1. Field itself changed, OR
            # 2. One of its dependencies was computed this cycle
            if needs_computation(field, fields_to_compute):
                new_value = compute_function(record, context)
                record[field] = new_value
                fields_to_compute.add(field)  # Propagate to dependents
```

## Data Access Patterns

The generator will support multiple ways to access record data:

### Python Dataclass (Recommended)
```python
@dataclass
class Contact:
    first_name: str
    last_name: str
    full_name: Optional[str] = None  # Computed

# Access
value = record.first_name
record.first_name = "John"
```

### Python Dictionary
```python
# Access
value = record["first_name"]
record["first_name"] = "John"
```

### Pydantic (Future)
```python
from pydantic import BaseModel

class Contact(BaseModel):
    first_name: str
    last_name: str
```

## Running Tests

```bash
# Run all tests
uv run pytest tests/test_incremental_runtime.py -v

# Run specific test
uv run pytest tests/test_incremental_runtime.py::TestComputationGraphBuilder::test_simple_graph_structure -v

# Run with coverage
uv run pytest tests/test_incremental_runtime.py --cov=web/code_generators/incremental_runtime_generator

# Run parity test helpers (available now)
uv run pytest tests/test_formula_parity.py::TestParityHelpers -v

# Run live Airtable parity tests (requires credentials, Phase 5B)
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
uv run pytest tests/test_formula_parity.py --airtable-live -v
```

### Parity Test Helper Functions ✅

The following parity test helpers are already implemented and tested:
- `extract_raw_fields()`: Separates raw fields from computed fields
- `get_computed_field_names()`: Gets list of computed field names from schema
- `assert_values_equal()`: Compares values with appropriate tolerances for different types

These are ready to use in Phase 5B when the full parity tests are implemented!

## Usage Example (Future)

Once fully implemented, usage will look like:

```python
from generated_evaluator import Contact, update_record, ComputationContext

# Create record
contact = Contact(id="rec123", first_name="John", last_name="Smith")

# Initial computation
context = ComputationContext(contact, {})
contact = update_record(contact, context)
print(contact.full_name)  # "John Smith"

# Update specific field
contact.first_name = "Jane"
contact = update_record(contact, context, changed_fields=["first_name"])
print(contact.full_name)  # "Jane Smith" (automatically recalculated)
print(contact.greeting)    # "Hello, Jane Smith" (cascaded)
```

## Integration with Existing Code

### Reuses Existing Components ✅
- `at_metadata_graph.py`: Graph building and depth calculation
- `python_runtime_generator.py`: Formula transpilation (will extend)
- `at_formula_parser.py`: Formula parsing
- `constants.py`: Field type constants

### New Components 🆕
- `incremental_runtime_generator.py`: Orchestrates generation
- Computation graph data structure
- Update function generator
- Context class generator

## Performance Goals

- **Simple update** (1 field, 1 dependent): < 1ms
- **Medium update** (5 fields, 10 dependents): < 5ms
- **Complex update** (20 fields, 50+ dependents): < 20ms

## Questions & Decisions

Before starting Phase 2, consider:

1. **AsyncIO Support**: Should we generate async/await code for async environments?
2. **Error Handling**: How should we handle formula evaluation errors?
3. **Transaction Support**: Do we need rollback capabilities?
4. **Type Stubs**: Should we generate `.pyi` files separately?

## Contributing

To continue this implementation:

1. Read the [design document](./formula-evaluator-incremental-design.md)
2. Start with Phase 2: Formula function generation
3. Follow TDD approach: write tests first
4. Maintain 80%+ test coverage
5. Update this README as you progress

## Resources

- **Design Doc:** [formula-evaluator-incremental-design.md](./formula-evaluator-incremental-design.md)
- **Core Module:** `web/code_generators/incremental_runtime_generator.py`
- **Tests:** `tests/test_incremental_runtime.py`
- **Existing Generator:** `web/code_generators/python_runtime_generator.py`
- **Graph Utils:** `web/at_metadata_graph.py`

---

**Status:** ✅ Phase 1 Complete | 📝 Ready for Phase 2
**Test Coverage:** 87% on new module | 8 tests passing
**Next Action:** Implement formula function generation (Phase 2)
