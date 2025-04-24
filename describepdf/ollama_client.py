import logging
import base64
import requests
from ollama import Client

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("Ollama Python client not available. Install with 'pip install ollama'")

def check_ollama_availability(endpoint):
    """
    Comprueba si Ollama está disponible en el endpoint proporcionado.
    
    Args:
        endpoint (str): URL del endpoint de Ollama.
        
    Returns:
        bool: True si Ollama está disponible, False en caso contrario.
    """
    if not OLLAMA_AVAILABLE:
        logging.error("Ollama Python client not installed.")
        return False
        
    try:
        endpoint = endpoint.rstrip('/')
        
        response = requests.get(f"{endpoint}/api/version", timeout=5)
        
        logging.info(f"Ollama is available at {endpoint}. Response status: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"Could not connect to Ollama at {endpoint}: {e}")
        return False

def get_vlm_description(endpoint, model, prompt_text, image_bytes, mime_type):
    """
    Obtiene la descripción de una página usando un VLM a través de Ollama.
    
    Args:
        endpoint (str): URL del endpoint de Ollama.
        model (str): Modelo VLM de Ollama.
        prompt_text (str): Prompt de texto.
        image_bytes (bytes): Bytes de la imagen de la página.
        mime_type (str): MIME type de la imagen ('image/png' o 'image/jpeg').
        
    Returns:
        str: Descripción generada, o None si hay error.
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama Python client not installed. Install with 'pip install ollama'")
    
    try:
        client = Client(
            host=endpoint.rstrip('/')
        )
        
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        messages = [
            {
                'role': 'user',
                'content': prompt_text,
                'images': [encoded_image]
            }
        ]
        
        logging.info(f"Calling Ollama VLM model: {model}")
        
        response = client.chat(
            model=model,
            messages=messages
        )
        
        if response and 'message' in response and 'content' in response['message']:
            content = response['message']['content']
            logging.info(f"Received VLM description from Ollama (model: {model}).")
            return str(content)
        else:
            logging.warning(f"Ollama VLM response structure unexpected: {response}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting VLM description from Ollama: {e}")
        raise e

def get_llm_summary(endpoint, model, prompt_text):
    """
    Obtiene un resumen usando un LLM a través de Ollama.
    
    Args:
        endpoint (str): URL del endpoint de Ollama.
        model (str): Modelo LLM para resumen.
        prompt_text (str): Prompt incluyendo el texto a resumir.
        
    Returns:
        str: Resumen generado, o None si hay error.
    """
    if not OLLAMA_AVAILABLE:
        raise ImportError("Ollama Python client not installed. Install with 'pip install ollama'")
    
    try:
        client = Client(
            host=endpoint.rstrip('/')
        )
        
        messages = [
            {
                'role': 'user',
                'content': prompt_text
            }
        ]
        
        logging.info(f"Calling Ollama LLM model for summary: {model}")
        
        response = client.chat(
            model=model,
            messages=messages
        )
        
        if response and 'message' in response and 'content' in response['message']:
            content = response['message']['content']
            logging.info(f"Received summary from Ollama (model: {model}).")
            return str(content)
        else:
            logging.warning(f"Ollama LLM summary response structure unexpected: {response}")
            return None
            
    except Exception as e:
        logging.error(f"Error getting LLM summary from Ollama: {e}")
        raise e