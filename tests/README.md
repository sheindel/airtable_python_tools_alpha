# Test Suite for Airtable Analysis Tools

This directory contains unit tests for the core Python business logic.

## Running Tests

```bash
# Run all tests
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

- `conftest.py` - Shared fixtures and test utilities
- `schema_loader.py` - Utilities for loading test schemas (supports external schemas)
- `test_at_metadata_graph.py` - Tests for graph construction and traversal
- `test_constants.py` - Tests for shared constants
- `test_performance_benchmarks.py` - Performance benchmarks for code generators
- `test_error_handling.py` - Tests for error handling utilities (TODO)
- `test_formula_compressor.py` - Tests for formula compression (TODO)
- `schemas/` - Directory for external test schemas (gitignored)

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
