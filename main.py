import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Optional
import httpx
from typer import Typer
from dotenv import load_dotenv

from web.airtable_mermaid_generator import airtable_schema_to_mermaid, get_node_id
from web.at_metadata_graph import (
    get_reachable_nodes_advanced,
    get_reachable_nodes,
    get_relationship_dependency_complexity, 
    graph_to_mermaid, 
    metadata_to_graph
)
from web.at_types import AirtableMetadata, TableMetadata

# Load environment variables from .env file
load_dotenv()

app = Typer()


def get_version_string() -> str:
    """Get version from pyproject.toml with git commit SHA if available."""
    # Read version from pyproject.toml
    pyproject_path = Path(__file__).parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    version = pyproject.get("project", {}).get("version", "unknown")
    
    # Try to get git commit SHA
    try:
        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        # Check if there are uncommitted changes
        dirty = subprocess.call(
            ["git", "diff", "--quiet"],
            stderr=subprocess.DEVNULL
        ) != 0
        
        suffix = "-dirty" if dirty else ""
        return f"v{version}-{commit_sha}{suffix}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or not a git repo
        return f"v{version}"


@app.command()
def run_web():
    """Start web server with automatic version injection."""
    import http.server
    import socketserver
    from urllib.parse import unquote

    version_string = get_version_string()
    print(f"Starting server with version: {version_string}")

    class Server(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory="web", **kwargs)
        
        def end_headers(self):
            self.send_my_headers()
            http.server.SimpleHTTPRequestHandler.end_headers(self)

        def send_my_headers(self):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        
        def do_GET(self):
            # Inject version into index.html
            if self.path == "/" or self.path == "/index.html":
                try:
                    file_path = Path("web") / "index.html"
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Replace version placeholder
                    content = content.replace(
                        '<span id="app-version">v0.1.0</span>',
                        f'<span id="app-version">{version_string}</span>'
                    )
                    
                    # Send response
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(content.encode('utf-8'))))
                    self.send_my_headers()
                    self.end_headers()
                    self.wfile.write(content.encode('utf-8'))
                    return
                except Exception as e:
                    print(f"Error injecting version: {e}")
                    # Fall through to default handler
            
            # Default handling for all other files
            super().do_GET()

    PORT = 8008

    with socketserver.TCPServer(("", PORT), Server) as httpd:
        print(f"Running server at http://localhost:{PORT}")
        httpd.serve_forever()


AIRTABLE_APP_ID = os.getenv("AIRTABLE_APP_ID")
if not AIRTABLE_APP_ID:
    raise Exception("AIRTABLE_APP_ID not found in environment")

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
if not AIRTABLE_API_KEY:
    raise Exception("AIRTABLE_API_KEY not found in environment")


