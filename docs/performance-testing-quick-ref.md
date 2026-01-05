# Performance Testing Quick Reference

## Running Benchmarks

### All Benchmarks
```bash
uv run pytest tests/test_performance_benchmarks.py -v -s
```

### Specific Test Class
```bash
# Python generator benchmarks
uv run pytest tests/test_performance_benchmarks.py::TestPythonGeneratorPerformance -v -s

# JavaScript generator benchmarks
uv run pytest tests/test_performance_benchmarks.py::TestJavaScriptGeneratorPerformance -v -s

# SQL generator benchmarks
uv run pytest tests/test_performance_benchmarks.py::TestSQLGeneratorPerformance -v -s

# Full workflow benchmarks
uv run pytest tests/test_performance_benchmarks.py::TestFullWorkflowPerformance -v -s
```

### Single Test
```bash
uv run pytest tests/test_performance_benchmarks.py::TestPythonGeneratorPerformance::test_python_library_generation_time -v -s
```

## Using External Schemas

### Via Environment Variable
```bash
# For any test
SCHEMA_PATH=/path/to/schema.json uv run pytest tests/test_*.py

# For benchmarks specifically
BENCHMARK_SCHEMA=/path/to/large-schema.json uv run pytest tests/test_performance_benchmarks.py -v -s
```

### Via tests/schemas/ Directory
```bash
# 1. Copy schema
cp ~/my-schema.json tests/schemas/my-test.json

# 2. Reference by name in tests
from schema_loader import SchemaLoader
metadata = SchemaLoader.load("my-test")

# 3. Or create benchmark.json for automatic detection
cp ~/large-base.json tests/schemas/benchmark.json
uv run pytest tests/test_performance_benchmarks.py -v -s
```

## Understanding Benchmark Output

```
============================================================
Python Library Generation Benchmark
============================================================
Schema: 7 tables, 58 fields      # Schema complexity
  - 8 formulas                    # Formula count
  - 3 lookups                     # Lookup count
  - 2 rollups                     # Rollup count
Time: 1.234s                      # Actual execution time
Threshold: 5.0s                   # Performance threshold
Generated: 45321 bytes            # Output size
============================================================
```

## Performance Thresholds

| Operation | Threshold | Notes |
|-----------|-----------|-------|
| Python Library | 5.0s | Includes formula transpilation |
| Python Types | 2.0s | Type generation only |
| TypeScript Types | 2.0s | Type generation only |
| JavaScript Library | 3.0s | Runtime generation |
| SQL Generation | 4.0s | Schema + functions |
| Full-Stack Workflow | 10.0s | All generators |

## Using SchemaLoader in Tests

```python
from schema_loader import SchemaLoader

# Load by name
metadata = SchemaLoader.load("demo")        # Default
metadata = SchemaLoader.load("crm")         # Built-in
metadata = SchemaLoader.load("my-test")     # External

# Load by path
metadata = SchemaLoader.load_from_path("/path/to/schema.json")

# List available schemas
schemas = SchemaLoader.list_available_schemas()
# Returns: {'default': ['demo', 'crm', ...], 'external': ['my-test', ...]}

# Get schema info
info = SchemaLoader.get_schema_info(metadata)
# Returns: {'id': 'app123', 'name': 'My Base', 'tables': 5, ...}
```

## Troubleshooting

### Test Fails with Timeout
```bash
# Check if schema is much larger than demo
BENCHMARK_SCHEMA=/path/to/schema.json uv run pytest tests/test_performance_benchmarks.py -v -s

# If consistently slow, consider:
# 1. Profiling the generator
# 2. Adjusting thresholds in test_performance_benchmarks.py
# 3. Optimizing bottlenecks
```

### Schema Not Found
```bash
# Check available schemas
python -c "from tests.schema_loader import SchemaLoader; print(SchemaLoader.list_available_schemas())"

# Verify file exists
ls tests/schemas/

# Check environment variable
echo $SCHEMA_PATH
echo $BENCHMARK_SCHEMA
```

### Benchmark Shows Warnings
```bash
# Run with full traceback
uv run pytest tests/test_performance_benchmarks.py -v -s --tb=long

# Check for import errors
uv run python -c "from tests.test_performance_benchmarks import *"
```

## CI Integration (Future)

```yaml
# .github/workflows/test.yml
- name: Run performance benchmarks
  run: |
    uv run pytest tests/test_performance_benchmarks.py -v
  timeout-minutes: 5
```

## Profiling (Advanced)

```bash
# Profile a specific generator
python -m cProfile -o profile.out -c "
from web.code_generators.python_runtime_generator import generate_python_library
from tests.schema_loader import load_demo_schema
metadata = load_demo_schema()
generate_python_library(metadata, {})
"

# Analyze profile
python -m pstats profile.out
# In pstats shell:
# sort cumulative
# stats 20
```
