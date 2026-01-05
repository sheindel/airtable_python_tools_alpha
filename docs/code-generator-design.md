# Code Generator - Unified Design Document

**Status**: Design Phase  
**Created**: January 4, 2026  
**Related**: [formula-runtime-design.md](formula-runtime-design.md), Types Generator Tab

## Executive Summary

This document outlines the design for a **unified Code Generator** that consolidates all code generation capabilities into a single, workflow-based interface. Instead of separate tools for types, runtime, and schema generation, users select their use case and get a tailored set of options.

**Key Innovation**: Progressive disclosure based on what users are building (client library, server SDK, database schema, or full-stack package).

---

## Current State Assessment

### Existing Generators (Already Built)

1. **Type Definitions** ([web/types_generator.py](web/types_generator.py))
   - TypeScript interfaces
   - Python dataclasses/TypedDict
   
2. **Runtime Code** ([web/code_generators/](web/code_generators/))
   - Python runtime ([python_runtime_generator.py](web/code_generators/python_runtime_generator.py))
   - JavaScript runtime ([javascript_runtime_generator.py](web/code_generators/javascript_runtime_generator.py))
   - SQL runtime ([sql_runtime_generator.py](web/code_generators/sql_runtime_generator.py))

3. **Helper Functions**
   - Python helpers ([python_helpers_generator.py](web/python_helpers_generator.py))
   - TypeScript helpers ([typescript_helpers_generator.py](web/typescript_helpers_generator.py))

4. **Schema Generation**
   - PostgreSQL schema ([postgres_schema_generator.py](web/postgres_schema_generator.py))

### Current UI

Single "Types Generator" tab that exposes limited functionality:
- TypeScript types
- Python types (dataclass/TypedDict)
- SQL functions/triggers

**Problem**: Capabilities are greater than what's exposed in the UI. Users don't understand all the options available.

---

## Design Philosophy

### Single Tab with Workflows

**Decision**: ONE flexible tab with a **workflow-based approach** rather than multiple tabs.

**Advantages**:
- Users naturally think "I need code for my Airtable base"
- Reduces navigation complexity
- Easier to explain in documentation
- All options visible in one place
- Generated files can be combined into a single download

**Key Principle**: **Progressive disclosure** - show relevant options based on what the user selects.

---

## User Interface Design

### Four-Step Process

```
┌────────────────────────────────────────────────────┐
│  CODE GENERATOR                                    │
│                                                    │
│  Step 1: What are you building?                   │
│  ┌──────────────────────────────────────┐        │
│  │ ○ Client Library (TypeScript/JS)     │        │
│  │ ○ Server SDK (Python)                │        │
│  │ ○ Database Schema (SQL)              │        │
│  │ ○ Full-Stack Package (All of above)  │        │
│  └──────────────────────────────────────┘        │
│                                                    │
│  Step 2: Configure Options                        │
│  [Dynamic form based on Step 1 selection]         │
│                                                    │
│  Step 3: Formula Handling                         │
│  [Options for how to handle computed fields]      │
│                                                    │
│  [Generate Code Button]                           │
│                                                    │
│  Step 4: Review & Download                        │
│  [File tree with previews and download options]   │
└────────────────────────────────────────────────────┘
```

---

## Workflow Definitions

### Step 1: Primary Use Case Selection

```javascript
workflows = [
  {
    id: "client-library",
    label: "Client Library",
    description: "TypeScript/JavaScript types and helpers for frontend/React/Vue apps",
    icon: "🌐",
    generates: ["types.ts", "helpers.ts", "helpers.js", "examples.ts"]
  },
  {
    id: "server-sdk",
    label: "Server SDK", 
    description: "Python library with computed field evaluators for backend services",
    icon: "🐍",
    generates: ["types.py", "helpers.py", "computed_fields.py", "examples.py"]
  },
  {
    id: "database-schema",
    label: "Database Schema",
    description: "PostgreSQL schema with tables, columns, and formula logic",
    icon: "🗄️", 
    generates: ["schema.sql", "functions.sql", "views.sql", "triggers.sql"]
  },
  {
    id: "fullstack",
    label: "Full-Stack Package",
    description: "Complete code package for all environments",
    icon: "📦",
    generates: ["All of the above organized in folders"]
  }
]
```

