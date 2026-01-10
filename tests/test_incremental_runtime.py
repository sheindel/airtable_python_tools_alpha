"""
Tests for incremental runtime generator

Tests the computation graph building and code generation logic.
"""

import sys
from pathlib import Path

# Add web directory to path before importing web modules
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

import pytest
from code_generators.incremental_runtime_generator import (
    build_computation_graph,
    GeneratorOptions,
    ComputationGraph,
    FieldInfo,
    _to_snake_case,
)
from constants import FIELD_TYPE_FORMULA, FIELD_TYPE_TEXT


@pytest.fixture
def simple_metadata():
    """Simple metadata with a basic formula field"""
    return {
        "tables": [
            {
                "id": "tbl123",
                "name": "Contacts",
                "fields": [
                    {
                        "id": "fld001",
                        "name": "First Name",
                        "type": "singleLineText"
                    },
                    {
                        "id": "fld002",
                        "name": "Last Name",
                        "type": "singleLineText"
                    },
                    {
                        "id": "fld003",
                        "name": "Full Name",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fld001}&\" \"&{fld002}",
                            "referencedFieldIds": ["fld001", "fld002"],
                            "result": {"type": "singleLineText"}
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def cascading_metadata():
    """Metadata with cascading formulas (depth > 1)"""
    return {
        "tables": [
            {
                "id": "tbl123",
                "name": "Contacts",
                "fields": [
                    {
                        "id": "fld001",
                        "name": "First Name",
                        "type": "singleLineText"
                    },
                    {
                        "id": "fld002",
                        "name": "Last Name",
                        "type": "singleLineText"
                    },
                    {
                        "id": "fld003",
                        "name": "Full Name",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "{fld001}&\" \"&{fld002}",
                            "referencedFieldIds": ["fld001", "fld002"],
                            "result": {"type": "singleLineText"}
                        }
                    },
                    {
                        "id": "fld004",
                        "name": "Greeting",
                        "type": "formula",
                        "options": {
                            "isValid": True,
                            "formula": "\"Hello, \"&{fld003}",
                            "referencedFieldIds": ["fld003"],
                            "result": {"type": "singleLineText"}
                        }
                    }
                ]
            }
        ]
    }


class TestComputationGraphBuilder:
    """Test computation graph building from metadata"""
    
    def test_simple_graph_structure(self, simple_metadata):
        """Test basic graph structure with one formula"""
        graph = build_computation_graph(simple_metadata)
        
        # Check basic structure
        assert isinstance(graph, ComputationGraph)
        assert graph.max_depth >= 1  # At least 2 depths (0 and 1)
        assert len(graph.depths) >= 2
        
        # Check depth 0 has basic fields
        depth_0 = graph.get_fields_at_depth(0)
        assert "fld001" in depth_0  # First Name
        assert "fld002" in depth_0  # Last Name
        
        # Check depth 1 has formula field
        depth_1 = graph.get_fields_at_depth(1)
        assert "fld003" in depth_1  # Full Name
        
        # Check field info
        full_name_field = depth_1["fld003"]
        assert full_name_field.name == "Full Name"
        assert full_name_field.field_type == FIELD_TYPE_FORMULA
        assert full_name_field.depth == 1
        assert "fld001" in full_name_field.dependencies
        assert "fld002" in full_name_field.dependencies
    
    def test_cascading_formulas(self, cascading_metadata):
        """Test formulas that depend on other formulas"""
        graph = build_computation_graph(cascading_metadata)
        
        # Should have at least 3 depths (0, 1, 2)
        assert graph.max_depth >= 2
        
        # Depth 0: Basic fields
        depth_0 = graph.get_fields_at_depth(0)
        assert "fld001" in depth_0  # First Name
        assert "fld002" in depth_0  # Last Name
        
        # Depth 1: Full Name (depends on First + Last)
        depth_1 = graph.get_fields_at_depth(1)
        assert "fld003" in depth_1  # Full Name
        full_name = depth_1["fld003"]
        assert set(full_name.dependencies) == {"fld001", "fld002"}
        
        # Depth 2: Greeting (depends on Full Name)
        depth_2 = graph.get_fields_at_depth(2)
        assert "fld004" in depth_2  # Greeting
        greeting = depth_2["fld004"]
        assert "fld003" in greeting.dependencies
    
    def test_field_id_name_mappings(self, simple_metadata):
        """Test bidirectional field ID/name mappings"""
        graph = build_computation_graph(simple_metadata)
        
        # Test field_id_to_name
        assert graph.field_id_to_name["fld001"] == "First Name"
        assert graph.field_id_to_name["fld002"] == "Last Name"
        assert graph.field_id_to_name["fld003"] == "Full Name"
        
        # Test field_name_to_id
        assert graph.field_name_to_id["First Name"] == "fld001"
        assert graph.field_name_to_id["Last Name"] == "fld002"
        assert graph.field_name_to_id["Full Name"] == "fld003"
    
    def test_function_name_generation(self, simple_metadata):
        """Test that computed fields get function names"""
        graph = build_computation_graph(simple_metadata)
        
        # Basic fields should not have function names
        first_name = graph.get_field("fld001")
        assert first_name.function_name is None
        
        # Formula fields should have function names
        full_name = graph.get_field("fld003")
        assert full_name.function_name == "compute_full_name"
    
    def test_get_computed_fields(self, cascading_metadata):
        """Test getting all computed fields"""
        graph = build_computation_graph(cascading_metadata)
        
        computed = graph.get_computed_fields()
        computed_names = {f.name for f in computed}
        
        assert "Full Name" in computed_names
        assert "Greeting" in computed_names
        assert "First Name" not in computed_names  # Not computed
        assert "Last Name" not in computed_names   # Not computed


class TestHelperFunctions:
    """Test helper utility functions"""
    
    def test_to_snake_case(self):
        """Test snake_case conversion"""
        assert _to_snake_case("First Name") == "first_name"
        assert _to_snake_case("Full Name") == "full_name"
        assert _to_snake_case("EmailAddress") == "email_address"
        assert _to_snake_case("DM Email") == "dm_email"
        assert _to_snake_case("Field123") == "field123"
        assert _to_snake_case("Multi  Space") == "multi_space"
        assert _to_snake_case("Field_With_Underscores") == "field_with_underscores"


class TestGeneratorOptions:
    """Test generator options dataclass"""
    
    def test_default_options(self):
        """Test default option values"""
        opts = GeneratorOptions()
        
        assert opts.data_access_mode == "dataclass"
        assert opts.include_null_checks is True
        assert opts.include_type_hints is True
        assert opts.include_docstrings is True
        assert opts.include_examples is False
        assert opts.optimize_depth_skipping is True
        assert opts.track_computation_stats is False
        assert opts.output_format == "single_file"
        assert opts.include_tests is False
    
    def test_custom_options(self):
        """Test creating custom options"""
        opts = GeneratorOptions(
            data_access_mode="dict",
            include_null_checks=False,
            include_examples=True
        )
        
        assert opts.data_access_mode == "dict"
        assert opts.include_null_checks is False
        assert opts.include_examples is True


# TODO: Phase 3 - Add tests for update function generation
# TODO: Phase 4 - Add tests for complete module generation
# TODO: Phase 5 - Add integration tests with real formula evaluation


# ============================================================================
# Phase 2 Tests: Formula Function Generation
# ============================================================================

class TestFormulaFunctionGeneration:
    """Test generation of formula computation functions"""
    
    def test_generate_simple_formula(self, simple_metadata):
        """Test generating a simple formula function"""
        from code_generators.incremental_runtime_generator import (
            generate_formula_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        full_name_field = graph.get_field("fld003")
        
        options = GeneratorOptions()
        func_code = generate_formula_function(full_name_field, simple_metadata, options)
        
        # Check function structure
        assert "def compute_full_name(" in func_code
        assert "context:" in func_code
        assert "return" in func_code
        
        # Check docstring
        assert "Compute Full Name field" in func_code
        assert "Dependencies:" in func_code
        
        # Check that it includes inline null checks in the transpiled formula
        # (Formula fields don't have upfront null checks, but the transpiled code
        # handles None values inline)
        assert "is not None" in func_code
    
    def test_generate_formula_without_null_checks(self, simple_metadata):
        """Test formula generation with null checks disabled"""
        from code_generators.incremental_runtime_generator import (
            generate_formula_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        full_name_field = graph.get_field("fld003")
        
        options = GeneratorOptions(include_null_checks=False)
        func_code = generate_formula_function(full_name_field, simple_metadata, options)
        
        # Should not have null check section
        assert "# Null safety check" not in func_code
    
    def test_generate_formula_without_docstrings(self, simple_metadata):
        """Test formula generation without docstrings"""
        from code_generators.incremental_runtime_generator import (
            generate_formula_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        full_name_field = graph.get_field("fld003")
        
        options = GeneratorOptions(include_docstrings=False)
        func_code = generate_formula_function(full_name_field, simple_metadata, options)
        
        # Should not have docstring
        assert '"""' not in func_code
    
    def test_generate_formula_dict_mode(self, simple_metadata):
        """Test formula generation for dict data access mode"""
        from code_generators.incremental_runtime_generator import (
            generate_formula_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        full_name_field = graph.get_field("fld003")
        
        options = GeneratorOptions(data_access_mode="dict")
        func_code = generate_formula_function(full_name_field, simple_metadata, options)
        
        # Dict mode should use record.get() for null checks
        assert 'record.get(' in func_code or 'record[' in func_code
    
    def test_generate_formula_missing_metadata(self):
        """Test formula generation with missing metadata"""
        from code_generators.incremental_runtime_generator import (
            generate_formula_function,
            GeneratorOptions,
            FieldInfo
        )
        
        # Create field with no metadata
        field_info = FieldInfo(
            field_id="fld999",
            name="Test Field",
            field_type="formula",
            table_id="tbl123",
            table_name="Test Table",
            depth=1,
            dependencies=[],
            dependents=[],
            metadata=None  # Missing metadata
        )
        
        options = GeneratorOptions()
        func_code = generate_formula_function(field_info, {"tables": []}, options)
        
        # Should generate stub function
        assert "def compute_test_field(" in func_code
        assert "Stub" in func_code
        assert "return None" in func_code


class TestLookupFunctionGeneration:
    """Test generation of lookup computation functions"""
    
    @pytest.fixture
    def lookup_metadata(self):
        """Metadata with lookup field"""
        return {
            "tables": [
                {
                    "id": "tblContacts",
                    "name": "Contacts",
                    "fields": [
                        {
                            "id": "fldCompanyLink",
                            "name": "Company",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tblCompanies"}
                        },
                        {
                            "id": "fldCompanyName",
                            "name": "Company Name",
                            "type": "multipleLookupValues",
                            "options": {
                                "recordLinkFieldId": "fldCompanyLink",
                                "fieldIdInLinkedTable": "fldName"
                            }
                        }
                    ]
                },
                {
                    "id": "tblCompanies",
                    "name": "Companies",
                    "fields": [
                        {
                            "id": "fldName",
                            "name": "Name",
                            "type": "singleLineText"
                        }
                    ]
                }
            ]
        }
    
    def test_generate_lookup_function(self, lookup_metadata):
        """Test generating a lookup function"""
        from code_generators.incremental_runtime_generator import (
            generate_lookup_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(lookup_metadata)
        lookup_field = graph.get_field("fldCompanyName")
        
        options = GeneratorOptions()
        func_code = generate_lookup_function(lookup_field, lookup_metadata, options)
        
        # Check function structure
        assert "def compute_company_name(" in func_code
        assert "context.lookup(" in func_code
        assert "return" in func_code
        
        # Check docstring
        assert "Lookup Company Name" in func_code
    
    def test_generate_lookup_missing_config(self):
        """Test lookup generation with missing configuration"""
        from code_generators.incremental_runtime_generator import (
            generate_lookup_function,
            GeneratorOptions,
            FieldInfo
        )
        
        field_info = FieldInfo(
            field_id="fld999",
            name="Test Lookup",
            field_type="multipleLookupValues",
            table_id="tbl123",
            table_name="Test Table",
            depth=1,
            dependencies=[],
            dependents=[],
            metadata={"options": {}}  # Empty options
        )
        
        options = GeneratorOptions()
        func_code = generate_lookup_function(field_info, {"tables": []}, options)
        
        # Should generate stub
        assert "Stub" in func_code
        assert "return None" in func_code


class TestRollupFunctionGeneration:
    """Test generation of rollup computation functions"""
    
    @pytest.fixture
    def rollup_metadata(self):
        """Metadata with rollup field"""
        return {
            "tables": [
                {
                    "id": "tblCompanies",
                    "name": "Companies",
                    "fields": [
                        {
                            "id": "fldDeals",
                            "name": "Deals",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tblDeals"}
                        },
                        {
                            "id": "fldTotalRevenue",
                            "name": "Total Revenue",
                            "type": "rollup",
                            "options": {
                                "recordLinkFieldId": "fldDeals",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "SUM"
                            }
                        }
                    ]
                },
                {
                    "id": "tblDeals",
                    "name": "Deals",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "currency"
                        }
                    ]
                }
            ]
        }
    
    def test_generate_rollup_function(self, rollup_metadata):
        """Test generating a rollup function"""
        from code_generators.incremental_runtime_generator import (
            generate_rollup_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(rollup_metadata)
        rollup_field = graph.get_field("fldTotalRevenue")
        
        options = GeneratorOptions()
        func_code = generate_rollup_function(rollup_field, rollup_metadata, options)
        
        # Check function structure
        assert "def compute_total_revenue(" in func_code
        assert "context.rollup(" in func_code
        assert "SUM" in func_code
        assert "return" in func_code
        
        # Check docstring
        assert "Rollup Total Revenue" in func_code
    
    def test_generate_rollup_with_different_aggregations(self, rollup_metadata):
        """Test rollup with various aggregation functions"""
        from code_generators.incremental_runtime_generator import (
            generate_rollup_function,
            GeneratorOptions,
            build_computation_graph
        )
        
        # Test COUNT aggregation
        rollup_metadata["tables"][0]["fields"][1]["options"]["aggregationFunction"] = "COUNT"
        graph = build_computation_graph(rollup_metadata)
        rollup_field = graph.get_field("fldTotalRevenue")
        
        options = GeneratorOptions()
        func_code = generate_rollup_function(rollup_field, rollup_metadata, options)
        
        assert "COUNT" in func_code
        assert "context.rollup(" in func_code


# ============================================================================
# Phase 3 Tests: Update Function and Context Generation
# ============================================================================

class TestComputationContextGeneration:
    """Test generation of ComputationContext class"""
    
    def test_generate_context_class_basic(self, simple_metadata):
        """Test basic context class generation"""
        from code_generators.incremental_runtime_generator import (
            generate_computation_context_class,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions()
        
        context_code = generate_computation_context_class(graph, options)
        
        # Check class structure
        assert "class ComputationContext:" in context_code
        assert "def __init__(" in context_code
        assert "def get_linked_records(" in context_code
        assert "def lookup(" in context_code
        assert "def rollup(" in context_code
        
        # Check that it tracks computed fields
        assert "computed_this_cycle" in context_code
    
    def test_context_class_with_type_hints(self, simple_metadata):
        """Test context class generation with type hints"""
        from code_generators.incremental_runtime_generator import (
            generate_computation_context_class,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions(include_type_hints=True)
        
        context_code = generate_computation_context_class(graph, options)
        
        # Check type hints
        assert "-> List[Any]" in context_code or "List[Any]" in context_code
    
    def test_context_class_without_docstrings(self, simple_metadata):
        """Test context class generation without docstrings"""
        from code_generators.incremental_runtime_generator import (
            generate_computation_context_class,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions(include_docstrings=False)
        
        context_code = generate_computation_context_class(graph, options)
        
        # Should have minimal docstrings
        assert context_code.count('"""') <= 2  # At most class docstring
    
    def test_context_rollup_aggregations(self, simple_metadata):
        """Test that rollup method includes all aggregation functions"""
        from code_generators.incremental_runtime_generator import (
            generate_computation_context_class,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions()
        
        context_code = generate_computation_context_class(graph, options)
        
        # Check all aggregation types
        assert "SUM" in context_code
        assert "AVG" in context_code
        assert "COUNT" in context_code
        assert "MAX" in context_code
        assert "MIN" in context_code
        assert "AND" in context_code
        assert "OR" in context_code
        assert "CONCATENATE" in context_code


class TestUpdateFunctionGeneration:
    """Test generation of update_record() function"""
    
    def test_generate_update_function_basic(self, simple_metadata):
        """Test basic update function generation"""
        from code_generators.incremental_runtime_generator import (
            generate_update_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions()
        
        update_code = generate_update_function(graph, options)
        
        # Check function structure
        assert "def update_record(" in update_code
        assert "changed_fields" in update_code
        assert "for depth in range(" in update_code
        assert "should_compute" in update_code
        assert "return record" in update_code
    
    def test_update_function_with_type_hints(self, simple_metadata):
        """Test update function with type hints"""
        from code_generators.incremental_runtime_generator import (
            generate_update_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions(include_type_hints=True)
        
        update_code = generate_update_function(graph, options)
        
        # Check type hints
        assert "ComputationContext" in update_code
        assert "Optional[List[str]]" in update_code or "changed_fields: Optional" in update_code
    
    def test_update_function_with_stats_tracking(self, simple_metadata):
        """Test update function with computation stats tracking"""
        from code_generators.incremental_runtime_generator import (
            generate_update_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions(track_computation_stats=True)
        
        update_code = generate_update_function(graph, options)
        
        # Check stats tracking
        assert "computation_stats" in update_code
        assert "computed" in update_code
        assert "skipped" in update_code
    
    def test_update_function_with_depth_optimization(self, cascading_metadata):
        """Test update function with depth skipping optimization"""
        from code_generators.incremental_runtime_generator import (
            generate_update_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(cascading_metadata)
        options = GeneratorOptions(optimize_depth_skipping=True)
        
        update_code = generate_update_function(graph, options)
        
        # Check optimization
        assert "Skip entire depth" in update_code or "skip" in update_code.lower()
    
    def test_update_function_uses_computation_graph(self, simple_metadata):
        """Test that update function references COMPUTATION_GRAPH"""
        from code_generators.incremental_runtime_generator import (
            generate_update_function,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions()
        
        update_code = generate_update_function(graph, options)
        
        # Check COMPUTATION_GRAPH references
        assert "COMPUTATION_GRAPH" in update_code
        assert "FIELD_COMPUTERS" in update_code
        assert "COMPUTED_FIELD_TYPES" in update_code


class TestHelperGenerators:
    """Test helper generator functions"""
    
    def test_generate_field_computers_mapping(self, simple_metadata):
        """Test generating field computers mapping"""
        from code_generators.incremental_runtime_generator import (
            generate_field_computers_mapping,
            GeneratorOptions
        )
        
        graph = build_computation_graph(simple_metadata)
        options = GeneratorOptions()
        
        mapping_code = generate_field_computers_mapping(graph, simple_metadata, options)
        
        # Check structure
        assert "FIELD_COMPUTERS" in mapping_code
        assert "{" in mapping_code
        assert "}" in mapping_code
        
        # Check that formula fields are included
        assert "full_name" in mapping_code or "compute_full_name" in mapping_code
    
    def test_generate_computation_graph_data(self, cascading_metadata):
        """Test generating computation graph data structure"""
        from code_generators.incremental_runtime_generator import (
            generate_computation_graph_data,
            GeneratorOptions
        )
        
        graph = build_computation_graph(cascading_metadata)
        options = GeneratorOptions()
        
        graph_code = generate_computation_graph_data(graph, options)
        
        # Check structure
        assert "COMPUTATION_GRAPH" in graph_code
        assert "'max_depth':" in graph_code
        assert "'depths':" in graph_code
        assert "'field_id_to_name':" in graph_code
        assert "'field_name_to_id':" in graph_code
        assert "'table_fields':" in graph_code
        
        # Check that it includes field data
        assert "fld001" in graph_code  # Field IDs
        assert "dependencies" in graph_code
        assert "dependents" in graph_code
    
    def test_generate_linked_table_map(self, simple_metadata):
        """Test generating linked table map"""
        from code_generators.incremental_runtime_generator import (
            generate_linked_table_map
        )
        
        # Add a link field to metadata
        link_metadata = {
            "tables": [
                {
                    "id": "tblContacts",
                    "name": "Contacts",
                    "fields": [
                        {
                            "id": "fldCompany",
                            "name": "Company",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tblCompanies"}
                        }
                    ]
                },
                {
                    "id": "tblCompanies",
                    "name": "Companies",
                    "fields": []
                }
            ]
        }
        
        graph = build_computation_graph(link_metadata)
        map_code = generate_linked_table_map(graph, link_metadata)
        
        # Check structure
        assert "LINKED_TABLE_MAP" in map_code
        assert "company" in map_code or "Company" in map_code
        assert "tblCompanies" in map_code


class TestCompleteModuleGeneration:
    """Test complete module generation (Phase 3 integration)"""
    
    def test_generate_complete_module_structure(self, simple_metadata):
        """Test that complete module has all required sections"""
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions
        )
        
        options = GeneratorOptions()
        module_code = generate_complete_module(simple_metadata, options=options)
        
        # Check all sections are present
        assert "from dataclasses import dataclass" in module_code
        assert "class ComputationContext:" in module_code
        assert "COMPUTATION_GRAPH" in module_code
        assert "FIELD_COMPUTERS" in module_code
        assert "def update_record(" in module_code
        
        # Check formula functions are included
        assert "def compute_full_name(" in module_code
    
    def test_generate_complete_module_with_options(self, cascading_metadata):
        """Test complete module generation with custom options"""
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions
        )
        
        options = GeneratorOptions(
            include_null_checks=False,
            include_docstrings=False,
            track_computation_stats=True
        )
        
        module_code = generate_complete_module(cascading_metadata, options=options)
        
        # Check options are applied
        assert "computation_stats" in module_code  # Stats tracking enabled
        # Fewer docstrings
        docstring_count = module_code.count('"""')
        assert docstring_count < 20  # Arbitrary but should be low
    
    def test_generated_module_is_valid_python(self, simple_metadata):
        """Test that generated module is syntactically valid Python"""
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions
        )
        
        options = GeneratorOptions()
        module_code = generate_complete_module(simple_metadata, options=options)
        
        # Try to compile it
        try:
            compile(module_code, "<generated>", "exec")
            is_valid = True
        except SyntaxError:
            is_valid = False
        
        assert is_valid, "Generated module has syntax errors"
    
    def test_complete_module_with_lookups_and_rollups(self):
        """Test complete module generation with lookup and rollup fields"""
        from code_generators.incremental_runtime_generator import (
            generate_complete_module,
            GeneratorOptions
        )
        
        # Create metadata with lookup and rollup
        metadata = {
            "tables": [
                {
                    "id": "tblContacts",
                    "name": "Contacts",
                    "fields": [
                        {
                            "id": "fldCompanyLink",
                            "name": "Company",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tblCompanies"}
                        },
                        {
                            "id": "fldCompanyName",
                            "name": "Company Name",
                            "type": "multipleLookupValues",
                            "options": {
                                "recordLinkFieldId": "fldCompanyLink",
                                "fieldIdInLinkedTable": "fldName"
                            }
                        }
                    ]
                },
                {
                    "id": "tblCompanies",
                    "name": "Companies",
                    "fields": [
                        {
                            "id": "fldName",
                            "name": "Name",
                            "type": "singleLineText"
                        },
                        {
                            "id": "fldDeals",
                            "name": "Deals",
                            "type": "multipleRecordLinks",
                            "options": {"linkedTableId": "tblDeals"}
                        },
                        {
                            "id": "fldRevenue",
                            "name": "Total Revenue",
                            "type": "rollup",
                            "options": {
                                "recordLinkFieldId": "fldDeals",
                                "fieldIdInLinkedTable": "fldAmount",
                                "aggregationFunction": "SUM"
                            }
                        }
                    ]
                },
                {
                    "id": "tblDeals",
                    "name": "Deals",
                    "fields": [
                        {
                            "id": "fldAmount",
                            "name": "Amount",
                            "type": "currency"
                        }
                    ]
                }
            ]
        }
        
        options = GeneratorOptions()
        module_code = generate_complete_module(metadata, options=options)
        
        # Check lookup function
        assert "def compute_company_name(" in module_code
        assert "context.lookup(" in module_code
        
        # Check rollup function
        assert "def compute_total_revenue(" in module_code
        assert "context.rollup(" in module_code
        
        # Check linked table map
        assert "LINKED_TABLE_MAP" in module_code


# TODO: Phase 4 - Add tests for type definition generation
# TODO: Phase 5 - Add integration tests with real formula evaluation
