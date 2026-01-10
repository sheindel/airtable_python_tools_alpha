#!/usr/bin/env python3
"""Inspect transpiler output for formulas.

Usage:
    uv run python scripts/debug/inspect_transpiler.py 'IF({fldA}, "Yes", "No")'
    uv run python scripts/debug/inspect_transpiler.py '{fldA} & " " & {fldB}'
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "web"))

from at_formula_parser import parse_airtable_formula
from code_generators.python_runtime_generator import PythonFormulaTranspiler


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    formula = sys.argv[1]
    
    # Mock metadata with common field IDs
    metadata = {
        "tables": [{
            "id": "tblTest",
            "name": "Test",
            "fields": [
                {"id": "fldGmD6imIF6DXO6I", "name": "First Name", "type": "singleLineText"},
                {"id": "fldzDPm0Tfe9piGCd", "name": "Last Name", "type": "singleLineText"},
                {"id": "fldA", "name": "A", "type": "singleLineText"},
                {"id": "fldB", "name": "B", "type": "singleLineText"},
                {"id": "fldC", "name": "C", "type": "singleLineText"},
                {"id": "fld001", "name": "Active", "type": "checkbox"},
                {"id": "fld002", "name": "Quantity", "type": "number"},
                {"id": "fld003", "name": "Price", "type": "number"},
            ]
        }]
    }
    
    print(f"\n{'='*70}")
    print(f"Airtable Formula: {formula}")
    print(f"{'='*70}\n")
    
    try:
        # Parse AST
        ast = parse_airtable_formula(formula, metadata)
        
        # Transpile to Python (dict mode)
        transpiler_dict = PythonFormulaTranspiler(data_access_mode="dict")
        python_code_dict = transpiler_dict.transpile(ast)
        
        print("Generated Python (dict mode):")
        print(f"  {python_code_dict}")
        print(f"\nLength: {len(python_code_dict)} characters")
        print(f"Lines: {len(python_code_dict.split(chr(10)))}")
        
        # Try dataclass mode too
        transpiler_dc = PythonFormulaTranspiler(data_access_mode="dataclass")
        python_code_dc = transpiler_dc.transpile(ast)
        
        if python_code_dc != python_code_dict:
            print(f"\nGenerated Python (dataclass mode):")
            print(f"  {python_code_dc}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
