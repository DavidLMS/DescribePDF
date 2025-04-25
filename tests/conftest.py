"""
Shared pytest fixtures for DescribePDF tests.

This module provides common fixtures used across multiple test modules.
"""

import os
import pytest
import tempfile
from unittest.mock import MagicMock, patch

# Define sample test data as fixtures
@pytest.fixture
def sample_pdf_content():
    """Return a small sample of binary data to simulate a PDF file."""
    # This is not actually a valid PDF, just a binary stub for testing
    return b"%PDF-1.7\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"

@pytest.fixture
def sample_image_bytes():
    """Return sample image bytes for testing the PDF renderer."""
    # This is not an actual image, just bytes for testing function calls
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

@pytest.fixture
def sample_markdown_content():
    """Return sample Markdown content for testing."""
    return """# Sample Header

This is a paragraph of text for testing.

- List item 1
- List item 2

## Subheader

More content for testing purposes.
"""

@pytest.fixture
def temp_pdf_file(sample_pdf_content):
    """Create a temporary PDF file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(sample_pdf_content)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Cleanup after test
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

@pytest.fixture
def mock_pymupdf():
    """Mock the PyMuPDF module for testing PDF operations."""
    # Create mock document
    mock_doc = MagicMock()
    mock_doc.__len__.return_value = 2  # Simulate 2 pages
    
    # Create mock pages
    mock_page1 = MagicMock()
    mock_page1.number = 0
    mock_page2 = MagicMock()
    mock_page2.number = 1
    
    # Setup mock PyMuPDF open function
    mock_open = MagicMock(return_value=mock_doc)
    
    # Mock document loading pages
    mock_doc.load_page.side_effect = lambda i: mock_page1 if i == 0 else mock_page2
    
    # Patch PyMuPDF
    with patch.dict('sys.modules', {'pymupdf': MagicMock()}):
        import sys
        sys.modules['pymupdf'].open = mock_open
        sys.modules['pymupdf'].Document = MagicMock
        sys.modules['pymupdf'].Page = MagicMock
        
        # Create an environment variable to indicate tests are running with mock
        os.environ['DESCRIBEPDF_TESTING'] = 'true'
        
        yield sys.modules['pymupdf']
        
        # Clean up
        if 'DESCRIBEPDF_TESTING' in os.environ:
            del os.environ['DESCRIBEPDF_TESTING']

@pytest.fixture
def mock_openrouter_response():
    """Return a mock OpenRouter API response."""
    return {
        "id": "gen_123",
        "model": "qwen/qwen2.5-vl-72b-instruct",
        "created": 1619644760,
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This page contains a header with the title 'DescribePDF' and a subtitle describing it as a tool to convert PDF files to Markdown descriptions using vision-language models."
                },
                "finish_reason": "stop",
                "index": 0
            }
        ],
        "usage": {
            "prompt_tokens": 250,
            "completion_tokens": 130,
            "total_tokens": 380
        }
    }

@pytest.fixture
def mock_ollama_response():
    """Return a mock Ollama API response."""
    return {
        "model": "llama3.2-vision",
        "created_at": "2023-11-04T12:34:56.789Z",
        "message": {
            "role": "assistant",
            "content": "This page shows a diagram of the application architecture with boxes representing different components and arrows showing the flow of data between them."
        },
        "done": True
    }

@pytest.fixture
def env_config_dict():
    """Return a sample environment configuration dictionary."""
    return {
        "openrouter_api_key": "test_api_key_12345",
        "or_vlm_model": "qwen/qwen2.5-vl-72b-instruct",
        "or_summary_model": "google/gemini-2.5-flash-preview",
        "ollama_endpoint": "http://localhost:11434",
        "ollama_vlm_model": "llama3.2-vision",
        "ollama_summary_model": "qwen2.5",
        "output_language": "English",
        "use_markitdown": False,
        "use_summary": False
    }

@pytest.fixture
def mock_config(monkeypatch, env_config_dict):
    """Mock the config module to return predetermined values."""
    # Create mock for get_config function
    def mock_get_config():
        return env_config_dict.copy()
    
    # Create mock prompt templates
    mock_prompts = {
        "summary": "Please summarize: [FULL_PDF_TEXT]",
        "vlm_base": "Describe page [PAGE_NUM] of [TOTAL_PAGES] in [LANGUAGE]:",
        "vlm_markdown": "Describe with markdown context: [MARKDOWN_CONTEXT]",
        "vlm_summary": "Describe with summary context: [SUMMARY_CONTEXT]",
        "vlm_full": "Describe with both contexts: [MARKDOWN_CONTEXT] and [SUMMARY_CONTEXT]"
    }
    
    def mock_get_prompts():
        return mock_prompts.copy()
    
    # Apply monkeypatches
    monkeypatch.setattr("describepdf.config.get_config", mock_get_config)
    monkeypatch.setattr("describepdf.config.get_prompts", mock_get_prompts)
    monkeypatch.setattr("describepdf.config.get_required_prompts_for_config", 
                        lambda cfg: {k: mock_prompts[k] for k in ["vlm_base", "summary"] 
                                    if k in mock_prompts})