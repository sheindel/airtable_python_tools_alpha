"""Code generation workflows that orchestrate multiple generators"""

from typing import Dict, Any
from abc import ABC, abstractmethod
import sys
import json
from datetime import datetime
import re

sys.path.append("web")


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
        from code_generators.javascript_runtime_generator import generate_javascript_library
        
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
            files["computed_fields.js"] = generate_javascript_library(
                self.metadata,
                options={
                    "data_access_mode": "object",
                    "use_typescript": False,
                    "module_format": "esm",
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
        from postgres_schema_generator import generate_schema
        from code_generators.sql_runtime_generator import generate_all_sql_files
        
        files = {}
        dialect = self.options.get("dialect", "postgresql")
        formula_mode = self.options.get("formula_mode", "functions")
        
        # Base schema (tables and basic columns)
        naming_mode = "field_ids" if self.options.get("use_field_ids") else "field_names"
        files["01_schema.sql"] = generate_schema(
            self.metadata,
            naming_mode=naming_mode,
            include_formulas_as_generated=(formula_mode == "generated"),
            formula_max_depth=self.options.get("formula_depth_limit", 2),
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
            # generate_all_sql_files returns a single file with functions and views combined
            combined_content = sql_files.get("airtable_computed_functions.sql", "")
            files["03_functions.sql"] = combined_content
            # Note: Views are included in 03_functions.sql when include_views=True
        
        if formula_mode == "triggers":
            trigger_files = generate_all_sql_files(
                self.metadata,
                mode="triggers",
                dialect=dialect,
            )
            files["05_triggers.sql"] = trigger_files.get("airtable_computed_triggers.sql", "")
        
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
```

## Usage

See individual README files in each directory for detailed usage examples.

## Generated

This code was generated on {self._get_timestamp()} from Airtable base schema.
"""
    
    def _generate_package_json(self) -> str:
        """Generate package.json for TypeScript package"""
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
        return re.sub(r'[^a-z0-9-]', '-', name.lower())
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Workflow registry for easy access
WORKFLOWS = {
    "client-library": ClientLibraryWorkflow,
    "server-sdk": ServerSDKWorkflow,
    "database-schema": DatabaseSchemaWorkflow,
    "fullstack": FullStackWorkflow,
}


# Default options for each workflow
DEFAULT_OPTIONS = {
    "client-library": {
        "include_helpers": True,
        "include_formula_runtime": False,
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
        "formula_mode": "functions",
        "use_field_ids": False,
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


def create_workflow(workflow_id: str, metadata: dict, options: dict = None) -> CodeGenerationWorkflow:
    """
    Factory function to create a workflow instance
    
    Args:
        workflow_id: The workflow identifier (e.g., "client-library")
        metadata: Airtable metadata dictionary
        options: Workflow options (uses defaults if not provided)
    
    Returns:
        Workflow instance
    
    Raises:
        ValueError: If workflow_id is not recognized
    """
    if workflow_id not in WORKFLOWS:
        raise ValueError(f"Unknown workflow: {workflow_id}. Available: {list(WORKFLOWS.keys())}")
    
    # Merge provided options with defaults
    final_options = DEFAULT_OPTIONS.get(workflow_id, {}).copy()
    if options:
        final_options.update(options)
    
    workflow_class = WORKFLOWS[workflow_id]
    return workflow_class(metadata, final_options)
