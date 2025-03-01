from enum import Enum
import re
from typing import TypedDict
import sys
sys.path.append("web")
from at_types import AirTableFieldMetadata, AirtableMetadata, TableMetadata

INDENT = "    "

class FieldGraphNode(TypedDict):
    nodes: list[str]
    edges: list[str]


def field_metadata_to_mermaid_node(
        field: AirTableFieldMetadata,
        full_description: bool = True
) -> FieldGraphNode:
    nodes: list[str] = []
    edges: list[str] = []
    icon: str = ""
    field_id = field["id"]
    field_name = field["name"]
    match field["type"]:
        case "autoNumber":
            icon = "↓"
        case "count":
            icon = "🗳️"
            linked_id = field["options"]["recordLinkFieldId"]
            edges.append(f"{field_id} --length--> {linked_id}")
        case "multipleRecordLinks":
            icon = "🔗"
            table_id = field["options"]["linkedTableId"]
            # if inverseLinkFieldId
            inverse_id = field["options"].get("inverseLinkFieldId", "")
            if inverse_id:
                edges.append(f"{field_id} <--> {inverse_id}")
            edges.append(f"{table_id} --> {field_id}")
        case "singleSelect":
            icon = "→"
        case "singleLineText" | "multilineText" | "richText":
            icon = "📝"
        case "number":
            icon = "🔢"
        case "multipleSelects":
            icon = "☰"
        case "checkbox":
            icon = "☑️"
        case "date":
            icon = "📅"
        case "createdTime":
            icon = "🕒"
        case "email":
            icon = "📧"
        case "url":
            icon = "🔗"
        case "percent":
            icon = "📊"
        case "rating":
            icon = "⭐"
        case "duration":
            icon = "⏱️"
        case "multipleAttachments":
            icon = "📎"
        case "rollup":
            icon = "🧻"
            linked_id = field["options"]["fieldIdInLinkedTable"]
            edges.append(f"{linked_id} --> {field_id}")
        case "multipleLookupValues":
            icon = "🔭"
            linked_id = field["options"]["fieldIdInLinkedTable"]
            edges.append(f"{linked_id} --> {field_id}")
        case "formula":
            # icon = "🖩"
            icon = "f<sub>x</sub>"
            if full_description:
                # TODO draw formula graph...
                for linked_id in field["options"]["referencedFieldIds"]:
                    edges.append(f"{linked_id} --> {field_id}")
            else:
                for linked_id in field["options"]["referencedFieldIds"]:
                    edges.append(f"{linked_id} --> {field_id}")
        case _:
            pass

    
    # TODO we are using an array of nodes here so that we could append entire formulas in a subgraph
    # if a specific type above hasn't specified a full descrition, then we fall back to our default
    if not nodes:
        if full_description:
            nodes.append(f'''
                {field_id}("
                Name: {field_name}<br>
                Type: {icon} {field["type"]}<br>
                Description: {field.get("description", "N/A").replace('"', '')}<br>
                ")''')
        else:
            nodes.append(f'{field["id"]}("{icon} {field_name}")')

    return {
        "nodes": nodes,
        "edges": edges
    }


class MermaidFlowchartDirection(Enum):
    TD = "TD"
    LR = "LR"
    RL = "RL"
    BT = "BT"

def airtable_schema_to_mermaid(
    airtable_metadata: AirtableMetadata,
    field: str = "", 
    table_name: str = "",
    full_field_description: bool = False,
    direction: str = "TD",
    verbose: bool = False,
):
    id_filter: list[str] = []
    if field:
        # if the field_id matches this regex fld[A-Za-z0-9]{14}, then it is a 
        # true field ID
        # if not, we will assume it is a field name and look it up
        if not re.match(r"fld[A-Za-z0-9]{14}", field):
            # if this isn't a field ID, then we assume it is a field name and we need the user
            # to specify the table as well
            if not table_name:
                raise Exception("Please specify a table name when using a field name")
            
            field_metadata = get_field_metadata_by_name(field, table_name, airtable_metadata)
            if not field_metadata:
                raise Exception(f"Field {field} not found")
            
            field = field_metadata["id"]
        id_filter = find_all_related_fields_by_id_(
            field, 
            airtable_metadata, 
            verbose
        )

    id_filter_set = set(id_filter)

    # TODO bug where if this is a basic field, it won't be included in the filter
    # and basic fields don't get included here
    if field:
        id_filter_set.add(field)
    mermaid_text = f'flowchart {direction}\n'
    tables = airtable_metadata["tables"]
    for table in tables:
        for line in table_metadata_to_mermaid(table, list(id_filter_set), full_field_description):
            mermaid_text += f"{INDENT}{line}\n"
        
    
    print(f"Mermaid result is {len(mermaid_text)} characters long")
    if verbose:
        print(mermaid_text)

    return mermaid_text
    

