import logging
from . import pdf_processor
from . import openrouter_client
from .config import get_prompts

def generate_summary(pdf_path: str, api_key: str, model: str):
    """
    Genera un resumen del contenido textual completo de un PDF.

    Args:
        pdf_path (str): Ruta al archivo PDF.
        api_key (str): Clave API de OpenRouter.
        model (str): Modelo LLM a usar para el resumen.

    Returns:
        str: El resumen generado, o None si falla algún paso.
    """
    logging.info(f"Starting summary generation for '{pdf_path}' using model {model}.")

    # 1. Extraer todo el texto
    logging.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    if full_text is None:
        logging.error("Failed to extract text for summary.")
        return None
    if not full_text.strip():
        logging.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logging.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    # 2. Construir el prompt de resumen
    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logging.error("Summary prompt template not found.")
        return None

    # Podríamos necesitar truncar el texto si es muy largo para el contexto del LLM
    # Esto es una simplificación, una mejor solución implicaría chunking/map-reduce
    max_chars_for_prompt = 30000 # Ajustar según el modelo de resumen
    if len(full_text) > max_chars_for_prompt:
        logging.warning(f"PDF text ({len(full_text)} chars) exceeds limit ({max_chars_for_prompt}), truncating for summary.")
        full_text = full_text[:max_chars_for_prompt] + "\n\n[... text truncated ...]"

    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    # 3. Llamar a la API LLM
    logging.info(f"Calling LLM for summary (model: {model})...")
    try:
        summary = openrouter_client.get_llm_summary(api_key, model, prompt_text)
        if summary:
            logging.info("Summary generated successfully.")
            return summary
        else:
            logging.error("LLM call for summary returned no content.")
            return None
    except (ValueError, ConnectionError, TimeoutError) as e:
        # Errores ya logueados en el cliente API
        logging.error(f"Failed to generate summary due to API error: {e}")
        return None # O podrías devolver el mensaje de error e
    except Exception as e:
        logging.error(f"Unexpected error during summary generation: {e}")
        return None