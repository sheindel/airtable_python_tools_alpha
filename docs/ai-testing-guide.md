# AI-Executable Regression Test Suite

This document contains a comprehensive regression test suite designed to be executed by an AI agent. The tests cover unit tests, CLI commands, and web application functionality.

## Test Execution Overview

This test suite is designed to be executed sequentially by an AI agent. Each section should be completed before moving to the next. The AI should report success/failure for each test and capture any errors encountered.

---

## Phase 1: Environment Setup and Unit Tests

### 1.1 Environment Verification
```bash
# Verify Python version and dependencies
uv --version
python --version
node --version
npm --version

# Verify project dependencies are installed
uv sync --group dev
npm install
```

**Expected**: All commands succeed without errors.

### 1.2 Build CSS Assets
```bash
# Build Tailwind CSS (required for web app)
npm run build:css
```

**Expected**: `web/output.css` file is created successfully.

### 1.3 Run Unit Tests
```bash
# Run all unit tests with coverage
uv run pytest --cov=web --cov-report=term-missing

# Run specific test files to verify core functionality
uv run pytest tests/test_at_metadata_graph.py -v
uv run pytest tests/test_constants.py -v
```

**Expected**: 
- All tests pass
- Coverage report shows reasonable coverage (>70% for core modules)
- No import errors or dependency issues

**Report**: Total tests passed/failed, coverage percentage, any failing tests.

---

## Phase 2: CLI Command Testing

For CLI tests, use the demo schema file at `demo_base_schema.json` to avoid requiring real Airtable API credentials.

### 2.1 Test: get-airtable-metadata (Mock Test)
```bash
# This requires real API credentials, so we'll verify the command exists
uv run python main.py get-airtable-metadata --help
```

**Expected**: Help text displays without errors.

### 2.2 Test: generate-mermaid-graph
```bash
# Generate a mermaid graph for a specific field
uv run python main.py generate-mermaid-graph \
  --table-name "Projects" \
  --field-name "Status" \
  --v2 \
  --direction "TD"
```

**Expected**: 
- Command executes without errors
- Mermaid diagram text is output to console
- Output includes "flowchart TD" and field/table nodes

**Report**: Capture output and verify it contains valid Mermaid syntax.

### 2.3 Test: get-table-complexity
```bash
# Generate complexity analysis for a table
uv run python main.py get-table-complexity "Projects"
```

**Expected**:
- CSV file created with name `Projects_field_complexity.csv`
- CSV contains headers and field complexity data
- No Python errors

**Report**: Verify CSV file exists and has content.

### 2.4 Test: generate-table-dependency-graph
```bash
# Generate table-level dependency graph
uv run python main.py generate-table-dependency-graph "Projects" --flowchart-type "TD"
```

**Expected**:
- Mermaid flowchart output showing table relationships
- Output includes table nodes and relationship edges

**Report**: Capture output and verify Mermaid syntax.

### 2.5 Test: compress-formula
```bash
# Test formula compression with a demo formula
uv run python main.py compress-formula \
  --table-name "Projects" \
  --field-name "Computed Status" \
  --compression-depth 2 \
  --output-format "field_names" \
  --display-format "compact"
```

**Expected**:
- Compressed formula output
- Shows compression depth
- No errors

**Report**: Note if compression worked or if field doesn't exist (acceptable).

### 2.6 Test: find-unused-fields
```bash
# Find unused fields
uv run python main.py find-unused-fields --output-file unused_fields_test.csv
```

**Expected**:
- CSV file created
- List of unused fields displayed
- No errors

**Report**: Count of unused fields found.

### 2.7 Test: complexity-scorecard
```bash
# Generate complexity scorecard
uv run python main.py complexity-scorecard --top-n 10 --output-file complexity_test.csv
```

**Expected**:
- CSV file created
- Top 10 most complex fields displayed
- Complexity scores calculated

**Report**: Verify output format and data.

### 2.8 Test: eval-formula
```bash
# Evaluate a simple formula
uv run python main.py eval-formula -f "IF(TRUE, 'yes', 'no')"

# Evaluate with field substitution
uv run python main.py eval-formula \
  -f "{fldABC123xyz45678} + {fldDEF456abc12345}" \
  -v '{"fldABC123xyz45678": "10", "fldDEF456abc12345": "20"}'
```

