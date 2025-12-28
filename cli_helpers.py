"""Helper functions for CLI commands that wrap web module functionality"""
import re
from typing import Optional, Literal, Tuple
from web.at_types import AirtableMetadata


def find_field_by_id(metadata: AirtableMetadata, field_id: str):
    """Find a field by its ID across all tables"""
    for table in metadata.get("tables", []):
        for field in table.get("fields", []):
            if field["id"] == field_id:
                return field
    return None


def compress_formula(
    metadata: AirtableMetadata,
    table_id: str,
    field_id: str,
    compression_depth: Optional[int] = None,
    output_format: Literal["field_ids", "field_names"] = "field_ids"
) -> Tuple[str, int]:
    """
    Compress/refactor an Airtable formula by replacing field references with their formulas.
    
    Args:
        metadata: Airtable metadata
        table_id: The ID of the table containing the field
        field_id: The ID of the field whose formula should be compressed
        compression_depth: How many levels deep to compress. None means compress fully
        output_format: Whether to use field IDs or field names
    
    Returns:
        Tuple of (compressed_formula, max_depth_reached)
    """
    # Find the starting field
    field = find_field_by_id(metadata, field_id)
    if not field:
        raise ValueError(f"Field {field_id} not found")
    
    if field.get("type") != "formula":
        raise ValueError(f"Field {field_id} is not a formula field")
    
    # Get the starting formula
    formula = field["options"]["formula"]
    
    # Recursively compress the formula
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
    """Recursively compress a formula by replacing field references"""
    if max_depth is not None and depth >= max_depth:
        return formula, depth
    
    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
    matches = list(re.finditer(field_id_pattern, formula))
    
    current_max_depth = depth
    result = formula
    
    for match in reversed(matches):
        field_id = match.group(1)
        
        if field_id in visited_fields:
            continue
        
        field = find_field_by_id(metadata, field_id)
        if not field:
            continue
        
        if field.get("type") == "formula":
            field_formula = field.get("options", {}).get("formula", "")
            
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
            
            current_max_depth = max(current_max_depth, field_max_depth)
            
            start, end = match.span()
            result = result[:start] + f"({compressed_field_formula})" + result[end:]
    
    return result, current_max_depth


def _convert_field_references(formula: str, metadata: dict, output_format: str) -> str:
    """Convert field references in a formula to the desired format"""
    if output_format == "field_ids":
        return formula
    
    field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
    
    def replace_with_name(match):
        field_id = match.group(1)
        field = find_field_by_id(metadata, field_id)
        if field:
            return f"{{{field['name']}}}"
        return match.group(0)
    
    return re.sub(field_id_pattern, replace_with_name, formula)


def compress_formula_by_name(
    metadata: AirtableMetadata,
    table_name: str,
    field_name: str,
    compression_depth: Optional[int] = None,
    output_format: Literal["field_ids", "field_names"] = "field_ids"
) -> Tuple[str, int]:
    """Compress a formula using table and field names instead of IDs"""
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
    
    return compress_formula(metadata, table_id, field_id, compression_depth, output_format)


def format_formula_compact(formula: str) -> str:
    """Format a formula in compact style (single line)"""
    compact = re.sub(r'\s+', ' ', formula)
    
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
            if not inside_field_reference:
                if result and result[-1] == ' ':
                    result.pop()
            result.append(char)
            if not inside_field_reference:
                while i + 1 < len(compact) and compact[i + 1] == ' ':
                    i += 1
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result).strip()


def format_formula_logical(formula: str, indent: str = "    ") -> str:
    """Format a formula in logical style with indentation"""
    formula = format_formula_compact(formula)
    
    result = []
    depth = 0
    i = 0
    inside_field_reference = False
    paren_stack = []
    
    while i < len(formula):
        char = formula[i]
        
        if char == '{':
            inside_field_reference = True
            result.append(char)
        elif char == '}':
            inside_field_reference = False
            result.append(char)
        elif char == '(' and not inside_field_reference:
            result.append(char)
            if i + 1 < len(formula) and formula[i + 1] not in (')', ' '):
                depth += 1
                paren_stack.append(True)
                result.append('\n')
                result.append(indent * depth)
            else:
                paren_stack.append(False)
        elif char == ')' and not inside_field_reference:
            if paren_stack and paren_stack.pop():
                depth -= 1
                result.append('\n')
                result.append(indent * depth)
            result.append(char)
        elif char == ',' and not inside_field_reference:
            result.append(char)
            if depth > 0:
                result.append('\n')
                result.append(indent * depth)
        else:
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def generate_table_compression_report(
    metadata: AirtableMetadata,
    table_name: str,
    compression_depth: Optional[int] = None
) -> str:
    """Generate a CSV report for all formula fields in a table"""
    import csv
    from io import StringIO
    
    # Find the table
    table = None
    for t in metadata["tables"]:
        if t["name"] == table_name:
            table = t
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found")
    
    output = StringIO()
    writer = csv.writer(output)
    
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
    
    for field in table["fields"]:
        if field.get("type") == "formula":
            field_name = field["name"]
            field_id = field["id"]
            field_type = field["type"]
            
            original_formula_ids = field["options"].get("formula", "")
            original_formula_names = _convert_field_references(
                original_formula_ids, 
                metadata, 
                "field_names"
            )
            
            formula_depth = 0
            try:
                reduced_formula_ids, formula_depth = compress_formula(
                    metadata,
                    table["id"],
                    field_id,
                    compression_depth,
                    "field_ids"
                )
            except Exception as e:
                reduced_formula_ids = f"Error: {str(e)}"
            
            try:
                reduced_formula_names, _ = compress_formula(
                    metadata,
                    table["id"],
                    field_id,
                    compression_depth,
                    "field_names"
                )
            except Exception as e:
                reduced_formula_names = f"Error: {str(e)}"
            
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
