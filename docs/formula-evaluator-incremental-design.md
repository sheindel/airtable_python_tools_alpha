# Formula Evaluator with Incremental Computation - Design Document

## Overview

This document outlines the design for a new code generation module that creates efficient formula evaluators with incremental computation capabilities. The goal is to minimize unnecessary recalculations when data changes by only recomputing formulas whose dependencies have actually changed.

## Core Concept

When a record is updated, we want to:
1. Accept a list of changed fields (or assume all fields if not provided)
2. Only recalculate formulas that depend on those changed fields
3. Avoid recalculating the same formula multiple times
4. Process formulas in the correct order (respecting dependencies)

## Architecture

### 1. Data Structures

#### 1.1 Formula Depth Groups
```python
{
    0: {  # Depth 0: No formula dependencies
        "fldXXX": {
            "name": "First Name",
            "type": "singleLineText",
            "table": "tblContacts",
            "function": compute_first_name  # For computed fields
        },
        "fldYYY": { ... }
    },
    1: {  # Depth 1: Depends only on depth-0 fields
        "fldZZZ": {
            "name": "Full Name",
            "type": "formula",
            "table": "tblContacts",
            "dependencies": ["fldXXX", "fldYYY"],
            "dependents": ["fldAAA", "fldBBB"],
            "function": compute_full_name
        }
    },
    2: { ... }  # And so on
}
```

**Key Properties:**
- Indexed by formula depth (integer from 0 to max_depth)
- Each depth contains a dictionary of field IDs
- Each field stores:
  - Metadata (name, type, table)
  - `dependencies`: list of field IDs this formula depends on
  - `dependents`: list of field IDs that depend on this formula
  - `function`: callable that computes the field value

#### 1.2 Dependency Graph Data
Already exists in `at_metadata_graph.py`:
- `metadata_to_graph()`: Creates NetworkX DiGraph
- `get_formula_depth()`: Calculates depth for each field
- `get_computation_order()`: Returns fields grouped by depth

### 2. Code Generation Output

The generated code will include:

#### 2.1 Type Definitions
Based on chosen data access pattern:

**Python Dataclass:**
```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class Contact:
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None  # Computed
    
    # Metadata for computed fields
    _computed_fields = {"full_name"}
```

**Python TypedDict:**
```python
from typing import TypedDict, Optional

class Contact(TypedDict, total=False):
    id: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: Optional[str]  # Computed
```

**Python Dictionary:**
```python
# No type definition, just documentation
# Contact = {
#     "id": str,
#     "first_name": str,
#     "last_name": str,
#     "full_name": str  # Computed from first_name, last_name
# }
```

#### 2.2 Formula Functions
Each formula becomes a standalone function:

```python
def compute_full_name(record: Contact, context: ComputationContext) -> Optional[str]:
    """
    Compute Full Name field
    Formula: {First Name} & " " & {Last Name}
    Dependencies: first_name, last_name
    """
    # Null safety checks (if enabled)
    if record.first_name is None or record.last_name is None:
        return None
    
    # Generated formula code
    return str(record.first_name) + " " + str(record.last_name)
```

#### 2.3 Computation Context
```python
class ComputationContext:
    """
    Context object passed to all formula functions.
    Provides access to related records for lookups/rollups.
    """
    def __init__(self, record: Any, all_records: Dict[str, List[Any]]):
        self.record = record
        self.all_records = all_records  # Tables of related records
        self.computed_this_cycle = set()  # Track what we've computed
    
    def get_linked_records(self, field_name: str) -> List[Any]:
        """Get records linked via a multipleRecordLinks field."""
        linked_ids = getattr(self.record, field_name, [])
        table_id = LINKED_TABLE_MAP[field_name]
        return [r for r in self.all_records.get(table_id, []) 
                if r.id in linked_ids]
    
    def lookup(self, link_field: str, target_field: str) -> List[Any]:
        """Perform a lookup operation."""
        linked_records = self.get_linked_records(link_field)
        return [getattr(r, target_field) for r in linked_records]
    
    def rollup(self, link_field: str, target_field: str, 
               aggregation: str) -> Any:
        """Perform a rollup operation."""
        values = self.lookup(link_field, target_field)
        if aggregation == "SUM":
            return sum(v for v in values if v is not None)
        elif aggregation == "COUNT":
            return len(values)
        # ... other aggregations
```

