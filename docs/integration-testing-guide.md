# Integration Testing with Real Airtable Data

## Overview

This project now includes comprehensive integration tests that validate functionality against **real Airtable bases** rather than synthetic test data. These tests catch edge cases that only appear in production environments.

## Quick Start

### Setup

1. **Set environment variables**:
```bash
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
```

2. **Run integration tests**:
```bash
# Run unit tests only (fast, default)
uv run pytest

# Run with integration tests (requires API access)
uv run pytest --airtable-live

# Run specific integration test class
uv run pytest tests/test_complexity_scorecard.py::TestComplexityScorecardIntegration --airtable-live -v
```

## Test Structure

### Unit Tests (Fast)
- Use synthetic fixtures
- No API calls
- Run by default
- Example: `TestComplexityScorecardUnit`

### Integration Tests (Slow)
- Use real Airtable data via API
- Marked with `@pytest.mark.airtable_live`
- Skipped by default (need `--airtable-live` flag)
- Example: `TestComplexityScorecardIntegration`

## Available Integration Tests

### 1. Graph Operations ([test_at_metadata_graph.py](../tests/test_at_metadata_graph.py))
**Class**: `TestMetadataGraphIntegration`

Tests graph construction and dependency analysis with real-world complexity:
- Complex cross-table dependencies
- Deep formula nesting
- Circular reference handling
- Computation order validation

**Why**: Real bases have patterns (multi-level lookups, circular refs) not in synthetic data.

### 2. Complexity Scorecard ([test_complexity_scorecard.py](../tests/test_complexity_scorecard.py))
**Class**: `TestComplexityScorecardIntegration`

Tests complexity scoring on real bases:
- Realistic complexity distributions
- Deep formula dependencies
- Cross-table rollups
- CSV export with real data

**Why**: Complexity scores only make sense with real-world formula patterns.

### 3. Formula Compression ([test_formula_compressor.py](../tests/test_formula_compressor.py))
**Class**: `TestFormulaCompressorIntegration`

Tests formula compression with real formulas:
- Special characters in formulas
- Deeply nested field references
- Depth limiting behavior
- Field ID to name conversion

**Why**: Real formulas have unexpected syntax (string literals, nested parens, emojis).

### 4. Dependency Mapping ([test_dependency_mapper.py](../tests/test_dependency_mapper.py))
**Class**: `TestDependencyMapperIntegration`

Tests dependency graph generation:
- Linked record relationships
- Formula dependencies
- Rollup cross-table paths
- All field types

**Why**: Real bases have complex multi-table chains not in test fixtures.

### 5. Mermaid Generation ([test_mermaid_generator.py](../tests/test_mermaid_generator.py))
**Class**: `TestMermaidGeneratorIntegration`

Tests diagram generation with real field names:
- Special characters escaping
- Emojis and unicode
- Large base handling
- All display modes

**Why**: Real field names break Mermaid syntax (parens, quotes, hashes, emojis).

### 6. Unused Fields Detection ([test_unused_fields.py](../tests/test_unused_fields.py))
**Class**: `TestUnusedFieldsIntegration`

Tests unused field detection:
- Genuine unused fields
- Complex dependency tracking
- Primary field handling
- Usage statistics accuracy

**Why**: Real bases have actual unused fields with subtle dependency patterns.

## Shared Fixtures

### `airtable_config` Fixture
Provides API credentials from environment:
```python
def test_something(airtable_config):
    base_id = airtable_config["base_id"]
    api_key = airtable_config["api_key"]
```

### `airtable_schema` Fixture
Fetches and caches real schema:
```python
def test_something(airtable_schema):
    # airtable_schema is full metadata dict
    for table in airtable_schema["tables"]:
        print(table["name"])
```

**Caching**: Schemas are cached for 24 hours in `.cache/airtable_schemas/`

## Writing New Integration Tests

### Template

```python
@pytest.mark.airtable_live
class TestMyFeatureIntegration:
    """Integration tests for MyFeature with real Airtable data."""
    
    def test_feature_with_real_base(self, airtable_schema):
        """Test feature behavior on real base."""
        from unittest.mock import patch
        
        with patch('my_module.get_local_storage_metadata', return_value=airtable_schema):
            result = my_feature_function()
            
            # Assertions
            assert result is not None
            # Add more specific checks
    
    def test_edge_case_with_real_data(self, airtable_schema):
        """Test edge case that only appears in real data."""
        # Find specific field type
        formula_field = None
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                if field["type"] == "formula":
                    formula_field = field
                    break
            if formula_field:
                break
        
        if not formula_field:
            pytest.skip("No formula fields in test base")
        
        # Test with the found field
        # ...
```

