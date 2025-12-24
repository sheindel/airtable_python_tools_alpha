"""Script to add complex formula, rollup, and lookup fields to the demo base"""
import httpx
import json
from dotenv import load_dotenv
import os
import time

load_dotenv()

# Get credentials from .env
PAT = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_APP_ID")


def get_base_schema():
    """Get the current schema of the base"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    return response.json()


def create_field(table_id: str, field_config: dict):
    """Create a new field in a table"""
    url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables/{table_id}/fields"
    
    response = httpx.post(
        url,
        headers={
            "Authorization": f"Bearer {PAT}",
            "Content-Type": "application/json"
        },
        json=field_config
    )
    
    if response.status_code in [200, 201]:
        print(f"✓ Created field: {field_config['name']}")
        return response.json()
    else:
        print(f"✗ Error creating {field_config['name']}: {response.status_code}")
        print(f"  {response.text}")
        return None


def find_table_by_name(schema, table_name: str):
    """Find a table by name"""
    for table in schema["tables"]:
        if table["name"] == table_name:
            return table
    return None


def find_field_by_name(table, field_name: str):
    """Find a field by name in a table"""
    for field in table["fields"]:
        if field["name"] == field_name:
            return field
    return None


def add_complex_fields():
    """Add complex formula, rollup, and lookup fields"""
    
    print("Fetching base schema...")
    schema = get_base_schema()
    
    if not schema:
        print("Failed to fetch schema")
        return
    
    print(f"\nAdding complex fields to base {BASE_ID}...\n")
    
    # Find table IDs
    projects_table = find_table_by_name(schema, "Projects")
    tasks_table = find_table_by_name(schema, "Tasks")
    clients_table = find_table_by_name(schema, "Clients")
    contacts_table = find_table_by_name(schema, "Contacts")
    resources_table = find_table_by_name(schema, "Resources")
    milestones_table = find_table_by_name(schema, "Milestones")
    
    # Get field IDs we need for references
    project_start_field = find_field_by_name(projects_table, "Start Date")
    project_end_field = find_field_by_name(projects_table, "End Date")
    project_budget_field = find_field_by_name(projects_table, "Budget")
    project_status_field = find_field_by_name(projects_table, "Status")
    project_tasks_field = find_field_by_name(projects_table, "Related Tasks")
    project_client_field = find_field_by_name(projects_table, "Client")
    
    task_due_field = find_field_by_name(tasks_table, "Due Date")
    task_status_field = find_field_by_name(tasks_table, "Status")
    task_project_field = find_field_by_name(tasks_table, "Project")
    task_dependencies_field = find_field_by_name(tasks_table, "Dependency Tasks")
    
    client_projects_field = find_field_by_name(clients_table, "Projects")
    
    milestone_target_field = find_field_by_name(milestones_table, "Target Date")
    milestone_tasks_field = find_field_by_name(milestones_table, "Related Tasks")
    
    # Wait a bit to avoid rate limiting
    time.sleep(1)
    
    print("=" * 60)
    print("PROJECTS TABLE - Complex Fields")
    print("=" * 60)
    
    # 1. Projects: Duration in Days (formula)
    create_field(projects_table["id"], {
        "name": "Duration (Days)",
        "type": "formula",
        "options": {
            "formula": f"DATETIME_DIFF({{{project_end_field['id']}}}, {{{project_start_field['id']}}}, 'days')"
        }
    })
    time.sleep(0.5)
    
    # 2. Projects: Budget per Day (formula with division)
    create_field(projects_table["id"], {
        "name": "Budget per Day",
        "type": "formula",
        "options": {
            "formula": f"IF(DATETIME_DIFF({{{project_end_field['id']}}}, {{{project_start_field['id']}}}, 'days') > 0, {{{project_budget_field['id']}}} / DATETIME_DIFF({{{project_end_field['id']}}}, {{{project_start_field['id']}}}, 'days'), 0)"
        }
    })
    time.sleep(0.5)
    
    # 3. Projects: Days Remaining (formula with NOW())
    create_field(projects_table["id"], {
        "name": "Days Remaining",
        "type": "formula",
        "options": {
            "formula": f"IF({{{project_status_field['id']}}} = 'Completed', 0, DATETIME_DIFF({{{project_end_field['id']}}}, TODAY(), 'days'))"
        }
    })
    time.sleep(0.5)
    
    # 4. Projects: Total Tasks (rollup count)
    create_field(projects_table["id"], {
        "name": "Total Tasks",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": project_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "count"
            }
        }
    })
    time.sleep(0.5)
    
    # 5. Projects: Completed Tasks (rollup with condition)
    create_field(projects_table["id"], {
        "name": "Completed Tasks",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": project_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "countAll",
                "conditions": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "fieldId": task_status_field["id"],
                            "operator": "is",
                            "value": "Done"
                        }
                    ]
                }
            }
        }
    })
    time.sleep(0.5)
    
    # 6. Projects: Percent Complete (formula using rollups)
    # First we need to get the IDs of the rollup fields we just created
    schema = get_base_schema()
    projects_table = find_table_by_name(schema, "Projects")
    total_tasks_field = find_field_by_name(projects_table, "Total Tasks")
    completed_tasks_field = find_field_by_name(projects_table, "Completed Tasks")
    
    create_field(projects_table["id"], {
        "name": "Progress %",
        "type": "formula",
        "options": {
            "formula": f"IF({{{total_tasks_field['id']}}} > 0, ROUND({{{completed_tasks_field['id']}}} / {{{total_tasks_field['id']}}} * 100, 1) & '%', '0%')"
        }
    })
    time.sleep(0.5)
    
    # 7. Projects: Project Health (complex conditional formula)
    days_remaining_field = find_field_by_name(projects_table, "Days Remaining")
    progress_field = find_field_by_name(projects_table, "Progress %")
    
    create_field(projects_table["id"], {
        "name": "Health Status",
        "type": "formula",
        "options": {
            "formula": f"""IF(
    {{{project_status_field['id']}}} = 'Completed',
    '✅ Complete',
    IF(
        {{{days_remaining_field['id']}}} < 0,
        '🔴 Overdue',
        IF(
            AND({{{days_remaining_field['id']}}} < 30, {{{total_tasks_field['id']}}} > 0, {{{completed_tasks_field['id']}}} / {{{total_tasks_field['id']}}} < 0.5),
            '🟡 At Risk',
            '🟢 On Track'
        )
    )
)"""
        }
    })
    time.sleep(0.5)
    
    # 8. Projects: Client Name (lookup)
    create_field(projects_table["id"], {
        "name": "Client Name (Lookup)",
        "type": "multipleLookupValues",
        "options": {
            "recordLinkFieldId": project_client_field["id"],
            "fieldIdInLinkedTable": clients_table["primaryFieldId"],
            "referencedFieldIds": [clients_table["primaryFieldId"]]
        }
    })
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("TASKS TABLE - Complex Fields")
    print("=" * 60)
    
    # 9. Tasks: Days Overdue (formula)
    create_field(tasks_table["id"], {
        "name": "Days Overdue",
        "type": "formula",
        "options": {
            "formula": f"IF(AND({{{task_status_field['id']}}} != 'Done', {{{task_due_field['id']}}} < TODAY()), DATETIME_DIFF(TODAY(), {{{task_due_field['id']}}}, 'days'), 0)"
        }
    })
    time.sleep(0.5)
    
    # 10. Tasks: Priority Score (complex formula)
    create_field(tasks_table["id"], {
        "name": "Priority Score",
        "type": "formula",
        "options": {
            "formula": f"""SWITCH(
    {{{task_status_field['id']}}},
    'Done', 0,
    'Blocked', 5,
    'In Progress', IF({{{task_due_field['id']}}} < DATEADD(TODAY(), 7, 'days'), 10, 7),
    'Not Started', IF({{{task_due_field['id']}}} < DATEADD(TODAY(), 3, 'days'), 9, 5)
)"""
        }
    })
    time.sleep(0.5)
    
    # 11. Tasks: Has Dependencies (formula checking if field is not empty)
    create_field(tasks_table["id"], {
        "name": "Has Dependencies",
        "type": "formula",
        "options": {
            "formula": f"IF(LEN({{{task_dependencies_field['id']}}}) > 0, '🔗 Yes', '')"
        }
    })
    time.sleep(0.5)
    
    # 12. Tasks: Project Budget (lookup)
    create_field(tasks_table["id"], {
        "name": "Project Budget (Lookup)",
        "type": "multipleLookupValues",
        "options": {
            "recordLinkFieldId": task_project_field["id"],
            "fieldIdInLinkedTable": project_budget_field["id"],
            "referencedFieldIds": [project_budget_field["id"]]
        }
    })
    time.sleep(0.5)
    
    # 13. Tasks: Project Client (lookup through project to client)
    create_field(tasks_table["id"], {
        "name": "Client (Lookup)",
        "type": "multipleLookupValues",
        "options": {
            "recordLinkFieldId": task_project_field["id"],
            "fieldIdInLinkedTable": project_client_field["id"],
            "referencedFieldIds": [project_client_field["id"]]
        }
    })
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("CLIENTS TABLE - Complex Fields")
    print("=" * 60)
    
    # 14. Clients: Total Project Budget (rollup sum)
    create_field(clients_table["id"], {
        "name": "Total Budget",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": client_projects_field["id"],
            "fieldIdInLinkedTable": project_budget_field["id"],
            "referencedFieldIds": [project_budget_field["id"]],
            "result": {
                "type": "sum"
            }
        }
    })
    time.sleep(0.5)
    
    # 15. Clients: Number of Active Projects (rollup with condition)
    create_field(clients_table["id"], {
        "name": "Active Projects",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": client_projects_field["id"],
            "fieldIdInLinkedTable": project_status_field["id"],
            "referencedFieldIds": [project_status_field["id"]],
            "result": {
                "type": "countAll",
                "conditions": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "fieldId": project_status_field["id"],
                            "operator": "is",
                            "value": "Active"
                        }
                    ]
                }
            }
        }
    })
    time.sleep(0.5)
    
    # 16. Clients: Average Project Budget (rollup average)
    create_field(clients_table["id"], {
        "name": "Avg Project Budget",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": client_projects_field["id"],
            "fieldIdInLinkedTable": project_budget_field["id"],
            "referencedFieldIds": [project_budget_field["id"]],
            "result": {
                "type": "average"
            }
        }
    })
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("MILESTONES TABLE - Complex Fields")
    print("=" * 60)
    
    # 17. Milestones: Days Until Milestone (formula)
    create_field(milestones_table["id"], {
        "name": "Days Until",
        "type": "formula",
        "options": {
            "formula": f"DATETIME_DIFF({{{milestone_target_field['id']}}}, TODAY(), 'days')"
        }
    })
    time.sleep(0.5)
    
    # 18. Milestones: Completion Status (formula with rollup)
    create_field(milestones_table["id"], {
        "name": "Tasks Complete Count",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": milestone_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "countAll",
                "conditions": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "fieldId": task_status_field["id"],
                            "operator": "is",
                            "value": "Done"
                        }
                    ]
                }
            }
        }
    })
    time.sleep(0.5)
    
    # 19. Milestones: Total Related Tasks
    create_field(milestones_table["id"], {
        "name": "Total Related Tasks",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": milestone_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "count"
            }
        }
    })
    time.sleep(0.5)
    
    # 20. Milestones: Milestone Achievement (complex formula)
    schema = get_base_schema()
    milestones_table = find_table_by_name(schema, "Milestones")
    days_until_field = find_field_by_name(milestones_table, "Days Until")
    tasks_complete_field = find_field_by_name(milestones_table, "Tasks Complete Count")
    total_related_tasks_field = find_field_by_name(milestones_table, "Total Related Tasks")
    
    create_field(milestones_table["id"], {
        "name": "Achievement Status",
        "type": "formula",
        "options": {
            "formula": f"""IF(
    {{{total_related_tasks_field['id']}}} = 0,
    '⚪ No Tasks',
    IF(
        {{{tasks_complete_field['id']}}} = {{{total_related_tasks_field['id']}}},
        '✅ Complete',
        IF(
            {{{days_until_field['id']}}} < 0,
            '❌ Missed',
            IF(
                {{{days_until_field['id']}}} < 7,
                '⚠️ Due Soon',
                '📝 In Progress'
            )
        )
    )
)"""
        }
    })
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("CONTACTS TABLE - Complex Fields")
    print("=" * 60)
    
    contacts_tasks_field = find_field_by_name(contacts_table, "Tasks")
    contacts_projects_field = find_field_by_name(contacts_table, "Projects")
    
    # 21. Contacts: Task Count (rollup)
    create_field(contacts_table["id"], {
        "name": "Task Count",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": contacts_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "count"
            }
        }
    })
    time.sleep(0.5)
    
    # 22. Contacts: Active Task Count (rollup with NOT Done)
    create_field(contacts_table["id"], {
        "name": "Active Tasks",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": contacts_tasks_field["id"],
            "fieldIdInLinkedTable": task_status_field["id"],
            "referencedFieldIds": [task_status_field["id"]],
            "result": {
                "type": "countAll",
                "conditions": {
                    "conjunction": "and",
                    "conditions": [
                        {
                            "fieldId": task_status_field["id"],
                            "operator": "isNot",
                            "value": "Done"
                        }
                    ]
                }
            }
        }
    })
    time.sleep(0.5)
    
    # 23. Contacts: Workload Indicator (formula)
    schema = get_base_schema()
    contacts_table = find_table_by_name(schema, "Contacts")
    active_tasks_field = find_field_by_name(contacts_table, "Active Tasks")
    
    create_field(contacts_table["id"], {
        "name": "Workload",
        "type": "formula",
        "options": {
            "formula": f"""SWITCH(
    TRUE(),
    {{{active_tasks_field['id']}}} = 0, '✅ Available',
    {{{active_tasks_field['id']}}} <= 2, '🟢 Light',
    {{{active_tasks_field['id']}}} <= 4, '🟡 Moderate',
    '🔴 Heavy'
)"""
        }
    })
    time.sleep(0.5)
    
    print("\n" + "=" * 60)
    print("RESOURCES TABLE - Complex Fields")
    print("=" * 60)
    
    resources_projects_field = find_field_by_name(resources_table, "Assigned Projects")
    resources_tasks_field = find_field_by_name(resources_table, "Assigned Tasks")
    
    # 24. Resources: Project Count
    create_field(resources_table["id"], {
        "name": "Project Count",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": resources_projects_field["id"],
            "fieldIdInLinkedTable": projects_table["primaryFieldId"],
            "referencedFieldIds": [projects_table["primaryFieldId"]],
            "result": {
                "type": "count"
            }
        }
    })
    time.sleep(0.5)
    
    # 25. Resources: Task Count
    create_field(resources_table["id"], {
        "name": "Task Count",
        "type": "rollup",
        "options": {
            "recordLinkFieldId": resources_tasks_field["id"],
            "fieldIdInLinkedTable": tasks_table["primaryFieldId"],
            "referencedFieldIds": [tasks_table["primaryFieldId"]],
            "result": {
                "type": "count"
            }
        }
    })
    time.sleep(0.5)
    
    # 26. Resources: Utilization Status (formula)
    schema = get_base_schema()
    resources_table = find_table_by_name(schema, "Resources")
    resource_project_count = find_field_by_name(resources_table, "Project Count")
    resource_task_count = find_field_by_name(resources_table, "Task Count")
    
    create_field(resources_table["id"], {
        "name": "Utilization",
        "type": "formula",
        "options": {
            "formula": f"""IF(
    {{{resource_project_count['id']}}} + {{{resource_task_count['id']}}} = 0,
    '⚪ Idle',
    IF(
        {{{resource_project_count['id']}}} + {{{resource_task_count['id']}}} <= 3,
        '🟢 Low',
        IF(
            {{{resource_project_count['id']}}} + {{{resource_task_count['id']}}} <= 6,
            '🟡 Medium',
            '🔴 High'
        )
    )
)"""
        }
    })
    
    print("\n" + "=" * 60)
    print("✅ COMPLETE! Added 26 complex fields:")
    print("=" * 60)
    print("""
