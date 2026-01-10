# Airtable Analysis Tools - AI Agent Instructions

## Project Overview

This is a dual-environment Python project that analyzes Airtable bases:
1. **CLI tool** ([main.py](main.py)) - Server-side analysis using Typer
2. **Web app** ([web/](web)) - Browser-based PyScript application with no backend

Both environments share core analysis modules ([web/at_metadata_graph.py](web/at_metadata_graph.py), [web/airtable_mermaid_generator.py](web/airtable_mermaid_generator.py)) but run in fundamentally different contexts.

## Architecture

### Dual Runtime Pattern
- **CLI**: Standard Python with `networkx`, `httpx`, runs via `uv run python main.py`
- **Web**: PyScript (Python in browser) with limited stdlib, no HTTP from Python side
  - JavaScript handles API calls ([web/script.js](web/script.js))
  - Python modules imported via [web/pyscript.toml](web/pyscript.toml)
  - Communication: Python exports functions to `window`, JavaScript calls them

### Graph-Based Analysis Core
All analysis revolves around `NetworkX.DiGraph` created by `metadata_to_graph()`:
- **Nodes**: Fields (with metadata) and tables
- **Edges**: Dependencies (formula refs, lookups, rollups, record links)
- **Relationships**: Edge attribute `relationship` specifies type (e.g., "formula", "lookup", "rollup_via")

Key pattern: Many tools follow `metadata → graph → subgraph → mermaid`:
```python
G = metadata_to_graph(airtable_metadata)
subgraph = get_reachable_nodes(G, field_id, direction="both")
mermaid = graph_to_mermaid(subgraph, direction="TD")
```

### Web App Tab Architecture
Six independent tabs ([web/tabs/](web/tabs/)) initialized by [web/main.py](web/main.py):
- Each tab is a self-contained module (~50-200 lines)
- Shared utilities in [web/components/](web/components/)
- Web components in [web/components/ui/](web/components/ui/) (at-dropdown, theme-toggle, tab-manager)
- Module structure enables parallel development without conflicts

## Development Workflows

### Building Assets
```bash
# Build optimized Tailwind CSS (required before running)
npm run build:css

# Watch mode for development
npm run watch:css

# Generate PyScript config (auto-run in CI)
uv run python scripts/generate_pyscript_config.py
```

### Running the Web App
```bash
uv run python main.py run-web
```
Serves at `http://localhost:8008` with aggressive cache-busting headers. Watch browser console for PyScript initialization logs.

### Environment Setup
```bash
uv sync              # Install Python dependencies
uv sync --group dev  # Install dev dependencies (pytest, etc.)
npm install          # Install Node dependencies (Tailwind CLI)
npm run build:css    # Build Tailwind CSS
```
Project requires Python ≥3.12, managed by `uv` (not virtualenv/poetry).

### Testing
```bash
# Run Python unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=web --cov-report=html

# Run specific test file
uv run pytest tests/test_at_metadata_graph.py
```
See [tests/README.md](tests/README.md) for more details.

### Adding a Web Tab
1. Create `web/tabs/new_tab.py` with `initialize()` function
2. Add HTML section in [web/index.html](web/index.html) with matching `id="new-tab-tab"`
3. Import and initialize in [web/main.py](web/main.py)
4. Add file mapping to [web/pyscript.toml](web/pyscript.toml) `[files]` section
5. Wire up JavaScript handlers in [web/script.js](web/script.js) if needed

Example tab structure:
```python
"""New Tab - Brief description"""
from pyscript import document, window
import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata

def initialize():
    """Initialize the tab"""
    window.myFunction = my_function  # Export to JS
    print("New tab initialized")
```

### PyScript Debugging
- Python `print()` outputs to browser console (not visible in UI)
- Check "PyScript is ready" log before expecting Python functions
- Use `window.functionName` pattern to call Python from JavaScript
- Store/retrieve data via `localStorage` (see [web/components/airtable_client.py](web/components/airtable_client.py))

## Project-Specific Conventions

### Shared Constants
Use constants from [web/constants.py](web/constants.py) instead of magic strings:
```python
from constants import FIELD_TYPE_FORMULA, COMPUTED_FIELD_TYPES, ERROR_NO_METADATA
```

