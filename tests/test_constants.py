"""Test suite for constants module.

Tests that constants are properly defined and accessible.
"""
import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from constants import (
    COMPUTED_FIELD_TYPES,
    BASIC_FIELD_TYPES,
    MERMAID_DIRECTIONS,
    DISPLAY_MODES,
    FIELD_ID_REGEX,
)


def test_computed_field_types():
    """Test that computed field types set is defined correctly."""
    assert "formula" in COMPUTED_FIELD_TYPES
    assert "rollup" in COMPUTED_FIELD_TYPES
    assert "multipleLookupValues" in COMPUTED_FIELD_TYPES
    assert "count" in COMPUTED_FIELD_TYPES
    assert len(COMPUTED_FIELD_TYPES) == 4


def test_basic_field_types():
    """Test that basic field types are defined."""
    assert "singleLineText" in BASIC_FIELD_TYPES
    assert "number" in BASIC_FIELD_TYPES
    assert "checkbox" in BASIC_FIELD_TYPES
    # Basic fields should not include computed types
    assert "formula" not in BASIC_FIELD_TYPES


def test_mermaid_directions():
    """Test that all Mermaid directions are defined."""
    assert "TD" in MERMAID_DIRECTIONS
    assert "LR" in MERMAID_DIRECTIONS
    assert "RL" in MERMAID_DIRECTIONS
    assert "BT" in MERMAID_DIRECTIONS
    assert len(MERMAID_DIRECTIONS) == 4


def test_display_modes():
    """Test that all display modes are defined."""
    assert "simple" in DISPLAY_MODES
    assert "descriptions" in DISPLAY_MODES
    assert "formulas" in DISPLAY_MODES
    assert "all" in DISPLAY_MODES
    assert len(DISPLAY_MODES) == 4


def test_field_id_regex():
    """Test that field ID regex pattern works correctly."""
    # Valid field IDs
    assert FIELD_ID_REGEX.search("{fldAbCdEfGhIjKlMn}")
    assert FIELD_ID_REGEX.search("Some text {fld12345678901234} more text")
    
    # Invalid field IDs
    assert not FIELD_ID_REGEX.search("{fld123}")  # Too short
    assert not FIELD_ID_REGEX.search("{fldAbCdEfGhIjKlMnO}")  # Too long
    assert not FIELD_ID_REGEX.search("fldAbCdEfGhIjKlMn")  # No braces
    assert not FIELD_ID_REGEX.search("{recAbCdEfGhIjKlMn}")  # Wrong prefix


def test_no_overlap_computed_and_basic():
    """Test that computed and basic field types don't overlap."""
    overlap = COMPUTED_FIELD_TYPES & BASIC_FIELD_TYPES
    assert len(overlap) == 0, f"Overlap found: {overlap}"
