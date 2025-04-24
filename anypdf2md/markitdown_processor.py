from markitdown import MarkItDown
import logging
import os

# Inicializar MarkItDown una vez
try:
    md_converter = MarkItDown()
    logging.info("MarkItDown initialized.")
except Exception as e:
    logging.error(f"Failed to initialize MarkItDown: {e}")
    md_converter = None

def get_markdown_for_page_via_temp_pdf(temp_pdf_path: str):
    """
    Usa MarkItDown para extraer Markdown de un archivo PDF (de una sola página).

    Args:
        temp_pdf_path (str): Ruta al archivo PDF temporal de una página.

    Returns:
        str: Contenido Markdown extraído, o None si hay error.
    """
    if not md_converter:
        logging.error("MarkItDown converter is not available.")
        return None
    if not os.path.exists(temp_pdf_path):
        logging.error(f"Temporary PDF file not found: {temp_pdf_path}")
        return None

    try:
        result = md_converter.convert(temp_pdf_path)
        logging.debug(f"Extracted Markdown from temporary PDF: {temp_pdf_path}")
        return result.text_content if result else ""
    except Exception as e:
        logging.error(f"MarkItDown failed to process {temp_pdf_path}: {e}")
        return None