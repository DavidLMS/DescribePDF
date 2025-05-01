"""
Integration tests for DescribePDF.

This module contains integration tests that verify multiple components 
working together correctly.
"""

from unittest.mock import patch, MagicMock

from describepdf import core

class TestIntegration:
    """Test suite for integration testing across multiple components."""

    def test_end_to_end_openrouter_flow(self, temp_pdf_file, sample_image_bytes, mock_openrouter_response, mock_config):
        """Test full conversion flow with OpenRouter provider."""
        # Setup test
        test_config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_api_key",
            "vlm_model": "qwen/qwen2.5-vl-72b-instruct",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False
        }
        
        # Mock progress callback
        progress_callback = MagicMock()
        
        # Mock document and pages
        mock_doc = MagicMock()
        mock_page = MagicMock(number=0)
        
        # Set up all required mocks for a successful flow
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', 
                   return_value=(mock_doc, [mock_page], 1)), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', 
                   return_value=(sample_image_bytes, "image/jpeg")), \
             patch('describepdf.core.openrouter_client.encode_image_to_base64',
                   return_value="data:image/jpeg;base64,encoded_image"), \
             patch('describepdf.core.openrouter_client.call_openrouter_api',
                   return_value=mock_openrouter_response):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown(temp_pdf_file, test_config, progress_callback)
            
            # Assert results
            assert status.startswith("Conversion completed successfully")
            assert result is not None
            assert "# Description of PDF:" in result
            assert "## Page 1" in result
            
            # Extract the page description from the mock response
            expected_content = mock_openrouter_response["choices"][0]["message"]["content"]
            assert expected_content in result

    def test_end_to_end_ollama_flow(self, temp_pdf_file, sample_image_bytes, mock_ollama_response, mock_config):
        """Test full conversion flow with Ollama provider."""
        # Setup test
        test_config = {
            "provider": "ollama",
            "ollama_endpoint": "http://localhost:11434",
            "vlm_model": "llama3.2-vision",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False
        }
        
        # Mock progress callback
        progress_callback = MagicMock()
        
        # Mock document and pages
        mock_doc = MagicMock()
        mock_page = MagicMock(number=0)
        
        # Set up all required mocks for a successful flow
        with patch('describepdf.core.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.core.ollama_client.check_ollama_availability', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', 
                   return_value=(mock_doc, [mock_page], 1)), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', 
                   return_value=(sample_image_bytes, "image/jpeg")), \
             patch('describepdf.core.ollama_client.Client', return_value=MagicMock()), \
             patch('base64.b64encode', return_value=b'encoded_image_data'), \
             patch('base64.b64encode().decode', return_value='encoded_image_data'), \
             patch('describepdf.core.ollama_client.get_vlm_description',
                   return_value=mock_ollama_response["message"]["content"]):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown(temp_pdf_file, test_config, progress_callback)
            
            # Assert results
            assert status.startswith("Conversion completed successfully")
            assert result is not None
            assert "# Description of PDF:" in result
            assert "## Page 1" in result
            
            # Extract the page description from the mock response
            expected_content = mock_ollama_response["message"]["content"]
            assert expected_content in result

    def test_with_summary_and_markitdown(self, temp_pdf_file, sample_image_bytes, 
                                         sample_markdown_content, mock_openrouter_response, mock_config):
        """Test conversion with both summary and Markitdown enabled."""
        # Setup test
        test_config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_api_key",
            "vlm_model": "qwen/qwen2.5-vl-72b-instruct",
            "output_language": "English",
            "use_markitdown": True,
            "use_summary": True,
            "summary_llm_model": "google/gemini-2.5-flash-preview"
        }
        
        # Mock progress callback
        progress_callback = MagicMock()
        
        # Mock document and pages
        mock_doc = MagicMock()
        mock_page = MagicMock(number=0)
        
        # Set up all required mocks for a successful flow with summary and markitdown
        with patch('os.path.exists', return_value=True), \
             patch('os.path.isfile', return_value=True), \
             patch('describepdf.core.summarizer.generate_summary', 
                   return_value="This is a test document summary."), \
             patch('describepdf.core.pdf_processor.get_pdf_pages', 
                   return_value=(mock_doc, [mock_page], 1)), \
             patch('describepdf.core.markitdown_processor.MARKITDOWN_AVAILABLE', True), \
             patch('describepdf.core.config.get_required_prompts_for_config',
                   return_value={
                       "vlm_base": "Base prompt",
                       "vlm_full": "Full prompt with [MARKDOWN_CONTEXT] and [SUMMARY_CONTEXT]",
                       "summary": "Summary prompt"
                   }), \
             patch('describepdf.core.pdf_processor.render_page_to_image_bytes', 
                   return_value=(sample_image_bytes, "image/jpeg")), \
             patch('describepdf.core.pdf_processor.save_page_as_temp_pdf', 
                   return_value="/tmp/temp_page.pdf"), \
             patch('describepdf.core.markitdown_processor.get_markdown_for_page_via_temp_pdf', 
                   return_value=sample_markdown_content), \
             patch('describepdf.core.openrouter_client.get_vlm_description', 
                   return_value="Description with both markdown and summary context."), \
             patch('os.remove'):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown(temp_pdf_file, test_config, progress_callback)
            
            # Assert results
            assert status.startswith("Conversion completed successfully")
            assert result is not None
            assert "# Description of PDF:" in result
            assert "## Page 1" in result
            assert "Description with both markdown and summary context." in result
            
            # Verify summarizer was called
            core.summarizer.generate_summary.assert_called_once()
            
            # Verify markitdown was used
            core.markitdown_processor.get_markdown_for_page_via_temp_pdf.assert_called_once()
            
            # Verify VLM was called with the correct prompt
            core.openrouter_client.get_vlm_description.assert_called_once()
            args = core.openrouter_client.get_vlm_description.call_args[0]
            # The prompt should contain both markdown and summary context
            assert "Full prompt with" in args[2]
      
    def test_end_to_end_with_page_selection(self, temp_pdf_file, sample_image_bytes, mock_openrouter_response, mock_config):
      """Test full conversion flow with page selection."""
      # Setup test
      test_config = {
            "provider": "openrouter",
            "openrouter_api_key": "test_api_key",
            "vlm_model": "qwen/qwen2.5-vl-72b-instruct",
            "output_language": "English",
            "use_markitdown": False,
            "use_summary": False,
            "page_selection": "1,3"
      }
      
      # Mock progress callback
      progress_callback = MagicMock()
      
      # Mock document and pages
      mock_doc = MagicMock()
      mock_page1 = MagicMock(number=0)
      mock_page2 = MagicMock(number=1)
      mock_page3 = MagicMock(number=2)
      
      # Set up all required mocks for a successful flow
      with patch('os.path.exists', return_value=True), \
            patch('os.path.isfile', return_value=True), \
            patch('describepdf.core.pdf_processor.get_pdf_pages', 
                  return_value=(mock_doc, [mock_page1, mock_page2, mock_page3], 3)), \
            patch('describepdf.core.pdf_processor.render_page_to_image_bytes', 
                  return_value=(sample_image_bytes, "image/jpeg")), \
            patch('describepdf.core.openrouter_client.encode_image_to_base64',
                  return_value="data:image/jpeg;base64,encoded_image"), \
            patch('describepdf.core.openrouter_client.call_openrouter_api',
                  return_value=mock_openrouter_response):
            
            # Execute test
            status, result = core.convert_pdf_to_markdown(temp_pdf_file, test_config, progress_callback)
            
            # Assert results
            assert status.startswith("Conversion completed successfully")
            assert result is not None
            
            assert "## Page 1" in result
            assert "## Page 3" in result
            assert "## Page 2" not in result