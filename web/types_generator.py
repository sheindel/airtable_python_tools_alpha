"""
Types Generator - Generate TypeScript or Python type definitions from Airtable schema

This module converts Airtable metadata into strongly-typed interfaces that can be used
in client applications (TypeScript) or Python code to ensure type safety when working
with Airtable records.
"""

from typing import Dict, List, Any, Set, Tuple
import sys
sys.path.append("web")

from constants import (
    FIELD_TYPE_TEXT,
    FIELD_TYPE_LONG_TEXT,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_RECORD_LINKS,
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_COUNT,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_AUTO_NUMBER,
    FIELD_TYPE_CURRENCY,
    FIELD_TYPE_PERCENT,
)


# TypeScript type mappings
TS_TYPE_MAPPINGS = {
    FIELD_TYPE_TEXT: "string",
    FIELD_TYPE_LONG_TEXT: "string",
    FIELD_TYPE_NUMBER: "number",
    FIELD_TYPE_CHECKBOX: "boolean",
    FIELD_TYPE_DATE: "string",
    FIELD_TYPE_DATETIME: "string",
    FIELD_TYPE_RECORD_LINKS: "Array<string>",
    "multipleAttachments": "Array<IAirtableAttachment>",
    "multipleCollaborators": "Array<IAirtableCollaborator>",
    "barcode": "string",
    "button": "string",
    "createdTime": "string",
    "lastModifiedTime": "string",
    FIELD_TYPE_AUTO_NUMBER: "number",
    FIELD_TYPE_CURRENCY: "number",
    FIELD_TYPE_PERCENT: "number",
    "duration": "number",
    "rating": "number",
    "url": "string",
    "email": "string",
    "phoneNumber": "string",
}

# Python type mappings
PYTHON_TYPE_MAPPINGS = {
    FIELD_TYPE_TEXT: "str",
    FIELD_TYPE_LONG_TEXT: "str",
    FIELD_TYPE_NUMBER: "float",
    FIELD_TYPE_CHECKBOX: "bool",
    FIELD_TYPE_DATE: "str",
    FIELD_TYPE_DATETIME: "str",
    FIELD_TYPE_RECORD_LINKS: "List[str]",
    "multipleAttachments": "List[AirtableAttachment]",
    "multipleCollaborators": "List[AirtableCollaborator]",
    "barcode": "str",
    "button": "str",
    "createdTime": "str",
    "lastModifiedTime": "str",
    FIELD_TYPE_AUTO_NUMBER: "int",
    FIELD_TYPE_CURRENCY: "float",
    FIELD_TYPE_PERCENT: "float",
    "duration": "int",
    "rating": "int",
    "url": "str",
    "email": "str",
    "phoneNumber": "str",
}


def _sanitize_name(name: str) -> str:
    """Sanitize field/table name for use as identifier"""
    # Replace spaces and special characters
    sanitized = name.replace(" ", "_").replace("-", "_").replace("(", "").replace(")", "")
    # Remove other special characters
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = "_" + sanitized
    return sanitized


