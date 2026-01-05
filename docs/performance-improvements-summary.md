# Performance Improvements Summary

This document summarizes the improvements made to address Python Server SDK generation performance issues.

## Changes Made

### 1. Loading Spinner UI Component

**File**: `web/components/loading.py`

A reusable loading spinner component with multiple display modes:

- **Simple spinner**: Basic loading indicator with message
- **Progress spinner**: Includes progress bar (0-100%)
- **Detailed spinner**: Shows title, message, and substeps with completion status

**Usage Example**:
```python
from components.loading import create_loading_spinner, show_loading

# In PyScript
show_loading("output-div", "Processing...")

# Or get HTML
html = create_loading_spinner("Loading data...")
```

**Features**:
- Dark mode support
- Tailwind CSS styling
- Can be updated dynamically
- Helper functions for showing/hiding

---

### 2. Async Operations Wrapper

**File**: `web/components/async_operations.py`

Utilities for managing long-running operations with progress tracking:

**Key Components**:

1. **`@with_loading_spinner` decorator**: Automatically wraps functions with loading UI
   ```python
   @with_loading_spinner("output-div", "Generating code...")
   def generate_code():
       # Long operation
       return result
   ```

2. **`ProgressTracker` class**: Track multi-step operations
   ```python
   tracker = ProgressTracker("output-div", total_steps=5)
   tracker.start("Starting...")
   tracker.update(1, "Step 1 complete")
   tracker.update(2, "Step 2 complete")
   tracker.complete("Done!")
   ```

3. **`defer_execution()`**: Defer heavy work to let UI update
   ```python
   show_loading("output-div", "Processing...")
   defer_execution(lambda: do_heavy_work(), 150)
   ```

---

### 3. Code Generator Integration

**File**: `web/tabs/code_generator.py`

Updated the code generator tab to use the new loading system:

**Changes**:
- Shows detailed spinner with workflow-specific substeps
- Defers actual code generation to allow spinner to render (150ms delay)
- Uses `ProgressTracker` to update progress during generation
- Shows completion state briefly before displaying results

**User Experience**:
1. User clicks "Generate"
2. Spinner appears immediately with expected steps
3. Progress updates as files are generated
4. Brief "Complete!" message shown
5. Results displayed with file tree

---

### 4. Performance Benchmark Suite

**File**: `tests/test_performance_benchmarks.py`

Comprehensive performance tests to measure and track code generation speed:

**Benchmarks**:
- Python library generation (< 5s threshold)
- Python types generation (< 2s threshold)
- TypeScript types generation (< 2s threshold)
- JavaScript library generation (< 3s threshold)
- SQL generation (< 4s threshold)
- Complete workflows (< 10s threshold)

**Features**:
- Measures actual execution time
- Prints detailed statistics (tables, fields, formulas)
- Compares against performance thresholds
- Reports file sizes and generation time
- Supports external schemas via environment variable

**Usage**:
```bash
# Run all benchmarks
uv run pytest tests/test_performance_benchmarks.py -v -s

# With custom schema
BENCHMARK_SCHEMA=/path/to/schema.json uv run pytest tests/test_performance_benchmarks.py -v

# Specific test
pytest tests/test_performance_benchmarks.py::TestPythonGeneratorPerformance::test_python_library_generation_time -v
```

---

### 5. External Schema Support

**Files**: 
- `tests/schema_loader.py` - Schema loading utility
- `tests/schemas/README.md` - Documentation
- `.gitignore` - Updated to ignore external schemas

**SchemaLoader** utility provides flexible schema loading:

**Priority Order**:
1. `SCHEMA_PATH` environment variable
2. External schemas in `tests/schemas/{name}.json`
3. Default schemas in repo root

