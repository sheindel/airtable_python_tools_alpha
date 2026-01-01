"""
Python Helpers Generator - Generate helper functions and utilities for Airtable records

This module generates Python helper functions that provide type-safe access to Airtable records,
including get_field/set_field functions, field ID lookups, and record manipulation utilities.
"""

from typing import Dict, Any, List
import sys
sys.path.append("web")

from types_generator import _sanitize_name


def generate_python_helpers(metadata: Dict[str, Any], use_dataclasses: bool = True) -> str:
    """
    Generate Python helper functions for type-safe record access
    
    Args:
        metadata: Airtable metadata dictionary
        use_dataclasses: Whether the types use dataclasses (True) or TypedDict (False)
    
    Returns:
        Python code as a string with helper functions
    """
    tables = metadata.get("tables", [])
    table_classes = [_sanitize_name(table.get("name", "")) for table in tables]
    
    lines = [
        '"""Generated Python helpers for Airtable records"""',
        "",
        "from typing import (",
        "    Dict, List, Optional, TypeVar, Generic, Union,",
        "    Protocol, Any, cast, overload, Literal",
        ")",
        "",
        "# Import the generated types",
        "from .types import *",
        "",
        "# Re-export all types for convenience",
        "__all__ = [",
    ]
    
    # Export all table classes
    for class_name in table_classes:
        lines.append(f'    "{class_name}",')
        lines.append(f'    "{class_name}_FIELD_ID_MAPPING",')
        lines.append(f'    "{class_name}_FIELD_NAME_MAPPING",')
    
    # Export helper functions
    lines.extend([
        '    "ATRecord",',
        '    "get_field_id",',
        '    "get_field_ids",',
        '    "get_field",',
        '    "set_field",',
        '    "get_fields",',
        '    "has_field",',
        '    "create_update",',
        '    "is_record",',
        '    "extract_fields",',
        "]",
        "",
        "",
        "# ============================================================================",
        "# Type Definitions",
        "# ============================================================================",
        "",
        "T = TypeVar('T')",
        "",
    ])
    
    if use_dataclasses:
        lines.extend([
            "class ATRecord(Protocol):",
            '    """Protocol for Airtable records with id and table metadata"""',
            "    id: str",
            "    _table: Optional[str] = None",
            "    _raw_fields: Optional[Dict[str, Any]] = None",
        ])
    else:
        lines.extend([
            "class ATRecord(TypedDict, total=False):",
            '    """TypedDict for Airtable records with id and table metadata"""',
            "    id: str",
            "    _table: str",
            "    _raw_fields: Dict[str, Any]",
        ])
    
    lines.extend([
        "",
        "",
        "# Table name literal type",
        "TableName = Literal[",
    ])
    
    for i, table in enumerate(tables):
        table_name = table.get("name", "")
        comma = "," if i < len(tables) - 1 else ""
        lines.append(f'    "{table_name}"{comma}')
    
    lines.extend([
        "]",
        "",
        "",
        "# Field ID mappings for all tables",
        "FIELD_ID_MAPPINGS: Dict[str, Dict[str, str]] = {",
    ])
    
    for table in tables:
        table_name = table.get("name", "")
        class_name = _sanitize_name(table_name)
        lines.append(f'    "{table_name}": {class_name}_FIELD_ID_MAPPING,')
    
    lines.extend([
        "}",
        "",
        "",
        "# Field name mappings for all tables (reverse of ID mappings)",
        "FIELD_NAME_MAPPINGS: Dict[str, Dict[str, str]] = {",
    ])
    
    for table in tables:
        table_name = table.get("name", "")
        class_name = _sanitize_name(table_name)
        lines.append(f'    "{table_name}": {class_name}_FIELD_NAME_MAPPING,')
    
    lines.extend([
        "}",
        "",
        "",
        "# ============================================================================",
        "# Helper Functions",
        "# ============================================================================",
        "",
        "def get_field_id(table_name: TableName, field_name: str) -> str:",
        '    """',
        "    Get a field ID from a table and field name",
        "    ",
        "    Args:",
        "        table_name: The name of the table",
        "        field_name: The name of the field",
        "    ",
        "    Returns:",
        "        The field ID, or the field_name if not found",
        '    """',
        "    mapping = FIELD_ID_MAPPINGS.get(table_name, {})",
        "    return mapping.get(field_name, field_name)",
        "",
        "",
        "def get_field_ids(table_name: TableName, field_names: List[str]) -> List[str]:",
        '    """',
        "    Get multiple field IDs from a table",
        "    ",
        "    Args:",
        "        table_name: The name of the table",
        "        field_names: List of field names",
        "    ",
        "    Returns:",
        "        List of field IDs",
        '    """',
        "    return [get_field_id(table_name, field_name) for field_name in field_names]",
        "",
        "",
        "def get_field(",
        "    record: Optional[Dict[str, Any]],",
        "    field_name: str,",
        "    default: Any = None,",
        "    use_field_id: bool = False",
        ") -> Any:",
        '    """',
        "    Get a field value from a record with proper typing",
        "    ",
        "    Args:",
        "        record: The Airtable record (dict-like object)",
        "        field_name: The name of the field (or field ID if use_field_id is True)",
        "        default: Default value if field is missing or undefined",
        "        use_field_id: Whether field_name is actually a field ID",
        "    ",
        "    Returns:",
        "        The field value, or default if not found",
        '    """',
        "    if record is None:",
        "        return default",
        "    ",
        "    key = field_name",
        "    value = record.get(key)",
        "    ",
        "    return value if value is not None else default",
        "",
        "",
        "def set_field(",
        "    record: Dict[str, Any],",
        "    field_name: str,",
        "    value: Any,",
        "    use_field_id: bool = False",
        ") -> None:",
        '    """',
        "    Set a field value on a record with proper typing",
        "    ",
        "    Args:",
        "        record: The Airtable record (dict-like object)",
        "        field_name: The name of the field (or field ID if use_field_id is True)",
        "        value: The value to set",
        "        use_field_id: Whether field_name is actually a field ID",
        '    """',
        "    if record is None:",
        "        return",
        "    ",
        "    key = field_name",
        "    record[key] = value",
        "",
        "",
        "def get_fields(",
        "    record: Optional[Dict[str, Any]],",
        "    field_names: List[str]",
        ") -> Dict[str, Any]:",
        '    """',
        "    Get multiple field values from a record",
        "    ",
        "    Args:",
        "        record: The Airtable record",
        "        field_names: List of field names to retrieve",
        "    ",
        "    Returns:",
        "        Dictionary with field names as keys and their values",
        '    """',
        "    if record is None:",
        "        return {}",
        "    ",
        "    result = {}",
        "    for field_name in field_names:",
        "        value = get_field(record, field_name)",
        "        if value is not None:",
        "            result[field_name] = value",
        "    ",
        "    return result",
        "",
        "",
        "def has_field(record: Optional[Dict[str, Any]], field_name: str) -> bool:",
        '    """',
        "    Check if a record has a specific field with a non-null value",
        "    ",
        "    Args:",
        "        record: The Airtable record",
        "        field_name: The name of the field",
        "    ",
        "    Returns:",
        "        True if field exists and has a non-null value",
        '    """',
        "    if record is None:",
        "        return False",
        "    ",
        "    return field_name in record and record[field_name] is not None",
        "",
        "",
        "def create_update(record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:",
        '    """',
        "    Create a record update object with proper structure",
        "    ",
        "    Args:",
        "        record_id: The record ID",
        "        fields: Dictionary of field names/IDs and their new values",
        "    ",
        "    Returns:",
        "        A record update object suitable for Airtable API",
        '    """',
        "    return {",
        '        "id": record_id,',
        '        "fields": fields',
        "    }",
        "",
        "",
        "def is_record(value: Any) -> bool:",
        '    """',
        "    Type guard to check if a value is a valid Airtable record",
        "    ",
        "    Args:",
        "        value: The value to check",
        "    ",
        "    Returns:",
        "        True if value is a dict-like record with an ID",
        '    """',
        "    return (",
        "        isinstance(value, dict) and",
        '        "id" in value and',
        '        isinstance(value["id"], str)',
        "    )",
        "",
        "",
        "def extract_fields(record: Dict[str, Any]) -> Dict[str, Any]:",
        '    """',
        "    Extract only the field data from a record (without id and metadata)",
        "    ",
        "    Args:",
        "        record: The Airtable record",
        "    ",
        "    Returns:",
        "        Dictionary containing only the field data",
        '    """',
        "    return {",
        "        k: v for k, v in record.items()",
        '        if k not in ("id", "_table", "_raw_fields")',
        "    }",
        "",
        "",
        "# ============================================================================",
        "# Typed Wrapper Classes (Optional - for better IDE support)",
        "# ============================================================================",
        "",
    ])
    
    # Generate typed wrapper classes for each table
    for table in tables:
        table_name = table.get("name", "")
        class_name = _sanitize_name(table_name)
        
        lines.extend([
            f"class {class_name}Record:",
            '    """',
            f"    Typed wrapper for {table_name} records with helper methods",
            '    """',
            "    ",
            f"    def __init__(self, record: Dict[str, Any]):",
            '        """Initialize from a raw Airtable record dict"""',
            "        self._record = record",
            "        self.id = record.get('id', '')",
            "    ",
            "    def get(self, field_name: str, default: Any = None) -> Any:",
            '        """Get a field value by name"""',
            "        return get_field(self._record, field_name, default)",
            "    ",
            "    def set(self, field_name: str, value: Any) -> None:",
            '        """Set a field value by name"""',
            "        set_field(self._record, field_name, value)",
            "    ",
            "    def has(self, field_name: str) -> bool:",
            '        """Check if a field exists and has a value"""',
            "        return has_field(self._record, field_name)",
            "    ",
            "    def to_dict(self) -> Dict[str, Any]:",
            '        """Convert to a plain dictionary"""',
            "        return self._record.copy()",
            "    ",
            "    def fields(self) -> Dict[str, Any]:",
            '        """Get only the field data (without id and metadata)"""',
            "        return extract_fields(self._record)",
            "    ",
            "    @staticmethod",
            "    def get_field_id(field_name: str) -> str:",
            '        """Get the field ID for a field name"""',
            f'        return get_field_id("{table_name}", field_name)',
            "    ",
            "    @staticmethod",
            "    def get_field_ids(field_names: List[str]) -> List[str]:",
            '        """Get field IDs for multiple field names"""',
            f'        return get_field_ids("{table_name}", field_names)',
            "",
            "",
        ])
    
    lines.extend([
        "# ============================================================================",
        "# Convenience Functions for Creating Typed Records",
        "# ============================================================================",
        "",
    ])
    
    for table in tables:
        table_name = table.get("name", "")
        class_name = _sanitize_name(table_name)
        func_name = f"create_{class_name.lower()}_record"
        
        lines.extend([
            f"def {func_name}(record: Dict[str, Any]) -> {class_name}Record:",
            '    """',
            f"    Create a typed {class_name}Record from a raw record dict",
            "    ",
            "    Args:",
            "        record: Raw Airtable record dictionary",
            "    ",
            "    Returns:",
            f"        Typed {class_name}Record instance",
            '    """',
            f"    return {class_name}Record(record)",
            "",
            "",
        ])
    
    return "\n".join(lines)


