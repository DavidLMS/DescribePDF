import pymupdf
from PIL import Image
import io
import os
import logging
import tempfile

def get_pdf_pages(pdf_path):
    """
    Abre un PDF y devuelve una lista de objetos de página y el número total de páginas.

    Args:
        pdf_path (str): Ruta al archivo PDF.

    Returns:
        tuple: (list[pymupdf.Page], int) o (None, 0) si hay error.
    """
    try:
        doc = pymupdf.open(pdf_path)
        pages = [doc.load_page(i) for i in range(len(doc))]
        total_pages = len(doc)
        logging.info(f"Opened PDF '{os.path.basename(pdf_path)}' with {total_pages} pages.")
        return doc, pages, total_pages
    except Exception as e:
        logging.error(f"Error opening or reading PDF {pdf_path}: {e}")
        return None, None, 0

def render_page_to_image_bytes(page: pymupdf.Page, image_format="jpeg", dpi=150):
    """
    Renderiza una página de PDF a bytes de imagen en memoria.

    Args:
        page (pymupdf.Page): Objeto de página de PyMuPDF.
        image_format (str): Formato deseado ('png' o 'jpeg').
        dpi (int): Resolución de la imagen.

    Returns:
        tuple: (bytes, str) - Bytes de la imagen y MIME type, o (None, None) en caso de error.
    """
    try:
        pix = page.get_pixmap(dpi=dpi)
        img_bytes_io = io.BytesIO()

        if image_format.lower() == "png":
            img_bytes = pix.tobytes("png")
            img_bytes_io.write(img_bytes)
            mime_type = "image/png"
        elif image_format.lower() == "jpeg":
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.save(img_bytes_io, format="JPEG")
            mime_type = "image/jpeg"
        else:
            logging.error(f"Unsupported image format: {image_format}")
            return None, None

        img_bytes_io.seek(0)
        logging.debug(f"Rendered page {page.number} to {image_format.upper()} bytes.")
        return img_bytes_io.getvalue(), mime_type

    except Exception as e:
        logging.error(f"Error rendering page {page.number} to image: {e}")
        return None, None

def extract_all_text(pdf_path):
    """
    Extrae todo el texto de un archivo PDF.

    Args:
        pdf_path (str): Ruta al archivo PDF.

    Returns:
        str: Texto concatenado de todas las páginas, o None si hay error.
    """
    doc = None
    try:
        doc = pymupdf.open(pdf_path)
        all_text = ""
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            all_text += page.get_text("text") + "\n\n" #
        logging.info(f"Extracted text from all pages of '{os.path.basename(pdf_path)}'.")
        return all_text
    except Exception as e:
        logging.error(f"Error extracting text from PDF {pdf_path}: {e}")
        return None
    finally:
        if doc:
            doc.close()

def save_page_as_temp_pdf(original_doc: pymupdf.Document, page_num: int):
    """
    Guarda una página específica como un archivo PDF temporal.

    Args:
        original_doc (pymupdf.Document): El documento PDF original abierto.
        page_num (int): El número de página (basado en 0).

    Returns:
        str: La ruta al archivo PDF temporal, o None si hay error.
    """
    temp_pdf = None
    new_doc = None
    try:
        temp_pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_pdf_path = temp_pdf_file.name
        temp_pdf_file.close()

        new_doc = pymupdf.open()
        new_doc.insert_pdf(original_doc, from_page=page_num, to_page=page_num)
        new_doc.save(temp_pdf_path)
        logging.debug(f"Saved page {page_num + 1} to temporary PDF: {temp_pdf_path}")
        return temp_pdf_path
    except Exception as e:
        logging.error(f"Error saving page {page_num + 1} as temporary PDF: {e}")
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
        return None
    finally:
        if new_doc:
            new_doc.close()