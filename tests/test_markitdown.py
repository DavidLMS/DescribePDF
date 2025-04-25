"""
Tests for the MarkItDown processor module of DescribePDF.

This module tests the integration with the MarkItDown library for
enhanced text extraction and markdown conversion from PDFs.
"""

from unittest.mock import MagicMock, patch

from describepdf import markitdown_processor

class TestMarkitdownProcessor:
    """Test suite for the Markitdown processor functionality."""

    def test_markitdown_not_available(self):
        """Test behavior when MarkItDown is not available."""
        # Setup test - ensure MARKITDOWN_AVAILABLE is False for this test
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', False):
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/temp.pdf")
            
            # Assert results
            assert result is None
            
            # Also test the is_available function
            assert markitdown_processor.is_available() is False

    def test_markitdown_file_not_found(self):
        """Test behavior when the temporary PDF file is not found."""
        # Setup test
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('os.path.exists', return_value=False):
            
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/nonexistent.pdf")
            
            # Assert results
            assert result is None

    def test_markitdown_converter_initialization_error(self):
        """Test handling when MarkItDown converter initialization fails."""
        # Setup test
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('os.path.exists', return_value=True), \
             patch('describepdf.markitdown_processor._get_markdown_converter', return_value=None):
            
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/valid.pdf")
            
            # Assert results
            assert result is None

    def test_markitdown_conversion_success(self):
        """Test successful conversion of PDF to Markdown with MarkItDown."""
        # Setup test
        mock_converter = MagicMock()
        mock_result = MagicMock()
        mock_result.text_content = "# Converted Markdown\n\nThis is the converted content."
        mock_converter.convert.return_value = mock_result
        
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('os.path.exists', return_value=True), \
             patch('describepdf.markitdown_processor._get_markdown_converter', return_value=mock_converter):
            
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/valid.pdf")
            
            # Assert results
            assert result == "# Converted Markdown\n\nThis is the converted content."
            mock_converter.convert.assert_called_once_with("/path/to/valid.pdf")

    def test_markitdown_conversion_exception(self):
        """Test handling of exceptions during MarkItDown conversion."""
        # Setup test
        mock_converter = MagicMock()
        mock_converter.convert.side_effect = Exception("Conversion error")
        
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('os.path.exists', return_value=True), \
             patch('describepdf.markitdown_processor._get_markdown_converter', return_value=mock_converter):
            
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/valid.pdf")
            
            # Assert results
            assert result is None
            mock_converter.convert.assert_called_once_with("/path/to/valid.pdf")

    def test_markitdown_empty_result(self):
        """Test handling when MarkItDown returns an empty result."""
        # Setup test
        mock_converter = MagicMock()
        mock_converter.convert.return_value = None
        
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('os.path.exists', return_value=True), \
             patch('describepdf.markitdown_processor._get_markdown_converter', return_value=mock_converter):
            
            # Execute test
            result = markitdown_processor.get_markdown_for_page_via_temp_pdf("/path/to/valid.pdf")
            
            # Assert results
            assert result == ""
            mock_converter.convert.assert_called_once_with("/path/to/valid.pdf")

    def test_get_markdown_converter_success(self):
        """Test successful creation of MarkItDown converter instance."""
        # Setup test
        mock_markitdown_class = MagicMock()
        mock_converter_instance = MagicMock()
        mock_markitdown_class.return_value = mock_converter_instance
        
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('describepdf.markitdown_processor.MarkItDown', mock_markitdown_class):
            
            # Execute test
            result = markitdown_processor._get_markdown_converter()
            
            # Assert results
            assert result == mock_converter_instance
            mock_markitdown_class.assert_called_once()

    def test_get_markdown_converter_exception(self):
        """Test handling of exceptions when creating MarkItDown converter."""
        # Setup test
        mock_markitdown_class = MagicMock(side_effect=Exception("Initialization error"))
        
        with patch('describepdf.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('describepdf.markitdown_processor.MarkItDown', mock_markitdown_class):
            
            # Execute test
            result = markitdown_processor._get_markdown_converter()
            
            # Assert results
            assert result is None
            mock_markitdown_class.assert_called_once()