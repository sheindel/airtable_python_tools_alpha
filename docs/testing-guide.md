# Regression Testing Suite - Quick Start Guide

This directory contains a comprehensive regression testing suite designed to be executed by AI agents. The test suite covers unit tests, CLI commands, and web application functionality.

## 📋 Overview

The regression test suite consists of three main components:

1. **Automated Python Tests** - Unit tests and CLI command tests that run automatically
2. **Web Application Tests** - Interactive tests using Chrome DevTools MCP
3. **Test Reports** - Markdown reports summarizing results

## 🚀 Quick Start

### Option 1: Run Automated Tests Only (Fastest)

```bash
# Run all automated tests (unit + CLI)
uv run python run_regression_tests.py

# Run specific phase
uv run python run_regression_tests.py --phase 1  # Unit tests only
uv run python run_regression_tests.py --phase 2  # CLI tests only

# Custom report file
uv run python run_regression_tests.py --output my_report.md
```

**Output**: `test_report.md` (or custom filename)

### Option 2: Full Test Suite (Includes Web App)

For complete testing including the web application:

1. **Start the web server**:
   ```bash
   uv run python main.py run-web
   ```
   Server runs at `http://localhost:8008`

2. **In a separate terminal, run automated tests**:
   ```bash
   uv run python run_regression_tests.py
   ```

3. **Execute web tests using Chrome MCP** (see [web-testing-guide.md](web-testing-guide.md)):
   - Activate Chrome MCP tools
   - Follow step-by-step test procedures
   - Capture screenshots and verify functionality

## 📚 Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| [ai-testing-guide.md](ai-testing-guide.md) | Complete test specification | Reference for understanding all test scenarios |
| [web-testing-guide.md](web-testing-guide.md) | Web app test procedures | When testing web UI with Chrome MCP |
| `run_regression_tests.py` | Automated test runner | Run CLI and unit tests automatically |
| `web_regression_tests.py` | Web test definitions | Generate web test guide |

## 🎯 Test Phases Explained

### Phase 1: Environment Setup & Unit Tests
- ✅ Verify dependencies installed
- ✅ Build Tailwind CSS assets
- ✅ Run pytest suite
- ✅ Generate coverage report

**Duration**: ~30-60 seconds

### Phase 2: CLI Command Tests
- ✅ Test all CLI commands with `--help`
- ✅ Test formula evaluation
- ✅ Test schema generation (if demo data available)
- ✅ Verify commands return expected output

**Duration**: ~30-45 seconds

### Phase 3: Web Application Tests
- ✅ Homepage load and initialization
- ✅ Load sample data
- ✅ Test each tab's core functionality
- ✅ Verify Mermaid graph generation
- ✅ Test dark mode toggle
- ✅ Check for console errors

**Duration**: ~5-10 minutes (manual with Chrome MCP)

### Phase 4: Integration Tests
- ✅ Verify module imports work
- ✅ Validate configuration files
- ✅ Check built assets exist

**Duration**: ~10 seconds

## 📊 Test Report

After running tests, you'll get a markdown report with:

- **Summary**: Total tests, pass/fail counts, duration
- **Environment**: OS, Python, Node versions
- **Phase Results**: Detailed results for each phase
- **Critical Issues**: Failed tests requiring attention
- **Recommendations**: Next steps based on results

Example summary:
```
Total Tests:  25
Passed:       23 ✅
Failed:       0 ❌
Skipped:      2 ⏭️
Errors:       0 🔥
Duration:     87.3s
```

## 🤖 For AI Agents

### Executing Automated Tests

```python
# Simple execution
import subprocess
result = subprocess.run(
    ["uv", "run", "python", "run_regression_tests.py"],
    capture_output=True,
    text=True
)

# Check result
if result.returncode == 0:
    print("✅ All tests passed!")
else:
    print("❌ Some tests failed")
    print(result.stdout)
```

### Executing Web Tests

1. **Start web server** (background process)
2. **Activate Chrome MCP** tools category
3. **Follow** [web-testing-guide.md](web-testing-guide.md) step-by-step
4. **Capture** screenshots at each major step
5. **Report** results with pass/fail for each test

## 🔍 Test Coverage

### Unit Tests
- ✅ Graph operations (`test_at_metadata_graph.py`)
- ✅ Constants validation (`test_constants.py`)
- ✅ Core business logic (various modules)

**Target Coverage**: 70%+ overall, 90%+ for core modules

### CLI Tests
- ✅ All 16 CLI commands
- ✅ Help text generation
- ✅ Formula evaluation
- ✅ Schema generation
- ✅ Complexity analysis

### Web Tests
- ✅ All 10+ tabs/features
- ✅ API credential handling
- ✅ Sample data loading
- ✅ Graph generation
- ✅ Dark mode
- ✅ Error handling

## 🛠️ Prerequisites

Before running tests, ensure:

```bash
# Python dependencies
uv sync --group dev

# Node dependencies (for CSS build)
npm install

# Build assets
npm run build:css
```

## 🐛 Troubleshooting

### Tests fail with "web/output.css not found"
```bash
npm run build:css
```

### Unit tests fail with import errors
```bash
uv sync --group dev
```

### CLI tests fail with "demo_base_schema.json not found"
This is expected if the demo file doesn't exist. CLI tests that require it will be skipped.

### Web tests fail to connect
1. Ensure web server is running: `uv run python main.py run-web`
2. Verify Chrome MCP is activated
3. Check browser can access `http://localhost:8008`

### PyScript not loading in web tests
- Wait at least 5-10 seconds after page load
- Check browser console for "PyScript is ready" message
- Verify internet connection (PyScript CDN loads external resources)

## 📈 CI/CD Integration

The automated test runner (`run_regression_tests.py`) is designed for CI/CD:

```yaml
# Example GitHub Actions
- name: Run regression tests
  run: |
    uv sync --group dev
    npm install
    npm run build:css
    uv run python run_regression_tests.py
```

Exit codes:
- `0`: All tests passed
- `1`: Some tests failed or errored

## 🎓 Best Practices

1. **Run tests before committing**: Catch regressions early
2. **Check coverage reports**: Aim for >70% coverage
3. **Review test reports**: Understand what failed and why
4. **Update tests when adding features**: Keep tests in sync
5. **Use --phase flag for quick checks**: Fast iteration during development

## 📝 Adding New Tests

### Adding a Unit Test
1. Create test file in `tests/` directory
2. Follow pytest conventions
3. Tests auto-discovered and run

### Adding a CLI Test
1. Edit `run_regression_tests.py`
2. Add test to `phase_2_cli_tests()` method
3. Use `run_test()` helper for consistency

### Adding a Web Test
1. Edit `web_regression_tests.py`
2. Add new test method to `WebTestSuite` class
3. Re-generate guide: `uv run python web_regression_tests.py`

## 🔗 Related Documentation

- [Project Architecture](.github/copilot-instructions.md)
- [Testing Reorganization](TESTING_REORGANIZATION.md)
- [pytest Configuration](pytest.ini)

## 📞 Support

If tests fail unexpectedly:
1. Check test report for specific failures
2. Review console output for error messages
3. Verify all prerequisites are met
4. Ensure sample data files exist (for relevant tests)

---

**Last Updated**: 2026-01-10
**Test Suite Version**: 1.0
**Maintained By**: Project maintainers
