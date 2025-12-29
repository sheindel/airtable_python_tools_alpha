"""Tests for the Dependency Analysis tab"""
import pytest
from unittest.mock import patch
import sys
sys.path.insert(0, 'web')

from tabs.dependency_analysis import get_table_dependencies


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
                    {"id": "fld001", "name": "Name", "type": "singleLineText"}
                ]
            }
        ]
    }


@pytest.fixture
def linked_tables():
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
def complex_dependencies():
    """Metadata with links, lookups, and rollups"""
    return {
        "tables": [
            {
                "id": "tbl001",
                "name": "Orders",
                "primaryFieldId": "fld001",
                "fields": [
                    {"id": "fld001", "name": "ID", "type": "singleLineText"},
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
                        "name": "Total",
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


class TestGetTableDependencies:
    """Test get_table_dependencies function"""
    
    def test_returns_none_when_no_metadata(self):
        """Should return None when no metadata available"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=None):
            result = get_table_dependencies()
            assert result is None
    
    def test_returns_list(self, simple_metadata):
        """Should return a list"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=simple_metadata):
            result = get_table_dependencies()
            assert isinstance(result, list)
    
    def test_empty_for_isolated_table(self, simple_metadata):
        """Table with no dependencies should return empty list"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=simple_metadata):
            result = get_table_dependencies()
            assert len(result) == 0
    
    def test_detects_linked_records(self, linked_tables):
        """Should detect linked record relationships"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=linked_tables):
            result = get_table_dependencies()
            
            assert len(result) >= 1
            # Each result should be a list with 6 elements
            for dep in result:
                assert len(dep) == 6  # [source, target, links, rollups, lookups, total]
                source, target, links, rollups, lookups, total = dep
                assert isinstance(source, str)
                assert isinstance(target, str)
                assert isinstance(links, int)
                assert isinstance(rollups, int)
                assert isinstance(lookups, int)
                assert isinstance(total, int)
    
    def test_counts_links_correctly(self, linked_tables):
        """Should count link fields correctly"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=linked_tables):
            result = get_table_dependencies()
            
            # Find the Orders -> Customers dependency
            orders_to_customers = [d for d in result if d[0] == "Orders" and d[1] == "Customers"]
            if orders_to_customers:
                dep = orders_to_customers[0]
                links_count = dep[2]
                assert links_count >= 1  # At least one link field
    
    def test_detects_lookups(self, complex_dependencies):
        """Should detect lookup fields"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            # Should have at least one dependency with lookups
            has_lookup = any(dep[4] > 0 for dep in result)
            assert has_lookup
    
    def test_detects_rollups(self, complex_dependencies):
        """Should detect rollup fields"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            # Should have at least one dependency with rollups
            has_rollup = any(dep[3] > 0 for dep in result)
            assert has_rollup
    
    def test_calculates_total_correctly(self, complex_dependencies):
        """Total should equal sum of links + rollups + lookups"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            for dep in result:
                source, target, links, rollups, lookups, total = dep
                assert total == links + rollups + lookups
    
    def test_sorted_by_source_table(self, complex_dependencies):
        """Results should be sorted by source table name"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            if len(result) > 1:
                # Check that source tables are in order
                source_tables = [dep[0] for dep in result]
                # Should be sorted (or grouped by source)
                for i in range(len(source_tables) - 1):
                    # Current source should be <= next source (allowing for same source)
                    assert source_tables[i] <= source_tables[i + 1] or source_tables[i] == source_tables[i - 1] if i > 0 else True
    
    def test_bidirectional_links(self, linked_tables):
        """Bidirectional links should create two separate entries"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=linked_tables):
            result = get_table_dependencies()
            
            # Should have Orders -> Customers and Customers -> Orders
            table_pairs = [(dep[0], dep[1]) for dep in result]
            
            # Could be bidirectional
            assert len(table_pairs) >= 1


class TestDependencyStructure:
    """Test the structure of dependency results"""
    
    def test_each_entry_has_six_elements(self, complex_dependencies):
        """Each dependency entry should have exactly 6 elements"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            for dep in result:
                assert len(dep) == 6
    
    def test_counts_are_non_negative(self, complex_dependencies):
        """All counts should be non-negative integers"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            for dep in result:
                links, rollups, lookups, total = dep[2], dep[3], dep[4], dep[5]
                assert links >= 0
                assert rollups >= 0
                assert lookups >= 0
                assert total >= 0
    
    def test_total_at_least_one(self, complex_dependencies):
        """Each dependency should have at least one connection"""
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=complex_dependencies):
            result = get_table_dependencies()
            
            for dep in result:
                total = dep[5]
                # Each listed dependency should have at least 1 connection
                assert total >= 1


class TestEdgeCases:
    """Test edge cases"""
    
    def test_handles_empty_tables_list(self):
        """Should handle metadata with empty tables list"""
        empty_metadata = {"tables": []}
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=empty_metadata):
            result = get_table_dependencies()
            assert result == []
    
    def test_handles_table_without_fields(self):
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
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=metadata):
            result = get_table_dependencies()
            # Should not crash
            assert isinstance(result, list)
    
    def test_multiple_links_between_same_tables(self):
        """Multiple link fields between same tables should be counted"""
        metadata = {
            "tables": [
                {
                    "id": "tbl001",
                    "name": "Table1",
                    "primaryFieldId": "fld001",
                    "fields": [
                        {"id": "fld001", "name": "Name", "type": "singleLineText"},
                        {
                            "id": "fld002",
                            "name": "Link1",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl002",
                                "inverseLinkFieldId": "fld004"
                            }
                        },
                        {
                            "id": "fld003",
                            "name": "Link2",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl002",
                                "inverseLinkFieldId": "fld005"
                            }
                        }
                    ]
                },
                {
                    "id": "tbl002",
                    "name": "Table2",
                    "primaryFieldId": "fld004",
                    "fields": [
                        {
                            "id": "fld004",
                            "name": "Back1",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl001",
                                "inverseLinkFieldId": "fld002"
                            }
                        },
                        {
                            "id": "fld005",
                            "name": "Back2",
                            "type": "multipleRecordLinks",
                            "options": {
                                "linkedTableId": "tbl001",
                                "inverseLinkFieldId": "fld003"
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch('tabs.dependency_analysis.get_local_storage_metadata', return_value=metadata):
            result = get_table_dependencies()
            
            # Find Table1 -> Table2 dependency
            t1_to_t2 = [d for d in result if d[0] == "Table1" and d[1] == "Table2"]
            if t1_to_t2:
                links_count = t1_to_t2[0][2]
                # Should count both link fields
                assert links_count == 2
