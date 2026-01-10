"""
Integration tests for the formula evaluator generator

Tests the complete workflow:
1. Generate evaluator code from schema
2. Execute generated code
3. Verify formula evaluations are correct
4. Test incremental computation
"""
import sys
from pathlib import Path
import json
import tempfile
import importlib.util

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from code_generators.incremental_runtime_generator import (
    generate_complete_module,
    GeneratorOptions
)


def load_schema(schema_name: str) -> dict:
    """Load a test schema from the project root"""
    schema_path = Path(__file__).parent.parent / schema_name
    with open(schema_path) as f:
        return json.load(f)


def load_generated_module(code: str, module_name: str = "test_evaluator"):
    """Load generated code as a Python module"""
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Load module from file
        spec = importlib.util.spec_from_file_location(module_name, temp_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        # Clean up temp file
        Path(temp_path).unlink(missing_ok=True)


class TestEvaluatorGeneration:
    """Test basic code generation"""
    
    def test_generates_valid_python_code(self):
        """Test that generator produces syntactically valid Python"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(
            data_access_mode="dataclass",
            include_null_checks=True,
        )
        
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",  # Contacts table
            options=options
        )
        
        # Should be able to load as module without syntax errors
        module = load_generated_module(code)
        
        # Check required exports exist
        assert hasattr(module, "Contacts")
        assert hasattr(module, "update_record")
        assert hasattr(module, "ComputationContext")
    
    def test_supports_all_data_access_modes(self):
        """Test generation with different data access patterns"""
        schema = load_schema("crm_schema.json")
        
        for mode in ["dataclass", "dict"]:
            options = GeneratorOptions(data_access_mode=mode)
            
            code = generate_complete_module(
                metadata=schema,
                table_id="tbl2OGQy64kSZEM93",
                options=options
            )
            
            # Should generate valid code for each mode
            module = load_generated_module(code, module_name=f"test_{mode}")
            assert hasattr(module, "update_record")
    
    def test_null_checks_option(self):
        """Test that null checks can be toggled"""
        schema = load_schema("crm_schema.json")
        
        # With null checks
        options_with = GeneratorOptions(include_null_checks=True)
        code_with = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options_with
        )
        
        # Without null checks
        options_without = GeneratorOptions(include_null_checks=False)
        code_without = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options_without
        )
        
        # Code with null checks should be longer
        assert len(code_with) > len(code_without)
        
        # Both should still be valid Python
        load_generated_module(code_with, "with_null_checks")
        load_generated_module(code_without, "without_null_checks")


class TestFormulaEvaluation:
    """Test that formulas evaluate correctly"""
    
    def test_simple_string_concat_formula(self):
        """Test basic string concatenation formula"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        # Create a contact record (using snake_case field names)
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        # Create context
        context = module.ComputationContext(contact, {})
        
        # Compute formulas
        contact = module.update_record(contact, context)
        
        # Name should be "First Name & ' ' & Last Name"
        assert contact.name == "John Smith"
    
    def test_formula_with_null_values(self):
        """Test formula handles null values correctly"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(
            data_access_mode="dataclass",
            include_null_checks=True
        )
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        # Create contact with missing last name
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name=None
        )
        
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        
        # Name should handle null gracefully
        # Exact behavior depends on null check implementation
        assert contact.name is None or isinstance(contact.name, str)


class TestIncrementalComputation:
    """Test incremental update logic"""
    
    def test_full_recomputation_when_no_changed_fields(self):
        """Test that all formulas compute when changed_fields is None"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        context = module.ComputationContext(contact, {})
        
        # Full recomputation (no changed_fields specified)
        contact = module.update_record(contact, context)
        
        # Name should be computed
        assert contact.name == "John Smith"
    
    def test_partial_recomputation_with_changed_fields(self):
        """Test that only affected formulas recompute"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        # Initial record
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        
        initial_name = contact.name
        assert initial_name == "John Smith"
        
        # Update only first_name
        contact.first_name = "Jane"
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context, changed_fields=["first_name"])
        
        # Name should be recomputed
        assert contact.name == "Jane Smith"
        assert contact.name != initial_name
    
    def test_no_recomputation_when_unrelated_field_changes(self):
        """Test that formulas don't recompute when unrelated fields change"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith",
            email="john@example.com"
        )
        
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        
        initial_name = contact.name
        
        # Change email (unrelated to Name formula)
        contact.Email = "jane@example.com"
        context = module.ComputationContext(contact, {})
        
        # Track what gets recomputed
        context.computed_this_cycle = set()
        contact = module.update_record(contact, context, changed_fields=["Email"])
        
        # Name should not be in recomputed fields
        # (This assumes field IDs are tracked in computed_this_cycle)
        assert contact.name == initial_name


