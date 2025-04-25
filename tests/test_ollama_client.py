"""
Tests for the Ollama client module of DescribePDF.

This module tests the interaction with the local Ollama server for
VLM (Vision Language Model) image descriptions and LLM text summarization.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

from describepdf import ollama_client

class TestOllamaClient:
    """Test suite for the Ollama client functionality."""

    def test_check_ollama_availability_success(self):
        """Test successful connection to Ollama server."""
        # Setup test
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('requests.get', return_value=mock_response):
            
            # Execute test
            result = ollama_client.check_ollama_availability("http://localhost:11434")
            
            # Assert results
            assert result is True
            requests.get.assert_called_once_with("http://localhost:11434/api/version", timeout=5)

    def test_check_ollama_availability_client_not_installed(self):
        """Test behavior when Ollama Python client is not installed."""
        # Setup test
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', False):
            # Execute test
            result = ollama_client.check_ollama_availability("http://localhost:11434")
            
            # Assert results
            assert result is False

    def test_check_ollama_availability_connection_error(self):
        """Test behavior when connection to Ollama server fails."""
        # Setup test
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error")):
            
            # Execute test
            result = ollama_client.check_ollama_availability("http://localhost:11434")
            
            # Assert results
            assert result is False
            requests.get.assert_called_once_with("http://localhost:11434/api/version", timeout=5)

    def test_check_ollama_availability_unexpected_error(self):
        """Test behavior when unexpected error occurs checking Ollama availability."""
        # Setup test
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('requests.get', side_effect=Exception("Unexpected error")):
            
            # Execute test
            result = ollama_client.check_ollama_availability("http://localhost:11434")
            
            # Assert results
            assert result is False
            requests.get.assert_called_once_with("http://localhost:11434/api/version", timeout=5)

    def test_get_vlm_description_client_not_installed(self):
        """Test behavior when Ollama Python client is not installed."""
        # Setup test
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', False):
            # Execute test and check exception
            with pytest.raises(ImportError) as excinfo:
                ollama_client.get_vlm_description(
                    "http://localhost:11434", 
                    "llama3.2-vision", 
                    "Describe this image", 
                    b"image_data", 
                    "image/jpeg"
                )
            
            # Assert exception message
            assert "not installed" in str(excinfo.value)

    def test_get_vlm_description_success(self):
        """Test successful VLM description request through Ollama."""
        # Setup test
        mock_client = MagicMock()
        mock_response = {
            "message": {
                "content": "Description of the image content."
            }
        }
        mock_client.chat.return_value = mock_response
        
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.ollama_client.Client', return_value=mock_client), \
             patch('base64.b64encode', return_value=b'encoded_image_data'), \
             patch('base64.b64encode().decode', return_value='encoded_image_data'):
            
            # Execute test
            result = ollama_client.get_vlm_description(
                "http://localhost:11434", 
                "llama3.2-vision", 
                "Describe this image", 
                b"image_data", 
                "image/jpeg"
            )
            
            # Assert results
            assert result == "Description of the image content."
            
            # Verify client was created and used correctly
            ollama_client.Client.assert_called_once_with(host="http://localhost:11434")
            assert mock_client.chat.call_count == 1
            
            # Verify chat call arguments
            chat_args = mock_client.chat.call_args[1]
            assert chat_args["model"] == "llama3.2-vision"
            assert len(chat_args["messages"]) == 1
            assert chat_args["messages"][0]["role"] == "user"
            assert chat_args["messages"][0]["content"] == "Describe this image"
            assert "images" in chat_args["messages"][0]

    def test_get_vlm_description_api_error(self):
        """Test error handling when Ollama API returns an error."""
        # Setup test
        mock_client = MagicMock()
        
        # Create a mock ResponseError class
        class MockResponseError(Exception):
            pass
        
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.ollama_client.Client', return_value=mock_client), \
             patch('describepdf.ollama_client.ollama.ResponseError', MockResponseError), \
             patch('base64.b64encode', return_value=b'encoded_image_data'), \
             patch('base64.b64encode().decode', return_value='encoded_image_data'):
            
            # Make the chat method raise an error
            mock_client.chat.side_effect = MockResponseError("API Error")
            
            # Execute test and check exception
            with pytest.raises(ConnectionError) as excinfo:
                ollama_client.get_vlm_description(
                    "http://localhost:11434", 
                    "llama3.2-vision", 
                    "Describe this image", 
                    b"image_data", 
                    "image/jpeg"
                )
            
            # Assert exception message
            assert "Ollama API error" in str(excinfo.value)

    def test_get_vlm_description_unexpected_response(self):
        """Test error handling when Ollama returns unexpected response structure."""
        # Setup test
        mock_client = MagicMock()
        # Response missing 'message' key
        mock_response = {"model": "llama3.2-vision"}
        mock_client.chat.return_value = mock_response
        
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.ollama_client.Client', return_value=mock_client), \
             patch('base64.b64encode', return_value=b'encoded_image_data'), \
             patch('base64.b64encode().decode', return_value='encoded_image_data'):
            
            # Execute test and check exception
            with pytest.raises(ValueError) as excinfo:
                ollama_client.get_vlm_description(
                    "http://localhost:11434", 
                    "llama3.2-vision", 
                    "Describe this image", 
                    b"image_data", 
                    "image/jpeg"
                )
            
            # Assert exception message
            assert "unexpected response structure" in str(excinfo.value)

    def test_get_llm_summary_success(self):
        """Test successful summary request through Ollama."""
        # Setup test
        mock_client = MagicMock()
        mock_response = {
            "message": {
                "content": "Summary of the document."
            }
        }
        mock_client.chat.return_value = mock_response
        
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', True), \
             patch('describepdf.ollama_client.Client', return_value=mock_client):
            
            # Execute test
            result = ollama_client.get_llm_summary(
                "http://localhost:11434",
                "qwen2.5",
                "Summarize this document"
            )
            
            # Assert results
            assert result == "Summary of the document."
            
            # Verify client was created and used correctly
            ollama_client.Client.assert_called_once_with(host="http://localhost:11434")
            assert mock_client.chat.call_count == 1
            
            # Verify chat call arguments
            chat_args = mock_client.chat.call_args[1]
            assert chat_args["model"] == "qwen2.5"
            assert len(chat_args["messages"]) == 1
            assert chat_args["messages"][0]["role"] == "user"
            assert chat_args["messages"][0]["content"] == "Summarize this document"

    def test_get_llm_summary_client_not_installed(self):
        """Test behavior when Ollama Python client is not installed."""
        # Setup test
        with patch('describepdf.ollama_client.OLLAMA_AVAILABLE', False):
            # Execute test and check exception
            with pytest.raises(ImportError) as excinfo:
                ollama_client.get_llm_summary(
                    "http://localhost:11434",
                    "qwen2.5",
                    "Summarize this document"
                )
            
            # Assert exception message
            assert "not installed" in str(excinfo.value)