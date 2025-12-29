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
```

## Test Organization

- `conftest.py` - Shared fixtures and test utilities
- `test_at_metadata_graph.py` - Tests for graph construction and traversal
- `test_constants.py` - Tests for shared constants
- `test_error_handling.py` - Tests for error handling utilities (TODO)
- `test_formula_compressor.py` - Tests for formula compression (TODO)

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
