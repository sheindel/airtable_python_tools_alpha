# Web Application Test Execution Guide

This guide contains detailed test procedures for AI execution using Chrome MCP.

## Prerequisites
1. Web server running at http://localhost:8008
2. Chrome MCP server activated and connected
3. Sample data file (demo_base_schema.json) available

## Test Suite Overview

## Test 1: All Tabs Load Test
**Tab**: All Tabs

### Steps

1. **iterate_tabs**
   - Params: `{'tabs': ['dependency-analysis', 'formula-grapher', 'formula-compressor', 'unused-fields', 'postgres-schema', 'code-generator', 'evaluator-generator', 'types-generator']}`
   - Expected: All tabs load without errors

---

## Test 2: Complexity Scorecard
**Tab**: Complexity Scorecard

### Steps

1. **click**
   - Params: `{'selector': '[data-tab="complexity-scorecard"]'}`
   - Expected: Tab switches

2. **wait_for**
   - Params: `{'text': 'Complexity Scorecard'}`
   - Expected: Tab loaded

3. **click**
   - Params: `{'selector': '#generate-scorecard'}`
   - Expected: Generate clicked

4. **wait**
   - Params: `{'duration': 3}`
   - Expected: Processing (may take time)

5. **evaluate_script**
   - Params: `{'function': "() => {\n                            const output = document.querySelector('#scorecard-output');\n                            return {\n                                hasOutput: !!output?.textContent,\n                                hasTable: !!output?.querySelector('table'),\n                                rowCount: output?.querySelectorAll('tr').length || 0,\n                                hasComplexityColumn: output?.textContent?.includes('Complexity')\n                            }\n                        }"}`
   - Expected: {'hasOutput': True, 'hasTable': True, 'rowCount': <function WebTestSuite.test_complexity_scorecard_tab.<locals>.<lambda> at 0x72becd725f80>}

6. **take_screenshot**
   - Expected: Results captured

---

## Test 3: Console Errors Check
**Tab**: Console

### Steps

1. **list_console_messages**
   - Params: `{'types': ['error']}`
   - Expected: Error list retrieved

2. **evaluate_result**
   - Params: `{'check': 'errors should be empty or contain only non-critical warnings'}`
   - Expected: No critical errors

---

## Test 4: Dark Mode Toggle
**Tab**: UI

### Steps

1. **evaluate_script**
   - Params: `{'function': "() => {\n                            return {\n                                isDarkBefore: document.documentElement.classList.contains('dark')\n                            }\n                        }"}`
   - Expected: {'isDarkBefore': False}

2. **click**
   - Params: `{'selector': 'theme-toggle'}`
   - Expected: Toggle clicked

3. **wait**
   - Params: `{'duration': 0.5}`
   - Expected: Transition completes

4. **evaluate_script**
   - Params: `{'function': "() => {\n                            return {\n                                isDark: document.documentElement.classList.contains('dark')\n                            }\n                        }"}`
   - Expected: {'isDark': True}

5. **take_screenshot**
   - Expected: Dark mode captured

6. **click**
   - Params: `{'selector': 'theme-toggle'}`
   - Expected: Toggle back

7. **wait**
   - Params: `{'duration': 0.5}`
   - Expected: Transition completes

---

## Test 5: Dependency Mapper
**Tab**: Dependency Mapper

### Steps

1. **click**
   - Params: `{'selector': '[data-tab="dependency-mapper"]'}`
   - Expected: Tab switches

2. **wait_for**
   - Params: `{'text': 'Field Dependency Mapper'}`
   - Expected: Tab content visible

3. **evaluate_script**
   - Params: `{'function': "() => {\n                            const tableSelect = document.querySelector('#table-select');\n                            const fieldSelect = document.querySelector('#field-select');\n                            return {\n                                hasTableDropdown: !!tableSelect,\n                                hasFieldDropdown: !!fieldSelect,\n                                tableCount: tableSelect?.options.length || 0,\n                                initialFieldCount: fieldSelect?.options.length || 0\n                            }\n                        }"}`
   - Expected: {'hasTableDropdown': True, 'hasFieldDropdown': True, 'tableCount': <function WebTestSuite.test_dependency_mapper_tab.<locals>.<lambda> at 0x72becd725f80>}

4. **evaluate_script**
   - Params: `{'function': "() => {\n                            const tableSelect = document.querySelector('#table-select');\n                            if (tableSelect && tableSelect.options.length > 1) {\n                                tableSelect.selectedIndex = 1;\n                                tableSelect.dispatchEvent(new Event('change', { bubbles: true }));\n                                return { tableSelected: true };\n                            }\n                            return { tableSelected: false };\n                        }"}`
   - Expected: {'tableSelected': True}

5. **wait**
   - Params: `{'duration': 1}`
   - Expected: Field dropdown populates

6. **evaluate_script**
   - Params: `{'function': "() => {\n                            const fieldSelect = document.querySelector('#field-select');\n                            if (fieldSelect && fieldSelect.options.length > 1) {\n                                fieldSelect.selectedIndex = 1;\n                                return { fieldSelected: true, fieldCount: fieldSelect.options.length };\n                            }\n                            return { fieldSelected: false, fieldCount: 0 };\n                        }"}`
   - Expected: {'fieldSelected': True}

7. **click**
   - Params: `{'selector': '#generate-dependency-tree'}`
   - Expected: Generate button clicked

8. **wait**
   - Params: `{'duration': 2}`
   - Expected: Processing completes

