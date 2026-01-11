"""
Web Application Regression Tests using Chrome MCP

This script contains AI-executable tests for the web application using the Chrome DevTools MCP.
These tests should be run after starting the web server with: uv run python main.py run-web

The AI agent should execute these tests sequentially and report results.
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class WebTestResult:
    """Result of a web test"""
    test_name: str
    tab_name: str
    status: str  # PASS, FAIL, SKIP
    message: str
    screenshot_taken: bool = False
    console_errors: List[str] = None
    
    def __post_init__(self):
        if self.console_errors is None:
            self.console_errors = []


class WebTestSuite:
    """
    Web application test suite for AI execution via Chrome MCP.
    
    This class provides a structured approach to testing the web application.
    Each test method returns a WebTestResult that can be aggregated into a report.
    """
    
    def __init__(self, base_url: str = "http://localhost:8008"):
        self.base_url = base_url
        self.results: List[WebTestResult] = []
    
    # =========================================================================
    # Test: Navigation and Initial Load
    # =========================================================================
    
    def test_navigate_to_app(self) -> Dict[str, Any]:
        """
        Test 1: Navigate to the application homepage
        
        Chrome MCP Commands:
        1. navigate_page('http://localhost:8008')
        2. take_screenshot()
        3. evaluate_script(() => ({ loaded: document.readyState === 'complete' }))
        
        Expected:
        - Page loads successfully
        - document.readyState is 'complete'
        - No critical console errors
        
        Returns test configuration for AI execution
        """
        return {
            "test_name": "Navigate to Homepage",
            "tab_name": "Homepage",
            "steps": [
                {
                    "action": "navigate_page",
                    "params": {"url": self.base_url},
                    "expected": "Page loads"
                },
                {
                    "action": "wait",
                    "params": {"duration": 2},
                    "expected": "Page fully renders"
                },
                {
                    "action": "take_screenshot",
                    "expected": "Screenshot captured"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            return {
                                loaded: document.readyState === 'complete',
                                hasHeader: !!document.querySelector('h1'),
                                hasApiInput: !!document.querySelector('#base-id'),
                                hasPATInput: !!document.querySelector('#pat'),
                                hasTabButtons: document.querySelectorAll('.tab-button').length > 0,
                                version: document.querySelector('#app-version')?.textContent
                            }
                        }"""
                    },
                    "expected": {
                        "loaded": True,
                        "hasHeader": True,
                        "hasApiInput": True,
                        "hasPATInput": True,
                        "hasTabButtons": True
                    }
                }
            ]
        }
    
    # =========================================================================
    # Test: Load Sample Data
    # =========================================================================
    
    def test_load_sample_data(self) -> Dict[str, Any]:
        """
        Test 2: Load sample metadata using the "Use Sample" button
        
        Chrome MCP Commands:
        1. click('#use-sample')
        2. wait_for('Sample metadata loaded')
        3. evaluate_script to check localStorage
        
        Expected:
        - Sample data loads successfully
        - localStorage contains metadata
        - No errors in console
        """
        return {
            "test_name": "Load Sample Data",
            "tab_name": "Setup",
            "steps": [
                {
                    "action": "click",
                    "params": {"uid": "use-sample"},
                    "expected": "Button clicked"
                },
                {
                    "action": "wait_for",
                    "params": {"text": "Sample metadata loaded"},
                    "expected": "Success message appears"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const metadata = localStorage.getItem('airtable_metadata');
                            const parsed = metadata ? JSON.parse(metadata) : null;
                            return {
                                hasMetadata: !!metadata,
                                metadataSize: metadata ? metadata.length : 0,
                                baseId: localStorage.getItem('base_id'),
                                tables: parsed?.tables?.length || 0
                            }
                        }"""
                    },
                    "expected": {
                        "hasMetadata": True,
                        "tables": lambda x: x > 0  # At least 1 table
                    }
                }
            ]
        }
    
    # =========================================================================
    # Test: Dependency Mapper Tab
    # =========================================================================
    
    def test_dependency_mapper_tab(self) -> Dict[str, Any]:
        """
        Test 3: Dependency Mapper functionality
        
        Chrome MCP Commands:
        1. Click tab button
        2. Wait for tab to load
        3. Select table and field from dropdowns
        4. Generate dependency graph
        5. Verify output
        """
        return {
            "test_name": "Dependency Mapper",
            "tab_name": "Dependency Mapper",
            "steps": [
                {
                    "action": "click",
                    "params": {"selector": '[data-tab="dependency-mapper"]'},
                    "expected": "Tab switches"
                },
                {
                    "action": "wait_for",
                    "params": {"text": "Field Dependency Mapper"},
                    "expected": "Tab content visible"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const tableSelect = document.querySelector('#table-select');
                            const fieldSelect = document.querySelector('#field-select');
                            return {
                                hasTableDropdown: !!tableSelect,
                                hasFieldDropdown: !!fieldSelect,
                                tableCount: tableSelect?.options.length || 0,
                                initialFieldCount: fieldSelect?.options.length || 0
                            }
                        }"""
                    },
                    "expected": {
                        "hasTableDropdown": True,
                        "hasFieldDropdown": True,
                        "tableCount": lambda x: x > 1  # At least "Select" + 1 table
                    }
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const tableSelect = document.querySelector('#table-select');
                            if (tableSelect && tableSelect.options.length > 1) {
                                tableSelect.selectedIndex = 1;
                                tableSelect.dispatchEvent(new Event('change', { bubbles: true }));
                                return { tableSelected: true };
                            }
                            return { tableSelected: false };
                        }"""
                    },
                    "expected": {"tableSelected": True}
                },
                {
                    "action": "wait",
                    "params": {"duration": 1},
                    "expected": "Field dropdown populates"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const fieldSelect = document.querySelector('#field-select');
                            if (fieldSelect && fieldSelect.options.length > 1) {
                                fieldSelect.selectedIndex = 1;
                                return { fieldSelected: true, fieldCount: fieldSelect.options.length };
                            }
                            return { fieldSelected: false, fieldCount: 0 };
                        }"""
                    },
                    "expected": {"fieldSelected": True}
                },
                {
                    "action": "click",
                    "params": {"selector": "#generate-dependency-tree"},
                    "expected": "Generate button clicked"
                },
                {
                    "action": "wait",
                    "params": {"duration": 2},
                    "expected": "Processing completes"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const output = document.querySelector('#dependency-output');
                            const mermaid = output?.querySelector('.mermaid');
                            return {
                                hasOutput: !!output,
                                hasMermaid: !!mermaid,
                                mermaidContent: mermaid?.textContent?.substring(0, 50),
                                hasCopyButton: !!output?.querySelector('button')
                            }
                        }"""
                    },
                    "expected": {
                        "hasOutput": True,
                        "hasMermaid": True
                    }
                },
                {
                    "action": "take_screenshot",
                    "expected": "Result captured"
                }
            ]
        }
    
    # =========================================================================
    # Test: Complexity Scorecard Tab
    # =========================================================================
    
    def test_complexity_scorecard_tab(self) -> Dict[str, Any]:
        """
        Test 4: Complexity Scorecard functionality
        """
        return {
            "test_name": "Complexity Scorecard",
            "tab_name": "Complexity Scorecard",
            "steps": [
                {
                    "action": "click",
                    "params": {"selector": '[data-tab="complexity-scorecard"]'},
                    "expected": "Tab switches"
                },
                {
                    "action": "wait_for",
                    "params": {"text": "Complexity Scorecard"},
                    "expected": "Tab loaded"
                },
                {
                    "action": "click",
                    "params": {"selector": "#generate-scorecard"},
                    "expected": "Generate clicked"
                },
                {
                    "action": "wait",
                    "params": {"duration": 3},
                    "expected": "Processing (may take time)"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const output = document.querySelector('#scorecard-output');
                            return {
                                hasOutput: !!output?.textContent,
                                hasTable: !!output?.querySelector('table'),
                                rowCount: output?.querySelectorAll('tr').length || 0,
                                hasComplexityColumn: output?.textContent?.includes('Complexity')
                            }
                        }"""
                    },
                    "expected": {
                        "hasOutput": True,
                        "hasTable": True,
                        "rowCount": lambda x: x > 0
                    }
                },
                {
                    "action": "take_screenshot",
                    "expected": "Results captured"
                }
            ]
        }
    
    # =========================================================================
    # Test: Formula Evaluator Tab
    # =========================================================================
    
    def test_formula_evaluator_tab(self) -> Dict[str, Any]:
        """
        Test 5: Formula Evaluator functionality
        """
        return {
            "test_name": "Formula Evaluator",
            "tab_name": "Formula Evaluator",
            "steps": [
                {
                    "action": "click",
                    "params": {"selector": '[data-tab="formula-evaluator"]'},
                    "expected": "Tab switches"
                },
                {
                    "action": "wait_for",
                    "params": {"text": "Formula Evaluator"},
                    "expected": "Tab loaded"
                },
                {
                    "action": "fill",
                    "params": {
                        "selector": "#eval-formula-input",
                        "value": 'IF(TRUE, "yes", "no")'
                    },
                    "expected": "Formula entered"
                },
                {
                    "action": "click",
                    "params": {"selector": "#eval-formula-btn"},
                    "expected": "Evaluate clicked"
                },
                {
                    "action": "wait",
                    "params": {"duration": 1},
                    "expected": "Evaluation completes"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            const output = document.querySelector('#eval-output');
                            const text = output?.textContent || '';
                            return {
                                hasOutput: !!text,
                                result: text.substring(0, 100),
                                containsYes: text.toLowerCase().includes('yes')
                            }
                        }"""
                    },
                    "expected": {
                        "hasOutput": True,
                        "containsYes": True
                    }
                },
                {
                    "action": "take_screenshot",
                    "expected": "Result captured"
                }
            ]
        }
    
    # =========================================================================
    # Test: Dark Mode Toggle
    # =========================================================================
    
    def test_dark_mode_toggle(self) -> Dict[str, Any]:
        """
        Test 6: Dark mode toggle functionality
        """
        return {
            "test_name": "Dark Mode Toggle",
            "tab_name": "UI",
            "steps": [
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            return {
                                isDarkBefore: document.documentElement.classList.contains('dark')
                            }
                        }"""
                    },
                    "expected": {"isDarkBefore": False}  # Assuming starts in light mode
                },
                {
                    "action": "click",
                    "params": {"selector": "theme-toggle"},
                    "expected": "Toggle clicked"
                },
                {
                    "action": "wait",
                    "params": {"duration": 0.5},
                    "expected": "Transition completes"
                },
                {
                    "action": "evaluate_script",
                    "params": {
                        "function": """() => {
                            return {
                                isDark: document.documentElement.classList.contains('dark')
                            }
                        }"""
                    },
                    "expected": {"isDark": True}
                },
                {
                    "action": "take_screenshot",
                    "expected": "Dark mode captured"
                },
                {
                    "action": "click",
                    "params": {"selector": "theme-toggle"},
                    "expected": "Toggle back"
                },
                {
                    "action": "wait",
                    "params": {"duration": 0.5},
                    "expected": "Transition completes"
                }
            ]
        }
    
    # =========================================================================
    # Test: Console Errors Check
    # =========================================================================
    
    def test_console_errors(self) -> Dict[str, Any]:
        """
        Test 7: Check for console errors during session
        """
        return {
            "test_name": "Console Errors Check",
            "tab_name": "Console",
            "steps": [
                {
                    "action": "list_console_messages",
                    "params": {"types": ["error"]},
                    "expected": "Error list retrieved"
                },
                {
                    "action": "evaluate_result",
                    "params": {
                        "check": "errors should be empty or contain only non-critical warnings"
                    },
                    "expected": "No critical errors"
                }
            ]
        }
    
    # =========================================================================
    # Additional Quick Tests (for all remaining tabs)
    # =========================================================================
    
    def test_all_tabs_load(self) -> Dict[str, Any]:
        """
        Test 8: Verify all tabs can be opened without errors
        """
        tabs = [
            "dependency-analysis",
            "formula-grapher",
            "formula-compressor",
            "unused-fields",
            "postgres-schema",
            "code-generator",
            "evaluator-generator",
            "types-generator"
        ]
        
        return {
            "test_name": "All Tabs Load Test",
            "tab_name": "All Tabs",
            "steps": [
                {
                    "action": "iterate_tabs",
                    "params": {"tabs": tabs},
                    "expected": "All tabs load without errors",
                    "details": """
                    For each tab:
                    1. Click tab button: document.querySelector('[data-tab="{tab}"]')?.click()
                    2. Wait 1 second
                    3. Check no errors: list_console_messages(types=['error'])
                    4. Verify tab is active
                    """
                }
            ]
        }


