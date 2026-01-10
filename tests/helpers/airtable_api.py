"""
Airtable API utilities for parity testing.

Provides functions for:
- Fetching schemas with caching
- Selecting random records
- Retrieving full record data
"""
import json
import os
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


# Configuration
CACHE_DIR = Path(".cache/airtable_schemas")
CACHE_EXPIRY = timedelta(hours=24)
API_BASE_URL = "https://api.airtable.com/v0"


class AirtableAPIError(Exception):
    """Raised when Airtable API request fails."""
    pass


def get_api_key() -> str:
    """Get Airtable API key from environment."""
    api_key = os.getenv("AIRTABLE_API_KEY")
    if not api_key:
        raise ValueError("AIRTABLE_API_KEY environment variable not set")
    return api_key


def get_base_id() -> str:
    """Get Airtable base ID from environment."""
    base_id = os.getenv("AIRTABLE_BASE_ID")
    if not base_id:
        raise ValueError("AIRTABLE_BASE_ID environment variable not set")
    return base_id


def fetch_schema_from_api(base_id: str, api_key: str) -> dict:
    """
    Fetch schema from Airtable API.
    
    Args:
        base_id: Airtable base ID (e.g., "appXXXXXXXXXXXXXX")
        api_key: Airtable API key
    
    Returns:
        Schema metadata as dict
    
    Raises:
        AirtableAPIError: If API request fails
    """
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise AirtableAPIError(f"Failed to fetch schema: {e}") from e


def fetch_schema_cached(base_id: str, api_key: str, force_refresh: bool = False) -> dict:
    """
    Fetch schema from Airtable with local file caching.
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        force_refresh: If True, ignore cache and fetch fresh schema
    
    Returns:
        Schema metadata as dict
    """
    cache_file = CACHE_DIR / f"{base_id}.json"
    
    # Check if cache exists and is fresh
    if not force_refresh and cache_file.exists():
        cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        if cache_age < CACHE_EXPIRY:
            print(f"Using cached schema (age: {cache_age})")
            return json.loads(cache_file.read_text())
    
    # Fetch fresh schema
    print("Fetching fresh schema from Airtable API...")
    schema = fetch_schema_from_api(base_id, api_key)
    
    # Save to cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(schema, indent=2))
    print(f"Schema cached to {cache_file}")
    
    return schema


def get_table_id_by_name(schema: dict, table_name: str) -> str:
    """
    Get table ID from table name.
    
    Args:
        schema: Airtable schema metadata
        table_name: Name of the table
    
    Returns:
        Table ID (e.g., "tblXXXXXXXXXXXXXX")
    
    Raises:
        ValueError: If table not found
    """
    for table in schema.get("tables", []):
        if table["name"] == table_name:
            return table["id"]
    raise ValueError(f"Table '{table_name}' not found in schema")


def fetch_records(
    base_id: str,
    api_key: str,
    table_name: str,
    max_records: int = 100,
    offset: Optional[str] = None
) -> dict:
    """
    Fetch records from a table.
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        table_name: Name of the table
        max_records: Maximum number of records to fetch
        offset: Pagination offset from previous request
    
    Returns:
        Response dict with 'records' and optional 'offset' keys
    
    Raises:
        AirtableAPIError: If API request fails
    """
    url = f"{API_BASE_URL}/{base_id}/{table_name}"
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"maxRecords": max_records}
    
    if offset:
        params["offset"] = offset
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise AirtableAPIError(f"Failed to fetch records: {e}") from e


def fetch_record(base_id: str, api_key: str, table_name: str, record_id: str) -> dict:
    """
    Fetch a single record by ID.
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        table_name: Name of the table
        record_id: Record ID (e.g., "recXXXXXXXXXXXXXX")
    
    Returns:
        Full record data including all fields
    
    Raises:
        AirtableAPIError: If API request fails
    """
    url = f"{API_BASE_URL}/{base_id}/{table_name}/{record_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        with httpx.Client() as client:
            response = client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        raise AirtableAPIError(f"Failed to fetch record {record_id}: {e}") from e


