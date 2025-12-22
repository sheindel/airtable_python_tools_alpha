"""Field Complexity Scorecard Tab - Identify and analyze the most complex fields in your base"""
from pyscript import window
import json

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from at_metadata_graph import (
    metadata_to_graph, 
    get_relationship_dependency_complexity,
    get_reachable_nodes
)
import networkx as nx


def calculate_field_complexity(G: nx.DiGraph, field_id: str) -> dict:
    """Calculate comprehensive complexity metrics for a single field.
    
    Args:
        G: The dependency graph
        field_id: The field ID to analyze
        
    Returns:
        Dictionary with complexity metrics
    """
    node_data = G.nodes.get(field_id, {})
    if not node_data or node_data.get("type") != "field":
        return None
    
    # Get backward dependencies (fields this field depends on)
    backward_nodes = get_reachable_nodes(G, field_id, direction="backward")
    backward_count = len([n for n in backward_nodes.nodes() if backward_nodes.nodes[n].get("type") == "field"]) - 1  # Exclude self
    
    # Get forward dependencies (fields that depend on this field)  
    forward_nodes = get_reachable_nodes(G, field_id, direction="forward")
    forward_count = len([n for n in forward_nodes.nodes() if forward_nodes.nodes[n].get("type") == "field"]) - 1  # Exclude self
    
    # Get relationship complexity
    rel_complexity = get_relationship_dependency_complexity(G, field_id)
    relationship_counts = rel_complexity.get("relationship_counts", {})
    tables_dependencies = rel_complexity.get("tables_dependencies", {})
    
    # Calculate depth (longest path to this node)
    try:
        G_reversed = G.reverse()
        if field_id in G_reversed:
            lengths = nx.single_source_shortest_path_length(G_reversed, field_id)
            max_depth = max(lengths.values()) if lengths else 0
        else:
            max_depth = 0
    except Exception:
        max_depth = 0
    
    # Calculate a composite complexity score
    # Weight factors for different complexity aspects
    score = (
        backward_count * 2 +           # Dependencies are important
        forward_count * 1.5 +          # Being depended upon is significant
        len(tables_dependencies) * 5 + # Cross-table complexity is high impact
        max_depth * 3 +                # Deep chains are complex
        relationship_counts.get("formula", 0) * 1 +
        relationship_counts.get("rollup", 0) * 2 +
        relationship_counts.get("lookup", 0) * 1.5 +
        relationship_counts.get("rollup_via", 0) * 2
    )
    
    return {
        "field_id": field_id,
        "field_name": node_data.get("name", field_id),
        "field_type": node_data.get("field_type", "unknown"),
        "table_id": node_data.get("table_id", ""),
        "table_name": node_data.get("table_name", ""),
        "backward_deps": backward_count,
        "forward_deps": forward_count,
        "max_depth": max_depth,
        "cross_table_deps": len(tables_dependencies),
        "table_dependencies": list(tables_dependencies.keys()),
        "relationship_counts": relationship_counts,
        "complexity_score": round(score, 1)
    }


