"""
Evaluator Generator Tab - Generate incremental formula evaluators

This tab allows users to generate Python code for evaluating computed fields
with incremental updates. Users can select a table and configure options like
data access mode, null checks, and output format.
"""

from pyscript import document, window
from pyodide.ffi import create_proxy
import sys
import json

sys.path.append("web")

from components.airtable_client import get_local_storage_metadata
from components.error_handling import handle_tab_error, validate_metadata, AnalysisError
from components.code_display import create_code_block
from components.async_operations import defer_execution
from code_generators.incremental_runtime_generator import (
    GeneratorOptions,
    generate_complete_module,
)


def initialize():
    """Initialize the evaluator generator tab"""
    print("Initializing Evaluator Generator tab...")
    
    # Export functions to JavaScript using create_proxy
    window.generateEvaluatorCode = create_proxy(generate_evaluator_code)
    window.downloadEvaluatorFile = create_proxy(download_evaluator_file)
    
    print("Evaluator Generator tab initialized")


def generate_evaluator_code():
    """Generate incremental evaluator code based on selected table and options"""
    try:
        # Get metadata
        metadata = validate_metadata(get_local_storage_metadata())
        
        # Get selected table
        table_dropdown = document.getElementById("evaluator-table-dropdown")
        if not table_dropdown:
            raise AnalysisError("Table dropdown not found", "UI initialization error")
        
        # Try to access selectedId property
        # In PyScript, JavaScript getters may require special handling
        try:
            table_id = table_dropdown.selectedId
        except (AttributeError, TypeError) as e:
            print(f"Error accessing selectedId: {e}")
            # Fallback: try to access internal _selected property
            try:
                selected_option = table_dropdown._selected
                table_id = selected_option.id if selected_option else None
            except:
                table_id = None
        
        # Debug logging
        dropdown_value = getattr(table_dropdown, 'value', '')
        print(f"Table dropdown - value: '{dropdown_value}', selectedId: '{table_id}'")
        
        if not table_id:
            if dropdown_value:
                # User typed something but didn't select - show helpful message
                raise AnalysisError(
                    "Please select a table from the dropdown list",
                    "Type to filter, then click a table from the list"
                )
            else:
                raise AnalysisError("No table selected", "Please select a table from the dropdown first")
        
        # Find the table
        table = None
        for t in metadata["tables"]:
            if t["id"] == table_id:
                table = t
                break
        
        if not table:
            raise AnalysisError("Table not found", f"Could not find table with ID {table_id}")
        
        # Collect options from form
        options = collect_evaluator_options()
        
        # Show loading state
        output = document.getElementById("evaluator-output")
        if output:
            output.innerHTML = """
                <div class="flex items-center justify-center py-12">
                    <div class="text-center">
                        <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                        <p class="text-gray-600 dark:text-gray-400">Generating evaluator code...</p>
                    </div>
                </div>
            """
        
        # Defer actual generation to allow loading UI to render
        def do_generation():
            try:
                # Generate the code
                generated_code = generate_complete_module(
                    metadata=metadata,
                    table_id=table_id,
                    options=options
                )
                
                # Display the generated code
                display_evaluator_code(generated_code, table["name"])
                
                print(f"Successfully generated evaluator for table: {table['name']}")
                
            except AnalysisError as e:
                handle_tab_error(e, "generating evaluator", "evaluator-output")
            except Exception as e:
                import traceback
                print("Error generating evaluator:", traceback.format_exc())
                handle_tab_error(
                    AnalysisError(str(e), "An unexpected error occurred during code generation"),
                    "generating evaluator",
                    "evaluator-output"
                )
        
        # Defer execution to allow UI update
        defer_execution(do_generation, 150)
        
    except AnalysisError as e:
        handle_tab_error(e, "generating evaluator", "evaluator-output")
    except Exception as e:
        import traceback
        print("Error in generate_evaluator_code:", traceback.format_exc())
        handle_tab_error(
            AnalysisError(str(e), "An unexpected error occurred"),
            "generating evaluator",
            "evaluator-output"
        )


