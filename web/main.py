import json

from pyscript import document, window
from pyodide.ffi.wrappers import add_event_listener

from at_types import AirtableMetadata
from airtable_mermaid_generator import airtable_schema_to_mermaid


def save_local_storage(key: str, value):
    window.localStorage.setItem(key, value)
    

def get_local_storage(key: str):
    return window.localStorage.getItem(key)


def get_local_storage_metadata():
    metadata = get_local_storage("airtableSchema")
    if metadata:
        json_data: AirtableMetadata = json.loads(metadata)["schema"]
        return json_data
    else:
        return None


table_dropdown = document.getElementById("table-dropdown")
field_dropdown = document.getElementById("field-dropdown")
flowchart_type_dropdown = document.getElementById("flowchart-type")
max_depth_input = document.getElementById("max-depth")

def update_mermaid_graph(
    table_name: str,
    field_name: str,
    flowchart_type: str,
):
    print(f"Table: {table_name}, Field: {field_name}")
    airtable_metadata = get_local_storage_metadata()
    mermaid_text = airtable_schema_to_mermaid(
        airtable_metadata,
        field=field_name, 
        table_name=table_name, 
        direction=flowchart_type,
        verbose=False
    )
    save_local_storage("lastGraphDefinition", mermaid_text)

    mermaid_container = document.getElementById("mermaid-container")
    mermaid_container.innerHTML = f'<div class="mermaid">{mermaid_text}</div>'
    window.mermaid.run()


def parametersChanged(event):
    # TODO are we sure this can't be multi-selected in the HTML?
    table = table_dropdown.selectedOptions[0].text
    field_name = field_dropdown.selectedOptions[0].text
    direction = flowchart_type_dropdown.selectedOptions[0].value
    max_depth = max_depth_input.value
    print(type(max_depth))
    print(f"Table: {table}, Field: {field_name}, Direction: {direction}, Max Depth: {max_depth}")

    update_mermaid_graph(table, field_name, direction)


add_event_listener(field_dropdown, "change", parametersChanged)
add_event_listener(flowchart_type_dropdown, "change", parametersChanged)
add_event_listener(max_depth_input, "change", parametersChanged)