def _get_typescript_type(field: Dict[str, Any]) -> str:
    """
    Convert an Airtable field to its TypeScript type representation
    
    Returns the type as a string, e.g., "string", "number", "Array<string>", "'option1' | 'option2'"
    """
    field_type = field.get("type")
    options = field.get("options", {})
    
    # Single select: union of string literals
    if field_type == FIELD_TYPE_SELECT:
        choices = options.get("choices", [])
        if choices:
            choice_names = [f"'{choice['name']}'" for choice in choices]
            return " | ".join(choice_names)
        return "string"
    
    # Multiple selects: array of string literals
    if field_type == FIELD_TYPE_MULTI_SELECT:
        choices = options.get("choices", [])
        if choices:
            choice_names = [f"'{choice['name']}'" for choice in choices]
            return f"Array<{' | '.join(choice_names)}>"
        return "Array<string>"
    
    # Formula, rollup, lookup - need to infer type from result
    if field_type in [FIELD_TYPE_FORMULA, FIELD_TYPE_ROLLUP, FIELD_TYPE_LOOKUP]:
        result_type = (options.get("result") or {}).get("type") if options else None
        
        # For lookups and rollups, check if they return arrays
        if field_type in [FIELD_TYPE_LOOKUP, FIELD_TYPE_ROLLUP]:
            result = (options.get("result") or {}) if options else {}
            
            # If it has options with choices (select field), handle union types
            if result_type == FIELD_TYPE_SELECT:
                result_options = result.get("options", {})
                choices = result_options.get("choices", [])
                if choices:
                    choice_names = [f"'{choice['name']}'" for choice in choices]
                    base_type = " | ".join(choice_names)
                    # Lookups/rollups can return single value or array
                    return f"string | Array<string>"  # Simplified
                return "string | Array<string>"
            elif result_type == FIELD_TYPE_MULTI_SELECT:
                return "Array<string>"
            
            # Default for lookups: could be single or array
            if result_type:
                base_type = TS_TYPE_MAPPINGS.get(result_type, "string")
                return f"{base_type} | Array<{base_type}>"
            return "string | Array<string>"
        
        # Regular formula
        if result_type:
            return TS_TYPE_MAPPINGS.get(result_type, "string")
        return "string"
    
    # Count always returns number
    if field_type == FIELD_TYPE_COUNT:
        return "number"
    
    # Use direct mapping
    return TS_TYPE_MAPPINGS.get(field_type, "string")


def _get_python_type(field: Dict[str, Any]) -> str:
    """
    Convert an Airtable field to its Python type representation
    
    Returns the type as a string, e.g., "str", "int", "List[str]", "Literal['opt1', 'opt2']"
    """
    field_type = field.get("type")
    options = field.get("options", {})
    
    # Single select: Literal union
    if field_type == FIELD_TYPE_SELECT:
        choices = options.get("choices", [])
        if choices:
            choice_names = [f"'{choice['name']}'" for choice in choices]
            return f"Literal[{', '.join(choice_names)}]"
        return "str"
    
    # Multiple selects: List of Literal union
    if field_type == FIELD_TYPE_MULTI_SELECT:
        choices = options.get("choices", [])
        if choices:
            choice_names = [f"'{choice['name']}'" for choice in choices]
            return f"List[Literal[{', '.join(choice_names)}]]"
        return "List[str]"
    
    # Formula, rollup, lookup - need to infer type from result
    if field_type in [FIELD_TYPE_FORMULA, FIELD_TYPE_ROLLUP, FIELD_TYPE_LOOKUP]:
        result_type = (options.get("result") or {}).get("type") if options else None
        
        # For lookups and rollups, check if they return arrays
        if field_type in [FIELD_TYPE_LOOKUP, FIELD_TYPE_ROLLUP]:
            result = (options.get("result") or {}) if options else {}
            
            if result_type == FIELD_TYPE_SELECT:
                return "Union[str, List[str]]"
            elif result_type == FIELD_TYPE_MULTI_SELECT:
                return "List[str]"
            
            # Default for lookups: could be single or array
            if result_type:
                base_type = PYTHON_TYPE_MAPPINGS.get(result_type, "str")
                return f"Union[{base_type}, List[{base_type}]]"
            return "Union[str, List[str]]"
        
        # Regular formula
        if result_type:
            return PYTHON_TYPE_MAPPINGS.get(result_type, "str")
        return "str"
    
    # Count always returns int
    if field_type == FIELD_TYPE_COUNT:
        return "int"
    
    # Use direct mapping
    return PYTHON_TYPE_MAPPINGS.get(field_type, "str")


def _is_required_field(field: Dict[str, Any]) -> bool:
    """
    Determine if a field is required (not optional)
    
    Primary fields are required, most others are optional
    """
    # Primary fields are required
    if field.get("isPrimary"):
        return True
    
    # Most computed fields (formula, rollup, count) are required since they always have a value
    field_type = field.get("type")
    if field_type in [FIELD_TYPE_COUNT, "createdTime", "lastModifiedTime", FIELD_TYPE_AUTO_NUMBER]:
        return True
    
    # Check if field is marked as required in options
    options = field.get("options", {})
    if options and options.get("isRequired"):
        return True
    
    return False


