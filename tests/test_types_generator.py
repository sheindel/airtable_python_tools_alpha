"""Tests for types_generator module"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from types_generator import (
    generate_typescript_types,
    generate_python_types,
    _get_typescript_type,
    _get_python_type,
    _is_required_field,
    _sanitize_name,
)
from constants import (
    FIELD_TYPE_TEXT,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_RECORD_LINKS,
    FIELD_TYPE_FORMULA,
)


def test_sanitize_name():
    """Test name sanitization for identifiers"""
    assert _sanitize_name("My Field") == "My_Field"
    assert _sanitize_name("field-name") == "field_name"
    assert _sanitize_name("Field (test)") == "Field_test"
    assert _sanitize_name("123Field") == "_123Field"
    assert _sanitize_name("Field@Name") == "FieldName"


def test_is_required_field():
    """Test required field detection"""
    # Primary field is required
    assert _is_required_field({"isPrimary": True}) == True
    
    # Count field is required
    assert _is_required_field({"type": "count"}) == True
    
    # Created time is required
    assert _is_required_field({"type": "createdTime"}) == True
    
    # Regular field is optional
    assert _is_required_field({"type": "singleLineText"}) == False


def test_get_typescript_type_basic():
    """Test TypeScript type mapping for basic fields"""
    # Text field
    field = {"type": FIELD_TYPE_TEXT}
    assert _get_typescript_type(field) == "string"
    
    # Number field
    field = {"type": FIELD_TYPE_NUMBER}
    assert _get_typescript_type(field) == "number"
    
    # Checkbox field
    field = {"type": FIELD_TYPE_CHECKBOX}
    assert _get_typescript_type(field) == "boolean"
    
    # Record links
    field = {"type": FIELD_TYPE_RECORD_LINKS}
    assert _get_typescript_type(field) == "Array<string>"


def test_get_typescript_type_single_select():
    """Test TypeScript type for single select fields"""
    field = {
        "type": FIELD_TYPE_SELECT,
        "options": {
            "choices": [
                {"name": "Option 1"},
                {"name": "Option 2"},
                {"name": "Option 3"},
            ]
        }
    }
    result = _get_typescript_type(field)
    assert result == "'Option 1' | 'Option 2' | 'Option 3'"


def test_get_typescript_type_multiple_selects():
    """Test TypeScript type for multiple select fields"""
    field = {
        "type": FIELD_TYPE_MULTI_SELECT,
        "options": {
            "choices": [
                {"name": "Tag A"},
                {"name": "Tag B"},
            ]
        }
    }
    result = _get_typescript_type(field)
    assert result == "Array<'Tag A' | 'Tag B'>"


def test_get_typescript_type_formula():
    """Test TypeScript type for formula fields"""
    # Formula returning number
    field = {
        "type": FIELD_TYPE_FORMULA,
        "options": {
            "result": {"type": FIELD_TYPE_NUMBER}
        }
    }
    assert _get_typescript_type(field) == "number"
    
    # Formula without result type defaults to string
    field = {"type": FIELD_TYPE_FORMULA}
    assert _get_typescript_type(field) == "string"


def test_get_python_type_basic():
    """Test Python type mapping for basic fields"""
    # Text field
    field = {"type": FIELD_TYPE_TEXT}
    assert _get_python_type(field) == "str"
    
    # Number field
    field = {"type": FIELD_TYPE_NUMBER}
    assert _get_python_type(field) == "float"
    
    # Checkbox field
    field = {"type": FIELD_TYPE_CHECKBOX}
    assert _get_python_type(field) == "bool"


def test_get_python_type_single_select():
    """Test Python type for single select fields"""
    field = {
        "type": FIELD_TYPE_SELECT,
        "options": {
            "choices": [
                {"name": "A"},
                {"name": "B"},
            ]
        }
    }
    result = _get_python_type(field)
    assert result == "Literal['A', 'B']"


def test_get_python_type_multiple_selects():
    """Test Python type for multiple select fields"""
    field = {
        "type": FIELD_TYPE_MULTI_SELECT,
        "options": {
            "choices": [
                {"name": "X"},
                {"name": "Y"},
            ]
        }
    }
    result = _get_python_type(field)
    assert result == "List[Literal['X', 'Y']]"


def test_generate_typescript_types():
    """Test full TypeScript type generation"""
    metadata = {
        "tables": [
            {
                "name": "Users",
                "id": "tblXXX",
                "fields": [
                    {
                        "id": "fldName",
                        "name": "Name",
                        "type": FIELD_TYPE_TEXT,
                        "isPrimary": True,
                    },
                    {
                        "id": "fldAge",
                        "name": "Age",
                        "type": FIELD_TYPE_NUMBER,
                    },
                    {
                        "id": "fldActive",
                        "name": "Active",
                        "type": FIELD_TYPE_CHECKBOX,
                    },
                ]
            }
        ]
    }
    
    result = generate_typescript_types(metadata, include_helpers=False)
    
    # Check for interface definition
    assert "export interface Users extends FieldSet {" in result
    
    # Check for required field (no ?)
    assert "'Name': string" in result
    
    # Check for optional fields (with ?)
    assert "'Age'?: number" in result
    assert "'Active'?: boolean" in result
    
    # Check for field ID mapping
    assert "export const UsersFieldIdMapping = {" in result
    assert "'Name': 'fldName'," in result
    assert "'Age': 'fldAge'," in result


def test_generate_typescript_types_with_helpers():
    """Test TypeScript generation includes helper types"""
    metadata = {"tables": []}
    
    result = generate_typescript_types(metadata, include_helpers=True)
    
    # Check for helper types
    assert "export interface IAirtableThumbnail {" in result
    assert "export interface IAirtableAttachment {" in result
    assert "export interface IAirtableCollaborator {" in result


def test_generate_python_types_dataclass():
    """Test Python dataclass generation"""
    metadata = {
        "tables": [
            {
                "name": "Products",
                "id": "tblProd",
                "fields": [
                    {
                        "id": "fldName",
                        "name": "Product Name",
                        "type": FIELD_TYPE_TEXT,
                        "isPrimary": True,
                    },
                    {
                        "id": "fldPrice",
                        "name": "Price",
                        "type": FIELD_TYPE_NUMBER,
                    },
                ]
            }
        ]
    }
    
    result = generate_python_types(metadata, include_helpers=False, use_dataclasses=True)
    
    # Check for dataclass decorator
    assert "@dataclass" in result
    
    # Check for class definition with sanitized name
    assert "class Products:" in result
    
    # Check for required field (in snake_case for dataclasses)
    assert "product_name: str" in result
    
    # Check for optional field (in snake_case for dataclasses)
    assert "price: Optional[float] = None" in result
    
    # Check for field ID mapping (uses snake_case for dataclasses)
    assert "Products_FIELD_ID_MAPPING = {" in result
    assert "'product_name': 'fldName'," in result
    
    # Check for reverse mapping (uses snake_case for dataclasses)
    assert "Products_FIELD_NAME_MAPPING = {" in result
    assert "'fldName': 'product_name'," in result


def test_generate_python_types_typeddict():
    """Test Python TypedDict generation"""
    metadata = {
        "tables": [
            {
                "name": "Tasks",
                "id": "tblTask",
                "fields": [
                    {
                        "id": "fldTitle",
                        "name": "Title",
                        "type": FIELD_TYPE_TEXT,
                        "isPrimary": True,
                    },
                    {
                        "id": "fldComplete",
                        "name": "Complete",
                        "type": FIELD_TYPE_CHECKBOX,
                    },
                ]
            }
        ]
    }
    
    result = generate_python_types(metadata, include_helpers=False, use_dataclasses=False)
    
    # Check for TypedDict class
    assert "class Tasks(TypedDict):" in result
    
    # Check for required field
    assert "Title: str" in result
    
    # Check for optional field with NotRequired
    assert "Complete: NotRequired[bool]" in result


def test_generate_python_types_with_helpers():
    """Test Python generation includes helper types"""
    metadata = {"tables": []}
    
    result = generate_python_types(metadata, include_helpers=True, use_dataclasses=True)
    
    # Check for helper types
    assert "class AirtableThumbnail:" in result
    assert "class AirtableAttachment:" in result
    assert "class AirtableCollaborator:" in result
