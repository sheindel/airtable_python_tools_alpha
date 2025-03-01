import json
import os
from pathlib import Path
from typing import Optional
import httpx
from typer import Typer

from web.airtable_mermaid_generator import airtable_schema_to_mermaid
from web.at_types import AirtableMetadata

app = Typer()


@app.command()
def run_web():
    # Start web server in the web/ directory
    import http.server
    import socketserver

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
    pass


@app.command()
def generate_mermaid_graph(
    table_name: str = "",
    field_name: str = "",
    flowchart_type: str = "TD",
    verbose: bool = False
):
    print("Generating Mermaid Graph")

    from rich.traceback import install
    install(show_locals=False)

    airtable_metadata = get_airtable_metadata(verbose=verbose)

    mermaid_text = airtable_schema_to_mermaid(
        airtable_metadata,
        field=field_name, 
        table_name=table_name, 
        direction=flowchart_type,
        verbose=verbose
    )
    
    return mermaid_text


if __name__ == "__main__":
    app()