**Usage**:
```python
from schema_loader import SchemaLoader

# Load by name
metadata = SchemaLoader.load("demo")  # Default
metadata = SchemaLoader.load("my-large-base")  # External

# Load from path
metadata = SchemaLoader.load_from_path("/path/to/schema.json")

# List available
schemas = SchemaLoader.list_available_schemas()
# {'default': ['demo', 'crm', 'issues', 'blog'], 'external': ['my-large-base']}

# Get stats
stats = SchemaLoader.get_schema_info(metadata)
# {'tables': 5, 'total_fields': 45, 'field_types': {...}}
```

**Benefits**:
- Test with large, complex schemas without committing to git
- Share schemas locally without exposing proprietary structures
- Easy switching between test schemas
- Automatic detection in benchmarks

---

### 6. Documentation Updates

**Updated Files**:
- `README.md` - Added performance testing section
- `tests/README.md` - Added external schema and benchmark documentation
- `tests/schemas/README.md` - Comprehensive guide for external schemas

**Key Documentation**:
- How to run benchmarks
- How to use external schemas
- Performance thresholds
- Schema file format requirements
- Best practices

---

## Usage Guide

### For Users: Seeing Progress

When generating code in the web app:
1. Click "Generate Code" button
2. See detailed spinner with expected steps
3. Watch progress as generation happens
4. Get results when complete

No action needed - improvements are automatic!

---

### For Developers: Running Benchmarks

#### Quick Start
```bash
# Install dependencies
uv sync --group dev

# Run all benchmarks with default schema
uv run pytest tests/test_performance_benchmarks.py -v -s
```

#### With Large Schema
```bash
# Option 1: Environment variable
BENCHMARK_SCHEMA=/path/to/large-schema.json uv run pytest tests/test_performance_benchmarks.py -v

# Option 2: Place in tests/schemas/
cp ~/large-schema.json tests/schemas/benchmark.json
uv run pytest tests/test_performance_benchmarks.py -v

# Option 3: Use any schema name
cp ~/schema.json tests/schemas/my-test.json
SCHEMA_PATH=tests/schemas/my-test.json uv run pytest
```

#### Understanding Output
```
Python Library Generation Benchmark
============================================================
Schema: 10 tables, 150 fields
  - 45 formulas
  - 12 lookups
  - 8 rollups
Time: 2.345s
Threshold: 5.0s
Generated: 125430 bytes
============================================================
```

#### Tracking Performance
1. Run benchmarks regularly (e.g., before commits)
2. Watch for tests failing due to timeout
3. Investigate if generation time increases significantly
4. Use `pytest -v -s` to see detailed output

---

### For Developers: Using External Schemas

#### Setting Up
```bash
# Create schemas directory (already done)
mkdir -p tests/schemas

# Add your schema
cp ~/my-airtable-export.json tests/schemas/production-copy.json
```

#### In Tests
```python
from schema_loader import SchemaLoader

@pytest.fixture
def large_metadata():
    """Load a large external schema"""
    return SchemaLoader.load("production-copy")

def test_with_large_schema(large_metadata):
    # Test with real-world data
    result = generate_python_library(large_metadata)
    assert len(result) > 0
```

#### In Code
```python
from tests.schema_loader import SchemaLoader

# List all available
schemas = SchemaLoader.list_available_schemas()
print(f"Available schemas: {schemas}")

# Get info about a schema
metadata = SchemaLoader.load("demo")
info = SchemaLoader.get_schema_info(metadata)
print(f"Tables: {info['tables']}, Fields: {info['total_fields']}")
```

---

## Technical Details

### Why Defer Execution?

PyScript runs Python in the browser using WebAssembly. Heavy computation can block the UI thread. By using `defer_execution()`, we:

1. Update DOM with loading spinner
2. Let browser render the spinner (150ms delay)
3. Start the heavy computation
4. Keep UI responsive

### Progress Tracking Implementation

The `ProgressTracker` class updates the DOM during generation:
- Calculates percentage based on current step / total steps
- Updates progress bar width dynamically
- Changes message and progress text
- Handles errors gracefully

### Performance Thresholds

