"""Dependency Mapper Tab - Visualize field dependencies in Airtable base"""
from pyscript import document, window
from pyodide.ffi.wrappers import add_event_listener
from collections import defaultdict

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage, save_local_storage, get_local_storage_metadata
from airtable_mermaid_generator import get_node_id
from at_metadata_graph import get_reachable_nodes_advanced, metadata_to_graph, get_reachable_nodes, get_reachable_nodes_depth, graph_to_mermaid


def generate_table_dependency_graph(
    table_id: str,
    flowchart_type: str = "TD",
):
    """
    Generate a Mermaid graph showing table-level dependencies.
    
    For a given table, shows all tables it connects to via:
    - Linked record fields
    - Lookup fields
    - Rollup fields
    - Formula fields that reference fields in other tables
    
    Edges are labeled with connection type and count (e.g., "Rollup (3)").
    """
    airtable_metadata = get_local_storage_metadata()
    G = metadata_to_graph(airtable_metadata)
    
    # Find the table
    source_table = None
    for table in airtable_metadata["tables"]:
        if table["id"] == table_id:
            source_table = table
            break
    
    if not source_table:
        print(f"Table {table_id} not found in metadata")
        return ""
    
    source_table_name = source_table["name"]
    
    # Track connections by (source_table, target_table, connection_type)
    connections = defaultdict(int)
    
    # Analyze each field in the source table
    for field in source_table["fields"]:
        field_id = field["id"]
        field_type = field.get("type")
        
        if field_type == "multipleRecordLinks":
            # Direct link to another table
            target_table_id = field["options"]["linkedTableId"]
            connections[(table_id, target_table_id, "Linked Records")] += 1
            
        elif field_type == "multipleLookupValues":
            # Lookup references a field in a linked table
            record_link_id = field["options"]["recordLinkFieldId"]
            # Get the target table from the record link field
            if record_link_id in G.nodes:
                record_link_metadata = G.nodes[record_link_id].get("metadata", {})
                if record_link_metadata and record_link_metadata.get("type") == "multipleRecordLinks":
                    target_table_id = record_link_metadata["options"]["linkedTableId"]
                    connections[(table_id, target_table_id, "Lookup")] += 1
            
        elif field_type == "rollup":
            # Rollup references a field in a linked table
            record_link_id = field["options"]["recordLinkFieldId"]
            # Get the target table from the record link field
            if record_link_id in G.nodes:
                record_link_metadata = G.nodes[record_link_id].get("metadata", {})
                if record_link_metadata and record_link_metadata.get("type") == "multipleRecordLinks":
                    target_table_id = record_link_metadata["options"]["linkedTableId"]
                    connections[(table_id, target_table_id, "Rollup")] += 1
        
        elif field_type == "formula":
            # Check if formula references fields in other tables
            referenced_field_ids = field["options"].get("referencedFieldIds", [])
            target_tables = set()
            for ref_field_id in referenced_field_ids:
                if ref_field_id in G.nodes:
                    ref_table_id = G.nodes[ref_field_id].get("table_id")
                    if ref_table_id and ref_table_id != table_id:
                        target_tables.add(ref_table_id)
            
            for target_table_id in target_tables:
                connections[(table_id, target_table_id, "Formula")] += 1
    
    # Generate Mermaid diagram
    mermaid_lines = [f"flowchart {flowchart_type}"]
    
    # Add nodes for all involved tables
    tables_in_graph = {table_id}
    for (src, tgt, _), _ in connections.items():
        tables_in_graph.add(src)
        tables_in_graph.add(tgt)
    
    for tbl_id in tables_in_graph:
        table_name_display = G.nodes[tbl_id].get("name", tbl_id)
        # Highlight the source table differently
        if tbl_id == table_id:
            mermaid_lines.append(f'    {tbl_id}["{table_name_display}"]')
            mermaid_lines.append(f'    style {tbl_id} fill:#3b82f6,stroke:#1e40af,color:#fff')
        else:
            mermaid_lines.append(f'    {tbl_id}["{table_name_display}"]')
    
    # Add edges with labels
    for (src, tgt, conn_type), count in sorted(connections.items()):
        label = f"{conn_type} [{count}]" if count > 1 else conn_type
        mermaid_lines.append(f'    {src} -->|"{label}"| {tgt}')
    
    mermaid_diagram = "\n".join(mermaid_lines)
    return mermaid_diagram


