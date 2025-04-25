"""
MarkItDown processor module for DescribePDF.

This module handles the enhanced text extraction functionality using the
MarkItDown library to convert PDF content to markdown format.
"""

import os
from typing import Optional

# Get logger from config module
from .config import logger

# Check if MarkItDown is available
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    logger.warning("MarkItDown library not installed. Install with 'pip install markitdown[pdf]'")
    MARKITDOWN_AVAILABLE = False
except Exception as e:
    logger.error(f"Failed to initialize MarkItDown: {e}")
    MARKITDOWN_AVAILABLE = False

def _get_markdown_converter():
    """
    Initialize and return a MarkItDown converter instance.
    
    Returns:
        MarkItDown: An initialized MarkItDown converter or None if not available
    """
    if not MARKITDOWN_AVAILABLE:
        return None
        
    try:
        converter = MarkItDown()
        return converter
    except Exception as e:
        logger.error(f"Failed to initialize MarkItDown converter: {e}")
        return None

def get_markdown_for_page_via_temp_pdf(temp_pdf_path: str) -> Optional[str]:
    """
    Use MarkItDown to extract Markdown from a PDF file (single page).

    Args:
        temp_pdf_path: Path to the temporary single-page PDF file

    Returns:
        str: Extracted Markdown content, or None if there was an error
    """
    if not MARKITDOWN_AVAILABLE:
        logger.error("MarkItDown converter is not available.")
        return None
        
    if not os.path.exists(temp_pdf_path):
        logger.error(f"Temporary PDF file not found: {temp_pdf_path}")
        return None

    try:
        md_converter = _get_markdown_converter()
        if not md_converter:
            return None
            
        result = md_converter.convert(temp_pdf_path)
        logger.debug(f"Extracted Markdown from temporary PDF: {temp_pdf_path}")
        return result.text_content if result else ""
    except Exception as e:
        logger.error(f"MarkItDown failed to process {temp_pdf_path}: {e}")
        return None

def is_available() -> bool:
    """
    Check if MarkItDown functionality is available.
    
    Returns:
        bool: True if MarkItDown is available, False otherwise
    """
    return MARKITDOWN_AVAILABLE