### Step 2: Language-Specific Options

These appear **dynamically** based on Step 1 selection.

#### For Client Library (TypeScript/JS)

```html
□ Include helper functions (getField, setField, etc.)
□ Generate JavaScript runtime for formulas
  └─ ☑ Async data access for lookups/rollups
  └─ ☑ Include JSDoc comments
  └─ ☑ Generate usage examples
□ Include React hooks (future)
□ Output as:
  ○ Separate files (recommended)
  ○ Single bundled file
```

**Generates**:
- `types.ts` - TypeScript interfaces for all tables
- `helpers.ts` - Type-safe helper functions
- `helpers.js` - JavaScript implementation
- `examples.ts` - Usage examples
- `computed_fields.ts` - Formula runtime (if selected)

#### For Server SDK (Python)

```html
□ Include helper functions
□ Generate computed field evaluators
  └─ Data access mode:
     ○ Dataclass attributes (record.field_name)
     ○ Dictionary keys (record["field_name"]) 
     ○ ORM attributes (SQLAlchemy/Django-style)
  └─ ☑ Include type hints (PEP 484)
  └─ ☑ Include docstrings
  └─ ☑ Add null safety checks
□ Generate async version (future)
□ Type definition style:
  ○ Dataclasses (@dataclass)
  ○ TypedDict (typing.TypedDict)
  ○ Pydantic models (future)
```

**Generates**:
- `types.py` - Python types for all tables
- `helpers.py` - Helper functions for record access
- `computed_fields.py` - Formula evaluators (if selected)
- `examples.py` - Usage examples

#### For Database Schema (SQL)

```html
□ Database dialect:
  ○ PostgreSQL (recommended)
  ○ MySQL (future)
  ○ SQLite (future)
□ Column naming:
  ○ Use Airtable field IDs (fld123...)
  ○ Transform to snake_case names
□ Include formula logic as:
  ☑ Generated columns (computed at write time)
  ☑ SQL functions (computed at read time)
  ☑ Views (virtualized computed fields)
  □ Triggers (update on dependent field changes)
□ Include:
  ☑ Foreign key constraints
  ☑ Indexes for linked fields
  ☑ Comments with Airtable field names
```

**Generates**:
- `01_schema.sql` - CREATE TABLE statements
- `02_generated_columns.sql` - Formula columns (if selected)
- `03_functions.sql` - SQL functions for complex formulas
- `04_views.sql` - Convenience views with computed fields
- `05_triggers.sql` - Automatic update triggers (if selected)

#### For Full-Stack Package

```html
Generates all files with best-practice defaults.

Choose primary languages:
☑ TypeScript
☑ Python
☑ SQL

Optional additions:
□ README with setup instructions
□ Package configuration (package.json, pyproject.toml)
□ Docker configuration
□ API documentation
```

**Generates**:
```
typescript/
  ├─ types.ts
  ├─ helpers.ts
  ├─ helpers.js
  ├─ examples.ts
  └─ computed_fields.ts
python/
  ├─ types.py
  ├─ helpers.py
  ├─ computed_fields.py
  └─ examples.py
sql/
  ├─ 01_schema.sql
  ├─ 02_generated_columns.sql
  ├─ 03_functions.sql
  ├─ 04_views.sql
  └─ 05_triggers.sql
README.md
package.json
pyproject.toml
```

### Step 3: Formula Handling (Computed Fields)

This is the **critical differentiator** and deserves its own prominent section:

