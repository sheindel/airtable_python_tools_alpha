"""Tests for TypeScript helpers generator"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from typescript_helpers_generator import (
    generate_typescript_helpers,
    generate_typescript_helpers_js,
)


def test_generate_typescript_helpers_basic():
    """Test generating TypeScript helpers with basic metadata"""
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
    
    result = generate_typescript_helpers(metadata)
    
    # Check for key components
    assert "import * as Types from './types'" in result
    assert "export type TableName = 'Tasks'" in result
    assert "export function getFieldId" in result
    assert "export function getField" in result
    assert "export function setField" in result
    assert "export function getFields" in result
    assert "export function hasField" in result
    assert "export function createUpdate" in result
    assert "export function isRecord" in result
    assert "export function fromAirtableRecord" in result


def test_generate_typescript_helpers_multiple_tables():
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
    
    result = generate_typescript_helpers(metadata)
    
    # Check for both table names
    assert "'Tasks'" in result
    assert "'Projects'" in result
    assert "export type TableName = 'Tasks' | 'Projects'" in result


def test_generate_typescript_helpers_js_basic():
    """Test generating JavaScript implementation"""
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
    
    result = generate_typescript_helpers_js(metadata)
    
    # Check for key JavaScript functions
    assert "export function getFieldId" in result
    assert "export function getField" in result
    assert "export function setField" in result
    assert "export function hasField" in result
    assert "const FIELD_ID_MAPPINGS" in result
    assert "'Tasks'" in result


def test_generate_typescript_helpers_empty_tables():
    """Test generating helpers with empty tables list"""
    metadata = {"tables": []}
    
    result = generate_typescript_helpers(metadata)
    
    # Should still generate valid TypeScript
    assert "export function getFieldId" in result
    assert "export type TableName" in result


def test_typescript_helpers_field_id_mapping():
    """Test that field ID mappings are included"""
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
    
    result = generate_typescript_helpers(metadata)
    
    # Check that field ID mapping type is referenced
    assert "FieldIdMappings" in result
    assert "Tasks" in result


def test_typescript_helpers_atrecord_type():
    """Test that ATRecord type is properly defined"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_typescript_helpers(metadata)
    
    # Check for ATRecord type definition
    assert "export type ATRecord" in result
    assert "id: string" in result
    assert "_table?: string" in result
    assert "_rawFields?: Record<string, any>" in result


def test_typescript_js_field_operations():
    """Test JavaScript field operation functions"""
    metadata = {
        "tables": [
            {
                "id": "tbl1",
                "name": "Tasks",
                "fields": [{"id": "fld1", "name": "Name", "type": "singleLineText"}],
            }
        ]
    }
    
    result = generate_typescript_helpers_js(metadata)
    
    # Check for all key operations
    assert "export function getFields" in result
    assert "export function createUpdate" in result
    assert "export function isRecord" in result
    assert "export function fromAirtableRecord" in result
    assert "export function fromAirtableRecords" in result
    assert "export function extractFields" in result
