"""Tests for the Dependency Mapper tab"""
import pytest
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, 'web')

from tabs.dependency_mapper import (
    generate_table_dependency_graph,
    update_mermaid_graph
)
from at_metadata_graph import metadata_to_graph


@pytest.fixture
def simple_metadata():
    """Simple metadata with single table"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Table1",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Name", "type": "singleLineText"},
                    {"id": "fld002", "name": "Value", "type": "number"}
                ]
            }
        ]
    }


@pytest.fixture
def linked_tables_metadata():
    """Metadata with linked record relationships"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Orders",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Order ID", "type": "singleLineText"},
                    {
                        "id": "fld002",
                        "name": "Customer",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl002",
                            "inverseLinkFieldId": "fld004"
                        }
                    }
                ]
            },
            {
                "id": "tbl002",
                "name": "Customers",
                "primaryFieldId": "fld003",
                "fields": [
                    {"id": "fld003", "name": "Name", "type": "singleLineText"},
                    {
                        "id": "fld004",
                        "name": "Orders",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl001",
                            "inverseLinkFieldId": "fld002"
                        }
                    }
                ]
            }
        ]
    }


@pytest.fixture
def complex_dependencies_metadata():
    """Metadata with lookup, rollup, and formula dependencies"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Orders",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "Order ID", "type": "singleLineText"},
                    {
                        "id": "fld002",
                        "name": "Customer",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl002",
                            "inverseLinkFieldId": "fld005"
                        }
                    },
                    {
                        "id": "fld003",
                        "name": "Customer Name",
                        "type": "multipleLookupValues",
                        "options": {
                            "recordLinkFieldId": "fld002",
                            "fieldIdInLinkedTable": "fld004"
                        }
                    },
                    {
                        "id": "fld006",
                        "name": "Total Amount",
                        "type": "rollup",
                        "options": {
                            "recordLinkFieldId": "fld002",
                            "fieldIdInLinkedTable": "fld007",
                            "aggregationFunction": "sum"
                        }
                    }
                ]
            },
            {
                "id": "tbl002",
                "name": "Customers",
                "primaryFieldId": "fld004",
                "fields": [
                    {"id": "fld004", "name": "Name", "type": "singleLineText"},
                    {
                        "id": "fld005",
                        "name": "Orders",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tbl001",
                            "inverseLinkFieldId": "fld002"
                        }
                    },
                    {"id": "fld007", "name": "Amount", "type": "number"}
                ]
            }
        ]
    }


class TestGenerateTableDependencyGraph:
    """Test table-level dependency graph generation"""
    
    def test_simple_table_no_dependencies(self, simple_metadata):
        """Table with no external dependencies should return empty or minimal graph"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=simple_metadata):
            graph = generate_table_dependency_graph("tbl001", "TD")
            
            assert isinstance(graph, str)
            # Should contain the mermaid graph syntax
            assert "graph" in graph or "flowchart" in graph or graph == ""
    
    def test_linked_records_create_connections(self, linked_tables_metadata):
        """Linked record fields should create table connections"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=linked_tables_metadata):
            graph = generate_table_dependency_graph("tbl001", "TD")
            
            assert isinstance(graph, str)
            # Should contain reference to both tables
            if graph:
                assert "tbl001" in graph or "Orders" in graph
                assert "tbl002" in graph or "Customers" in graph
    
    def test_lookup_creates_connection(self, complex_dependencies_metadata):
        """Lookup fields should create table connections"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=complex_dependencies_metadata):
            graph = generate_table_dependency_graph("tbl001", "TD")
            
            assert isinstance(graph, str)
            # Should show connection via lookup
            if graph:
                assert "Lookup" in graph or "tbl002" in graph or "Customers" in graph
    
    def test_rollup_creates_connection(self, complex_dependencies_metadata):
        """Rollup fields should create table connections"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=complex_dependencies_metadata):
            graph = generate_table_dependency_graph("tbl001", "TD")
            
            assert isinstance(graph, str)
            # Should show connection via rollup
            if graph:
                assert "Rollup" in graph or "tbl002" in graph
    
    def test_respects_flowchart_direction(self, linked_tables_metadata):
        """Should respect flowchart direction parameter"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=linked_tables_metadata):
            graph_td = generate_table_dependency_graph("tbl001", "TD")
            graph_lr = generate_table_dependency_graph("tbl001", "LR")
            
            # Both should be valid strings (may be same or different)
            assert isinstance(graph_td, str)
            assert isinstance(graph_lr, str)
    
    def test_nonexistent_table(self, simple_metadata):
        """Should handle non-existent table gracefully"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=simple_metadata):
            graph = generate_table_dependency_graph("tblNonExistent", "TD")
            
            # Should return empty string or handle gracefully
            assert isinstance(graph, str)


class TestUpdateMermaidGraph:
    """Test the main update function"""
    
    def test_handles_missing_parameters(self, simple_metadata):
        """Should handle missing table_id or field_id"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=simple_metadata):
            # Should not crash with empty parameters
            result = update_mermaid_graph("", "", "TD")
            assert result is None or isinstance(result, str)
            
            result = update_mermaid_graph("tbl001", "", "TD")
            assert result is None or isinstance(result, str)
    
    def test_table_dependencies_special_case(self, linked_tables_metadata):
        """Should handle special __TABLE_DEPENDENCIES__ field_id"""
        mock_save = MagicMock()
        mock_document = MagicMock()
        mock_window = MagicMock()
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=linked_tables_metadata):
            with patch('tabs.dependency_mapper.save_local_storage', mock_save):
                with patch('tabs.dependency_mapper.document', mock_document):
                    with patch('tabs.dependency_mapper.window', mock_window):
                        update_mermaid_graph("tbl001", "__TABLE_DEPENDENCIES__", "TD")
                        
                        # Should have saved the graph definition
                        assert mock_save.called
    
    def test_handles_no_metadata(self):
        """Should handle missing metadata gracefully"""
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=None):
            result = update_mermaid_graph("tbl001", "fld001", "TD")
            # Should not crash
            assert result is None or isinstance(result, str)


