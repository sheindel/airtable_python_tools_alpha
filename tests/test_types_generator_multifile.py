"""Tests for types generator multi-file generation"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from types_generator import (
    generate_all_typescript_files,
    generate_all_python_files,
)


def test_generate_all_typescript_files():
    """Test generating all TypeScript files at once"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [
                    {"id": "fld1", "name": "Name", "type": "singleLineText"},
                    {"id": "fld2", "name": "Status", "type": "singleSelect"},
                ],
            }
        ]
    }
    
    files = generate_all_typescript_files(metadata, include_helpers=True)
    
    # Check that all expected files are present
    assert "types.ts" in files
    assert "helpers.ts" in files
    assert "helpers.js" in files
    
    # Check types.ts content
    assert "export interface Tasks" in files["types.ts"]
    assert "IAirtableAttachment" in files["types.ts"]
    
    # Check helpers.ts content
    assert "export function getFieldId" in files["helpers.ts"]
    assert "export type ATRecord" in files["helpers.ts"]
    
    # Check helpers.js content
    assert "export function getFieldId" in files["helpers.js"]
    assert "const FIELD_ID_MAPPINGS" in files["helpers.js"]


def test_generate_all_typescript_files_no_helpers():
    """Test generating TypeScript files without helper types"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    files = generate_all_typescript_files(metadata, include_helpers=False)
    
    # Check that files are still generated
    assert "types.ts" in files
    assert "helpers.ts" in files
    assert "helpers.js" in files
    
    # Types file should not have helper interfaces
    assert "IAirtableAttachment" not in files["types.ts"]


def test_generate_all_python_files_dataclass():
    """Test generating all Python files with dataclasses"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [
                    {"id": "fld1", "name": "Name", "type": "singleLineText"},
                    {"id": "fld2", "name": "Done", "type": "checkbox"},
                ],
            }
        ]
    }
    
    files = generate_all_python_files(metadata, include_helpers=True, use_dataclasses=True)
    
    # Check that both files are present
    assert "types.py" in files
    assert "helpers.py" in files
    
    # Check types.py content
    assert "@dataclass" in files["types.py"]
    assert "class Tasks:" in files["types.py"]
    
    # Check helpers.py content
    assert "def get_field_id" in files["helpers.py"]
    assert "class TasksRecord:" in files["helpers.py"]
    assert "class ATRecord(Protocol):" in files["helpers.py"]


def test_generate_all_python_files_typeddict():
    """Test generating all Python files with TypedDict"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Projects",
                "fields": [{"id": "fld1", "name": "Title", "type": "singleLineText"}],
            }
        ]
    }
    
    files = generate_all_python_files(metadata, include_helpers=True, use_dataclasses=False)
    
    # Check that both files are present
    assert "types.py" in files
    assert "helpers.py" in files
    
    # Check types.py content
    assert "class Projects(TypedDict):" in files["types.py"]
    assert "@dataclass" not in files["types.py"]
    
    # Check helpers.py content
    assert "def get_field_id" in files["helpers.py"]
    assert "class ATRecord(TypedDict" in files["helpers.py"]


def test_generate_all_files_multiple_tables():
    """Test generating files with multiple tables"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            },
            {
                "id": "tbl2",
                "name": "Projects",
                "fields": [{"id": "fld2", "name": "Title", "type": "singleLineText"}],
            },
            {
                "id": "tbl3",
                "name": "Users",
                "fields": [{"id": "fld3", "name": "Email", "type": "email"}],
            },
        ]
    }
    
    # Test TypeScript
    ts_files = generate_all_typescript_files(metadata)
    assert "'Tasks'" in ts_files["helpers.ts"]
    assert "'Projects'" in ts_files["helpers.ts"]
    assert "'Users'" in ts_files["helpers.ts"]
    
    # Test Python
    py_files = generate_all_python_files(metadata)
    assert '"Tasks"' in py_files["helpers.py"]
    assert '"Projects"' in py_files["helpers.py"]
    assert '"Users"' in py_files["helpers.py"]


def test_typescript_files_consistency():
    """Test that TypeScript files reference each other correctly"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    files = generate_all_typescript_files(metadata)
    
    # helpers.ts should import from types.ts
    assert "import * as Types from './types'" in files["helpers.ts"]
    
    # helpers.js should import from types.js
    assert "import * as Types from './types.js'" in files["helpers.js"]
    
    # types.ts should export interfaces
    assert "export interface Tasks" in files["types.ts"]


def test_python_files_consistency():
    """Test that Python files reference each other correctly"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    files = generate_all_python_files(metadata)
    
    # helpers.py should import from types.py
    assert "from .types import *" in files["helpers.py"]
    
    # types.py should define classes
    assert "class Tasks" in files["types.py"]


def test_empty_metadata():
    """Test generating files with empty metadata"""
    metadata = {"tables": []}
    
    # TypeScript should still generate valid files
    ts_files = generate_all_typescript_files(metadata)
    assert len(ts_files) == 3
    assert "export function getFieldId" in ts_files["helpers.ts"]
    
    # Python should still generate valid files
    py_files = generate_all_python_files(metadata)
    assert len(py_files) == 2
    assert "def get_field_id" in py_files["helpers.py"]
