import requests
import base64
import logging
import json

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
# Referer y Title pueden ser personalizados
HTTP_REFERER = "https://github.com/usuario/anypdf2md" # Cambia esto a tu repo si lo tienes
X_TITLE = "AnyPDF2MD"

def encode_image_to_base64(image_bytes: bytes, mime_type: str):
    """Codifica bytes de imagen a string Base64 para la API."""
    try:
        encoded = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{encoded}"
    except Exception as e:
        logging.error(f"Error encoding image to Base64: {e}")
        return None

def call_openrouter_api(api_key: str, model: str, messages: list):
    """
    Realiza una llamada a la API de OpenRouter Chat Completions.

    Args:
        api_key (str): Clave API de OpenRouter.
        model (str): Nombre del modelo a usar.
        messages (list): Lista de mensajes en el formato de la API.

    Returns:
        dict: La respuesta JSON de la API, o None si hay error.
    """
    if not api_key:
        logging.error("OpenRouter API Key is missing.")
        raise ValueError("OpenRouter API Key is missing.") # Lanzar error para detener el proceso

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": X_TITLE
    }
    payload = {
        "model": model,
        "messages": messages
    }

    try:
        logging.debug(f"Calling OpenRouter API. Model: {model}. Messages: {json.dumps(messages)[:200]}...") # Log truncado
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=180) # Timeout largo para VLM
        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
        logging.debug(f"API call successful. Status: {response.status_code}.")
        return response.json()

    except requests.exceptions.Timeout:
        logging.error(f"API call timed out for model {model}.")
        raise TimeoutError(f"API call timed out for model {model}.")
    except requests.exceptions.RequestException as e:
        logging.error(f"API call failed for model {model}. Status: {e.response.status_code if e.response else 'N/A'}. Response: {e.response.text if e.response else 'No response'}")
        # Intentar extraer mensaje de error de OpenRouter si es posible
        error_message = f"API Error: {e}"
        if e.response is not None:
            try:
                error_details = e.response.json()
                if 'error' in error_details and 'message' in error_details['error']:
                    error_message = f"API Error ({e.response.status_code}): {error_details['error']['message']}"
                else:
                     error_message = f"API Error ({e.response.status_code}): {e.response.text[:200]}" # Truncar respuesta larga
            except json.JSONDecodeError:
                 error_message = f"API Error ({e.response.status_code}): {e.response.text[:200]}"

        raise ConnectionError(error_message) # Lanzar error más específico

def get_vlm_description(api_key: str, model: str, prompt_text: str, image_bytes: bytes, mime_type: str):
    """
    Obtiene la descripción de una página usando un VLM a través de OpenRouter.

    Args:
        api_key (str): Clave API.
        model (str): Modelo VLM.
        prompt_text (str): Prompt de texto.
        image_bytes (bytes): Bytes de la imagen de la página.
        mime_type (str): MIME type de la imagen ('image/png' o 'image/jpeg').

    Returns:
        str: Descripción generada, o None si hay error.
    """
    base64_image = encode_image_to_base64(image_bytes, mime_type)
    if not base64_image:
        return None # Error ya logueado en encode_image

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
        response_json = call_openrouter_api(api_key, model, messages)
        if response_json and 'choices' in response_json and len(response_json['choices']) > 0:
            # Asumiendo que la respuesta está en choices[0].message.content
            content = response_json['choices'][0].get('message', {}).get('content')
            if content:
                 logging.info(f"Received VLM description for page (model: {model}).")
                 return str(content) # Asegurar que sea string
            else:
                 logging.warning(f"VLM response structure unexpected or content empty: {response_json}")
                 return None
        else:
            logging.warning(f"VLM response JSON structure unexpected: {response_json}")
            return None
    except (ValueError, ConnectionError, TimeoutError) as e:
        # Errores ya logueados en call_openrouter_api o por la validación de API Key
        # Relanzar para que el core lo maneje
        raise e
    except Exception as e:
        logging.error(f"Unexpected error getting VLM description: {e}")
        raise e # Relanzar

def get_llm_summary(api_key: str, model: str, prompt_text: str):
    """
    Obtiene un resumen usando un LLM a través de OpenRouter.

    Args:
        api_key (str): Clave API.
        model (str): Modelo LLM para resumen.
        prompt_text (str): Prompt incluyendo el texto a resumir.

    Returns:
        str: Resumen generado, o None si hay error.
    """
    messages = [
        {"role": "user", "content": prompt_text}
    ]

    try:
        response_json = call_openrouter_api(api_key, model, messages)
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
        raise e # Relanzar
    except Exception as e:
        logging.error(f"Unexpected error getting LLM summary: {e}")
        raise e # Relanzar