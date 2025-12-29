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