def table_metadata_to_mermaid(
        table: TableMetadata, 
        id_filter: list[str],
        full_field_description: bool = False
) -> list[str]:
    result: list[str] = []
    table_id = table["id"]
    table_name = table["name"]
    all_nodes: list[str] = []
    all_edges: list[str] = []
    for field in table["fields"]:
        if id_filter and field["id"] not in id_filter:
            continue

        edge_node_result = field_metadata_to_mermaid_node(
            field,
            full_field_description
        )
        nodes, edges = edge_node_result["nodes"], edge_node_result["edges"]
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    if not all_nodes:
        return []
    
    result.append(f'subgraph {table_id}["{table_name}"]')
    result.extend((f'{INDENT}{node}' for node in all_nodes))
    result.append("end")
    result.extend(all_edges)
    return result


def get_field_metadata_by_name(
        field_name: str, 
        table_name: str,
        metadata: AirtableMetadata
):
    for table in metadata["tables"]:
        if table["name"] == table_name:
            for field in table["fields"]:
                if field["name"] == field_name:
                    return field
    return None

def get_field_name_by_id(field_id: str, metadata: AirtableMetadata):
    metadata = get_field_metadata_by_id(field_id, metadata)
    if metadata:
        return metadata["name"]
    return None

def get_field_metadata_by_id(field_id: str, metadata: AirtableMetadata):
    for table in metadata["tables"]:
        for field in table["fields"]:
            if field["id"] == field_id:
                return field
    return None


def find_all_related_fields_by_id_(
        field_id: str, 
        airtable_metadata: AirtableMetadata,
        verbose: bool = False
)-> list[str]:
    field = get_field_metadata_by_id(field_id, airtable_metadata)
    if not field:
        print(f"Field {field_id} not found")
        return []
    
    result: list[str] = []
    visited_fields: set[str] = set()
    result.extend(get_related_fields(airtable_metadata, field, visited_fields))
    if verbose:
        print(f'Related Fields: {result}')
        print(f'Visited Fields: {visited_fields}')
    
    return result


def get_related_fields(
        airtable_metadata: AirtableMetadata, 
        field_metadata: AirTableFieldMetadata, 
        visited_fields: set[str] = set(),
        depth = 0,
):
    def print_debug(x): print(f"{depth * INDENT}{x}")

    next_fields_to_search: list[str] = []

    print_debug(f'Exploring {field_metadata["id"]} {field_metadata["type"]} {field_metadata["name"]}')
    
    if field_metadata["id"] in visited_fields:
        print_debug(f"Already visited {field_metadata['id']}")
        return []

    visited_fields.add(field_metadata["id"])

    match field_metadata["type"]:
        case "count":
            next_fields_to_search = [field_metadata["options"]["recordLinkFieldId"]]
        case "multipleLookupValues" | "rollup":
            id_to_search = field_metadata["options"]["fieldIdInLinkedTable"]
            next_fields_to_search = [id_to_search]
        case "formula":
            next_fields_to_search = field_metadata["options"]["referencedFieldIds"]
        case "multipleRecordLinks":
            # TODO for some reason, sometimes the inverse link field is not present
            inverse_field = field_metadata["options"].get("inverseLinkFieldId", "")
            if inverse_field:
                next_fields_to_search = [inverse_field]
            else:
                next_fields_to_search = [field_metadata["options"]["linkedTableId"]]
        case "rollup":
            next_fields_to_search = [field_metadata["options"]["fieldIdInLinkedTable"]]
        case _:
            print_debug("Return default")
            return []
    
    if not next_fields_to_search:
        return []
    
    result: list[str] = [field_metadata["id"]]
    for field_id in next_fields_to_search:
        field = get_field_metadata_by_id(field_id, airtable_metadata)
        if field:
            result.append(field_id)
            result.extend(
                get_related_fields(
                    airtable_metadata, 
                    field, 
                    visited_fields, 
                    depth + 1
                )
            )
    
    print(f"Get related fields: {result}")
    return result