#### 2.4 Computation Graph Data Structure
```python
# Generated at code-generation time, embedded in output
COMPUTATION_GRAPH = {
    "max_depth": 3,
    "depths": {
        0: {
            "fldGmD6imIF6DXO6I": {
                "name": "first_name",
                "type": "singleLineText",
                "table": "tbl2OGQy64kSZEM93",
                "dependencies": [],
                "dependents": ["fldILdQXpcUeXKwT5"]
            },
            "fldzDPm0Tfe9piGCd": {
                "name": "last_name",
                "type": "singleLineText",
                "table": "tbl2OGQy64kSZEM93",
                "dependencies": [],
                "dependents": ["fldILdQXpcUeXKwT5"]
            }
        },
        1: {
            "fldILdQXpcUeXKwT5": {
                "name": "full_name",
                "type": "formula",
                "table": "tbl2OGQy64kSZEM93",
                "dependencies": ["fldGmD6imIF6DXO6I", "fldzDPm0Tfe9piGCd"],
                "dependents": ["fldXXXXXXX"],  # Other fields that use full_name
                "function_name": "compute_full_name"
            }
        },
        2: { ... }
    },
    "field_id_to_name": {
        "fldGmD6imIF6DXO6I": "first_name",
        "fldzDPm0Tfe9piGCd": "last_name",
        "fldILdQXpcUeXKwT5": "full_name"
    },
    "field_name_to_id": {
        "first_name": "fldGmD6imIF6DXO6I",
        "last_name": "fldzDPm0Tfe9piGCd",
        "full_name": "fldILdQXpcUeXKwT5"
    },
    "table_fields": {
        "tbl2OGQy64kSZEM93": ["first_name", "last_name", "full_name", ...]
    }
}

# Mapping of field names to their computation functions
FIELD_COMPUTERS = {
    "full_name": compute_full_name,
    "source_date": compute_source_date,
    # ... all computed fields
}
```

#### 2.5 Main Update Function
```python
def update_record(
    record: Contact,
    context: ComputationContext,
    changed_fields: Optional[List[str]] = None
) -> Contact:
    """
    Update a record by recomputing affected formula fields.
    
    Args:
        record: The record to update
        context: Computation context with related records
        changed_fields: List of field names that changed.
                       If None or empty, assume all fields changed.
    
    Returns:
        Updated record with recomputed formulas
    """
    # If no changed fields specified, assume everything changed
    if not changed_fields:
        changed_fields = COMPUTATION_GRAPH["table_fields"][record._table_id]
    
    # Convert field names to IDs
    changed_field_ids = set()
    for name in changed_fields:
        field_id = COMPUTATION_GRAPH["field_name_to_id"].get(name)
        if field_id:
            changed_field_ids.add(field_id)
    
    # Track what needs recalculation
    fields_to_compute = set()
    
    # Process each depth level in order
    for depth in range(COMPUTATION_GRAPH["max_depth"] + 1):
        depth_fields = COMPUTATION_GRAPH["depths"][depth]
        
        # For each field at this depth
        for field_id, field_info in depth_fields.items():
            # Skip if not a computed field
            if field_info["type"] not in ["formula", "rollup", "multipleLookupValues", "count"]:
                continue
            
            # Check if this field needs recomputation
            should_compute = False
            
            # Reason 1: Field is in the initial changed list
            if field_id in changed_field_ids:
                should_compute = True
            
            # Reason 2: One of its dependencies changed
            elif any(dep_id in fields_to_compute for dep_id in field_info["dependencies"]):
                should_compute = True
            
            # Compute if needed
            if should_compute and field_id not in context.computed_this_cycle:
                field_name = field_info["name"]
                compute_func = FIELD_COMPUTERS[field_name]
                
                # Compute the new value
                new_value = compute_func(record, context)
                
                # Update the record (depends on data access mode)
                setattr(record, field_name, new_value)
                
                # Mark as computed and as changed (for downstream dependencies)
                context.computed_this_cycle.add(field_id)
                fields_to_compute.add(field_id)
    
    return record
```

