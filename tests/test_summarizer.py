"""
Tests for the summarizer module of DescribePDF.

This module tests the generation of document summaries from PDF text content
using either OpenRouter or Ollama LLM models.
"""

from unittest.mock import patch

from describepdf import summarizer

class TestSummarizer:
    """Test suite for the summarizer functionality."""

    def test_generate_summary_extract_text_error(self):
        """Test handling when text extraction from PDF fails."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value=None):
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_empty_text(self):
        """Test handling when PDF contains no extractable text."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value=""):
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result == "Document contains no extractable text."

    def test_generate_summary_prompt_not_found(self):
        """Test handling when summary prompt template is not found."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={}):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_text_truncation(self):
        """Test truncation of text when it exceeds the maximum length."""
        # Setup test
        long_text = "a" * (summarizer.MAX_CHARS_FOR_PROMPT + 1000)  # Text longer than the limit
        
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value=long_text),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.openrouter_client.get_llm_summary') as mock_get_summary:
            
            # Configure mock to return a predefined summary
            mock_get_summary.return_value = "This is a summary."
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result == "This is a summary."
            
            # Verify summary was called with truncated text
            call_args = mock_get_summary.call_args[0]
            prompt_text = call_args[2]
            assert "Summarize: " in prompt_text
            assert "[... text truncated ...]" in prompt_text
            assert len(prompt_text) <= summarizer.MAX_CHARS_FOR_PROMPT + 100  # Allow for prompt template text

    def test_generate_summary_openrouter_success(self):
        """Test successful summary generation using OpenRouter."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.openrouter_client.get_llm_summary', return_value="Generated summary."):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result == "Generated summary."
            
            # Verify OpenRouter client was called correctly
            summarizer.openrouter_client.get_llm_summary.assert_called_once_with(
                "test_api_key", "test_model", "Summarize: Text content"
            )

    def test_generate_summary_ollama_success(self):
        """Test successful summary generation using Ollama."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.ollama_client.get_llm_summary', return_value="Generated summary."):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="ollama",
                ollama_endpoint="http://localhost:11434",
                model="test_model"
            )
            
            # Assert results
            assert result == "Generated summary."
            
            # Verify Ollama client was called correctly
            summarizer.ollama_client.get_llm_summary.assert_called_once_with(
                "http://localhost:11434", "test_model", "Summarize: Text content"
            )

    def test_generate_summary_openrouter_missing_api_key(self):
        """Test handling when OpenRouter API key is missing."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key=None,
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_ollama_missing_endpoint(self):
        """Test handling when Ollama endpoint URL is missing."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="ollama",
                ollama_endpoint=None,
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_unsupported_provider(self):
        """Test handling of unsupported provider."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="unsupported_provider",
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_value_error(self):
        """Test handling of ValueError during summary generation."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.openrouter_client.get_llm_summary', side_effect=ValueError("API Error")):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_connection_error(self):
        """Test handling of ConnectionError during summary generation."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.openrouter_client.get_llm_summary', side_effect=ConnectionError("Connection failed")):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result is None

    def test_generate_summary_timeout_error(self):
        """Test handling of TimeoutError during summary generation."""
        # Setup test
        with patch('describepdf.summarizer.pdf_processor.extract_all_text', return_value="Text content"),\
             patch('describepdf.summarizer.get_prompts', return_value={"summary": "Summarize: [FULL_PDF_TEXT]"}),\
             patch('describepdf.summarizer.openrouter_client.get_llm_summary', side_effect=TimeoutError("Request timed out")):
            
            # Execute test
            result = summarizer.generate_summary(
                "test.pdf",
                provider="openrouter",
                api_key="test_api_key",
                model="test_model"
            )
            
            # Assert results
            assert result is None