```html
<div class="formula-options border-2 border-blue-500 rounded-lg p-4">
  <h3>Formula & Computed Field Handling</h3>
  <p class="text-sm text-gray-600">
    Your base has X formula fields, Y lookups, Z rollups
  </p>
  
  <label>
    <input type="radio" name="formula-mode" value="skip" checked>
    Skip computed fields (types only)
  </label>
  
  <label>
    <input type="radio" name="formula-mode" value="getters">
    Include as getter methods/functions
    <div class="ml-6 mt-2" id="getter-options">
      Language: <span class="badge">[Auto-detected from Step 1]</span>
      <br>
      Evaluation mode:
      <label><input type="radio" name="eval-mode" value="simple" checked> 
        Simple (inline field references only)
      </label>
      <label><input type="radio" name="eval-mode" value="deep"> 
        Deep (fully executable formulas)
      </label>
    </div>
  </label>
  
  <label>
    <input type="radio" name="formula-mode" value="sql">
    Include in SQL schema
    <div class="ml-6 mt-2" id="sql-formula-options">
      Method:
      <label><input type="radio" name="sql-method" value="generated" checked>
        Generated columns (STORED) - faster reads, slower writes
      </label>
      <label><input type="radio" name="sql-method" value="functions">
        SQL functions - slower reads, no write cost
      </label>
      <label><input type="radio" name="sql-method" value="hybrid">
        Hybrid (simple as STORED, complex as functions)
      </label>
      <br>
      Formula complexity limit:
      <input type="range" min="0" max="10" value="3" id="depth-slider">
      <span id="depth-value">3</span>
      <p class="text-sm">Formulas deeper than this will be skipped</p>
    </div>
  </label>
  
  <label>
    <input type="radio" name="formula-mode" value="sync-service">
    Generate server-side sync service
    <div class="ml-6 mt-2 text-sm text-gray-600">
      Create a Python/Node.js service that periodically recalculates 
      all formulas and syncs back to Airtable
    </div>
    <div class="ml-6 mt-2" id="sync-options">
      Schedule: <input type="text" value="0 */6 * * *" placeholder="Cron expression">
      <br>
      <label><input type="checkbox"> Webhook support</label>
    </div>
  </label>
  
  <details class="mt-4">
    <summary class="cursor-pointer font-semibold">Advanced Options</summary>
    <div class="ml-4 mt-2">
      <label><input type="checkbox"> Optimize formula code (constant folding, CSE)</label>
      <label><input type="checkbox" checked> Include formula dependency comments</label>
      <label><input type="checkbox"> Generate unit tests for formulas</label>
      <label><input type="checkbox"> Add performance profiling hooks</label>
    </div>
  </details>
</div>
```

---

## Implementation Architecture

### File Structure

```
web/
├─ tabs/
│  └─ code_generator.py          # Main tab (rename from types_generator.py)
├─ code_generators/
│  ├─ __init__.py
│  ├─ python_runtime_generator.py    # ✅ Already exists
│  ├─ javascript_runtime_generator.py # ✅ Already exists
│  ├─ sql_runtime_generator.py       # ✅ Already exists
│  └─ workflows.py                    # NEW: Workflow classes
├─ types_generator.py            # ✅ Already exists
├─ python_helpers_generator.py   # ✅ Already exists
├─ typescript_helpers_generator.py # ✅ Already exists
└─ postgres_schema_generator.py  # ✅ Already exists
```

### Workflow Classes

Create `web/code_generators/workflows.py`:

