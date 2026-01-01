"""Tests for Python helpers generator"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from python_helpers_generator import generate_python_helpers


def test_generate_python_helpers_dataclass():
    """Test generating Python helpers with dataclass types"""
    metadata = {
        "tables": [
            {
                "id": "tblTest123",
                "name": "Tasks",
                "fields": [
                    {"id": "fldName001", "name": "Name", "type": "singleLineText"},
                    {"id": "fldStatus001", "name": "Status", "type": "singleSelect"},
                ],
            }
        ]
    }
    
    result = generate_python_helpers(metadata, use_dataclasses=True)
    
    # Check for key components
    assert "from .types import *" in result
    assert "class ATRecord(Protocol):" in result
    assert "def get_field_id" in result
    assert "def get_field" in result
    assert "def set_field" in result
    assert "def get_fields" in result
    assert "def has_field" in result
    assert "def create_update" in result
    assert "def is_record" in result
    assert "def extract_fields" in result


def test_generate_python_helpers_typeddict():
    """Test generating Python helpers with TypedDict types"""
    metadata = {
        "tables": [
            {
                "id": "tblTest123",
                "name": "Tasks",
                "fields": [
                    {"id": "fldName001", "name": "Name", "type": "singleLineText"},
                ],
            }
        ]
    }
    
    result = generate_python_helpers(metadata, use_dataclasses=False)
    
    # Check for TypedDict-specific syntax
    assert "class ATRecord(TypedDict" in result
    assert "def get_field_id" in result


def test_generate_python_helpers_multiple_tables():
    """Test generating helpers for multiple tables"""
    metadata = {
        "tables": [
            {
                "id": "tblTest1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            },
            {
                "id": "tblTest2",
                "name": "Projects",
                "fields": [{"id": "fld2", "name": "Title", "type": "singleLineText"}],
            },
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check for both table names
    assert '"Tasks"' in result
    assert '"Projects"' in result
    assert "TableName = Literal[" in result


def test_python_helpers_wrapper_classes():
    """Test that wrapper classes are generated for each table"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check for wrapper class
    assert "class TasksRecord:" in result
    assert "def get(self, field_name: str" in result
    assert "def set(self, field_name: str" in result
    assert "def has(self, field_name: str" in result
    assert "def to_dict(self)" in result
    assert "def fields(self)" in result


def test_python_helpers_field_mappings():
    """Test that field ID mappings are properly referenced"""
    metadata = {
        "tables": [
            {
                "id": "tblTest",
                "name": "Tasks",
                "fields": [
                    {"id": "fld1", "name": "Name", "type": "singleLineText"},
                    {"id": "fld2", "name": "Status", "type": "singleSelect"},
                ],
            }
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check for field mapping dictionaries
    assert "FIELD_ID_MAPPINGS: Dict[str, Dict[str, str]]" in result
    assert "FIELD_NAME_MAPPINGS: Dict[str, Dict[str, str]]" in result
    assert "Tasks_FIELD_ID_MAPPING" in result


def test_python_helpers_convenience_functions():
    """Test that convenience functions are generated"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check for convenience function
    assert "def create_tasks_record(" in result
    assert "TasksRecord(record)" in result


def test_python_helpers_empty_tables():
    """Test generating helpers with empty tables list"""
    metadata = {"tables": []}
    
    result = generate_python_helpers(metadata)
    
    # Should still generate valid Python code
    assert "def get_field_id" in result
    assert "TableName = Literal[" in result


def test_python_helpers_sanitize_names():
    """Test that table names with spaces are sanitized"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Project Tasks",
                "fields": [{"id": "fld1", "name": "Task Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check that sanitized name is used
    assert "class Project_TasksRecord:" in result
    assert "def create_project_tasks_record(" in result


def test_python_helpers_exports():
    """Test that __all__ exports are properly defined"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_python_helpers(metadata)
    
    # Check for exports
    assert "__all__ = [" in result
    assert '"Tasks"' in result
    assert '"get_field_id"' in result
    assert '"set_field"' in result


def test_python_helpers_record_protocol():
    """Test that ATRecord protocol/TypedDict is properly defined"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    # Test with dataclass
    result_dataclass = generate_python_helpers(metadata, use_dataclasses=True)
    assert "class ATRecord(Protocol):" in result_dataclass
    assert "id: str" in result_dataclass
    
    # Test with TypedDict
    result_typeddict = generate_python_helpers(metadata, use_dataclasses=False)
    assert "class ATRecord(TypedDict" in result_typeddict
