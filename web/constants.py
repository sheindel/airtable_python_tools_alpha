"""Shared constants for Airtable analysis tools.

This module contains constants used across multiple modules to ensure
consistency and avoid magic strings.
"""

import re

# Field Types
FIELD_TYPE_FORMULA = "formula"
FIELD_TYPE_ROLLUP = "rollup"
FIELD_TYPE_LOOKUP = "multipleLookupValues"
FIELD_TYPE_COUNT = "count"
FIELD_TYPE_RECORD_LINKS = "multipleRecordLinks"
FIELD_TYPE_TEXT = "singleLineText"
FIELD_TYPE_LONG_TEXT = "multilineText"
FIELD_TYPE_NUMBER = "number"
FIELD_TYPE_PERCENT = "percent"
FIELD_TYPE_CURRENCY = "currency"
FIELD_TYPE_CHECKBOX = "checkbox"
FIELD_TYPE_DATE = "date"
FIELD_TYPE_DATETIME = "dateTime"
FIELD_TYPE_SELECT = "singleSelect"
FIELD_TYPE_MULTI_SELECT = "multipleSelects"
FIELD_TYPE_AUTO_NUMBER = "autoNumber"

# Computed field types (have formulas/calculations)
COMPUTED_FIELD_TYPES = {
    FIELD_TYPE_FORMULA,
    FIELD_TYPE_ROLLUP,
    FIELD_TYPE_LOOKUP,
    FIELD_TYPE_COUNT,
}

# Basic field types (direct values, no dependencies)
BASIC_FIELD_TYPES = {
    FIELD_TYPE_TEXT,
    FIELD_TYPE_LONG_TEXT,
    FIELD_TYPE_NUMBER,
    FIELD_TYPE_PERCENT,
    FIELD_TYPE_CURRENCY,
    FIELD_TYPE_CHECKBOX,
    FIELD_TYPE_DATE,
    FIELD_TYPE_DATETIME,
    FIELD_TYPE_SELECT,
    FIELD_TYPE_MULTI_SELECT,
    FIELD_TYPE_AUTO_NUMBER,
}

# Relationship types for graph edges
RELATIONSHIP_FORMULA = "formula"
RELATIONSHIP_ROLLUP = "rollup"
RELATIONSHIP_ROLLUP_VIA = "rollup_via"
RELATIONSHIP_LOOKUP = "lookup"
RELATIONSHIP_COUNT = "count"
RELATIONSHIP_RECORD_LINK = "record_link"

# Mermaid diagram directions
MERMAID_DIRECTION_TOP_DOWN = "TD"
MERMAID_DIRECTION_LEFT_RIGHT = "LR"
MERMAID_DIRECTION_RIGHT_LEFT = "RL"
MERMAID_DIRECTION_BOTTOM_TOP = "BT"

MERMAID_DIRECTIONS = [
    MERMAID_DIRECTION_TOP_DOWN,
    MERMAID_DIRECTION_LEFT_RIGHT,
    MERMAID_DIRECTION_RIGHT_LEFT,
    MERMAID_DIRECTION_BOTTOM_TOP,
]

# Display modes for diagrams
DISPLAY_MODE_SIMPLE = "simple"
DISPLAY_MODE_DESCRIPTIONS = "descriptions"
DISPLAY_MODE_FORMULAS = "formulas"
DISPLAY_MODE_ALL = "all"

DISPLAY_MODES = [
    DISPLAY_MODE_SIMPLE,
    DISPLAY_MODE_DESCRIPTIONS,
    DISPLAY_MODE_FORMULAS,
    DISPLAY_MODE_ALL,
]

# Field ID pattern (matches Airtable field IDs: fld + 14 alphanumeric chars)
FIELD_ID_PATTERN = r"\{(fld[A-Za-z0-9]{14})\}"
FIELD_ID_REGEX = re.compile(FIELD_ID_PATTERN)

# Output formats for formula compression
OUTPUT_FORMAT_IDS = "ids"
OUTPUT_FORMAT_NAMES = "names"

OUTPUT_FORMATS = [
    OUTPUT_FORMAT_IDS,
    OUTPUT_FORMAT_NAMES,
]

# Error messages
ERROR_NO_METADATA = "No schema data available. Please load schema first."
ERROR_FIELD_NOT_FOUND = "Field not found in schema."
ERROR_INVALID_FIELD_TYPE = "Invalid field type for this operation."
ERROR_CIRCULAR_DEPENDENCY = "Circular dependency detected."

import re
