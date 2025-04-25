"""
OpenRouter client module for DescribePDF.

This module handles all interactions with the OpenRouter API for
VLM (Vision Language Model) image description and LLM text summarization.
"""

import requests
import base64
import logging
import json
from typing import Dict, Any, Optional, List

# Constants
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_TIMEOUT = 300  # 5 minutes

def encode_image_to_base64(image_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Encode image bytes to Base64 string for the API.
    
    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of the image ('image/png' or 'image/jpeg')
        
    Returns:
        str: Base64 encoded image string with data URI scheme, or None if encoding fails
    """
    try:
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        logging.error(f"Error encoding image to Base64: {e}")
        return None

def call_openrouter_api(api_key: str, model: str, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
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
        logging.error("OpenRouter API Key is missing.")
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
        logging.debug(f"Calling OpenRouter API. Model: {model}. Messages: {msg_log}")
        
        # Make API request
        response = requests.post(
            OPENROUTER_API_URL, 
            headers=headers, 
            json=payload, 
            timeout=DEFAULT_TIMEOUT
        )
        response.raise_for_status()
        
        logging.debug(f"API call successful. Status: {response.status_code}.")
        return response.json()

    except requests.exceptions.Timeout:
        logging.error(f"API call timed out for model {model}.")
        raise TimeoutError(f"API call timed out for model {model}.")
        
    except requests.exceptions.RequestException as e:
        # Log error details
        status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'N/A'
        response_text = e.response.text if hasattr(e, 'response') and e.response else 'No response'
        logging.error(f"API call failed for model {model}. Status: {status_code}. Response: {response_text}")
        
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

def get_vlm_description(api_key: str, model: str, prompt_text: str, image_bytes: bytes, mime_type: str) -> Optional[str]:
    """
    Get a page description using a VLM through OpenRouter.

    Args:
        api_key: OpenRouter API key
        model: VLM model name
        prompt_text: Text prompt
        image_bytes: Bytes of the page image
        mime_type: MIME type of the image ('image/png' or 'image/jpeg')

    Returns:
        str: Generated description, or None if there was an error
        
    Raises:
        ValueError: If API key is missing
        ConnectionError: If API call fails with error response
        TimeoutError: If API call times out
    """
    # Encode image to base64
    base64_image = encode_image_to_base64(image_bytes, mime_type)
    if not base64_image:
        return None

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

    try:
        # Call OpenRouter API
        response_json = call_openrouter_api(api_key, model, messages)
        
        # Process response
        if response_json and 'choices' in response_json and len(response_json['choices']) > 0:
            content = response_json['choices'][0].get('message', {}).get('content')
            if content:
                logging.info(f"Received VLM description for page (model: {model}).")
                return str(content)
            else:
                logging.warning(f"VLM response structure unexpected or content empty: {response_json}")
                return None
        else:
            logging.warning(f"VLM response JSON structure unexpected: {response_json}")
            return None
            
    except (ValueError, ConnectionError, TimeoutError) as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error getting VLM description: {e}")
        raise e

def get_llm_summary(api_key: str, model: str, prompt_text: str) -> Optional[str]:
    """
    Get a summary using an LLM through OpenRouter.

    Args:
        api_key: OpenRouter API key
        model: LLM model for summary
        prompt_text: Prompt including the text to summarize

    Returns:
        str: Generated summary, or None if there was an error
        
    Raises:
        ValueError: If API key is missing
        ConnectionError: If API call fails with error response
        TimeoutError: If API call times out
    """
    # Prepare messages for API
    messages = [
        {"role": "user", "content": prompt_text}
    ]

    try:
        # Call OpenRouter API
        response_json = call_openrouter_api(api_key, model, messages)
        
        # Process response
        if response_json and 'choices' in response_json and len(response_json['choices']) > 0:
            content = response_json['choices'][0].get('message', {}).get('content')
            if content:
                logging.info(f"Received summary (model: {model}).")
                return str(content)
            else:
                logging.warning(f"LLM summary response structure unexpected or content empty: {response_json}")
                return None
        else:
            logging.warning(f"LLM summary response JSON structure unexpected: {response_json}")
            return None
            
    except (ValueError, ConnectionError, TimeoutError) as e:
        raise e
    except Exception as e:
        logging.error(f"Unexpected error getting LLM summary: {e}")
        raise e