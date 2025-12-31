"""Tests for code display helper components"""

import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from components.code_display import (
    create_code_block,
    create_inline_code,
    create_result_card,
    CODE_BLOCK_CLASSES,
    CODE_TEXT_CLASSES,
    INLINE_CODE_CLASSES
)
import pytest


class TestCreateCodeBlock:
    """Tests for create_code_block function"""
    
    def test_simple_code_block(self):
        """Test creating a simple code block"""
        code = "const x = 42;"
        result = create_code_block(code)
        
        # Should contain the code
        assert code in result
        
        # Should have proper dark mode text colors
        assert "text-gray-800" in result
        assert "dark:text-gray-200" in result
        
        # Should have background styling
        assert "dark:bg-gray-900" in result
        
    def test_code_block_with_copy_button(self):
        """Test creating code block with copy button"""
        code = "SELECT * FROM users;"
        button_id = "copy-sql-btn"
        result = create_code_block(code, show_copy_button=True, copy_button_id=button_id)
        
        # Should contain the code
        assert code in result
        
        # Should have copy button
        assert button_id in result
        assert 'title="Copy to clipboard"' in result
        assert "backdrop-filter: blur(4px)" in result
        
        # Should have relative container
        assert '<div class="relative">' in result
        
    def test_code_block_missing_button_id(self):
        """Test that copy button requires button ID"""
        with pytest.raises(ValueError, match="copy_button_id required"):
            create_code_block("code", show_copy_button=True)
            
    def test_dark_mode_classes_always_present(self):
        """Test that dark mode text colors are always included"""
        code = "print('hello')"
        result = create_code_block(code)
        
        # These classes MUST be present to avoid black text on dark background
        assert "text-gray-800" in result
        assert "dark:text-gray-200" in result
        

class TestCreateInlineCode:
    """Tests for create_inline_code function"""
    
    def test_inline_code(self):
        """Test creating inline code element"""
        text = "getData()"
        result = create_inline_code(text)
        
        # Should contain the text
        assert text in result
        
        # Should have inline styling
        assert "px-1.5" in result
        assert "py-0.5" in result
        
        # Should have dark mode colors
        assert "dark:bg-gray-800" in result
        assert "dark:text-gray-200" in result
        
        # Should be a code element
        assert result.startswith("<code")
        assert result.endswith("</code>")


class TestCreateResultCard:
    """Tests for create_result_card function"""
    
    def test_info_card(self):
        """Test creating an info card"""
        title = "Test Result"
        content = "This is the content"
        result = create_result_card(title, content, card_type="info")
        
        assert title in result
        assert content in result
        assert "border-blue-200" in result
        assert "dark:border-blue-800" in result
        
    def test_success_card(self):
        """Test creating a success card"""
        result = create_result_card("Success", "It worked", card_type="success")
        
        assert "border-green-200" in result
        assert "dark:border-green-800" in result
        
    def test_warning_card(self):
        """Test creating a warning card"""
        result = create_result_card("Warning", "Be careful", card_type="warning")
        
        assert "border-yellow-200" in result
        assert "dark:border-yellow-800" in result
        
    def test_error_card(self):
        """Test creating an error card"""
        result = create_result_card("Error", "Something failed", card_type="error")
        
        assert "border-red-200" in result
        assert "dark:border-red-800" in result
        
    def test_default_card_type(self):
        """Test that unknown card type defaults to info"""
        result = create_result_card("Title", "Content", card_type="unknown")
        
        assert "border-blue-200" in result
        
    def test_dark_mode_text_in_card(self):
        """Test that cards include dark mode text colors"""
        result = create_result_card("Title", "Content")
        
        # Title should have dark mode color
        assert "dark:text-white" in result
        
        # Content should have dark mode color
        assert "dark:text-gray-300" in result


class TestClassConstants:
    """Tests for exported class constants"""
    
    def test_code_block_classes_exist(self):
        """Test that CODE_BLOCK_CLASSES is defined"""
        assert isinstance(CODE_BLOCK_CLASSES, str)
        assert "dark:bg-gray-900" in CODE_BLOCK_CLASSES
        
    def test_code_text_classes_exist(self):
        """Test that CODE_TEXT_CLASSES is defined"""
        assert isinstance(CODE_TEXT_CLASSES, str)
        assert "text-gray-800" in CODE_TEXT_CLASSES
        assert "dark:text-gray-200" in CODE_TEXT_CLASSES
        
    def test_inline_code_classes_exist(self):
        """Test that INLINE_CODE_CLASSES is defined"""
        assert isinstance(INLINE_CODE_CLASSES, str)
        assert "dark:text-gray-200" in INLINE_CODE_CLASSES