def generate_typescript_types(metadata: Dict[str, Any], include_helpers: bool = True) -> str:
    """
    Generate TypeScript type definitions from Airtable metadata
    
    Args:
        metadata: Airtable metadata dictionary
        include_helpers: Whether to include helper type definitions for attachments/collaborators
    
    Returns:
        TypeScript code as a string
    """
    lines = ["// @ts-nocheck"]
    lines.append("// Generated TypeScript types from Airtable schema")
    lines.append("// We are ignoring type errors related to FieldSet because Airtable's SDK doesn't have correct types")
    lines.append("import { FieldSet } from 'airtable'")
    lines.append("")
    
    if include_helpers:
        # Add helper types for attachments and collaborators
        lines.append("export interface IAirtableThumbnail {")
        lines.append("  url: string")
        lines.append("  width: number")
        lines.append("  height: number")
        lines.append("}")
        lines.append("")
        lines.append("export interface IAirtableAttachment {")
        lines.append("  id: string")
        lines.append("  url: string")
        lines.append("  filename: string")
        lines.append("  size: number")
        lines.append("  type: string")
        lines.append("  thumbnails?: {")
        lines.append("    small: IAirtableThumbnail")
        lines.append("    large: IAirtableThumbnail")
        lines.append("    full: IAirtableThumbnail")
        lines.append("  }")
        lines.append("}")
        lines.append("")
        lines.append("export interface IAirtableCollaborator {")
        lines.append("  id: string")
        lines.append("  email: string")
        lines.append("  name: string")
        lines.append("}")
        lines.append("")
    
    tables = metadata.get("tables", [])
    
    for table in tables:
        table_name = table.get("name", "")
        table_id = table.get("id", "")
        fields = table.get("fields", [])
        
        # Generate interface
        lines.append(f"export interface {table_name} extends FieldSet {{")
        
        for field in fields:
            field_name = field.get("name", "")
            field_type = _get_typescript_type(field)
            is_required = _is_required_field(field)
            optional_marker = "" if is_required else "?"
            
            lines.append(f"  '{field_name}'{optional_marker}: {field_type}")
        
        lines.append("}")
        lines.append("")
        
        # Generate field ID mapping
        lines.append(f"export const {table_name}FieldIdMapping = {{")
        
        for field in fields:
            field_name = field.get("name", "")
            field_id = field.get("id", "")
            lines.append(f"  '{field_name}': '{field_id}',")
        
        lines.append("} as const;")
        lines.append("")
    
    return "\n".join(lines)