@app.command()
def get_airtable_metadata(
    table_name: Optional[str] = None, 
    verbose: bool = False,
    output_filename: Optional[Path] = None
):
    # curl "https://api.airtable.com/v0/meta/bases/{baseId}/tables" \
    # -H "Authorization: Bearer YOUR_TOKEN"

    url = f"https://api.airtable.com/v0/meta/bases/{AIRTABLE_APP_ID}/tables"
    response = httpx.get(url, headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"})
    data: AirtableMetadata = response.json()

    if output_filename:
        with open(output_filename, "w") as f:
            f.write(json.dumps(data, indent=4))    
        if verbose:
            print(f"Metadata written to {output_filename}")
    
    if table_name:
        for table in data["tables"]:
            if table["name"] == table_name:
                break
    
        if not table:
            raise Exception(f"Table {table_name} not found")
        
        if verbose:
            print(json.dumps(table))
            
        return table

    if verbose:
        print(json.dumps(data))

    return data



@app.command()
def airtable_formula_to_mermaid_graph(
    field_id: str,
    verbose: bool = False
):
    # First remove any unnecessary whitespace (whitespace not in strings)

    pass


airtable_function_names = [
    # Text Fucntions
    "ARRAYJOIN",
    "CONCATENATE",
    "ENCODE_URL_COMPONENT",
    "FIND",
    "LEFT",
    "LEN",
    "LOWER",
    "MID",
    "REPLACE",
    "REPT",
    "RIGHT",
    "SEARCH",
    "SUBSTITUTE",
    "T",
    "TRIM",
    "UPPER",

    # Logical Operators
    ">",
    "<",
    ">=",
    "<=",
    "=",
    "!=",

    # Logical Functions
    "AND",
    "BLANK",
    "ERROR",
    "FALSE",
    "IF",
    "ISERROR",
    "NOT",
    "OR",
    "SWITCH",
    "TRUE",
    "XOR",

    # Numeric Operators
    "+",
    "-",
    "*",
    "/",

    # Numeric Functions
    "ABS",
    "AVERAGE",
    "CEILING",
    "COUNT",
    "COUNTA",
    "COUNTALL",
    "EVEN",
    "EXP",
    "FLOOR",
    "INT",
    "LOG",
    "MAX",
    "MIN",
    "MOD",
    "ODD",
    "POWER",
    "ROUND",
    "ROUNDDOWN",
    "ROUNDUP",
    "SQRT",
    "SUM",
    "VALUE",

    # Date and Time Functions
    "CREATED_TIME",
    "DATEADD",
    "DATESTR",
    "DATETIME_DIFF",
    "DATETIME_FORMAT",
    "DATETIME_PARSE",
    "DAY",
    "HOUR",
    "IS_AFTER",
    "IS_BEFORE",
    "IS_SAME",
    "LAST_MODIFIED_TIME",
    "MINUTE",
    "MONTH",
    "NOW",
    "SECOND",
    "SET_LOCALE",
    "SET_TIMEZONE",
    "TIMESTR",
    "TONOW",
    "TODAY",
    "WEEKDAY",
    "WEEKNUM",
    "WORKDAY",
    "WORKDAY_DIFF",
    "YEAR",

    # Array Functions
    "ARRAYCOMPACT",
    "ARRAYFLATTEN",
    "ARRAYJOIN",
    "ARRAYUNIQUE",
    "ARRAYSLICE",

    # AirTable Unique Record Functions
    "CREATED_TIME",
    "LAST_MODIFIED_TIME",
    "RECORD_ID",

    # Regex Functions
    "REGEX_MATCH",
    "REGEX_EXTRACT",
    "REGEX_REPLACE",
]


def process_function_text(text: str):
    import re
    matcher = re.compile(r"(\w*)\((.*)\)")
    # extract all dependencies

    matches = matcher.findall(text)
    new_node: FunctionNode = None
    last_node: FunctionNode = None
    while True:
        if not matches:
            break
        func_name, args = matches[0]
        # if last_node:
            
class FunctionNode:
    def __init__(self, name: str, inner_text: str):
        self.name = name
        self.inner_text = inner_text
        self.arguments: list[FunctionNode] = []
    
    def add_argument(self, arguments):
        self.arguments.append(arguments)
    

    


@app.command()
def test_function_graph_generation():
    import re
    f = "IF({fldIcvYvgV4dEWnba}=BLANK(),{fldrxOEmukdbxien8},{fldIcvYvgV4dEWnba})"

    # (\w*)\((.*)\)
    matcher = re.compile(r"(\w*)\((.*)\)")
    # extract all dependencies

    matches = matcher.findall(f)
    while True:
        if not matches:
            break
        func_name, args = matches[0]
        print(func_name, args)
        matches = matcher.findall(args)


def table_ids_to_names(
    table_ids: list[str],
    metadata: AirtableMetadata
) -> list[str]:
    result: list[str] = []
    for table_id in table_ids:
        for table in metadata["tables"]:
            if table["id"] == table_id:
                result.append(table["name"])
                break
    return result


@app.command()
def formula_walker(
    table_name: str = '',
    field_name: str = ''
):
    airtable_metadata = get_airtable_metadata()
    G = metadata_to_graph(airtable_metadata)



@app.command()
def get_table_complexity(
    table_name: str
):
    from rich.traceback import install
    install(show_locals=False)

    airtable_metadata = get_airtable_metadata()
    G = metadata_to_graph(airtable_metadata)
    for table in airtable_metadata["tables"]:
        if table["name"] == table_name:
            break
    if not table:
        raise ValueError(f"Table {table_name} not found in metadata")

    csv_results: list[list[str]] = []  
    for field in table["fields"]:
        field_type = field.get("type")
        if field_type not in ["formula", "rollup", "lookup"]:
            continue
        result = get_relationship_dependency_complexity(G, field["id"])
        table_names = table_ids_to_names(
            list(result["tables_dependencies"].keys()),
            airtable_metadata
        )
        csv_results.append(
            [field["name"], field_type, ";".join(table_names)]
        )

    # write csv results to file
    output_filename = f"{table_name}_field_complexity.csv"
    with open(output_filename, "w") as f:
        f.write("Field Name,Field Type,Dependent Tables\n")
        for row in csv_results:
            f.write(",".join(row) + "\n")
    return result


@app.command()
def generate_table_dependency_graph(
    table_name: str,
    flowchart_type: str = "TD",
):
    """
    Generate a Mermaid graph showing table-level dependencies.
    
    For a given table, shows all tables it connects to via:
    - Linked record fields
    - Lookup fields
    - Rollup fields
    - Formula fields that reference fields in other tables
    
    Edges are labeled with connection type and count (e.g., "Rollup (3)").
    """
    from rich.traceback import install
    install(show_locals=False)
    from collections import defaultdict

    airtable_metadata = get_airtable_metadata()
    G = metadata_to_graph(airtable_metadata)
    
    # Find the table
    source_table = None
    for table in airtable_metadata["tables"]:
        if table["name"] == table_name:
            source_table = table
            break
    
    if not source_table:
        raise ValueError(f"Table {table_name} not found in metadata")
    
    source_table_id = source_table["id"]
    
    # Track connections by (source_table, target_table, connection_type)
    connections = defaultdict(int)
    
    # Analyze each field in the source table
    for field in source_table["fields"]:
        field_id = field["id"]
        field_type = field.get("type")
        
        if field_type == "multipleRecordLinks":
            # Direct link to another table
            target_table_id = field["options"]["linkedTableId"]
            connections[(source_table_id, target_table_id, "Linked Records")] += 1
            
        elif field_type == "multipleLookupValues":
            # Lookup references a field in a linked table
            record_link_id = field["options"]["recordLinkFieldId"]
            # Get the target table from the record link field
            if record_link_id in G.nodes:
                record_link_metadata = G.nodes[record_link_id].get("metadata", {})
                if record_link_metadata and record_link_metadata.get("type") == "multipleRecordLinks":
                    target_table_id = record_link_metadata["options"]["linkedTableId"]
                    connections[(source_table_id, target_table_id, "Lookup")] += 1
            
        elif field_type == "rollup":
            # Rollup references a field in a linked table
            record_link_id = field["options"]["recordLinkFieldId"]
            # Get the target table from the record link field
            if record_link_id in G.nodes:
                record_link_metadata = G.nodes[record_link_id].get("metadata", {})
                if record_link_metadata and record_link_metadata.get("type") == "multipleRecordLinks":
                    target_table_id = record_link_metadata["options"]["linkedTableId"]
                    connections[(source_table_id, target_table_id, "Rollup")] += 1
        
        elif field_type == "formula":
            # Check if formula references fields in other tables
            referenced_field_ids = field["options"].get("referencedFieldIds", [])
            target_tables = set()
            for ref_field_id in referenced_field_ids:
                if ref_field_id in G.nodes:
                    ref_table_id = G.nodes[ref_field_id].get("table_id")
                    if ref_table_id and ref_table_id != source_table_id:
                        target_tables.add(ref_table_id)
            
            for target_table_id in target_tables:
                connections[(source_table_id, target_table_id, "Formula")] += 1
    
    # Generate Mermaid diagram
    mermaid_lines = [f"flowchart {flowchart_type}"]
    
    # Add nodes for all involved tables
    tables_in_graph = {source_table_id}
    for (src, tgt, _), _ in connections.items():
        tables_in_graph.add(src)
        tables_in_graph.add(tgt)
    
    for table_id in tables_in_graph:
        table_name_display = G.nodes[table_id].get("name", table_id)
        # Highlight the source table differently
        if table_id == source_table_id:
            mermaid_lines.append(f'    {table_id}["{table_name_display}"]')
            mermaid_lines.append(f'    style {table_id} fill:#3b82f6,stroke:#1e40af,color:#fff')
        else:
            mermaid_lines.append(f'    {table_id}["{table_name_display}"]')
    
    # Add edges with labels
    for (src, tgt, conn_type), count in sorted(connections.items()):
        label = f"{conn_type} ({count})" if count > 1 else conn_type
        mermaid_lines.append(f'    {src} -->|{label}| {tgt}')
    
    mermaid_diagram = "\n".join(mermaid_lines)
    print(mermaid_diagram)
    return mermaid_diagram


@app.command()
def get_field_complexity(
    table_name: str,
    field_name: str
):
    airtable_metadata = get_airtable_metadata()
    field_id = get_node_id(
        airtable_metadata,
        field_name, 
        table_name, 
    )

    G = metadata_to_graph(airtable_metadata)

    result = get_relationship_dependency_complexity(G, field_id)

    print(result)

    return result


@app.command()
def generate_mermaid_graph(
    table_name: str = "",
    field_name: str = "",
    flowchart_type: str = "TD",
    full_field_description: bool = False,
    verbose: bool = False,
    v2: bool = False,
    direction: str = "both",
    max_depth: int = 3
):
    print("Generating Mermaid Graph")

    from rich.traceback import install
    install(show_locals=False)

    airtable_metadata = get_airtable_metadata()

    if v2:
        # Create graph and get subgraph
        G = metadata_to_graph(airtable_metadata)

        field_id = get_node_id(
            airtable_metadata,
            field_name, 
            table_name, 
        )

        subgraph = get_reachable_nodes(G, field_id, direction=direction)

        # Convert to Mermaid
        mermaid_diagram = graph_to_mermaid(subgraph, direction=flowchart_type, full_description=full_field_description)
        if verbose:
            print(mermaid_diagram)
        return mermaid_diagram
    
    mermaid_text = airtable_schema_to_mermaid(
        airtable_metadata,
        field=field_name, 
        table_name=table_name, 
        direction=flowchart_type,
        full_field_description=full_field_description,
        verbose=verbose
    )
    
    return mermaid_text


if __name__ == "__main__":
    app()