def get_random_record_id(
    base_id: str,
    api_key: str,
    table_name: str,
    max_attempts: int = 3
) -> str:
    """
    Get a random record ID using a heuristic approach.
    
    Strategy:
    1. Fetch first page of records (up to 100)
    2. Pick a random record from the results
    3. Retry if no records found
    
    Args:
        base_id: Airtable base ID
        api_key: Airtable API key
        table_name: Name of the table
        max_attempts: Maximum number of fetch attempts
    
    Returns:
        Random record ID
    
    Raises:
        ValueError: If no records found after max_attempts
        AirtableAPIError: If API request fails
    """
    for attempt in range(max_attempts):
        try:
            response = fetch_records(base_id, api_key, table_name, max_records=100)
            records = response.get("records", [])
            
            if records:
                random_record = random.choice(records)
                return random_record["id"]
            
            # No records on this page, maybe there's more?
            if "offset" not in response:
                # No more pages
                break
                
        except AirtableAPIError as e:
            if attempt == max_attempts - 1:
                raise
            # Wait before retry
            time.sleep(1)
    
    raise ValueError(f"No records found in table '{table_name}' after {max_attempts} attempts")


def extract_raw_fields(full_record: dict, schema: dict, table_id: str) -> dict:
    """
    Extract only raw (non-computed) fields from a record.
    
    Computed field types: formula, rollup, multipleLookupValues, count
    
    Args:
        full_record: Full record from Airtable API
        schema: Airtable metadata schema
        table_id: Table ID to find field definitions
    
    Returns:
        Dict with only raw field values (excludes computed fields).
        All raw fields are included, even if not present in the record (set to None).
    """
    computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
    
    # Find table in schema
    table = None
    for t in schema.get("tables", []):
        if t["id"] == table_id:
            table = t
            break
    
    if not table:
        raise ValueError(f"Table {table_id} not found in schema")
    
    # Build set of computed field names and collect all raw field names
    computed_field_names = set()
    raw_field_names = set()
    for field in table.get("fields", []):
        if field["type"] in computed_types:
            computed_field_names.add(field["name"])
        else:
            raw_field_names.add(field["name"])
    
    # Initialize all raw fields with None
    raw_fields = {"id": full_record["id"]}  # Always include ID
    for field_name in raw_field_names:
        raw_fields[field_name] = None
    
    # Fill in actual values from record
    for field_name, value in full_record.get("fields", {}).items():
        if field_name not in computed_field_names:
            raw_fields[field_name] = value
    
    return raw_fields


def get_computed_field_names(schema: dict, table_id: str) -> List[str]:
    """
    Get list of computed field names for a table.
    
    Args:
        schema: Airtable metadata schema
        table_id: Table ID
    
    Returns:
        List of computed field names
    """
    computed_types = {"formula", "rollup", "multipleLookupValues", "count"}
    
    # Find table in schema
    table = None
    for t in schema.get("tables", []):
        if t["id"] == table_id:
            table = t
            break
    
    if not table:
        raise ValueError(f"Table {table_id} not found in schema")
    
    # Extract computed field names
    computed_fields = []
    for field in table.get("fields", []):
        if field["type"] in computed_types:
            computed_fields.append(field["name"])
    
    return computed_fields


def to_snake_case(name: str) -> str:
    """
    Convert a field name to snake_case for Python identifiers.
    
    Matches the conversion used by the code generator.
    
    Args:
        name: Original field name (e.g., "First Name")
    
    Returns:
        Snake case version (e.g., "first_name")
    """
    import re
    # Replace spaces and special chars with underscores
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    # Convert camelCase to snake_case
    name = re.sub(r'([a-z])([A-Z])', r'\1_\2', name)
    # Convert to lowercase
    name = name.lower()
    # Remove duplicate underscores
    name = re.sub(r'_+', '_', name)
    # Remove leading/trailing underscores
    name = name.strip('_')
    return name


def convert_record_to_snake_case(record: dict) -> dict:
    """
    Convert all field names in a record to snake_case.
    
    This is needed because generated evaluator code uses snake_case
    field names, but Airtable records use the original field names.
    
    Args:
        record: Record dict with original Airtable field names
    
    Returns:
        New dict with snake_case field names
    """
    converted = {}
    for key, value in record.items():
        snake_key = to_snake_case(key)
        converted[snake_key] = value
    return converted
