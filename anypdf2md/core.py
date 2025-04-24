import os
import logging
import tempfile
import time

from . import config
from . import pdf_processor
from . import markitdown_processor
from . import summarizer
from . import openrouter_client

def format_markdown_output(descriptions: list, original_filename: str):
    """
    Combina las descripciones de página en un único archivo Markdown.

    Args:
        descriptions (list): Lista de strings, cada uno es la descripción de una página.
        original_filename (str): Nombre del archivo PDF original.

    Returns:
        str: El contenido Markdown completo.
    """
    md_content = f"# Description of PDF: {original_filename}\n\n"
    for i, desc in enumerate(descriptions):
        md_content += f"## Page {i + 1}\n\n"
        md_content += desc if desc else "*No description generated for this page.*"
        md_content += "\n\n---\n\n" # Separador claro
    return md_content

def convert_pdf_to_markdown(
    pdf_file_obj, # Objeto archivo de Gradio
    cfg: dict,
    progress_callback # Función para reportar progreso
):
    """
    Orquesta el proceso completo de conversión de PDF a Markdown descriptivo.

    Args:
        pdf_file_obj: Objeto archivo temporal de Gradio.
        cfg (dict): Diccionario de configuración actual.
        progress_callback: Función que acepta un string de estado.

    Returns:
        tuple: (str, str or None) - (status_message, result_markdown or None)
    """
    start_time = time.time()
    progress_callback("Starting conversion process...")
    logging.info("Starting conversion process...")

    # --- Validación Inicial ---
    api_key = cfg.get("openrouter_api_key")
    if not api_key:
        msg = "Error: OpenRouter API Key is not configured."
        logging.error(msg)
        progress_callback(msg)
        return msg, None

    if not pdf_file_obj:
        msg = "Error: No PDF file provided."
        logging.error(msg)
        progress_callback(msg)
        return msg, None

    original_filename = os.path.basename(pdf_file_obj.name)
    logging.info(f"Processing file: {original_filename}")

    # Guardar el archivo subido a una ruta temporal permanente (PyMuPDF la necesita)
    temp_pdf_path = None
    pdf_doc = None
    pages = []
    temp_page_files = [] # Para guardar rutas de PDFs temporales de Markitdown

    try:
        # Crear un archivo temporal con extensión .pdf
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", prefix="anypdf2md_") as temp_file:
            temp_pdf_path = temp_file.name
            # Copiar contenido del objeto de Gradio al archivo temporal
            with open(pdf_file_obj.name, 'rb') as source_f:
                temp_file.write(source_f.read())
        logging.info(f"PDF saved temporarily to: {temp_pdf_path}")

        # --- Cargar Prompts ---
        prompts = config.get_prompts()
        if not prompts:
             msg = "Error: Could not load prompt templates."
             progress_callback(msg)
             logging.error(msg)
             return msg, None

        # --- Generar Resumen (Opcional) ---
        pdf_summary = None
        if cfg.get("use_summary"):
            progress_callback(f"Generating summary using {cfg.get('summary_llm_model')}...")
            try:
                pdf_summary = summarizer.generate_summary(
                    temp_pdf_path, api_key, cfg.get("summary_llm_model")
                )
                if pdf_summary:
                    progress_callback("Summary generated.")
                    logging.info("PDF summary generated.")
                else:
                    # No detener el proceso, solo advertir
                    progress_callback("Warning: Could not generate summary.")
                    logging.warning("Failed to generate PDF summary.")
            except Exception as e:
                 # No detener el proceso, solo advertir
                 error_msg = f"Warning: Summary generation failed: {e}"
                 progress_callback(error_msg)
                 logging.warning(error_msg)


        # --- Procesar PDF ---
        progress_callback("Analyzing PDF structure...")
        pdf_doc, pages, total_pages = pdf_processor.get_pdf_pages(temp_pdf_path)
        if not pages:
            msg = f"Error: Could not process PDF file: {original_filename}"
            progress_callback(msg)
            logging.error(msg)
            return msg, None
        progress_callback(f"PDF has {total_pages} pages. Starting page processing...")

        # --- Bucle por Página ---
        all_descriptions = []
        for i, page in enumerate(pages):
            page_num = i + 1
            progress_callback(f"Processing page {page_num}/{total_pages}...")
            logging.info(f"Processing page {page_num}/{total_pages}")

            page_description = None
            temp_page_pdf_path = None # Para Markitdown

            try:
                # 1. Generar Imagen
                progress_callback(f"Page {page_num}: Rendering image...")
                image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(page, image_format="jpeg") # JPEG suele ser más pequeño
                if not image_bytes:
                    logging.warning(f"Could not render image for page {page_num}. Skipping VLM call.")
                    all_descriptions.append(f"*Error: Could not render image for page {page_num}.*")
                    continue # Saltar al siguiente ciclo

                # 2. Procesar Markitdown (Opcional)
                markdown_context = None
                if cfg.get("use_markitdown"):
                    progress_callback(f"Page {page_num}: Extracting text (Markitdown)...")
                    # Guardar página como PDF temporal para Markitdown
                    temp_page_pdf_path = pdf_processor.save_page_as_temp_pdf(pdf_doc, i)
                    if temp_page_pdf_path:
                        temp_page_files.append(temp_page_pdf_path) # Añadir a la lista para limpieza
                        markdown_context = markitdown_processor.get_markdown_for_page_via_temp_pdf(temp_page_pdf_path)
                        if markdown_context is None:
                             logging.warning(f"Markitdown failed for page {page_num}. Proceeding without it.")
                             progress_callback(f"Page {page_num}: Markitdown extraction failed.")
                        else:
                             logging.info(f"Markitdown context extracted for page {page_num}.")
                    else:
                        logging.warning(f"Could not create temporary PDF for Markitdown on page {page_num}.")
                        progress_callback(f"Page {page_num}: Failed to prepare for Markitdown.")


                # 3. Construir Prompt VLM
                prompt_key = "vlm_base"
                if cfg.get("use_markitdown") and cfg.get("use_summary"):
                    prompt_key = "vlm_full"
                elif cfg.get("use_markitdown"):
                    prompt_key = "vlm_markdown"
                elif cfg.get("use_summary"):
                    prompt_key = "vlm_summary"

                vlm_prompt_template = prompts.get(prompt_key)
                if not vlm_prompt_template:
                    msg = f"Error: VLM prompt template '{prompt_key}' not found."
                    progress_callback(msg)
                    logging.error(msg)
                    # Podríamos intentar continuar con una base o fallar todo
                    return msg, None

                prompt_text = vlm_prompt_template.replace("[PAGE_NUM]", str(page_num))
                prompt_text = prompt_text.replace("[TOTAL_PAGES]", str(total_pages))
                prompt_text = prompt_text.replace("[LANGUAGE]", cfg.get("output_language", "English"))
                if "[MARKDOWN_CONTEXT]" in prompt_text:
                    prompt_text = prompt_text.replace("[MARKDOWN_CONTEXT]", markdown_context if markdown_context else "N/A")
                if "[SUMMARY_CONTEXT]" in prompt_text:
                    prompt_text = prompt_text.replace("[SUMMARY_CONTEXT]", pdf_summary if pdf_summary else "N/A")

                # 4. Llamar API VLM
                progress_callback(f"Page {page_num}: Calling VLM ({cfg.get('vlm_model')})...")
                try:
                    page_description = openrouter_client.get_vlm_description(
                        api_key, cfg.get("vlm_model"), prompt_text, image_bytes, mime_type
                    )
                    if page_description:
                        progress_callback(f"Page {page_num}: Description received.")
                        logging.info(f"VLM description received for page {page_num}.")
                    else:
                        # No detener, pero registrar
                        page_description = f"*Warning: VLM did not return a description for page {page_num}.*"
                        progress_callback(f"Page {page_num}: VLM returned no description.")
                        logging.warning(f"VLM returned no description for page {page_num}.")

                except (ValueError, ConnectionError, TimeoutError) as api_err:
                     # Error de API (clave inválida, timeout, conexión, etc.)
                     error_msg = f"API Error on page {page_num}: {api_err}. Aborting."
                     progress_callback(error_msg)
                     logging.error(error_msg)
                     return error_msg, None # Abortar todo el proceso
                except Exception as vlm_err:
                     # Error inesperado durante la llamada VLM
                     error_msg = f"Unexpected error during VLM call for page {page_num}: {vlm_err}. Skipping page."
                     progress_callback(error_msg)
                     logging.exception(error_msg) # Log con traceback
                     page_description = f"*Error: Failed to get VLM description for page {page_num} due to an unexpected error.*"


                all_descriptions.append(page_description if page_description else "*No description available.*")

            except Exception as page_err:
                # Captura errores inesperados dentro del bucle de página
                error_msg = f"Unexpected error processing page {page_num}: {page_err}. Skipping page."
                progress_callback(error_msg)
                logging.exception(error_msg)
                all_descriptions.append(f"*Error: An unexpected error occurred while processing page {page_num}.*")
            finally:
                # Limpiar el PDF temporal de la página si se creó
                if temp_page_pdf_path and os.path.exists(temp_page_pdf_path):
                    try:
                        os.remove(temp_page_pdf_path)
                        logging.debug(f"Cleaned up temporary page PDF: {temp_page_pdf_path}")
                    except OSError as e:
                        logging.warning(f"Could not remove temporary page PDF {temp_page_pdf_path}: {e}")


        # --- Combinar Resultados ---
        progress_callback("Combining page descriptions into final Markdown...")
        final_markdown = format_markdown_output(all_descriptions, original_filename)
        logging.info("Final Markdown content assembled.")

        end_time = time.time()
        duration = end_time - start_time
        final_status = f"Conversion completed successfully in {duration:.2f} seconds."
        progress_callback(final_status)
        logging.info(final_status)

        return final_status, final_markdown

    except Exception as e:
        # Captura errores fuera del bucle de página (ej. carga inicial PDF, resumen)
        error_msg = f"Critical Error during conversion: {e}"
        progress_callback(error_msg)
        logging.exception(error_msg) # Log completo con traceback
        return error_msg, None

    finally:
        # --- Limpieza Final ---
        logging.debug("Performing final cleanup...")
        if pdf_doc:
            try:
                pdf_doc.close()
                logging.debug("Closed main PDF document.")
            except Exception as e:
                 logging.warning(f"Error closing PDF document: {e}")

        if temp_pdf_path and os.path.exists(temp_pdf_path):
            try:
                os.remove(temp_pdf_path)
                logging.info(f"Cleaned up main temporary PDF: {temp_pdf_path}")
            except OSError as e:
                logging.warning(f"Could not remove temporary PDF {temp_pdf_path}: {e}")

        # Asegurarse de limpiar archivos de página si hubo error antes del finally del bucle
        for temp_f in temp_page_files:
             if os.path.exists(temp_f):
                 try:
                     os.remove(temp_f)
                     logging.debug(f"Cleaned up leftover temporary page PDF: {temp_f}")
                 except OSError as e:
                     logging.warning(f"Could not remove leftover temporary page PDF {temp_f}: {e}")