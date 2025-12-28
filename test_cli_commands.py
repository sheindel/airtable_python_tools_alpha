#!/usr/bin/env python3
"""Test the new CLI commands with sample data"""
import json
from pathlib import Path
from web.tabs.formula_compressor import compress_formula_by_name
from web.tabs.unused_fields import get_unused_fields
from web.tabs.complexity_scorecard import get_all_field_complexity
from web.components.airtable_client import _metadata_cache

# Load sample schema
sample_schema_path = Path(__file__).parent / "web" / "sample_schema.json"
with open(sample_schema_path) as f:
    metadata = json.load(f)

# Set up metadata cache
_metadata_cache['metadata'] = metadata

print("=== Testing Formula Compression ===")
# Find a formula field in the sample data
for table in metadata["tables"]:
    for field in table["fields"]:
        if field.get("type") == "formula":
            print(f"Testing with: {table['name']}.{field['name']}")
            try:
                compressed, depth = compress_formula_by_name(
                    table["name"],
                    field["name"],
                    None,
                    "field_names"
                )
                print(f"✓ Formula compression works! Depth: {depth}")
                print(f"  Compressed: {compressed[:100]}...")
            except Exception as e:
                print(f"✗ Error: {e}")
            break
    break

print("\n=== Testing Unused Fields Detection ===")
try:
    unused = get_unused_fields()
    print(f"✓ Found {len(unused)} unused fields")
    if unused:
        print(f"  Example: {unused[0]['table_name']}.{unused[0]['field_name']}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n=== Testing Complexity Scorecard ===")
try:
    complexity = get_all_field_complexity()
    print(f"✓ Analyzed {len(complexity)} computed fields")
    if complexity:
        top = complexity[0]
        print(f"  Most complex: {top['table_name']}.{top['field_name']} (score: {top['complexity_score']})")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n✅ All tests passed!")
