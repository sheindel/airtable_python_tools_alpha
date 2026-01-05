"""Utilities for handling long-running asynchronous operations in PyScript.

Provides wrappers and decorators for showing loading states during operations.
"""

import sys
sys.path.append("web")

from functools import wraps
from typing import Callable, Optional, Any
from components.loading import show_loading, hide_loading, update_progress


def with_loading_spinner(
    element_id: str,
    loading_message: str = "Processing...",
    error_element_id: Optional[str] = None
):
    """
    Decorator to wrap a function with loading spinner display.
    
    Args:
        element_id: ID of element to show loading in
        loading_message: Message to display while loading
        error_element_id: Optional separate element for error display
        
    Usage:
        @with_loading_spinner("output-div", "Generating code...")
        def generate_code():
            # Long-running operation
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            from pyscript import document
            from components.error_handling import display_error_in_element, AnalysisError
            
            # Show loading
            show_loading(element_id, loading_message)
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                return result
            except AnalysisError as e:
                # Handle known errors
                error_target = error_element_id or element_id
                display_error_in_element(e, error_target)
                return None
            except Exception as e:
                # Handle unexpected errors
                error_target = error_element_id or element_id
                from components.error_handling import AnalysisError
                analysis_error = AnalysisError(str(e), "An unexpected error occurred")
                display_error_in_element(analysis_error, error_target)
                return None
        
        return wrapper
    return decorator


class ProgressTracker:
    """
    Helper class to track and display progress for multi-step operations.
    
    Usage:
        tracker = ProgressTracker("output-div", total_steps=3)
        tracker.start("Generating code...")
        
        tracker.update(1, "Generating types...")
        # ... do work ...
        
        tracker.update(2, "Generating helpers...")
        # ... do work ...
        
        tracker.complete("Done!")
    """
    
    def __init__(self, element_id: str, total_steps: int = 100):
        """
        Initialize progress tracker.
        
        Args:
            element_id: ID of element to show progress in
            total_steps: Total number of steps (for percentage calculation)
        """
        self.element_id = element_id
        self.total_steps = total_steps
        self.current_step = 0
        self.is_running = False
    
    def start(self, message: str = "Starting..."):
        """
        Start the progress tracker.
        
        Args:
            message: Initial message to display
        """
        self.is_running = True
        self.current_step = 0
        update_progress(self.element_id, 0, message, "")
    
    def update(self, step: int, message: str = "", progress_text: str = ""):
        """
        Update progress.
        
        Args:
            step: Current step number
            message: Main message
            progress_text: Additional progress details
        """
        if not self.is_running:
            return
        
        self.current_step = step
        progress_pct = int((step / self.total_steps) * 100)
        update_progress(self.element_id, progress_pct, message, progress_text)
    
    def increment(self, message: str = "", progress_text: str = ""):
        """
        Increment progress by one step.
        
        Args:
            message: Main message
            progress_text: Additional progress details
        """
        self.update(self.current_step + 1, message, progress_text)
    
    def complete(self, message: str = "Complete!"):
        """
        Mark progress as complete.
        
        Args:
            message: Completion message
        """
        self.update(self.total_steps, message, "")
        self.is_running = False
    
    def error(self, error_message: str):
        """
        Display error and stop tracking.
        
        Args:
            error_message: Error message to display
        """
        from pyscript import document
        from components.error_handling import AnalysisError, display_error_in_element
        
        self.is_running = False
        error = AnalysisError(error_message, "Operation failed")
        display_error_in_element(error, self.element_id)


def run_with_progress(
    element_id: str,
    operation: Callable,
    steps: list[tuple[str, str]],
    on_complete: Optional[Callable] = None,
    on_error: Optional[Callable] = None
):
    """
    Run a multi-step operation with progress tracking.
    
    Args:
        element_id: ID of element to show progress in
        operation: Function to execute (receives tracker as argument)
        steps: List of (step_name, step_description) tuples
        on_complete: Optional callback when complete
        on_error: Optional error callback
        
    Usage:
        def my_operation(tracker):
            tracker.update(1, "Step 1...")
            # ... do work ...
            tracker.update(2, "Step 2...")
            # ... do work ...
            return result
        
        run_with_progress(
            "output-div",
            my_operation,
            [("Step 1", "Doing first thing"), ("Step 2", "Doing second thing")]
        )
    """
    tracker = ProgressTracker(element_id, total_steps=len(steps))
    
    try:
        tracker.start(f"Starting {len(steps)} steps...")
        result = operation(tracker)
        tracker.complete("Complete!")
        
        if on_complete:
            on_complete(result)
        
        return result
    
    except Exception as e:
        tracker.error(str(e))
        
        if on_error:
            on_error(e)
        
        raise


def defer_execution(func: Callable, delay_ms: int = 100) -> None:
    """
    Defer execution of a function to allow UI to update.
    
    This is useful in PyScript to ensure loading spinners are rendered
    before starting heavy computation.
    
    Args:
        func: Function to execute
        delay_ms: Delay in milliseconds (default: 100ms)
        
    Usage:
        show_loading("output-div", "Processing...")
        defer_execution(lambda: do_heavy_work(), 100)
    """
    import js
    
    def wrapper():
        try:
            func()
        except Exception as e:
            print(f"Error in deferred execution: {e}")
    
    js.setTimeout(wrapper, delay_ms)