### 3. Data Access Modes

The generator supports multiple data access patterns:

#### 3.1 Python Dataclass (Recommended)
```python
@dataclass
class Contact:
    first_name: str
    last_name: str

# Access
value = record.first_name
record.first_name = "John"
```

**Pros:** Type-safe, IDE autocomplete, clean syntax
**Cons:** Slightly less flexible than dicts

#### 3.2 Python Dictionary
```python
Contact = Dict[str, Any]

# Access
value = record["first_name"]
record["first_name"] = "John"
```

**Pros:** Maximum flexibility, JSON-compatible
**Cons:** No type safety, no autocomplete

#### 3.3 Pydantic Model (Future)
```python
from pydantic import BaseModel

class Contact(BaseModel):
    first_name: str
    last_name: str
```

**Pros:** Runtime validation, type safety, JSON serialization
**Cons:** Slightly heavier dependency

### 4. Implementation Plan

#### Phase 1: Core Data Structure Builder (Week 1)
**File:** `web/code_generators/incremental_runtime_generator.py`

Tasks:
1. ✅ Already have: `get_computation_order()` from `at_metadata_graph.py`
2. Build `build_computation_graph()` function:
   - Use existing `metadata_to_graph()` and `get_computation_order()`
   - For each field at each depth:
     - Extract dependencies (predecessors in graph)
     - Extract dependents (successors in graph)
     - Store field metadata
3. Create `ComputationGraph` class to encapsulate the data structure
4. Write unit tests for graph building

**Deliverable:** Function that takes Airtable metadata and produces the computation graph data structure

#### Phase 2: Formula Function Generator (Week 2)
**File:** Extend `web/code_generators/python_runtime_generator.py`

Tasks:
1. ✅ Already have: `PythonFormulaTranspiler` class
2. Create `generate_formula_function()`:
   - Input: field metadata, formula AST, data access mode
   - Output: Python function definition string
   - Use existing transpiler
   - Add null safety checks (configurable)
   - Add docstring with formula and dependencies
3. Create `generate_lookup_function()` for lookup fields
4. Create `generate_rollup_function()` for rollup fields
5. Write unit tests for each function generator

**Deliverable:** Functions that generate Python code for each computed field type

#### Phase 3: Update Function Generator (Week 3)
**File:** Continue in `incremental_runtime_generator.py`

Tasks:
1. Implement `generate_update_function()`:
   - Generate the main `update_record()` function
   - Embed the computation graph data structure
   - Generate the field-to-function mapping
   - Support different data access modes
2. Implement `generate_context_class()`:
   - Generate `ComputationContext` class
   - Include lookup/rollup helpers
   - Support related record access
3. Write integration tests

**Deliverable:** Complete update function generator

#### Phase 4: Type Definition Generator (Week 4)
**File:** Extend existing `web/types_generator.py`

Tasks:
1. Enhance existing type generator:
   - Add option for dataclass vs TypedDict
   - Mark computed fields in docstrings
   - Generate proper type hints for optional fields
2. Create `generate_complete_module()`:
   - Combine types + functions + update logic
   - Add imports
   - Add module docstring
   - Format with proper indentation
3. Write integration tests for full module generation

**Deliverable:** Complete module generator that outputs a usable Python file

#### Phase 5: CLI Integration & Testing (Week 5)
**File:** `main.py` and integration tests

Tasks:
1. Add new CLI command:
   ```bash
   uv run python main.py generate-evaluator \
       --schema crm_schema.json \
       --output evaluator.py \
       --mode dataclass \
       --null-checks
   ```