### Error Handling
Use standardized error handling from [web/components/error_handling.py](web/components/error_handling.py):
```python
from components.error_handling import handle_tab_error, display_error_in_element, validate_metadata

try:
    metadata = validate_metadata(get_metadata())
    # ... operation
except AnalysisError as e:
    handle_tab_error(e, "generating diagram", "output-element-id")
```

### Airtable Field Reference Formats
Field IDs like `{fld[A-Za-z0-9]{14}}` appear throughout:
- **Internal**: Always use field IDs for graph operations
- **Display**: Convert to field names via `_convert_field_references()` for user-facing output
- **Formula compression** ([web/tabs/formula_compressor.py](web/tabs/formula_compressor.py)) supports both output modes

### Graph Traversal Directions
Three modes in `get_reachable_nodes()`:
- `backward`: What this field depends on (ancestors)
- `forward`: What depends on this field (descendants)
- `both`: Full dependency graph (default)

Direction affects analysis semantics:
- Dependency mapper: User choice (shows "used by" vs "uses")
- Complexity scorecard: Always `backward` (count dependencies)
- Unused fields: Check `in_degree` (no incoming edges)

### Mermaid Diagram Generation
Standard flow: `networkx.DiGraph` → `graph_to_mermaid()` → Mermaid text → rendered via [mermaid.js](https://mermaid.js.org/)
- Display modes: "simple", "descriptions", "formulas", "all"
- Flowchart directions: "TD" (top-down), "LR" (left-right), "RL", "BT"
- Subgraphs group fields by table automatically
- Escape parentheses in text to avoid Mermaid syntax conflicts

### Formula Compression Algorithm
The compression system ([web/tabs/formula_compressor.py](web/tabs/formula_compressor.py)) recursively inlines field references:

**Core Algorithm**:
```python
def _compress_formula_recursive(formula, metadata, max_depth, output_format, depth, visited_fields):
    # 1. Check depth limit
    if max_depth is not None and depth >= max_depth:
        return formula, depth
    
    # 2. Find all field references: {fldXXXXXXXXXXXXXX}
    matches = list(re.finditer(r'\{(fld[a-zA-Z0-9]+)\}', formula))
    
    # 3. Process in REVERSE order (maintains string positions)
    for match in reversed(matches):
        field_id = match.group(1)
        
        # 4. Circular reference protection
        if field_id in visited_fields:
            continue
        
        # 5. Replace only formula fields, recursively
        if field.type == "formula":
            visited_fields_copy = visited_fields.copy()
            visited_fields_copy.add(field_id)
            compressed_inner = _compress_formula_recursive(...)
            
            # 6. Wrap in parens for operator precedence safety
            result = result[:start] + f"({compressed_inner})" + result[end:]
```

**Key Implementation Details**:
- **Reverse iteration**: Process matches from end to start to avoid index shifting after replacement
- **Visited set copying**: Each recursion branch gets its own copy to allow the same field in different branches
- **Parenthesization**: Always wrap replaced formulas in `()` to preserve operator precedence
- **Depth tracking**: Returns `(compressed_formula, max_depth_reached)` tuple
- **Two-phase conversion**: Compress with IDs, then convert to names if requested (not during recursion)
- **Non-formula fields**: Stop recursion at basic fields (text, number, etc.) - don't try to "expand" them

**Output Formatting**:
- `format_formula_compact()`: Single line, removes all whitespace except in string literals
- `format_formula_logical()`: Multi-line with indentation based on function nesting depth

**Common Use Case**: Inline helper fields into main formulas to understand total calculation without jumping between fields.

### Module Path Management
All web modules use `sys.path.append("web")` to import shared modules. This is required for PyScript's import system.

## Build System

### Tailwind CSS Pipeline
The project uses Tailwind CSS for all styling, compiled via standalone CLI (no PostCSS or Node build system needed beyond Tailwind itself).

**Architecture**:
- **Source**: [web/input.css](web/input.css) - Tailwind directives only (@tailwind base/components/utilities)
- **Config**: [tailwind.config.js](tailwind.config.js) - Scans `web/**/*.{html,js,py}` for class usage
- **Output**: `web/output.css` - Minified CSS (~27KB), gitignored
- **Build**: `npm run build:css` - Must run before testing/deploying app

**Content Detection**:
Tailwind scans all files in `web/` directory for class usage:
- HTML: `web/index.html` and any template files
- JavaScript: `web/**/*.js` (including dynamically generated classes)
- Python: `web/**/*.py` (classes in Python string literals like `element.className = "..."`)

**Custom Configuration** ([tailwind.config.js](tailwind.config.js)):
```javascript
module.exports = {
  content: ["./web/**/*.{html,js,py}"],
  darkMode: 'class',  // Manual toggle via .dark class
  theme: {
    extend: {
      colors: {
        primary: { /* 50-900 blue palette */ }
      }
    }
  }
}
```

**Development Workflow**:
```bash
# One-time build (required before running app)
npm run build:css

# Watch mode for active development (auto-rebuilds on file changes)
npm run watch:css
```

**Important**: The `web/output.css` file MUST exist for the app to render correctly. If you see unstyled HTML, run `npm run build:css` first.

**Dependencies** ([package.json](package.json)):
- `tailwindcss@^3.4.17` as devDependency
- No other Node dependencies (no webpack, postcss, etc.)

### PyScript Configuration
- Generator: [scripts/generate_pyscript_config.py](scripts/generate_pyscript_config.py)
- Auto-discovers all `.py` files in [web/](web/) directory
- Updates [web/pyscript.toml](web/pyscript.toml) `[files]` section
- Run manually: `uv run python scripts/generate_pyscript_config.py`
- CI: Runs automatically in GitHub Actions

### GitHub Actions Workflow
1. Install Node.js and run `npm ci`
2. Build Tailwind CSS with `npm run build:css`
3. Install Python and generate PyScript config
4. Inject version number into HTML
5. Deploy to GitHub Pages

### Dependency Management
**Python** ([pyproject.toml](pyproject.toml)):
- Manager: `uv` (not pip/poetry/virtualenv)
- Python version: ≥3.12
- Key dependencies: `networkx`, `httpx`, `typer`, `pyscript`
- Dev dependencies: `pytest`, `pytest-cov`, `pytest-asyncio`
- Install: `uv sync` or `uv sync --group dev`

**Node** ([package.json](package.json)):
- Manager: `npm`
- Only dependency: `tailwindcss` (dev)
- Install: `npm install` (rarely needed after initial setup)

## Key Implementation Details

### Field Type Handling
Match statements in [web/airtable_mermaid_generator.py](web/airtable_mermaid_generator.py) show canonical field type cases:
- Computed fields: `formula`, `rollup`, `multipleLookupValues`, `count`
- Link fields: `multipleRecordLinks` (bidirectional via `inverseLinkFieldId`)
- Basic fields: `singleLineText`, `number`, `checkbox`, etc.

### Web Component Communication
Data flows: User action → JavaScript event → Python function → DOM update
```javascript
// JavaScript calls Python
window.myPythonFunction(arg1, arg2);

// Python exports to JavaScript
window.myPythonFunction = my_python_function
```

### Metadata Structure
Airtable metadata (see [web/at_types.py](web/at_types.py)) follows this hierarchy:
```
AirtableMetadata
  └─ tables[]
      └─ fields[]
          ├─ id, name, type
          └─ options (type-specific, contains formulas/references)
```

Access patterns: Always iterate `metadata["tables"]` then `table["fields"]`, not direct ID lookup.

## Testing

### Running Tests
```bash
# Run all Python unit tests
uv run pytest

# Run with coverage report
uv run pytest --cov=web --cov-report=html

# Run specific test
uv run pytest tests/test_at_metadata_graph.py -v
```

### Pytest Import System
The project uses a specific import pattern to enable tests to import web modules:

**In conftest.py** (runs before all tests):
```python
import sys
from pathlib import Path

# Mock PyScript before importing any web modules
sys.modules['pyscript'] = MagicMock()

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))
```

**In individual test files** (when not using conftest fixtures):
```python
import sys
from pathlib import Path

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from at_metadata_graph import metadata_to_graph
from constants import FIELD_TYPE_FORMULA
```

**Key Points**:
- **Always** add web directory to `sys.path` before importing web modules
- PyScript is mocked globally in conftest.py (required since web modules import from pyscript)
- Use `sys.path.insert(0, ...)` not `append()` to prioritize web directory
- The pytest.ini configuration automatically sets coverage to track the `web/` directory

### Test Organization
- [tests/conftest.py](tests/conftest.py): Shared fixtures and PyScript mocking
- [tests/test_at_metadata_graph.py](tests/test_at_metadata_graph.py): Graph operations
- [tests/test_constants.py](tests/test_constants.py): Constants validation
- [pytest.ini](pytest.ini): Test runner configuration (coverage, test discovery)
- See [tests/README.md](tests/README.md) for detailed documentation

### Coverage Configuration
Coverage is configured in [pytest.ini](pytest.ini):
- Source: `web/` directory only (excludes CLI and scripts)
- Omits: test files, pycache, and test_ files
- Reports: terminal output with missing lines + HTML report in `htmlcov/`
- Run with every test invocation via `addopts = --cov=web --cov-report=term-missing`

### Coverage Goals
- Core business logic: 80%+
- Graph operations: 90%+
- Error handling: 70%+

## Common Pitfalls

1. **PyScript limitations**: No `httpx`/`requests` in browser context - use JavaScript `fetch()` instead
2. **Path imports**: Forget `sys.path.append("web")` → import errors in browser
3. **Circular dependencies**: Use `visited_fields` set in recursive graph traversals
4. **Field ID vs name confusion**: Graph operations need IDs, UI needs names
5. **Mermaid syntax errors**: Unescaped parentheses in text break diagrams
6. **localStorage timing**: Check `get_local_storage_metadata() is not None` before processing
7. **Missing CSS build**: Unstyled HTML means `web/output.css` doesn't exist - run `npm run build:css`
8. **Test imports**: Tests fail with import errors if `sys.path.insert(0, "web")` is missing
9. **PyScript mocking in tests**: Must mock pyscript module before importing web modules (done in conftest.py)
10. **Dark mode text colors**: Always include dark mode text color classes (see "Code Display Components" section below)
11. **Import verification**: ALWAYS verify function names exist in source modules before importing (use grep_search on the source file)

## Web Development Checklist

When adding a new web tab or feature, follow this checklist:

1. ✅ **Verify Imports First**
   - Use `grep_search` to find actual function names in source modules
   - Check function signatures match your usage
   - Common mistake: Assuming function names without checking

2. ✅ **Create Tab Module** (`web/tabs/your_tab.py`)
   - Add `sys.path.append("web")` at top
   - Export functions to `window` in `initialize()`
   - Verify ALL imported functions actually exist

3. ✅ **Update HTML** (`web/index.html`)
   - Add option to mobile dropdown (`<select id="mobile-tab-selector">`)
   - Add tab button to desktop navigation
   - Add tab content section with matching `id="your-tab-tab"`

4. ✅ **Update Main** (`web/main.py`)
   - Import tab module in imports section
   - Call `your_tab.initialize()` in `initialize_tabs()`

5. ✅ **Update Script** (`web/script.js`)
   - Add dropdown wiring in `wireDropdowns()` if needed
   - Add dropdown population in table options if needed
   - Add tab-specific initialization to `tab-change` event listener if needed

6. ✅ **Update Config** (`web/pyscript.toml`)
   - Add tab file: `"./tabs/your_tab.py" = "tabs/your_tab.py"`
   - Add any new dependencies in `[files]` section

7. ✅ **Build & Test**
   - Run `npm run build:css` to rebuild Tailwind
   - Refresh browser to see changes
   - Check browser console for Python import errors
   - Test all tab functionality

## External Dependencies

- **Airtable API**: Schema fetched via `/v0/meta/bases/{baseId}/tables` endpoint
- **Mermaid.js**: Renders flowcharts from text definitions
- **PyScript**: Enables Python in browser (version 2025.2.3)
- **Tailwind CSS**: Styling via CDN, dark mode via `class="dark"`
- **NetworkX**: Graph analysis (works in PyScript)

## CSS/Tailwind Styling Patterns

### Code Display Components
**ALWAYS use the reusable helpers from [web/components/code_display.py](web/components/code_display.py) when displaying code:**

```python
from components.code_display import create_code_block, create_inline_code

# Simple code block (properly styled with dark mode support)
html = create_code_block(code_string)

# Code block with copy button
html = create_code_block(
    code_string, 
    show_copy_button=True, 
    copy_button_id="copy-btn"
)

# Inline code
text = f"Use the {create_inline_code('getData()')} function"
```

**Why this matters**: Dark mode requires `text-gray-800 dark:text-gray-200` classes on `<code>` elements. Missing these classes causes black text on dark backgrounds (unreadable). The helper functions guarantee correct styling.

**Manual code blocks** (if you must create them manually):
```python
# ✅ CORRECT - includes dark mode text colors
f'<code class="text-sm text-gray-800 dark:text-gray-200">{code}</code>'

# ❌ WRONG - missing dark mode text colors (black text on dark bg)
f'<code class="text-sm">{code}</code>'
```

**Standard class constants** (imported from code_display.py):
- `CODE_BLOCK_CLASSES`: Background, padding, borders
- `CODE_TEXT_CLASSES`: Text size and colors (light + dark)
- `INLINE_CODE_CLASSES`: Inline code styling

### Dark Mode Implementation
- Uses `class="dark"` toggle on root elements (managed by [web/components/ui/theme-toggle.js](web/components/ui/theme-toggle.js))
- All color classes must have dark mode variants: `bg-white dark:bg-gray-800`
- Transitions on color changes: `transition-colors duration-200`

### Custom Tailwind Configuration
Extended color palette in [web/index.html](web/index.html) `<head>`:
```javascript
tailwind.config = {
    darkMode: 'class',  // Not 'media' - manual toggle
    theme: {
        extend: {
            colors: {
                primary: {  // Blue shades 50-900
                    500: '#3b82f6',  // Default blue
                    600: '#2563eb',  // Hover state
                    // ... etc
                }
            }
        }
    }
}
```

### Consistent Component Styling
**Buttons**: Always use primary-600 with hover/active states
```html
<button class="bg-primary-600 hover:bg-primary-700 active:bg-primary-800 
               text-white font-semibold py-2.5 px-4 rounded-lg shadow-sm 
               hover:shadow transition-all duration-150 
               disabled:opacity-60 disabled:cursor-not-allowed">
```

**Input Fields**: Consistent padding and dark mode
```html
<input class="w-full p-2 border rounded 
              dark:bg-gray-700 dark:border-gray-600 dark:text-white">
```

**Cards/Containers**: Standard rounded corners and shadows
```html
<div class="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md 
            transition-colors duration-200">
```

**Tab Navigation**: Active state uses border-bottom-2 with color
```html
<button class="tab-button active 
               border-b-2 border-blue-500 text-blue-600 
               dark:text-blue-400 dark:border-blue-400">
```

### Icon Integration
- Inline SVGs for icons (not icon fonts)
- Always include `dark:` variants for stroke/fill colors
- Consistent sizing: `w-5 h-5` for inline icons, `w-4 h-4` for button icons

### Backdrop Overlays
Copy/action buttons use glassmorphism:
```html
<button class="bg-white/80 dark:bg-gray-800/80 
               opacity-0 hover:opacity-100 focus:opacity-100"
        style="backdrop-filter: blur(4px);">
```

### Important Note
**Always run `npm run build:css` after modifying Tailwind classes** to regenerate the optimized CSS file.

## File Organization Logic

- [main.py](main.py): CLI commands (use Typer's `@app.command()`)
- [web/main.py](web/main.py): Tab initialization coordinator
- [web/tabs/*.py](web/tabs/): Independent tab implementations
- [web/components/](web/components/): Shared Python utilities
- [web/modules/*.js](web/modules/): Shared JavaScript utilities
- [web/components/ui/*.js](web/components/ui/): Web components
