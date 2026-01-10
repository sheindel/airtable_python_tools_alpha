# Test Suite for Airtable Analysis Tools

This directory contains unit tests for the core Python business logic.

## Running Tests

### Unit Tests (Fast, Default)
```bash
# Run all unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=web --cov-report=html

# Run specific test file
uv run pytest tests/test_at_metadata_graph.py

# Run tests matching a pattern
uv run pytest -k "test_formula"

# Verbose output
uv run pytest -v

# Run performance benchmarks
uv run pytest tests/test_performance_benchmarks.py -v -s

# Run benchmarks with external schema
BENCHMARK_SCHEMA=/path/to/schema.json uv run pytest tests/test_performance_benchmarks.py -v
```

### Integration Tests (Real Airtable Data)
```bash
# Set up credentials first
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX

# Run ALL tests including integration tests
uv run pytest --airtable-live

# Run only integration tests
uv run pytest -m airtable_live --airtable-live -v

# Run specific integration test class
uv run pytest tests/test_complexity_scorecard.py::TestComplexityScorecardIntegration --airtable-live -v
```

**Note**: Integration tests are skipped by default. Use `--airtable-live` to enable them.

See [Integration Testing Guide](../docs/integration-testing-guide.md) for comprehensive documentation.

## Performance Benchmarks

The test suite includes performance benchmarks to measure code generation speed and track regressions:

```bash
# Run all benchmarks
uv run pytest tests/test_performance_benchmarks.py -v -s

# Run specific benchmark
uv run pytest tests/test_performance_benchmarks.py::TestPythonGeneratorPerformance::test_python_library_generation_time -v
```

**Benchmarked Operations**:
- Python Server SDK generation
- TypeScript client library generation
- SQL schema generation
- Complete workflow execution

**Performance Thresholds**:
- Python SDK: < 5 seconds
- TypeScript types: < 2 seconds
- SQL generation: < 4 seconds
- Full-stack workflow: < 10 seconds

See [test_performance_benchmarks.py](test_performance_benchmarks.py) for details.

## Test Organization

### Core Test Files
- `conftest.py` - Shared fixtures, pytest configuration, and Airtable API fixtures
- `schema_loader.py` - Utilities for loading test schemas (supports external schemas)
- `test_at_metadata_graph.py` - Graph construction and traversal (+ integration tests)
- `test_complexity_scorecard.py` - Complexity scoring (+ integration tests)
- `test_formula_compressor.py` - Formula compression (+ integration tests)
- `test_dependency_mapper.py` - Dependency mapping (+ integration tests)
- `test_mermaid_generator.py` - Mermaid diagram generation (+ integration tests)
- `test_unused_fields.py` - Unused field detection (+ integration tests)
- `test_constants.py` - Shared constants validation
- `test_error_handling.py` - Error handling utilities
- `test_performance_benchmarks.py` - Performance benchmarks for code generators
- `test_formula_parity.py` - Formula evaluation parity tests (Phase 5B)

### Helper Modules
- `helpers/airtable_api.py` - Airtable API utilities (schema fetching, caching)
- `helpers/comparison.py` - Value comparison utilities for parity testing
- `helpers/__init__.py` - Helper module initialization

### Test Data
- `schemas/` - Directory for external test schemas (gitignored)
- `.cache/airtable_schemas/` - Cached schemas from API (24hr expiry)

### External Test Schemas

The `schemas/` directory (gitignored) allows you to test with large, complex, or proprietary schemas without committing them:

```bash
# Add an external schema
cp ~/my-large-base.json tests/schemas/large-base.json

# Use it in tests
SCHEMA_PATH=tests/schemas/large-base.json uv run pytest

# Or use SchemaLoader in test code
from schema_loader import SchemaLoader
metadata = SchemaLoader.load("large-base")
```

See [schemas/README.md](schemas/README.md) for details on using external schemas.

## Writing Tests

### Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Using Fixtures
```python
def test_something(sample_metadata):
    # sample_metadata is automatically provided by fixture
    graph = metadata_to_graph(sample_metadata)
    assert graph is not None
```

### Coverage Goals
- Core business logic: 80%+ coverage
- Graph operations: 90%+ coverage
- Error handling: 70%+ coverage

## Future Tests Needed

1. **Formula Compression**
   - Test recursive expansion
   - Test circular dependency detection
   - Test max depth limiting

2. **Error Handling**
   - Test all custom exceptions
   - Test error display formatting
   - Test validation functions

3. **Mermaid Generation**
   - Test diagram generation
   - Test different display modes
   - Test field ID to name conversion

4. **Formula Evaluator**
   - Test expression evaluation
   - Test field substitution
   - Test error cases

## CI/CD Integration

Tests will run automatically in GitHub Actions before deployment (TODO).