def generate_python_examples(metadata: Dict[str, Any], use_dataclasses: bool = True) -> str:
    """
    Generate Python usage examples for the generated types and helpers
    
    Args:
        metadata: Airtable metadata dictionary
        use_dataclasses: Whether the types use dataclasses (True) or TypedDict (False)
    
    Returns:
        Python example code as a string
    """
    tables = metadata.get("tables", [])
    
    # Pick first table for examples
    example_table = tables[0] if tables else None
    if not example_table:
        return "# No tables found in metadata"
    
    table_name = example_table.get("name", "")
    class_name = _sanitize_name(table_name)
    fields = example_table.get("fields", [])
    
    # Get a few example fields
    text_field = next((f for f in fields if f.get("type") in ["singleLineText", "multilineText"]), None)
    number_field = next((f for f in fields if f.get("type") == "number"), None)
    checkbox_field = next((f for f in fields if f.get("type") == "checkbox"), None)
    
    lines = [
        '"""',
        "Usage Examples for Generated Airtable Types and Helpers",
        "",
        "This file demonstrates how to use the generated types and helper functions",
        "to work with Airtable records in a type-safe manner.",
        '"""',
        "",
        "from typing import List, Dict, Any, Optional",
        "from pyairtable import Api",
        "",
        "# Import the generated types and helpers",
        "from .helpers import (",
        f"    {class_name},",
        f"    {class_name}Record,",
        f"    create_{class_name.lower()}_record,",
        "    get_field,",
        "    set_field,",
        "    get_field_id,",
        "    get_field_ids,",
        "    has_field,",
        "    create_update,",
        "    is_record,",
        "    extract_fields",
        ")",
        "",
        "# ============================================================================",
        "# Example 1: Initialize Airtable Connection",
        "# ============================================================================",
        "",
        'def get_airtable_table():',
        '    """Initialize connection to Airtable"""',
        "    api = Api('YOUR_API_KEY')",
        "    base = api.base('YOUR_BASE_ID')",
        f"    table = base.table('{table_name}')",
        "    return table",
        "",
        "",
        "# ============================================================================",
        "# Example 2: Fetch Records with Proper Typing",
        "# ============================================================================",
        "",
        f"def fetch_records() -> List[{class_name}Record]:",
        '    """Fetch records from Airtable with proper typing"""',
        "    table = get_airtable_table()",
        "    ",
        "    # Fetch records from Airtable",
        "    records = table.all(max_records=10, view='Grid view')",
        "    ",
        "    # Convert to typed records",
        f"    typed_records = [create_{class_name.lower()}_record(record) for record in records]",
        "    ",
        "    return typed_records",
        "",
        "",
        "# ============================================================================",
        "# Example 3: Access Fields Safely",
        "# ============================================================================",
        "",
        "def access_fields():",
        '    """Demonstrate safe field access"""',
        "    records = fetch_records()",
        "    ",
        "    if not records:",
        "        print('No records found')",
        "        return",
        "    ",
        "    record = records[0]",
        "",
    ]
    
    if text_field:
        field_name = text_field.get("name", "")
        safe_field_name = _sanitize_name(field_name)
        lines.extend([
            f"    # Access field with proper typing",
            f"    value = record.get('{safe_field_name}')",
            f"    print(f'Field value: {{value}}')",
            "",
        ])
    
    if checkbox_field:
        field_name = checkbox_field.get("name", "")
        safe_field_name = _sanitize_name(field_name)
        lines.extend([
            f"    # Check if field exists and has value",
            f"    if record.has('{safe_field_name}'):",
            f"        print('{field_name} is checked')",
            "",
        ])
    
    lines.extend([
        "",
        "# ============================================================================",
        "# Example 4: Get Field IDs",
        "# ============================================================================",
        "",
        "def work_with_field_ids():",
        '    """Demonstrate working with field IDs"""',
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        safe_field_name = _sanitize_name(field_name)
        lines.extend([
            f"    # Get field ID for a specific field",
            f"    field_id = {class_name}Record.get_field_id('{safe_field_name}')",
            f"    print(f'Field ID: {{field_id}}')",
            "",
        ])
    
    field_names = [_sanitize_name(f.get("name", "")) for f in fields[:3]]
    if field_names:
        field_names_str = "', '".join(field_names)
        lines.extend([
            f"    # Get multiple field IDs at once",
            f"    field_ids = {class_name}Record.get_field_ids(['{field_names_str}'])",
            "    print(f'Field IDs: {field_ids}')",
            "",
        ])
    
    lines.extend([
        "",
        "# ============================================================================",
        "# Example 5: Update Records",
        "# ============================================================================",
        "",
        "def update_records():",
        '    """Demonstrate updating records"""',
        "    table = get_airtable_table()",
        "    records = fetch_records()",
        "    ",
        "    if not records:",
        "        print('No records found')",
        "        return",
        "    ",
        "    record = records[0]",
        "",
    ])
    
    if text_field and number_field:
        text_name = _sanitize_name(text_field.get("name", ""))
        number_name = _sanitize_name(number_field.get("name", ""))
        lines.extend([
            f"    # Modify field values",
            f"    record.set('{text_name}', 'Updated value')",
            f"    record.set('{number_name}', 42)",
            "",
            f"    # Get the fields to update",
            "    fields = record.fields()",
            "",
            f"    # Send update to Airtable",
            "    table.update(record.id, fields)",
            "",
        ])
    
    lines.extend([
        "",
        "# ============================================================================",
        "# Example 6: Create New Records",
        "# ============================================================================",
        "",
        "def create_records():",
        '    """Demonstrate creating new records"""',
        "    table = get_airtable_table()",
        "    ",
        f"    # Prepare new record data",
        "    new_record = {",
    ])
    
    if text_field:
        field_name = _sanitize_name(text_field.get("name", ""))
        lines.append(f"        '{field_name}': 'New record value',")
    
    if number_field:
        field_name = _sanitize_name(number_field.get("name", ""))
        lines.append(f"        '{field_name}': 100,")
    
    if checkbox_field:
        field_name = _sanitize_name(checkbox_field.get("name", ""))
        lines.append(f"        '{field_name}': True,")
    
    lines.extend([
        "    }",
        "    ",
        "    # Create record in Airtable",
        "    created_record = table.create(new_record)",
        f"    typed_record = create_{class_name.lower()}_record(created_record)",
        "    ",
        "    print(f'Created record with ID: {typed_record.id}')",
        "    return typed_record",
        "",
        "",
        "# ============================================================================",
        "# Example 7: Filter and Query Records",
        "# ============================================================================",
        "",
        f"def query_records() -> List[{class_name}Record]:",
        '    """Demonstrate querying records with filters"""',
        "    table = get_airtable_table()",
        "    ",
    ])
    
    if text_field:
        field_name = text_field.get("name", "")
        safe_field_name = _sanitize_name(field_name)
        field_id = text_field.get("id", "")
        lines.extend([
            f"    # Use field IDs in formulas for more reliable queries",
            f"    field_id = {class_name}Record.get_field_id('{safe_field_name}')",
            f"    ",
            f"    # Query with filter formula",
            "    records = table.all(",
            "        formula=f'{{{field_id}}} != \\\"\\\"',",
            "        sort=[field_id]",
            "    )",
            "    ",
            f"    typed_records = [create_{class_name.lower()}_record(r) for r in records]",
            "    return typed_records",
        ])
    
    lines.extend([
        "",
        "",
        "# ============================================================================",
        "# Example 8: Batch Operations",
        "# ============================================================================",
        "",
        "def batch_update():",
        '    """Demonstrate batch updates"""',
        "    table = get_airtable_table()",
        "    records = fetch_records()",
        "    ",
    ])
    
    if text_field:
        field_name = _sanitize_name(text_field.get("name", ""))
        lines.extend([
            f"    # Prepare batch updates",
            "    updates = []",
            "    for record in records:",
            f"        record.set('{field_name}', f'Updated: {{record.id}}')",
            "        updates.append({",
            "            'id': record.id,",
            "            'fields': record.fields()",
            "        })",
            "    ",
            "    # Send batch update to Airtable (max 10 at a time)",
            "    batch_size = 10",
            "    for i in range(0, len(updates), batch_size):",
            "        batch = updates[i:i + batch_size]",
            "        table.batch_update(batch)",
            "    ",
            "    print(f'Updated {len(updates)} records')",
        ])
    
    lines.extend([
        "",
        "",
        "# ============================================================================",
        "# Example 9: Using Helper Functions Directly",
        "# ============================================================================",
        "",
        "def use_helper_functions():",
        '    """Demonstrate using helper functions directly on raw dicts"""',
        "    records = fetch_records()",
        "    ",
        "    if not records:",
        "        return",
        "    ",
        "    # Get raw record dict",
        "    raw_record = records[0].to_dict()",
        "    ",
    ])
    
    if text_field:
        field_name = _sanitize_name(text_field.get("name", ""))
        lines.extend([
            f"    # Use helper functions",
            f"    value = get_field(raw_record, '{field_name}')",
            f"    print(f'Field value: {{value}}')",
            "    ",
            f"    # Check if field exists",
            f"    exists = has_field(raw_record, '{field_name}')",
            f"    print(f'Field exists: {{exists}}')",
            "    ",
        ])
    
    lines.extend([
        "    # Check if it's a valid record",
        "    if is_record(raw_record):",
        "        print(f'Valid record with ID: {raw_record[\"id\"]}')",
        "    ",
        "    # Extract just the fields (without metadata)",
        "    fields_only = extract_fields(raw_record)",
        "    print(f'Fields: {fields_only}')",
        "",
        "",
        "# ============================================================================",
        "# Example 10: Type-Safe Field Access with Dataclass/TypedDict",
        "# ============================================================================",
        "",
        "def direct_field_access():",
        '    """Demonstrate direct field access on typed records"""',
        "    records = fetch_records()",
        "    ",
        "    if not records:",
        "        return",
        "    ",
        "    record = records[0]",
        "    ",
    ])
    
    if text_field:
        field_name = _sanitize_name(text_field.get("name", ""))
        lines.extend([
            f"    # Direct field access (with IDE autocomplete)",
            f"    value = record.get('{field_name}')",
            f"    print(f'Direct access: {{value}}')",
            "    ",
        ])
    
    lines.extend([
        "    # Get all fields as dict",
        "    all_fields = record.fields()",
        "    print(f'All fields: {all_fields}')",
        "",
        "",
        "# ============================================================================",
        "# Running Examples",
        "# ============================================================================",
        "",
        "def main():",
        '    """Run all examples"""',
        "    try:",
        "        print('Fetching records...')",
        "        access_fields()",
        "        ",
        "        print('\\nWorking with field IDs...')",
        "        work_with_field_ids()",
        "        ",
        "        print('\\nExamples completed successfully!')",
        "        ",
        "    except Exception as e:",
        "        print(f'Error running examples: {e}')",
        "",
        "",
        "if __name__ == '__main__':",
        "    # Uncomment to run examples",
        "    # main()",
        "    pass",
    ])
    
    return "\n".join(lines)
