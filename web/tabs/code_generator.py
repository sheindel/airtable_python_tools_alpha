"""
Code Generator Tab - Unified code generation interface with workflow-based approach

This module provides a single interface for generating various types of code from Airtable schemas:
- Client libraries (TypeScript/JavaScript)
- Server SDKs (Python)
- Database schemas (SQL)
- Full-stack packages (all of the above)
"""

from pyscript import document, window
from pyodide.ffi import create_proxy, create_once_callable
import sys
import json

sys.path.append("web")

from components.airtable_client import get_local_storage_metadata
from components.error_handling import handle_tab_error, validate_metadata, AnalysisError
from components.code_display import create_code_block
from components.async_operations import defer_execution, ProgressTracker
from code_generators.workflows import (
    create_workflow,
    WORKFLOWS,
    DEFAULT_OPTIONS,
)


def initialize():
    """Initialize the code generator tab"""
    print("Initializing Code Generator tab...")
    
    # Export functions to JavaScript using create_proxy
    window.generateCodeFromWorkflow = create_proxy(generate_code_from_workflow)
    window.updateWorkflowOptions = create_proxy(update_workflow_options)
    window.downloadGeneratedFile = create_proxy(download_generated_file)
    window.downloadAllFiles = create_proxy(download_all_files)
    
    # Setup workflow selector event listeners
    setup_workflow_selector()
    
    print("Code Generator tab initialized")


def setup_workflow_selector():
    """Setup the workflow selector UI"""
    workflow_selector = document.getElementById("workflow-selector")
    if not workflow_selector:
        return
    
    # Create workflow option cards
    workflow_options_html = """
    <div class="workflow-options grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div class="workflow-card border-2 border-gray-300 dark:border-gray-600 rounded-lg p-4 cursor-pointer hover:border-primary-500 transition-all"
             onclick="window.selectWorkflow('client-library')" data-workflow="client-library">
            <div class="text-3xl mb-2">🌐</div>
            <h3 class="font-bold text-lg mb-1 dark:text-white">Client Library</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">TypeScript/JavaScript types and helpers for frontend/React/Vue apps</p>
            <div class="text-xs text-gray-500 dark:text-gray-500 mt-2">
                Generates: types.ts, helpers.ts, examples.ts
            </div>
        </div>
        
        <div class="workflow-card border-2 border-gray-300 dark:border-gray-600 rounded-lg p-4 cursor-pointer hover:border-primary-500 transition-all"
             onclick="window.selectWorkflow('server-sdk')" data-workflow="server-sdk">
            <div class="text-3xl mb-2">🐍</div>
            <h3 class="font-bold text-lg mb-1 dark:text-white">Server SDK</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Python library with computed field evaluators for backend services</p>
            <div class="text-xs text-gray-500 dark:text-gray-500 mt-2">
                Generates: types.py, helpers.py, computed_fields.py
            </div>
        </div>
        
        <div class="workflow-card border-2 border-gray-300 dark:border-gray-600 rounded-lg p-4 cursor-pointer hover:border-primary-500 transition-all"
             onclick="window.selectWorkflow('database-schema')" data-workflow="database-schema">
            <div class="text-3xl mb-2">🗄️</div>
            <h3 class="font-bold text-lg mb-1 dark:text-white">Database Schema</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">PostgreSQL schema with tables, columns, and formula logic</p>
            <div class="text-xs text-gray-500 dark:text-gray-500 mt-2">
                Generates: schema.sql, functions_and_views.sql
            </div>
        </div>
        
        <div class="workflow-card border-2 border-gray-300 dark:border-gray-600 rounded-lg p-4 cursor-pointer hover:border-primary-500 transition-all"
             onclick="window.selectWorkflow('fullstack')" data-workflow="fullstack">
            <div class="text-3xl mb-2">📦</div>
            <h3 class="font-bold text-lg mb-1 dark:text-white">Full-Stack Package</h3>
            <p class="text-sm text-gray-600 dark:text-gray-400">Complete code package for all environments</p>
            <div class="text-xs text-gray-500 dark:text-gray-500 mt-2">
                Generates: All of the above organized in folders
            </div>
        </div>
    </div>
    """
    workflow_selector.innerHTML = workflow_options_html
    
    # Export select function using create_proxy
    window.selectWorkflow = create_proxy(select_workflow)


