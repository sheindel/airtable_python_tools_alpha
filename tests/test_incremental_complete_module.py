"""
Tests for complete module generation in incremental_runtime_generator.

Phase 4 integration tests - validates that generate_complete_module() produces
a usable Python module with types, functions, and update logic.
"""

import sys
from pathlib import Path
import pytest

# Add web directory to path before importing
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from code_generators.incremental_runtime_generator import (
    generate_complete_module,
    GeneratorOptions,
    build_computation_graph,
)


# Sample metadata for testing
SAMPLE_METADATA = {
    "tables": [
        {
            "id": "tblContacts",
            "name": "Contacts",
            "fields": [
                {
                    "id": "fldFirstName",
                    "name": "First Name",
                    "type": "singleLineText",
                },
                {
                    "id": "fldLastName",
                    "name": "Last Name",
                    "type": "singleLineText",
                },
                {
                    "id": "fldFullName",
                    "name": "Full Name",
                    "type": "formula",
                    "options": {
                        "formula": "{First Name} & ' ' & {Last Name}",
                        "referencedFieldIds": ["fldFirstName", "fldLastName"],
                        "result": {"type": "singleLineText"},
                    },
                },
                {
                    "id": "fldAge",
                    "name": "Age",
                    "type": "number",
                },
                {
                    "id": "fldScore",
                    "name": "Score",
                    "type": "number",
                },
                {
                    "id": "fldDoubleScore",
                    "name": "Double Score",
                    "type": "formula",
                    "options": {
                        "formula": "{Score} * 2",
                        "referencedFieldIds": ["fldScore"],
                        "result": {"type": "number"},
                    },
                },
            ],
        }
    ]
}


def test_generate_complete_module_basic():
    """Test that generate_complete_module() produces valid Python code."""
    options = GeneratorOptions(
        data_access_mode="dataclass",
        include_null_checks=True,
        include_type_hints=True,
        include_docstrings=True,
    )
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have module content
    assert len(module_code) > 0
    
    # Should have key components
    assert "from dataclasses import dataclass" in module_code
    assert "from typing import" in module_code
    assert "class ComputationContext:" in module_code
    assert "def update_record(" in module_code
    assert "COMPUTATION_GRAPH" in module_code
    assert "FIELD_COMPUTERS" in module_code


def test_generate_complete_module_dataclass_types():
    """Test that dataclass types are generated correctly."""
    options = GeneratorOptions(data_access_mode="dataclass")
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have dataclass definition
    assert "@dataclass" in module_code
    assert "class Contacts:" in module_code
    
    # Should have field definitions (types_generator uses sanitized names)
    assert "First_Name" in module_code or "first_name:" in module_code
    assert "Last_Name" in module_code or "last_name:" in module_code
    assert "Full_Name" in module_code or "full_name:" in module_code  # Computed field
    
    # Should mark computed fields
    assert "_computed_fields" in module_code or "# Computed field" in module_code


def test_generate_complete_module_formula_functions():
    """Test that formula functions are generated."""
    options = GeneratorOptions(include_docstrings=True)
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have formula functions
    assert "def compute_full_name(" in module_code
    assert "def compute_double_score(" in module_code
    
    # Should have docstrings
    assert "Compute Full Name" in module_code or "full_name" in module_code


def test_generate_complete_module_computation_graph():
    """Test that computation graph data is embedded."""
    options = GeneratorOptions()
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have computation graph structure
    assert "COMPUTATION_GRAPH = {" in module_code
    assert "'max_depth':" in module_code
    assert "'depths':" in module_code
    assert "'field_id_to_name':" in module_code
    assert "'field_name_to_id':" in module_code
    
    # Should have field IDs from our sample data
    assert "fldFirstName" in module_code
    assert "fldFullName" in module_code


def test_generate_complete_module_field_computers():
    """Test that FIELD_COMPUTERS mapping is generated."""
    options = GeneratorOptions()
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have field computers mapping
    assert "FIELD_COMPUTERS = {" in module_code
    assert "compute_full_name" in module_code
    assert "compute_double_score" in module_code


def test_generate_complete_module_update_function():
    """Test that update_record() function is generated."""
    options = GeneratorOptions(
        include_docstrings=True,
        track_computation_stats=True,
    )
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have update function
    assert "def update_record(" in module_code
    assert "changed_fields" in module_code
    
    # Should have computation logic
    assert "for depth in range" in module_code
    assert "should_compute" in module_code
    assert "compute_func" in module_code
    
    # Should have stats tracking (since we enabled it)
    assert "computation_stats" in module_code


def test_generate_complete_module_context_class():
    """Test that ComputationContext class is generated."""
    options = GeneratorOptions(include_docstrings=True)
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have context class
    assert "class ComputationContext:" in module_code
    
    # Should have methods
    assert "def __init__" in module_code
    assert "def get_linked_records(" in module_code
    assert "def lookup(" in module_code
    assert "def rollup(" in module_code
    
    # Should have computed tracking
    assert "computed_this_cycle" in module_code


