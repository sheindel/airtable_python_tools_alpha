# Phase 5B: Formula Parity Testing

## Overview

Phase 5B implements advanced parity tests that validate generated formula evaluators produce **identical results** to Airtable's own calculations. These tests fetch live data from Airtable and compare locally computed values against Airtable's values.

## Project Structure

```
tests/
├── test_formula_parity.py      # Main parity test suite
├── helpers/
│   ├── __init__.py
│   ├── airtable_api.py         # Airtable API utilities (schema, records)
│   └── comparison.py           # Value comparison utilities
└── README_PHASE5B.md           # This file

.cache/
└── airtable_schemas/           # Cached schemas (expires after 24 hours)
    └── appXXXXXXXXXXXXXX.json
```

## Setup

### 1. Environment Variables

Set your Airtable credentials:

```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
```

Or create a `.env` file:

```bash
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
```

### 2. Install Dependencies

```bash
uv sync --group dev
```

## Running Tests

### Run All Parity Tests

```bash
# Run with --airtable-live flag (required)
uv run pytest tests/test_formula_parity.py --airtable-live -v
```

### Run Specific Test Classes

```bash
# Only formula parity tests
uv run pytest tests/test_formula_parity.py::TestFormulaParity --airtable-live -v

# Only comparison utility tests (no API access needed)
uv run pytest tests/test_formula_parity.py::TestParityHelpers -v
```

### Run With Multiple Samples

Test with more random records for statistical confidence:

```bash
uv run pytest tests/test_formula_parity.py --airtable-live --samples=10 -v
```

### Without --airtable-live Flag

Tests marked with `@pytest.mark.airtable_live` will be **skipped**:

```bash
# These will be skipped
uv run pytest tests/test_formula_parity.py -v
```

## Test Strategy

### 1. Schema Caching

Schemas are cached locally for 24 hours to reduce API calls:

- **Cache location**: `.cache/airtable_schemas/{base_id}.json`
- **Expiry**: 24 hours
- **Refresh**: Automatic on expiry or use `force_refresh=True`

```python
from helpers.airtable_api import fetch_schema_cached

schema = fetch_schema_cached(base_id, api_key, force_refresh=True)
```

### 2. Random Record Selection

Tests use random records to increase coverage:

```python
from helpers.airtable_api import get_random_record_id, fetch_record

# Get random record ID
record_id = get_random_record_id(base_id, api_key, "Contacts")

# Fetch full record
record = fetch_record(base_id, api_key, "Contacts", record_id)
```

### 3. Raw Field Extraction

Separates computed fields from raw input fields:

```python
from helpers.airtable_api import extract_raw_fields, get_table_id_by_name

table_id = get_table_id_by_name(schema, "Contacts")
raw_fields = extract_raw_fields(full_record, schema, table_id)

# raw_fields contains only:
# - singleLineText
# - number
# - checkbox
# - multipleRecordLinks
# etc.

# Excludes computed fields:
# - formula
# - rollup
# - multipleLookupValues
# - count
```

### 4. Value Comparison

Intelligent comparison with type-specific handling:

```python
from helpers.comparison import assert_values_equal

# Numbers (with tolerance)
assert_values_equal(3.14159, 3.14160, "pi", tolerance=0.001)

# Strings (exact match)
assert_values_equal("hello", "hello", "greeting")

# Arrays (order-independent by default)
assert_values_equal([1, 2, 3], [3, 2, 1], "items")

# Arrays (order-dependent if needed)
assert_values_equal([1, 2, 3], [1, 2, 3], "items", array_order_matters=True)

# Nulls
assert_values_equal(None, None, "optional_field")
```

### 5. Bulk Comparison

Compare all computed fields at once:

```python
from helpers.comparison import compare_records

results = compare_records(
    local_record=local_contact,
    airtable_record=airtable_record,
    computed_field_names=["Full Name", "Age in Years", "Company Count"],
    tolerance=0.001
)

print(f"Matches: {results['matches']}")
print(f"Mismatches: {results['mismatches']}")
for error in results['errors']:
    print(f"  {error['field']}: {error['error']}")
```

## Test Workflow

### Current Status: Phase 5B Framework Complete ✅

The testing framework is ready but tests are skipped until Phase 5A (evaluator generation) is complete.

**What's implemented:**
- ✅ Airtable API utilities (schema, records)
- ✅ Schema caching (24-hour expiry)
- ✅ Random record selection
- ✅ Raw field extraction
- ✅ Value comparison utilities
- ✅ Pytest configuration (--airtable-live flag)
- ✅ Test fixtures and helpers

**What's pending (requires Phase 5A):**
- ⏳ Evaluator code generation
- ⏳ Execute generated code
- ⏳ Actual parity tests (currently skipped)

### Full Test Workflow (After Phase 5A)

```python
def test_formula_parity_full_workflow(airtable_config, airtable_schema):
    """Full parity test workflow (future implementation)."""
    
    # 1. Fetch schema (cached)
    schema = airtable_schema
    
    # 2. Pick random record
    record_id = get_random_record_id(
        airtable_config["base_id"],
        airtable_config["api_key"],
        "Contacts"
    )
    
    # 3. Fetch full record
    full_record = fetch_record(
        airtable_config["base_id"],
        airtable_config["api_key"],
        "Contacts",
        record_id
    )
    
    # 4. Extract raw fields
    table_id = get_table_id_by_name(schema, "Contacts")
    raw_fields = extract_raw_fields(full_record, schema, table_id)
    
    # 5. Generate evaluator (TODO: Phase 5A)
    evaluator_code = generate_evaluator_for_table(schema, table_id)
    
    # 6. Execute evaluator (TODO: Phase 5A)
    local_record = execute_evaluator_code(evaluator_code, raw_fields)
    
    # 7. Compare values
    computed_fields = get_computed_field_names(schema, table_id)
    results = compare_records(
        local_record,
        full_record,
        computed_fields,
        tolerance=0.001
    )
    
    # 8. Assert all match
    assert results['mismatches'] == 0, f"Found {results['mismatches']} mismatches"
```

