"""Shared Airtable API and schema management functionality"""
import json
from pyscript import window


def save_local_storage(key: str, value):
    """Save data to browser's local storage"""
    window.localStorage.setItem(key, value)


def get_local_storage(key: str):
    """Retrieve data from browser's local storage"""
    return window.localStorage.getItem(key)


def get_local_storage_metadata():
    """Get Airtable metadata from local storage"""
    metadata = get_local_storage("airtableSchema")
    if metadata:
        json_data = json.loads(metadata)["schema"]
        return json_data
    return None


def get_schema_timestamp():
    """Get the timestamp of when schema was last refreshed"""
    schema_data = get_local_storage("airtableSchema")
    if schema_data:
        return json.loads(schema_data).get("timestamp")
    return None


def find_table_by_name(metadata, table_name: str):
    """Find a table by name in the metadata"""
    if not metadata:
        return None
    for table in metadata["tables"]:
        if table["name"] == table_name:
            return table
    return None


def find_field_by_name(metadata, table_name: str, field_name: str):
    """Find a field by name within a table"""
    table = find_table_by_name(metadata, table_name)
    if not table:
        return None
    for field in table["fields"]:
        if field["name"] == field_name:
            return field
    return None


def find_field_by_id(metadata, field_id: str):
    """Find a field by ID across all tables"""
    if not metadata:
        return None
    for table in metadata["tables"]:
        for field in table["fields"]:
            if field["id"] == field_id:
                return field
    return None