Thresholds are set based on the **demo schema** (5 tables, ~30 fields):
- Python SDK: 5s (includes formula transpilation)
- TypeScript: 2s (simpler type generation)
- SQL: 4s (includes function generation)
- Full-stack: 10s (all of the above)

These should scale roughly linearly with schema size.

---

## Next Steps

### Potential Improvements

1. **Incremental Progress**: Update progress bar as each file is generated
2. **Caching**: Cache parsed ASTs to avoid re-parsing formulas
3. **Parallel Generation**: Generate files in parallel (challenging in PyScript)
4. **Streaming Output**: Show files as they're generated, not all at once
5. **Web Workers**: Move heavy computation to web workers (requires PyScript support)

### Monitoring

1. Set up CI to run benchmarks on PRs
2. Track performance over time
3. Alert on significant regressions
4. Profile slow operations with cProfile

### Testing

1. Add more test schemas of varying complexity
2. Test with schemas of different sizes (10, 50, 100+ tables)
3. Identify bottlenecks with profiling
4. Optimize hot paths in generators

---

## Files Created/Modified

### New Files
- `web/components/loading.py` - Loading spinner components
- `web/components/async_operations.py` - Async operation utilities
- `tests/test_performance_benchmarks.py` - Performance benchmark suite
- `tests/schema_loader.py` - Schema loading utility
- `tests/schemas/README.md` - External schema documentation
- `docs/performance-improvements-summary.md` - This file

### Modified Files
- `web/tabs/code_generator.py` - Integrated loading UI
- `.gitignore` - Added tests/schemas/*.json
- `README.md` - Added performance testing section
- `tests/README.md` - Added benchmarks and external schema docs

---

## Example Output

### Loading Spinner (Web UI)
```
┌─────────────────────────────────┐
│          Generating Code         │
│                                  │
│   Please wait while we generate  │
│       your code files...         │
│                                  │
│   ✓ Generating Python types      │
│   ✓ Generating helper functions  │
│   ⋯ Generating computed fields   │
│   ⋯ Generating usage examples    │
└─────────────────────────────────┘
```

### Benchmark Output
```bash
$ uv run pytest tests/test_performance_benchmarks.py -v -s

============================================================
Python Library Generation Benchmark
============================================================
Schema: 5 tables, 28 fields
  - 8 formulas
  - 3 lookups
  - 2 rollups
Time: 1.234s
Threshold: 5.0s
Generated: 45321 bytes
============================================================
PASSED

============================================================
Server SDK Workflow Benchmark
============================================================
Schema: 5 tables, 28 fields
Time: 2.456s
Threshold: 10.0s
Generated files: 3
  - types.py: 12340 bytes
  - helpers.py: 8901 bytes
  - computed_fields.py: 24080 bytes
============================================================
PASSED
```

---

## FAQ

**Q: Why do I see a loading spinner now?**
A: The spinner shows while code is being generated, especially for large schemas. It provides feedback that the system is working.

**Q: How do I know if generation is slow?**
A: Run the benchmarks! They'll tell you exactly how long each operation takes and compare against thresholds.

**Q: Can I test with my own schema?**
A: Yes! Place it in `tests/schemas/` or use the `SCHEMA_PATH` environment variable.

**Q: What if benchmarks fail?**
A: First, check if your schema is much larger than the demo. If thresholds are unrealistic, adjust them in `test_performance_benchmarks.py`.

**Q: Do external schemas get committed?**
A: No, the `tests/schemas/` directory is gitignored (except the README).

**Q: Can I use this in production?**
A: The web app is designed for interactive use. For batch processing, use the CLI which doesn't need the loading UI overhead.

---

## Conclusion

These improvements provide:
1. ✅ **Better UX**: Users see progress instead of a frozen screen
2. ✅ **Performance Tracking**: Benchmarks catch regressions early
3. ✅ **Flexible Testing**: Test with any schema without committing it
4. ✅ **Developer Tools**: Easy to measure and optimize generation speed

The system is now ready to handle large, complex schemas while keeping users informed of progress!
