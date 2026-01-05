"""Utilities for loading test schemas.

Supports loading schemas from multiple sources:
- Default schemas in repository (demo_base_schema.json, etc.)
- External schemas in tests/schemas/ directory (gitignored)
- Environment variable SCHEMA_PATH

This allows testing with large, real-world schemas without committing them to git.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List


class SchemaLoader:
    """Helper for loading Airtable schemas for testing"""
    
    # Default schemas in repo
    REPO_ROOT = Path(__file__).parent.parent
    DEFAULT_SCHEMAS = {
        "demo": REPO_ROOT / "demo_base_schema.json",
        "crm": REPO_ROOT / "crm_schema.json",
        "issues": REPO_ROOT / "issues_schema.json",
        "blog": REPO_ROOT / "blog_metadata.json",
    }
    
    # External schemas directory (gitignored)
    EXTERNAL_DIR = Path(__file__).parent / "schemas"
    
    @classmethod
    def load(cls, schema_name: str = "demo") -> Dict[str, Any]:
        """
        Load a schema by name.
        
        Priority:
        1. Environment variable SCHEMA_PATH (if set)
        2. External schema in tests/schemas/{schema_name}.json
        3. Default schema from repo
        
        Args:
            schema_name: Name of the schema to load (e.g., "demo", "crm")
        
        Returns:
            Airtable metadata dictionary
        
        Raises:
            FileNotFoundError: If schema not found
        """
        # Check environment variable
        env_path = os.environ.get("SCHEMA_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return cls._load_file(path)
            else:
                raise FileNotFoundError(f"Schema path from SCHEMA_PATH not found: {env_path}")
        
        # Check external directory
        external_path = cls.EXTERNAL_DIR / f"{schema_name}.json"
        if external_path.exists():
            return cls._load_file(external_path)
        
        # Check default schemas
        if schema_name in cls.DEFAULT_SCHEMAS:
            default_path = cls.DEFAULT_SCHEMAS[schema_name]
            if default_path.exists():
                return cls._load_file(default_path)
        
        raise FileNotFoundError(
            f"Schema '{schema_name}' not found. Searched:\n"
            f"  - Environment: SCHEMA_PATH\n"
            f"  - External: {external_path}\n"
            f"  - Default: {cls.DEFAULT_SCHEMAS.get(schema_name, 'N/A')}"
        )
    
    @classmethod
    def load_from_path(cls, path: str) -> Dict[str, Any]:
        """
        Load schema from a specific file path.
        
        Args:
            path: Path to JSON schema file
        
        Returns:
            Airtable metadata dictionary
        """
        return cls._load_file(Path(path))
    
    @classmethod
    def _load_file(cls, path: Path) -> Dict[str, Any]:
        """Load and validate JSON schema file"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation
        if not isinstance(data, dict):
            raise ValueError(f"Invalid schema format in {path}: expected dict, got {type(data)}")
        
        if "tables" not in data:
            raise ValueError(f"Invalid schema format in {path}: missing 'tables' key")
        
        return data
    
    @classmethod
    def list_available_schemas(cls) -> Dict[str, List[str]]:
        """
        List all available schemas.
        
        Returns:
            Dictionary with 'default' and 'external' lists
        """
        result = {
            "default": list(cls.DEFAULT_SCHEMAS.keys()),
            "external": []
        }
        
        # Scan external directory
        if cls.EXTERNAL_DIR.exists():
            for file in cls.EXTERNAL_DIR.glob("*.json"):
                result["external"].append(file.stem)
        
        return result
    
    @classmethod
    def get_schema_info(cls, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary information about a schema.
        
        Args:
            metadata: Airtable metadata dictionary
        
        Returns:
            Dictionary with schema statistics
        """
        stats = {
            "id": metadata.get("id", "Unknown"),
            "name": metadata.get("name", "Unknown"),
            "tables": len(metadata.get("tables", [])),
            "total_fields": 0,
            "field_types": {},
        }
        
        for table in metadata.get("tables", []):
            fields = table.get("fields", [])
            stats["total_fields"] += len(fields)
            
            for field in fields:
                field_type = field.get("type", "unknown")
                stats["field_types"][field_type] = stats["field_types"].get(field_type, 0) + 1
        
        return stats
    
    @classmethod
    def save_external_schema(cls, metadata: Dict[str, Any], name: str) -> Path:
        """
        Save a schema to the external directory.
        
        Args:
            metadata: Airtable metadata dictionary
            name: Name for the schema file (without .json extension)
        
        Returns:
            Path to saved file
        """
        cls.EXTERNAL_DIR.mkdir(exist_ok=True)
        path = cls.EXTERNAL_DIR / f"{name}.json"
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return path


def load_demo_schema() -> Dict[str, Any]:
    """Load the default demo schema (convenience function)"""
    return SchemaLoader.load("demo")


def load_crm_schema() -> Dict[str, Any]:
    """Load the CRM schema (convenience function)"""
    return SchemaLoader.load("crm")


def load_test_schema(name: str = "demo") -> Dict[str, Any]:
    """
    Load a test schema by name (convenience function).
    
    Args:
        name: Schema name or "demo" for default
    
    Returns:
        Airtable metadata dictionary
    """
    return SchemaLoader.load(name)