9. **evaluate_script**
   - Params: `{'function': "() => {\n                            const output = document.querySelector('#dependency-output');\n                            const mermaid = output?.querySelector('.mermaid');\n                            return {\n                                hasOutput: !!output,\n                                hasMermaid: !!mermaid,\n                                mermaidContent: mermaid?.textContent?.substring(0, 50),\n                                hasCopyButton: !!output?.querySelector('button')\n                            }\n                        }"}`
   - Expected: {'hasOutput': True, 'hasMermaid': True}

10. **take_screenshot**
   - Expected: Result captured

---

## Test 6: Formula Evaluator
**Tab**: Formula Evaluator

### Steps

1. **click**
   - Params: `{'selector': '[data-tab="formula-evaluator"]'}`
   - Expected: Tab switches

2. **wait_for**
   - Params: `{'text': 'Formula Evaluator'}`
   - Expected: Tab loaded

3. **fill**
   - Params: `{'selector': '#eval-formula-input', 'value': 'IF(TRUE, "yes", "no")'}`
   - Expected: Formula entered

4. **click**
   - Params: `{'selector': '#eval-formula-btn'}`
   - Expected: Evaluate clicked

5. **wait**
   - Params: `{'duration': 1}`
   - Expected: Evaluation completes

6. **evaluate_script**
   - Params: `{'function': "() => {\n                            const output = document.querySelector('#eval-output');\n                            const text = output?.textContent || '';\n                            return {\n                                hasOutput: !!text,\n                                result: text.substring(0, 100),\n                                containsYes: text.toLowerCase().includes('yes')\n                            }\n                        }"}`
   - Expected: {'hasOutput': True, 'containsYes': True}

7. **take_screenshot**
   - Expected: Result captured

---

## Test 7: Load Sample Data
**Tab**: Setup

### Steps

1. **click**
   - Params: `{'uid': 'use-sample'}`
   - Expected: Button clicked

2. **wait_for**
   - Params: `{'text': 'Sample metadata loaded'}`
   - Expected: Success message appears

3. **evaluate_script**
   - Params: `{'function': "() => {\n                            const metadata = localStorage.getItem('airtable_metadata');\n                            const parsed = metadata ? JSON.parse(metadata) : null;\n                            return {\n                                hasMetadata: !!metadata,\n                                metadataSize: metadata ? metadata.length : 0,\n                                baseId: localStorage.getItem('base_id'),\n                                tables: parsed?.tables?.length || 0\n                            }\n                        }"}`
   - Expected: {'hasMetadata': True, 'tables': <function WebTestSuite.test_load_sample_data.<locals>.<lambda> at 0x72becd725f80>}

---

## Test 8: Navigate to Homepage
**Tab**: Homepage

### Steps

1. **navigate_page**
   - Params: `{'url': 'http://localhost:8008'}`
   - Expected: Page loads

2. **wait**
   - Params: `{'duration': 2}`
   - Expected: Page fully renders

3. **take_screenshot**
   - Expected: Screenshot captured

4. **evaluate_script**
   - Params: `{'function': "() => {\n                            return {\n                                loaded: document.readyState === 'complete',\n                                hasHeader: !!document.querySelector('h1'),\n                                hasApiInput: !!document.querySelector('#base-id'),\n                                hasPATInput: !!document.querySelector('#pat'),\n                                hasTabButtons: document.querySelectorAll('.tab-button').length > 0,\n                                version: document.querySelector('#app-version')?.textContent\n                            }\n                        }"}`
   - Expected: {'loaded': True, 'hasHeader': True, 'hasApiInput': True, 'hasPATInput': True, 'hasTabButtons': True}

---

## AI Execution Instructions

# Web Test Execution Instructions for AI

To execute these tests, the AI should:

1. **Start the web server** (if not already running):
   ```bash
   uv run python main.py run-web &
   ```

2. **Ensure Chrome MCP is activated and connected**

3. **For each test method** in WebTestSuite:
   - Call the test method to get test configuration
   - Execute each step in the "steps" list
   - Verify "expected" conditions are met
   - Capture screenshots where indicated
   - Report any failures with details
   - Continue to next test even if one fails

4. **Example execution pattern**:
   ```python
   suite = WebTestSuite()
   test_config = suite.test_navigate_to_app()
   
   for step in test_config["steps"]:
       action = step["action"]
       params = step.get("params", {})
       expected = step["expected"]
       
       # Execute the action using Chrome MCP
       if action == "navigate_page":
           navigate_page(params["url"])
       elif action == "click":
           click(params["selector"])
       elif action == "evaluate_script":
           result = evaluate_script(params["function"])
           # Verify result matches expected
       # ... etc
   ```

5. **Report format**:
   For each test, report:
   - Test name
   - Status (PASS/FAIL)
   - Execution time
   - Screenshot file (if taken)
   - Any errors encountered
   - Console errors (if applicable)

6. **Error handling**:
   - If a test fails, capture the error and continue
   - Take screenshot on failure for debugging
   - Check console for JavaScript errors
   - Report which step failed and why

7. **Cleanup**:
   - After all tests, kill the web server
   - Generate summary report

## Quick Test Execution Checklist

- [ ] Navigate to homepage
- [ ] Load sample data
- [ ] Test Dependency Mapper
- [ ] Test Complexity Scorecard
- [ ] Test Formula Evaluator
- [ ] Test Dark Mode Toggle
- [ ] Check all tabs load
- [ ] Review console for errors
- [ ] Generate test report

## Expected Results

All tests should PASS with:
- No critical JavaScript errors
- All tabs load successfully
- All interactive elements work
- Mermaid diagrams render
- Dark mode toggles correctly
- Sample data loads properly