def select_workflow(workflow_id):
    """
    Handle workflow selection
    
    Args:
        workflow_id: The selected workflow ID
    """
    print(f"Selected workflow: {workflow_id}")
    
    # Update UI to highlight selected workflow
    cards = document.querySelectorAll(".workflow-card")
    for card in cards:
        if card.getAttribute("data-workflow") == workflow_id:
            card.classList.add("border-primary-500", "bg-primary-50", "dark:bg-primary-900/20")
        else:
            card.classList.remove("border-primary-500", "bg-primary-50", "dark:bg-primary-900/20")
    
    # Show options for selected workflow
    show_workflow_options(workflow_id)
    
    # Show generate button
    generate_button = document.getElementById("generate-code-button")
    if generate_button:
        generate_button.classList.remove("hidden")


def show_workflow_options(workflow_id):
    """
    Display options form for the selected workflow
    
    Args:
        workflow_id: The workflow ID
    """
    options_container = document.getElementById("workflow-options")
    if not options_container:
        return
    
    defaults = DEFAULT_OPTIONS.get(workflow_id, {})
    
    # Build options HTML based on workflow
    options_html = f'<input type="hidden" id="selected-workflow" value="{workflow_id}">'
    options_html += '<div class="options-form space-y-4 mt-6">'
    options_html += '<h3 class="text-lg font-bold mb-4 dark:text-white">Configuration Options</h3>'
    
    if workflow_id == "client-library":
        options_html += '''
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-helpers" checked class="rounded">
            <span class="dark:text-gray-200">Include helper functions (getField, setField, etc.)</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-formula-runtime" class="rounded">
            <span class="dark:text-gray-200">Generate JavaScript runtime for formulas</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-examples" checked class="rounded">
            <span class="dark:text-gray-200">Include usage examples</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-async-data-access" checked class="rounded">
            <span class="dark:text-gray-200">Async data access for lookups/rollups</span>
        </label>
        <div class="ml-4">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Output format:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="output-mode" value="separate" checked class="rounded">
                <span class="dark:text-gray-200">Separate files (recommended)</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="output-mode" value="bundled" class="rounded">
                <span class="dark:text-gray-200">Single bundled file</span>
            </label>
        </div>
        '''
    
    elif workflow_id == "server-sdk":
        options_html += '''
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-helpers" checked class="rounded">
            <span class="dark:text-gray-200">Include helper functions</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-formula-runtime" checked class="rounded">
            <span class="dark:text-gray-200">Generate computed field evaluators</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-examples" checked class="rounded">
            <span class="dark:text-gray-200">Include usage examples</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-null-checks" checked class="rounded">
            <span class="dark:text-gray-200">Add null safety checks</span>
        </label>
        <div class="ml-4">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Type definition style:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="type-style" value="dataclass" checked class="rounded">
                <span class="dark:text-gray-200">Dataclasses (@dataclass)</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="type-style" value="typeddict" class="rounded">
                <span class="dark:text-gray-200">TypedDict (typing.TypedDict)</span>
            </label>
        </div>
        <div class="ml-4 mt-2">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Data access mode:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="data-access-mode" value="dataclass" checked class="rounded">
                <span class="dark:text-gray-200">Dataclass attributes (record.field_name)</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="data-access-mode" value="dict" class="rounded">
                <span class="dark:text-gray-200">Dictionary keys (record["field_name"])</span>
            </label>
        </div>
        '''
    
    elif workflow_id == "database-schema":
        options_html += '''
        <div class="ml-4">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Database dialect:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="dialect" value="postgresql" checked class="rounded">
                <span class="dark:text-gray-200">PostgreSQL (recommended)</span>
            </label>
        </div>
        <div class="ml-4 mt-2">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Column naming:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="use-field-ids" value="false" checked class="rounded">
                <span class="dark:text-gray-200">Transform to snake_case names</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="use-field-ids" value="true" class="rounded">
                <span class="dark:text-gray-200">Use Airtable field IDs (fld123...)</span>
            </label>
        </div>
        <div class="ml-4 mt-2">
            <label class="block text-sm font-medium mb-2 dark:text-gray-200">Formula handling:</label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="formula-mode" value="skip" class="rounded">
                <span class="dark:text-gray-200">Skip formulas (types only)</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="formula-mode" value="generated" class="rounded">
                <span class="dark:text-gray-200">Generated columns (STORED)</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="formula-mode" value="functions" checked class="rounded">
                <span class="dark:text-gray-200">SQL functions</span>
            </label>
            <label class="flex items-center space-x-2">
                <input type="radio" name="formula-mode" value="hybrid" class="rounded">
                <span class="dark:text-gray-200">Hybrid (simple as STORED, complex as functions)</span>
            </label>
        </div>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-views" checked class="rounded">
            <span class="dark:text-gray-200">Include views</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-indexes" checked class="rounded">
            <span class="dark:text-gray-200">Include indexes for linked fields</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-constraints" checked class="rounded">
            <span class="dark:text-gray-200">Include foreign key constraints</span>
        </label>
        '''
    
    elif workflow_id == "fullstack":
        options_html += '''
        <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Generates all files with best-practice defaults.
        </p>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-typescript" checked class="rounded">
            <span class="dark:text-gray-200">Include TypeScript</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-python" checked class="rounded">
            <span class="dark:text-gray-200">Include Python</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-sql" checked class="rounded">
            <span class="dark:text-gray-200">Include SQL</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-readme" checked class="rounded">
            <span class="dark:text-gray-200">Include README with setup instructions</span>
        </label>
        <label class="flex items-center space-x-2">
            <input type="checkbox" id="opt-include-config" checked class="rounded">
            <span class="dark:text-gray-200">Include package configuration files</span>
        </label>
        '''
    
    options_html += '</div>'
    options_container.innerHTML = options_html


