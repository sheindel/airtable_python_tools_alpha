"""Test suite for at_metadata_graph.py

Tests the core graph building and analysis functionality.
"""
import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from at_metadata_graph import metadata_to_graph, get_reachable_nodes
from at_types import AirtableMetadata


@pytest.fixture
def sample_metadata():
    """Sample Airtable metadata for testing."""
    return {
        "tables": [
            {
                "id": "tbl1",
                "name": "Test Table",
                "fields": [
                    {
                        "id": "fld1",
                        "name": "Name",
                        "type": "singleLineText",
                    },
                    {
                        "id": "fld2",
                        "name": "Price",
                        "type": "number",
                    },
                    {
                        "id": "fld3",
                        "name": "Total",
                        "type": "formula",
                        "options": {
                            "formula": "{fld2} * 1.1",
                            "referencedFieldIds": ["fld2"],
                        },
                    },
                    {
                        "id": "fld4",
                        "name": "Display",
                        "type": "formula",
                        "options": {
                            "formula": "{fld1} & ' - ' & {fld3}",
                            "referencedFieldIds": ["fld1", "fld3"],
                        },
                    },
                ]
            }
        ]
    }


def test_metadata_to_graph(sample_metadata):
    """Test basic graph construction from metadata."""
    graph = metadata_to_graph(sample_metadata)
    
    # Should have 4 field nodes + 1 table node
    assert len(graph.nodes) == 5
    
    # Check field nodes exist
    assert "fld1" in graph.nodes
    assert "fld2" in graph.nodes
    assert "fld3" in graph.nodes
    assert "fld4" in graph.nodes
    
    # Check table node exists
    assert "tbl1" in graph.nodes


def test_formula_dependencies(sample_metadata):
    """Test that formula dependencies are correctly captured."""
    graph = metadata_to_graph(sample_metadata)
    
    # fld3 (Total) depends on fld2 (Price)
    assert graph.has_edge("fld2", "fld3")
    assert graph.edges["fld2", "fld3"]["relationship"] == "formula"
    
    # fld4 (Display) depends on fld1 (Name) and fld3 (Total)
    assert graph.has_edge("fld1", "fld4")
    assert graph.has_edge("fld3", "fld4")


def test_get_reachable_nodes_backward(sample_metadata):
    """Test backward traversal (dependencies)."""
    graph = metadata_to_graph(sample_metadata)
    
    # Get dependencies of fld4 (Display)
    subgraph = get_reachable_nodes(graph, "fld4", direction="backward")
    
    # Should include fld4 itself, fld1 (Name), fld3 (Total), and fld2 (Price)
    node_ids = [n for n in subgraph.nodes if n.startswith("fld")]
    assert "fld4" in node_ids
    assert "fld1" in node_ids
    assert "fld3" in node_ids
    assert "fld2" in node_ids


def test_get_reachable_nodes_forward(sample_metadata):
    """Test forward traversal (dependents)."""
    graph = metadata_to_graph(sample_metadata)
    
    # Get dependents of fld2 (Price)
    subgraph = get_reachable_nodes(graph, "fld2", direction="forward")
    
    # Should include fld2 itself, fld3 (Total), and fld4 (Display)
    node_ids = [n for n in subgraph.nodes if n.startswith("fld")]
    assert "fld2" in node_ids
    assert "fld3" in node_ids
    assert "fld4" in node_ids
    # Should NOT include fld1 (Name) as it doesn't depend on fld2
    assert "fld1" not in node_ids


def test_empty_metadata():
    """Test handling of empty metadata."""
    empty_metadata = {"tables": []}
    graph = metadata_to_graph(empty_metadata)
    
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0


def test_field_without_dependencies(sample_metadata):
    """Test field with no dependencies."""
    graph = metadata_to_graph(sample_metadata)
    
    # fld1 (Name) has no dependencies
    predecessors = list(graph.predecessors("fld1"))
    field_predecessors = [p for p in predecessors if p.startswith("fld")]
    assert len(field_predecessors) == 0


# ============================================================================
# Phase 1: Formula Depth Calculator Tests
# ============================================================================

from at_metadata_graph import get_formula_depth, get_computation_order, get_computation_order_with_metadata


def test_get_formula_depth_basic_field(sample_metadata):
    """Test depth of basic field with no dependencies."""
    graph = metadata_to_graph(sample_metadata)
    
    # fld1 (Name) and fld2 (Price) are basic fields
    assert get_formula_depth("fld1", graph) == 0
    assert get_formula_depth("fld2", graph) == 0


def test_get_formula_depth_one_level(sample_metadata):
    """Test depth of formula with one level of dependencies."""
    graph = metadata_to_graph(sample_metadata)
    
    # fld3 (Total) depends only on fld2 (basic field)
    assert get_formula_depth("fld3", graph) == 1


