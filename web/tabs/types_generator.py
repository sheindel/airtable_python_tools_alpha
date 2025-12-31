"""Types Generator Tab - Generate TypeScript or Python type definitions"""

from pyscript import document, window
import sys
sys.path.append("web")

from components.airtable_client import get_local_storage_metadata
from components.error_handling import handle_tab_error, validate_metadata, AnalysisError
from types_generator import generate_typescript_types, generate_python_types


def generate_types():
    """Generate type definitions based on user selections"""
    try:
        # Get metadata
        metadata = validate_metadata(get_local_storage_metadata())
        
        # Get user selections
        language_select = document.getElementById("types-language")
        include_helpers_checkbox = document.getElementById("types-include-helpers")
        
        if not language_select:
            raise AnalysisError("Language select element not found")
        
        language = language_select.value
        include_helpers = include_helpers_checkbox.checked if include_helpers_checkbox else True
        
        # Generate types based on language
        if language == "typescript":
            types_code = generate_typescript_types(metadata, include_helpers=include_helpers)
        elif language == "python-dataclass":
            types_code = generate_python_types(metadata, include_helpers=include_helpers, use_dataclasses=True)
        elif language == "python-typeddict":
            types_code = generate_python_types(metadata, include_helpers=include_helpers, use_dataclasses=False)
        else:
            raise AnalysisError(f"Unknown language: {language}")
        
        # Display result
        output_elem = document.getElementById("types-output")
        if output_elem:
            # Create container with copy button
            output_elem.innerHTML = f"""
                <div class="relative">
                    <button id="copy-types-btn" 
                            class="absolute top-2 right-2 bg-white/80 dark:bg-gray-800/80 hover:bg-white dark:hover:bg-gray-700 
                                   text-gray-700 dark:text-gray-300 p-2 rounded-lg shadow-sm transition-all duration-150 
                                   opacity-0 hover:opacity-100 focus:opacity-100 group"
                            style="backdrop-filter: blur(4px);"
                            title="Copy to clipboard">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                        </svg>
                    </button>
                    <pre class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto border border-gray-200 dark:border-gray-700"><code class="text-sm text-gray-800 dark:text-gray-200">{types_code}</code></pre>
                </div>
            """
            
            # Wire up copy button
            copy_btn = document.getElementById("copy-types-btn")
            if copy_btn:
                copy_btn.onclick = lambda e: copy_types_to_clipboard(types_code)
        
    except AnalysisError as e:
        handle_tab_error(e, "generating types", "types-output")
    except Exception as e:
        handle_tab_error(
            AnalysisError(f"Unexpected error: {str(e)}"),
            "generating types",
            "types-output"
        )


def copy_types_to_clipboard(types_code: str):
    """Copy generated types to clipboard"""
    try:
        # Use navigator.clipboard API via JavaScript
        window.navigator.clipboard.writeText(types_code)
        
        # Show success feedback
        copy_btn = document.getElementById("copy-types-btn")
        if copy_btn:
            original_html = copy_btn.innerHTML
            copy_btn.innerHTML = """
                <svg class="w-5 h-5 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
            """
            copy_btn.classList.add("opacity-100")
            
            # Reset after 2 seconds
            def reset_button():
                if copy_btn:
                    copy_btn.innerHTML = original_html
                    copy_btn.classList.remove("opacity-100")
            
            window.setTimeout(reset_button, 2000)
            
    except Exception as e:
        print(f"Error copying to clipboard: {e}")


def initialize():
    """Initialize the types generator tab"""
    # Export function to global scope
    window.generateTypes = generate_types
    
    print("Types generator tab initialized")