def collect_evaluator_options():
    """
    Collect options from the form
    
    Returns:
        GeneratorOptions instance with user selections
    """
    options = GeneratorOptions()
    
    # Data access mode
    dataclass_radio = document.getElementById("opt-eval-dataclass")
    dict_radio = document.getElementById("opt-eval-dict")
    if dataclass_radio and dataclass_radio.checked:
        options.data_access_mode = "dataclass"
    elif dict_radio and dict_radio.checked:
        options.data_access_mode = "dict"
    
    # Null checks
    null_checks = document.getElementById("opt-eval-null-checks")
    if null_checks:
        options.include_null_checks = null_checks.checked
    
    # Type hints
    type_hints = document.getElementById("opt-eval-type-hints")
    if type_hints:
        options.include_type_hints = type_hints.checked
    
    # Docstrings
    docstrings = document.getElementById("opt-eval-docstrings")
    if docstrings:
        options.include_docstrings = docstrings.checked
    
    # Examples
    examples = document.getElementById("opt-eval-examples")
    if examples:
        options.include_examples = examples.checked
    
    # Optimization
    optimize = document.getElementById("opt-eval-optimize")
    if optimize:
        options.optimize_depth_skipping = optimize.checked
    
    # Stats tracking
    stats = document.getElementById("opt-eval-stats")
    if stats:
        options.track_computation_stats = stats.checked
    
    return options


def display_evaluator_code(code: str, table_name: str):
    """
    Display the generated evaluator code with download button
    
    Args:
        code: The generated Python code
        table_name: Name of the table (for filename)
    """
    output = document.getElementById("evaluator-output")
    if not output:
        return
    
    # Store code in global state for download
    # Store as plain strings to avoid borrowed proxy issues
    import js
    window.evaluatorCode = js.String(code)
    window.evaluatorTableName = js.String(table_name)
    
    # Sanitize table name for filename
    import re
    safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name.lower())
    filename = f"{safe_table_name}_evaluator.py"
    
    # Calculate file size
    size_kb = len(code.encode('utf-8')) / 1024
    size_str = f"{size_kb:.1f} KB"
    
    # Build display HTML
    html = f"""
    <div class="generated-evaluator-container">
        <div class="flex justify-between items-center mb-4">
            <div>
                <h3 class="text-xl font-bold dark:text-white">Generated Evaluator</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">{filename} • {size_str}</p>
            </div>
            <button onclick="window.downloadEvaluatorFile()" 
                    class="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm hover:shadow transition-all duration-150">
                ⬇️ Download {filename}
            </button>
        </div>
        
        <div class="code-preview bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg p-4">
            {create_code_block(code, show_copy_button=True, copy_button_id="copy-evaluator-code")}
        </div>
        
        <div class="mt-4 bg-blue-50 dark:bg-blue-900/30 border border-blue-200 dark:border-blue-700 rounded-lg p-4">
            <h4 class="font-semibold mb-2 text-blue-900 dark:text-blue-100">📚 Usage</h4>
            <p class="text-sm text-blue-800 dark:text-blue-200 mb-2">
                This evaluator efficiently updates computed fields when dependencies change:
            </p>
            <pre class="text-xs bg-white dark:bg-gray-800 p-3 rounded border border-blue-200 dark:border-blue-600 overflow-x-auto"><code class="text-gray-900 dark:text-gray-100">from {safe_table_name}_evaluator import {table_name.replace(' ', '')}, update_record, ComputationContext

# Create a record
record = {table_name.replace(' ', '')}(id="rec123", ...)

# Initial computation
context = ComputationContext(record, {{}})
record = update_record(record, context)

# Update a field and recompute only affected formulas
record.field_name = "new value"
record = update_record(record, context, changed_fields=["field_name"])</code></pre>
        </div>
    </div>
    """
    
    output.innerHTML = html


def download_evaluator_file():
    """Download the generated evaluator code as a Python file"""
    import js
    
    code = window.evaluatorCode
    table_name = window.evaluatorTableName
    
    if not code:
        print("No evaluator code to download")
        return
    
    # Sanitize table name for filename
    import re
    safe_table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name.lower())
    filename = f"{safe_table_name}_evaluator.py"
    
    # Create blob and download
    blob = js.Blob.new([code], {"type": "text/plain"})
    url = js.URL.createObjectURL(blob)
    
    link = document.createElement("a")
    link.href = url
    link.download = filename
    link.click()
    
    js.URL.revokeObjectURL(url)
    
    print(f"Downloaded {filename}")