def update_workflow_options(workflow_id):
    """
    Update displayed options when workflow changes
    
    Args:
        workflow_id: The new workflow ID
    """
    show_workflow_options(workflow_id)


def generate_code_from_workflow():
    """Generate code using the selected workflow"""
    try:
        # Get metadata
        metadata = validate_metadata(get_local_storage_metadata())
        
        # Get selected workflow
        workflow_select = document.getElementById("selected-workflow")
        if not workflow_select:
            raise AnalysisError("No workflow selected", "Please select a workflow first")
        
        workflow_id = workflow_select.value
        
        # Collect options from form
        options = collect_form_options(workflow_id)
        
        # Show loading and defer heavy work to allow UI update
        output = document.getElementById("code-generator-output")
        if output:
            from components.loading import create_detailed_spinner
            
            # Determine steps based on workflow
            substeps = get_workflow_steps(workflow_id, options)
            output.innerHTML = create_detailed_spinner(
                "Generating Code",
                "Please wait while we generate your code files...",
                substeps,
                "code-gen-spinner"
            )
        
        # Defer actual generation to allow spinner to render
        def do_generation():
            try:
                # Create workflow and generate
                tracker = ProgressTracker("code-generator-output", total_steps=len(substeps))
                tracker.start("Initializing code generation...")
                
                workflow = create_workflow(workflow_id, metadata, options)
                
                # Update progress during generation
                tracker.update(1, "Generating files...", f"Using {workflow_id} workflow")
                generated_files = workflow.generate()
                
                tracker.update(len(substeps), "Complete!", f"Generated {len(generated_files)} files")
                
                # Small delay to show completion state
                import js
                js.setTimeout(create_once_callable(lambda: display_generated_files(generated_files)), 500)
                
                print(f"Generated {len(generated_files)} files using {workflow_id} workflow")
                
            except AnalysisError as e:
                handle_tab_error(e, "generating code", "code-generator-output")
            except Exception as e:
                handle_tab_error(
                    AnalysisError(str(e), "An unexpected error occurred"),
                    "generating code",
                    "code-generator-output"
                )
        
        # Defer execution by 150ms to ensure spinner renders
        defer_execution(do_generation, 150)
        
    except AnalysisError as e:
        handle_tab_error(e, "generating code", "code-generator-output")
    except Exception as e:
        handle_tab_error(
            AnalysisError(str(e), "An unexpected error occurred"),
            "generating code",
            "code-generator-output"
        )


