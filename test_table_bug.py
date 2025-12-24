#!/usr/bin/env python3
"""Test script to verify table nodes are included in dependency graphs"""

import json
import sys
sys.path.append("web")

from web.at_metadata_graph import metadata_to_graph, get_reachable_nodes, graph_to_mermaid

# Load sample schema
with open("web/sample_schema.json") as f:
    metadata = json.load(f)

# Create the full graph
G = metadata_to_graph(metadata)

# Test the specific field mentioned by the user: fldzfxzDCAD7dYyxj (Attendees field in Events table)
field_id = "fldzfxzDCAD7dYyxj"

# Get reachable nodes
subgraph = get_reachable_nodes(G, field_id, direction="both")

# Generate Mermaid diagram
mermaid = graph_to_mermaid(subgraph, direction="TD", display_mode="simple")

print("Generated Mermaid diagram:")
print(mermaid)
print("\n" + "="*80 + "\n")

# Check if the linked table is in the graph
linked_table_id = "tbl622YB7LCEUgXhy"  # Contacts table
if linked_table_id in subgraph.nodes:
    table_data = subgraph.nodes[linked_table_id]
    print(f"✅ Table {linked_table_id} found in graph")
    print(f"   Name: {table_data.get('name', 'N/A')}")
    print(f"   Type: {table_data.get('type', 'N/A')}")
else:
    print(f"❌ Table {linked_table_id} NOT found in graph")
    print(f"   This is the bug!")

print("\nAll nodes in subgraph:")
for node_id in subgraph.nodes:
    node_data = subgraph.nodes[node_id]
    print(f"  {node_id}: {node_data.get('name', 'N/A')} ({node_data.get('type', 'N/A')})")
