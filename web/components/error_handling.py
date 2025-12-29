"""Standardized error handling utilities for web components.

This module provides consistent error handling patterns across all tabs
and components, including error display, logging, and user feedback.
"""
import traceback
from typing import Optional
from pyscript import document
import sys
sys.path.append("web")
from constants import (
    ERROR_NO_METADATA,
    ERROR_FIELD_NOT_FOUND,
    ERROR_INVALID_FIELD_TYPE,
    ERROR_CIRCULAR_DEPENDENCY,
)


class AnalysisError(Exception):
    """Base exception for analysis-related errors."""
    pass


class MetadataError(AnalysisError):
    """Raised when schema metadata is unavailable or invalid."""
    pass


class FieldNotFoundError(AnalysisError):
    """Raised when a field cannot be found in the schema."""
    pass


class InvalidFieldTypeError(AnalysisError):
    """Raised when an operation is attempted on an invalid field type."""
    pass


class CircularDependencyError(AnalysisError):
    """Raised when a circular dependency is detected."""
    pass


def log_error(message: str, exception: Optional[Exception] = None, include_trace: bool = True) -> None:
    """
    Log an error message to console with optional exception details.
    
    Args:
        message: Human-readable error message
        exception: Optional exception object
        include_trace: Whether to include full traceback
    """
    print(f"❌ Error: {message}")
    
    if exception:
        print(f"   Exception type: {type(exception).__name__}")
        print(f"   Exception message: {str(exception)}")
    
    if include_trace and exception:
        print("   Traceback:")
        print(traceback.format_exc())


def display_error_in_element(element_id: str, error_message: str, error_type: str = "error") -> None:
    """
    Display an error message in a DOM element with consistent styling.
    
    Args:
        element_id: ID of the element to update
        error_message: Error message to display
        error_type: Type of error - "error" (red), "warning" (yellow), or "info" (blue)
    """
    element = document.getElementById(element_id)
    if not element:
        print(f"Warning: Could not find element with ID '{element_id}' to display error")
        return
    
    # Choose colors based on error type
    if error_type == "warning":
        bg_color = "bg-yellow-50"
        dark_bg_color = "dark:bg-yellow-900/20"
        text_color = "text-yellow-800"
        dark_text_color = "dark:text-yellow-200"
        border_color = "border-yellow-300"
        dark_border_color = "dark:border-yellow-700"
        icon = "⚠️"
    elif error_type == "info":
        bg_color = "bg-blue-50"
        dark_bg_color = "dark:bg-blue-900/20"
        text_color = "text-blue-800"
        dark_text_color = "dark:text-blue-200"
        border_color = "border-blue-300"
        dark_border_color = "dark:border-blue-700"
        icon = "ℹ️"
    else:  # error
        bg_color = "bg-red-50"
        dark_bg_color = "dark:bg-red-900/20"
        text_color = "text-red-800"
        dark_text_color = "dark:text-red-200"
        border_color = "border-red-300"
        dark_border_color = "dark:border-red-700"
        icon = "❌"
    
    element.innerHTML = f"""
        <div class="{bg_color} {dark_bg_color} border {border_color} {dark_border_color} 
                    rounded-lg p-4 {text_color} {dark_text_color}">
            <span class="font-semibold">{icon} {error_type.capitalize()}:</span>
            <span class="ml-2">{error_message}</span>
        </div>
    """


def handle_tab_error(
    error: Exception,
    context: str,
    display_element_id: Optional[str] = None,
    user_message: Optional[str] = None
) -> None:
    """
    Standardized error handler for tab operations.
    
    Logs the error to console and optionally displays it to the user.
    
    Args:
        error: The exception that occurred
        context: Description of what was being attempted (e.g., "generating mermaid diagram")
        display_element_id: Optional element ID to display error in
        user_message: Optional custom message for the user (defaults to generic message)
    """
    # Log to console
    log_error(f"Error during {context}", error, include_trace=True)
    
    # Display to user if element provided
    if display_element_id:
        if user_message is None:
            user_message = f"An error occurred while {context}. Check the console for details."
        display_error_in_element(display_element_id, user_message)


def validate_metadata(metadata: Optional[dict]) -> dict:
    """
    Validate that metadata is available and properly structured.
    
    Args:
        metadata: Metadata dictionary to validate
        
    Returns:
        The validated metadata dictionary
        
    Raises:
        MetadataError: If metadata is invalid or missing
    """
    if metadata is None:
        raise MetadataError(ERROR_NO_METADATA)
    
    if not isinstance(metadata, dict):
        raise MetadataError("Schema metadata is not a valid dictionary")
    
    if "tables" not in metadata:
        raise MetadataError("Schema metadata is missing 'tables' key")
    
    return metadata


def find_field_by_id(metadata: dict, field_id: str) -> tuple[dict, dict]:
    """
    Find a field and its parent table by field ID.
    
    Args:
        metadata: Schema metadata
        field_id: Field ID to search for
        
    Returns:
        Tuple of (table, field) dictionaries
        
    Raises:
        FieldNotFoundError: If field is not found
    """
    for table in metadata.get("tables", []):
        for field in table.get("fields", []):
            if field.get("id") == field_id:
                return table, field
    
    raise FieldNotFoundError(f"{ERROR_FIELD_NOT_FOUND} (ID: {field_id})")


def validate_field_type(field: dict, expected_types: list[str], operation: str) -> None:
    """
    Validate that a field is one of the expected types.
    
    Args:
        field: Field dictionary
        expected_types: List of acceptable field types
        operation: Description of the operation being attempted
        
    Raises:
        InvalidFieldTypeError: If field type doesn't match expectations
    """
    field_type = field.get("type")
    field_name = field.get("name", "Unknown")
    
    if field_type not in expected_types:
        expected = ", ".join(expected_types)
        raise InvalidFieldTypeError(
            f"{ERROR_INVALID_FIELD_TYPE} Field '{field_name}' is type '{field_type}', "
            f"but {operation} requires one of: {expected}"
        )
