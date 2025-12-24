from at_types import AirTableFieldMetadata, AirtableMetadata
import networkx as nx
import re


class Node:
    def __init__(self, field_metadata: AirTableFieldMetadata):
        self.field_metadata: AirTableFieldMetadata = field_metadata
        self.children: set[Node] = []
        self.parents: set[Node] = []

    def get_parents(self):
        return self.parents

    def get_children(self):
        return self.children
    
    def add_parent(self, parent):
        self.parents.add(parent)
        parent.children.add(self)

    def __repr__(self):
        return self.name


def metadata_to_graph(metadata: AirtableMetadata) -> nx.DiGraph:
    """
    Convert AirtableMetadata to a NetworkX DiGraph.
    
    Nodes represent fields and tables, with edges representing relationships:
    - Formula fields -> referenced fields
    - Lookup fields -> linked fields
    - Rollup fields -> linked fields
    - Count fields -> record link fields
    - Record link fields <-> inverse link fields
    
    Args:
        metadata: AirtableMetadata instance containing tables and fields
        
    Returns:
        nx.DiGraph: A directed graph where you can traverse both forwards and backwards
    """
    G = nx.DiGraph()
    
    # Add all fields as nodes with their metadata
    for table in metadata["tables"]:
        table_id = table["id"]
        table_name = table["name"]
        
        # Add table as a node
        G.add_node(table_id, type="table", name=table_name)
        
        for field in table["fields"]:
            field_id = field["id"]
            field_name = field["name"]
            field_type = field["type"]

            if field.get("options", {}).get("isValid") is False:
                continue  # Skip invalid fields
            
            # Add field as a node with metadata
            G.add_node(
                field_id,
                type="field",
                name=field_name,
                field_type=field_type,
                table_id=table_id,
                table_name=table_name,
                metadata=field
            )
            
            # Add edge from table to field
            # G.add_edge(table_id, field_id, relationship="contains")
            
            # Add edges based on field type
            match field_type:
                case "count":
                    # Count field depends on a record link field
                    linked_id = field["options"]["recordLinkFieldId"]
                    G.add_edge(linked_id, field_id, relationship="count")
                    
                case "multipleRecordLinks":
                    # Link to the linked table
                    linked_table_id = field["options"]["linkedTableId"]
                    G.add_edge(field_id, linked_table_id, relationship="links_to")
                    
                    # Bidirectional link with inverse field if present
                    # TODO fix inverse links
                    # inverse_id = field["options"].get("inverseLinkFieldId", "")
                    # if inverse_id:
                    #     G.add_edge(field_id, inverse_id, relationship="inverse_link")
                    #     G.add_edge(inverse_id, field_id, relationship="inverse_link")
                        
                case "rollup":
                    # Rollup depends on a field in a linked table
                    linked_id = field["options"].get("fieldIdInLinkedTable")
                    if linked_id:
                        G.add_edge(linked_id, field_id, relationship="rollup")
                    
                    # Also depends on the record link field
                    record_link_id = field["options"]["recordLinkFieldId"]
                    G.add_edge(record_link_id, field_id, relationship="rollup_via")
                    
                case "multipleLookupValues":
                    # Lookup depends on a field in a linked table
                    linked_id = field["options"]["fieldIdInLinkedTable"]
                    G.add_edge(linked_id, field_id, relationship="lookup")
                    
                    # Also depends on the record link field
                    record_link_id = field["options"]["recordLinkFieldId"]
                    G.add_edge(record_link_id, field_id, relationship="lookup_via")
                    
                case "formula":
                    # Formula depends on referenced fields
                    for referenced_id in field["options"]["referencedFieldIds"]:
                        G.add_edge(referenced_id, field_id, relationship="formula")
                        
                case "lastModifiedTime":
                    # Last modified time can track specific fields
                    referenced_ids = field["options"].get("referencedFieldIds", [])
                    for referenced_id in referenced_ids:
                        G.add_edge(referenced_id, field_id, relationship="modified_time")
    
    return G