2. Create comprehensive test suite:
   - Use `crm_schema.json` for tests
   - Test with actual record updates
   - Verify incremental computation (only necessary recalcs)
   - Performance benchmarks
3. Add to CI/CD pipeline
4. Write documentation

**Deliverable:** Production-ready CLI command with full test coverage

#### Phase 5B: Advanced Parity Tests (Week 6)
**File:** `tests/test_formula_parity.py`

**Goal:** Validate that generated formula evaluators produce **identical results** to Airtable's own calculations.

**Test Strategy:**
```python
def test_formula_parity_against_live_airtable():
    """
    Test that our formula evaluation matches Airtable exactly.
    
    Steps:
    1. Fetch schema from Airtable (with caching)
    2. Pick random record ID using heuristic
    3. Retrieve full record with all fields
    4. Extract raw (non-computed) field values
    5. Generate evaluator code
    6. Compute all formulas locally
    7. Compare local vs Airtable values
    """
    # Setup
    base_id = os.getenv("AIRTABLE_BASE_ID")
    api_key = os.getenv("AIRTABLE_API_KEY")
    
    # Step 1: Get schema (cached)
    schema = fetch_schema_cached(base_id, api_key)
    
    # Step 2: Get random record
    record_id = get_random_record_id(base_id, api_key, table_name="Contacts")
    
    # Step 3: Fetch full record
    full_record = fetch_record(base_id, api_key, table_name="Contacts", record_id=record_id)
    
    # Step 4: Extract raw fields (non-computed)
    raw_fields = extract_raw_fields(full_record, schema)
    
    # Step 5: Generate evaluator
    evaluator_code = generate_complete_module(schema, table_id="tblContacts")
    exec(evaluator_code, globals())  # Load generated code
    
    # Step 6: Compute locally
    local_record = Contact(**raw_fields)
    context = ComputationContext(local_record, {})
    local_record = update_record(local_record, context)
    
    # Step 7: Compare results
    computed_fields = get_computed_field_names(schema, table_id="tblContacts")
    for field_name in computed_fields:
        airtable_value = full_record["fields"][field_name]
        local_value = getattr(local_record, field_name)
        
        assert_values_equal(
            local_value, 
            airtable_value, 
            field_name=field_name,
            tolerance=0.001  # For floating point comparisons
        )
```

**Implementation Details:**

1. **Schema Caching:**
```python
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_DIR = Path(".cache/airtable_schemas")
CACHE_EXPIRY = timedelta(hours=24)

def fetch_schema_cached(base_id: str, api_key: str) -> dict:
    """Fetch schema from Airtable with local caching."""
    cache_file = CACHE_DIR / f"{base_id}.json"
    
    # Check if cache exists and is fresh
    if cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age < CACHE_EXPIRY:
            print(f"Using cached schema (age: {cache_age})")
            return json.loads(cache_file.read_text())
    
    # Fetch fresh schema
    print("Fetching fresh schema from Airtable API...")
    schema = fetch_schema_from_api(base_id, api_key)
    
    # Save to cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(schema, indent=2))
    
    return schema
```

2. **Random Record Selection:**
```python
def get_random_record_id(base_id: str, api_key: str, table_name: str) -> str:
    """
    Get a random record ID using a heuristic approach.
    
    Heuristics:
    1. Try to get records from first page (fast)
    2. If available, use random offset
    3. Pick random record from results
    """
    import random
    
    # Fetch first page of records (max 100)
    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"maxRecords": 100}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    records = response.json()["records"]
    if not records:
        raise ValueError(f"No records found in table {table_name}")
    
    # Pick random record
    random_record = random.choice(records)
    return random_record["id"]
```

