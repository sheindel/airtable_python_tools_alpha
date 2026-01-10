#!/usr/bin/env python3
"""Inspect computation graph structure for a given table.

Usage:
    export AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
    export AIRTABLE_API_KEY=keyXXXXXXXXXXXXXX
    uv run python scripts/debug/inspect_graph.py --table Contacts
"""
import sys
import os
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests"))

from helpers.airtable_api import fetch_schema_cached
from code_generators.incremental_runtime_generator import build_computation_graph


def main():
    parser = argparse.ArgumentParser(description="Inspect computation graph for a table")
    parser.add_argument("--table", required=True, help="Table name to inspect")
    parser.add_argument("--base-id", help="Airtable base ID (or use AIRTABLE_BASE_ID env)")
    parser.add_argument("--api-key", help="Airtable API key (or use AIRTABLE_API_KEY env)")
    args = parser.parse_args()
    
    base_id = args.base_id or os.environ.get("AIRTABLE_BASE_ID")
    api_key = args.api_key or os.environ.get("AIRTABLE_API_KEY")
    
    if not base_id or not api_key:
        print("ERROR: Must provide --base-id and --api-key or set environment variables")
        sys.exit(1)
    
    # Fetch schema
    print(f"Fetching schema for base {base_id}...")
    schema = fetch_schema_cached(base_id, api_key)
    
    # Find table
    table = next((t for t in schema["tables"] if t["name"] == args.table), None)
    if not table:
        print(f"ERROR: Table '{args.table}' not found")
        print(f"Available tables: {', '.join(t['name'] for t in schema['tables'])}")
        sys.exit(1)
    
    table_id = table["id"]
    print(f"\nTable: {table['name']}")
    print(f"ID: {table_id}")
    print(f"Fields: {len(table['fields'])}")
    
    # Check computed fields in schema
    computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
    computed_fields = [f for f in table["fields"] if f["type"] in computed_types]
    print(f"\nComputed fields in schema: {len(computed_fields)}")
    for f in computed_fields[:10]:
        print(f"  - {f['name']} ({f['type']})")
    if len(computed_fields) > 10:
        print(f"  ... and {len(computed_fields) - 10} more")
    
    # Build computation graph
    print(f"\nBuilding computation graph...")
    graph = build_computation_graph(schema, table_id=table_id)
    
    print(f"\nGraph statistics:")
    print(f"  Max depth: {graph.max_depth}")
    print(f"  Total fields: {len(graph.field_id_to_name)}")
    
    # Check each depth
    for depth in sorted(graph.depths.keys()):
        depth_fields = graph.depths[depth]
        computed_at_depth = [f for f in depth_fields.values() if f.field_type in computed_types]
        if depth_fields:
            print(f"\n  Depth {depth}: {len(depth_fields)} fields, {len(computed_at_depth)} computed")
            for field_info in list(depth_fields.values())[:5]:
                deps = f" (deps: {len(field_info.dependencies)})" if field_info.dependencies else ""
                print(f"    - {field_info.name} ({field_info.field_type}){deps}")
            if len(depth_fields) > 5:
                print(f"    ... and {len(depth_fields) - 5} more")


if __name__ == "__main__":
    main()