Projects (8 fields):
  - Duration (Days) - Formula
  - Budget per Day - Formula
  - Days Remaining - Formula
  - Total Tasks - Rollup
  - Completed Tasks - Rollup with condition
  - Progress % - Formula using rollups
  - Health Status - Complex conditional formula
  - Client Name (Lookup) - Lookup

Tasks (5 fields):
  - Days Overdue - Formula
  - Priority Score - Complex SWITCH formula
  - Has Dependencies - Formula
  - Project Budget (Lookup) - Lookup
  - Client (Lookup) - Nested lookup

Clients (3 fields):
  - Total Budget - Rollup sum
  - Active Projects - Rollup with condition
  - Avg Project Budget - Rollup average

Milestones (4 fields):
  - Days Until - Formula
  - Tasks Complete Count - Rollup with condition
  - Total Related Tasks - Rollup count
  - Achievement Status - Complex conditional formula

Contacts (3 fields):
  - Task Count - Rollup count
  - Active Tasks - Rollup with condition
  - Workload - SWITCH formula

Resources (3 fields):
  - Project Count - Rollup count
  - Task Count - Rollup count
  - Utilization - Complex conditional formula
""")
    
    print("\nThese fields create complex dependency chains perfect for testing:")
    print("  - Formulas that reference other formulas")
    print("  - Rollups with conditions")
    print("  - Lookups across multiple tables")
    print("  - Multi-level calculations (formulas using rollups)")


if __name__ == "__main__":
    add_complex_fields()
