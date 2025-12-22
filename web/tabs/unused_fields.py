"""Unused Field Detector Tab - Find fields with zero inbound references for cleanup"""
from pyscript import window
import json

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from at_metadata_graph import metadata_to_graph
import networkx as nx


def get_field_usage_stats(G: nx.DiGraph, field_id: str) -> dict:
    """Get usage statistics for a single field.
    
    Args:
        G: The dependency graph
        field_id: The field ID to analyze
        
    Returns:
        Dictionary with usage information
    """
    try:
        node_data = G.nodes.get(field_id, {})
        if not node_data or node_data.get("type") != "field":
            return None
        
        # Count inbound edges (fields that reference this field)
        inbound_count = G.in_degree(field_id)
        
        # Get the types of inbound relationships
        inbound_relationships = {}
        for predecessor in G.predecessors(field_id):
            edge_data = G.get_edge_data(predecessor, field_id)
            if edge_data:
                rel_type = edge_data.get("relationship", "unknown")
                inbound_relationships[rel_type] = inbound_relationships.get(rel_type, 0) + 1
        
        # Count outbound edges (fields this field references)
        outbound_count = G.out_degree(field_id)
        
        return {
            "field_id": field_id,
            "field_name": node_data.get("name", field_id),
            "field_type": node_data.get("field_type", "unknown"),
            "table_id": node_data.get("table_id", ""),
            "table_name": node_data.get("table_name", ""),
            "inbound_count": inbound_count,
            "outbound_count": outbound_count,
            "inbound_relationships": inbound_relationships,
            "is_unused": inbound_count == 0
        }
    except Exception as e:
        print(f"Error in get_field_usage_stats for {field_id}: {e}")
        return None


def get_unused_fields() -> list:
    """Find all fields with zero inbound references.
    
    These are fields that are not used by any formula, rollup, lookup, or count.
    They may be candidates for cleanup or review.
    
    Returns:
        List of dictionaries with field information, grouped by table
    """
    try:
        airtable_metadata = get_local_storage_metadata()
        if not airtable_metadata:
            print("No metadata available")
            return []
        
        G = metadata_to_graph(airtable_metadata)
        
        unused_fields = []
        
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            if node_data.get("type") != "field":
                continue
            
            stats = get_field_usage_stats(G, node_id)
            if stats and stats["is_unused"]:
                unused_fields.append(stats)
        
        # Sort by table name, then field name
        unused_fields.sort(key=lambda x: (x["table_name"], x["field_name"]))
        
        return unused_fields
    except Exception as e:
        print(f"Error in get_unused_fields: {e}")
        import traceback
        traceback.print_exc()
        return []


def get_all_fields_usage() -> list:
    """Get usage statistics for all fields.
    
    Returns:
        List of dictionaries with usage stats for each field
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        print("No metadata available")
        return []
    
    G = metadata_to_graph(airtable_metadata)
    
    all_fields = []
    
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        if node_data.get("type") != "field":
            continue
        
        stats = get_field_usage_stats(G, node_id)
        if stats:
            all_fields.append(stats)
    
    # Sort by inbound count (ascending) so unused are first
    all_fields.sort(key=lambda x: (x["inbound_count"], x["table_name"], x["field_name"]))
    
    return all_fields


def get_unused_fields_summary() -> str:
    """Get summary statistics about unused fields.
    
    Returns:
        JSON string with summary statistics
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        return json.dumps({
            "total_fields": 0,
            "unused_count": 0,
            "unused_percentage": 0,
            "tables_with_unused": 0,
            "by_table": {}
        })
    
    G = metadata_to_graph(airtable_metadata)
    
    total_fields = 0
    unused_count = 0
    by_table = {}
    by_type = {}
    
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        if node_data.get("type") != "field":
            continue
        
        total_fields += 1
        table_name = node_data.get("table_name", "Unknown")
        field_type = node_data.get("field_type", "unknown")
        
        if table_name not in by_table:
            by_table[table_name] = {"total": 0, "unused": 0}
        by_table[table_name]["total"] += 1
        
        if field_type not in by_type:
            by_type[field_type] = {"total": 0, "unused": 0}
        by_type[field_type]["total"] += 1
        
        # Check if unused
        inbound_count = G.in_degree(node_id)
        if inbound_count == 0:
            unused_count += 1
            by_table[table_name]["unused"] += 1
            by_type[field_type]["unused"] += 1
    
    # Count tables with unused fields
    tables_with_unused = sum(1 for t in by_table.values() if t["unused"] > 0)
    
    return json.dumps({
        "total_fields": total_fields,
        "unused_count": unused_count,
        "unused_percentage": round(unused_count / total_fields * 100, 1) if total_fields > 0 else 0,
        "tables_with_unused": tables_with_unused,
        "total_tables": len(by_table),
        "by_table": by_table,
        "by_type": by_type
    })


def get_unused_fields_for_table(table_name: str) -> list:
    """Get unused fields for a specific table.
    
    Args:
        table_name: Name of the table to analyze
        
    Returns:
        List of unused field dictionaries
    """
    all_unused = get_unused_fields()
    return [f for f in all_unused if f["table_name"] == table_name]


def get_unused_fields_data(filter_table: str = None, filter_type: str = None) -> str:
    """Get unused fields data with optional filters.
    
    Args:
        filter_table: Optional table name to filter by
        filter_type: Optional field type to filter by
        
    Returns:
        JSON string of unused field dictionaries
    """
    try:
        unused = get_unused_fields()
        
        # Handle empty strings as None
        if filter_table and filter_table.strip():
            unused = [f for f in unused if f["table_name"] == filter_table]
        
        if filter_type and filter_type.strip():
            unused = [f for f in unused if f["field_type"] == filter_type]
        
        return json.dumps(unused)
    except Exception as e:
        print(f"Error in get_unused_fields_data: {e}")
        import traceback
        traceback.print_exc()
        return "[]"


def get_field_types_for_dropdown() -> list:
    """Get list of unique field types for the filter dropdown.
    
    Returns:
        List of field type strings
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        return []
    
    types = set()
    for table in airtable_metadata.get("tables", []):
        for field in table.get("fields", []):
            types.add(field.get("type", "unknown"))
    
    return sorted(list(types))


def export_unused_fields_csv() -> str:
    """Export unused fields as CSV string.
    
    Returns:
        CSV formatted string
    """
    unused = get_unused_fields()
    
    if not unused:
        return "No unused fields found"
    
    lines = ["Table,Field,Type,Outbound References"]
    
    for field in unused:
        line = ",".join([
            f'"{field["table_name"]}"',
            f'"{field["field_name"]}"',
            field["field_type"],
            str(field["outbound_count"])
        ])
        lines.append(line)
    
    return "\n".join(lines)


def initialize():
    """Initialize the Unused Fields tab"""
    print("Unused Fields Detector tab initialized")
    
    # Export functions to JavaScript
    window.getUnusedFieldsData = get_unused_fields_data
    window.getUnusedFieldsSummary = get_unused_fields_summary
    window.getFieldTypesForDropdown = get_field_types_for_dropdown
    window.exportUnusedFieldsCSV = export_unused_fields_csv
    window.getTableNamesForUnused = lambda: [t["name"] for t in get_local_storage_metadata().get("tables", [])] if get_local_storage_metadata() else []
