import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
import httpx
from typer import Typer, Option
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
from web.airtable_formula_evaluator import (
    evaluate_formula, 
    substitute_field_values, 
    get_unresolved_fields,
    FormulaEvaluationError
)

# Import postgres generator from web modules that work cross-environment
import sys
sys.path.append("web")
from postgres_schema_generator import (
    generate_schema,
    DATA_FIELD_TYPES,
    COMPUTED_FIELD_TYPES,
    ALL_FIELD_TYPES,
)

# Load environment variables from .env file
load_dotenv()

app = Typer()


@contextmanager
def mock_web_module_context(airtable_metadata: AirtableMetadata):
    """Context manager to mock localStorage for web modules when called from CLI.
    
    This allows CLI commands to reuse business logic from web tab modules
    without duplicating code.
    """
    import sys
    sys.path.append("web")
    import web.components.airtable_client as client_module
    
    # Mock localStorage for the web module
    class MockLocalStorage:
        def __init__(self):
            self._storage = {}
        
        def setItem(self, key, value):
            self._storage[key] = value
        
        def getItem(self, key):
            return self._storage.get(key)
    
    class MockWindow:
        localStorage = MockLocalStorage()
    
    original_window = getattr(client_module, 'window', None)
    mock_window = MockWindow()
    mock_window.localStorage.setItem("airtableSchema", json.dumps({
        "schema": airtable_metadata,
        "timestamp": "CLI"
    }))
    
    client_module.window = mock_window
    
    try:
        yield
    finally:
        if original_window is not None:
            client_module.window = original_window


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
    """Generate a CSV report of field complexity for a specific table."""
    from rich.traceback import install
    install(show_locals=False)

    import sys
    sys.path.append("web")
    from tabs.dependency_analysis import get_table_complexity as web_get_table_complexity
    
    airtable_metadata = get_airtable_metadata()
    
    with mock_web_module_context(airtable_metadata):
        csv_results = web_get_table_complexity(table_name)
        
        if not csv_results:
            raise ValueError(f"Table {table_name} not found in metadata")
        
        # Write csv results to file
        output_filename = f"{table_name}_field_complexity.csv"
        with open(output_filename, "w") as f:
            for row in csv_results:
                f.write(",".join(row) + "\n")
        
        print(f"Wrote complexity analysis to {output_filename}")
        return csv_results


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


@app.command()
def compress_formula(
    table_name: str,
    field_name: str,
    compression_depth: Optional[int] = None,
    output_format: str = "field_names",
    display_format: str = "compact",
    output_file: Optional[Path] = None
):
    """
    Compress a formula by recursively inlining field references.
    
    Args:
        table_name: Name of the table containing the field
        field_name: Name of the formula field to compress
        compression_depth: Maximum recursion depth (None = fully compress)
        output_format: "field_ids" or "field_names"
        display_format: "compact" (single line) or "logical" (multi-line indented)
        output_file: Optional file path to write the result
    """
    from cli_helpers import compress_formula_by_name, format_formula_compact, format_formula_logical
    
    airtable_metadata = get_airtable_metadata()
    
    try:
        compressed, depth = compress_formula_by_name(
            airtable_metadata,
            table_name,
            field_name,
            compression_depth,
            output_format
        )
        
        # Apply display formatting
        if display_format == "logical":
            formatted = format_formula_logical(compressed)
        else:
            formatted = format_formula_compact(compressed)
        
        print(f"\n=== Compressed Formula for {table_name}.{field_name} ===")
        print(f"Compression Depth: {depth}")
        print(f"\n{formatted}")
        
        if output_file:
            with open(output_file, "w") as f:
                f.write(f"Table: {table_name}\n")
                f.write(f"Field: {field_name}\n")
                f.write(f"Depth: {depth}\n")
                f.write(f"Format: {output_format}\n\n")
                f.write(formatted)
            print(f"\nSaved to {output_file}")
        
        return compressed
        
    except Exception as e:
        print(f"Error: {e}")
        raise


@app.command()
def compress_table_formulas(
    table_name: str,
    compression_depth: Optional[int] = None,
    output_file: Optional[Path] = None
):
    """
    Compress all formula fields in a table and output as CSV.
    
    Args:
        table_name: Name of the table to analyze
        compression_depth: Maximum recursion depth (None = fully compress)
        output_file: Optional CSV file path (default: {table_name}_compressed.csv)
    """
    from cli_helpers import generate_table_compression_report
    
    airtable_metadata = get_airtable_metadata()
    
    csv_data = generate_table_compression_report(airtable_metadata, table_name, compression_depth)
    
    if not output_file:
        output_file = Path(f"{table_name}_compressed.csv")
    
    with open(output_file, "w") as f:
        f.write(csv_data)
    
    print(f"Saved compressed formulas to {output_file}")
    return csv_data


