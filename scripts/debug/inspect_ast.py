#!/usr/bin/env python3
"""Inspect AST structure for Airtable formulas.

Usage:
    uv run python scripts/debug/inspect_ast.py 'IF({fldA}, "Yes", "No")'
    uv run python scripts/debug/inspect_ast.py '{fldA} & " " & {fldB}'
"""
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))

from at_formula_parser import parse_airtable_formula
import json


def print_ast(node, indent=0):
    """Pretty print AST structure."""
    prefix = "  " * indent
    node_type = type(node).__name__
    print(f"{prefix}{node_type}:")
    
    if hasattr(node, '__dict__'):
        for key, value in node.__dict__.items():
            if key.startswith('_'):
                continue
            print(f"{prefix}  {key}:", end=" ")
            if isinstance(value, (str, int, float, bool, type(None))):
                print(value)
            elif isinstance(value, list):
                print(f"[{len(value)} items]")
                for item in value:
                    if hasattr(item, '__dict__'):
                        print_ast(item, indent + 2)
                    else:
                        print(f"{prefix}    {item}")
            elif hasattr(value, '__dict__'):
                print()
                print_ast(value, indent + 2)
            else:
                print(type(value))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    formula = sys.argv[1]
    
    # Mock metadata for testing
    metadata = {
        "tables": [{
            "id": "tblTest",
            "name": "Test",
            "fields": [
                {"id": "fldA", "name": "A", "type": "singleLineText"},
                {"id": "fldB", "name": "B", "type": "singleLineText"},
                {"id": "fldC", "name": "C", "type": "singleLineText"},
            ]
        }]
    }
    
    print(f"\n{'='*70}")
    print(f"Formula: {formula}")
    print(f"{'='*70}\n")
    
    try:
        ast = parse_airtable_formula(formula, metadata)
        print_ast(ast)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
