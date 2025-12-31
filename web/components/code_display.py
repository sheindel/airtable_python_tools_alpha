"""Reusable code display components for consistent dark mode styling"""

from typing import Optional


def create_code_block(
    code: str,
    language: Optional[str] = None,
    show_copy_button: bool = False,
    copy_button_id: Optional[str] = None
) -> str:
    """
    Create a styled code block with consistent dark mode support.
    
    This helper ensures all code displays have proper text colors in both
    light and dark modes. Always use this instead of manually creating
    <pre><code> elements.
    
    Args:
        code: The code content to display
        language: Optional language hint (currently not used for syntax highlighting)
        show_copy_button: Whether to include a copy button overlay
        copy_button_id: ID for the copy button (required if show_copy_button=True)
    
    Returns:
        HTML string with properly styled code block
    
    Example:
        >>> html = create_code_block("const x = 42;", language="typescript")
        >>> html = create_code_block(sql, show_copy_button=True, copy_button_id="copy-sql-btn")
    """
    # Core code block with guaranteed dark mode text colors
    code_html = f"""<pre class="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto border border-gray-200 dark:border-gray-700"><code class="text-sm text-gray-800 dark:text-gray-200">{code}</code></pre>"""
    
    if show_copy_button:
        if not copy_button_id:
            raise ValueError("copy_button_id required when show_copy_button=True")
        
        return f"""
            <div class="relative">
                <button id="{copy_button_id}" 
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
                {code_html}
            </div>
        """
    
    return code_html


def create_inline_code(text: str) -> str:
    """
    Create an inline code element with consistent dark mode styling.
    
    Args:
        text: The text to display as inline code
    
    Returns:
        HTML string with styled inline code element
    
    Example:
        >>> html = f"The function {create_inline_code('getData()')} returns..."
    """
    return f'<code class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded text-sm font-mono">{text}</code>'


def create_result_card(
    title: str,
    content: str,
    card_type: str = "info"
) -> str:
    """
    Create a styled result card with consistent dark mode support.
    
    Args:
        title: Card title/heading
        content: Card content (can include HTML)
        card_type: Type of card - "info", "success", "warning", "error"
    
    Returns:
        HTML string with styled card
    
    Example:
        >>> html = create_result_card("Generated Schema", sql_code, "success")
    """
    type_classes = {
        "info": "border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20",
        "success": "border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20",
        "warning": "border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/20",
        "error": "border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20"
    }
    
    card_class = type_classes.get(card_type, type_classes["info"])
    
    return f"""
        <div class="border-2 {card_class} rounded-lg p-4 transition-colors duration-200">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">{title}</h3>
            <div class="text-gray-700 dark:text-gray-300">
                {content}
            </div>
        </div>
    """


# Standard class combinations for consistency
CODE_BLOCK_CLASSES = "bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-x-auto border border-gray-200 dark:border-gray-700"
CODE_TEXT_CLASSES = "text-sm text-gray-800 dark:text-gray-200"
INLINE_CODE_CLASSES = "px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded text-sm font-mono"