def test_get_formula_depth_two_levels(sample_metadata):
    """Test depth of formula with two levels of dependencies."""
    graph = metadata_to_graph(sample_metadata)
    
    # fld4 (Display) depends on fld1 (depth 0) and fld3 (depth 1)
    # So fld4 should be depth 2
    assert get_formula_depth("fld4", graph) == 2


def test_get_formula_depth_invalid_field():
    """Test error handling for invalid field ID."""
    graph = metadata_to_graph({"tables": []})
    
    with pytest.raises(ValueError):
        get_formula_depth("invalid_field", graph)


def test_get_computation_order_basic(sample_metadata):
    """Test computation order grouping."""
    order = get_computation_order(sample_metadata)
    
    # Should have 3 depth levels (0, 1, 2)
    assert len(order) == 3
    
    # Depth 0: fld1 and fld2 (basic fields)
    assert set(order[0]) == {"fld1", "fld2"}
    
    # Depth 1: fld3 (depends on fld2)
    assert "fld3" in order[1]
    
    # Depth 2: fld4 (depends on fld3)
    assert "fld4" in order[2]


def test_get_computation_order_with_metadata_basic(sample_metadata):
    """Test computation order with metadata enrichment."""
    order = get_computation_order_with_metadata(sample_metadata)
    
    # Should have 3 depth levels
    assert len(order) == 3
    
    # Check depth 0 fields have correct metadata
    depth_0_names = {f["name"] for f in order[0]}
    assert "Name" in depth_0_names
    assert "Price" in depth_0_names
    
    # Check depth 1 field
    assert len(order[1]) >= 1
    assert any(f["name"] == "Total" for f in order[1])
    
    # Check depth 2 field
    assert len(order[2]) >= 1
    assert any(f["name"] == "Display" for f in order[2])


@pytest.fixture
def complex_metadata():
    """More complex metadata with multiple tables and dependencies."""
    return {
        "tables": [
            {
                "id": "tbl1",
                "name": "Orders",
                "fields": [
                    {
                        "id": "fld1",
                        "name": "Amount",
                        "type": "number",
                    },
                    {
                        "id": "fld2",
                        "name": "Tax",
                        "type": "formula",
                        "options": {
                            "formula": "{fld1} * 0.08",
                            "referencedFieldIds": ["fld1"],
                        },
                    },
                    {
                        "id": "fld3",
                        "name": "Total",
                        "type": "formula",
                        "options": {
                            "formula": "{fld1} + {fld2}",
                            "referencedFieldIds": ["fld1", "fld2"],
                        },
                    },
                    {
                        "id": "fld4",
                        "name": "Display",
                        "type": "formula",
                        "options": {
                            "formula": "'Total: ' & {fld3}",
                            "referencedFieldIds": ["fld3"],
                        },
                    },
                    {
                        "id": "fld5",
                        "name": "Status",
                        "type": "singleLineText",
                    },
                    {
                        "id": "fld6",
                        "name": "ComplexCalc",
                        "type": "formula",
                        "options": {
                            "formula": "IF({fld3} > 100, {fld4}, {fld5})",
                            "referencedFieldIds": ["fld3", "fld4", "fld5"],
                        },
                    },
                ]
            }
        ]
    }


def test_get_formula_depth_complex(complex_metadata):
    """Test depth calculation with more complex dependencies."""
    graph = metadata_to_graph(complex_metadata)
    
    # Basic fields: depth 0
    assert get_formula_depth("fld1", graph) == 0  # Amount
    assert get_formula_depth("fld5", graph) == 0  # Status
    
    # First level formulas: depth 1
    assert get_formula_depth("fld2", graph) == 1  # Tax (depends on Amount)
    
    # Second level formulas: depth 2
    assert get_formula_depth("fld3", graph) == 2  # Total (depends on Tax which is depth 1)
    
    # Third level formulas: depth 3
    assert get_formula_depth("fld4", graph) == 3  # Display (depends on Total which is depth 2)
    
    # Formula depending on multiple depths: takes max
    assert get_formula_depth("fld6", graph) == 4  # ComplexCalc (depends on fld4 which is depth 3)


def test_get_computation_order_complex(complex_metadata):
    """Test computation order with complex dependencies."""
    order = get_computation_order(complex_metadata)
    
    # Should have 5 depth levels (0 through 4)
    assert len(order) == 5
    
    # Depth 0: Amount and Status
    assert set(order[0]) == {"fld1", "fld5"}
    
    # Depth 1: Tax
    assert "fld2" in order[1]
    
    # Depth 2: Total
    assert "fld3" in order[2]
    
    # Depth 3: Display
    assert "fld4" in order[3]
    
    # Depth 4: ComplexCalc
    assert "fld6" in order[4]


