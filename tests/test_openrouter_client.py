"""
Tests for the OpenRouter client module of DescribePDF.

This module tests the interaction with the OpenRouter API for
VLM (Vision Language Model) image descriptions and LLM text summarization.
"""

import json
import pytest
import base64
import responses
from unittest.mock import patch

from describepdf import openrouter_client

@pytest.fixture
def mock_base64_image():
    """Fixture providing a mock base64 encoded image string."""
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."

@pytest.fixture
def setup_responses():
    """Setup responses library for mocking HTTP requests."""
    with responses.RequestsMock() as rsps:
        yield rsps

class TestOpenRouterClient:
    """Test suite for the OpenRouter client functionality."""

    def test_encode_image_to_base64(self, sample_image_bytes):
        """Test encoding image bytes to base64 string."""
        # Execute test
        result = openrouter_client.encode_image_to_base64(sample_image_bytes, "image/jpeg")
        
        # Assert results
        expected_prefix = "data:image/jpeg;base64,"
        assert result.startswith(expected_prefix)
        
        # Decode and verify
        base64_part = result[len(expected_prefix):]
        decoded = base64.b64decode(base64_part)
        assert decoded == sample_image_bytes

    def test_encode_image_to_base64_error(self):
        """Test error handling when image encoding fails."""
        # Setup test
        with patch('base64.b64encode', side_effect=Exception("Encoding error")):
            # Execute test and check exception
            with pytest.raises(ValueError) as excinfo:
                openrouter_client.encode_image_to_base64(b"invalid image data", "image/png")
            
            # Assert exception message
            assert "Failed to encode image" in str(excinfo.value)

    def test_call_openrouter_api_success(self, setup_responses, mock_openrouter_response):
        """Test successful call to OpenRouter API."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        messages = [{"role": "user", "content": "Test message"}]
        
        # Mock the API response
        setup_responses.add(
            responses.POST,
            openrouter_client.OPENROUTER_API_URL,
            json=mock_openrouter_response,
            status=200
        )
        
        # Execute test
        result = openrouter_client.call_openrouter_api(api_key, model, messages)
        
        # Assert results
        assert result == mock_openrouter_response
        assert len(setup_responses.calls) == 1
        
        # Validate request
        request_body = json.loads(setup_responses.calls[0].request.body)
        assert request_body["model"] == model
        assert request_body["messages"] == messages

    def test_call_openrouter_api_missing_key(self):
        """Test error handling when API key is missing."""
        # Execute test and check exception
        with pytest.raises(ValueError) as excinfo:
            openrouter_client.call_openrouter_api("", "model_name", [])
        
        # Assert exception message
        assert "API Key is missing" in str(excinfo.value)

    def test_call_openrouter_api_timeout(self, setup_responses):
        """Test error handling when API call times out."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        messages = [{"role": "user", "content": "Test message"}]
        
        # Mock timeout response
        setup_responses.add(
            responses.POST,
            openrouter_client.OPENROUTER_API_URL,
            body=responses.ConnectionError("Connection timed out")
        )
        
        # Execute test and check exception
        with pytest.raises(TimeoutError) as excinfo:
            openrouter_client.call_openrouter_api(api_key, model, messages)
        
        # Assert exception message
        assert "API call timed out" in str(excinfo.value)

    def test_call_openrouter_api_error_response(self, setup_responses):
        """Test error handling when API returns an error response."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        messages = [{"role": "user", "content": "Test message"}]
        
        # Mock error response
        error_json = {
            "error": {
                "message": "Invalid model specified",
                "type": "invalid_request_error",
                "code": "model_not_found"
            }
        }
        
        setup_responses.add(
            responses.POST,
            openrouter_client.OPENROUTER_API_URL,
            json=error_json,
            status=400
        )
        
        # Execute test and check exception
        with pytest.raises(ConnectionError) as excinfo:
            openrouter_client.call_openrouter_api(api_key, model, messages)
        
        # Assert exception message
        assert "API Error" in str(excinfo.value)
        assert "Invalid model specified" in str(excinfo.value)

    def test_get_vlm_description_success(self, setup_responses, sample_image_bytes, mock_openrouter_response):
        """Test getting a page description using a VLM through OpenRouter."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        prompt = "Describe this image"
        mime_type = "image/jpeg"
        
        # Mock encode_image_to_base64
        with patch('describepdf.openrouter_client.encode_image_to_base64', 
                   return_value="data:image/jpeg;base64,encodedImageData"), \
             patch('describepdf.openrouter_client.call_openrouter_api', 
                   return_value=mock_openrouter_response):
            
            # Execute test
            result = openrouter_client.get_vlm_description(api_key, model, prompt, sample_image_bytes, mime_type)
            
            # Assert results
            expected_content = mock_openrouter_response["choices"][0]["message"]["content"]
            assert result == expected_content

    def test_get_vlm_description_empty_response(self):
        """Test handling when VLM returns empty or unexpected response structure."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        prompt = "Describe this image"
        
        empty_response = {
            "choices": [
                {
                    "message": {
                        "content": ""
                    }
                }
            ]
        }
        
        with patch('describepdf.openrouter_client.encode_image_to_base64', 
                   return_value="data:image/jpeg;base64,encodedImageData"), \
             patch('describepdf.openrouter_client.call_openrouter_api', 
                   return_value=empty_response):
            
            # Execute test and check exception
            with pytest.raises(ValueError) as excinfo:
                openrouter_client.get_vlm_description(api_key, model, prompt, b"image_data", "image/jpeg")
            
            # Assert exception message
            assert "VLM returned no usable content" in str(excinfo.value)

    def test_get_vlm_description_invalid_response_structure(self):
        """Test handling when VLM returns invalid response structure."""
        # Setup test
        api_key = "test_api_key"
        model = "qwen/qwen2.5-vl-72b-instruct"
        prompt = "Describe this image"
        
        invalid_response = {
            "id": "gen_123",
            "model": "qwen/qwen2.5-vl-72b-instruct"
            # Missing 'choices' key
        }
        
        with patch('describepdf.openrouter_client.encode_image_to_base64', 
                   return_value="data:image/jpeg;base64,encodedImageData"), \
             patch('describepdf.openrouter_client.call_openrouter_api', 
                   return_value=invalid_response):
            
            # Execute test and check exception
            with pytest.raises(ValueError) as excinfo:
                openrouter_client.get_vlm_description(api_key, model, prompt, b"image_data", "image/jpeg")
            
            # Assert exception message
            assert "unexpected response structure" in str(excinfo.value)

    def test_get_llm_summary_success(self, mock_openrouter_response):
        """Test getting a summary using an LLM through OpenRouter."""
        # Setup test
        api_key = "test_api_key"
        model = "google/gemini-2.5-flash-preview"
        prompt = "Summarize this document"
        
        with patch('describepdf.openrouter_client.call_openrouter_api', 
                   return_value=mock_openrouter_response):
            
            # Execute test
            result = openrouter_client.get_llm_summary(api_key, model, prompt)
            
            # Assert results
            expected_content = mock_openrouter_response["choices"][0]["message"]["content"]
            assert result == expected_content

    def test_get_llm_summary_error(self):
        """Test error handling when getting a summary from LLM fails."""
        # Setup test
        api_key = "test_api_key"
        model = "google/gemini-2.5-flash-preview"
        prompt = "Summarize this document"
        
        with patch('describepdf.openrouter_client.call_openrouter_api', 
                   side_effect=ValueError("API Error")):
            
            # Execute test and check exception
            with pytest.raises(ValueError) as excinfo:
                openrouter_client.get_llm_summary(api_key, model, prompt)
            
            # Assert exception message
            assert "API Error" in str(excinfo.value)