def get_relationship_dependency_complexity(
    G: nx.DiGraph, 
    field_id: str
):
    nodes = get_reachable_nodes(
        G,
        field_id,
        direction="backward"
    )

    relationship_counts = {}
    for u, v in nodes.edges():
        edge_data = nodes.get_edge_data(u, v)
        relationship = edge_data.get('relationship', 'unknown')
        relationship_counts[relationship] = relationship_counts.get(relationship, 0) + 1
    
    tables_dependencies: dict[str, int] = get_distinct_table_dependencies_from_nodes(nodes)
    
    return {
        "relationship_counts": relationship_counts, 
        "tables_dependencies": tables_dependencies
    }


def get_distinct_table_dependencies_from_nodes(G: nx.DiGraph):
    tables_dependencies: dict[str, int] = {}
    for node_id in G.nodes():
        table_id = G.nodes[node_id].get("table_id")
        if table_id:
            tables_dependencies[table_id] = tables_dependencies.get(table_id, 0) + 1
    return tables_dependencies


def calculate_distances(
    G: nx.DiGraph, 
    source_node_id: str
) -> dict[str, int]:
    """
    Calculate the shortest distance from the source node to all other nodes in the graph.
    
    Args:
        G: The NetworkX DiGraph
        source_node_id: The starting node ID
    Returns:
        dict[str, int]: A dictionary mapping node IDs to their shortest distance from the source
    """
    distances = nx.single_source_shortest_path_length(G, source_node_id)
    return distances


def get_reachable_nodes(
    G: nx.DiGraph, 
    node_id: str,
    direction: str="both",
):
    # Use NetworkX built-in functions to get all reachable nodes
    if direction == 'backward':
        # Get all ancestors (nodes that have a path TO this node)
        nodes = list(nx.ancestors(G, node_id))
    elif direction == 'forward':
        # Get all descendants (nodes this node has a path TO)
        nodes = list(nx.descendants(G, node_id))
    else:  # both
        # Get both ancestors and descendants
        nodes = list(nx.ancestors(G, node_id)) + list(nx.descendants(G, node_id))

    # Add the source node
    nodes.append(node_id)

    # Get all table IDs from the reachable nodes
    table_ids = set()
    for node in nodes:
        if node in G.nodes:
            node_data = G.nodes[node]
            # Add table if this is a field node
            if node_data.get("type") == "field":
                table_id = node_data.get("table_id")
                if table_id:
                    table_ids.add(table_id)
            # Also check if this node is referenced as a linked table in edges
            for _, target, edge_data in G.out_edges(node, data=True):
                if edge_data.get("relationship") == "links_to" and target in G.nodes:
                    if G.nodes[target].get("type") == "table":
                        table_ids.add(target)
    
    # Add all table nodes to the nodes list
    nodes.extend(table_ids)

    return G.subgraph(nodes).copy()


def get_reachable_nodes_depth(
    G: nx.DiGraph, 
    node_id: str,
    direction: str="both",
    max_depth: int | None = None,
):
    """
    Get all reachable nodes with depth information.
    
    Uses NetworkX's built-in traversal but tracks depth for each node.
    
    Args:
        G: The NetworkX DiGraph
        node_id: The starting node ID
        direction: 'backward', 'forward', or 'both'
        max_depth: Optional maximum depth to traverse
        
    Returns:
        tuple: (subgraph, depth_dict) where depth_dict maps node IDs to their depth from source
    """
    # Calculate distances (depths) from the source node
    if direction == 'backward':
        # For backward, we need to reverse the graph to get distances
        G_reversed = G.reverse()
        distances = nx.single_source_shortest_path_length(G_reversed, node_id, cutoff=max_depth)
        nodes = list(distances.keys())
        nodes.remove(node_id)  # Remove source from list
    elif direction == 'forward':
        distances = nx.single_source_shortest_path_length(G, node_id, cutoff=max_depth)
        nodes = list(distances.keys())
        nodes.remove(node_id)  # Remove source from list
    else:  # both
        # Get forward distances
        forward_distances = nx.single_source_shortest_path_length(G, node_id, cutoff=max_depth)
        # Get backward distances
        G_reversed = G.reverse()
        backward_distances = nx.single_source_shortest_path_length(G_reversed, node_id, cutoff=max_depth)
        
        # Combine, preferring shorter distance if node appears in both
        distances = {}
        for node, depth in forward_distances.items():
            distances[node] = depth
        for node, depth in backward_distances.items():
            if node in distances:
                distances[node] = min(distances[node], depth)
            else:
                distances[node] = depth
        
        nodes = list(distances.keys())
        nodes.remove(node_id)  # Remove source from list
    
    # Add source node with depth 0
    distances[node_id] = 0
    
    # Get all table IDs from the reachable nodes and add them
    table_ids = set(get_distinct_table_dependencies_from_nodes(G.subgraph(nodes + [node_id])).keys())
    for table_id in table_ids:
        if table_id not in distances:
            nodes.append(table_id)
            distances[table_id] = -1  # Mark table nodes with special depth
    
    # Create subgraph and add depth as node attribute
    subgraph = G.subgraph(nodes + [node_id]).copy()
    nx.set_node_attributes(subgraph, distances, 'depth')
    
    print(f"Reached max depth of {max(d for d in distances.values() if d >= 0)} from node {node_id} reaching {len(distances)} nodes")
    
    return subgraph, distances