def generate_python_types(metadata: Dict[str, Any], include_helpers: bool = True, use_dataclasses: bool = True) -> str:
    """
    Generate Python type definitions from Airtable metadata
    
    Args:
        metadata: Airtable metadata dictionary
        include_helpers: Whether to include helper type definitions for attachments/collaborators
        use_dataclasses: Whether to use dataclasses (True) or TypedDict (False)
    
    Returns:
        Python code as a string
    """
    lines = ['"""Generated Python types from Airtable schema"""']
    lines.append("")
    
    if use_dataclasses:
        lines.append("from dataclasses import dataclass")
        lines.append("from typing import Optional, List, Union, Literal")
    else:
        lines.append("from typing import TypedDict, Optional, List, Union, Literal, NotRequired")
    
    lines.append("")
    lines.append("")
    
    if include_helpers:
        # Add helper types for attachments and collaborators
        if use_dataclasses:
            lines.append("@dataclass")
            lines.append("class AirtableThumbnail:")
            lines.append("    url: str")
            lines.append("    width: int")
            lines.append("    height: int")
            lines.append("")
            lines.append("")
            lines.append("@dataclass")
            lines.append("class AirtableAttachment:")
            lines.append("    id: str")
            lines.append("    url: str")
            lines.append("    filename: str")
            lines.append("    size: int")
            lines.append("    type: str")
            lines.append("    thumbnails: Optional[dict[str, AirtableThumbnail]] = None")
            lines.append("")
            lines.append("")
            lines.append("@dataclass")
            lines.append("class AirtableCollaborator:")
            lines.append("    id: str")
            lines.append("    email: str")
            lines.append("    name: str")
        else:
            lines.append("class AirtableThumbnail(TypedDict):")
            lines.append("    url: str")
            lines.append("    width: int")
            lines.append("    height: int")
            lines.append("")
            lines.append("")
            lines.append("class AirtableAttachment(TypedDict):")
            lines.append("    id: str")
            lines.append("    url: str")
            lines.append("    filename: str")
            lines.append("    size: int")
            lines.append("    type: str")
            lines.append("    thumbnails: NotRequired[dict[str, AirtableThumbnail]]")
            lines.append("")
            lines.append("")
            lines.append("class AirtableCollaborator(TypedDict):")
            lines.append("    id: str")
            lines.append("    email: str")
            lines.append("    name: str")
        
        lines.append("")
        lines.append("")
    
    tables = metadata.get("tables", [])
    
    for table in tables:
        table_name = table.get("name", "")
        table_id = table.get("id", "")
        fields = table.get("fields", [])
        
        # Sanitize table name for Python
        class_name = _sanitize_name(table_name)
        
        # Generate class/TypedDict
        if use_dataclasses:
            lines.append("@dataclass")
            lines.append(f"class {class_name}:")
        else:
            lines.append(f"class {class_name}(TypedDict):")
        
        for field in fields:
            field_name = field.get("name", "")
            field_id = field.get("id", "")
            field_type = _get_python_type(field)
            is_required = _is_required_field(field)
            
            # Sanitize field name for Python
            safe_field_name = _sanitize_name(field_name)
            
            if use_dataclasses:
                if is_required:
                    lines.append(f"    {safe_field_name}: {field_type}")
                else:
                    lines.append(f"    {safe_field_name}: Optional[{field_type}] = None")
            else:
                if is_required:
                    lines.append(f"    {safe_field_name}: {field_type}")
                else:
                    lines.append(f"    {safe_field_name}: NotRequired[{field_type}]")
        
        lines.append("")
        lines.append("")
        
        # Generate field ID mapping
        mapping_name = f"{class_name}_FIELD_ID_MAPPING"
        lines.append(f"{mapping_name} = {{")
        
        for field in fields:
            field_name = field.get("name", "")
            field_id = field.get("id", "")
            safe_field_name = _sanitize_name(field_name)
            lines.append(f"    '{safe_field_name}': '{field_id}',")
        
        lines.append("}")
        lines.append("")
        
        # Also add a reverse mapping (field ID to name)
        reverse_mapping_name = f"{class_name}_FIELD_NAME_MAPPING"
        lines.append(f"{reverse_mapping_name} = {{")
        
        for field in fields:
            field_name = field.get("name", "")
            field_id = field.get("id", "")
            safe_field_name = _sanitize_name(field_name)
            lines.append(f"    '{field_id}': '{safe_field_name}',")
        
        lines.append("}")
        lines.append("")
    
    return "\n".join(lines)


def generate_all_typescript_files(metadata: Dict[str, Any], include_helpers: bool = True) -> Dict[str, str]:
    """
    Generate all TypeScript files (types + helpers + JS implementation)
    
    Args:
        metadata: Airtable metadata dictionary
        include_helpers: Whether to include helper type definitions
    
    Returns:
        Dictionary mapping filename to file content
    """
    from typescript_helpers_generator import (
        generate_typescript_helpers,
        generate_typescript_helpers_js
    )
    
    files = {
        "types.ts": generate_typescript_types(metadata, include_helpers),
        "helpers.ts": generate_typescript_helpers(metadata),
        "helpers.js": generate_typescript_helpers_js(metadata),
    }
    
    return files


def generate_all_python_files(
    metadata: Dict[str, Any],
    include_helpers: bool = True,
    use_dataclasses: bool = True
) -> Dict[str, str]:
    """
    Generate all Python files (types + helpers)
    
    Args:
        metadata: Airtable metadata dictionary
        include_helpers: Whether to include helper type definitions
        use_dataclasses: Whether to use dataclasses (True) or TypedDict (False)
    
    Returns:
        Dictionary mapping filename to file content
    """
    from python_helpers_generator import generate_python_helpers
    
    files = {
        "types.py": generate_python_types(metadata, include_helpers, use_dataclasses),
        "helpers.py": generate_python_helpers(metadata, use_dataclasses),
    }
    
    return files
