"""Formula Compressor Tab - Optimize and compress formulas"""
from pyscript import document, window
import re
from typing import Optional, Literal, Tuple

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata, find_field_by_id


def compress_formula(
    table_id: str,
    field_id: str,
    compression_depth: Optional[int] = None,
    output_format: Literal["field_ids", "field_names"] = "field_ids"
) -> Tuple[str, int]:
    """
    Compress/refactor an Airtable formula by replacing field references with their formulas.
    
    Args:
        table_id: The ID of the table containing the field
        field_id: The ID of the field whose formula should be compressed
        compression_depth: How many levels deep to compress. None means compress fully
                          until only non-formula fields remain.
        output_format: Whether to use field IDs (e.g., {fldXXX}) or field names (e.g., {Field Name})
    
    Returns:
        Tuple of (compressed_formula, max_depth_reached)
        
    Example:
        If field A has formula: AND({B}, {C})
        And field B has formula: {D}+{E}
        And field C has formula: OR({D}, NOT({E}))
        And D and E are non-formula fields
        
        Then compress_formula(..., compression_depth=None) returns:
        ("AND({D}+{E}, OR({D}, NOT({E})))", 2)
    """
    metadata = get_local_storage_metadata()
    if not metadata:
        raise ValueError("No metadata available")
    
    # Find the starting field
    field = find_field_by_id(metadata, field_id)
    if not field:
        raise ValueError(f"Field {field_id} not found")
    
    if field.get("type") != "formula":
        raise ValueError(f"Field {field_id} is not a formula field")
    
    # Get the starting formula
    formula = field["options"]["formula"]
    
    # Recursively compress the formula and track depth
    compressed, max_depth = _compress_formula_recursive(
        formula,
        metadata,
        compression_depth,
        output_format,
        depth=0,
        visited_fields=set()
    )
    
    # Final conversion to output format
    compressed = _convert_field_references(compressed, metadata, output_format)
    
    return compressed, max_depth


def _compress_formula_recursive(
    formula: str,
    metadata: dict,
    max_depth: Optional[int],
    output_format: str,
    depth: int,
    visited_fields: set
) -> Tuple[str, int]:
    """
    Recursively compress a formula by replacing field references.
    
    Args:
        formula: The formula text to compress
        metadata: Airtable metadata
        max_depth: Maximum depth to compress (None = unlimited)
        output_format: "field_ids" or "field_names"
        depth: Current recursion depth
        visited_fields: Set of field IDs already visited (to prevent infinite loops)
    
    Returns:
        Tuple of (compressed_formula, max_depth_reached)
    """
    # Check if we've reached the maximum depth
    if max_depth is not None and depth >= max_depth:
        return formula, depth
    
    # Find all field references in the formula (pattern: {fldXXXXXXXXXXXXXX})
    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
    matches = list(re.finditer(field_id_pattern, formula))
    
    # Track the maximum depth reached
    current_max_depth = depth
    
    # Process matches in reverse order to maintain string positions
    result = formula
    for match in reversed(matches):
        field_id = match.group(1)
        
        # Skip if we've already visited this field (circular reference protection)
        if field_id in visited_fields:
            continue
        
        # Find the field metadata
        field = find_field_by_id(metadata, field_id)
        if not field:
            continue
        
        # Only compress if it's a formula field
        if field.get("type") == "formula":
            # Get the formula for this field
            field_formula = field.get("options", {}).get("formula", "")
            
            # Recursively compress this field's formula
            visited_fields_copy = visited_fields.copy()
            visited_fields_copy.add(field_id)
            
            compressed_field_formula, field_max_depth = _compress_formula_recursive(
                field_formula,
                metadata,
                max_depth,
                output_format,
                depth + 1,
                visited_fields_copy
            )
            
            # Update max depth if this branch went deeper
            current_max_depth = max(current_max_depth, field_max_depth)
            
            # Replace in the original formula (wrap in parens for safety)
            start, end = match.span()
            result = result[:start] + f"({compressed_field_formula})" + result[end:]
    
    return result, current_max_depth


def _convert_field_references(
    formula: str,
    metadata: dict,
    output_format: str
) -> str:
    """
    Convert field references in a formula to the desired format.
    
    Args:
        formula: The formula text
        metadata: Airtable metadata
        output_format: "field_ids" or "field_names"
    
    Returns:
        Formula with converted field references
    """
    if output_format == "field_ids":
        # Already in field ID format, return as is
        return formula
    
    # Convert to field names
    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
    
    def replace_with_name(match):
        field_id = match.group(1)
        field = find_field_by_id(metadata, field_id)
        if field:
            return f"{{{field['name']}}}"
        return match.group(0)  # Return original if field not found
    
    return re.sub(field_id_pattern, replace_with_name, formula)


