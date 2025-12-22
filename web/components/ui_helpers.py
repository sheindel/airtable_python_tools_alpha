"""Shared UI helper functions"""
from pyscript import document


def populate_table_dropdown(tables_data: list, dropdown_id: str = "table-dropdown"):
    """Populate table dropdown with sorted table names
    
    Args:
        tables_data: List of table metadata dictionaries
        dropdown_id: ID of the dropdown element to populate
    """
    table_options = []
    for table in tables_data:
        table_options.append({
            "id": table["id"],
            "text": table["name"]
        })
    
    # Sort alphabetically
    table_options.sort(key=lambda x: x["text"])
    
    return table_options


def populate_field_dropdown(fields_data: list, table_id: str, dropdown_id: str = "field-dropdown"):
    """Populate field dropdown with sorted field names
    
    Args:
        fields_data: List of field metadata dictionaries
        table_id: ID of the parent table
        dropdown_id: ID of the dropdown element to populate
    """
    field_options = []
    for field in fields_data:
        field_options.append({
            "id": field["id"],
            "text": field["name"],
            "tableId": table_id
        })
    
    # Sort alphabetically
    field_options.sort(key=lambda x: x["text"])
    
    return field_options


def show_error(message: str, container_id: str = "error-container"):
    """Display an error message to the user"""
    container = document.getElementById(container_id)
    if container:
        container.innerHTML = f'<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">{message}</div>'
        container.classList.remove("hidden")


def hide_error(container_id: str = "error-container"):
    """Hide the error message container"""
    container = document.getElementById(container_id)
    if container:
        container.classList.add("hidden")
