"""Tests for PostgreSQL schema generator module"""

import pytest
from postgres_schema_generator import (
    transform_field_name,
    get_postgres_type_for_field,
    get_column_name,
    should_include_field,
    generate_create_table_statement,
    generate_schema,
    DATA_FIELD_TYPES,
    COMPUTED_FIELD_TYPES,
)
from at_types import AirTableFieldMetadata, TableMetadata, AirtableMetadata


class TestTransformFieldName:
    """Test field name transformation logic"""
    
    def test_basic_transformation(self):
        """Test basic field name transformations"""
        assert transform_field_name("Contact Name") == "contact_name"
        assert transform_field_name("Customer ID") == "customer_id"
        assert transform_field_name("First & Last Name") == "first_last_name"
    
    def test_remove_brackets(self):
        """Test removal of bracketed prefixes"""
        assert transform_field_name("[read-only] Contact Name") == "contact_name"
        assert transform_field_name("[calculated] Total Amount") == "total_amount"
        assert transform_field_name("  [prefix]  Field Name  ") == "field_name"
    
    def test_special_characters(self):
        """Test handling of special characters"""
        assert transform_field_name("Price ($)") == "price"
        assert transform_field_name("Contact #123") == "contact_123"
        assert transform_field_name("Field/Name") == "field_name"
        assert transform_field_name("Field@Name") == "field_name"
    
    def test_multiple_underscores(self):
        """Test that multiple consecutive special chars become one underscore"""
        assert transform_field_name("Field  --  Name") == "field_name"
        assert transform_field_name("A:::B") == "a_b"
    
    def test_edge_cases(self):
        """Test edge cases"""
        assert transform_field_name("___Field___") == "field"
        assert transform_field_name("123") == "123"
        assert transform_field_name("") == ""


