"""
Tests for the core module of DescribePDF.

This module tests the main orchestration logic for converting PDFs to Markdown descriptions.
"""

from unittest.mock import patch, MagicMock, call

from describepdf import core

class TestCore:
    """Test suite for the core functionality."""

    def test_format_markdown_output(self):
        """Test formatting of page descriptions into a complete Markdown document."""
        # Setup test data
        descriptions = [
            "Description of page 1 with some content.",
            "Description of page 2 with different content.",
            ""  # Empty description for page 3
        ]
        filename = "test_document.pdf"
        
        # Execute test
        result = core.format_markdown_output(descriptions, filename)
        
        # Assert results
        assert "# Description of PDF: test_document.pdf" in result
        assert "## Page 1" in result
        assert "Description of page 1 with some content." in result
        assert "## Page 2" in result
        assert "Description of page 2 with different content." in result
        assert "## Page 3" in result
        assert "*No description generated for this page.*" in result
        assert "---" in result  # Check for separators

    def test_convert_pdf_to_markdown_invalid_provider(self):
        """Test handling of invalid provider."""
        # Setup test
        config = {"provider": "invalid_provider"}
        progress_callback = MagicMock()
        
        # Execute test
        status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
        
        # Assert results
        assert result is None
        assert "Unknown provider" in status
        progress_callback.assert_called_once_with(0.0, "Error: Unknown provider 'invalid_provider'. Use 'openrouter' or 'ollama'.")

    def test_convert_pdf_to_markdown_missing_api_key(self):
        """Test handling of missing OpenRouter API key."""
        # Setup test
        config = {"provider": "openrouter", "openrouter_api_key": None}
        progress_callback = MagicMock()
        
        # Execute test
        status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
        
        # Assert results
        assert result is None
        assert "API Key is missing" in status
        progress_callback.assert_called_once_with(0.0, "Error: OpenRouter API Key is missing.")

    def test_convert_pdf_to_markdown_ollama_not_available(self):
        """Test handling when Ollama client is not available."""
        # Setup test
        config = {"provider": "ollama", "ollama_endpoint": "http://localhost:11434"}
        progress_callback = MagicMock()
        
        with patch('describepdf.core.ollama_client.OLLAMA_AVAILABLE', False):
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "Ollama Python client not installed" in status
            progress_callback.assert_called_once_with(0.0, "Error: Ollama Python client not installed. Install with 'pip install ollama'.")

    def test_convert_pdf_to_markdown_ollama_not_running(self):
        """Test handling when Ollama server is not running."""
        # Setup test
        config = {"provider": "ollama", "ollama_endpoint": "http://localhost:11434"}
        progress_callback = MagicMock()
        
        with patch('describepdf.core.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.core.ollama_client.check_ollama_availability', return_value=False):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "Could not connect to Ollama" in status
            progress_callback.assert_called_once()

    def test_convert_pdf_to_markdown_invalid_pdf(self):
        """Test handling of invalid or missing PDF file."""
        # Setup test
        config = {"provider": "openrouter", "openrouter_api_key": "test_key"}
        progress_callback = MagicMock()
        
        with patch('os.path.exists', return_value=False):
            # Execute test
            status, result = core.convert_pdf_to_markdown("nonexistent.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "Invalid or missing PDF file" in status
            progress_callback.assert_called_once_with(0.0, "Error: Invalid or missing PDF file.")

    def test_convert_pdf_to_markdown_missing_prompts(self):
        """Test handling when required prompt templates are missing."""
        # Setup test
        config = {"provider": "openrouter", "openrouter_api_key": "test_key"}
        progress_callback = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', return_value={}):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "Could not load all required prompt templates" in status

    def test_convert_pdf_to_markdown_summary_generation_success(self):
        """Test successful summary generation during conversion."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "use_summary": True,
            "summary_llm_model": "test_model"
        }
        progress_callback = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Test prompt", "summary": "Summary prompt"}), \
             patch('describepdf.core.summarizer.generate_summary', return_value="Generated summary"):
            
            # Mock PDF loading to fail after summary to simplify test
            with patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(None, None, 0)):
                # Execute test
                status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
                
                # Assert results
                assert result is None  # Test fails at PDF loading
                core.summarizer.generate_summary.assert_called_once_with(
                    "test.pdf", 
                    provider="openrouter", 
                    api_key="test_key", 
                    ollama_endpoint=None, 
                    model="test_model"
                )

    def test_convert_pdf_to_markdown_summary_generation_failure(self):
        """Test handling when summary generation fails but conversion continues."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "use_summary": True,
            "summary_llm_model": "test_model"
        }
        progress_callback = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Test prompt"}), \
             patch('describepdf.core.summarizer.generate_summary', return_value=None):
            
            # Mock PDF loading to fail after summary to simplify test
            with patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(None, None, 0)):
                # Execute test
                status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
                
                # Assert results
                assert result is None  # Test fails at PDF loading
                assert config["use_summary"] is False  # Should be set to False when summary fails
                core.summarizer.generate_summary.assert_called_once()

    def test_convert_pdf_to_markdown_pdf_load_failure(self):
        """Test handling when PDF loading fails."""
        # Setup test
        config = {"provider": "openrouter", "openrouter_api_key": "test_key"}
        progress_callback = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Test prompt"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(None, None, 0)):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "Could not process PDF file" in status

    def test_convert_pdf_to_markdown_pdf_empty(self):
        """Test handling when PDF is empty (zero pages)."""
        # Setup test
        config = {"provider": "openrouter", "openrouter_api_key": "test_key"}
        progress_callback = MagicMock()
        mock_doc = MagicMock()
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Test prompt"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(mock_doc, [], 0)):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "PDF file is empty" in status
            mock_doc.close.assert_called_once()  # Ensure document is closed

    def test_convert_pdf_to_markdown_full_success(self):
        """Test successful conversion of PDF to Markdown with all steps."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "vlm_model": "test_model",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False
        }
        progress_callback = MagicMock()
        
        # Create mock document and pages
        mock_doc = MagicMock()
        mock_page1 = MagicMock(number=0)
        mock_page2 = MagicMock(number=1)
        mock_pages = [mock_page1, mock_page2]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Describe page [PAGE_NUM] in [LANGUAGE]:"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(mock_doc, mock_pages, 2)), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', 
                   return_value=(b"image_data", "image/jpeg")), \
             patch('describepdf.core.openrouter_client.get_vlm_description', 
                   side_effect=["Description for page 1", "Description for page 2"]):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is not None
            assert "Conversion completed successfully" in status
            assert "# Description of PDF: test.pdf" in result
            assert "## Page 1" in result
            assert "Description for page 1" in result
            assert "## Page 2" in result
            assert "Description for page 2" in result
            
            # Verify VLM was called for each page
            assert core.openrouter_client.get_vlm_description.call_count == 2
            
            # Verify document was closed
            mock_doc.close.assert_called_once()

    def test_convert_pdf_to_markdown_partial_success(self):
        """Test partial success in conversion when some pages fail."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "vlm_model": "test_model",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False
        }
        progress_callback = MagicMock()
        
        # Create mock document and pages
        mock_doc = MagicMock()
        mock_page1 = MagicMock(number=0)
        mock_page2 = MagicMock(number=1)
        mock_pages = [mock_page1, mock_page2]
        
        # First page renders successfully, second page fails to render
        def mock_render_page(page, *args, **kwargs):
            if page.number == 0:
                return (b"image_data", "image/jpeg")
            else:
                return (None, None)
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Describe page [PAGE_NUM] in [LANGUAGE]:"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(mock_doc, mock_pages, 2)), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', side_effect=mock_render_page), \
             patch('describepdf.core.openrouter_client.get_vlm_description', return_value="Description for page 1"):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is not None
            assert "Conversion completed successfully" in status
            assert "# Description of PDF: test.pdf" in result
            assert "## Page 1" in result
            assert "Description for page 1" in result
            assert "## Page 2" in result
            assert "*Error: Could not render image for page 2*" in result
            
            # Verify VLM was called only for the successful page
            assert core.openrouter_client.get_vlm_description.call_count == 1
            
            # Verify document was closed
            mock_doc.close.assert_called_once()

    def test_convert_pdf_to_markdown_with_markitdown(self):
        """Test conversion with Markitdown enhanced text extraction."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "vlm_model": "test_model",
            "output_language": "English",
            "use_markitdown": True,
            "use_summary": False
        }
        progress_callback = MagicMock()
        
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock(number=0)
        mock_pages = [mock_page]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Base prompt", "vlm_markdown": "Markdown prompt: [MARKDOWN_CONTEXT]"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(mock_doc, mock_pages, 1)), \
             patch('describepdf.core.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', return_value=(b"image_data", "image/jpeg")), \
             patch('describepdf.core.pdf_processor.save_page_as_temp_pdf', return_value="/tmp/temp_page.pdf"), \
             patch('describepdf.core.markitdown_processor.get_markdown_for_page_via_temp_pdf', 
                   return_value="Extracted markdown content"), \
             patch('describepdf.core.openrouter_client.get_vlm_description', return_value="Description with markdown context"), \
             patch('os.remove') as mock_remove:
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is not None
            assert "Conversion completed successfully" in status
            assert "# Description of PDF: test.pdf" in result
            assert "Description with markdown context" in result
            
            # Verify markitdown extraction was called
            core.markitdown_processor.get_markdown_for_page_via_temp_pdf.assert_called_once_with("/tmp/temp_page.pdf")
            
            # Verify temp file was removed
            mock_remove.assert_called_once_with("/tmp/temp_page.pdf")
            
            # Verify VLM was called with the markdown prompt
            core.openrouter_client.get_vlm_description.assert_called_once()
            args = core.openrouter_client.get_vlm_description.call_args[0]
            assert "Extracted markdown content" in args[2]  # Check that markdown was included in prompt

    def test_convert_pdf_to_markdown_api_critical_error(self):
        """Test handling of critical API errors during conversion."""
        # Setup test
        config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_key",
            "vlm_model": "test_model",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False
        }
        progress_callback = MagicMock()
        
        # Create mock document and page
        mock_doc = MagicMock()
        mock_page = MagicMock(number=0)
        mock_pages = [mock_page]
        
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.config.get_required_prompts_for_config', 
                   return_value={"vlm_base": "Test prompt"}), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', return_value=(mock_doc, mock_pages, 1)), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', return_value=(b"image_data", "image/jpeg")), \
             patch('describepdf.core.openrouter_client.get_vlm_description', 
                   side_effect=ValueError("Critical API error")):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown("test.pdf", config, progress_callback)
            
            # Assert results
            assert result is None
            assert "API Error" in status
            
            # Verify document was closed
            mock_doc.close.assert_called_once()