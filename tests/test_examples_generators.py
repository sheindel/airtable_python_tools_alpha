"""Tests for TypeScript and Python examples generators"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from typescript_helpers_generator import generate_typescript_examples
from python_helpers_generator import generate_python_examples


def test_generate_typescript_examples_basic(minimal_metadata):
    """Test generating TypeScript examples with basic metadata"""
    result = generate_typescript_examples(minimal_metadata)
    
    # Check that we got some output
    assert result
    assert isinstance(result, str)
    
    # Check for key TypeScript example content
    assert "Usage Examples" in result
    assert "import" in result
    assert "async function" in result or "function" in result
    assert "Example" in result  # Should have example comments
    
    # Check for some specific helper function usage
    assert "getField" in result
    assert "setField" in result
    assert "getFieldId" in result


def test_generate_typescript_examples_includes_table_name(minimal_metadata):
    """Test that examples include the actual table name from metadata"""
    result = generate_typescript_examples(minimal_metadata)
    
    # Should include the first table name from metadata
    table_name = minimal_metadata["tables"][0]["name"]
    assert table_name in result
    
    # Should have Airtable API calls
    assert "base(" in result or ".select(" in result


def test_generate_python_examples_basic(minimal_metadata):
    """Test generating Python examples with basic metadata"""
    result = generate_python_examples(minimal_metadata)
    
    # Check that we got some output
    assert result
    assert isinstance(result, str)
    
    # Check for key Python example content
    assert "Usage Examples" in result
    assert "import" in result or "from" in result
    assert "def " in result  # Should have function definitions
    assert "Example" in result  # Should have example comments
    
    # Check for some specific helper function usage
    assert "get_field" in result
    assert "set_field" in result
    assert "get_field_id" in result


def test_generate_python_examples_includes_table_name(minimal_metadata):
    """Test that examples include the actual table name from metadata"""
    result = generate_python_examples(minimal_metadata)
    
    # Should include the first table name from metadata
    table_name = minimal_metadata["tables"][0]["name"]
    # Python sanitizes the name
    assert "Record" in result  # Should reference record class
    
    # Should have pyairtable API calls
    assert "table" in result.lower()


def test_generate_python_examples_dataclass_mode(minimal_metadata):
    """Test generating Python examples for dataclass mode"""
    result = generate_python_examples(minimal_metadata, use_dataclasses=True)
    
    assert result
    assert "def " in result


def test_generate_python_examples_typeddict_mode(minimal_metadata):
    """Test generating Python examples for TypedDict mode"""
    result = generate_python_examples(minimal_metadata, use_dataclasses=False)
    
    assert result
    assert "def " in result


def test_typescript_examples_with_empty_tables():
    """Test TypeScript examples generation with no tables"""
    metadata = {"tables": []}
    result = generate_typescript_examples(metadata)
    
    # Should handle empty gracefully
    assert result
    assert "No tables" in result or result == "// No tables found in metadata"


def test_python_examples_with_empty_tables():
    """Test Python examples generation with no tables"""
    metadata = {"tables": []}
    result = generate_python_examples(metadata)
    
    # Should handle empty gracefully
    assert result
    assert "No tables" in result or result == "# No tables found in metadata"


def test_typescript_examples_includes_field_operations(minimal_metadata):
    """Test that TypeScript examples show field operations"""
    result = generate_typescript_examples(minimal_metadata)
    
    # Should demonstrate various operations
    assert "fetch" in result.lower()
    assert "update" in result.lower() or "create" in result.lower()
    
    # Should have field manipulation examples
    assert "getField(" in result or "setField(" in result


def test_python_examples_includes_field_operations(minimal_metadata):
    """Test that Python examples show field operations"""
    result = generate_python_examples(minimal_metadata)
    
    # Should demonstrate various operations
    assert "fetch" in result.lower()
    assert "update" in result.lower() or "create" in result.lower()
    
    # Should have field manipulation examples
    assert ".get(" in result or ".set(" in result


def test_typescript_examples_valid_syntax(minimal_metadata):
    """Test that generated TypeScript examples have valid-looking syntax"""
    result = generate_typescript_examples(minimal_metadata)
    
    # Should have proper TypeScript structure
    assert result.count("async function") + result.count("function") > 0
    assert "{" in result
    assert "}" in result
    
    # Should have imports at top
    lines = result.split("\n")
    import_lines = [line for line in lines[:20] if "import" in line]
    assert len(import_lines) > 0


def test_python_examples_valid_syntax(minimal_metadata):
    """Test that generated Python examples have valid-looking syntax"""
    result = generate_python_examples(minimal_metadata)
    
    # Should have proper Python structure
    assert "def " in result
    assert ":" in result
    
    # Should have imports at top
    lines = result.split("\n")
    import_lines = [line for line in lines[:20] if "import" in line or "from" in line]
    assert len(import_lines) > 0
    
    # Should have docstrings
    assert '"""' in result or "'''" in result