class TestGetPostgresType:
    """Test PostgreSQL type mapping"""
    
    def test_text_fields(self):
        """Test text field type mapping"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Test",
            "type": "singleLineText",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123"
        }
        assert get_postgres_type_for_field(field) == "TEXT"
    
    def test_number_fields(self):
        """Test number field type mapping"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Amount",
            "type": "number",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {"precision": 2}
        }
        assert get_postgres_type_for_field(field) == "NUMERIC"
    
    def test_checkbox_field(self):
        """Test checkbox field type mapping"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Active",
            "type": "checkbox",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {"icon": "check", "color": "blue"}
        }
        assert get_postgres_type_for_field(field) == "BOOLEAN"
    
    def test_formula_with_result_type(self):
        """Test formula field with result type"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Calculated",
            "type": "formula",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {
                "isValid": True,
                "formula": "1 + 1",
                "referencedFieldIds": [],
                "result": {
                    "type": "number",
                    "options": {}
                }
            }
        }
        assert get_postgres_type_for_field(field) == "NUMERIC"
    
    def test_count_field(self):
        """Test count field type mapping"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Count",
            "type": "count",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {
                "isValid": True,
                "recordLinkFieldId": "fldXXX"
            }
        }
        assert get_postgres_type_for_field(field) == "INTEGER"


class TestGetColumnName:
    """Test column name generation"""
    
    def test_field_id_mode(self):
        """Test using field IDs as column names"""
        field: AirTableFieldMetadata = {
            "id": "fldABC123XYZ45678",
            "name": "Contact Name",
            "type": "singleLineText",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123"
        }
        assert get_column_name(field, "field_ids") == "fldABC123XYZ45678"
    
    def test_field_name_mode(self):
        """Test using transformed field names as column names"""
        field: AirTableFieldMetadata = {
            "id": "fldABC123XYZ45678",
            "name": "Contact Name",
            "type": "singleLineText",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123"
        }
        assert get_column_name(field, "field_names") == "contact_name"


class TestShouldIncludeField:
    """Test field filtering logic"""
    
    def test_include_data_fields(self):
        """Test that data fields are included when specified"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Name",
            "type": "singleLineText",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123"
        }
        assert should_include_field(field, DATA_FIELD_TYPES) is True
    
    def test_exclude_computed_fields(self):
        """Test that computed fields are excluded when not specified"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Calculated",
            "type": "formula",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {
                "isValid": True,
                "formula": "1 + 1",
                "referencedFieldIds": [],
                "result": {"type": "number", "options": {}}
            }
        }
        assert should_include_field(field, DATA_FIELD_TYPES) is False
    
    def test_include_computed_fields(self):
        """Test that computed fields are included when specified"""
        field: AirTableFieldMetadata = {
            "id": "fld123",
            "name": "Calculated",
            "type": "formula",
            "description": None,
            "strong_links": [],
            "weak_links": [],
            "table": "tbl123",
            "options": {
                "isValid": True,
                "formula": "1 + 1",
                "referencedFieldIds": [],
                "result": {"type": "number", "options": {}}
            }
        }
        assert should_include_field(field, COMPUTED_FIELD_TYPES) is True


class TestGenerateCreateTableStatement:
    """Test CREATE TABLE statement generation"""
    
    def test_basic_table(self):
        """Test basic table generation with field names"""
        table: TableMetadata = {
            "id": "tblABC123",
            "name": "Contacts",
            "primaryFieldId": "fld001",
            "fields": [
                {
                    "id": "fld001",
                    "name": "Name",
                    "type": "singleLineText",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123"
                },
                {
                    "id": "fld002",
                    "name": "Email",
                    "type": "email",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123"
                }
            ],
            "field_lookup": {}
        }
        
        sql = generate_create_table_statement(table, naming_mode="field_names")
        
        assert "CREATE TABLE contacts" in sql
        assert "record_id TEXT PRIMARY KEY" in sql
        assert "name TEXT" in sql
        assert "email TEXT" in sql
    
    def test_table_with_field_ids(self):
        """Test table generation with field IDs"""
        table: TableMetadata = {
            "id": "tblABC123",
            "name": "Contacts",
            "primaryFieldId": "fld001",
            "fields": [
                {
                    "id": "fld001",
                    "name": "Name",
                    "type": "singleLineText",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123"
                }
            ],
            "field_lookup": {}
        }
        
        sql = generate_create_table_statement(table, naming_mode="field_ids")
        
        assert "CREATE TABLE tblABC123" in sql
        assert "fld001 TEXT" in sql
    
    def test_checkbox_field_defaults(self):
        """Test that checkbox fields have NOT NULL and DEFAULT constraints"""
        table: TableMetadata = {
            "id": "tblABC123",
            "name": "Tasks",
            "primaryFieldId": "fld001",
            "fields": [
                {
                    "id": "fld001",
                    "name": "Task Name",
                    "type": "singleLineText",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123"
                },
                {
                    "id": "fld002",
                    "name": "Completed",
                    "type": "checkbox",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123",
                    "options": {"icon": "check", "color": "blue"}
                }
            ],
            "field_lookup": {}
        }
        
        sql = generate_create_table_statement(table, naming_mode="field_names")
        
        assert "completed BOOLEAN NOT NULL DEFAULT FALSE" in sql
    
    def test_field_type_filtering(self):
        """Test that field type filtering works"""
        table: TableMetadata = {
            "id": "tblABC123",
            "name": "Contacts",
            "primaryFieldId": "fld001",
            "fields": [
                {
                    "id": "fld001",
                    "name": "Name",
                    "type": "singleLineText",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123"
                },
                {
                    "id": "fld002",
                    "name": "Calculated",
                    "type": "formula",
                    "description": None,
                    "strong_links": [],
                    "weak_links": [],
                    "table": "tblABC123",
                    "options": {
                        "isValid": True,
                        "formula": "1 + 1",
                        "referencedFieldIds": [],
                        "result": {"type": "number", "options": {}}
                    }
                }
            ],
            "field_lookup": {}
        }
        
        # Only include data fields (should exclude formula)
        sql = generate_create_table_statement(
            table, 
            naming_mode="field_names",
            included_field_types=DATA_FIELD_TYPES
        )
        
        assert "name TEXT" in sql
        assert "calculated" not in sql.lower()


class TestGenerateSchema:
    """Test complete schema generation"""
    
    def test_multi_table_schema(self):
        """Test schema generation with multiple tables"""
        metadata: AirtableMetadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Contacts",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Name",
                            "type": "singleLineText",
                            "description": None,
                            "strong_links": [],
                            "weak_links": [],
                            "table": "tbl001"
                        }
                    ],
                    "field_lookup": {}
                },
                {
                    "id": "tbl002",
                    "name": "Companies",
                    "primaryFieldId": "fld002",
                    "fields": [
                        {
                            "id": "fld002",
                            "name": "Company Name",
                            "type": "singleLineText",
                            "description": None,
                            "strong_links": [],
                            "weak_links": [],
                            "table": "tbl002"
                        }
                    ],
                    "field_lookup": {}
                }
            ]
        }
        
        sql = generate_schema(metadata, naming_mode="field_names")
        
        assert "CREATE TABLE contacts" in sql
        assert "CREATE TABLE companies" in sql
        assert "-- PostgreSQL Schema Generated from Airtable" in sql
    
    def test_table_filtering(self):
        """Test filtering which tables to include"""
        metadata: AirtableMetadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Contacts",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "Name",
                            "type": "singleLineText",
                            "description": None,
                            "strong_links": [],
                            "weak_links": [],
                            "table": "tbl001"
                        }
                    ],
                    "field_lookup": {}
                },
                {
                    "id": "tbl002",
                    "name": "Companies",
                    "primaryFieldId": "fld002",
                    "fields": [
                        {
                            "id": "fld002",
                            "name": "Company Name",
                            "type": "singleLineText",
                            "description": None,
                            "strong_links": [],
                            "weak_links": [],
                            "table": "tbl002"
                        }
                    ],
                    "field_lookup": {}
                }
            ]
        }
        
        # Only include Contacts table
        sql = generate_schema(
            metadata, 
            naming_mode="field_names",
            tables_to_include={"tbl001"}
        )
        
        assert "CREATE TABLE contacts" in sql
        assert "CREATE TABLE companies" not in sql
