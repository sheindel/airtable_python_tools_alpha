# Test Schemas Directory

This directory is for **external test schemas** that should not be committed to the repository.

## Purpose

When testing code generators with large, complex, or real-world Airtable schemas, you may not want to commit these files to git (they might be large, contain sensitive structure info, or be proprietary).

Place your test schema JSON files here, and they will be automatically:
- **Gitignored** - Not committed to the repository
- **Available to tests** - Can be loaded using `SchemaLoader.load(name)`
- **Used in benchmarks** - Automatically detected by performance benchmarks

## Usage

### Adding a Schema

1. Export your Airtable base schema to JSON
2. Save it here with a descriptive name:
   ```bash
   tests/schemas/my-large-base.json
   tests/schemas/production-copy.json
   tests/schemas/benchmark.json
   ```

### Using in Tests

```python
from schema_loader import SchemaLoader

# Load by name (without .json extension)
metadata = SchemaLoader.load("my-large-base")

# Or load demo schema (in repo)
metadata = SchemaLoader.load("demo")
```

### Using for Benchmarks

The performance benchmarks will automatically use `benchmark.json` from this directory if it exists:

```bash
# Uses tests/schemas/benchmark.json if present
pytest tests/test_performance_benchmarks.py -v

# Or specify via environment variable
BENCHMARK_SCHEMA=/path/to/huge-schema.json pytest tests/test_performance_benchmarks.py -v
```

### Listing Available Schemas

```python
from schema_loader import SchemaLoader

schemas = SchemaLoader.list_available_schemas()
print("Default schemas:", schemas["default"])  # ['demo', 'crm', 'issues', 'blog']
print("External schemas:", schemas["external"])  # Files in this directory
```

## File Format

Schema files should be Airtable base metadata in JSON format:

```json
{
  "id": "appXXXXXXXXXXXXXX",
  "name": "My Base",
  "tables": [
    {
      "id": "tblXXXXXXXXXXXXXX",
      "name": "Table Name",
      "fields": [
        {
          "id": "fldXXXXXXXXXXXXXX",
          "name": "Field Name",
          "type": "singleLineText",
          ...
        }
      ]
    }
  ]
}
```

## Best Practices

1. **Use descriptive names**: `enterprise-crm.json` is better than `test1.json`
2. **Document complexity**: Add a comment in test files about what makes a schema interesting
3. **Create benchmark.json**: This is the default for performance tests
4. **Don't commit**: This directory is gitignored, so schemas stay local

## Environment Variables

You can also specify schemas via environment variables:

- `SCHEMA_PATH=/path/to/schema.json` - Use this specific schema
- `BENCHMARK_SCHEMA=/path/to/schema.json` - Use this for benchmarks

These take priority over files in this directory.
