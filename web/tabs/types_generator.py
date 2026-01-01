"""Types Generator Tab - Generate TypeScript or Python type definitions"""

from pyscript import document, window
import sys
sys.path.append("web")

from components.airtable_client import get_local_storage_metadata
from components.error_handling import handle_tab_error, validate_metadata, AnalysisError
from types_generator import (
    generate_typescript_types,
    generate_python_types,
    generate_all_typescript_files,
    generate_all_python_files,
)


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
        
        # Generate files based on language
        files = {}
        if language == "typescript":
            files = generate_all_typescript_files(metadata, include_helpers=include_helpers)
        elif language == "python-dataclass":
            files = generate_all_python_files(metadata, include_helpers=include_helpers, use_dataclasses=True)
        elif language == "python-typeddict":
            files = generate_all_python_files(metadata, include_helpers=include_helpers, use_dataclasses=False)
        else:
            raise AnalysisError(f"Unknown language: {language}")
        
        # Display results
        output_elem = document.getElementById("types-output")
        if output_elem:
            html_parts = ['<div class="space-y-6">']
            
            # Add download all button at the top
            html_parts.append(f'''
                <div class="text-center mb-4">
                    <button id="download-all-btn"
                            class="bg-primary-600 hover:bg-primary-700 text-white font-semibold px-6 py-2.5 rounded-lg shadow-sm hover:shadow transition-all duration-150">
                        <svg class="w-5 h-5 inline-block mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                        </svg>
                        Download All Files
                    </button>
                </div>
            ''')
            
            # Generate HTML for each file with collapsible sections
            for i, (filename, content) in enumerate(files.items()):
                file_id = filename.replace(".", "-")
                is_first = i == 0
                collapsed_class = "" if is_first else "hidden"
                chevron_direction = "rotate-0" if is_first else "-rotate-90"
                
                html_parts.append(f'''
                    <div class="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <div class="bg-gray-100 dark:bg-gray-800 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                            <div class="flex items-center justify-between">
                                <button id="toggle-{file_id}-btn" 
                                        class="flex items-center gap-2 flex-1 text-left group"
                                        onclick="toggleCodePreview('{file_id}')">
                                    <svg id="chevron-{file_id}" 
                                         class="w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform duration-200 {chevron_direction}" 
                                         fill="none" 
                                         stroke="currentColor" 
                                         viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                                    </svg>
                                    <h3 class="font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                                        {filename}
                                    </h3>
                                </button>
                                <div class="flex gap-2">
                                    <button id="copy-{file_id}-btn" 
                                            class="bg-primary-600 hover:bg-primary-700 text-white text-sm px-3 py-1.5 rounded transition-colors duration-150"
                                            title="Copy to clipboard">
                                        <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                  d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                                        </svg>
                                        Copy
                                    </button>
                                    <button id="download-{file_id}-btn"
                                            class="bg-green-600 hover:bg-green-700 text-white text-sm px-3 py-1.5 rounded transition-colors duration-150"
                                            title="Download file">
                                        <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                        </svg>
                                        Download
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div id="preview-{file_id}" class="transition-all duration-200 {collapsed_class}">
                            <pre class="bg-gray-50 dark:bg-gray-900 p-4 overflow-x-auto max-h-96 overflow-y-auto"><code class="text-sm text-gray-800 dark:text-gray-200" id="code-{file_id}">{content}</code></pre>
                        </div>
                    </div>
                ''')
            
            html_parts.append('</div>')
            output_elem.innerHTML = ''.join(html_parts)
            
            # Wire up download all button first
            download_all_btn = document.getElementById("download-all-btn")
            if download_all_btn:
                download_all_btn.onclick = lambda e: download_all_files(files)
            
            # Wire up buttons for each file
            for filename, content in files.items():
                file_id = filename.replace(".", "-")
                
                # Copy button
                copy_btn = document.getElementById(f"copy-{file_id}-btn")
                if copy_btn:
                    copy_btn.onclick = lambda e, c=content, f=filename: copy_to_clipboard(c, f"copy-{file_id.replace('.', '-')}-btn")
                
                # Download button
                download_btn = document.getElementById(f"download-{file_id}-btn")
                if download_btn:
                    download_btn.onclick = lambda e, c=content, f=filename: download_file(c, f)
        
    except AnalysisError as e:
        handle_tab_error(e, "generating types", "types-output")
    except Exception as e:
        handle_tab_error(
            AnalysisError(f"Unexpected error: {str(e)}"),
            "generating types",
            "types-output"
        )


def toggle_code_preview(file_id: str):
    """Toggle visibility of code preview"""
    preview_elem = document.getElementById(f"preview-{file_id}")
    chevron_elem = document.getElementById(f"chevron-{file_id}")
    
    if preview_elem and chevron_elem:
        if preview_elem.classList.contains("hidden"):
            # Show preview
            preview_elem.classList.remove("hidden")
            chevron_elem.classList.remove("-rotate-90")
            chevron_elem.classList.add("rotate-0")
        else:
            # Hide preview
            preview_elem.classList.add("hidden")
            chevron_elem.classList.remove("rotate-0")
            chevron_elem.classList.add("-rotate-90")



def copy_to_clipboard(content: str, button_id: str):
    """Copy content to clipboard and show feedback"""
    try:
        # Use navigator.clipboard API via JavaScript
        window.navigator.clipboard.writeText(content)
        
        # Show success feedback
        copy_btn = document.getElementById(button_id)
        if copy_btn:
            original_html = copy_btn.innerHTML
            copy_btn.innerHTML = """
                <svg class="w-4 h-4 inline-block mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                Copied!
            """
            copy_btn.classList.add("bg-green-600")
            copy_btn.classList.remove("bg-primary-600")
            
            # Reset after 2 seconds
            def reset_button():
                if copy_btn:
                    copy_btn.innerHTML = original_html
                    copy_btn.classList.remove("bg-green-600")
                    copy_btn.classList.add("bg-primary-600")
            
            window.setTimeout(reset_button, 2000)
            
    except Exception as e:
        print(f"Error copying to clipboard: {e}")


def download_file(content: str, filename: str):
    """Download a single file"""
    try:
        # Create a blob and download it
        blob = window.Blob.new([content], {"type": "text/plain"})
        url = window.URL.createObjectURL(blob)
        
        # Create a temporary link and click it
        link = document.createElement("a")
        link.href = url
        link.download = filename
        link.click()
        
        # Clean up
        window.URL.revokeObjectURL(url)
        
    except Exception as e:
        print(f"Error downloading file: {e}")


def download_all_files(files: dict):
    """Download all files as a zip (or trigger individual downloads)"""
    try:
        # For now, download each file individually
        # In the future, we could create a zip file
        for filename, content in files.items():
            download_file(content, filename)
            
    except Exception as e:
        print(f"Error downloading files: {e}")


def initialize():
    """Initialize the types generator tab"""
    # Export functions to global scope
    window.generateTypes = generate_types
    window.toggleCodePreview = toggle_code_preview
    
    print("Types generator tab initialized")