def get_workflow_steps(workflow_id: str, options: dict) -> list:
    """
    Get the expected steps for a workflow based on options.
    
    Args:
        workflow_id: The workflow ID
        options: Workflow options
        
    Returns:
        List of dicts with 'text' keys for substeps
    """
    steps = []
    
    if workflow_id == "client-library":
        steps.append({"text": "Generating TypeScript types", "completed": False})
        if options.get("include_helpers"):
            steps.append({"text": "Generating helper functions", "completed": False})
        if options.get("include_formula_runtime"):
            steps.append({"text": "Generating formula runtime", "completed": False})
        if options.get("include_examples"):
            steps.append({"text": "Generating usage examples", "completed": False})
    
    elif workflow_id == "server-sdk":
        steps.append({"text": "Generating Python types", "completed": False})
        if options.get("include_helpers"):
            steps.append({"text": "Generating helper functions", "completed": False})
        if options.get("include_formula_runtime"):
            steps.append({"text": "Generating computed field evaluators", "completed": False})
        if options.get("include_examples"):
            steps.append({"text": "Generating usage examples", "completed": False})
    
    elif workflow_id == "database-schema":
        steps.append({"text": "Generating table schema", "completed": False})
        if options.get("formula_mode") in ["functions", "hybrid"]:
            steps.append({"text": "Generating SQL functions", "completed": False})
        if options.get("include_views"):
            steps.append({"text": "Generating views", "completed": False})
        if options.get("formula_mode") == "triggers":
            steps.append({"text": "Generating triggers", "completed": False})
    
    elif workflow_id == "fullstack":
        if options.get("include_typescript"):
            steps.append({"text": "Generating TypeScript package", "completed": False})
        if options.get("include_python"):
            steps.append({"text": "Generating Python package", "completed": False})
        if options.get("include_sql"):
            steps.append({"text": "Generating SQL schema", "completed": False})
        if options.get("include_readme"):
            steps.append({"text": "Generating documentation", "completed": False})
    
    return steps


def collect_form_options(workflow_id):
    """
    Collect options from the form
    
    Args:
        workflow_id: The workflow ID
    
    Returns:
        Dictionary of options
    """
    options = {}
    
    # Collect checkbox values
    checkboxes = document.querySelectorAll("#workflow-options input[type='checkbox']")
    for checkbox in checkboxes:
        checkbox_id = checkbox.id
        if checkbox_id.startswith("opt-"):
            option_name = checkbox_id.replace("opt-", "").replace("-", "_")
            options[option_name] = checkbox.checked
    
    # Collect radio button values
    radio_groups = ["output-mode", "type-style", "data-access-mode", "dialect", "use-field-ids", "formula-mode"]
    for group in radio_groups:
        radios = document.querySelectorAll(f"input[name='{group}']:checked")
        if radios and len(radios) > 0:
            option_name = group.replace("-", "_")
            value = radios[0].value
            # Convert string booleans
            if value == "true":
                options[option_name] = True
            elif value == "false":
                options[option_name] = False
            else:
                options[option_name] = value
    
    return options


