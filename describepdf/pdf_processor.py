"""
PDF processor module for DescribePDF.

This module handles all PDF file operations using PyMuPDF,
including rendering, text extraction, and file manipulation.
"""

import io
import os
import tempfile
import logging
from typing import Tuple, List, Optional

# Get logger from config module
logger = logging.getLogger('describepdf')

# Import PyMuPDF
try:
    import pymupdf
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.error("PyMuPDF not installed. Install with 'pip install pymupdf'")

# Import PIL for image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.error("Pillow not installed. Install with 'pip install pillow'")

def get_pdf_pages(pdf_path: str) -> Tuple[Optional[pymupdf.Document], Optional[List[pymupdf.Page]], int]:
    """
    Open a PDF and return a list of page objects and the total number of pages.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Tuple containing:
        - pymupdf.Document: The open PDF document
        - List[pymupdf.Page]: List of page objects
        - int: Total number of pages (0 if error)
    """
    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF is required for PDF processing but is not installed.")
        return None, None, 0
        
    try:
        doc = pymupdf.open(pdf_path)
        pages = [doc.load_page(i) for i in range(len(doc))]
        total_pages = len(doc)
        logger.info(f"Opened PDF '{os.path.basename(pdf_path)}' with {total_pages} pages.")
        return doc, pages, total_pages
    except Exception as e:
        logger.error(f"Error opening or reading PDF {pdf_path}: {e}")
        return None, None, 0

def render_page_to_image_bytes(page: pymupdf.Page, image_format: str = "jpeg", dpi: int = 150) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Render a PDF page to image bytes in memory.

    Args:
        page: PyMuPDF Page object
        image_format: Desired format ('png' or 'jpeg')
        dpi: Image resolution

    Returns:
        Tuple containing:
        - bytes: Image bytes
        - str: MIME type ('image/png' or 'image/jpeg')
        Returns (None, None) on error
    """
    if not PYMUPDF_AVAILABLE or not PIL_AVAILABLE:
        logger.error("PyMuPDF and Pillow are required for image rendering but are not installed.")
        return None, None
        
    try:
        # Render page to pixmap
        pix = page.get_pixmap(dpi=dpi)
        img_bytes_io = io.BytesIO()

        if image_format.lower() == "png":
            # Use PyMuPDF's built-in PNG conversion
            img_bytes = pix.tobytes("png")
            img_bytes_io.write(img_bytes)
            mime_type = "image/png"
        elif image_format.lower() == "jpeg":
            # Use PIL for JPEG conversion (better quality control)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(img_bytes_io, format="JPEG", quality=85)  # Adjust JPEG quality
            mime_type = "image/jpeg"
        else:
            logger.error(f"Unsupported image format: {image_format}")
            return None, None

        img_bytes_io.seek(0)
        logger.debug(f"Rendered page {page.number + 1} to {image_format.upper()} bytes.")
        return img_bytes_io.getvalue(), mime_type

    except Exception as e:
        logger.error(f"Error rendering page {page.number + 1} to image: {e}")
        return None, None

def extract_all_text(pdf_path: str) -> Optional[str]:
    """
    Extract all text from a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        str: Concatenated text from all pages, or None if there was an error
    """
    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF is required for text extraction but is not installed.")
        return None
        
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        all_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            all_text += page.get_text("text") + "\n\n"
        logger.info(f"Extracted text from all pages of '{os.path.basename(pdf_path)}'.")
        return all_text
    except Exception as e:
        logger.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return None
    finally:
        if doc:
            doc.close()

def save_page_as_temp_pdf(original_doc: pymupdf.Document, page_num: int) -> Optional[str]:
    """
    Save a specific page as a temporary PDF file.

    Args:
        original_doc: The open original PDF document
        page_num: The page number (zero-based)

    Returns:
        str: Path to the temporary PDF file, or None if there was an error
    """
    if not PYMUPDF_AVAILABLE:
        logger.error("PyMuPDF is required for PDF processing but is not installed.")
        return None
        
    new_doc = None
    temp_pdf_path = None
    
    try:
        # Create a temporary file with a proper naming pattern
        with tempfile.NamedTemporaryFile(suffix=".pdf", prefix="describepdf_page_", delete=False) as tmp_file:
            temp_pdf_path = tmp_file.name
        
        # Create new document with the single page
        new_doc = pymupdf.open()
        new_doc.insert_pdf(original_doc, from_page=page_num, to_page=page_num)
        new_doc.save(temp_pdf_path)
        
        logger.debug(f"Saved page {page_num + 1} to temporary PDF: {temp_pdf_path}")
        return temp_pdf_path
        
    except Exception as e:
        logger.error(f"Error saving page {page_num + 1} as temporary PDF: {e}")
        # Clean up on error
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
                logger.debug(f"Cleaned up temporary PDF due to error: {temp_pdf_path}")
            except OSError as os_err:
                logger.warning(f"Failed to remove temporary PDF after error: {os_err}")
        return None
        
    finally:
        # Close the new document
        if new_doc:
            new_doc.close()