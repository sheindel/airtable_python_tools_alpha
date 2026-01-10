#!/usr/bin/env python3
"""Inspect generated evaluator code for a table.

Usage:
    export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
    export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
    uv run python scripts/debug/inspect_evaluator.py --table Contacts --output evaluator.py
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests"))

from helpers.airtable_api import fetch_schema_cached
from code_generators.incremental_runtime_generator import generate_complete_module, GeneratorOptions


def main():
    parser = argparse.ArgumentParser(description="Inspect generated evaluator code")
    parser.add_argument("--table", required=True, help="Table name to generate evaluator for")
    parser.add_argument("--output", help="Output file path (optional, prints to stdout if not specified)")
    parser.add_argument("--base-id", help="Airtable base ID (or use AIRTABLE_BASE_ID env)")
    parser.add_argument("--api-key", help="Airtable API key (or use AIRTABLE_API_KEY env)")
    parser.add_argument("--data-access", choices=["dict", "dataclass"], default="dict", 
                       help="Data access mode (default: dict)")
    args = parser.parse_args()
    
    base_id = args.base_id or os.environ.get("AIRTABLE_BASE_ID")
    api_key = args.api_key or os.environ.get("AIRTABLE_API_KEY")
    
    if not base_id or not api_key:
        print("ERROR: Must provide --base-id and --api-key or set environment variables", file=sys.stderr)
        sys.exit(1)
    
    # Fetch schema
    print(f"Fetching schema for base {base_id}...", file=sys.stderr)
    schema = fetch_schema_cached(base_id, api_key)
    
    # Find table
    table = next((t for t in schema["tables"] if t["name"] == args.table), None)
    if not table:
        print(f"ERROR: Table '{args.table}' not found", file=sys.stderr)
        print(f"Available tables: {', '.join(t['name'] for t in schema['tables'])}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Generating evaluator for table: {table['name']}", file=sys.stderr)
    
    # Generate evaluator
    options = GeneratorOptions(
        data_access_mode=args.data_access,
        include_null_checks=True,
        include_type_hints=False,
        include_docstrings=True,
    )
    
    module_code = generate_complete_module(schema, table_id=table["id"], options=options)
    
    print(f"Generated {len(module_code)} characters of code", file=sys.stderr)
    
    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(module_code)
        print(f"Saved to: {output_path}", file=sys.stderr)
    else:
        print("\n" + "="*70, file=sys.stderr)
        print(module_code)


if __name__ == "__main__":
    main()