def get_reachable_nodes_advanced(
    G: nx.DiGraph, 
    node_id: str,
    direction: str="both",
    include_types=None, 
    exclude_types=["contains"],
    max_depth: int | None = None,
    include_table_nodes: bool = True,
):
    def is_edge_allowed(u, v):
        edge_data = G.get_edge_data(u, v)
        if not edge_data:
            return False
        
        edge_type = edge_data.get('relationship')

        # Logic 1: If include list is provided, edge type MUST be in it.
        if include_types is not None:
            if edge_type not in include_types:
                return False
        
        # Logic 2: If exclude list is provided, edge type MUST NOT be in it.
        if exclude_types is not None:
            if edge_type in exclude_types:
                return False
                
        # If both checks pass (or were None), the edge is allowed.
        return True

    # Define the custom neighbor generator using the new is_edge_allowed checker
    if direction == 'backward':
        def neighbors_func(n):
            for predecessor in G.predecessors(n):
                if is_edge_allowed(predecessor, n):
                    yield predecessor
    elif direction == 'forward':
        def neighbors_func(n):
            for successor in G.successors(n):
                if is_edge_allowed(n, successor):
                    yield successor
    elif direction == 'both':
        def neighbors_func(n):
            for predecessor in G.predecessors(n):
                if is_edge_allowed(predecessor, n):
                    yield predecessor
            for successor in G.successors(n):
                if is_edge_allowed(n, successor):
                    yield successor
    
    # Perform BFS traversal manually with custom neighbor function
    queue: list[dict] = [{ "id": node_id, "depth": 0 }] 
    visited_nodes: dict[str, dict] = {node_id: { "depth": 0 }}
    
    max_visited_depth = 0
    while queue:
        current = queue.pop(0)

        if max_depth and current["depth"] >= max_depth:
            continue

        for neighbor in neighbors_func(current["id"]):
            if neighbor not in visited_nodes:
                current_depth = current["depth"] + 1
                next_node = { "depth": current_depth }
                visited_nodes[neighbor] = next_node
                max_visited_depth = max(max_visited_depth, current_depth)
                queue.append({ "id": neighbor, "depth": current_depth })

    print(f"Reached max depth of {max_visited_depth} from node {node_id} reaching {len(visited_nodes)} nodes")
    
    # visited_nodes.update(table_ids)
    nodes_graph = G.subgraph(list(visited_nodes.keys())).copy()
    table_ids = set(get_distinct_table_dependencies_from_nodes(nodes_graph).keys())
    for table_id in table_ids:
        nodes_graph.add_node(
            table_id,
            type="table",
            name=G.nodes[table_id].get("name", table_id)
        )

    return nodes_graph