```python
"""Code generation workflows that orchestrate multiple generators"""

from typing import Dict, Any
from abc import ABC, abstractmethod

class CodeGenerationWorkflow(ABC):
    """Base class for code generation workflows"""
    
    def __init__(self, metadata: dict, options: dict):
        self.metadata = metadata
        self.options = options
    
    @abstractmethod
    def get_options_schema(self) -> dict:
        """Return JSON schema for workflow options"""
        pass
    
    @abstractmethod
    def generate(self) -> Dict[str, str]:
        """Generate files, return {filename: content}"""
        pass
    
    def get_formula_handling_mode(self) -> str:
        """Extract formula handling preference from options"""
        return self.options.get("formula_mode", "skip")


class ClientLibraryWorkflow(CodeGenerationWorkflow):
    """Generate TypeScript/JavaScript client library"""
    
    def get_options_schema(self) -> dict:
        return {
            "include_helpers": {"type": "boolean", "default": True},
            "include_formula_runtime": {"type": "boolean", "default": False},
            "include_examples": {"type": "boolean", "default": True},
            "async_data_access": {"type": "boolean", "default": True},
            "output_mode": {"type": "string", "enum": ["separate", "bundled"], "default": "separate"},
        }
    
    def generate(self) -> Dict[str, str]:
        from types_generator import (
            generate_typescript_types,
            generate_all_typescript_files,
        )
        from code_generators.javascript_runtime_generator import generate_javascript_runtime
        
        files = {}
        
        # Always generate types
        if self.options.get("output_mode") == "separate":
            files.update(generate_all_typescript_files(
                self.metadata,
                include_helpers=self.options.get("include_helpers", True)
            ))
        else:
            # Single file mode
            files["airtable-types.ts"] = generate_typescript_types(
                self.metadata,
                include_helpers=self.options.get("include_helpers", True)
            )
        
        # Conditionally generate formula runtime
        if self.options.get("include_formula_runtime"):
            files["computed_fields.ts"] = generate_javascript_runtime(
                self.metadata,
                options={
                    "async_data_access": self.options.get("async_data_access"),
                    "include_helpers": True,
                    "include_comments": True,
                }
            )
        
        return files


class ServerSDKWorkflow(CodeGenerationWorkflow):
    """Generate Python server SDK"""
    
    def get_options_schema(self) -> dict:
        return {
            "include_helpers": {"type": "boolean", "default": True},
            "include_formula_runtime": {"type": "boolean", "default": True},
            "type_style": {"type": "string", "enum": ["dataclass", "typeddict", "pydantic"], "default": "dataclass"},
            "data_access_mode": {"type": "string", "enum": ["dataclass", "dict", "orm"], "default": "dataclass"},
            "null_checks": {"type": "boolean", "default": True},
            "include_examples": {"type": "boolean", "default": True},
        }
    
    def generate(self) -> Dict[str, str]:
        from types_generator import generate_all_python_files
        from code_generators.python_runtime_generator import generate_python_library
        
        files = {}
        use_dataclasses = self.options.get("type_style") == "dataclass"
        
        # Generate types and helpers
        files.update(generate_all_python_files(
            self.metadata,
            include_helpers=self.options.get("include_helpers"),
            use_dataclasses=use_dataclasses
        ))
        
        # Formula runtime
        if self.options.get("include_formula_runtime"):
            files["computed_fields.py"] = generate_python_library(
                self.metadata,
                options={
                    "data_access_mode": self.options.get("data_access_mode"),
                    "include_null_checks": self.options.get("null_checks"),
                    "include_types": False,  # Already in types.py
                    "include_helpers": True,
                }
            )
        
        return files


class DatabaseSchemaWorkflow(CodeGenerationWorkflow):
    """Generate SQL database schema"""
    
    def get_options_schema(self) -> dict:
        return {
            "dialect": {"type": "string", "enum": ["postgresql", "mysql", "sqlite"], "default": "postgresql"},
            "use_field_ids": {"type": "boolean", "default": False},
            "formula_mode": {"type": "string", "enum": ["skip", "generated", "functions", "hybrid", "triggers"], "default": "functions"},
            "formula_depth_limit": {"type": "integer", "default": 3, "min": 0, "max": 10},
            "include_views": {"type": "boolean", "default": True},
            "include_indexes": {"type": "boolean", "default": True},
            "include_constraints": {"type": "boolean", "default": True},
        }
    
    def generate(self) -> Dict[str, str]:
        from postgres_schema_generator import generate_postgres_schema
        from code_generators.sql_runtime_generator import generate_all_sql_files
        
        files = {}
        dialect = self.options.get("dialect", "postgresql")
        formula_mode = self.options.get("formula_mode", "functions")
        
        # Base schema (tables and basic columns)
        files["01_schema.sql"] = generate_postgres_schema(
            self.metadata,
            use_field_ids=self.options.get("use_field_ids"),
            include_formulas=(formula_mode == "generated"),
            include_indexes=self.options.get("include_indexes"),
            include_constraints=self.options.get("include_constraints"),
        )
        
        # Formula handling based on mode
        if formula_mode in ["functions", "hybrid"]:
            sql_files = generate_all_sql_files(
                self.metadata,
                mode="functions",
                dialect=dialect,
                include_formulas=True,
                include_views=self.options.get("include_views"),
            )
            files["03_functions.sql"] = sql_files.get("functions.sql", "")
            if self.options.get("include_views"):
                files["04_views.sql"] = sql_files.get("views.sql", "")
        
        if formula_mode == "triggers":
            trigger_files = generate_all_sql_files(
                self.metadata,
                mode="triggers",
                dialect=dialect,
            )
            files["05_triggers.sql"] = trigger_files.get("triggers.sql", "")
        
        return files


class FullStackWorkflow(CodeGenerationWorkflow):
    """Generate complete full-stack package"""
    
    def get_options_schema(self) -> dict:
        return {
            "include_typescript": {"type": "boolean", "default": True},
            "include_python": {"type": "boolean", "default": True},
            "include_sql": {"type": "boolean", "default": True},
            "include_readme": {"type": "boolean", "default": True},
            "include_config": {"type": "boolean", "default": True},
        }
    
    def generate(self) -> Dict[str, str]:
        files = {}
        
        # TypeScript files
        if self.options.get("include_typescript"):
            ts_workflow = ClientLibraryWorkflow(self.metadata, {
                "include_helpers": True,
                "include_formula_runtime": True,
                "include_examples": True,
            })
            for filename, content in ts_workflow.generate().items():
                files[f"typescript/{filename}"] = content
        
        # Python files
        if self.options.get("include_python"):
            py_workflow = ServerSDKWorkflow(self.metadata, {
                "include_helpers": True,
                "include_formula_runtime": True,
                "include_examples": True,
                "type_style": "dataclass",
                "data_access_mode": "dataclass",
            })
            for filename, content in py_workflow.generate().items():
                files[f"python/{filename}"] = content
        
        # SQL files
        if self.options.get("include_sql"):
            sql_workflow = DatabaseSchemaWorkflow(self.metadata, {
                "dialect": "postgresql",
                "formula_mode": "hybrid",
                "include_views": True,
                "include_indexes": True,
            })
            for filename, content in sql_workflow.generate().items():
                files[f"sql/{filename}"] = content
        
        # Package metadata
        if self.options.get("include_readme"):
            files["README.md"] = self._generate_readme()
        
        if self.options.get("include_config"):
            files["package.json"] = self._generate_package_json()
            files["pyproject.toml"] = self._generate_pyproject_toml()
        
        return files
    
    def _generate_readme(self) -> str:
        """Generate README with setup instructions"""
        base_name = self.metadata.get("name", "Airtable Base")
        return f"""# {base_name} - Generated Code Package

This package contains automatically generated code from your Airtable base schema.

## Contents

- `typescript/` - TypeScript types and helpers for frontend applications
- `python/` - Python SDK with computed field evaluators
- `sql/` - PostgreSQL schema with formula logic

## Setup

### TypeScript
```bash
cd typescript
npm install
```

### Python
```bash
cd python
pip install -r requirements.txt
```

### SQL
```bash
psql your_database < sql/01_schema.sql
psql your_database < sql/03_functions.sql
psql your_database < sql/04_views.sql
```

## Usage

See individual README files in each directory for detailed usage examples.

## Generated

This code was generated on {self._get_timestamp()} from Airtable base schema.
"""
    
    def _generate_package_json(self) -> str:
        """Generate package.json for TypeScript package"""
        import json
        return json.dumps({
            "name": f"airtable-{self._sanitize_name(self.metadata.get('name', 'base'))}",
            "version": "1.0.0",
            "description": "Generated TypeScript types from Airtable",
            "main": "typescript/types.ts",
            "types": "typescript/types.ts",
            "scripts": {
                "build": "tsc",
                "test": "jest"
            },
            "keywords": ["airtable", "typescript", "types"],
            "author": "",
            "license": "MIT"
        }, indent=2)
    
    def _generate_pyproject_toml(self) -> str:
        """Generate pyproject.toml for Python package"""
        name = self._sanitize_name(self.metadata.get("name", "base"))
        return f"""[project]
name = "airtable-{name}"
version = "1.0.0"
description = "Generated Python types and SDK from Airtable"
requires-python = ">=3.10"
dependencies = [
    "typing-extensions>=4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "mypy>=1.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    
    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid package name"""
        import re
        return re.sub(r'[^a-z0-9-]', '-', name.lower())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

---

## Smart Defaults

Provide excellent defaults that work for 80% of use cases:

```python
DEFAULT_OPTIONS = {
    "client-library": {
        "include_helpers": True,
        "include_formula_runtime": False,  # Advanced feature
        "include_examples": True,
        "async_data_access": True,
        "output_mode": "separate",
    },
    "server-sdk": {
        "include_helpers": True,
        "include_formula_runtime": True,
        "type_style": "dataclass",
        "data_access_mode": "dataclass",
        "null_checks": True,
        "include_examples": True,
    },
    "database-schema": {
        "dialect": "postgresql",
        "formula_mode": "functions",  # Safest default
        "use_field_ids": False,  # More readable
        "include_views": True,
        "include_indexes": True,
        "include_constraints": True,
    },
    "fullstack": {
        "include_typescript": True,
        "include_python": True,
        "include_sql": True,
        "include_readme": True,
        "include_config": True,
    },
}
```

---

## UI/UX Patterns

### Progressive Disclosure

```javascript
// script.js additions
function onWorkflowChange(workflowId) {
  // Hide all option groups
  document.querySelectorAll('.workflow-options').forEach(el => {
    el.classList.add('hidden');
  });
  
  // Show relevant group
  document.getElementById(`options-${workflowId}`).classList.remove('hidden');
  
  // Update preview of what will be generated
  updateGenerationPreview(workflowId);
}