def get_all_field_complexity() -> list:
    """Get complexity metrics for all fields in the base.
    
    Uses batch computation for better performance on large bases.
    
    Returns:
        List of dictionaries with complexity metrics for each field,
        sorted by complexity score (highest first)
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        print("No metadata available")
        return []
    
    G = metadata_to_graph(airtable_metadata)
    
    # Pre-compute data that can be reused across all fields
    # Build reverse graph once for all backward traversals
    G_reversed = G.reverse()
    
    results = []
    
    # Analyze only computed fields (formulas, rollups, lookups)
    computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
    
    # Collect computed field IDs first
    computed_field_ids = []
    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        if node_data.get("type") != "field":
            continue
        field_type = node_data.get("field_type", "")
        if field_type in computed_types:
            computed_field_ids.append(node_id)
    
    print(f"Analyzing {len(computed_field_ids)} computed fields...")
    
    for i, node_id in enumerate(computed_field_ids):
        if i > 0 and i % 50 == 0:
            print(f"  Processed {i}/{len(computed_field_ids)} fields...")
        
        complexity = calculate_field_complexity_fast(G, G_reversed, node_id)
        if complexity:
            results.append(complexity)
    
    print(f"Completed analysis of {len(results)} fields")
    
    # Sort by complexity score (highest first)
    results.sort(key=lambda x: x["complexity_score"], reverse=True)
    
    return results


def calculate_field_complexity_fast(G: nx.DiGraph, G_reversed: nx.DiGraph, field_id: str) -> dict:
    """Calculate complexity metrics for a single field using pre-computed data.
    
    This is an optimized version that uses a pre-computed reverse graph.
    
    Args:
        G: The dependency graph
        G_reversed: Pre-computed reverse of G for faster backward traversal
        field_id: The field ID to analyze
        
    Returns:
        Dictionary with complexity metrics
    """
    node_data = G.nodes.get(field_id, {})
    if not node_data or node_data.get("type") != "field":
        return None
    
    # Get backward dependencies using pre-computed reverse graph
    # ancestors in G = descendants in G_reversed
    try:
        backward_nodes = nx.descendants(G_reversed, field_id)
        backward_count = len([n for n in backward_nodes if G.nodes.get(n, {}).get("type") == "field"])
    except Exception:
        backward_count = 0
        backward_nodes = set()
    
    # Get forward dependencies (fields that depend on this field)
    try:
        forward_nodes = nx.descendants(G, field_id)
        forward_count = len([n for n in forward_nodes if G.nodes.get(n, {}).get("type") == "field"])
    except Exception:
        forward_count = 0
    
    # Get cross-table dependencies from backward nodes
    tables_dependencies = {}
    for node in backward_nodes:
        table_id = G.nodes.get(node, {}).get("table_id")
        if table_id:
            tables_dependencies[table_id] = tables_dependencies.get(table_id, 0) + 1
    
    # Count relationship types in backward dependencies
    relationship_counts = {}
    for node in backward_nodes:
        for pred in G.predecessors(node):
            if pred in backward_nodes or pred == field_id:
                continue
            edge_data = G.get_edge_data(pred, node)
            if edge_data:
                rel = edge_data.get("relationship", "unknown")
                relationship_counts[rel] = relationship_counts.get(rel, 0) + 1
    
    # Also count direct incoming edges to this field
    for pred in G.predecessors(field_id):
        edge_data = G.get_edge_data(pred, field_id)
        if edge_data:
            rel = edge_data.get("relationship", "unknown")
            relationship_counts[rel] = relationship_counts.get(rel, 0) + 1
    
    # Calculate depth using simple BFS on reverse graph
    try:
        if field_id in G_reversed:
            lengths = nx.single_source_shortest_path_length(G_reversed, field_id)
            max_depth = max(lengths.values()) if lengths else 0
        else:
            max_depth = 0
    except Exception:
        max_depth = 0
    
    # Calculate a composite complexity score
    score = (
        backward_count * 2 +
        forward_count * 1.5 +
        len(tables_dependencies) * 5 +
        max_depth * 3 +
        relationship_counts.get("formula", 0) * 1 +
        relationship_counts.get("rollup", 0) * 2 +
        relationship_counts.get("lookup", 0) * 1.5 +
        relationship_counts.get("rollup_via", 0) * 2
    )
    
    return {
        "field_id": field_id,
        "field_name": node_data.get("name", field_id),
        "field_type": node_data.get("field_type", "unknown"),
        "table_id": node_data.get("table_id", ""),
        "table_name": node_data.get("table_name", ""),
        "backward_deps": backward_count,
        "forward_deps": forward_count,
        "max_depth": max_depth,
        "cross_table_deps": len(tables_dependencies),
        "table_dependencies": list(tables_dependencies.keys()),
        "relationship_counts": relationship_counts,
        "complexity_score": round(score, 1)
    }


def get_complexity_for_table(table_name: str) -> list:
    """Get complexity metrics for all computed fields in a specific table.
    
    Args:
        table_name: Name of the table to analyze
        
    Returns:
        List of dictionaries with complexity metrics, sorted by score
    """
    all_complexity = get_all_field_complexity()
    return [f for f in all_complexity if f["table_name"] == table_name]


def get_complexity_summary() -> str:
    """Get summary statistics for the entire base.
    
    Returns:
        JSON string with summary statistics
    """
    all_complexity = get_all_field_complexity()
    
    if not all_complexity:
        return json.dumps({
            "total_computed_fields": 0,
            "avg_complexity_score": 0,
            "max_complexity_score": 0,
            "top_5_fields": [],
            "tables_by_complexity": {}
        })
    
    # Calculate statistics
    scores = [f["complexity_score"] for f in all_complexity]
    
    # Group by table
    tables_complexity = {}
    for field in all_complexity:
        table_name = field["table_name"]
        if table_name not in tables_complexity:
            tables_complexity[table_name] = {
                "field_count": 0,
                "total_score": 0,
                "max_score": 0
            }
        tables_complexity[table_name]["field_count"] += 1
        tables_complexity[table_name]["total_score"] += field["complexity_score"]
        tables_complexity[table_name]["max_score"] = max(
            tables_complexity[table_name]["max_score"], 
            field["complexity_score"]
        )
    
    # Calculate averages for each table
    for table_name in tables_complexity:
        count = tables_complexity[table_name]["field_count"]
        total = tables_complexity[table_name]["total_score"]
        tables_complexity[table_name]["avg_score"] = round(total / count, 1) if count > 0 else 0
    
    return json.dumps({
        "total_computed_fields": len(all_complexity),
        "avg_complexity_score": round(sum(scores) / len(scores), 1),
        "max_complexity_score": max(scores),
        "top_5_fields": all_complexity[:5],
        "tables_by_complexity": tables_complexity
    })


def get_complexity_scorecard_data(filter_table: str = None, min_score: float = 0) -> str:
    """Get complexity data formatted for the UI scorecard.
    
    Args:
        filter_table: Optional table name to filter by
        min_score: Minimum complexity score to include (default 0)
        
    Returns:
        JSON string of field complexity data for display
    """
    all_complexity = get_all_field_complexity()
    
    # Apply filters
    if filter_table:
        all_complexity = [f for f in all_complexity if f["table_name"] == filter_table]
    
    if min_score > 0:
        all_complexity = [f for f in all_complexity if f["complexity_score"] >= min_score]
    
    return json.dumps(all_complexity)


def get_table_names_for_dropdown() -> list:
    """Get list of table names for the filter dropdown.
    
    Returns:
        List of table names
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        return []
    
    return [table["name"] for table in airtable_metadata.get("tables", [])]