**Expected**:
- First command returns "yes"
- Second command returns 30
- No evaluation errors

**Report**: Actual results for both formulas.

### 2.9 Test: generate-postgres-schema
```bash
# Generate PostgreSQL schema
uv run python main.py generate-postgres-schema \
  -s demo_base_schema.json \
  -o test_schema.sql \
  -n field_names \
  -t data
```

**Expected**:
- SQL file created at `test_schema.sql`
- Contains CREATE TABLE statements
- Valid PostgreSQL syntax

**Report**: Verify file exists and contains SQL.

### 2.10 Test: generate-evaluator
```bash
# Generate Python evaluator (requires table ID from schema)
# First, let's extract a table ID from demo schema
# This test may require manual inspection of the schema file

# Example (will need to substitute actual table ID):
# uv run python main.py generate-evaluator \
#   -s demo_base_schema.json \
#   -o test_evaluator.py \
#   -t tblXXXXXXXXXXXXXX \
#   -m dataclass
```

**Expected**: 
- Python file generated
- Contains evaluator functions
- No syntax errors

**Report**: Verify file generation or skip if table ID not available.

---

## Phase 3: Web Application Testing

### 3.1 Start Web Server
```bash
# Start the web server in background
uv run python main.py run-web &
# Store the PID to kill later if needed
WEB_SERVER_PID=$!
```

**Expected**: Server starts on `http://localhost:8008`

### 3.2 Activate Chrome MCP and Navigate
Use the Chrome DevTools MCP to interact with the web application.

```javascript
// Navigate to the app
navigate_page('http://localhost:8008')

// Wait for page load
evaluate_script(() => {
  return {
    loaded: document.readyState === 'complete',
    pyScriptReady: typeof window.pyscript !== 'undefined'
  }
})
```

**Expected**: Page loads successfully, PyScript initializes.

### 3.3 Test: Homepage Load
```javascript
// Take screenshot of homepage
take_screenshot()

// Verify key elements exist
evaluate_script(() => {
  return {
    hasHeader: !!document.querySelector('h1'),
    hasApiInput: !!document.querySelector('#base-id'),
    hasPATInput: !!document.querySelector('#pat'),
    hasTabButtons: document.querySelectorAll('.tab-button').length > 0,
    version: document.querySelector('#app-version')?.textContent
  }
})
```

**Expected**:
- All elements exist
- Version displayed
- UI is visible and styled

**Report**: Screenshot and element verification results.

### 3.4 Test: Enter Sample API Credentials
```javascript
// Click "Use Sample" button to load demo data
click('#use-sample')

// Wait for metadata to load
wait_for('Sample metadata loaded')

// Verify metadata is stored
evaluate_script(() => {
  const metadata = localStorage.getItem('airtable_metadata');
  return {
    hasMetadata: !!metadata,
    metadataSize: metadata ? metadata.length : 0,
    baseId: localStorage.getItem('base_id'),
    tables: metadata ? JSON.parse(metadata).tables?.length : 0
  }
})
```

**Expected**:
- Sample data loads successfully
- localStorage contains metadata
- Multiple tables available

**Report**: Number of tables loaded, metadata size.

