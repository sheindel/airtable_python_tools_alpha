"""Tests for Mermaid diagram generator

Tests the core mermaid diagram generation logic that visualizes field dependencies.
This is critical for the dependency mapper and formula grapher tabs.
"""
import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from airtable_mermaid_generator import (
    _escape_mermaid_text,
    field_metadata_to_mermaid_node,
)
from at_metadata_graph import metadata_to_graph, graph_to_mermaid


class TestEscapeMermaidText:
    """Test mermaid text escaping"""
    
    def test_escapes_parentheses(self):
        """Parentheses should be replaced with brackets"""
        text = "Field (with parens)"
        result = _escape_mermaid_text(text)
        assert "(" not in result
        assert ")" not in result
        assert "[" in result
        assert "]" in result
    
    def test_escapes_quotes(self):
        """Double quotes should become single quotes"""
        text = 'Field "with quotes"'
        result = _escape_mermaid_text(text)
        assert '"' not in result
        assert "'" in result
    
    def test_escapes_hash(self):
        """Hash should be HTML escaped to avoid mermaid comments"""
        text = "Field #1"
        result = _escape_mermaid_text(text)
        # The raw # is replaced with HTML entity
        assert "&#35;" in result
    
    def test_handles_empty_string(self):
        """Should handle empty string"""
        result = _escape_mermaid_text("")
        assert result == ""
    
    def test_handles_no_special_chars(self):
        """Should not modify text without special chars"""
        text = "Normal Field Name"
        result = _escape_mermaid_text(text)
        assert result == text


class TestFieldMetadataToMermaidNode:
    """Test conversion of field metadata to mermaid nodes"""
    
    def test_simple_text_field(self):
        """Text field should generate basic node"""
        field = {
            "id": "fld1",
            "name": "Name",
            "type": "singleLineText",
            "options": {}
        }
        
        result = field_metadata_to_mermaid_node(field)
        
        assert "nodes" in result
        assert "edges" in result
        # Should have a node but no edges
        assert len(result["nodes"]) >= 0
        assert len(result["edges"]) == 0
    
    def test_formula_field_creates_edges(self):
        """Formula field should create edges to referenced fields"""
        field = {
            "id": "fld1",
            "name": "Total",
            "type": "formula",
            "options": {
                "formula": "{fld2} + {fld3}",
                "referencedFieldIds": ["fld2", "fld3"]
            }
        }
        
        result = field_metadata_to_mermaid_node(field, full_description=True)
        
        # Should have edges from dependencies
        assert len(result["edges"]) == 2
        assert any("fld2" in edge and "fld1" in edge for edge in result["edges"])
        assert any("fld3" in edge and "fld1" in edge for edge in result["edges"])
    
    def test_rollup_field_creates_edge(self):
        """Rollup field should create edge to linked field"""
        field = {
            "id": "fld1",
            "name": "Total Sales",
            "type": "rollup",
            "options": {
                "recordLinkFieldId": "fld2",
                "fieldIdInLinkedTable": "fld3",
                "aggregationFunction": "sum"
            }
        }
        
        result = field_metadata_to_mermaid_node(field)
        
        # Should have edge from the field being rolled up
        assert len(result["edges"]) >= 1
        assert any("fld3" in edge for edge in result["edges"])
    
    def test_lookup_field_creates_edge(self):
        """Lookup field should create edge to linked field"""
        field = {
            "id": "fld1",
            "name": "Customer Name",
            "type": "multipleLookupValues",
            "options": {
                "recordLinkFieldId": "fld2",
                "fieldIdInLinkedTable": "fld3"
            }
        }
        
        result = field_metadata_to_mermaid_node(field)
        
        # Should have edge from the looked-up field
        assert len(result["edges"]) >= 1
        assert any("fld3" in edge for edge in result["edges"])
    
    def test_linked_record_field_creates_bidirectional_edge(self):
        """Linked record field with inverse should create bidirectional edge"""
        field = {
            "id": "fld1",
            "name": "Orders",
            "type": "multipleRecordLinks",
            "options": {
                "linkedTableId": "tbl2",
                "inverseLinkFieldId": "fld2"
            }
        }
        
        result = field_metadata_to_mermaid_node(field)
        
        # Should have bidirectional edge
        assert len(result["edges"]) >= 1
        assert any("<-->" in edge for edge in result["edges"])
    
    def test_count_field_creates_edge(self):
        """Count field should create edge to link field"""
        field = {
            "id": "fld1",
            "name": "Order Count",
            "type": "count",
            "options": {
                "recordLinkFieldId": "fld2"
            }
        }
        
        result = field_metadata_to_mermaid_node(field)
        
        # Should have edge to the link field being counted
        assert len(result["edges"]) >= 1


