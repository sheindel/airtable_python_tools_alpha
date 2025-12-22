# Airtable Analysis Tools

A web-based application for analyzing Airtable bases with multiple analysis tools organized in a tab interface.

## Features

### 1. Dependency Mapper (Active)
Visualize how fields depend on each other in your Airtable base.
- Generate Mermaid flowcharts showing field relationships
- Choose graph direction (forward, backward, or both)
- Customize flowchart layout (top-down, left-right, etc.)
- Export as SVG, Mermaid text, or open in Mermaid Live
- Show full field descriptions in nodes

### 2. Dependency Analysis (Coming Soon)
Analyze dependency complexity and identify potential issues in your base structure.
- Calculate relationship complexity metrics
- Identify circular dependencies
- Analyze table coupling
- Suggest optimization opportunities

### 3. Formula Grapher (Coming Soon)
Visualize and analyze formula structures and their dependencies.
- Parse and visualize formula syntax trees
- Show nested formula structures
- Identify field references within formulas
- Analyze formula complexity

### 4. Formula Compressor (Coming Soon)
Optimize and compress complex Airtable formulas.
- Remove unnecessary whitespace
- Simplify nested expressions
- Suggest formula optimizations
- Reduce formula length while maintaining functionality

## Architecture

### Directory Structure
```
web/
├── components/              # Shared components
│   ├── __init__.py
│   ├── airtable_client.py  # Airtable API & localStorage utilities
│   └── ui_helpers.py       # Common UI helper functions
├── tabs/                   # Tab-specific modules
│   ├── __init__.py
│   ├── dependency_mapper.py    # Dependency visualization
│   ├── dependency_analysis.py  # Complexity analysis
│   ├── formula_grapher.py      # Formula visualization
│   └── formula_compressor.py   # Formula optimization
├── index.html              # Main HTML with tab navigation
├── main.py                 # Tab routing and coordination
├── script.js               # Tab switching and UI logic
├── pyscript.toml          # PyScript configuration
└── README.md              # This file
```

### Design Principles

1. **Separation of Concerns**
   - Each tab is a self-contained module
   - Shared functionality is extracted to `components/`
   - UI code is separate from business logic

2. **Code Reuse**
   - Common Airtable operations in `airtable_client.py`
   - Shared UI utilities in `ui_helpers.py`
   - Graph operations in `at_metadata_graph.py`

3. **Maintainability**
   - Each tab module is ~50-100 lines
   - Clear file organization
   - Consistent naming conventions

4. **Progressive Enhancement**
   - Existing functionality preserved
   - New tabs can be added incrementally
   - Each tab can be developed independently

## Usage

### Getting Started

1. Enter your Airtable Base ID and Personal Access Token (PAT)
2. Click "Refresh Schema" to load your base structure
3. Select a tab to use different analysis tools
4. Choose tables and fields to analyze

### Dependency Mapper

1. Select a table from the dropdown
2. Select a field to analyze
3. Choose graph direction (forward shows what depends on this field, backward shows what it depends on)
4. Customize flowchart direction and description display
5. Export or share your diagram

## Development

### Adding a New Tab

1. Create a new module in `tabs/`:
   ```python
   """New Tab - Description of functionality"""
   from pyscript import document, window
   import sys
   sys.path.append("web")
   from components.airtable_client import get_local_storage_metadata
   
   def initialize():
       """Initialize the tab"""
       print("New tab initialized")
   ```

2. Add HTML for the tab in `index.html`:
   ```html
   <button class="tab-button ..." 
           data-tab="new-tab" 
           onclick="switchTab('new-tab')">
       New Tab
   </button>
   
   <div id="new-tab-tab" class="tab-content hidden ...">
       <!-- Tab content -->
   </div>
   ```

3. Import and initialize in `main.py`:
   ```python
   from tabs import new_tab
   
   def initialize_tabs():
       # ... other tabs
       new_tab.initialize()
   ```

4. Add files to `pyscript.toml`:
   ```toml
   [files]
   # ... other files
   "./tabs/new_tab.py" = ""
   ```

### Using Shared Components

```python
# Import shared utilities
from components.airtable_client import (
    get_local_storage_metadata,
    save_local_storage,
    find_field_by_id
)

# Get metadata
metadata = get_local_storage_metadata()

# Find a specific field
field = find_field_by_id(metadata, "fldXXXX")
```

## Technologies

- **PyScript**: Run Python in the browser
- **Tailwind CSS**: Styling and layout
- **Mermaid.js**: Diagram generation
- **NetworkX**: Graph analysis
- **Airtable API**: Schema retrieval

## License

See LICENSE file in project root.