### 3.5 Test: Dependency Mapper Tab
```javascript
// Switch to Dependency Mapper tab
evaluate_script(() => {
  document.querySelector('[data-tab="dependency-mapper"]')?.click();
  return { switched: true }
})

// Wait for tab to activate
wait_for('Field Dependency Mapper')

// Check dropdown population
evaluate_script(() => {
  const tableSelect = document.querySelector('#table-select');
  const fieldSelect = document.querySelector('#field-select');
  return {
    tableCount: tableSelect?.options.length || 0,
    fieldCount: fieldSelect?.options.length || 0,
    hasDropdowns: !!(tableSelect && fieldSelect)
  }
})

// Select first table and first field, generate
evaluate_script(() => {
  const tableSelect = document.querySelector('#table-select');
  const fieldSelect = document.querySelector('#field-select');
  
  if (tableSelect && tableSelect.options.length > 1) {
    tableSelect.selectedIndex = 1; // Skip "Select a table"
    tableSelect.dispatchEvent(new Event('change'));
  }
  
  // Wait a moment for field dropdown to populate
  setTimeout(() => {
    if (fieldSelect && fieldSelect.options.length > 1) {
      fieldSelect.selectedIndex = 1;
    }
  }, 500);
  
  return { ready: true }
})

// Click generate button
click('#generate-dependency-tree')

// Wait for output
wait_for('Mermaid')

// Verify output exists
evaluate_script(() => {
  const output = document.querySelector('#dependency-output');
  return {
    hasOutput: !!output?.querySelector('.mermaid'),
    mermaidContent: output?.querySelector('.mermaid')?.textContent?.substring(0, 100),
    hasCopyButton: !!output?.querySelector('button')
  }
})

// Take screenshot of result
take_screenshot()
```

**Expected**:
- Tab switches successfully
- Dropdowns populate with data
- Graph generates and displays
- Mermaid diagram visible

**Report**: Screenshot and verification results.

### 3.6 Test: Dependency Analysis Tab
```javascript
// Switch to Dependency Analysis tab
evaluate_script(() => {
  document.querySelector('[data-tab="dependency-analysis"]')?.click();
  return { switched: true }
})

// Wait for tab
wait_for('Table Complexity Analysis')

// Select a table
evaluate_script(() => {
  const select = document.querySelector('#analysis-table-select');
  if (select && select.options.length > 1) {
    select.selectedIndex = 1;
  }
  return { ready: true }
})

// Click analyze button
click('#analyze-table')

// Wait for results
wait_for('CSV')

// Verify output
evaluate_script(() => {
  const output = document.querySelector('#analysis-output');
  return {
    hasCSV: output?.textContent.includes('Field Name'),
    hasCopyButton: !!output?.querySelector('button'),
    outputLength: output?.textContent?.length || 0
  }
})

// Take screenshot
take_screenshot()
```

**Expected**:
- Analysis generates successfully
- CSV output displayed
- Contains field complexity data

**Report**: Screenshot and output verification.

### 3.7 Test: Formula Grapher Tab
```javascript
// Switch to Formula Grapher tab
evaluate_script(() => {
  document.querySelector('[data-tab="formula-grapher"]')?.click();
  return { switched: true }
})

wait_for('Formula Logic Grapher')

// This tab may require selecting a formula field
// For now, just verify it loads
evaluate_script(() => {
  return {
    hasInputs: !!document.querySelector('#formula-table-select'),
    tabVisible: document.querySelector('#formula-grapher-tab')?.classList.contains('active')
  }
})

take_screenshot()
```

**Expected**: Tab loads without errors.

**Report**: Screenshot of tab.

### 3.8 Test: Formula Compressor Tab
```javascript
// Switch to Formula Compressor tab
evaluate_script(() => {
  document.querySelector('[data-tab="formula-compressor"]')?.click();
  return { switched: true }
})

wait_for('Formula Compressor')

// Select table and field
evaluate_script(() => {
  const tableSelect = document.querySelector('#compress-table-select');
  if (tableSelect && tableSelect.options.length > 1) {
    tableSelect.selectedIndex = 1;
    tableSelect.dispatchEvent(new Event('change'));
  }
  return { ready: true }
})

// Try to compress (may not have formula fields)
evaluate_script(() => {
  const fieldSelect = document.querySelector('#compress-field-select');
  if (fieldSelect && fieldSelect.options.length > 1) {
    fieldSelect.selectedIndex = 1;
    document.querySelector('#compress-formula')?.click();
  }
  return { attempted: true }
})

take_screenshot()
```

**Expected**: Tab loads and UI is functional.

**Report**: Screenshot.

### 3.9 Test: Complexity Scorecard Tab
```javascript
// Switch to Complexity Scorecard tab
evaluate_script(() => {
  document.querySelector('[data-tab="complexity-scorecard"]')?.click();
  return { switched: true }
})

wait_for('Complexity Scorecard')

// Click generate scorecard
click('#generate-scorecard')

// Wait for results
wait_for('Complexity Score')

// Verify output
evaluate_script(() => {
  const output = document.querySelector('#scorecard-output');
  return {
    hasResults: output?.textContent?.includes('Complexity Score'),
    tableVisible: !!output?.querySelector('table'),
    rowCount: output?.querySelectorAll('tr').length || 0
  }
})

take_screenshot()
```

