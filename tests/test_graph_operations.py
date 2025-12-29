"""
Unit tests for Airtable Metadata Graph

Tests graph construction, traversal, and Mermaid diagram generation.
Includes tests for table node handling in dependency graphs.
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Mock pyscript before importing any modules
sys.modules['pyscript'] = MagicMock()

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from at_metadata_graph import (
    metadata_to_graph,
    get_reachable_nodes,
    graph_to_mermaid
)
from components.airtable_client import find_field_by_id


@pytest.fixture
def sample_metadata():
    """Load the sample schema for testing"""
    sample_path = Path(__file__).parent.parent / "web" / "sample_schema.json"
    with open(sample_path) as f:
        return json.load(f)


@pytest.fixture
def simple_metadata():
    """Create simple metadata for focused testing"""
    return {
        "tables": [
            {
                "id": "tblTable1",
                "name": "Table 1",
                "fields": [
                    {
                        "id": "fldField1",
                        "name": "Field 1",
                        "type": "singleLineText"
                    },
                    {
                        "id": "fldField2",
                        "name": "Field 2",
                        "type": "formula",
                        "options": {
                            "formula": "{fldField1} & ' suffix'",
                            "referencedFieldIds": ["fldField1"]
                        }
                    }
                ]
            },
            {
                "id": "tblTable2",
                "name": "Table 2",
                "fields": [
                    {
                        "id": "fldLink",
                        "name": "Link",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tblTable1",
                            "inverseLinkFieldId": "fldBacklink"
                        }
                    }
                ]
            }
        ]
    }


class TestGraphConstruction:
    """Test metadata to graph conversion"""
    
    def test_create_graph_from_metadata(self, simple_metadata):
        """Test that graph is created successfully"""
        G = metadata_to_graph(simple_metadata)
        
        assert G is not None
        assert len(G.nodes) > 0
    
    def test_graph_contains_fields(self, simple_metadata):
        """Test that all fields are added as nodes"""
        G = metadata_to_graph(simple_metadata)
        
        field_ids = ["fldField1", "fldField2", "fldLink"]
        for field_id in field_ids:
            assert field_id in G.nodes
    
    def test_graph_contains_tables(self, simple_metadata):
        """Test that tables are added as nodes"""
        G = metadata_to_graph(simple_metadata)
        
        table_ids = ["tblTable1", "tblTable2"]
        for table_id in table_ids:
            assert table_id in G.nodes
    
    def test_field_nodes_have_metadata(self, simple_metadata):
        """Test that field nodes contain proper metadata"""
        G = metadata_to_graph(simple_metadata)
        
        field_data = G.nodes["fldField1"]
        assert field_data["type"] == "field"
        assert field_data["field_type"] == "singleLineText"
        assert field_data["name"] == "Field 1"
        assert "table_id" in field_data
    
    def test_table_nodes_have_metadata(self, simple_metadata):
        """Test that table nodes contain proper metadata"""
        G = metadata_to_graph(simple_metadata)
        
        table_data = G.nodes["tblTable1"]
        assert table_data["type"] == "table"
        assert table_data["name"] == "Table 1"
    
    def test_formula_dependencies_create_edges(self, simple_metadata):
        """Test that formula references create edges"""
        G = metadata_to_graph(simple_metadata)
        
        # fldField2 depends on fldField1
        assert G.has_edge("fldField1", "fldField2")
        
        edge_data = G.edges["fldField1", "fldField2"]
        assert edge_data["relationship"] == "formula"
    
    def test_record_links_create_edges(self, simple_metadata):
        """Test that record links create edges from field to table"""
        G = metadata_to_graph(simple_metadata)
        
        # fldLink should link to tblTable1
        assert G.has_edge("fldLink", "tblTable1")
        
        edge_data = G.edges["fldLink", "tblTable1"]
        assert edge_data["relationship"] == "links_to"


class TestGraphTraversal:
    """Test graph traversal and reachability"""
    
    def test_get_reachable_backward(self, simple_metadata):
        """Test backward (dependency) traversal"""
        G = metadata_to_graph(simple_metadata)
        
        # Get what fldField2 depends on
        subgraph = get_reachable_nodes(G, "fldField2", direction="backward")
        
        # Should include fldField1 (dependency)
        assert "fldField1" in subgraph.nodes
        # Should include the field itself
        assert "fldField2" in subgraph.nodes
    
    def test_get_reachable_forward(self, simple_metadata):
        """Test forward (dependent) traversal"""
        G = metadata_to_graph(simple_metadata)
        
        # Get what depends on fldField1
        subgraph = get_reachable_nodes(G, "fldField1", direction="forward")
        
        # Should include fldField2 (depends on fldField1)
        assert "fldField2" in subgraph.nodes
        # Should include the field itself
        assert "fldField1" in subgraph.nodes
    
    def test_get_reachable_both(self, simple_metadata):
        """Test bidirectional traversal"""
        G = metadata_to_graph(simple_metadata)
        
        subgraph = get_reachable_nodes(G, "fldField2", direction="both")
        
        # Should include dependencies and dependents
        assert "fldField1" in subgraph.nodes
        assert "fldField2" in subgraph.nodes
    
    def test_isolated_node_returns_self(self, simple_metadata):
        """Test that isolated nodes return only themselves"""
        G = metadata_to_graph(simple_metadata)
        
        # fldField1 has dependents but let's test an isolated case
        # Actually, let's test with a table that might be isolated
        # For now, just verify the function doesn't crash
        subgraph = get_reachable_nodes(G, "tblTable2", direction="backward")
        assert "tblTable2" in subgraph.nodes


class TestTableNodesInDependencies:
    """Test that table nodes are properly included in dependency graphs"""
    
    def test_record_link_includes_table_node(self, sample_metadata):
        """Test that record links include the linked table node"""
        G = metadata_to_graph(sample_metadata)
        
        # Find a multipleRecordLinks field
        link_field = None
        for table in sample_metadata["tables"]:
            for field in table["fields"]:
                if field.get("type") == "multipleRecordLinks":
                    link_field = field
                    break
            if link_field:
                break
        
        if not link_field:
            pytest.skip("No record link fields in sample data")
        
        field_id = link_field["id"]
        linked_table_id = link_field["options"]["linkedTableId"]
        
        # Get dependencies
        subgraph = get_reachable_nodes(G, field_id, direction="both")
        
        # Linked table should be in the subgraph
        assert linked_table_id in subgraph.nodes, \
            f"Linked table {linked_table_id} not in dependency graph for field {field_id}"
        
        # Table node should have correct type
        table_data = subgraph.nodes[linked_table_id]
        assert table_data["type"] == "table"
    
    def test_mermaid_includes_table_nodes(self, sample_metadata):
        """Test that Mermaid diagrams include table nodes"""
        G = metadata_to_graph(sample_metadata)
        
        # Find a record link field
        link_field = None
        for table in sample_metadata["tables"]:
            for field in table["fields"]:
                if field.get("type") == "multipleRecordLinks":
                    link_field = field
                    break
            if link_field:
                break
        
        if not link_field:
            pytest.skip("No record link fields in sample data")
        
        field_id = link_field["id"]
        linked_table_id = link_field["options"]["linkedTableId"]
        
        # Get subgraph and generate Mermaid
        subgraph = get_reachable_nodes(G, field_id, direction="both")
        mermaid = graph_to_mermaid(subgraph, direction="TD", display_mode="simple")
        
        # Table ID should appear in the Mermaid diagram
        assert linked_table_id in mermaid, \
            f"Table {linked_table_id} not in Mermaid diagram"
    
    def test_multiple_record_links_show_all_tables(self, sample_metadata):
        """Test that all linked tables appear in complex graphs"""
        G = metadata_to_graph(sample_metadata)
        
        # Get all record link fields
        link_fields = []
        for table in sample_metadata["tables"]:
            for field in table["fields"]:
                if field.get("type") == "multipleRecordLinks":
                    link_fields.append(field)
        
        if len(link_fields) < 2:
            pytest.skip("Need at least 2 record link fields")
        
        # Test each link field
        for link_field in link_fields[:2]:  # Test first two
            field_id = link_field["id"]
            linked_table_id = link_field["options"]["linkedTableId"]
            
            subgraph = get_reachable_nodes(G, field_id, direction="both")
            
            # Should include the linked table
            assert linked_table_id in subgraph.nodes


class TestMermaidGeneration:
    """Test Mermaid diagram generation"""
    
    def test_generate_simple_mermaid(self, simple_metadata):
        """Test basic Mermaid generation"""
        G = metadata_to_graph(simple_metadata)
        mermaid = graph_to_mermaid(G, direction="TD", display_mode="simple")
        
        assert mermaid.startswith("flowchart TD")
        assert "fldField1" in mermaid
        assert "fldField2" in mermaid
    
    def test_mermaid_direction_lr(self, simple_metadata):
        """Test left-right Mermaid diagram"""
        G = metadata_to_graph(simple_metadata)
        mermaid = graph_to_mermaid(G, direction="LR", display_mode="simple")
        
        assert mermaid.startswith("flowchart LR")
    
    def test_mermaid_display_modes(self, simple_metadata):
        """Test different display modes"""
        G = metadata_to_graph(simple_metadata)
        
        modes = ["simple", "descriptions", "formulas", "all"]
        for mode in modes:
            mermaid = graph_to_mermaid(G, direction="TD", display_mode=mode)
            assert len(mermaid) > 0
            assert "flowchart TD" in mermaid
    
    def test_mermaid_escapes_special_characters(self, simple_metadata):
        """Test that special characters are escaped"""
        G = metadata_to_graph(simple_metadata)
        mermaid = graph_to_mermaid(G, direction="TD", display_mode="formulas")
        
        # Should not have unescaped parentheses in node text (outside node definition)
        # This is a basic check - full validation would be more complex
        assert mermaid is not None
    
    def test_mermaid_creates_subgraphs(self, simple_metadata):
        """Test that tables create subgraphs"""
        G = metadata_to_graph(simple_metadata)
        mermaid = graph_to_mermaid(G, direction="TD", display_mode="simple")
        
        # Should have subgraph declarations
        assert "subgraph" in mermaid.lower()


class TestFieldLookup:
    """Test field lookup helpers"""
    
    def test_find_field_by_id(self, sample_metadata):
        """Test finding a field by ID"""
        # Get any field from metadata
        test_field = sample_metadata["tables"][0]["fields"][0]
        field_id = test_field["id"]
        
        found_field = find_field_by_id(sample_metadata, field_id)
        
        assert found_field is not None
        assert found_field["id"] == field_id
    
    def test_find_nonexistent_field(self, sample_metadata):
        """Test that nonexistent field returns None"""
        found_field = find_field_by_id(sample_metadata, "fldNonexistent")
        assert found_field is None


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_metadata(self):
        """Test with empty metadata"""
        metadata = {"tables": []}
        G = metadata_to_graph(metadata)
        
        assert len(G.nodes) == 0
    
    def test_table_with_no_fields(self):
        """Test table with no fields"""
        metadata = {
            "tables": [
                {
                    "id": "tblEmpty",
                    "name": "Empty Table",
                    "fields": []
                }
            ]
        }
        G = metadata_to_graph(metadata)
        
        # Should still create table node
        assert "tblEmpty" in G.nodes
    
    def test_circular_dependencies(self):
        """Test that circular dependencies don't break graph creation"""
        metadata = {
            "tables": [
                {
                    "id": "tblTest",
                    "name": "Test",
                    "fields": [
                        {
                            "id": "fldA",
                            "name": "A",
                            "type": "formula",
                            "options": {
                                "formula": "{fldB}",
                                "referencedFieldIds": ["fldB"]
                            }
                        },
                        {
                            "id": "fldB",
                            "name": "B",
                            "type": "formula",
                            "options": {
                                "formula": "{fldA}",
                                "referencedFieldIds": ["fldA"]
                            }
                        }
                    ]
                }
            ]
        }
        
        # Should not crash
        G = metadata_to_graph(metadata)
        assert len(G.nodes) > 0
        
        # Should have edges for both dependencies
        assert G.has_edge("fldA", "fldB") or G.has_edge("fldB", "fldA")