function updateGenerationPreview(workflowId) {
  const workflow = WORKFLOWS[workflowId];
  const fileList = workflow.generates.map(f => `• ${f}`).join('\n');
  document.getElementById('generation-preview').innerHTML = `
    <div class="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
      <h4 class="font-semibold mb-2">Will generate:</h4>
      <pre class="text-sm">${fileList}</pre>
    </div>
  `;
}
```

### File Tree Visualization

After generation, show an interactive file tree:

```html
<div id="generated-files" class="mt-6">
  <div class="flex justify-between items-center mb-4">
    <h3 class="text-xl font-bold">Generated Files</h3>
    <button onclick="downloadAllAsZip()" class="btn-primary">
      📦 Download All (.zip)
    </button>
  </div>
  
  <div class="file-tree">
    <!-- Collapsible folder structure -->
    <div class="folder">
      <div class="folder-header" onclick="toggleFolder(this)">
        📁 typescript/
      </div>
      <div class="folder-contents">
        <div class="file" onclick="previewFile('typescript/types.ts')">
          📄 types.ts <span class="file-size">12.3 KB</span>
        </div>
        <div class="file" onclick="previewFile('typescript/helpers.ts')">
          📄 helpers.ts <span class="file-size">8.1 KB</span>
        </div>
      </div>
    </div>
  </div>
  
  <!-- File preview pane -->
  <div id="file-preview" class="mt-4">
    <!-- Code preview with syntax highlighting -->
  </div>