**Expected**:
- Scorecard generates
- Table displays with complexity data
- No errors

**Report**: Screenshot and row count.

### 3.10 Test: Unused Fields Tab
```javascript
// Switch to Unused Fields tab
evaluate_script(() => {
  document.querySelector('[data-tab="unused-fields"]')?.click();
  return { switched: true }
})

wait_for('Unused Fields')

// Click find unused fields
click('#find-unused')

// Wait for results
wait_for('unused fields found')

// Verify output
evaluate_script(() => {
  const output = document.querySelector('#unused-output');
  return {
    hasResults: !!output?.textContent,
    hasTable: !!output?.querySelector('table'),
    message: output?.textContent?.substring(0, 100)
  }
})

take_screenshot()
```

**Expected**: Unused fields analysis completes.

**Report**: Screenshot and results summary.

### 3.11 Test: Formula Evaluator Tab
```javascript
// Switch to Formula Evaluator tab
evaluate_script(() => {
  document.querySelector('[data-tab="formula-evaluator"]')?.click();
  return { switched: true }
})

wait_for('Formula Evaluator')

// Enter a simple formula
fill('#eval-formula-input', 'IF(TRUE, "yes", "no")')

// Click evaluate
click('#eval-formula-btn')

// Wait for result
wait_for('Result')

// Verify output
evaluate_script(() => {
  const output = document.querySelector('#eval-output');
  return {
    hasResult: !!output?.textContent,
    result: output?.textContent?.substring(0, 50)
  }
})

take_screenshot()
```

**Expected**: Formula evaluates to "yes".

**Report**: Screenshot and result.

### 3.12 Test: Postgres Schema Generator Tab
```javascript
// Switch to Postgres Schema tab
evaluate_script(() => {
  document.querySelector('[data-tab="postgres-schema"]')?.click();
  return { switched: true }
})

wait_for('PostgreSQL Schema Generator')

// Click generate
click('#generate-postgres')

// Wait for output
wait_for('CREATE TABLE')

// Verify output
evaluate_script(() => {
  const output = document.querySelector('#postgres-output');
  return {
    hasSQL: output?.textContent?.includes('CREATE TABLE'),
    hasCopyButton: !!output?.querySelector('button'),
    sqlLength: output?.textContent?.length || 0
  }
})

take_screenshot()
```

**Expected**: PostgreSQL schema generated successfully.

**Report**: Screenshot and SQL verification.

### 3.13 Test: Code Generator Tab
```javascript
// Switch to Code Generator tab
evaluate_script(() => {
  document.querySelector('[data-tab="code-generator"]')?.click();
  return { switched: true }
})

wait_for('Code Generator')

take_screenshot()
```

**Expected**: Tab loads.

**Report**: Screenshot.

### 3.14 Test: Evaluator Generator Tab
```javascript
// Switch to Evaluator Generator tab
evaluate_script(() => {
  document.querySelector('[data-tab="evaluator-generator"]')?.click();
  return { switched: true }
})

wait_for('Evaluator Generator')

// Select first table
evaluate_script(() => {
  const select = document.querySelector('#eval-table-select');
  if (select && select.options.length > 1) {
    select.selectedIndex = 1;
  }
  return { ready: true }
})

// Click generate
click('#generate-evaluator')

// Wait for output
wait_for('def ')

// Verify code generated
evaluate_script(() => {
  const output = document.querySelector('#evaluator-output');
  return {
    hasCode: output?.textContent?.includes('def '),
    codeLength: output?.textContent?.length || 0
  }
})

take_screenshot()
```

**Expected**: Python evaluator code generated.

**Report**: Screenshot and code verification.

### 3.15 Test: Types Generator Tab
```javascript
// Switch to Types Generator tab (if exists)
evaluate_script(() => {
  const tab = document.querySelector('[data-tab="types-generator"]');
  if (tab) {
    tab.click();
    return { switched: true, exists: true }
  }
  return { switched: false, exists: false }
})

take_screenshot()
```