## Helper Modules

### `helpers/airtable_api.py`

Functions for interacting with Airtable API:

- `fetch_schema_cached()` - Fetch schema with caching
- `fetch_schema_from_api()` - Direct API schema fetch
- `get_random_record_id()` - Select random record
- `fetch_record()` - Fetch single record by ID
- `fetch_records()` - Fetch multiple records (paginated)
- `extract_raw_fields()` - Separate computed from raw fields
- `get_computed_field_names()` - List computed field names
- `get_table_id_by_name()` - Lookup table ID by name
- `get_api_key()` - Get API key from env
- `get_base_id()` - Get base ID from env

### `helpers/comparison.py`

Functions for comparing values:

- `assert_values_equal()` - Compare two values with type-specific logic
- `compare_records()` - Compare all computed fields in a record
- `ValueMismatchError` - Custom exception for mismatches

## Configuration

### pytest.ini

Markers and defaults are configured in [pytest.ini](../pytest.ini):

```ini
[tool:pytest]
markers =
    airtable_live: tests requiring live Airtable API access
```

### Command-Line Options

Added via `pytest_addoption()`:

- `--airtable-live`: Enable live API tests (default: skip)
- `--samples=N`: Number of random samples to test (default: 3)

### Pytest Hooks

- `pytest_configure()`: Register markers
- `pytest_addoption()`: Add custom options
- `pytest_collection_modifyitems()`: Skip tests without `--airtable-live`

## Error Handling

### API Errors

```python
from helpers.airtable_api import AirtableAPIError

try:
    schema = fetch_schema_from_api(base_id, api_key)
except AirtableAPIError as e:
    print(f"API request failed: {e}")
```

### Comparison Errors

```python
from helpers.comparison import ValueMismatchError

try:
    assert_values_equal(local_val, airtable_val, "field_name")
except ValueMismatchError as e:
    print(f"Values don't match: {e}")
```

## Examples

### Test Helper Functions (Works Now)

```bash
# Test comparison utilities (no API needed)
uv run pytest tests/test_formula_parity.py::TestParityHelpers -v
```

Example test:

```python
def test_assert_values_equal_numbers():
    """Test numeric comparison with tolerance."""
    # Should pass
    assert_values_equal(1.0, 1.0001, "test", tolerance=0.001)
    
    # Should fail
    with pytest.raises(ValueMismatchError):
        assert_values_equal(1.0, 1.1, "test", tolerance=0.001)
```

### Full Parity Test (After Phase 5A)

```python
@pytest.mark.airtable_live
def test_simple_formulas(airtable_config, airtable_schema):
    """Test simple string/numeric formulas."""
    # Implementation pending Phase 5A
```

## Troubleshooting

### Tests Always Skip

**Problem**: Tests are skipped even with credentials set.

**Solution**: Add `--airtable-live` flag:

```bash
uv run pytest tests/test_formula_parity.py --airtable-live -v
```

### API Key Not Found

**Problem**: `ValueError: AIRTABLE_API_KEY environment variable not set`

**Solution**: Export credentials:

```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'helpers'`

**Solution**: Tests must be run from project root:

```bash
cd /path/to/airtable_python_tools_alpha
uv run pytest tests/test_formula_parity.py --airtable-live
```

### Cache Issues

**Problem**: Schema cache is stale

**Solution**: Delete cache and re-fetch:

```bash
rm -rf .cache/airtable_schemas/
uv run pytest tests/test_formula_parity.py --airtable-live
```

Or force refresh in code:

```python
schema = fetch_schema_cached(base_id, api_key, force_refresh=True)
```

## Next Steps

### After Phase 5A Complete

1. Implement `generate_evaluator_for_table()` function
2. Implement `execute_evaluator_code()` function
3. Remove `pytest.skip()` from parity tests
4. Add actual comparison logic
5. Run full test suite against live data

### Future Enhancements

- **Multi-table support**: Test linked records and cross-table formulas
- **Edge case library**: Collect known edge cases (nulls, division by zero)
- **Performance tracking**: Measure evaluation speed
- **Regression tests**: Save failing cases for future testing
- **CI integration**: Run parity tests in nightly builds

## Related Documentation

- [Design Document](../docs/formula-evaluator-incremental-design.md) - Phase 5B specification
- [Test README](README.md) - General testing documentation
- [Airtable API Docs](https://airtable.com/developers/web/api/introduction) - API reference

## Contributing

When adding new parity tests:

1. Use `@pytest.mark.airtable_live` decorator
2. Use fixtures: `airtable_config`, `airtable_schema`, `random_record`
3. Add docstrings explaining what's being tested
4. Use helper functions from `helpers/` modules
5. Handle errors gracefully (skip if table missing, etc.)

Example:

```python
@pytest.mark.airtable_live
def test_new_feature(airtable_config, airtable_schema):
    """Test description."""
    try:
        # Test implementation
        pass
    except AirtableAPIError as e:
        pytest.skip(f"API error: {e}")
```