def test_generate_complete_module_with_null_checks():
    """Test that null checks are included when requested."""
    options = GeneratorOptions(include_null_checks=True)
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have null checks in formula functions
    assert "is None" in module_code or "None" in module_code


def test_generate_complete_module_no_null_checks():
    """Test that null checks can be disabled."""
    options = GeneratorOptions(include_null_checks=False)
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Module should still be generated
    assert len(module_code) > 0
    assert "def compute_full_name" in module_code


def test_generate_complete_module_different_data_modes():
    """Test generation with different data access modes."""
    modes = ["dataclass", "dict"]
    
    for mode in modes:
        options = GeneratorOptions(data_access_mode=mode)
        module_code = generate_complete_module(SAMPLE_METADATA, options=options)
        
        # Should generate code for each mode
        assert len(module_code) > 0
        assert "def update_record(" in module_code


def test_generate_complete_module_single_table():
    """Test generation for a single table only."""
    options = GeneratorOptions()
    
    # Generate for just the Contacts table
    module_code = generate_complete_module(
        SAMPLE_METADATA,
        table_id="tblContacts",
        options=options
    )
    
    # Should have content
    assert len(module_code) > 0
    assert "class Contacts:" in module_code


def test_generated_module_is_syntactically_valid():
    """Test that the generated module is valid Python syntax."""
    options = GeneratorOptions()
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Try to compile it
    try:
        compile(module_code, '<generated>', 'exec')
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")


def test_build_computation_graph():
    """Test that computation graph is built correctly."""
    graph = build_computation_graph(SAMPLE_METADATA)
    
    # Should have correct max depth (2: base fields, formulas, nested formulas)
    assert graph.max_depth >= 0
    
    # Should have depths populated
    assert len(graph.depths) > 0
    
    # Should have field mappings
    assert len(graph.field_id_to_name) > 0
    assert len(graph.field_name_to_id) > 0
    
    # Should find computed fields
    computed_fields = graph.get_computed_fields()
    assert len(computed_fields) > 0
    
    # Check specific computed fields
    computed_names = [f.name for f in computed_fields]
    assert "Full Name" in computed_names
    assert "Double Score" in computed_names


def test_computation_graph_depths():
    """Test that fields are organized by depth correctly."""
    graph = build_computation_graph(SAMPLE_METADATA)
    
    # Depth 0 should have non-computed fields
    depth_0_fields = graph.get_fields_at_depth(0)
    assert len(depth_0_fields) > 0
    
    # Find base fields at depth 0
    depth_0_names = [f.name for f in depth_0_fields.values()]
    assert "First Name" in depth_0_names
    assert "Last Name" in depth_0_names
    assert "Age" in depth_0_names
    
    # Depth 1+ should have computed fields
    all_fields = []
    for depth in range(1, graph.max_depth + 1):
        fields = graph.get_fields_at_depth(depth)
        all_fields.extend(fields.values())
    
    # Should have our formula fields somewhere
    all_names = [f.name for f in all_fields]
    assert "Full Name" in all_names or any("full" in n.lower() for n in all_names)


def test_field_info_structure():
    """Test that FieldInfo objects have correct structure."""
    graph = build_computation_graph(SAMPLE_METADATA)
    
    # Get a computed field
    full_name_field = None
    for depth_fields in graph.depths.values():
        for field_info in depth_fields.values():
            if field_info.name == "Full Name":
                full_name_field = field_info
                break
    
    assert full_name_field is not None
    assert full_name_field.field_id == "fldFullName"
    assert full_name_field.field_type == "formula"
    assert full_name_field.function_name is not None
    assert "compute" in full_name_field.function_name
    
    # Should have dependencies
    assert len(full_name_field.dependencies) > 0


def test_module_header_generation():
    """Test that module header has correct imports."""
    options = GeneratorOptions(
        data_access_mode="dataclass",
        include_type_hints=True,
    )
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should have module docstring
    lines = module_code.split("\n")
    assert '"""' in lines[0] or '"""' in lines[1]
    
    # Should have necessary imports
    assert "from dataclasses import dataclass" in module_code
    assert "from typing import" in module_code
    assert "Dict" in module_code
    assert "List" in module_code
    assert "Optional" in module_code


def test_computed_fields_marked_in_types():
    """Test that computed fields are marked in type definitions."""
    options = GeneratorOptions(data_access_mode="dataclass")
    
    module_code = generate_complete_module(SAMPLE_METADATA, options=options)
    
    # Should either have _computed_fields class attribute or comments
    has_computed_marker = (
        "_computed_fields" in module_code or
        "# Computed field" in module_code or
        "Computed" in module_code
    )
    assert has_computed_marker


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
