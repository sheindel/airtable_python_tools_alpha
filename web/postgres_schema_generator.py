"""PostgreSQL Schema Generator from Airtable Metadata

Generates PostgreSQL CREATE TABLE statements from Airtable schema, with options for:
- Using field IDs or transformed field names as column names
- Filtering by field types to include
- Converting formulas to PostgreSQL generated columns (with depth limits)
"""

import re
from typing import Literal, Optional, Set, Dict
from at_types import AirtableMetadata, AirTableFieldMetadata, TableMetadata
from airtable_formula_to_sql import (
    convert_formula_to_generated_column,
    is_formula_convertible,
    FormulaConversionError
)
from constants import (
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_TEXT,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_DATE,
    FIELD_TYPE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_AUTO_NUMBER,
    FIELD_TYPE_PERCENT,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_COUNT,
    FIELD_TYPE_RECORD_LINKS,
)


def transform_field_name(name: str) -> str:
    """Transform Airtable field name into PostgreSQL-safe column name.
    
    Rules:
    1. Remove bracketed prefixes like "[read-only]"
    2. Lowercase
    3. Replace any sequence of non-alphanumeric characters with underscore
    4. Remove leading/trailing underscores
    
    Args:
        name: Original Airtable field name
        
    Returns:
        Transformed PostgreSQL-safe column name
        
    Examples:
        "[read-only] Contact Name" -> "contact_name"
        "Customer ID #" -> "customer_id"
        "First & Last Name" -> "first_last_name"
    """
    # 1. Remove bracketed prefixes like "[read-only]"
    name = re.sub(r'^\s*\[[^\]]*\]\s*', '', name)

    # 2. Lowercase
    name = name.lower()

    # 3. Replace any sequence of non-alphanumeric characters with underscore
    name = re.sub(r'[^a-z0-9]+', '_', name)

    # 4. Remove leading/trailing underscores
    name = name.strip('_')

    return name


# Mapping of Airtable field types to PostgreSQL types
AIRTABLE_TO_POSTGRES_TYPE_MAP = {
    FIELD_TYPE_TEXT: "TEXT",
    "multilineText": "TEXT",
    "richText": "TEXT",
    "email": "TEXT",
    "url": "TEXT",
    "phoneNumber": "TEXT",
    FIELD_TYPE_NUMBER: "NUMERIC",
    FIELD_TYPE_PERCENT: "NUMERIC",
    "currency": "NUMERIC",
    "rating": "INTEGER",
    "duration": "INTEGER",
    FIELD_TYPE_CHECKBOX: "BOOLEAN",
    FIELD_TYPE_DATE: "DATE",
    "dateTime": "TIMESTAMP",
    "createdTime": "TIMESTAMP",
    "lastModifiedTime": "TIMESTAMP",
    FIELD_TYPE_SELECT: "TEXT",  # Could be ENUM in advanced mode
    FIELD_TYPE_MULTI_SELECT: "TEXT[]",  # Array of text
    FIELD_TYPE_AUTO_NUMBER: "SERIAL",
    FIELD_TYPE_RECORD_LINKS: "TEXT[]",  # Array of record IDs
    "multipleAttachments": "JSONB",  # Store as JSON
    "collaborator": "TEXT",
    "multipleCollaborators": "TEXT[]",
    "barcode": "JSONB",
    # Computed fields - will be converted based on result type
    FIELD_TYPE_FORMULA: None,  # Determined by result type
    FIELD_TYPE_ROLLUP: None,  # Determined by result type
    FIELD_TYPE_LOOKUP: None,  # Determined by result type
    FIELD_TYPE_COUNT: "INTEGER",
}


