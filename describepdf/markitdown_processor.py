"""
MarkItDown processor module for DescribePDF.

This module handles the enhanced text extraction functionality using the
MarkItDown library to convert PDF content to markdown format.
"""

import logging
import os
from typing import Optional

# Try to import MarkItDown, but handle gracefully if it's not available
try:
    from markitdown import MarkItDown
    md_converter = MarkItDown()
    logging.info("MarkItDown initialized successfully.")
    MARKITDOWN_AVAILABLE = True
except ImportError:
    logging.warning("MarkItDown library not installed. Install with 'pip install markitdown[pdf]'")
    md_converter = None
    MARKITDOWN_AVAILABLE = False
except Exception as e:
    logging.error(f"Failed to initialize MarkItDown: {e}")
    md_converter = None
    MARKITDOWN_AVAILABLE = False

def get_markdown_for_page_via_temp_pdf(temp_pdf_path: str) -> Optional[str]:
    """
    Use MarkItDown to extract Markdown from a PDF file (single page).

    Args:
        temp_pdf_path: Path to the temporary single-page PDF file

    Returns:
        str: Extracted Markdown content, or None if there was an error
    """
    if not MARKITDOWN_AVAILABLE or not md_converter:
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

def is_available() -> bool:
    """
    Check if MarkItDown functionality is available.
    
    Returns:
        bool: True if MarkItDown is available, False otherwise
    """
    return MARKITDOWN_AVAILABLE