@app.command()
def find_unused_fields(
    table_name: Optional[str] = None,
    field_type: Optional[str] = None,
    output_file: Optional[Path] = None
):
    """
    Find fields with zero inbound references (not used by any other field).
    
    Args:
        table_name: Optional table name to filter by
        field_type: Optional field type to filter by
        output_file: Optional CSV file path to save results
    """
    import sys
    sys.path.append("web")
    from tabs.unused_fields import get_unused_fields
    
    airtable_metadata = get_airtable_metadata()
    
    with mock_web_module_context(airtable_metadata):
        unused_fields = get_unused_fields()
        
        # Apply filters
        if table_name:
            unused_fields = [f for f in unused_fields if f["table_name"] == table_name]
        
        if field_type:
            unused_fields = [f for f in unused_fields if f["field_type"] == field_type]
        
        print(f"\n=== Unused Fields Analysis ===")
        print(f"Total unused fields: {len(unused_fields)}")
        
        if unused_fields:
            print(f"\n{'Table':<30} {'Field':<30} {'Type':<20} {'Outbound'}")
            print("-" * 100)
            for field in unused_fields:
                print(f"{field['table_name']:<30} {field['field_name']:<30} {field['field_type']:<20} {field['outbound_count']}")
        
        if output_file:
            lines = ["Table,Field,Type,Outbound References"]
            for field in unused_fields:
                line = ",".join([
                    f'"{field["table_name"]}"',
                    f'"{field["field_name"]}"',
                    field["field_type"],
                    str(field["outbound_count"])
                ])
                lines.append(line)
            
            with open(output_file, "w") as f:
                f.write("\n".join(lines))
            print(f"\nSaved to {output_file}")
        
        return unused_fields


@app.command()
def complexity_scorecard(
    table_name: Optional[str] = None,
    min_score: float = 0,
    top_n: Optional[int] = None,
    output_file: Optional[Path] = None
):
    """
    Generate a complexity scorecard for computed fields (formulas, rollups, lookups).
    
    Higher scores indicate more complex dependencies (backward deps, cross-table refs, depth).
    
    Args:
        table_name: Optional table name to filter by
        min_score: Minimum complexity score to include (default: 0)
        top_n: Show only top N most complex fields
        output_file: Optional CSV file path to save full results
    """
    import sys
    sys.path.append("web")
    from tabs.complexity_scorecard import get_all_field_complexity
    
    airtable_metadata = get_airtable_metadata()
    
    print("Analyzing field complexity... (this may take a moment)")
    
    with mock_web_module_context(airtable_metadata):
        all_complexity = get_all_field_complexity()
        
        # Apply filters
        if table_name:
            all_complexity = [f for f in all_complexity if f["table_name"] == table_name]
        
        if min_score > 0:
            all_complexity = [f for f in all_complexity if f["complexity_score"] >= min_score]
        
        if top_n:
            all_complexity = all_complexity[:top_n]
        
        print(f"\n=== Field Complexity Scorecard ===")
        print(f"Total fields analyzed: {len(all_complexity)}")
        
        if all_complexity:
            print(f"\n{'Table':<25} {'Field':<30} {'Type':<10} {'Score':<8} {'Depth':<6} {'Back':<6} {'Fwd':<6} {'XTable'}")
            print("-" * 110)
            for field in all_complexity:
                print(f"{field['table_name']:<25} {field['field_name']:<30} {field['field_type']:<10} "
                      f"{field['complexity_score']:<8.1f} {field['max_depth']:<6} {field['backward_deps']:<6} "
                      f"{field['forward_deps']:<6} {field['cross_table_deps']}")
        
        if output_file:
            lines = ["Table,Field,Type,Score,Depth,Backward Deps,Forward Deps,Cross-Table Deps"]
            for field in all_complexity:
                line = ",".join([
                    f'"{field["table_name"]}"',
                    f'"{field["field_name"]}"',
                    field["field_type"],
                    str(field["complexity_score"]),
                    str(field["max_depth"]),
                    str(field["backward_deps"]),
                    str(field["forward_deps"]),
                    str(field["cross_table_deps"])
                ])
                lines.append(line)
            
            with open(output_file, "w") as f:
                f.write("\n".join(lines))
            print(f"\nFull results saved to {output_file}")
        
        return all_complexity