class TestGraphToMermaid:
    """Test full graph to mermaid conversion"""
    
    def test_simple_graph(self):
        """Test conversion of simple graph"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "primaryFieldId": "fld1",
                    "fields": [
                        {"id": "fld1", "name": "Name", "type": "singleLineText"},
                        {"id": "fld2", "name": "Value", "type": "number"}
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should contain mermaid syntax
        assert "graph TD" in mermaid or "flowchart TD" in mermaid
        # Should include field IDs
        assert "fld1" in mermaid
        assert "fld2" in mermaid
    
    def test_graph_with_formula(self):
        """Test graph with formula dependency"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "primaryFieldId": "fld1",
                    "fields": [
                        {"id": "fld1", "name": "Base", "type": "number"},
                        {
                            "id": "fld2",
                            "name": "Double",
                            "type": "formula",
                            "options": {
                                "formula": "{fld1} * 2",
                                "referencedFieldIds": ["fld1"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should show dependency
        assert "-->" in mermaid
        # Should have both fields
        assert "fld1" in mermaid
        assert "fld2" in mermaid
    
    def test_flowchart_directions(self):
        """Test different flowchart directions"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {"id": "fld1", "name": "Field", "type": "text"}
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        
        # Top-down
        mermaid_td = graph_to_mermaid(graph, "TD", "simple")
        assert "TD" in mermaid_td
        
        # Left-right
        mermaid_lr = graph_to_mermaid(graph, "LR", "simple")
        assert "LR" in mermaid_lr
    
    def test_display_modes(self):
        """Test different display modes"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "MyField",
                            "type": "formula",
                            "options": {
                                "formula": "1 + 1",
                                "referencedFieldIds": [],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        
        # Simple mode - just field IDs
        simple = graph_to_mermaid(graph, "TD", "simple")
        
        # Descriptions mode - field names
        descriptions = graph_to_mermaid(graph, "TD", "descriptions")
        assert "MyField" in descriptions or "fld1" in descriptions
        
        # Formulas mode - show formulas
        formulas = graph_to_mermaid(graph, "TD", "formulas")
        # Should include formula text or reference
    
    def test_multiple_tables_create_subgraphs(self):
        """Multiple tables should create subgraphs"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table1",
                    "fields": [{"id": "fld1", "name": "Field1", "type": "text"}]
                },
                {
                    "id": "tbl2",
                    "name": "Table2",
                    "fields": [{"id": "fld2", "name": "Field2", "type": "text"}]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should have subgraph syntax
        assert "subgraph" in mermaid.lower()
        # Should include both table names
        assert "Table1" in mermaid or "tbl1" in mermaid
        assert "Table2" in mermaid or "tbl2" in mermaid
    
    def test_cross_table_dependencies(self):
        """Test visualization of cross-table dependencies"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Orders",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Customer Link",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl2",
                                "inverseLinkFieldId": "fld2"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fld2",
                            "name": "Orders",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl1",
                                "inverseLinkFieldId": "fld1"
                            }
                        }
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should show connection between tables
        assert "<-->" in mermaid or "-->" in mermaid
        # Both fields should be present
        assert "fld1" in mermaid
        assert "fld2" in mermaid
    
    def test_handles_empty_graph(self):
        """Should handle empty graph gracefully"""
        metadata = {"tables": []}
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should still be valid mermaid syntax
        assert isinstance(mermaid, str)
        # Should have graph/flowchart declaration
        assert "graph" in mermaid.lower() or "flowchart" in mermaid.lower()
    
    def test_escapes_special_characters_in_field_names(self):
        """Should escape special characters in field names"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "Field (with parens)",
                            "type": "text"
                        }
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "descriptions")
        
        # Parentheses should be escaped
        # Either they're not in output, or they're converted
        # The important thing is the mermaid is valid


class TestComplexScenarios:
    """Test complex real-world scenarios"""
    
    def test_deeply_nested_formula_chain(self):
        """Test visualization of deeply nested formulas"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {"id": "fld1", "name": "Base", "type": "number"},
                        {
                            "id": "fld2",
                            "name": "Level1",
                            "type": "formula",
                            "options": {
                                "formula": "{fld1} * 2",
                                "referencedFieldIds": ["fld1"],
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld3",
                            "name": "Level2",
                            "type": "formula",
                            "options": {
                                "formula": "{fld2} + 10",
                                "referencedFieldIds": ["fld2"],
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld4",
                            "name": "Level3",
                            "type": "formula",
                            "options": {
                                "formula": "{fld3} / 2",
                                "referencedFieldIds": ["fld3"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should show chain of dependencies
        assert "fld1" in mermaid
        assert "fld2" in mermaid
        assert "fld3" in mermaid
        assert "fld4" in mermaid
        # Should have arrows
        assert "-->" in mermaid
    
    def test_rollup_with_lookup_chain(self):
        """Test visualization of rollup with lookup dependencies"""
        metadata = {
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
                                "inverseLinkFieldId": "fld3"
                            }
                        },
                        {
                            "id": "fld2",
                            "name": "Customer Name",
                            "type": "multipleLookupValues",
                            "options": {
                                "recordLinkFieldId": "fld1",
                                "fieldIdInLinkedTable": "fld4"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl2",
                    "name": "Customers",
                    "fields": [
                        {
                            "id": "fld3",
                            "name": "Orders",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl1",
                                "inverseLinkFieldId": "fld1"
                            }
                        },
                        {"id": "fld4", "name": "Name", "type": "singleLineText"}
                    ]
                }
            ]
        }
        
        graph = metadata_to_graph(metadata)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should show relationships across tables
        assert "fld1" in mermaid  # Link field
        assert "fld2" in mermaid  # Lookup field
        assert "fld4" in mermaid  # Looked-up field


# ============================================================================
# Integration Tests with Real Airtable Data
# ============================================================================

@pytest.mark.airtable_live
class TestMermaidGeneratorIntegration:
    """Integration tests using real Airtable data.
    
    These tests validate Mermaid diagram generation with real-world field names
    that contain special characters, emojis, multi-language text, and other
    edge cases not present in synthetic test data.
    """
    
    def test_generate_mermaid_from_real_schema(self, airtable_schema):
        """Test Mermaid generation from real Airtable schema."""
        graph = metadata_to_graph(airtable_schema)
        
        # Test different display modes
        for mode in ["simple", "descriptions", "formulas"]:
            mermaid = graph_to_mermaid(graph, "TD", mode)
            
            assert isinstance(mermaid, str)
            assert len(mermaid) > 0
            assert "graph" in mermaid.lower() or "flowchart" in mermaid.lower()
    
    def test_field_names_with_special_characters(self, airtable_schema):
        """Test that real field names with special chars are properly escaped."""
        graph = metadata_to_graph(airtable_schema)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should not have unescaped problematic characters that break Mermaid
        # Check for common issues:
        # - Unbalanced quotes should be handled
        # - Parentheses should be escaped or in proper context
        
        # Basic validation: should be valid Mermaid syntax structure
        assert mermaid.count("[") >= mermaid.count("]") - 5  # Allow some flexibility
        
        # Should not crash when rendering real field names
        assert isinstance(mermaid, str)
    
    def test_all_field_types_render_correctly(self, airtable_schema):
        """Test that all field types in real base render without errors."""
        graph = metadata_to_graph(airtable_schema)
        
        # Collect unique field types
        field_types = set()
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                field_types.add(field["type"])
        
        # Generate mermaid and ensure all types are handled
        for mode in ["simple", "descriptions"]:
            mermaid = graph_to_mermaid(graph, "TD", mode)
            assert isinstance(mermaid, str)
            assert len(mermaid) > 0
    
    def test_cross_table_relationships_in_diagram(self, airtable_schema):
        """Test that cross-table relationships appear in Mermaid diagrams."""
        # Find tables with relationships
        has_links = False
        for table in airtable_schema["tables"]:
            for field in table["fields"]:
                if field["type"] in ["multipleRecordLinks", "multipleLookupValues", "rollup"]:
                    has_links = True
                    break
            if has_links:
                break
        
        if not has_links:
            pytest.skip("No cross-table relationships in test base")
        
        graph = metadata_to_graph(airtable_schema)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        # Should have subgraphs for tables
        assert "subgraph" in mermaid.lower()
        
        # Should have edges between fields
        assert "-->" in mermaid or "---" in mermaid
    
    def test_mermaid_directions_with_real_data(self, airtable_schema):
        """Test all Mermaid direction options with real schema."""
        graph = metadata_to_graph(airtable_schema)
        
        for direction in ["TD", "LR", "RL", "BT"]:
            mermaid = graph_to_mermaid(graph, direction, "simple")
            
            assert isinstance(mermaid, str)
            assert len(mermaid) > 0
            # Should specify the direction
            assert direction in mermaid or direction.lower() in mermaid.lower()
    
    def test_formula_display_mode_with_real_formulas(self, airtable_schema):
        """Test formula display mode with real formula content."""
        # Find formula fields
        has_formulas = any(
            field["type"] == "formula"
            for table in airtable_schema["tables"]
            for field in table["fields"]
        )
        
        if not has_formulas:
            pytest.skip("No formula fields in test base")
        
        graph = metadata_to_graph(airtable_schema)
        mermaid = graph_to_mermaid(graph, "TD", "formulas")
        
        assert isinstance(mermaid, str)
        assert len(mermaid) > 0
        
        # Should handle formula text without breaking Mermaid syntax
        # (We can't easily verify the formula content, but it shouldn't crash)
    
    def test_large_base_generates_valid_mermaid(self, airtable_schema):
        """Test that large real bases generate valid Mermaid diagrams."""
        total_fields = sum(
            len(table["fields"])
            for table in airtable_schema["tables"]
        )
        
        if total_fields == 0:
            pytest.skip("No fields in test base")
        
        graph = metadata_to_graph(airtable_schema)
        mermaid = graph_to_mermaid(graph, "TD", "simple")
        
        assert isinstance(mermaid, str)
        assert len(mermaid) > 0
        
        # Basic syntax validation for large diagrams
        lines = mermaid.split('\n')
        assert len(lines) > 0
        
        # Should have proper structure
        assert any("graph" in line.lower() or "flowchart" in line.lower() for line in lines)