def get_postgres_type_for_field(field: AirTableFieldMetadata) -> str:
    """Get PostgreSQL type for an Airtable field.
    
    Args:
        field: Airtable field metadata
        
    Returns:
        PostgreSQL type string
    """
    field_type = field["type"]
    
    # Check direct mapping first
    if field_type in AIRTABLE_TO_POSTGRES_TYPE_MAP:
        postgres_type = AIRTABLE_TO_POSTGRES_TYPE_MAP[field_type]
        if postgres_type is not None:
            return postgres_type
    
    # For computed fields (formula, rollup, lookup), check result type
    if field_type in [FIELD_TYPE_FORMULA, FIELD_TYPE_ROLLUP, FIELD_TYPE_LOOKUP]:
        options = field.get("options", {})
        result = options.get("result")
        if result:
            result_type = result.get("type")
            if result_type in AIRTABLE_TO_POSTGRES_TYPE_MAP:
                postgres_type = AIRTABLE_TO_POSTGRES_TYPE_MAP[result_type]
                if postgres_type is not None:
                    return postgres_type
    
    # Default fallback
    return "TEXT"


def get_column_name(
    field: AirTableFieldMetadata,
    naming_mode: Literal["field_ids", "field_names"]
) -> str:
    """Get PostgreSQL column name for a field.
    
    Args:
        field: Airtable field metadata
        naming_mode: Whether to use field IDs or transformed field names
        
    Returns:
        PostgreSQL column name
    """
    if naming_mode == "field_ids":
        return field["id"]
    else:
        return transform_field_name(field["name"])


def should_include_field(
    field: AirTableFieldMetadata,
    included_field_types: Set[str]
) -> bool:
    """Check if a field should be included based on type filters.
    
    Args:
        field: Airtable field metadata
        included_field_types: Set of field types to include
        
    Returns:
        True if field should be included
    """
    return field["type"] in included_field_types


def build_field_name_map(
    table: TableMetadata,
    naming_mode: Literal["field_ids", "field_names"]
) -> Dict[str, str]:
    """Build a mapping of field IDs to PostgreSQL column names.
    
    Args:
        table: Airtable table metadata
        naming_mode: Whether to use field IDs or transformed field names
        
    Returns:
        Dictionary mapping field IDs to column names
    """
    field_map = {}
    for field in table["fields"]:
        field_id = field["id"]
        column_name = get_column_name(field, naming_mode)
        field_map[field_id] = column_name
    return field_map


def generate_create_table_statement(
    table: TableMetadata,
    naming_mode: Literal["field_ids", "field_names"] = "field_names",
    included_field_types: Optional[Set[str]] = None,
    include_formulas_as_generated: bool = False,
    formula_max_depth: int = 2
) -> str:
    """Generate PostgreSQL CREATE TABLE statement for an Airtable table.
    
    Args:
        table: Airtable table metadata
        naming_mode: Whether to use field IDs or transformed field names
        included_field_types: Set of field types to include (None = all)
        include_formulas_as_generated: Whether to convert formulas to generated columns
        formula_max_depth: Maximum formula compression depth for generated columns
        
    Returns:
        PostgreSQL CREATE TABLE statement
    """
    table_name = transform_field_name(table["name"]) if naming_mode == "field_names" else table["id"]
    
    # If no filter specified, include all field types
    if included_field_types is None:
        included_field_types = set(AIRTABLE_TO_POSTGRES_TYPE_MAP.keys())
    
    columns = []
    generated_columns = []  # Store generated columns separately to add at end
    
    # Add primary key (Airtable record ID)
    columns.append("    record_id TEXT PRIMARY KEY")
    
    # Build field name map for formula conversion
    field_name_map = build_field_name_map(table, naming_mode)
    
    # Process each field
    for field in table["fields"]:
        if not should_include_field(field, included_field_types):
            continue
        
        field_type = field["type"]
        column_name = get_column_name(field, naming_mode)
        
        # Handle formula fields with conversion to generated columns
        if field_type == FIELD_TYPE_FORMULA and include_formulas_as_generated:
            try:
                # Get the formula from field options
                formula = field.get("options", {}).get("formula", "")
                
                if not formula:
                    # No formula, skip this field
                    continue
                
                # Check if the formula is convertible
                if not is_formula_convertible(formula):
                    # Add as comment if not convertible
                    generated_columns.append(
                        f"    -- {column_name}: Formula not convertible (unsupported functions)"
                    )
                    continue
                
                # Get the PostgreSQL type for this field
                postgres_type = get_postgres_type_for_field(field)
                
                # Convert formula to generated column
                generated_col_def = convert_formula_to_generated_column(
                    column_name,
                    formula,
                    field_name_map,
                    postgres_type
                )
                
                # Add to generated columns list (these go after regular columns)
                generated_columns.append(f"    {generated_col_def}")
                continue
                
            except FormulaConversionError as e:
                # If conversion fails, add as comment
                generated_columns.append(
                    f"    -- {column_name}: Formula conversion failed - {str(e)}"
                )
                continue
            except Exception as e:
                # Any other error, add as comment
                generated_columns.append(
                    f"    -- {column_name}: Unexpected error during conversion - {str(e)}"
                )
                continue
        
        postgres_type = get_postgres_type_for_field(field)
        
        # Add column definition
        column_def = f"    {column_name} {postgres_type}"
        
        # Add NOT NULL constraint for certain field types
        if field_type in [FIELD_TYPE_AUTO_NUMBER, FIELD_TYPE_CHECKBOX]:
            column_def += " NOT NULL"
        
        # Add DEFAULT for checkboxes
        if field_type == FIELD_TYPE_CHECKBOX:
            column_def += " DEFAULT FALSE"
        
        columns.append(column_def)
    
    # Add generated columns at the end
    all_columns = columns + generated_columns
    
    # Build CREATE TABLE statement
    columns_sql = ",\n".join(all_columns)
    sql = f"CREATE TABLE {table_name} (\n{columns_sql}\n);"
    
    return sql


