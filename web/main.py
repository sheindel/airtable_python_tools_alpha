"""Main entry point for Airtable Analysis Tools web application

This module handles:
- Tab initialization and routing
- Common UI state management
- Coordination between different analysis tools
"""
import sys
sys.path.append("web")

import pyodide

from pyscript import window

# Import tab modules
from tabs import (
    dependency_mapper, 
    dependency_analysis, 
    formula_grapher, 
    formula_compressor, 
    complexity_scorecard, 
    unused_fields, 
    formula_evaluator, 
    postgres_schema, 
    types_generator,
    code_generator
)

# Store current active tab
current_tab = "dependency-mapper"


def initialize_tabs():
    """Initialize all tab modules"""
    print("Initializing tabs...")
    
    # Initialize each tab
    dependency_mapper.initialize()
    dependency_analysis.initialize()
    formula_grapher.initialize()
    formula_compressor.initialize()
    complexity_scorecard.initialize()
    unused_fields.initialize()
    formula_evaluator.initialize()
    postgres_schema.initialize()
    types_generator.initialize()
    code_generator.initialize()  # NEW: Initialize code generator tab
    
    print("All tabs initialized")


def switch_tab(tab_name: str):
    """Switch to a different tab
    
    Args:
        tab_name: Name of the tab to switch to
    """
    global current_tab
    current_tab = tab_name


# Export tab switching function to JavaScript
window.switchTabPython = switch_tab

# Initialize all tabs when PyScript is ready
initialize_tabs()