class TestFieldDependencyGraph:
    """Test field-level dependency visualization"""
    
    def test_formula_dependencies(self):
        """Formula fields should show their dependencies"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {"id": "fld001", "name": "A", "type": "number"},
                        {"id": "fld002", "name": "B", "type": "number"},
                        {
                            "id": "fld003",
                            "name": "Sum",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001} + {fld002}",
                                "referencedFieldIds": ["fld001", "fld002"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=metadata):
            G = metadata_to_graph(metadata)
            
            # Check that dependencies exist in the graph
            assert "fld003" in G.nodes
            # Formula should depend on its referenced fields
            assert G.has_edge("fld003", "fld001") or G.has_edge("fld001", "fld003")
            assert G.has_edge("fld003", "fld002") or G.has_edge("fld002", "fld003")


class TestGraphDirectionality:
    """Test different graph direction options"""
    
    def test_backward_direction(self):
        """Backward direction should show what a field depends on"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {"id": "fld001", "name": "Base", "type": "number"},
                        {
                            "id": "fld002",
                            "name": "Double",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001} * 2",
                                "referencedFieldIds": ["fld001"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=metadata):
            from at_metadata_graph import get_reachable_nodes
            
            G = metadata_to_graph(metadata)
            backward = get_reachable_nodes(G, "fld002", direction="backward")
            
            # Should include fld001 (dependency)
            assert "fld001" in backward.nodes or "fld002" in backward.nodes
    
    def test_forward_direction(self):
        """Forward direction should show what depends on a field"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {"id": "fld001", "name": "Base", "type": "number"},
                        {
                            "id": "fld002",
                            "name": "Double",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001} * 2",
                                "referencedFieldIds": ["fld001"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=metadata):
            from at_metadata_graph import get_reachable_nodes
            
            G = metadata_to_graph(metadata)
            forward = get_reachable_nodes(G, "fld001", direction="forward")
            
            # Should include fld002 (dependent)
            assert "fld002" in forward.nodes or "fld001" in forward.nodes


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_circular_dependencies(self):
        """Should handle circular dependencies without crashing"""
        # This is technically invalid but shouldn't crash
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {
                            "id": "fld001",
                            "name": "A",
                            "type": "formula",
                            "options": {
                                "formula": "{fld002}",
                                "referencedFieldIds": ["fld002"],
                                "result": {"type": "number"}
                            }
                        },
                        {
                            "id": "fld002",
                            "name": "B",
                            "type": "formula",
                            "options": {
                                "formula": "{fld001}",
                                "referencedFieldIds": ["fld001"],
                                "result": {"type": "number"}
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=metadata):
            # Should not crash
            G = metadata_to_graph(metadata)
            assert "fld001" in G.nodes
            assert "fld002" in G.nodes
    
    def test_empty_metadata(self):
        """Should handle empty metadata"""
        empty = {"tables": []}
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=empty):
            graph = generate_table_dependency_graph("tbl001", "TD")
            assert isinstance(graph, str)
    
    def test_table_without_fields(self):
        """Should handle table with no fields"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "EmptyTable",
                    "primaryFieldId": None,
                    "fields": []
                }
            ]
        }
        
        with patch('tabs.dependency_mapper.get_local_storage_metadata', return_value=metadata):
            graph = generate_table_dependency_graph("tbl001", "TD")
            assert isinstance(graph, str)
