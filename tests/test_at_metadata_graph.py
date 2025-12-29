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