</div>
```

---

## Advanced Features (Phase 2+)

### Configuration Templates

```javascript
// Allow users to save/load configurations
function saveConfig() {
  const config = {
    workflow: selectedWorkflow,
    options: getFormValues(),
    timestamp: Date.now(),
  };
  localStorage.setItem('code-gen-config', JSON.stringify(config));
  showToast('Configuration saved');
}

function loadConfig() {
  const config = JSON.parse(localStorage.getItem('code-gen-config'));
  applyConfig(config);
}

// Shareable config via URL
function shareConfig() {
  const config = btoa(JSON.stringify(getConfig()));
  const url = `${window.location.href}?config=${config}`;
  copyToClipboard(url);
  showToast('Shareable link copied');
}
```

### Comparison Mode

Generate with different options and compare side-by-side:

```
┌─────────────────┬─────────────────┐
│ Config A        │ Config B        │
│ (Dataclasses)   │ (TypedDict)     │
├─────────────────┼─────────────────┤
│ @dataclass      │ class User(     │
│ class User:     │   TypedDict):   │
│   name: str     │   name: str     │
└─────────────────┴─────────────────┘
```

### Formula Visualization

Before generating, show which formulas will be included/excluded:

```
Formula Analysis:
  ✅ 12 formulas (depth 0-2) → Will generate
  ⚠️  3 formulas (depth 3-4) → Optional (check box to include)
  ❌ 1 formula (depth 5+) → Too complex, skipped
  