def export_complexity_to_csv() -> str:
    """Export all complexity data as CSV string.
    
    Returns:
        CSV formatted string
    """
    all_complexity = get_all_field_complexity()
    
    if not all_complexity:
        return "No data available"
    
    # CSV header
    lines = ["Table,Field,Type,Score,Depth,Backward Deps,Forward Deps,Cross-Table Deps,Formula Refs,Rollup Refs,Lookup Refs"]
    
    for field in all_complexity:
        rel_counts = field.get("relationship_counts", {})
        line = ",".join([
            f'"{field["table_name"]}"',
            f'"{field["field_name"]}"',
            field["field_type"],
            str(field["complexity_score"]),
            str(field["max_depth"]),
            str(field["backward_deps"]),
            str(field["forward_deps"]),
            str(field["cross_table_deps"]),
            str(rel_counts.get("formula", 0)),
            str(rel_counts.get("rollup", 0) + rel_counts.get("rollup_via", 0)),
            str(rel_counts.get("lookup", 0) + rel_counts.get("lookup_via", 0))
        ])
        lines.append(line)
    
    return "\n".join(lines)


def initialize():
    """Initialize the Complexity Scorecard tab"""
    print("Complexity Scorecard tab initialized")
    
    # Export functions to JavaScript
    window.getComplexityScorecardData = get_complexity_scorecard_data
    window.getComplexitySummary = get_complexity_summary
    window.getTableNamesForScorecard = get_table_names_for_dropdown
    window.exportComplexityCSV = export_complexity_to_csv