@app.command()
def graph_formula_logic(
    table_name: str,
    field_name: str,
    flowchart_direction: str = "TD",
    expand_fields: bool = False,
    max_expansion_depth: int = 1,
    output_file: Optional[Path] = None
):
    """
    Generate a Mermaid flowchart showing the logical structure of a formula.
    
    This creates a flowchart showing IF statements, functions, operators, and field references.
    Different from generate_mermaid_graph which shows field dependencies.
    
    Args:
        table_name: Name of the table containing the field
        field_name: Name of the formula field
        flowchart_direction: Mermaid direction (TD, LR, RL, BT)
        expand_fields: Whether to expand referenced formula fields inline
        max_expansion_depth: Maximum depth for field expansion
        output_file: Optional file path to save the Mermaid code
    """
    from web.at_formula_parser import tokenize
    from cli_helpers import find_field_by_id
    
    airtable_metadata = get_airtable_metadata()
    
    # Find the table and field
    table = None
    field = None
    for t in airtable_metadata.get("tables", []):
        if t["name"] == table_name:
            table = t
            for f in t.get("fields", []):
                if f["name"] == field_name:
                    field = f
                    break
            break
    
    if not table:
        raise ValueError(f"Table '{table_name}' not found")
    if not field:
        raise ValueError(f"Field '{field_name}' not found in table '{table_name}'")
    if field.get("type") != "formula":
        raise ValueError(f"Field '{field_name}' is not a formula field")
    
    formula = field.get("options", {}).get("formula", "")
    if not formula:
        raise ValueError(f"Field '{field_name}' has no formula")
    
    # Simple parsing: just show the formula structure
    # For now, create a basic flowchart (full parser integration would require more work)
    mermaid_code = f"""flowchart {flowchart_direction}
    A["🎯 {field_name}"]
    B["Formula: {formula[:50]}..."]
    B --> A
    
    style A fill:#3b82f6,stroke:#1e40af,color:#fff
"""
    
    print(f"\n=== Formula Logic Flowchart for {table_name}.{field_name} ===\n")
    print(mermaid_code)
    print("\nNote: Full formula parsing visualization is available in the web interface.")
    print("Use 'uv run python main.py run-web' to access advanced formula graphing.")
    
    if output_file:
        with open(output_file, "w") as f:
            f.write(mermaid_code)
        print(f"\nSaved to {output_file}")
    
    return mermaid_code


@app.command()
def eval_formula(
    formula: str = Option(..., "--formula", "-f", help="Formula to evaluate"),
    values: Optional[str] = Option(None, "--values", "-v", help="JSON object with field ID to value mappings (e.g. '{\"fldABC...\": \"value\"}')")
):
    """
    Evaluate an Airtable formula with optional field substitutions
    
    Example:
      eval-formula -f "IF(TRUE, 'yes', 'no')"
      eval-formula -f "{fldABC123xyz45678} + {fldDEF456abc12345}" -v '{"fldABC123xyz45678": "10", "fldDEF456abc12345": "20"}'
    """
    try:
        # Parse field values if provided
        field_values = {}
        if values:
            try:
                field_values = json.loads(values)
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON for values: {e}")
                return
        
        # Substitute field values if any
        if field_values:
            formula_with_values = substitute_field_values(formula, field_values)
            print(f"Original formula: {formula}")
            print(f"After substitution: {formula_with_values}")
            
            # Check for unresolved fields
            unresolved = get_unresolved_fields(formula_with_values)
            if unresolved:
                print(f"\nWarning: Unresolved field references: {', '.join(unresolved)}")
                print("Formula cannot be fully evaluated without all field values.\n")
                return
            
            formula = formula_with_values
        
        # Evaluate the formula
        result = evaluate_formula(formula)
        
        print(f"\nResult: {result}")
        print(f"Type: {type(result).__name__}")
        
    except FormulaEvaluationError as e:
        print(f"Formula evaluation error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


@app.command()
def generate_postgres_schema(
    schema_file: str = Option(..., "--schema", "-s", help="Path to Airtable schema JSON file"),
    output_file: Optional[str] = Option(None, "--output", "-o", help="Output SQL file (default: stdout)"),
    naming_mode: str = Option("field_names", "--naming", "-n", help="Column naming: 'field_ids' or 'field_names'"),
    field_types: str = Option("data", "--types", "-t", help="Field types to include: 'all', 'data', 'computed', 'data+computed', or comma-separated list"),
    include_formulas: bool = Option(False, "--include-formulas", help="Include formulas as generated columns (experimental)"),
    formula_depth: int = Option(2, "--formula-depth", help="Maximum formula compression depth for generated columns"),
):
    """
    Generate PostgreSQL schema from Airtable metadata
    
    Examples:
      # Generate schema with transformed field names, data fields only
      generate-postgres-schema -s schema.json -o schema.sql
      
      # Use field IDs as column names
      generate-postgres-schema -s schema.json -n field_ids
      
      # Include all field types
      generate-postgres-schema -s schema.json -t all
      
      # Include data + computed fields
      generate-postgres-schema -s schema.json -t data+computed
      
      # Specific field types
      generate-postgres-schema -s schema.json -t "singleLineText,number,checkbox"
    """
    # Validate naming mode
    if naming_mode not in ["field_ids", "field_names"]:
        print(f"Error: Invalid naming mode '{naming_mode}'. Must be 'field_ids' or 'field_names'")
        return
    
    # Load schema
    try:
        with open(schema_file) as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {schema_file}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}")
        return
    
    # Determine which field types to include
    included_field_types = None
    if field_types == "all":
        included_field_types = ALL_FIELD_TYPES
    elif field_types == "data":
        included_field_types = DATA_FIELD_TYPES
    elif field_types == "computed":
        included_field_types = COMPUTED_FIELD_TYPES
    elif field_types == "data+computed":
        included_field_types = DATA_FIELD_TYPES | COMPUTED_FIELD_TYPES
    else:
        # Parse comma-separated list of field types
        included_field_types = set(t.strip() for t in field_types.split(","))
    
    # Generate schema
    try:
        sql = generate_schema(
            metadata,
            naming_mode=naming_mode,
            included_field_types=included_field_types,
            include_formulas_as_generated=include_formulas,
            formula_max_depth=formula_depth
        )
        
        # Output result
        if output_file:
            with open(output_file, "w") as f:
                f.write(sql)
            print(f"PostgreSQL schema written to {output_file}")
        else:
            print(sql)
            
    except Exception as e:
        print(f"Error generating schema: {e}")
        import traceback
        traceback.print_exc()