[View Formula Dependency Graph]
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Rename `web/tabs/types_generator.py` → `web/tabs/code_generator.py`
- [ ] Create `web/code_generators/workflows.py` with workflow classes
- [ ] Implement workflow selector UI in HTML
- [ ] Wire up existing generators to new workflows
- [ ] Ensure backward compatibility with existing functionality

### Phase 2: Enhanced UI (Week 3-4)
- [ ] Implement progressive disclosure (show/hide option groups)
- [ ] Add formula handling options section
- [ ] Create generation preview component
- [ ] Build file tree visualization
- [ ] Add individual file download buttons

### Phase 3: Full-Stack Workflow (Week 5)
- [ ] Implement `FullStackWorkflow` class
- [ ] Generate README.md
- [ ] Generate package.json / pyproject.toml
- [ ] Add ZIP download functionality
- [ ] Test with real-world bases

### Phase 4: Polish & Documentation (Week 6-7)
- [ ] Add configuration save/load
- [ ] Create user documentation
- [ ] Add tooltips and help text
- [ ] Implement comparison mode (future)
- [ ] Performance optimization

### Phase 5: Advanced Features (Week 8+)
- [ ] Formula optimization options
- [ ] Unit test generation
- [ ] Performance profiling hooks
- [ ] Shareable configuration URLs
- [ ] Template library

---

## Migration Strategy

### Backward Compatibility

Current "Types Generator" tab will be renamed but maintain all existing functionality:

- All existing options work as before
- New workflows are additions, not replacements
- Users with bookmarks to old tab see same interface
- Add deprecation notice: "This tab has been renamed to Code Generator"

### URL Routing

```javascript
// Handle legacy URLs
if (window.location.hash === '#types-generator') {
  window.location.hash = '#code-generator';
}
```

---

## Key Decisions Summary

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Tab Count** | 1 unified tab | Simpler UX, progressive disclosure |
| **Primary Selector** | Workflow-based (use case) | Users think in terms of what they're building |
| **Formula Options** | Separate section (Step 3) | Complex enough to deserve dedicated space |
| **Defaults** | Opinionated, best-practice | 80% of users can just click "Generate" |
| **File Organization** | Folder structure for full-stack | Mirrors real project structure |
| **Download Format** | Individual + ZIP all | Flexibility for different use cases |
| **Backward Compatibility** | Full compatibility | Don't break existing users |

---

## Success Metrics

- ✅ **Usage**: 80%+ of code generations use workflow selector (not legacy mode)
- ✅ **Satisfaction**: Users can generate production-ready code in < 2 minutes
- ✅ **Completeness**: Full-stack workflow generates deployable package
- ✅ **Flexibility**: Power users can customize all aspects via options
- ✅ **Reliability**: Generated code compiles/runs without errors 95%+ of time

---

## Open Questions

1. **Should we support custom formula functions?**
   - User-defined functions in Airtable scripts
   - How to transpile these?

2. **How to handle Airtable-specific types?**
   - Attachments, barcodes, buttons
   - May not have direct equivalents in all platforms

3. **Should we generate tests for the generated code?**
   - Property-based tests?
   - Sample data generation?

4. **How to handle formula versioning?**
   - If Airtable formula changes, regenerate code?
   - Migration strategy?

5. **Should we support incremental updates?**
   - Generate only changed formulas?
   - Merge with existing generated code?

---

## Related Documents

- [formula-runtime-design.md](formula-runtime-design.md) - Detailed formula runtime architecture
- [phase1-complete.md](phase1-complete.md) - Initial parser implementation
- [phase2-complete.md](phase2-complete.md) - Python transpiler implementation
- [phase3-complete.md](phase3-complete.md) - JavaScript transpiler implementation
- [phase4-complete.md](phase4-complete.md) - SQL generator implementation
- [phase5-complete.md](phase5-complete.md) - Advanced features implementation

---

## Conclusion

This unified Code Generator design provides:

1. **Simplicity**: One tab, four workflows, smart defaults
2. **Power**: All existing capabilities exposed through clean interface
3. **Flexibility**: Progressive disclosure reveals advanced options
4. **Scalability**: Workflow architecture allows easy addition of new languages/modes
5. **User-Centric**: Organized by what users are building, not technical architecture

The workflow-based approach makes it immediately clear to users what this tool can do for them, while the progressive disclosure pattern ensures power users aren't constrained.
