"""
Ollama client module for DescribePDF.

This module handles all interactions with local Ollama API for 
VLM (Vision Language Model) image description and LLM text summarization.
"""

import logging
import base64
import requests
from typing import Optional
from urllib.parse import urljoin

# Try to import Ollama, but handle gracefully if it's not available
try:
    import ollama
    from ollama import Client
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama Python client not available. Install with 'pip install ollama'")

def check_ollama_availability(endpoint: str) -> bool:
    """
    Check if Ollama is available at the specified endpoint.
    
    Args:
        endpoint: URL of the Ollama endpoint
        
    Returns:
        bool: True if Ollama is available, False otherwise
    """
    if not OLLAMA_AVAILABLE:
        logging.error("Ollama Python client not installed.")
        return False
        
    try:
        # Normalize endpoint URL by removing trailing slashes
        endpoint = endpoint.rstrip('/')
        
        # Use requests to check API availability (faster than creating a Client)
        response = requests.get(f"{endpoint}/api/version", timeout=5)
        response.raise_for_status()
        
        logging.info(f"Ollama is available at {endpoint}. Response status: {response.status_code}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Could not connect to Ollama at {endpoint}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error checking Ollama availability: {e}")
        return False

def get_vlm_description(endpoint: str, model: str, prompt_text: str, image_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Get a page description using a VLM through Ollama.
    
    Args:
        endpoint: URL of the Ollama endpoint
        model: Ollama VLM model name
        prompt_text: Text prompt
        image_bytes: Bytes of the page image
        mime_type: MIME type of the image ('image/png' or 'image/jpeg')
        
    Returns:
        str: Generated description, or None if there was an error
        
    Raises:
        ImportError: If Ollama Python client is not installed
        ConnectionError: If communication with Ollama fails
        ValueError: If there's an issue with the request parameters
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama Python client not installed. Install with 'pip install ollama'")
    
    try:
        # Create Ollama client
        client = Client(host=endpoint.rstrip('/'))
        
        # Encode image to base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Prepare messages for chat API
        messages = [
            {
                'role': 'user',
                'content': prompt_text,
                'images': [encoded_image]
            }
        ]
        
        logging.info(f"Calling Ollama VLM model: {model}")
        
        # Call Ollama chat API
        response = client.chat(
            model=model,
            messages=messages
        )
        
        # Extract and validate response
        if response and 'message' in response and 'content' in response['message']:
            content = response['message']['content']
            logging.info(f"Received VLM description from Ollama (model: {model}).")
            return str(content)
        else:
            logging.warning(f"Ollama VLM response structure unexpected: {response}")
            return None
            
    except ollama.ResponseError as e:
        logging.error(f"Ollama API error: {e}")
        raise ConnectionError(f"Ollama API error: {e}")
    except Exception as e:
        logging.error(f"Error getting VLM description from Ollama: {e}")
        raise

def get_llm_summary(endpoint: str, model: str, prompt_text: str) -> Optional[str]:
    """
    Get a summary using an LLM through Ollama.
    
    Args:
        endpoint: URL of the Ollama endpoint
        model: Ollama LLM model for summary
        prompt_text: Prompt including the text to summarize
        
    Returns:
        str: Generated summary, or None if there was an error
        
    Raises:
        ImportError: If Ollama Python client is not installed
        ConnectionError: If communication with Ollama fails
        ValueError: If there's an issue with the request parameters
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama Python client not installed. Install with 'pip install ollama'")
    
    try:
        # Create Ollama client
        client = Client(host=endpoint.rstrip('/'))
        
        # Prepare messages for chat API
        messages = [
            {
                'role': 'user',
                'content': prompt_text
            }
        ]
        
        logging.info(f"Calling Ollama LLM model for summary: {model}")
        
        # Call Ollama chat API
        response = client.chat(
            model=model,
            messages=messages
        )
        
        # Extract and validate response
        if response and 'message' in response and 'content' in response['message']:
            content = response['message']['content']
            logging.info(f"Received summary from Ollama (model: {model}).")
            return str(content)
        else:
            logging.warning(f"Ollama LLM summary response structure unexpected: {response}")
            return None
            
    except ollama.ResponseError as e:
        logging.error(f"Ollama API error: {e}")
        raise ConnectionError(f"Ollama API error: {e}")
    except Exception as e:
        logging.error(f"Error getting LLM summary from Ollama: {e}")
        raise