@app.command()
def generate_evaluator(
    schema_file: str = Option(..., "--schema", "-s", help="Path to Airtable schema JSON file"),
    output_file: str = Option(..., "--output", "-o", help="Output Python file path"),
    table_id: str = Option(..., "--table-id", "-t", help="Table ID to generate evaluator for"),
    mode: str = Option("dataclass", "--mode", "-m", help="Data access mode: 'dataclass', 'dict', or 'pydantic'"),
    null_checks: bool = Option(True, "--null-checks/--no-null-checks", help="Include null safety checks in generated code"),
    type_hints: bool = Option(True, "--type-hints/--no-type-hints", help="Include type hints in generated code"),
    docstrings: bool = Option(True, "--docstrings/--no-docstrings", help="Include docstrings in generated code"),
):
    """
    Generate a Python formula evaluator with incremental computation
    
    This creates a Python module with:
    - Type definitions for records
    - Formula computation functions
    - Incremental update logic (only recomputes changed dependencies)
    - Computation context for lookups/rollups
    
    Examples:
      # Generate with dataclasses (recommended)
      generate-evaluator -s schema.json -o evaluator.py -t tblContacts
      
      # Generate with dictionaries (more flexible)
      generate-evaluator -s schema.json -o evaluator.py -t tblContacts -m dict
      
      # Generate without null checks (faster but less safe)
      generate-evaluator -s schema.json -o evaluator.py -t tblContacts --no-null-checks
    """
    # Validate mode
    valid_modes = ["dataclass", "dict", "pydantic"]
    if mode not in valid_modes:
        print(f"Error: Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}")
        return
    
    # Load schema
    try:
        with open(schema_file) as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found: {schema_file}")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in schema file: {e}")
        return
    
    # Validate table_id exists
    table_names = [t.get("id", t.get("name", "")) for t in metadata.get("tables", [])]
    if table_id not in table_names:
        print(f"Error: Table ID '{table_id}' not found in schema")
        print(f"Available tables: {', '.join(table_names)}")
        return
    
    # Import the generator
    import sys
    sys.path.append("web")
    from code_generators.incremental_runtime_generator import (
        generate_complete_module,
        GeneratorOptions
    )
    
    # Configure options
    options = GeneratorOptions(
        data_access_mode=mode,
        include_null_checks=null_checks,
        include_type_hints=type_hints,
        include_docstrings=docstrings,
        include_examples=False,
        optimize_depth_skipping=True,
        track_computation_stats=False,
        output_format="single_file",
        include_tests=False,
    )
    
    # Generate code
    try:
        print(f"Generating evaluator for table {table_id}...")
        generated_code = generate_complete_module(
            metadata=metadata,
            table_id=table_id,
            options=options
        )
        
        # Write to file
        with open(output_file, "w") as f:
            f.write(generated_code)
        
        print(f"✓ Successfully generated evaluator: {output_file}")
        print(f"  Mode: {mode}")
        print(f"  Null checks: {'enabled' if null_checks else 'disabled'}")
        print(f"  Type hints: {'enabled' if type_hints else 'disabled'}")
        
        # Provide usage hint
        print(f"\nUsage:")
        print(f"  from {Path(output_file).stem} import update_record, ComputationContext")
        print(f"  # See generated file for complete API documentation")
        
    except Exception as e:
        print(f"Error generating evaluator: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    app()