def graph_to_mermaid(
    graph: nx.DiGraph,
    direction: str = "TD",
    display_mode: str = "simple"
) -> str:
    """
    Convert a NetworkX DiGraph to a Mermaid flowchart diagram.
    
    Args:
        graph: The NetworkX DiGraph to convert
        direction: Flowchart direction - "TD" (top-down), "LR" (left-right), 
                  "RL" (right-left), or "BT" (bottom-top)
        display_mode: Display mode - "simple", "descriptions", "formulas", or "all"
        
    Returns:
        str: Mermaid flowchart diagram as a string
    """
    if direction not in ["TD", "LR", "RL", "BT"]:
        raise ValueError(f"Invalid direction '{direction}'. Must be 'TD', 'LR', 'RL', or 'BT'")
    
    mermaid_lines = [f"flowchart {direction}"]

    print(f"Generating Mermaid diagram with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    
    # Group nodes by table for subgraphs
    tables = {}
    standalone_nodes = []
    
    for node_id in graph.nodes():
        node_data = graph.nodes[node_id]
        node_type = node_data.get("type")
        
        if node_type == "table":
            if node_id not in tables:
                tables[node_id] = {
                    "name": node_data.get("name", node_id),
                    "fields": []
                }
            # Otherwise, update the name
            tables[node_id]["name"] = node_data.get("name", node_id) 
        elif node_type == "field":
            table_id = node_data.get("table_id")
            if table_id and table_id in graph.nodes():
                if table_id not in tables:
                    tables[table_id] = {
                        "name": graph.nodes[table_id].get("name", table_id),
                        "fields": []
                    }
                tables[table_id]["fields"].append(node_id)
            else:
                standalone_nodes.append(node_id)
    
    # Generate table subgraphs
    for table_id, table_info in tables.items():
        if not table_info["fields"]:
            # Table with no fields - render as a simple box node
            escaped_name = table_info["name"].replace("(", "[").replace(")", "]").replace('"', "'").replace("#", "&#35;")
            mermaid_lines.append(f'    {table_id}["{escaped_name}"]')
            continue
            
        mermaid_lines.append(f'    subgraph {table_id}["{table_info["name"]}"]')
        
        for field_id in table_info["fields"]:
            node_label = _format_node_label(graph, field_id, display_mode)
            mermaid_lines.append(f'        {field_id}{node_label}')
        
        mermaid_lines.append("    end")
    
    # Generate standalone nodes (fields without tables in the graph)
    for node_id in standalone_nodes:
        node_label = _format_node_label(graph, node_id, display_mode)
        mermaid_lines.append(f'    {node_id}{node_label}')
    
    # Generate edges
    for source, target in graph.edges():
        edge_data = graph.edges[source, target]
        relationship = edge_data.get("relationship", "")
        
        # Skip "contains" relationships as they're implicit in subgraphs
        if relationship == "contains":
            continue
        
        # Format edge based on relationship type
        edge_style = _format_edge(relationship)
        label = f"|{relationship}|" if relationship else ""
        
        mermaid_lines.append(f'    {source} {edge_style}{label} {target}')
    
    return "\n".join(mermaid_lines)


def _replace_field_ids_with_names(formula: str, graph: nx.DiGraph) -> str:
    """
    Replace field IDs in a formula with their corresponding field names.
    
    Field IDs are in the format {fldXXXXXXXXXXXXXX} where X is alphanumeric.
    
    Args:
        formula: The formula string containing field IDs
        graph: The NetworkX graph containing field metadata
        
    Returns:
        str: Formula with field IDs replaced by field names
    """
    # Pattern to match field IDs: {fld followed by 14 alphanumeric characters}
    field_id_pattern = r'\{(fld[A-Za-z0-9]{14})\}'
    
    def replace_id(match):
        field_id = match.group(1)
        # Look up the field name in the graph
        if field_id in graph.nodes:
            field_name = graph.nodes[field_id].get("name", field_id)
            return f"{{{field_name}}}"
        # If not found, keep the original ID
        return match.group(0)
    
    return re.sub(field_id_pattern, replace_id, formula)


def _get_formula_text(field_metadata: dict, graph: nx.DiGraph = None) -> str:
    """
    Extract formula/calculation text from field metadata.
    
    Returns formula text for:
    - Formula fields: the actual formula
    - Rollup fields: the aggregation function
    - Lookup fields: indication of lookup (formulas would be in the source field)
    
    Args:
        field_metadata: The field metadata dictionary
        graph: The NetworkX graph (optional, used for replacing field IDs with names)
        
    Returns:
        str: The formula text or empty string if not applicable
    """
    field_type = field_metadata.get("type")
    options = field_metadata.get("options", {})
    
    match field_type:
        case "formula":
            formula = options.get("formula", "")
            # Replace field IDs with names if graph is provided
            if formula and graph:
                formula = _replace_field_ids_with_names(formula, graph)
            return formula
        case "rollup":
            # For rollups, we can't show the full formula easily, but we can show the aggregation
            # The actual calculation happens via recordLinkFieldId -> fieldIdInLinkedTable
            return "ROLLUP(...)"  # Simplified representation
        case "multipleLookupValues":
            # Lookups just reference a field, no formula per se
            return "LOOKUP(...)"  # Simplified representation
        case _:
            return ""


def _format_node_label(graph: nx.DiGraph, node_id: str, display_mode: str = "simple") -> str:
    """
    Format a node label for Mermaid based on node data and display mode.
    
    Args:
        graph: The NetworkX graph
        node_id: The node ID to format
        display_mode: One of "simple", "descriptions", "formulas", or "all"
        
    Returns:
        str: Formatted Mermaid node label
    """
    node_data = graph.nodes[node_id]
    node_type = node_data.get("type")
    name = node_data.get("name", node_id)
    
    # Escape problematic characters for Mermaid
    def escape_mermaid_text(text: str) -> str:
        """Escape characters that cause Mermaid syntax issues"""
        # Replace parentheses with square brackets to avoid syntax conflicts
        text = text.replace("(", "[").replace(")", "]")
        # Also escape quotes
        text = text.replace('"', "'")
        # Escape # to prevent it from being treated as a comment
        text = text.replace("#", "&#35;")
        return text
    
    if node_type == "table":
        return f'["{escape_mermaid_text(name)}"]'
    
    # Field node
    field_type = node_data.get("field_type", "")
    metadata = node_data.get("metadata", {})
    
    # Get icon based on field type
    icon = _get_field_icon(field_type)
    escaped_name = escape_mermaid_text(name)
    
    # Simple mode: just name with icon
    if display_mode == "simple":
        return f'("{icon} {escaped_name}")'
    
    # Build detailed label based on mode
    table_name = escape_mermaid_text(node_data.get("table_name", ""))
    lines = [f"Name: {escaped_name}", f"Type: {icon} {field_type}", f"Table: {table_name}"]
    
    # Add description if needed
    if display_mode in ["descriptions", "all"]:
        description = escape_mermaid_text(metadata.get("description", "N/A"))
        lines.append(f"Description: {description}")
    
    # Add formula if needed and applicable
    if display_mode in ["formulas", "all"]:
        formula_text = _get_formula_text(metadata, graph)
        if formula_text:
            escaped_formula = escape_mermaid_text(formula_text)
            lines.append(f"Formula: {escaped_formula}")
    
    # Join lines with <br> for Mermaid
    content = "<br>\n".join(lines)
    return f'''("
{content}<br>
")'''


def _get_field_icon(field_type: str) -> str:
    """Get an emoji icon for a field type."""
    icons = {
        "autoNumber": "↓",
        "count": "🗳️",
        "multipleRecordLinks": "🔗",
        "singleSelect": "→",
        "singleLineText": "📝",
        "multilineText": "📝",
        "richText": "📝",
        "number": "🔢",
        "multipleSelects": "☰",
        "checkbox": "☑️",
        "date": "📅",
        "createdTime": "🕒",
        "email": "📧",
        "url": "🔗",
        "percent": "📊",
        "rating": "⭐",
        "duration": "⏱️",
        "multipleAttachments": "📎",
        "rollup": "🧻",
        "multipleLookupValues": "🔭",
        "formula": "f<sub>x</sub>",
    }
    return icons.get(field_type, "")


def _format_edge(relationship: str) -> str:
    """Format edge style based on relationship type."""
    edge_styles = {
        "inverse_link": "<-->",
        "links_to": "-->",
        "formula": "-->",
        "lookup": "-.->",
        "lookup_via": "-.->",
        "rollup": "-.->",
        "rollup_via": "-.->",
        "count": "-->",
        "modified_time": "-->",
    }
    return edge_styles.get(relationship, "-->")
    