def _find_field_id_by_name(metadata: dict, field_name: str) -> Optional[str]:
    """
    Find a field ID by its name. Searches across all tables.
    
    Args:
        metadata: Airtable metadata
        field_name: Name of the field to find
    
    Returns:
        The field ID if found, None otherwise
    """
    for table in metadata.get("tables", []):
        for field in table.get("fields", []):
            if field.get("name") == field_name:
                return field["id"]
    return None


def compress_formula_by_name(
    table_name: str,
    field_name: str,
    compression_depth: Optional[int] = None,
    output_format: Literal["field_ids", "field_names"] = "field_ids"
) -> Tuple[str, int]:
    """
    Compress a formula using table and field names instead of IDs.
    
    Args:
        table_name: Name of the table
        field_name: Name of the field
        compression_depth: How many levels deep to compress (None = fully)
        output_format: "field_ids" or "field_names"
    
    Returns:
        Tuple of (compressed_formula, max_depth_reached)
    """
    metadata = get_local_storage_metadata()
    if not metadata:
        raise ValueError("No metadata available")
    
    # Find table and field
    table_id = None
    field_id = None
    
    for table in metadata["tables"]:
        if table["name"] == table_name:
            table_id = table["id"]
            for field in table["fields"]:
                if field["name"] == field_name:
                    field_id = field["id"]
                    break
            break
    
    if not table_id or not field_id:
        raise ValueError(f"Could not find table '{table_name}' or field '{field_name}'")
    
    return compress_formula(table_id, field_id, compression_depth, output_format)


def format_formula_compact(formula: str) -> str:
    """
    Format a formula in compact style (single line).
    
    Args:
        formula: The formula to format
    
    Returns:
        Compacted formula without extra whitespace
    """
    # Remove all newlines, carriage returns, and extra spaces
    compact = re.sub(r'\s+', ' ', formula)
    
    # Remove spaces around operators and commas, but preserve spaces inside field references
    # Use a more sophisticated approach that doesn't affect content inside {...}
    result = []
    inside_field_reference = False
    i = 0
    
    while i < len(compact):
        char = compact[i]
        
        if char == '{':
            inside_field_reference = True
            result.append(char)
        elif char == '}':
            inside_field_reference = False
            result.append(char)
        elif char in '(),':
            # Remove spaces before and after, unless inside field reference
            if not inside_field_reference:
                # Remove trailing space from result if present
                if result and result[-1] == ' ':
                    result.pop()
            result.append(char)
            # Skip any following spaces if not inside field reference
            if not inside_field_reference:
                while i + 1 < len(compact) and compact[i + 1] == ' ':
                    i += 1
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result).strip()


def format_formula_logical(formula: str, indent: str = "    ") -> str:
    """
    Format a formula in logical style with indentation.
    
    Args:
        formula: The formula to format
        indent: The indentation string (default: 4 spaces)
    
    Returns:
        Formatted formula with proper indentation
    """
    # First compact the formula to remove existing formatting
    formula = format_formula_compact(formula)
    
    result = []
    depth = 0
    i = 0
    inside_field_reference = False
    # Stack to track which opening parens added indentation
    paren_stack = []
    
    while i < len(formula):
        char = formula[i]
        
        # Track when we're inside a field reference {...}
        if char == '{':
            inside_field_reference = True
            result.append(char)
        elif char == '}':
            inside_field_reference = False
            result.append(char)
        elif char == '(' and not inside_field_reference:
            result.append(char)
            # Look ahead to see if we should add newline
            # Only add newline if there's content after the opening paren
            if i + 1 < len(formula) and formula[i + 1] not in (')', ' '):
                depth += 1
                paren_stack.append(True)  # This paren added indentation
                result.append('\n')
                result.append(indent * depth)
            else:
                paren_stack.append(False)  # This paren did NOT add indentation
        elif char == ')' and not inside_field_reference:
            # Only add newline before closing paren if its matching opening paren added indentation
            if paren_stack and paren_stack.pop():
                depth -= 1
                result.append('\n')
                result.append(indent * depth)
            result.append(char)
        elif char == ',' and not inside_field_reference:
            result.append(char)
            # Add newline after comma if we're inside a function
            if depth > 0:
                result.append('\n')
                result.append(indent * depth)
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def initialize():
    """Initialize the Formula Compressor tab"""
    print("Formula Compressor tab initialized")
    
    # Export functions to JavaScript
    window.compressFormulaFromUI = compress_formula_from_ui
    window.convertFormulaDisplay = convert_formula_display
    window.generateTableReportData = generate_table_report_data
    window.formatFormulaCompact = format_formula_compact
    window.formatFormulaLogical = format_formula_logical


