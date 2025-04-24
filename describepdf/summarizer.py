import logging
from . import pdf_processor
from . import openrouter_client
from . import ollama_client
from .config import get_prompts

def generate_summary_openrouter(pdf_path: str, api_key: str, model: str):
    """
    Genera un resumen del contenido textual completo de un PDF usando OpenRouter.

    Args:
        pdf_path (str): Ruta al archivo PDF.
        api_key (str): Clave API de OpenRouter.
        model (str): Modelo LLM a usar para el resumen.

    Returns:
        str: El resumen generado, o None si falla algún paso.
    """
    logging.info(f"Starting summary generation for '{pdf_path}' using OpenRouter model {model}.")

    logging.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    if full_text is None:
        logging.error("Failed to extract text for summary.")
        return None
    if not full_text.strip():
        logging.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logging.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logging.error("Summary prompt template not found.")
        return None

    max_chars_for_prompt = 512000
    if len(full_text) > max_chars_for_prompt:
        logging.warning(f"PDF text ({len(full_text)} chars) exceeds limit ({max_chars_for_prompt}), truncating for summary.")
        full_text = full_text[:max_chars_for_prompt] + "\n\n[... text truncated ...]"

    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    logging.info(f"Calling OpenRouter LLM for summary (model: {model})...")
    try:
        summary = openrouter_client.get_llm_summary(api_key, model, prompt_text)
        if summary:
            logging.info("Summary generated successfully via OpenRouter.")
            return summary
        else:
            logging.error("OpenRouter LLM call for summary returned no content.")
            return None
    except (ValueError, ConnectionError, TimeoutError) as e:
        logging.error(f"Failed to generate summary due to OpenRouter API error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during summary generation with OpenRouter: {e}")
        return None

def generate_summary_ollama(pdf_path: str, endpoint: str, model: str):
    """
    Genera un resumen del contenido textual completo de un PDF usando Ollama.

    Args:
        pdf_path (str): Ruta al archivo PDF.
        endpoint (str): URL del endpoint de Ollama.
        model (str): Modelo LLM a usar para el resumen.

    Returns:
        str: El resumen generado, o None si falla algún paso.
    """
    logging.info(f"Starting summary generation for '{pdf_path}' using Ollama model {model}.")

    logging.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    if full_text is None:
        logging.error("Failed to extract text for summary.")
        return None
    if not full_text.strip():
        logging.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logging.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logging.error("Summary prompt template not found.")
        return None

    max_chars_for_prompt = 512000
    if len(full_text) > max_chars_for_prompt:
        logging.warning(f"PDF text ({len(full_text)} chars) exceeds limit ({max_chars_for_prompt}), truncating for summary.")
        full_text = full_text[:max_chars_for_prompt] + "\n\n[... text truncated ...]"

    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    logging.info(f"Calling Ollama LLM for summary (model: {model})...")
    try:
        summary = ollama_client.get_llm_summary(endpoint, model, prompt_text)
        if summary:
            logging.info("Summary generated successfully via Ollama.")
            return summary
        else:
            logging.error("Ollama LLM call for summary returned no content.")
            return None
    except (ValueError, ConnectionError, TimeoutError, ImportError) as e:
        logging.error(f"Failed to generate summary due to Ollama error: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error during summary generation with Ollama: {e}")
        return None

# Función de compatibilidad para código existente
def generate_summary(pdf_path: str, api_key: str, model: str):
    """
    Función de compatibilidad que utiliza OpenRouter.
    
    Args:
        pdf_path (str): Ruta al archivo PDF.
        api_key (str): Clave API de OpenRouter.
        model (str): Modelo LLM a usar para el resumen.
        
    Returns:
        str: El resumen generado, o None si falla algún paso.
    """
    return generate_summary_openrouter(pdf_path, api_key, model)