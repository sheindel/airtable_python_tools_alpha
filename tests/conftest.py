"""Test fixtures and utilities shared across test suite."""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock PyScript before importing any web modules
sys.modules['pyscript'] = MagicMock()

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))


@pytest.fixture
def minimal_metadata():
    """Minimal valid Airtable metadata structure."""
    return {
        "tables": [
            {
                "id": "tbl1",
                "name": "Table 1",
                "fields": [
                    {
                        "id": "fld1",
                        "name": "Field 1",
                        "type": "singleLineText",
                    }
                ]
            }
        ]
    }


@pytest.fixture
def complex_metadata():
    """Complex metadata with multiple field types and dependencies."""
    return {
        "tables": [
            {
                "id": "tblTasks",
                "name": "Tasks",
                "fields": [
                    {
                        "id": "fldTaskName",
                        "name": "Task Name",
                        "type": "singleLineText",
                    },
                    {
                        "id": "fldHours",
                        "name": "Hours",
                        "type": "number",
                    },
                    {
                        "id": "fldRate",
                        "name": "Rate",
                        "type": "currency",
                    },
                    {
                        "id": "fldCost",
                        "name": "Cost",
                        "type": "formula",
                        "options": {
                            "formula": "{fldHours} * {fldRate}",
                            "referencedFieldIds": ["fldHours", "fldRate"],
                        },
                    },
                    {
                        "id": "fldProject",
                        "name": "Project",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tblProjects",
                            "inverseLinkFieldId": "fldProjectTasks",
                        },
                    },
                ]
            },
            {
                "id": "tblProjects",
                "name": "Projects",
                "fields": [
                    {
                        "id": "fldProjectName",
                        "name": "Project Name",
                        "type": "singleLineText",
                    },
                    {
                        "id": "fldProjectTasks",
                        "name": "Tasks",
                        "type": "multipleRecordLinks",
                        "options": {
                            "linkedTableId": "tblTasks",
                            "inverseLinkFieldId": "fldProject",
                        },
                    },
                    {
                        "id": "fldTotalCost",
                        "name": "Total Cost",
                        "type": "rollup",
                        "options": {
                            "fieldIdInLinkedTable": "fldCost",
                            "recordLinkFieldId": "fldProjectTasks",
                            "aggregationFunction": "sum",
                        },
                    },
                    {
                        "id": "fldTaskCount",
                        "name": "Task Count",
                        "type": "count",
                        "options": {
                            "recordLinkFieldId": "fldProjectTasks",
                        },
                    },
                ]
            }
        ]
    }


# ============================================================================
# Airtable Live Testing Configuration
# ============================================================================

def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--airtable-live",
        action="store_true",
        default=False,
        help="Run tests that require live Airtable API access"
    )


def pytest_collection_modifyitems(config, items):
    """Skip airtable_live tests unless --airtable-live is passed."""
    if config.getoption("--airtable-live"):
        return  # Run all tests
    
    skip_live = pytest.mark.skip(reason="need --airtable-live option to run")
    for item in items:
        if "airtable_live" in item.keywords:
            item.add_marker(skip_live)


@pytest.fixture
def airtable_config():
    """Get Airtable configuration from environment."""
    import os
    from helpers.airtable_api import get_api_key, get_base_id
    
    try:
        return {
            "api_key": get_api_key(),
            "base_id": get_base_id()
        }
    except ValueError as e:
        pytest.skip(f"Airtable credentials not configured: {e}")


@pytest.fixture
def airtable_schema(airtable_config):
    """Fetch and cache real Airtable schema."""
    from helpers.airtable_api import fetch_schema_cached
    
    try:
        return fetch_schema_cached(
            airtable_config["base_id"],
            airtable_config["api_key"]
        )
    except Exception as e:
        pytest.skip(f"Could not fetch Airtable schema: {e}")
