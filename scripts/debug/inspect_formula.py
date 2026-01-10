#!/usr/bin/env python3
"""Inspect and debug a specific formula field in detail.

Usage:
    export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
    export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
    uv run python scripts/debug/inspect_formula.py --table Contacts --field Name --record recXXXXXXXXXXXXXX
"""
import sys
import os
import argparse
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests"))

from helpers.airtable_api import (
    fetch_schema_cached,
    fetch_record,
    extract_raw_fields,
    convert_record_to_snake_case,
)
from code_generators.incremental_runtime_generator import generate_complete_module, GeneratorOptions


def main():
    parser = argparse.ArgumentParser(description="Debug a specific formula field")
    parser.add_argument("--table", required=True, help="Table name")
    parser.add_argument("--field", required=True, help="Field name to debug")
    parser.add_argument("--record", help="Specific record ID (optional, uses random if not specified)")
    parser.add_argument("--base-id", help="Airtable base ID (or use AIRTABLE_BASE_ID env)")
    parser.add_argument("--api-key", help="Airtable API key (or use AIRTABLE_API_KEY env)")
    args = parser.parse_args()
    
    base_id = args.base_id or os.environ.get("AIRTABLE_BASE_ID")
    api_key = args.api_key or os.environ.get("AIRTABLE_API_KEY")
    
    if not base_id or not api_key:
        print("ERROR: Must provide --base-id and --api-key or set environment variables")
        sys.exit(1)
    
    # Fetch schema
    print(f"Fetching schema...")
    schema = fetch_schema_cached(base_id, api_key)
    
    # Find table
    table = next((t for t in schema["tables"] if t["name"] == args.table), None)
    if not table:
        print(f"ERROR: Table '{args.table}' not found")
        sys.exit(1)
    
    # Find field
    field = next((f for f in table["fields"] if f["name"] == args.field), None)
    if not field:
        print(f"ERROR: Field '{args.field}' not found in table '{args.table}'")
        print(f"Available fields: {', '.join(f['name'] for f in table['fields'])}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print(f"Field: {field['name']}")
    print(f"Type: {field['type']}")
    print(f"ID: {field['id']}")
    print(f"{'='*70}\n")
    
    # Show formula if it's a computed field
    if field['type'] == 'formula':
        formula = field.get('options', {}).get('formula', '')
        print(f"Formula: {formula}\n")
        
        # Extract field IDs
        field_ids = re.findall(r'\{(fld[a-zA-Z0-9]+)\}', formula)
        if field_ids:
            print("Referenced fields:")
            for fid in field_ids:
                ref_field = next((f for f in table["fields"] if f["id"] == fid), None)
                if ref_field:
                    print(f"  {fid} = {ref_field['name']} ({ref_field['type']})")
            print()
    
    # Fetch test record
    if args.record:
        record_id = args.record
    else:
        from helpers.airtable_api import get_random_record_id
        print("Fetching random record...")
        record_id = get_random_record_id(base_id, api_key, args.table)
    
    print(f"Using record: {record_id}")
    record = fetch_record(base_id, api_key, args.table, record_id)
    
    airtable_value = record['fields'].get(args.field)
    print(f"\nAirtable value: {airtable_value}")
    
    # Extract raw fields and convert to snake_case
    raw_fields = extract_raw_fields(record, schema, table["id"])
    raw_fields_snake = convert_record_to_snake_case(raw_fields)
    
    # Generate and execute evaluator
    print(f"\nGenerating evaluator...")
    options = GeneratorOptions(
        data_access_mode="dict",
        include_null_checks=True,
    )
    module_code = generate_complete_module(schema, table_id=table["id"], options=options)
    
    # Execute
    namespace = {}
    exec(module_code, namespace)
    update_record = namespace.get("update_record")
    ComputationContext = namespace.get("ComputationContext")
    
    if not update_record or not ComputationContext:
        print("ERROR: Could not load update_record or ComputationContext from generated code")
        sys.exit(1)
    
    # Compute
    local_record = {"id": record_id, **raw_fields_snake}
    context = ComputationContext(local_record, {})
    result = update_record(local_record, context)
    
    # Get field name in snake_case
    from helpers.airtable_api import to_snake_case
    field_snake = to_snake_case(args.field)
    local_value = result.get(field_snake)
    
    print(f"Local value:    {local_value}")
    
    # Compare
    print(f"\n{'='*70}")
    if local_value == airtable_value:
        print("✓ VALUES MATCH")
    else:
        print("✗ VALUES DIFFER")
        print(f"  Expected: {airtable_value}")
        print(f"  Got:      {local_value}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