3. **Raw Field Extraction:**
```python
def extract_raw_fields(full_record: dict, schema: dict) -> dict:
    """
    Extract only raw (non-computed) fields from a record.
    
    Args:
        full_record: Full record from Airtable API
        schema: Airtable metadata schema
    
    Returns:
        Dict with only raw field values (excludes formulas, lookups, rollups, count)
    """
    computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
    
    # Build set of computed field names
    computed_field_names = set()
    for table in schema["tables"]:
        for field in table["fields"]:
            if field["type"] in computed_types:
                computed_field_names.add(field["name"])
    
    # Extract only raw fields
    raw_fields = {}
    for field_name, value in full_record["fields"].items():
        if field_name not in computed_field_names:
            raw_fields[field_name] = value
    
    return raw_fields
```

4. **Value Comparison:**
```python
def assert_values_equal(
    local_value: Any,
    airtable_value: Any,
    field_name: str,
    tolerance: float = 0.001
):
    """
    Compare local and Airtable values with appropriate tolerances.
    
    Handles:
    - Numbers (with floating point tolerance)
    - Strings (exact match)
    - Dates (format normalization)
    - Arrays (order-independent for lookup/rollup)
    - Null/None equivalence
    """
    # Handle None/null
    if local_value is None and airtable_value is None:
        return
    if local_value is None or airtable_value is None:
        raise AssertionError(
            f"Field '{field_name}': null mismatch\n"
            f"  Local: {local_value}\n"
            f"  Airtable: {airtable_value}"
        )
    
    # Handle numbers
    if isinstance(local_value, (int, float)) and isinstance(airtable_value, (int, float)):
        if abs(local_value - airtable_value) > tolerance:
            raise AssertionError(
                f"Field '{field_name}': numeric mismatch\n"
                f"  Local: {local_value}\n"
                f"  Airtable: {airtable_value}\n"
                f"  Difference: {abs(local_value - airtable_value)}"
            )
        return
    
    # Handle strings
    if isinstance(local_value, str) and isinstance(airtable_value, str):
        if local_value != airtable_value:
            raise AssertionError(
                f"Field '{field_name}': string mismatch\n"
                f"  Local: {repr(local_value)}\n"
                f"  Airtable: {repr(airtable_value)}"
            )
        return
    
    # Handle arrays (order-independent for lookups/rollups)
    if isinstance(local_value, list) and isinstance(airtable_value, list):
        if sorted(local_value) != sorted(airtable_value):
            raise AssertionError(
                f"Field '{field_name}': array mismatch\n"
                f"  Local: {local_value}\n"
                f"  Airtable: {airtable_value}"
            )
        return
    
    # Default: exact equality
    if local_value != airtable_value:
        raise AssertionError(
            f"Field '{field_name}': mismatch\n"
            f"  Local: {local_value} ({type(local_value).__name__})\n"
            f"  Airtable: {airtable_value} ({type(airtable_value).__name__})"
        )
```

**Test Configuration:**
```bash
# .env file
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Run parity tests
uv run pytest tests/test_formula_parity.py -v --airtable-live

# Run with specific table
uv run pytest tests/test_formula_parity.py::test_parity_contacts_table -v

# Run with multiple random samples
uv run pytest tests/test_formula_parity.py --samples=10
```

**Test Suite Structure:**
```python
@pytest.mark.airtable_live  # Skip by default (requires API access)
class TestFormulaParity:
    """Test formula evaluation against live Airtable data."""
    
    def test_simple_formula_fields(self, live_airtable_fixture):
        """Test basic formula fields (string concat, arithmetic)."""
        pass
    
    def test_lookup_fields(self, live_airtable_fixture):
        """Test lookup field evaluation."""
        pass
    
    def test_rollup_fields(self, live_airtable_fixture):
        """Test rollup aggregations (SUM, AVG, COUNT, etc.)."""
        pass
    
    def test_nested_formulas(self, live_airtable_fixture):
        """Test formulas that reference other formulas."""
        pass
    
    def test_edge_cases(self, live_airtable_fixture):
        """Test null values, empty strings, zero division, etc."""
        pass
    
    @pytest.mark.parametrize("table_name", ["Contacts", "Companies", "Deals"])
    def test_all_tables(self, live_airtable_fixture, table_name):
        """Test all tables in the base."""
        pass
    
    def test_multiple_random_samples(self, live_airtable_fixture):
        """Test with multiple random records for statistical confidence."""
        for _ in range(10):
            # Test random record
            pass
```

