#!/usr/bin/env python3
"""Extended test to verify table nodes work in various scenarios"""

import json
import sys
sys.path.append("web")

from web.at_metadata_graph import metadata_to_graph, get_reachable_nodes, graph_to_mermaid

# Load sample schema
with open("web/sample_schema.json") as f:
    metadata = json.load(f)

# Create the full graph
G = metadata_to_graph(metadata)

test_cases = [
    ("fldzfxzDCAD7dYyxj", "Attendees field linking to Contacts table"),
    ("fldJ6JauxlLpLJo5U", "Projects field in Contacts table"),
    ("fldLEmWK0V3LnC8ra", "Contacts field in Projects table"),
]

for field_id, description in test_cases:
    print(f"\n{'='*80}")
    print(f"Test: {description}")
    print(f"Field ID: {field_id}")
    print('='*80)
    
    # Get reachable nodes
    subgraph = get_reachable_nodes(G, field_id, direction="both")
    
    # Count table nodes
    table_nodes = [n for n in subgraph.nodes if subgraph.nodes[n].get("type") == "table"]
    
    print(f"\nFound {len(table_nodes)} table nodes:")
    for table_id in table_nodes:
        print(f"  - {table_id}: {subgraph.nodes[table_id].get('name')}")
    
    # Generate Mermaid diagram
    mermaid = graph_to_mermaid(subgraph, direction="TD", display_mode="simple")
    
    # Check all table nodes are in the diagram
    for table_id in table_nodes:
        if table_id in mermaid:
            print(f"  ✅ Table {table_id} appears in diagram")
        else:
            print(f"  ❌ Table {table_id} MISSING from diagram")
    
    print("\nGenerated diagram:")
    print(mermaid)