def display_generated_files(files):
    """
    Display generated files in a file tree with previews
    
    Args:
        files: Dictionary mapping filename to content
    """
    output = document.getElementById("code-generator-output")
    if not output:
        return
    
    # Store files in global state for download
    # Convert Python dict to JS object
    import js
    window.generatedFiles = js.Object.fromEntries(
        js.Object.entries(files)
    )
    
    # Build file tree HTML
    html = '<div class="generated-files-container mt-6">'
    html += '<div class="flex justify-between items-center mb-4">'
    html += '<h3 class="text-xl font-bold">Generated Files</h3>'
    html += '<button onclick="window.downloadAllFiles()" class="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-lg shadow-sm hover:shadow transition-all duration-150">'
    html += '📦 Download All (.zip)</button>'
    html += '</div>'
    
    # Create file list
    html += '<div class="file-tree space-y-2">'
    
    # Organize files by folder
    folders = {}
    for filename, content in files.items():
        if "/" in filename:
            folder = filename.split("/")[0]
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(filename)
        else:
            if "root" not in folders:
                folders["root"] = []
            folders["root"].append(filename)
    
    # Render folders
    for folder, filenames in folders.items():
        if folder == "root":
            # Root level files
            for filename in filenames:
                html += render_file_item(filename, files[filename])
        else:
            # Folder
            html += f'<div class="folder mb-4">'
            html += f'<div class="folder-header font-bold text-lg mb-2 dark:text-white">📁 {folder}/</div>'
            html += f'<div class="folder-contents ml-4 space-y-2">'
            for filename in filenames:
                html += render_file_item(filename, files[filename])
            html += '</div></div>'
    
    html += '</div></div>'
    
    output.innerHTML = html


def render_file_item(filename, content):
    """
    Render a single file item in the tree
    
    Args:
        filename: The filename
        content: The file content
    
    Returns:
        HTML string
    """
    # Calculate file size
    size_kb = len(content.encode('utf-8')) / 1024
    size_str = f"{size_kb:.1f} KB"
    
    # Determine file extension for syntax highlighting
    ext = filename.split(".")[-1] if "." in filename else "txt"
    
    html = f'<div class="file-item border border-gray-300 dark:border-gray-600 rounded-lg p-3 bg-white dark:bg-gray-800">'
    html += f'<div class="flex justify-between items-center">'
    html += f'<div class="flex items-center space-x-2 flex-1 cursor-pointer" onclick="window.toggleFilePreview(\'{filename}\')">'
    html += f'<span>📄</span>'
    html += f'<span class="font-medium dark:text-white">{filename.split("/")[-1]}</span>'
    html += f'<span class="text-xs text-gray-500 dark:text-gray-400">{size_str}</span>'
    html += f'</div>'
    html += f'<button onclick="window.downloadGeneratedFile(\'{filename}\')" class="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 px-3 py-1 rounded text-sm dark:text-white">'
    html += '⬇️ Download</button>'
    html += '</div>'
    html += f'<div id="preview-{filename.replace("/", "-").replace(".", "-")}" class="file-preview hidden mt-3">'
    html += create_code_block(content)  # Show full content, not truncated
    html += '</div>'
    html += '</div>'
    
    return html


# Export toggle function
def toggle_file_preview(filename):
    """Toggle file preview visibility"""
    preview_id = f"preview-{filename.replace('/', '-').replace('.', '-')}"
    preview = document.getElementById(preview_id)
    if preview:
        if preview.classList.contains("hidden"):
            preview.classList.remove("hidden")
        else:
            preview.classList.add("hidden")


window.toggleFilePreview = create_proxy(toggle_file_preview)


def download_generated_file(filename):
    """
    Download a single generated file
    
    Args:
        filename: The filename to download
    """
    import js
    
    files = window.generatedFiles
    if not files or filename not in files:
        print(f"File not found: {filename}")
        return
    
    content = files[filename]
    
    # Create blob and download
    blob = js.Blob.new([content], {"type": "text/plain"})
    url = js.URL.createObjectURL(blob)
    
    link = document.createElement("a")
    link.href = url
    link.download = filename.split("/")[-1]  # Just the filename, not the path
    link.click()
    
    js.URL.revokeObjectURL(url)


def download_all_files():
    """Download all generated files as a ZIP"""
    # TODO: Implement ZIP file creation
    # For now, just download each file separately
    import js
    
    files = window.generatedFiles
    if not files:
        print("No files to download")
        return
    
    for filename, content in files.items():
        # Small delay between downloads to avoid browser blocking
        js.setTimeout(create_once_callable(lambda f=filename: download_generated_file(f)), 100)
    
    print(f"Downloading {len(files)} files...")