@pytest.fixture
def lookup_metadata():
    """Metadata with lookup and rollup fields."""
    return {
        "tables": [
            {
                "id": "tbl1",
                "name": "Orders",
                "fields": [
                    {
                        "id": "fld1",
                        "name": "Customer",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl2",
                            "inverseLinkFieldId": "fld4",
                        },
                    },
                    {
                        "id": "fld2",
                        "name": "Customer Email",
                        "type": "multipleLookupValues",
                        "options": {
                            "recordLinkFieldId": "fld1",
                            "fieldIdInLinkedTable": "fld3",
                        },
                    },
                ]
            },
            {
                "id": "tbl2",
                "name": "Customers",
                "fields": [
                    {
                        "id": "fld3",
                        "name": "Email",
                        "type": "email",
                    },
                    {
                        "id": "fld4",
                        "name": "Orders",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl1",
                            "inverseLinkFieldId": "fld1",
                        },
                    },
                ]
            }
        ]
    }


def test_get_formula_depth_with_lookups(lookup_metadata):
    """Test depth calculation with lookup fields."""
    graph = metadata_to_graph(lookup_metadata)
    
    # Basic fields: depth 0
    assert get_formula_depth("fld3", graph) == 0  # Email (basic field)
    
    # Link fields: depth 0 (no dependencies)
    assert get_formula_depth("fld1", graph) == 0  # Customer link
    
    # Lookup fields: depth 1 (depends on both link and target field)
    assert get_formula_depth("fld2", graph) == 1  # Customer Email lookup


def test_get_computation_order_with_lookups(lookup_metadata):
    """Test computation order with lookup fields."""
    order = get_computation_order(lookup_metadata)
    
    # Should have 2 depth levels
    assert len(order) >= 2
    
    # Depth 0: Basic fields and links
    assert "fld3" in order[0]  # Email
    assert "fld1" in order[0]  # Customer link
    assert "fld4" in order[0]  # Orders link
    
    # Depth 1: Lookup
    assert "fld2" in order[1]  # Customer Email lookup


@pytest.fixture
def rollup_metadata():
    """Metadata with rollup fields."""
    return {
        "tables": [
            {
                "id": "tbl1",
                "name": "Orders",
                "fields": [
                    {
                        "id": "fld1",
                        "name": "Items",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl2",
                            "inverseLinkFieldId": "fld4",
                        },
                    },
                    {
                        "id": "fld2",
                        "name": "Total Value",
                        "type": "rollup",
                        "options": {
                            "recordLinkFieldId": "fld1",
                            "fieldIdInLinkedTable": "fld3",
                        },
                    },
                    {
                        "id": "fld5",
                        "name": "With Tax",
                        "type": "formula",
                        "options": {
                            "formula": "{fld2} * 1.08",
                            "referencedFieldIds": ["fld2"],
                        },
                    },
                ]
            },
            {
                "id": "tbl2",
                "name": "Items",
                "fields": [
                    {
                        "id": "fld3",
                        "name": "Price",
                        "type": "number",
                    },
                    {
                        "id": "fld4",
                        "name": "Order",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl1",
                            "inverseLinkFieldId": "fld1",
                        },
                    },
                ]
            }
        ]
    }


def test_get_formula_depth_with_rollups(rollup_metadata):
    """Test depth calculation with rollup fields."""
    graph = metadata_to_graph(rollup_metadata)
    
    # Basic fields: depth 0
    assert get_formula_depth("fld3", graph) == 0  # Price
    
    # Link fields: depth 0
    assert get_formula_depth("fld1", graph) == 0  # Items link
    
    # Rollup fields: depth 1 (depends on link and target field)
    assert get_formula_depth("fld2", graph) == 1  # Total Value rollup
    
    # Formula depending on rollup: depth 2
    assert get_formula_depth("fld5", graph) == 2  # With Tax


def test_get_computation_order_with_rollups(rollup_metadata):
    """Test computation order with rollup fields."""
    order = get_computation_order(rollup_metadata)
    
    # Should have 3 depth levels
    assert len(order) >= 3
    
    # Depth 0: Basic fields and links
    assert "fld3" in order[0]  # Price
    assert "fld1" in order[0]  # Items link
    
    # Depth 1: Rollup
    assert "fld2" in order[1]  # Total Value rollup
    
    # Depth 2: Formula depending on rollup
    assert "fld5" in order[2]  # With Tax


def test_empty_metadata_computation_order():
    """Test computation order with empty metadata."""
    order = get_computation_order({"tables": []})
    
    # Should return empty list or list with empty sublists
    assert len(order) == 0 or all(len(level) == 0 for level in order)


def test_get_computation_order_preserves_all_fields(complex_metadata):
    """Test that all fields appear exactly once in computation order."""
    order = get_computation_order(complex_metadata)
    
    # Flatten the order
    all_fields = []
    for level in order:
        all_fields.extend(level)
    
    # Should have all 6 fields, each appearing exactly once
    assert len(all_fields) == 6
    assert len(set(all_fields)) == 6  # No duplicates
    assert set(all_fields) == {"fld1", "fld2", "fld3", "fld4", "fld5", "fld6"}