**Benefits:**
1. **Validation**: Proves generated code matches Airtable exactly
2. **Regression Testing**: Catch formula evaluation bugs
3. **Confidence**: Statistical sampling across many records
4. **Edge Cases**: Discovers real-world data patterns
5. **Documentation**: Serves as live examples of correct behavior

**Challenges & Solutions:**
- **API Rate Limits**: Use caching, implement backoff
- **Large Bases**: Test random sample, not all records
- **Linked Records**: Need to fetch related records for context
- **Formula Complexity**: Start simple, add complex cases incrementally
- **Flakiness**: Handle Airtable API errors gracefully

**Deliverable:** High-confidence validation that generated evaluators match Airtable's calculations

#### Phase 6: Web UI Integration (Week 7)
**File:** New tab `web/tabs/evaluator_generator.py`

Tasks:
1. Create new tab in web UI
2. Allow users to:
   - Select data access mode
   - Configure options (null checks, etc.)
   - Preview generated code
   - Download as .py file
3. Add to `web/main.py` tab initialization
4. Update documentation

**Deliverable:** Web UI for evaluator generation

### 5. Usage Examples

#### Example 1: Simple Formula Update
```python
from generated_evaluator import Contact, update_record, ComputationContext

# Create a record
contact = Contact(
    id="rec123",
    first_name="John",
    last_name="Smith"
)

# Initial computation (all fields)
context = ComputationContext(contact, {})
contact = update_record(contact, context)
print(contact.full_name)  # "John Smith"

# Update only last name
contact.last_name = "Doe"
contact = update_record(contact, context, changed_fields=["last_name"])
print(contact.full_name)  # "John Doe"
```

#### Example 2: Cascading Updates
```python
# Formula depths:
# 0: first_name, last_name
# 1: full_name = {first_name} & " " & {last_name}
# 2: greeting = "Hello, " & {full_name}

# Change first_name -> recomputes full_name -> recomputes greeting
contact.first_name = "Jane"
contact = update_record(contact, context, changed_fields=["first_name"])

# Both full_name and greeting are updated automatically
print(contact.full_name)  # "Jane Doe"
print(contact.greeting)   # "Hello, Jane Doe"
```

#### Example 3: Lookup Fields
```python
# Contacts table has a lookup to Companies table
context = ComputationContext(
    record=contact,
    all_records={
        "tblCompanies": [company1, company2, ...],
        "tblContacts": [contact1, contact2, ...]
    }
)

# When company link changes, biz_phone lookup is recomputed
contact.company_link = ["recCompanyXYZ"]
contact = update_record(contact, context, changed_fields=["company_link"])
print(contact.biz_phone)  # Automatically fetched from linked company
```

### 6. Performance Considerations

#### 6.1 Optimization Strategies
1. **Lazy Evaluation**: Only compute when `update_record()` is called
2. **Dependency Pruning**: Skip entire depth levels if no dependencies changed
3. **Memoization**: Track computed fields to avoid duplicate work
4. **Batch Updates**: Process multiple records with shared context

#### 6.2 Benchmarking Targets
- **Simple update** (1 field, 1 dependent): < 1ms
- **Medium update** (5 fields, 10 dependents): < 5ms
- **Complex update** (20 fields, 50+ dependents): < 20ms
- **Full recompute** (all fields): Baseline comparison

### 7. Configuration Options

