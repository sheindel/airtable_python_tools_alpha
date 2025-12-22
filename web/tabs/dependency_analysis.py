"""Dependency Analysis Tab - Analyze complexity and issues in base structure"""
from pyscript import document, window

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from at_metadata_graph import metadata_to_graph, get_relationship_dependency_complexity


def analyze_field_complexity(field_id: str):
    """Analyze the complexity of a field's dependencies
    
    Returns information about:
    - Number and types of relationships
    - Tables involved
    - Depth of dependency tree
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        print("No metadata available")
        return None
    
    G = metadata_to_graph(airtable_metadata)
    complexity = get_relationship_dependency_complexity(G, field_id)
    
    return complexity


def initialize():
    """Initialize the Dependency Analysis tab"""
    print("Dependency Analysis tab initialized")
    # TODO: Add UI elements and event handlers
    pass
