"""Script to add demo data to an Airtable base"""
import httpx
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Get credentials from .env
PAT = os.getenv("AIRTABLE_API_KEY")

def list_bases():
    """List all accessible bases"""
    url = "https://api.airtable.com/v0/meta/bases"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    bases = response.json()
    print("Available bases:")
    print(json.dumps(bases, indent=2))
    return bases


def get_base_schema(base_id: str):
    """Get the schema of a specific base"""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
    
    schema = response.json()
    print(f"\nBase {base_id} schema:")
    print(json.dumps(schema, indent=2))
    return schema


def create_records(base_id: str, table_id_or_name: str, records: list):
    """Create records in a table"""
    url = f"https://api.airtable.com/v0/{base_id}/{table_id_or_name}"
    
    # Airtable API accepts max 10 records per request
    for i in range(0, len(records), 10):
        batch = records[i:i+10]
        data = {"records": batch}
        
        response = httpx.post(
            url, 
            headers={
                "Authorization": f"Bearer {PAT}",
                "Content-Type": "application/json"
            },
            json=data
        )
        
        if response.status_code not in [200, 201]:
            print(f"Error creating records: {response.status_code}")
            print(response.text)
            return None
        
        print(f"Created {len(batch)} records")
    
    return True


def add_complex_demo_data(base_id: str, schema: dict):
    """Add complex demo data with interconnected relationships"""
    
    tables = schema.get("tables", [])
    
    if not tables:
        print("No tables found in schema")
        return
    
    print(f"\nFound {len(tables)} tables - adding demo data...")
    
    # Step 1: Add Clients (no dependencies)
    print("\n1. Adding Clients...")
    client_records = create_records(base_id, "Clients", [
        {"fields": {"Name": "Acme Corporation", "Status": "In progress", "Notes": "Major client - high priority"}},
        {"fields": {"Name": "TechStart Inc", "Status": "Done", "Notes": "Completed onboarding"}},
        {"fields": {"Name": "Global Logistics", "Status": "Todo", "Notes": "New prospect"}},
    ])
    
    # Step 2: Add Contacts (no dependencies)
    print("\n2. Adding Contacts...")
    contact_records = create_records(base_id, "Contacts", [
        {"fields": {"Name": "Sarah Johnson", "Email": "sarah@acme.com", "Cell": "+1-555-0101", "Notes": "CEO at Acme"}},
        {"fields": {"Name": "Michael Chen", "Email": "mchen@techstart.io", "Cell": "+1-555-0102", "Notes": "CTO - technical lead"}},
        {"fields": {"Name": "Emily Rodriguez", "Email": "emily.r@global-log.com", "Cell": "+1-555-0103", "Notes": "Project coordinator"}},
        {"fields": {"Name": "David Kim", "Email": "dkim@acme.com", "Cell": "+1-555-0104", "Notes": "Product Manager"}},
        {"fields": {"Name": "Lisa Wang", "Email": "lwang@techstart.io", "Cell": "+1-555-0105", "Notes": "Lead Developer"}},
    ])
    
    # Step 3: Add Resources (no dependencies)
    print("\n3. Adding Resources...")
    resource_records = create_records(base_id, "Resources", [
        {"fields": {"Resource Name": "Senior Developer Team", "Type": "Personnel", "Notes": "5 developers available"}},
        {"fields": {"Resource Name": "Cloud Infrastructure", "Type": "Equipment", "Notes": "AWS resources"}},
        {"fields": {"Resource Name": "Design Software Licenses", "Type": "Material", "Notes": "Adobe Creative Suite"}},
        {"fields": {"Resource Name": "Meeting Room A", "Type": "Equipment", "Notes": "Conference space for 12"}},
    ])
    
    # Step 4: Add Projects (links to Clients and Contacts)
    print("\n4. Adding Projects...")
    
    # Get record IDs from previous creations
    # For demo purposes, we'll need to fetch them
    url = f"https://api.airtable.com/v0/{base_id}/Clients"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    clients = response.json()["records"]
    
    url = f"https://api.airtable.com/v0/{base_id}/Contacts"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    contacts = response.json()["records"]
    
    url = f"https://api.airtable.com/v0/{base_id}/Resources"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    resources = response.json()["records"]
    
    project_records = create_records(base_id, "Projects", [
        {
            "fields": {
                "Project Name": "Website Redesign",
                "Description": "Complete overhaul of corporate website with modern UX",
                "Start Date": "2024-01-15",
                "End Date": "2024-06-30",
                "Budget": 150000,
                "Status": "Active",
                "Client": [clients[0]["id"]],  # Acme Corporation
                "Contacts": [contacts[0]["id"], contacts[3]["id"]],  # Sarah, David
                "Resources": [resources[0]["id"], resources[2]["id"]]  # Dev team, Design licenses
            }
        },
        {
            "fields": {
                "Project Name": "Mobile App Development",
                "Description": "iOS and Android app for customer engagement",
                "Start Date": "2024-02-01",
                "End Date": "2024-09-30",
                "Budget": 250000,
                "Status": "Active",
                "Client": [clients[1]["id"]],  # TechStart Inc
                "Contacts": [contacts[1]["id"], contacts[4]["id"]],  # Michael, Lisa
                "Resources": [resources[0]["id"], resources[1]["id"]]  # Dev team, Cloud
            }
        },
        {
            "fields": {
                "Project Name": "Supply Chain Optimization",
                "Description": "Streamline logistics and inventory management",
                "Start Date": "2024-03-01",
                "End Date": "2024-12-31",
                "Budget": 500000,
                "Status": "Planned",
                "Client": [clients[2]["id"]],  # Global Logistics
                "Contacts": [contacts[2]["id"]],  # Emily
                "Resources": [resources[1]["id"]]  # Cloud
            }
        }
    ])
    
    # Step 5: Add Milestones (links to Projects)
    print("\n5. Adding Milestones...")
    url = f"https://api.airtable.com/v0/{base_id}/Projects"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    projects = response.json()["records"]
    
    milestone_records = create_records(base_id, "Milestones", [
        {"fields": {"Milestone Name": "Design Phase Complete", "Target Date": "2024-03-15", "Project": [projects[0]["id"]], "Status": "On Track"}},
        {"fields": {"Milestone Name": "Backend API Ready", "Target Date": "2024-05-01", "Project": [projects[0]["id"]], "Status": "On Track"}},
        {"fields": {"Milestone Name": "Beta Release", "Target Date": "2024-06-15", "Project": [projects[1]["id"]], "Status": "Not Started"}},
        {"fields": {"Milestone Name": "User Testing Complete", "Target Date": "2024-08-01", "Project": [projects[1]["id"]], "Status": "Not Started"}},
        {"fields": {"Milestone Name": "Requirements Gathering", "Target Date": "2024-04-15", "Project": [projects[2]["id"]], "Status": "Not Started"}},
    ])
    
    # Step 6: Add Tasks (links to Projects, Contacts, Milestones)
    print("\n6. Adding Tasks...")
    url = f"https://api.airtable.com/v0/{base_id}/Milestones"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    milestones = response.json()["records"]
    
    task_records = create_records(base_id, "Tasks", [
        {"fields": {"Task Name": "Create wireframes", "Description": "Design initial wireframes for all pages", "Due Date": "2024-02-15", "Status": "Done", "Project": [projects[0]["id"]], "Related Contacts": [contacts[0]["id"]], "Resources": [resources[2]["id"]], "Milestones": [milestones[0]["id"]]}},
        {"fields": {"Task Name": "Develop homepage", "Description": "Build responsive homepage with hero section", "Due Date": "2024-03-30", "Status": "In Progress", "Project": [projects[0]["id"]], "Resources": [resources[0]["id"]], "Milestones": [milestones[1]["id"]]}},
        {"fields": {"Task Name": "Setup authentication", "Description": "Implement OAuth and JWT authentication", "Due Date": "2024-04-15", "Status": "Not Started", "Project": [projects[1]["id"]], "Related Contacts": [contacts[1]["id"]], "Resources": [resources[0]["id"], resources[1]["id"]], "Milestones": [milestones[2]["id"]]}},
        {"fields": {"Task Name": "Design app navigation", "Description": "Create intuitive navigation structure", "Due Date": "2024-03-20", "Status": "Not Started", "Project": [projects[1]["id"]], "Resources": [resources[2]["id"]], "Milestones": [milestones[2]["id"]]}},
        {"fields": {"Task Name": "Database schema design", "Description": "Design normalized database schema", "Due Date": "2024-03-01", "Status": "Blocked", "Project": [projects[1]["id"]], "Milestones": [milestones[2]["id"]]}},
        {"fields": {"Task Name": "Conduct stakeholder interviews", "Description": "Interview 10 key stakeholders", "Due Date": "2024-04-01", "Status": "Not Started", "Project": [projects[2]["id"]], "Related Contacts": [contacts[2]["id"]], "Milestones": [milestones[4]["id"]]}},
        {"fields": {"Task Name": "API integration", "Description": "Integrate with existing systems", "Due Date": "2024-05-15", "Status": "Not Started", "Project": [projects[0]["id"]], "Milestones": [milestones[1]["id"]]}},
    ])
    
    # Step 7: Add task dependencies (self-referencing)
    print("\n7. Adding Task Dependencies...")
    url = f"https://api.airtable.com/v0/{base_id}/Tasks"
    response = httpx.get(url, headers={"Authorization": f"Bearer {PAT}"})
    tasks = response.json()["records"]
    
    # Update tasks to add dependencies
    # Task "Develop homepage" depends on "Create wireframes"
    httpx.patch(
        f"https://api.airtable.com/v0/{base_id}/Tasks/{tasks[1]['id']}",
        headers={"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"},
        json={"fields": {"Dependency Tasks": [tasks[0]["id"]]}}
    )
    
    # Task "API integration" depends on "Develop homepage"
    httpx.patch(
        f"https://api.airtable.com/v0/{base_id}/Tasks/{tasks[6]['id']}",
        headers={"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"},
        json={"fields": {"Dependency Tasks": [tasks[1]["id"]]}}
    )
    
    # Task "Setup authentication" depends on "Database schema design"
    httpx.patch(
        f"https://api.airtable.com/v0/{base_id}/Tasks/{tasks[2]['id']}",
        headers={"Authorization": f"Bearer {PAT}", "Content-Type": "application/json"},
        json={"fields": {"Dependency Tasks": [tasks[4]["id"]]}}
    )
    
    # Step 8: Add Events (links to Projects, Clients, Contacts)
    print("\n8. Adding Events...")
    event_records = create_records(base_id, "Events", [
        {"fields": {"Event Name": "Project Kickoff - Website", "Date": "2024-01-20T10:00:00.000Z", "Location": "Acme HQ", "Event Type": "Kickoff", "Related Projects": [projects[0]["id"]], "Related Clients": [clients[0]["id"]], "Attendees": [contacts[0]["id"], contacts[3]["id"]]}},
        {"fields": {"Event Name": "Design Review Meeting", "Date": "2024-03-01T14:00:00.000Z", "Location": "Virtual - Zoom", "Event Type": "Review", "Related Projects": [projects[0]["id"]], "Attendees": [contacts[0]["id"]]}},
        {"fields": {"Event Name": "Mobile App Workshop", "Date": "2024-02-15T09:00:00.000Z", "Location": "TechStart Office", "Event Type": "Workshop", "Related Projects": [projects[1]["id"]], "Related Clients": [clients[1]["id"]], "Attendees": [contacts[1]["id"], contacts[4]["id"]]}},
        {"fields": {"Event Name": "Sprint Planning", "Date": "2024-03-25T10:00:00.000Z", "Location": "Virtual - Teams", "Event Type": "Meeting", "Related Projects": [projects[1]["id"]], "Attendees": [contacts[1]["id"], contacts[4]["id"]]}},
        {"fields": {"Event Name": "Discovery Session", "Date": "2024-03-15T13:00:00.000Z", "Location": "Global Logistics HQ", "Event Type": "Meeting", "Related Projects": [projects[2]["id"]], "Related Clients": [clients[2]["id"]], "Attendees": [contacts[2]["id"]]}},
    ])
    
    print("\n✅ Demo data creation complete!")
    print(f"Added:")
    print(f"  - 3 Clients")
    print(f"  - 5 Contacts")
    print(f"  - 4 Resources")
    print(f"  - 3 Projects")
    print(f"  - 5 Milestones")
    print(f"  - 7 Tasks (with dependencies)")
    print(f"  - 5 Events")
    print(f"\nThis creates a complex interconnected structure perfect for testing!")
    
    # Return info about the data
    return {
        "clients": len(clients),
        "contacts": len(contacts),
        "resources": len(resources),
        "projects": len(projects),
        "milestones": len(milestones),
        "tasks": len(tasks),
        "events": 5
    }
    

if __name__ == "__main__":
    print("Fetching available bases...")
    bases_result = list_bases()
    
    if bases_result and "bases" in bases_result:
        bases = bases_result["bases"]
        if bases:
            # Use the first base if available
            first_base = bases[0]
            base_id = first_base["id"]
            print(f"\nUsing base: {first_base['name']} ({base_id})")
            
            # Get schema
            schema = get_base_schema(base_id)
            
            if schema:
                add_complex_demo_data(base_id, schema)
