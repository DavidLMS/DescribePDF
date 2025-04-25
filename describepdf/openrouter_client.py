"""
OpenRouter client module for DescribePDF.

This module handles all interactions with the OpenRouter API for
VLM (Vision Language Model) image description and LLM text summarization.
"""

import requests
import base64
import json
import logging
from typing import Dict, Any, Optional, List

# Get logger from config module
logger = logging.getLogger('describepdf')

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 300  # 5 minutes

def encode_image_to_base64(image_bytes: bytes, mime_type: str) -> str:
    """
    Encode image bytes to Base64 string for the API.
    
    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of the image ('image/png' or 'image/jpeg')
        
    Returns:
        str: Base64 encoded image string with data URI scheme
        
    Raises:
        ValueError: If image encoding fails
    """
    try:
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        logger.error(f"Error encoding image to Base64: {e}")
        raise ValueError(f"Failed to encode image: {e}")

def call_openrouter_api(api_key: str, model: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Make a call to the OpenRouter Chat Completions API.

    Args:
        api_key: OpenRouter API key
        model: Model name to use
        messages: List of messages in API format

    Returns:
        Dict: The JSON response from the API
        
    Raises:
        ValueError: If API key is missing
        ConnectionError: If API call fails with error response
        TimeoutError: If API call times out
    """
    if not api_key:
        logger.error("OpenRouter API Key is missing.")
        raise ValueError("OpenRouter API Key is missing.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": model,
        "messages": messages
    }

    try:
        # Log API call (without full message content for privacy/size)
        msg_log = json.dumps(messages)[:200] + ("..." if len(json.dumps(messages)) > 200 else "")
        logger.debug(f"Calling OpenRouter API. Model: {model}. Messages: {msg_log}")
        
        # Make API request
        response = requests.post(
            OPENROUTER_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        
        logger.debug(f"API call successful. Status: {response.status_code}.")
        return response.json()

    except requests.exceptions.Timeout:
        logger.error(f"API call timed out for model {model}.")
        raise TimeoutError(f"API call timed out for model {model}.")
        
    except requests.exceptions.RequestException as e:
        # Log error details without assuming response exists
        status_code = getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'
        response_text = getattr(e.response, 'text', 'No response') if hasattr(e, 'response') else 'No response'
        logger.error(f"API call failed for model {model}. Status: {status_code}. Response: {response_text}")
        
        # Extract error message from response if possible
        error_message = f"API Error: {e}"
        if hasattr(e, 'response') and e.response:
            try:
                error_details = e.response.json()
                if 'error' in error_details and 'message' in error_details['error']:
                    error_message = f"API Error ({e.response.status_code}): {error_details['error']['message']}"
                else:
                    error_message = f"API Error ({e.response.status_code}): {e.response.text[:200]}"
            except json.JSONDecodeError:
                error_message = f"API Error ({e.response.status_code}): {e.response.text[:200]}"
                
        raise ConnectionError(error_message)

def get_vlm_description(api_key: str, model: str, prompt_text: str, image_bytes: bytes, mime_type: str) -> str:
    """
    Get a page description using a VLM through OpenRouter.

    Args:
        api_key: OpenRouter API key
        model: VLM model name
        prompt_text: Text prompt
        image_bytes: Bytes of the page image
        mime_type: MIME type of the image ('image/png' or 'image/jpeg')

    Returns:
        str: Generated description
        
    Raises:
        ValueError: If API key is missing or image encoding fails
        ConnectionError: If API call fails with error response
        TimeoutError: If API call times out
    """
    # Encode image to base64
    base64_image = encode_image_to_base64(image_bytes, mime_type)

    # Prepare messages for API
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
                {
                    "type": "image_url",
                    "image_url": {"url": base64_image}
                }
            ]
        }
    ]

    # Call OpenRouter API
    response_json = call_openrouter_api(api_key, model, messages)
    
    # Process response
    if response_json and 'choices' in response_json and response_json['choices']:
        if len(response_json['choices']) > 0:
            message = response_json['choices'][0].get('message', {})
            if message and 'content' in message:
                content = message.get('content')
                if content:
                    logger.info(f"Received VLM description for page (model: {model}).")
                    return str(content)
                
        logger.warning(f"VLM response structure unexpected or content empty.")
        raise ValueError("VLM returned no usable content")
    else:
        logger.warning(f"VLM response JSON structure unexpected: {response_json}")
        raise ValueError("VLM returned unexpected response structure")

def get_llm_summary(api_key: str, model: str, prompt_text: str) -> str:
    """
    Get a summary using an LLM through OpenRouter.

    Args:
        api_key: OpenRouter API key
        model: LLM model for summary
        prompt_text: Prompt including the text to summarize

    Returns:
        str: Generated summary
        
    Raises:
        ValueError: If API key is missing
        ConnectionError: If API call fails with error response
        TimeoutError: If API call times out
    """
    # Prepare messages for API
    messages = [
        {"role": "user", "content": prompt_text}
    ]

    # Call OpenRouter API
    response_json = call_openrouter_api(api_key, model, messages)
    
    # Process response
    if response_json and 'choices' in response_json and response_json['choices']:
        if len(response_json['choices']) > 0:
            message = response_json['choices'][0].get('message', {})
            if message and 'content' in message:
                content = message.get('content')
                if content:
                    logger.info(f"Received summary (model: {model}).")
                    return str(content)
        
        logger.warning(f"LLM summary response structure unexpected or content empty.")
        raise ValueError("LLM returned no usable content")
    else:
        logger.warning(f"LLM summary response JSON structure unexpected: {response_json}")
        raise ValueError("LLM returned unexpected response structure")