```python
GeneratorOptions = {
    # Data access pattern
    "data_access_mode": "dataclass" | "dict" | "pydantic",
    
    # Code generation
    "include_null_checks": True,        # Add null safety
    "include_type_hints": True,         # Add type annotations
    "include_docstrings": True,         # Add documentation
    "include_examples": False,          # Generate usage examples
    
    # Optimization
    "optimize_depth_skipping": True,    # Skip entire depth levels when possible
    "track_computation_stats": False,   # Add performance tracking code
    
    # Output format
    "output_format": "single_file" | "module",  # Single file or package
    "include_tests": False,             # Generate unit tests
}
```

### 8. Future Enhancements

#### 8.1 Multi-Language Support
- **JavaScript/TypeScript**: For browser/Node.js environments
- **SQL**: Generate database triggers/functions
- **Rust**: For high-performance applications

#### 8.2 Advanced Features
- **Circular dependency detection**: Warn about formula cycles
- **Dependency visualization**: Generate Mermaid diagrams
- **Change tracking**: Record what changed and why
- **Audit log**: Track all recomputations

#### 8.3 Real-Time Updates
- **WebSocket integration**: Push updates from server
- **React hooks**: `useAirtableRecord()` with auto-updates
- **Observable pattern**: Subscribe to field changes

### 9. Relationship to Existing Code

#### 9.1 Reuse from Current Codebase
✅ **Already have:**
- `at_metadata_graph.py`: Graph building, depth calculation
- `python_runtime_generator.py`: Formula transpilation
- `at_formula_parser.py`: Parse formulas into AST
- `constants.py`: Field type constants

📝 **Need to create:**
- `incremental_runtime_generator.py`: Main generator module
- Computation graph builder
- Update function generator
- Integration between components

#### 9.2 Integration Points
- **CLI**: Add new command to `main.py`
- **Web UI**: New tab similar to `code_generator.py`
- **Tests**: Extend `tests/` with evaluator tests
- **Docs**: Add to `/docs` with examples

### 10. Success Criteria

✅ **Functional Requirements:**
- Generate correct Python code from Airtable schema
- Support all formula types (formula, lookup, rollup, count)
- Incremental updates only recompute affected fields
- Handle circular dependencies gracefully
- Support multiple data access patterns

✅ **Non-Functional Requirements:**
- Performance: < 20ms for complex updates
- Code quality: 80%+ test coverage
- Documentation: Complete API docs and examples
- Usability: Works via CLI and web UI
- Maintainability: Clean, modular architecture

### 11. Next Steps

**Immediate Actions:**
1. ✅ Review this design document with team
2. Create skeleton file structure
3. Write unit tests for Phase 1 (TDD approach)
4. Implement Phase 1: Computation graph builder
5. Demo working prototype

**Questions to Resolve:**
- ❓ Should we support AsyncIO for async formula evaluation?
- ❓ Do we need transaction support (rollback on error)?
- ❓ Should we generate type stubs (.pyi) separately?
- ❓ How should we handle lookup/rollup errors (missing linked records)?

---

## Appendix A: Code Structure

```
web/
├── code_generators/
│   ├── incremental_runtime_generator.py  # NEW: Main module
│   ├── python_runtime_generator.py       # EXTEND: Add null checks
│   ├── javascript_runtime_generator.py   # FUTURE
│   └── sql_runtime_generator.py          # FUTURE
├── tabs/
│   └── evaluator_generator.py            # NEW: Web UI tab
└── at_metadata_graph.py                  # EXISTING: Reuse

tests/
├── test_incremental_runtime.py           # NEW: Unit tests
└── test_integration_evaluator.py         # NEW: Integration tests

docs/
└── formula-evaluator-incremental-design.md  # THIS FILE
```

## Appendix B: Example Generated Code

See inline examples throughout document, particularly sections 2.1-2.5.

## Appendix C: References

- [Airtable Formula Reference](https://support.airtable.com/docs/formula-field-reference)
- [NetworkX Documentation](https://networkx.org/)
- [Python dataclasses](https://docs.python.org/3/library/dataclasses.html)
- [TypedDict](https://docs.python.org/3/library/typing.html#typing.TypedDict)
- Existing project files: `at_metadata_graph.py`, `python_runtime_generator.py`