# =============================================================================
# Test Execution Instructions for AI
# =============================================================================

AI_EXECUTION_INSTRUCTIONS = """
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
"""


def generate_test_execution_guide():
    """Generate a markdown guide for AI test execution"""
    suite = WebTestSuite()
    
    guide_lines = [
        "# Web Application Test Execution Guide",
        "",
        "This guide contains detailed test procedures for AI execution using Chrome MCP.",
        "",
        "## Prerequisites",
        "1. Web server running at http://localhost:8008",
        "2. Chrome MCP server activated and connected",
        "3. Sample data file (demo_base_schema.json) available",
        "",
        "## Test Suite Overview",
        ""
    ]
    
    # Get all test methods
    test_methods = [
        method for method in dir(suite)
        if method.startswith('test_') and callable(getattr(suite, method))
    ]
    
    for i, method_name in enumerate(test_methods, 1):
        method = getattr(suite, method_name)
        test_config = method()
        
        guide_lines.append(f"## Test {i}: {test_config['test_name']}")
        guide_lines.append(f"**Tab**: {test_config['tab_name']}")
        guide_lines.append("")
        guide_lines.append("### Steps")
        guide_lines.append("")
        
        for j, step in enumerate(test_config['steps'], 1):
            guide_lines.append(f"{j}. **{step['action']}**")
            if 'params' in step:
                guide_lines.append(f"   - Params: `{step['params']}`")
            guide_lines.append(f"   - Expected: {step['expected']}")
            guide_lines.append("")
        
        guide_lines.append("---")
        guide_lines.append("")
    
    guide_lines.append("## AI Execution Instructions")
    guide_lines.append(AI_EXECUTION_INSTRUCTIONS)
    
    return "\n".join(guide_lines)


if __name__ == "__main__":
    # Generate the test execution guide
    guide = generate_test_execution_guide()
    
    # Save to file
    with open("test_results/WEB_TEST_GUIDE.md", "w") as f:
        f.write(guide)
    
    print("✅ Web test guide generated: test_results/WEB_TEST_GUIDE.md")
    print("   This guide contains detailed test procedures for AI execution")
    print("   using Chrome DevTools MCP.")