def update_mermaid_graph(
    table_id: str,
    field_id: str,
    flowchart_type: str,
):
    """Generate and display a Mermaid diagram for field dependencies"""
    print(f"Table ID: {table_id}, Field ID: {field_id}")
    
    # Check if this is the special table dependencies request
    if field_id == "__TABLE_DEPENDENCIES__":
        mermaid_text = generate_table_dependency_graph(table_id, flowchart_type)
        save_local_storage("lastGraphDefinition", mermaid_text)
        mermaid_container = document.getElementById("mermaid-container")
        mermaid_container.innerHTML = f'<div class="mermaid">{mermaid_text}</div>'
        window.mermaid.run()
        return
    
    airtable_metadata = get_local_storage_metadata()
    
    # Get UI parameters
    display_mode_dropdown = document.getElementById("description-display-mode")
    graph_direction_dropdown = document.getElementById("graph-direction")
    max_depth_input = document.getElementById("max-depth")
    
    display_mode = display_mode_dropdown.value
    direction = graph_direction_dropdown.value
    max_depth_value = max_depth_input.value.strip()
    
    # Parse max_depth: use None if empty, NaN, or invalid
    max_depth = None
    if max_depth_value:
        try:
            max_depth = int(max_depth_value)
            if max_depth <= 0:
                max_depth = None
        except (ValueError, TypeError):
            max_depth = None

    print(f"Direction: {direction}, Display Mode: {display_mode}, Max Depth: {max_depth}")
    
    # Use the graph-based approach
    G = metadata_to_graph(airtable_metadata)
    
    # Get the field name for get_node_id
    field_metadata = None
    table_name = ""
    for table in airtable_metadata["tables"]:
        if table["id"] == table_id:
            table_name = table["name"]
            for field in table["fields"]:
                if field["id"] == field_id:
                    field_metadata = field
                    break
            break
    
    if not field_metadata:
        print(f"Field {field_id} not found in table {table_id}")
        return
    
    # Get the node ID
    node_id = get_node_id(
        airtable_metadata,
        field_id,
        table_name
    )
    
    # Get reachable nodes - use depth-aware function if max_depth is specified
    if max_depth is not None:
        subgraph, depth_dict = get_reachable_nodes_depth(G, node_id, direction=direction, max_depth=max_depth)
        print(f"Retrieved {len(depth_dict)} nodes with depth information")
    else:
        subgraph = get_reachable_nodes(G, node_id, direction=direction)
    
    # Convert to Mermaid
    mermaid_text = graph_to_mermaid(
        subgraph, 
        direction=flowchart_type, 
        display_mode=display_mode
    )
    
    save_local_storage("lastGraphDefinition", mermaid_text)

    mermaid_container = document.getElementById("mermaid-container")
    mermaid_container.innerHTML = f'<div class="mermaid">{mermaid_text}</div>'
    window.mermaid.run()


def parameters_changed(event):
    """Handle parameter changes from UI controls"""
    table_dropdown = document.getElementById("table-dropdown")
    field_dropdown = document.getElementById("field-dropdown")
    flowchart_type_dropdown = document.getElementById("flowchart-type")
    
    table_name = table_dropdown.value
    field_name = field_dropdown.value.strip()
    direction = flowchart_type_dropdown.value
    
    # Find the table ID and field ID from the metadata
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        print("No metadata available")
        return
    
    table_id = None
    field_id = None
    
    # Find table ID by name
    for table in airtable_metadata["tables"]:
        if table["name"] == table_name:
            table_id = table["id"]
            # Find field ID by name within this table (if field is specified)
            if field_name and field_name != "<Show Table Dependencies>":
                for field in table["fields"]:
                    if field["name"] == field_name:
                        field_id = field["id"]
                        break
            break
    
    if not table_id:
        print(f"Could not find table '{table_name}'")
        return
    
    # If special table dependencies option is selected or no field, generate table-level graph
    if not field_name or field_name == "<Show Table Dependencies>" or not field_id:
        print(f"Generating table-level dependency graph for {table_name}")
        mermaid_text = generate_table_dependency_graph(table_id, direction)
        save_local_storage("lastGraphDefinition", mermaid_text)
        mermaid_container = document.getElementById("mermaid-container")
        mermaid_container.innerHTML = f'<div class="mermaid">{mermaid_text}</div>'
        window.mermaid.run()
        return
    
    print(f"Table: {table_name} ({table_id}), Field: {field_name} ({field_id}), Direction: {direction}")
    update_mermaid_graph(table_id, field_id, direction)


def initialize():
    """Initialize the Dependency Mapper tab"""
    # Get UI elements
    field_dropdown = document.getElementById("field-dropdown")
    flowchart_type_dropdown = document.getElementById("flowchart-type")
    graph_direction_dropdown = document.getElementById("graph-direction")
    display_mode_dropdown = document.getElementById("description-display-mode")
    max_depth_input = document.getElementById("max-depth")
    
    # Export function to JavaScript
    window.updateMermaidGraph = update_mermaid_graph
    
    # Add event listeners
    add_event_listener(field_dropdown, "change", parameters_changed)
    add_event_listener(flowchart_type_dropdown, "change", parameters_changed)
    add_event_listener(graph_direction_dropdown, "change", parameters_changed)
    add_event_listener(display_mode_dropdown, "change", parameters_changed)
    add_event_listener(max_depth_input, "input", parameters_changed)
