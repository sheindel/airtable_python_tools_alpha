"""Tests for error handling utilities

Tests the standardized error handling patterns used across web components.
These are critical for user experience and debugging.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from components.error_handling import (
    AnalysisError,
    MetadataError,
    FieldNotFoundError,
    InvalidFieldTypeError,
    CircularDependencyError,
    validate_metadata,
    find_field_by_id,
    validate_field_type,
    display_error_in_element,
    handle_tab_error,
)
from constants import ERROR_NO_METADATA, ERROR_FIELD_NOT_FOUND, ERROR_INVALID_FIELD_TYPE


class TestExceptionHierarchy:
    """Test custom exception classes"""
    
    def test_analysis_error_is_exception(self):
        """AnalysisError should be an Exception subclass"""
        error = AnalysisError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
    
    def test_metadata_error_is_analysis_error(self):
        """MetadataError should inherit from AnalysisError"""
        error = MetadataError("no metadata")
        assert isinstance(error, AnalysisError)
        assert isinstance(error, Exception)
    
    def test_field_not_found_error_is_analysis_error(self):
        """FieldNotFoundError should inherit from AnalysisError"""
        error = FieldNotFoundError("field missing")
        assert isinstance(error, AnalysisError)
    
    def test_invalid_field_type_error_is_analysis_error(self):
        """InvalidFieldTypeError should inherit from AnalysisError"""
        error = InvalidFieldTypeError("wrong type")
        assert isinstance(error, AnalysisError)
    
    def test_circular_dependency_error_is_analysis_error(self):
        """CircularDependencyError should inherit from AnalysisError"""
        error = CircularDependencyError("circular reference")
        assert isinstance(error, AnalysisError)


class TestValidateMetadata:
    """Test metadata validation"""
    
    def test_valid_metadata_returns_itself(self):
        """Valid metadata should be returned unchanged"""
        metadata = {"tables": [{"id": "tbl1", "name": "Table", "fields": []}]}
        result = validate_metadata(metadata)
        assert result == metadata
    
    def test_none_metadata_raises_error(self):
        """None metadata should raise MetadataError"""
        with pytest.raises(MetadataError, match=ERROR_NO_METADATA):
            validate_metadata(None)
    
    def test_non_dict_metadata_raises_error(self):
        """Non-dict metadata should raise MetadataError"""
        with pytest.raises(MetadataError, match="not a valid dictionary"):
            validate_metadata("not a dict")
    
    def test_metadata_without_tables_raises_error(self):
        """Metadata without 'tables' key should raise error"""
        with pytest.raises(MetadataError, match="missing 'tables' key"):
            validate_metadata({"some_other_key": []})
    
    def test_empty_tables_is_valid(self):
        """Metadata with empty tables array is valid"""
        metadata = {"tables": []}
        result = validate_metadata(metadata)
        assert result == metadata


class TestFindFieldById:
    """Test field lookup by ID"""
    
    def test_finds_existing_field(self):
        """Should find and return field and its table"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table1",
                    "fields": [
                        {"id": "fld1", "name": "Field1", "type": "text"},
                        {"id": "fld2", "name": "Field2", "type": "number"}
                    ]
                }
            ]
        }
        
        table, field = find_field_by_id(metadata, "fld2")
        
        assert table["id"] == "tbl1"
        assert field["id"] == "fld2"
        assert field["name"] == "Field2"
    
    def test_finds_field_in_second_table(self):
        """Should search across multiple tables"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table1",
                    "fields": [{"id": "fld1", "name": "Field1"}]
                },
                {
                    "id": "tbl2",
                    "name": "Table2",
                    "fields": [{"id": "fld2", "name": "Field2"}]
                }
            ]
        }
        
        table, field = find_field_by_id(metadata, "fld2")
        
        assert table["id"] == "tbl2"
        assert field["id"] == "fld2"
    
    def test_raises_error_for_nonexistent_field(self):
        """Should raise FieldNotFoundError if field doesn't exist"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table1",
                    "fields": [{"id": "fld1", "name": "Field1"}]
                }
            ]
        }
        
        with pytest.raises(FieldNotFoundError, match=ERROR_FIELD_NOT_FOUND):
            find_field_by_id(metadata, "fldNonExistent")
    
    def test_includes_field_id_in_error_message(self):
        """Error message should include the field ID"""
        metadata = {"tables": []}
        
        with pytest.raises(FieldNotFoundError, match="fldMissing"):
            find_field_by_id(metadata, "fldMissing")
    
    def test_handles_empty_tables(self):
        """Should handle metadata with no tables gracefully"""
        metadata = {"tables": []}
        
        with pytest.raises(FieldNotFoundError):
            find_field_by_id(metadata, "fld1")