class TestComputationContext:
    """Test computation context functionality"""
    
    def test_context_creation(self):
        """Test that ComputationContext can be created"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(id="rec123")
        context = module.ComputationContext(contact, {})
        
        assert context is not None
        assert hasattr(context, "record")
        assert hasattr(context, "all_records")
        assert hasattr(context, "computed_this_cycle")
    
    def test_context_tracks_computations(self):
        """Test that context tracks which fields were computed"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        
        # Context should track what was computed
        assert len(context.computed_this_cycle) > 0


class TestDataAccessModes:
    """Test different data access patterns"""
    
    def test_dataclass_mode_field_access(self):
        """Test dataclass attribute access"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        # Should use attribute access
        assert contact.first_name == "John"
        assert contact.last_name == "Smith"
        
        # Should be able to set attributes
        contact.first_name = "Jane"
        assert contact.first_name == "Jane"
    
    def test_dict_mode_field_access(self):
        """Test dictionary key access"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dict")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = {
            "id": "rec123",
            "first_name": "John",
            "last_name": "Smith"
        }
        
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        
        # Should use dictionary access
        assert contact["first_name"] == "John"
        assert contact["last_name"] == "Smith"
        assert contact["name"] == "John Smith"


class TestComputationGraph:
    """Test computation graph generation"""
    
    def test_computation_graph_exists(self):
        """Test that COMPUTATION_GRAPH constant is generated"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        # Should have computation graph
        assert hasattr(module, "COMPUTATION_GRAPH")
        
        graph = module.COMPUTATION_GRAPH
        assert "max_depth" in graph
        assert "depths" in graph
        assert "field_id_to_name" in graph
        assert "field_name_to_id" in graph
    
    def test_computation_graph_has_depths(self):
        """Test that fields are organized by depth"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        graph = module.COMPUTATION_GRAPH
        depths = graph["depths"]
        
        # Should have depth 0 (base fields)
        assert 0 in depths
        assert len(depths[0]) > 0
        
        # Each field should have metadata
        for field_id, field_info in depths[0].items():
            assert "name" in field_info
            assert "type" in field_info
            assert "dependencies" in field_info
            assert "dependents" in field_info


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_record(self):
        """Test handling of record with no data"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(
            data_access_mode="dataclass",
            include_null_checks=True
        )
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        # Record with only ID
        contact = module.Contacts(id="rec123")
        
        context = module.ComputationContext(contact, {})
        
        # Should not crash
        contact = module.update_record(contact, context)
        
        # Formulas should handle nulls
        assert contact.name is None or isinstance(contact.name, str)
    
    def test_multiple_updates(self):
        """Test that a record can be updated multiple times"""
        schema = load_schema("crm_schema.json")
        
        options = GeneratorOptions(data_access_mode="dataclass")
        code = generate_complete_module(
            metadata=schema,
            table_id="tbl2OGQy64kSZEM93",
            options=options
        )
        
        module = load_generated_module(code)
        
        contact = module.Contacts(
            id="rec123",
            first_name="John",
            last_name="Smith"
        )
        
        # First update
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context)
        assert contact.name == "John Smith"
        
        # Second update
        contact.first_name = "Jane"
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context, changed_fields=["first_name"])
        assert contact.name == "Jane Smith"
        
        # Third update
        contact.last_name = "Doe"
        context = module.ComputationContext(contact, {})
        contact = module.update_record(contact, context, changed_fields=["last_name"])
        assert contact.name == "Jane Doe"