def convert_formula_display(formula: str, output_format: str) -> str:
    """Convert a formula's field references to the specified format for display.
    
    Args:
        formula: The formula string to convert
        output_format: "field_ids" or "field_names"
    
    Returns:
        The formula with converted field references
    """
    try:
        metadata = get_local_storage_metadata()
        if not metadata:
            return formula
        
        converted = _convert_field_references(formula, metadata, output_format)
        return converted
    except Exception as e:
        print(f"Error converting formula display: {e}")
        return formula


def generate_table_report_data(table_name: str, compression_depth: Optional[int]) -> str:
    """Generate a CSV report for all formula fields in a table.
    
    Args:
        table_name: Name of the table to analyze
        compression_depth: How many levels deep to compress (None = fully)
    
    Returns:
        CSV string with report data
    """
    import csv
    from io import StringIO
    
    metadata = get_local_storage_metadata()
    if not metadata:
        raise ValueError("No metadata available")
    
    # Find the table
    table = None
    for t in metadata["tables"]:
        if t["name"] == table_name:
            table = t
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found")
    
    # Create CSV in memory
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Field Name",
        "Field ID",
        "Field Type",
        "Formula Depth",
        "Original Formula (Field Names)",
        "Reduced Formula (Field Names)",
        "Original Formula (Field IDs)",
        "Reduced Formula (Field IDs)"
    ])
    
    # Process each formula field
    for field in table["fields"]:
        if field.get("type") == "formula":
            field_name = field["name"]
            field_id = field["id"]
            field_type = field["type"]
            
            # Get original formula (stored as field IDs)
            original_formula_ids = field["options"].get("formula", "")
            
            # Convert original to field names
            original_formula_names = _convert_field_references(
                original_formula_ids, 
                metadata, 
                "field_names"
            )
            
            # Compress with field IDs and get depth
            formula_depth = 0
            try:
                reduced_formula_ids, formula_depth = compress_formula(
                    table["id"],
                    field_id,
                    compression_depth,
                    "field_ids"
                )
            except Exception as e:
                reduced_formula_ids = f"Error: {str(e)}"
            
            # Compress with field names
            try:
                reduced_formula_names, _ = compress_formula(
                    table["id"],
                    field_id,
                    compression_depth,
                    "field_names"
                )
            except Exception as e:
                reduced_formula_names = f"Error: {str(e)}"
            
            # Write row
            writer.writerow([
                field_name,
                field_id,
                field_type,
                formula_depth,
                original_formula_names,
                reduced_formula_names,
                original_formula_ids,
                reduced_formula_ids
            ])
    
    return output.getvalue()


def compress_formula_from_ui(
    table_name: str,
    field_name: str,
    compression_depth: Optional[int],
    output_format: str,
    display_format: str = "compact"
):
    """
    UI handler for compressing a formula. Called from JavaScript.
    
    Args:
        table_name: Name of the table
        field_name: Name of the field
        compression_depth: How many levels deep to compress (None = fully)
        output_format: "field_ids" or "field_names"
        display_format: "compact" or "logical"
    """
    try:
        compressed, depth = compress_formula_by_name(
            table_name,
            field_name,
            compression_depth,
            output_format
        )
        
        # Apply display formatting
        if display_format == "logical":
            formatted_compressed = format_formula_logical(compressed)
        else:
            formatted_compressed = format_formula_compact(compressed)
        
        # Update the UI with the result
        compressed_display = document.getElementById("compressed-formula-display")
        # Escape HTML characters and wrap in span with dark mode text color
        escaped_formula = formatted_compressed.replace("<", "&lt;").replace(">", "&gt;")
        compressed_display.innerHTML = f'<span class="text-gray-900 dark:text-gray-100">{escaped_formula}</span>'
        
        # Store the raw (unformatted) formula for later reformatting
        compressed_display.setAttribute("data-raw-formula", compressed)
        
        print(f"Successfully compressed formula for {table_name}.{field_name} (depth: {depth})")
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg)
        
        # Show error in UI
        compressed_display = document.getElementById("compressed-formula-display")
        compressed_display.innerHTML = f'<span class="text-red-600 dark:text-red-400">{error_msg}</span>'
