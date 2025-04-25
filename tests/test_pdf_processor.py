"""
Tests for the PDF processor module of DescribePDF.

This module tests the functionality for handling PDF files, including
opening, rendering, text extraction, and page manipulation.
"""

from unittest.mock import MagicMock, patch

# Import module under test
from describepdf import pdf_processor

class TestPDFProcessor:
    """Test suite for the PDF processor functionality."""

    def test_get_pdf_pages_success(self, mock_pymupdf, temp_pdf_file):
        """Test successful opening of a PDF and retrieval of pages."""
        # Setup test
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 3
        mock_page1, mock_page2, mock_page3 = MagicMock(), MagicMock(), MagicMock()
        mock_doc.load_page.side_effect = [mock_page1, mock_page2, mock_page3]
        mock_pymupdf.open.return_value = mock_doc

        # Execute test
        doc, pages, total_pages = pdf_processor.get_pdf_pages(temp_pdf_file)

        # Assert results
        assert doc == mock_doc
        assert len(pages) == 3
        assert total_pages == 3
        mock_pymupdf.open.assert_called_once_with(temp_pdf_file)

    def test_get_pdf_pages_file_not_found(self, mock_pymupdf):
        """Test handling of non-existent PDF file."""
        # Setup test
        mock_pymupdf.open.side_effect = FileNotFoundError("File not found")

        # Execute test
        doc, pages, total_pages = pdf_processor.get_pdf_pages("nonexistent.pdf")

        # Assert results
        assert doc is None
        assert pages is None
        assert total_pages == 0

    def test_render_page_to_image_bytes_png(self, mock_pymupdf, sample_image_bytes):
        """Test rendering a page to PNG image bytes."""
        # Setup test
        mock_page = MagicMock()
        mock_page.number = 0
        mock_pixmap = MagicMock()
        mock_pixmap.tobytes.return_value = sample_image_bytes
        mock_page.get_pixmap.return_value = mock_pixmap

        # Test PNG format
        with patch('describepdf.pdf_processor.PIL_AVAILABLE', True):
            # Execute test
            image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(mock_page, "png")

            # Assert results
            assert image_bytes == sample_image_bytes
            assert mime_type == "image/png"
            mock_page.get_pixmap.assert_called_once()
            mock_pixmap.tobytes.assert_called_once_with("png")

    def test_render_page_to_image_bytes_jpeg(self, mock_pymupdf, sample_image_bytes):
        """Test rendering a page to JPEG image bytes."""
        # Setup test
        mock_page = MagicMock()
        mock_page.number = 0
        mock_pixmap = MagicMock()
        mock_pixmap.samples = b"sample_image_data"
        mock_pixmap.width = 100
        mock_pixmap.height = 100
        mock_page.get_pixmap.return_value = mock_pixmap

        # Mock PIL Image
        mock_pil_image = MagicMock()
        mock_pil_image.save.side_effect = lambda io_buf, format, quality: io_buf.write(sample_image_bytes)

        # Test JPEG format with PIL
        with patch('describepdf.pdf_processor.PIL_AVAILABLE', True), \
             patch('describepdf.pdf_processor.Image.frombytes', return_value=mock_pil_image):
            
            # Execute test
            image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(mock_page, "jpeg")

            # Assert results
            assert image_bytes == sample_image_bytes
            assert mime_type == "image/jpeg"
            mock_page.get_pixmap.assert_called_once()

    def test_render_page_invalid_format(self, mock_pymupdf):
        """Test handling of invalid image format."""
        # Setup test
        mock_page = MagicMock()

        # Execute test
        image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(mock_page, "invalid_format")

        # Assert results
        assert image_bytes is None
        assert mime_type is None
        
    def test_extract_all_text(self, mock_pymupdf, temp_pdf_file):
        """Test extraction of text from a PDF file."""
        # Setup test
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_page1, mock_page2 = MagicMock(), MagicMock()
        mock_page1.get_text.return_value = "Text from page 1"
        mock_page2.get_text.return_value = "Text from page 2"
        mock_doc.load_page.side_effect = [mock_page1, mock_page2]
        
        with patch.object(mock_pymupdf, 'open', return_value=mock_doc):
            # Execute test
            result = pdf_processor.extract_all_text(temp_pdf_file)

            # Assert results
            assert result == "Text from page 1\n\nText from page 2\n\n"
            mock_pymupdf.open.assert_called_once_with(temp_pdf_file)
            assert mock_doc.load_page.call_count == 2
            mock_page1.get_text.assert_called_once_with("text")
            mock_page2.get_text.assert_called_once_with("text")

    def test_save_page_as_temp_pdf(self, mock_pymupdf):
        """Test saving a single page as a temporary PDF file."""
        # Setup test
        mock_orig_doc = MagicMock()
        mock_new_doc = MagicMock()
        mock_pymupdf.open.return_value = mock_new_doc
        
        # Mock tempfile.NamedTemporaryFile
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_page.pdf"
        
        with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file), \
             patch('os.path.exists', return_value=True):
            
            # Execute test
            result = pdf_processor.save_page_as_temp_pdf(mock_orig_doc, 1)
            
            # Assert results
            assert result == "/tmp/test_page.pdf"
            mock_pymupdf.open.assert_called_once()
            mock_new_doc.insert_pdf.assert_called_once_with(mock_orig_doc, from_page=1, to_page=1)
            mock_new_doc.save.assert_called_once_with("/tmp/test_page.pdf")
            mock_new_doc.close.assert_called_once()
            
    def test_save_page_as_temp_pdf_error(self, mock_pymupdf):
        """Test error handling when saving a page as temporary PDF fails."""
        # Setup test
        mock_orig_doc = MagicMock()
        mock_new_doc = MagicMock()
        mock_pymupdf.open.return_value = mock_new_doc
        mock_new_doc.insert_pdf.side_effect = Exception("PDF creation error")
        
        # Mock tempfile.NamedTemporaryFile
        mock_temp_file = MagicMock()
        mock_temp_file.name = "/tmp/test_page.pdf"
        
        with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            # Execute test
            result = pdf_processor.save_page_as_temp_pdf(mock_orig_doc, 1)
            
            # Assert results
            assert result is None
            mock_pymupdf.open.assert_called_once()
            mock_new_doc.insert_pdf.assert_called_once_with(mock_orig_doc, from_page=1, to_page=1)
            mock_remove.assert_called_once_with("/tmp/test_page.pdf")