**Expected**: Tab loads if it exists.

**Report**: Screenshot or note if tab doesn't exist.

### 3.16 Test: Dark Mode Toggle
```javascript
// Toggle dark mode
evaluate_script(() => {
  const toggle = document.querySelector('theme-toggle');
  if (toggle) {
    toggle.click();
  }
  return {
    isDark: document.documentElement.classList.contains('dark')
  }
})

// Take screenshot in dark mode
take_screenshot()

// Toggle back
evaluate_script(() => {
  const toggle = document.querySelector('theme-toggle');
  if (toggle) {
    toggle.click();
  }
  return {
    isDark: document.documentElement.classList.contains('dark')
  }
})
```

**Expected**: Dark mode toggles successfully.

**Report**: Screenshots of both modes.

### 3.17 Test: Console Errors
```javascript
// Check for any console errors during testing
list_console_messages(types=['error', 'warn'])
```

**Expected**: No critical errors (warnings acceptable).

**Report**: List any errors found.

### 3.18 Cleanup Web Server
```bash
# Kill the web server
kill $WEB_SERVER_PID
```

---

## Phase 4: Integration and Smoke Tests

### 4.1 Verify Generated Files
```bash
# Check that all generated test files exist
ls -la test_schema.sql
ls -la complexity_test.csv
ls -la unused_fields_test.csv

# Verify file sizes (should not be empty)
wc -l test_schema.sql
wc -l complexity_test.csv
wc -l unused_fields_test.csv
```

**Expected**: All files exist and contain data.

### 4.2 Verify No Regressions in Package
```bash
# Verify pyproject.toml is valid
uv run python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"

# Verify web modules can be imported
uv run python -c "import sys; sys.path.append('web'); from at_metadata_graph import metadata_to_graph"

# Verify CLI is accessible
uv run python main.py --help
```

**Expected**: All checks pass without errors.

---

## Test Report Template

After completing all tests, generate a report with this structure:

```markdown
# Regression Test Report
Date: [YYYY-MM-DD]
Environment: [OS, Python version, Node version]

## Summary
- Total Tests: [X]
- Passed: [X]
- Failed: [X]
- Skipped: [X]
- Duration: [XX minutes]

## Phase 1: Unit Tests
- Status: PASS/FAIL
- Coverage: [XX%]
- Notes: [Any issues]

## Phase 2: CLI Commands
- Total Commands Tested: [X]
- Passed: [X]
- Failed: [X]
- Failed Commands: [List]
- Notes: [Any issues]

## Phase 3: Web Application
- Total Tabs Tested: [X]
- Passed: [X]
- Failed: [X]
- Failed Tabs: [List]
- Console Errors: [Count]
- Notes: [Any issues]

## Phase 4: Integration Tests
- Status: PASS/FAIL
- Notes: [Any issues]

## Critical Issues
[List any blocking issues]

## Warnings
[List any non-blocking warnings]

## Recommendations
[Any improvements or follow-up actions]
```

---

## Notes for AI Execution

1. **Error Handling**: If a test fails, capture the error message and continue with remaining tests. Note the failure in the report.

2. **Screenshots**: Take screenshots at each major step to provide visual verification.

3. **Timeout Handling**: Some operations (especially web app loading) may take time. Allow up to 30 seconds for PyScript initialization.

4. **Conditional Tests**: Some tests may require specific data (e.g., formula fields). If data is not available, mark as SKIPPED rather than FAILED.

5. **Cleanup**: Ensure web server is stopped and temporary files are cleaned up after testing.

6. **Chrome MCP**: The Chrome DevTools MCP server must be running and connected before Phase 3.

7. **Sample Data**: The web app's "Use Sample" feature loads `demo_base_schema.json` - ensure this file exists and is valid.

8. **Parallel Execution**: Do not run tests in parallel. Execute sequentially to avoid race conditions.

9. **State Management**: Between web tests, ensure previous operations have completed before moving to the next test.

10. **Report Generation**: Generate the final report as a markdown file that can be reviewed by humans.