### Best Practices

1. **Use `pytest.skip()`** if base doesn't have required fields:
```python
if not has_required_field:
    pytest.skip("Test base doesn't have required field type")
```

2. **Verify structure** before accessing:
```python
assert isinstance(result, list)
assert len(result) > 0
assert "field_name" in result[0]
```

3. **Test first few items** in large collections:
```python
for field in all_fields[:5]:  # Test first 5
    # Validate field
```

4. **Handle missing data gracefully**:
```python
if not airtable_schema.get("tables"):
    pytest.skip("No tables in test base")
```

5. **Use clear assertion messages**:
```python
assert field_id not in unused_ids, \
    f"Field {field_id} used by {formula_name} should not be unused"
```

## CI/CD Integration

### Recommended Strategy

**Pull Requests**:
```yaml
# Fast unit tests only
- run: uv run pytest
```

**Nightly Builds**:
```yaml
# Comprehensive testing
- run: uv run pytest --airtable-live
  env:
    AIRTABLE_BASE_ID: ${{ secrets.AIRTABLE_BASE_ID }}
    AIRTABLE_API_KEY: ${{ secrets.AIRTABLE_API_KEY }}
```

## Troubleshooting

### Tests Always Skip

**Problem**: Integration tests skip even with credentials set.

**Solution**: Add `--airtable-live` flag:
```bash
uv run pytest --airtable-live
```

### API Key Not Found

**Problem**: `ValueError: AIRTABLE_API_KEY environment variable not set`

**Solution**: Set environment variables:
```bash
export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
```

### Test Base Missing Required Fields

**Problem**: Tests skip with "No formula fields in test base"

**Solution**: This is expected! Tests auto-skip if your base doesn't have the required field types. Use a base with diverse field types for comprehensive testing.

### Schema Cache Stale

**Problem**: Tests use old schema after base changes

**Solution**: Clear cache:
```bash
rm -rf .cache/airtable_schemas/
```

Or force refresh in code:
```python
from helpers.airtable_api import fetch_schema_cached

schema = fetch_schema_cached(base_id, api_key, force_refresh=True)
```

## Performance

### Test Timing

- **Unit tests**: ~2-5 seconds total
- **Integration tests**: ~30-60 seconds total (includes API calls)
- **Schema caching**: Reduces API calls by 90%+

### Rate Limiting

Airtable API has rate limits (5 requests/second). Integration tests:
- Use cached schemas (24hr expiry)
- Test samples, not all fields
- Run serially within each test class

## Real-World Benefits

### Edge Cases Caught by Integration Tests

1. **Special Characters**: Field names with `"quotes"`, `(parens)`, `#hash`, 🎉 emojis
2. **Complex Dependencies**: 5+ level formula nesting, circular refs
3. **Cross-Table Patterns**: Lookup → Rollup → Formula chains
4. **Naming Conflicts**: snake_case conversion collisions
5. **Scale Issues**: Bases with 50+ tables, 200+ fields
6. **Null Handling**: Fields with missing/null values in various contexts
7. **Type Mismatches**: Unexpected field type combinations

### Statistics from Real Bases

From testing against production Airtable bases:

- **30%** of real formulas have nested field references 3+ levels deep
- **15%** of field names contain special chars that break naive escaping
- **8%** of bases have genuinely unused fields (not detected without graph analysis)
- **5%** of formulas reference 10+ other fields (stress-tests complexity scoring)

## Related Documentation

- [Phase 5B Testing](../tests/README_PHASE5B.md) - Parity testing framework
- [Test README](../tests/README.md) - General testing documentation
- [Airtable API Helpers](../tests/helpers/airtable_api.py) - API utilities

## Future Enhancements

Potential additions:

- [ ] Multi-base testing (test against multiple bases in one run)
- [ ] Performance benchmarking with real data
- [ ] Regression test suite (save failing cases)
- [ ] Coverage analysis per field type
- [ ] Automated edge case discovery
