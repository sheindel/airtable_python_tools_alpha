"""Table Dependencies Tab - Analyze table-to-table dependencies and relationships"""
try:
    from pyscript import document, window
    _HAS_PYSCRIPT = True
except ImportError:
    _HAS_PYSCRIPT = False

import sys
sys.path.append("web")
from components.airtable_client import get_local_storage_metadata
from at_metadata_graph import get_table_to_table_dependencies


def get_table_dependencies():
    """Get all table-to-table dependencies in the base.
    
    Returns a list of lists: [source_table, target_table, links, rollups, lookups, total]
    """
    airtable_metadata = get_local_storage_metadata()
    if not airtable_metadata:
        return None
    
    dependencies_dict = get_table_to_table_dependencies(airtable_metadata)
    
    # Convert to flat list of lists for JavaScript compatibility
    results = []
    for source_table, targets in dependencies_dict.items():
        for target_table, counts in targets.items():
            total = counts["links"] + counts["rollups"] + counts["lookups"]
            # Return as list: [source, target, links, rollups, lookups, total]
            results.append([
                source_table,
                target_table,
                counts["links"],
                counts["rollups"],
                counts["lookups"],
                total
            ])
    
    # Sort by source table, then by total count descending
    results.sort(key=lambda x: (x[0], -x[5]))
    
    return results


def initialize():
    """Initialize the Table Dependencies tab"""
    print("Table Dependencies tab initialized")
    
    # Export functions to JavaScript (only in PyScript context)
    if _HAS_PYSCRIPT:
        window.getTableDependencies = get_table_dependencies
