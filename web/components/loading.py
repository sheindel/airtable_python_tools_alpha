"""Loading spinner and progress indicator components.

Provides reusable UI components for showing loading states during long-running operations.
"""

from typing import Optional


class LoadingConfig:
    """Configuration constants for loading UI"""
    
    # Spinner HTML templates
    SPINNER_DEFAULT = """
    <div class="flex flex-col items-center justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <p class="mt-4 text-gray-600 dark:text-gray-400">{message}</p>
    </div>
    """
    
    SPINNER_WITH_PROGRESS = """
    <div class="flex flex-col items-center justify-center p-8">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <p class="mt-4 text-gray-600 dark:text-gray-400 font-semibold">{message}</p>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-500">{progress_text}</p>
        <div class="w-64 bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-3">
            <div class="bg-primary-600 h-2 rounded-full transition-all duration-300" style="width: {progress}%"></div>
        </div>
    </div>
    """
    
    SPINNER_DETAILED = """
    <div class="flex flex-col items-center justify-center p-8">
        <div class="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600"></div>
        <h3 class="mt-4 text-lg font-bold text-gray-800 dark:text-white">{title}</h3>
        <p class="mt-2 text-gray-600 dark:text-gray-400">{message}</p>
        {substeps_html}
    </div>
    """
    
    SUBSTEP_ITEM = """
    <div class="flex items-center space-x-2 text-sm">
        <span class="{icon_class}">{icon}</span>
        <span class="{text_class}">{text}</span>
    </div>
    """


def create_loading_spinner(
    message: str = "Loading...",
    spinner_id: Optional[str] = None
) -> str:
    """
    Create a simple loading spinner.
    
    Args:
        message: Loading message to display
        spinner_id: Optional ID for the spinner container
        
    Returns:
        HTML string for the loading spinner
    """
    id_attr = f' id="{spinner_id}"' if spinner_id else ''
    return f'<div{id_attr}>{LoadingConfig.SPINNER_DEFAULT.format(message=message)}</div>'


def create_progress_spinner(
    message: str = "Processing...",
    progress: int = 0,
    progress_text: str = "",
    spinner_id: Optional[str] = None
) -> str:
    """
    Create a loading spinner with progress bar.
    
    Args:
        message: Main loading message
        progress: Progress percentage (0-100)
        progress_text: Additional progress details
        spinner_id: Optional ID for the spinner container
        
    Returns:
        HTML string for the progress spinner
    """
    id_attr = f' id="{spinner_id}"' if spinner_id else ''
    return f'<div{id_attr}>{LoadingConfig.SPINNER_WITH_PROGRESS.format(message=message, progress=progress, progress_text=progress_text)}</div>'


def create_detailed_spinner(
    title: str,
    message: str,
    substeps: Optional[list] = None,
    spinner_id: Optional[str] = None
) -> str:
    """
    Create a detailed loading spinner with substeps.
    
    Args:
        title: Main title
        message: Loading message
        substeps: List of dicts with 'text', 'completed' keys
        spinner_id: Optional ID for the spinner container
        
    Returns:
        HTML string for the detailed spinner
    """
    substeps_html = ""
    if substeps:
        substeps_html = '<div class="mt-4 space-y-2">'
        for step in substeps:
            icon = "✓" if step.get("completed") else "⋯"
            icon_class = "text-green-600 dark:text-green-400" if step.get("completed") else "text-gray-400 dark:text-gray-600"
            text_class = "text-gray-700 dark:text-gray-300" if step.get("completed") else "text-gray-500 dark:text-gray-500"
            substeps_html += LoadingConfig.SUBSTEP_ITEM.format(
                icon=icon,
                icon_class=icon_class,
                text=step.get("text", ""),
                text_class=text_class
            )
        substeps_html += '</div>'
    
    id_attr = f' id="{spinner_id}"' if spinner_id else ''
    return f'<div{id_attr}>{LoadingConfig.SPINNER_DETAILED.format(title=title, message=message, substeps_html=substeps_html)}</div>'


def show_loading(element_id: str, message: str = "Loading..."):
    """
    Show loading spinner in an element (requires pyscript import).
    
    Args:
        element_id: ID of the element to show loading in
        message: Loading message
        
    Note:
        This function requires pyscript to be imported.
        It's a convenience wrapper around create_loading_spinner.
    """
    try:
        from pyscript import document
        element = document.getElementById(element_id)
        if element:
            element.innerHTML = create_loading_spinner(message)
    except ImportError:
        print("Warning: pyscript not available, cannot show loading spinner")


def hide_loading(element_id: str):
    """
    Clear loading spinner from an element.
    
    Args:
        element_id: ID of the element to clear
        
    Note:
        This function requires pyscript to be imported.
    """
    try:
        from pyscript import document
        element = document.getElementById(element_id)
        if element:
            element.innerHTML = ""
    except ImportError:
        print("Warning: pyscript not available, cannot hide loading spinner")


def update_progress(element_id: str, progress: int, message: str = "Processing...", progress_text: str = ""):
    """
    Update progress spinner in an element.
    
    Args:
        element_id: ID of the element containing the progress spinner
        progress: Progress percentage (0-100)
        message: Main message
        progress_text: Additional progress details
        
    Note:
        This function requires pyscript to be imported.
    """
    try:
        from pyscript import document
        element = document.getElementById(element_id)
        if element:
            element.innerHTML = create_progress_spinner(message, progress, progress_text)
    except ImportError:
        print("Warning: pyscript not available, cannot update progress")
