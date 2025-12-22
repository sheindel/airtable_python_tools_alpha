"""
Test script for the formula compressor functionality.
This demonstrates how the compress_formula function works.
"""
import json
import re
from typing import Optional


def create_test_metadata():
    """Create sample Airtable metadata for testing"""
    return {
        "tables": [
            {
                "id": "tblTestTable1",
                "name": "Test Table",
                "primaryFieldId": "fldPrimary0000001",
                "fields": [
                    {
                        "id": "fldFieldA0000001",
                        "name": "Field A",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "AND({fldFieldB0000002}, {fldFieldC0000003})",
                            "referencedFieldIds": ["fldFieldB0000002", "fldFieldC0000003"],
                            "result": {"type": "checkbox"}
                        }
                    },
                    {
                        "id": "fldFieldB0000002",
                        "name": "Field B",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fldFieldD0000004}+{fldFieldE0000005}",
                            "referencedFieldIds": ["fldFieldD0000004", "fldFieldE0000005"],
                            "result": {"type": "number"}
                        }
                    },
                    {
                        "id": "fldFieldC0000003",
                        "name": "Field C",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "OR({fldFieldD0000004}, NOT({fldFieldE0000005}))",
                            "referencedFieldIds": ["fldFieldD0000004", "fldFieldE0000005"],
                            "result": {"type": "checkbox"}
                        }
                    },
                    {
                        "id": "fldFieldD0000004",
                        "name": "Field D",
                        "type": "number",
                        "options": {"precision": 0}
                    },
                    {
                        "id": "fldFieldE0000005",
                        "name": "Field E",
                        "type": "checkbox",
                        "options": {"icon": "check", "color": "green"}
                    }
                ]
            }
        ]
    }


def find_field_by_id(metadata, field_id):
    """Helper function to find a field by ID"""
    for table in metadata["tables"]:
        for field in table["fields"]:
            if field["id"] == field_id:
                return field
    return None


def compress_formula(
    field_id: str,
    metadata: dict,
    compression_depth=None,
    output_format="field_ids"
):
    """
    Compress/refactor an Airtable formula by replacing field references with their formulas.
    
    Args:
        field_id: The ID of the field whose formula should be compressed
        metadata: Airtable metadata dictionary
        compression_depth: How many levels deep to compress. None means compress fully
        output_format: "field_ids" or "field_names"
    
    Returns:
        The compressed formula string
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
    def compress_recursive(formula, depth, visited_fields):
        # Check if we've reached the maximum depth
        if compression_depth is not None and depth >= compression_depth:
            return formula
        
        # Find all field references in the formula (pattern: {fldXXXXXXXXXXXXXX})
        field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
        matches = list(re.finditer(field_id_pattern, formula))
        
        # Process matches in reverse order to maintain string positions
        result = formula
        for match in reversed(matches):
            field_id = match.group(1)
            
            # Skip if we've already visited this field
            if field_id in visited_fields:
                continue
            
            # Find the field metadata
            field = find_field_by_id(metadata, field_id)
            if not field or field.get("type") != "formula":
                continue
            
            # Get the formula for this field
            field_formula = field.get("options", {}).get("formula", "")
            
            # Recursively compress this field's formula
            visited_fields_copy = visited_fields.copy()
            visited_fields_copy.add(field_id)
            
            compressed = compress_recursive(field_formula, depth + 1, visited_fields_copy)
            
            # Replace in the original formula (wrap in parens for safety)
            start, end = match.span()
            result = result[:start] + f"({compressed})" + result[end:]
        
        return result
    
    def convert_field_references(formula):
        """Convert field references to the desired format"""
        if output_format == "field_ids":
            return formula
        
        # Convert to field names
        field_id_pattern = r'\{(fld[a-zA-Z0-9]+)\}'
        
        def replace_with_name(match):
            field_id = match.group(1)
            field = find_field_by_id(metadata, field_id)
            if field:
                return f"{{{field['name']}}}"
            return match.group(0)
        
        return re.sub(field_id_pattern, replace_with_name, formula)
    
    compressed = compress_recursive(formula, 0, set())
    
    # Final conversion to output format
    compressed = convert_field_references(compressed)
    
    return compressed


def main():
    """Run test cases for the formula compressor"""
    metadata = create_test_metadata()
    
    print("=" * 80)
    print("FORMULA COMPRESSOR TEST CASES")
    print("=" * 80)
    print()
    
    # Display the test setup
    print("Test Setup:")
    print("-" * 80)
    print("Field A (formula): AND({Field B}, {Field C})")
    print("Field B (formula): {Field D}+{Field E}")
    print("Field C (formula): OR({Field D}, NOT({Field E}))")
    print("Field D: number field (not a formula)")
    print("Field E: checkbox field (not a formula)")
    print()
    
    # Test Case 1: Full compression with field IDs
    print("Test Case 1: Full compression (depth=None) with field IDs")
    print("-" * 80)
    result = compress_formula("fldFieldA0000001", metadata, compression_depth=None, output_format="field_ids")
    print(f"Result: {result}")
    print(f"Expected: AND(({'{fldFieldD0000004}'}+{'{fldFieldE0000005}'}), (OR({'{fldFieldD0000004}'}, NOT({'{fldFieldE0000005}'}))))")
    print()
    
    # Test Case 2: Full compression with field names
    print("Test Case 2: Full compression (depth=None) with field names")
    print("-" * 80)
    result = compress_formula("fldFieldA0000001", metadata, compression_depth=None, output_format="field_names")
    print(f"Result: {result}")
    print()
    
    # Test Case 3: Compression depth = 1
    print("Test Case 3: Compression depth = 1 (expand one level)")
    print("-" * 80)
    result = compress_formula("fldFieldA0000001", metadata, compression_depth=1, output_format="field_names")
    print(f"Result: {result}")
    print("Expected: AND(({Field D}+{Field E}), (OR({Field D}, NOT({Field E}))))")
    print()
    
    # Test Case 4: Compression depth = 0 (no compression)
    print("Test Case 4: Compression depth = 0 (no compression)")
    print("-" * 80)
    result = compress_formula("fldFieldA0000001", metadata, compression_depth=0, output_format="field_names")
    print(f"Result: {result}")
    print("Expected: AND({Field B}, {Field C})")
    print()
    
    # Test Case 5: Start from Field B
    print("Test Case 5: Compress Field B fully")
    print("-" * 80)
    result = compress_formula("fldFieldB0000002", metadata, compression_depth=None, output_format="field_names")
    print(f"Result: {result}")
    print("Expected: {Field D}+{Field E}")
    print()
    
    print("=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()