def generate_schema(
    metadata: AirtableMetadata,
    naming_mode: Literal["field_ids", "field_names"] = "field_names",
    included_field_types: Optional[Set[str]] = None,
    include_formulas_as_generated: bool = False,
    formula_max_depth: int = 2,
    tables_to_include: Optional[Set[str]] = None
) -> str:
    """Generate complete PostgreSQL schema from Airtable metadata.
    
    Args:
        metadata: Airtable metadata
        naming_mode: Whether to use field IDs or transformed field names
        included_field_types: Set of field types to include (None = all)
        include_formulas_as_generated: Whether to convert formulas to generated columns
        formula_max_depth: Maximum formula compression depth for generated columns
        tables_to_include: Set of table IDs or names to include (None = all)
        
    Returns:
        Complete PostgreSQL schema as SQL statements
    """
    sql_statements = []
    
    # Add header comment
    sql_statements.append("-- PostgreSQL Schema Generated from Airtable")
    sql_statements.append("-- Naming mode: " + naming_mode)
    sql_statements.append("")
    
    for table in metadata["tables"]:
        # Check if table should be included
        if tables_to_include is not None:
            if table["id"] not in tables_to_include and table["name"] not in tables_to_include:
                continue
        
        table_sql = generate_create_table_statement(
            table,
            naming_mode=naming_mode,
            included_field_types=included_field_types,
            include_formulas_as_generated=include_formulas_as_generated,
            formula_max_depth=formula_max_depth
        )
        
        sql_statements.append(table_sql)
        sql_statements.append("")
    
    return "\n".join(sql_statements)


# Common field type groupings for filtering
DATA_FIELD_TYPES = {
    FIELD_TYPE_TEXT,
    "multilineText",
    "richText",
    "email",
    "url",
    "phoneNumber",
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_PERCENT,
    "currency",
    "rating",
    "duration",
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_DATE,
    "dateTime",
    FIELD_TYPE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_AUTO_NUMBER,
    FIELD_TYPE_RECORD_LINKS,
    "multipleAttachments",
    "collaborator",
    "multipleCollaborators",
    "barcode",
}

COMPUTED_FIELD_TYPES = {
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_COUNT,
}

SYSTEM_FIELD_TYPES = {
    "createdTime",
    "lastModifiedTime",
    FIELD_TYPE_AUTO_NUMBER,
}

ALL_FIELD_TYPES = DATA_FIELD_TYPES | COMPUTED_FIELD_TYPES | SYSTEM_FIELD_TYPES
