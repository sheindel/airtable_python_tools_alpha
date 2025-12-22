"""Table Analysis Tab - Analyze table complexity and external dependencies"""
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


def table_ids_to_names(table_ids: list, metadata) -> list:
    """Convert table IDs to table names"""
    result = []
    for table_id in table_ids:
        for table in metadata["tables"]:
            if table["id"] == table_id:
                result.append(table["name"])
                break
    return result


def get_table_complexity(table_name: str):
    """Analyze a table and return CSV data of field complexity
    
    Returns information about formula, rollup, and lookup fields
    including which external tables they depend on.
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        return None
    
    G = metadata_to_graph(airtable_metadata)
    
    # Find the table
    target_table = None
    for table in airtable_metadata["tables"]:
        if table["name"] == table_name:
            target_table = table
            break
    
    if not target_table:
        return None
    
    csv_results = []
    csv_results.append(["Field Name", "Field Type", "Dependent Tables"])
    
    for field in target_table["fields"]:
        field_type = field.get("type")
        if field_type not in ["formula", "rollup", "multipleLookupValues"]:
            continue
        
        result = get_relationship_dependency_complexity(G, field["id"])
        table_names = table_ids_to_names(
            list(result["tables_dependencies"].keys()),
            airtable_metadata
        )
        csv_results.append(
            [field["name"], field_type, ";".join(table_names)]
        )
    
    return csv_results


def initialize():
    """Initialize the Table Analysis tab"""
    print("Table Analysis tab initialized")
    
    # Export functions to JavaScript
    from pyscript import window
    window.getTableComplexityData = get_table_complexity
    
    pass