class TestValidateFieldType:
    """Test field type validation"""
    
    def test_valid_single_type_passes(self):
        """Should not raise error for valid type"""
        field = {"id": "fld1", "name": "Test", "type": "formula"}
        # Should not raise
        validate_field_type(field, ["formula"], "compression")
    
    def test_valid_multiple_types_passes(self):
        """Should accept field if type matches any in list"""
        field = {"id": "fld1", "name": "Test", "type": "rollup"}
        # Should not raise
        validate_field_type(field, ["formula", "rollup", "lookup"], "analysis")
    
    def test_invalid_type_raises_error(self):
        """Should raise InvalidFieldTypeError for wrong type"""
        field = {"id": "fld1", "name": "Test", "type": "text"}
        
        with pytest.raises(InvalidFieldTypeError, match=ERROR_INVALID_FIELD_TYPE):
            validate_field_type(field, ["formula"], "compression")
    
    def test_error_includes_field_name(self):
        """Error message should include field name"""
        field = {"id": "fld1", "name": "MyField", "type": "text"}
        
        with pytest.raises(InvalidFieldTypeError, match="MyField"):
            validate_field_type(field, ["formula"], "compression")
    
    def test_error_includes_actual_type(self):
        """Error message should include actual field type"""
        field = {"id": "fld1", "name": "Test", "type": "checkbox"}
        
        with pytest.raises(InvalidFieldTypeError, match="checkbox"):
            validate_field_type(field, ["formula"], "compression")
    
    def test_error_includes_expected_types(self):
        """Error message should list expected types"""
        field = {"id": "fld1", "name": "Test", "type": "text"}
        
        with pytest.raises(InvalidFieldTypeError, match="formula, rollup"):
            validate_field_type(field, ["formula", "rollup"], "operation")
    
    def test_error_includes_operation_context(self):
        """Error message should include operation being attempted"""
        field = {"id": "fld1", "name": "Test", "type": "text"}
        
        with pytest.raises(InvalidFieldTypeError, match="my_operation"):
            validate_field_type(field, ["formula"], "my_operation")


class TestDisplayErrorInElement:
    """Test error display in DOM"""
    
    def test_displays_error_message(self):
        """Should set innerHTML with error message"""
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            display_error_in_element("error-div", "Something went wrong", "error")
            
            assert mock_document.getElementById.called
            assert "Something went wrong" in mock_element.innerHTML
    
    def test_uses_error_styling_by_default(self):
        """Should use red error styling for error type"""
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            display_error_in_element("error-div", "Error occurred", "error")
            
            html = mock_element.innerHTML
            assert "bg-red-50" in html
            assert "dark:bg-red-900" in html
            assert "❌" in html
    
    def test_uses_warning_styling(self):
        """Should use yellow styling for warning type"""
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            display_error_in_element("warn-div", "Be careful", "warning")
            
            html = mock_element.innerHTML
            assert "bg-yellow-50" in html
            assert "dark:bg-yellow-900" in html
            assert "⚠️" in html
    
    def test_uses_info_styling(self):
        """Should use blue styling for info type"""
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            display_error_in_element("info-div", "FYI", "info")
            
            html = mock_element.innerHTML
            assert "bg-blue-50" in html
            assert "dark:bg-blue-900" in html
            assert "ℹ️" in html
    
    def test_handles_missing_element_gracefully(self):
        """Should not crash if element doesn't exist"""
        mock_document = MagicMock()
        mock_document.getElementById.return_value = None
        
        with patch('components.error_handling.document', mock_document):
            # Should not raise
            display_error_in_element("nonexistent", "Error", "error")


class TestHandleTabError:
    """Test tab error handler"""
    
    def test_displays_error_when_element_provided(self):
        """Should call display_error_in_element when element ID provided"""
        error = ValueError("Test error")
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            handle_tab_error(error, "testing", "output-div")
            
            # Should have displayed the error
            assert mock_element.innerHTML is not None
            assert "testing" in mock_element.innerHTML
    
    def test_uses_custom_user_message(self):
        """Should use provided user message"""
        error = ValueError("Internal error")
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            handle_tab_error(
                error,
                "operation",
                "output-div",
                user_message="Custom message for user"
            )
            
            assert "Custom message for user" in mock_element.innerHTML
    
    def test_generates_default_message_from_context(self):
        """Should generate message from context if no custom message"""
        error = ValueError("Error")
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        with patch('components.error_handling.document', mock_document):
            handle_tab_error(error, "generating diagram", "output-div")
            
            html = mock_element.innerHTML
            assert "generating diagram" in html
    
    def test_works_without_display_element(self):
        """Should still log error if no display element provided"""
        error = ValueError("Error")
        # Should not raise even without element
        handle_tab_error(error, "operation", display_element_id=None)


class TestRealWorldScenarios:
    """Test realistic usage scenarios"""
    
    def test_validation_chain_for_compression(self):
        """Test typical validation chain for formula compression"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {
                            "id": "fld1",
                            "name": "MyFormula",
                            "type": "formula",
                            "options": {"formula": "1+1"}
                        }
                    ]
                }
            ]
        }
        
        # Validate metadata
        validated = validate_metadata(metadata)
        assert validated is not None
        
        # Find field
        table, field = find_field_by_id(validated, "fld1")
        assert field["name"] == "MyFormula"
        
        # Validate field type
        validate_field_type(field, ["formula"], "compression")
        # Should not raise
    
    def test_validation_fails_for_wrong_field_type(self):
        """Test that validation chain catches wrong field type"""
        metadata = {
            "tables": [
                {
                    "id": "tbl1",
                    "name": "Table",
                    "fields": [
                        {"id": "fld1", "name": "NotFormula", "type": "text"}
                    ]
                }
            ]
        }
        
        validated = validate_metadata(metadata)
        table, field = find_field_by_id(validated, "fld1")
        
        # Should raise because text field can't be compressed
        with pytest.raises(InvalidFieldTypeError):
            validate_field_type(field, ["formula"], "compression")
    
    def test_missing_metadata_error_flow(self):
        """Test error flow when metadata is missing"""
        mock_element = MagicMock()
        mock_document = MagicMock()
        mock_document.getElementById.return_value = mock_element
        
        try:
            validate_metadata(None)
        except MetadataError as e:
            with patch('components.error_handling.document', mock_document):
                handle_tab_error(e, "loading schema", "error-div")
        
        # Should have displayed error with generic message (not the exact constant)
        assert "loading schema" in mock_element.innerHTML
