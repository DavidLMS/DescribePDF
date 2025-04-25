"""
Core module for DescribePDF.

This module contains the main orchestration logic for converting PDFs to Markdown descriptions.
"""

import os
import logging
import time
from typing import Dict, Any, Callable, Tuple, List, Optional
import contextlib

from . import config
from . import pdf_processor
from . import markitdown_processor
from . import summarizer
from . import openrouter_client
from . import ollama_client

def format_markdown_output(descriptions: List[str], original_filename: str) -> str:
    """
    Combine page descriptions into a single Markdown file.

    Args:
        descriptions: List of strings, each being a description of a page
        original_filename: Name of the original PDF file

    Returns:
        str: Complete Markdown content
    """
    md_content = f"# Description of PDF: {original_filename}\n\n"
    for i, desc in enumerate(descriptions):
        md_content += f"## Page {i + 1}\n\n"
        md_content += desc if desc else "*No description generated for this page.*"
        md_content += "\n\n---\n\n"
    return md_content

def convert_pdf_to_markdown(
    pdf_path: str,
    cfg: Dict[str, Any],
    progress_callback: Callable[[float, str], None]
) -> Tuple[str, Optional[str]]:
    """
    Orchestrate the complete PDF to descriptive Markdown conversion process.

    Args:
        pdf_path: Path to the PDF file
        cfg: Configuration dictionary for this run
        progress_callback: Function accepting (float_progress, string_status)

    Returns:
        tuple: (status_message, result_markdown or None)
    """
    start_time = time.time()
    progress_callback(0.0, "Starting conversion process...")
    logging.info("Starting conversion process...")

    # Validate provider
    provider = cfg.get("provider", "openrouter").lower()
    logging.info(f"Using provider: {provider}")

    if provider == "openrouter":
        api_key = cfg.get("openrouter_api_key")
        if not api_key:
            msg = "Error: OpenRouter API Key is missing."
            logging.error(msg)
            progress_callback(0.0, msg)
            return msg, None
    elif provider == "ollama":
        ollama_endpoint = cfg.get("ollama_endpoint", "http://localhost:11434")
        if not ollama_client.OLLAMA_AVAILABLE:
            msg = "Error: Ollama Python client not installed. Install with 'pip install ollama'."
            logging.error(msg)
            progress_callback(0.0, msg)
            return msg, None
        
        if not ollama_client.check_ollama_availability(ollama_endpoint):
            msg = f"Error: Could not connect to Ollama at {ollama_endpoint}. Make sure it is running."
            logging.error(msg)
            progress_callback(0.0, msg)
            return msg, None
    else:
        msg = f"Error: Unknown provider '{provider}'. Use 'openrouter' or 'ollama'."
        logging.error(msg)
        progress_callback(0.0, msg)
        return msg, None

    # Validate input file
    if not pdf_path or not os.path.exists(pdf_path) or not os.path.isfile(pdf_path):
        msg = "Error: Invalid or missing PDF file."
        logging.error(msg)
        progress_callback(0.0, msg)
        return msg, None

    original_filename = os.path.basename(pdf_path)
    logging.info(f"Processing file: {original_filename}")

    temp_page_files = []
    pdf_doc = None

    try:
        # Load required prompts
        required_prompts = config.get_required_prompts_for_config(cfg)
        if not required_prompts:
            msg = "Error: Could not load all required prompt templates. Check the 'prompts' directory."
            progress_callback(0.0, msg)
            logging.error(msg)
            return msg, None

        # Generate summary if needed
        pdf_summary = None
        summary_progress = 0.05
        if cfg.get("use_summary"):
            summary_model = cfg.get("summary_llm_model")
            progress_callback(summary_progress, f"Generating summary using {summary_model}...")
            try:
                if provider == "openrouter":
                    pdf_summary = summarizer.generate_summary_openrouter(
                        pdf_path, cfg.get("openrouter_api_key"), summary_model
                    )
                elif provider == "ollama":
                    pdf_summary = summarizer.generate_summary_ollama(
                        pdf_path, cfg.get("ollama_endpoint"), summary_model
                    )
                
                if pdf_summary:
                    progress_callback(summary_progress, "Summary generated.")
                    logging.info("PDF summary generated.")
                else:
                    progress_callback(summary_progress, "Warning: Could not generate summary (LLM might have returned empty).")
                    logging.warning("Failed to generate PDF summary or summary was empty.")
            except Exception as e:
                 error_msg = f"Warning: Summary generation failed: {e}"
                 progress_callback(summary_progress, error_msg)
                 logging.warning(error_msg)
                 # Continue without summary
        else:
            summary_progress = 0.0

        # Load PDF and process pages
        pdf_load_progress = summary_progress + 0.05
        progress_callback(pdf_load_progress, "Analyzing PDF structure...")
        pdf_doc, pages, total_pages = pdf_processor.get_pdf_pages(pdf_path)

        if pdf_doc is None or not pages or total_pages == 0:
            msg = f"Error: Could not process PDF file or PDF is empty: {original_filename}"
            progress_callback(pdf_load_progress, msg)
            logging.error(msg)
            if pdf_doc:
                pdf_doc.close()
            return msg, None
            
        progress_callback(pdf_load_progress, f"PDF has {total_pages} pages. Starting page processing...")

        # Process each page
        all_descriptions = []
        page_processing_progress_start = pdf_load_progress
        total_page_progress_ratio = (0.98 - page_processing_progress_start) if total_pages > 0 else 0

        for i, page in enumerate(pages):
            page_num = i + 1
            current_page_ratio = (page_num / total_pages) if total_pages > 0 else 1.0
            current_progress = page_processing_progress_start + (current_page_ratio * total_page_progress_ratio)

            progress_callback(current_progress, f"Processing page {page_num}/{total_pages}...")
            logging.info(f"Processing page {page_num}/{total_pages}")

            page_description = None
            temp_page_pdf_path = None

            try:
                # Render page to image
                progress_callback(current_progress, f"Page {page_num}: Rendering image...")
                image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(page, image_format="jpeg")
                if not image_bytes:
                    logging.warning(f"Could not render image for page {page_num}. Skipping VLM call.")
                    all_descriptions.append(f"*Error: Could not render image for page {page_num}.*")
                    continue

                # Extract markdown context if needed
                markdown_context = None
                if cfg.get("use_markitdown"):
                    progress_callback(current_progress, f"Page {page_num}: Extracting text (Markitdown)...")
                    with contextlib.ExitStack() as stack:
                        temp_page_pdf_path = pdf_processor.save_page_as_temp_pdf(pdf_doc, i)
                        if temp_page_pdf_path:
                            # Register a cleanup callback
                            stack.callback(lambda: os.remove(temp_page_pdf_path) if os.path.exists(temp_page_pdf_path) else None)
                            temp_page_files.append(temp_page_pdf_path)
                            
                            markdown_context = markitdown_processor.get_markdown_for_page_via_temp_pdf(temp_page_pdf_path)
                            if markdown_context is None:
                                logging.warning(f"Markitdown failed for page {page_num}. Proceeding without it.")
                                progress_callback(current_progress, f"Page {page_num}: Markitdown extraction failed.")
                            else:
                                logging.info(f"Markitdown context extracted for page {page_num}.")
                        else:
                            logging.warning(f"Could not create temporary PDF for Markitdown on page {page_num}.")
                            progress_callback(current_progress, f"Page {page_num}: Failed to prepare for Markitdown.")

                # Select appropriate prompt
                prompt_key = "vlm_base"
                has_markdown = cfg.get("use_markitdown") and markdown_context is not None
                has_summary = cfg.get("use_summary") and pdf_summary is not None

                if has_markdown and has_summary:
                    prompt_key = "vlm_full"
                elif has_markdown:
                    prompt_key = "vlm_markdown"
                elif has_summary:
                    prompt_key = "vlm_summary"

                vlm_prompt_template = required_prompts.get(prompt_key)
                if not vlm_prompt_template:
                    error_msg = f"Missing required prompt template: {prompt_key}"
                    progress_callback(current_progress, error_msg)
                    logging.error(error_msg)
                    all_descriptions.append(f"*Error: Could not generate description for page {page_num} due to missing prompt template.*")
                    continue

                # Prepare prompt
                prompt_text = vlm_prompt_template.replace("[PAGE_NUM]", str(page_num))
                prompt_text = prompt_text.replace("[TOTAL_PAGES]", str(total_pages))
                prompt_text = prompt_text.replace("[LANGUAGE]", cfg.get("output_language", "English"))
                if "[MARKDOWN_CONTEXT]" in prompt_text:
                    prompt_text = prompt_text.replace("[MARKDOWN_CONTEXT]", markdown_context if markdown_context else "N/A")
                if "[SUMMARY_CONTEXT]" in prompt_text:
                    prompt_text = prompt_text.replace("[SUMMARY_CONTEXT]", pdf_summary if pdf_summary else "N/A")

                # Call VLM
                vlm_model = cfg.get("vlm_model")
                progress_callback(current_progress, f"Page {page_num}: Calling VLM ({vlm_model})...")
                try:
                    if provider == "openrouter":
                        page_description = openrouter_client.get_vlm_description(
                            cfg.get("openrouter_api_key"), vlm_model, prompt_text, image_bytes, mime_type
                        )
                    elif provider == "ollama":
                        page_description = ollama_client.get_vlm_description(
                            cfg.get("ollama_endpoint"), vlm_model, prompt_text, image_bytes, mime_type
                        )
                    
                    if page_description:
                        logging.info(f"VLM description received for page {page_num}.")
                    else:
                        page_description = f"*Warning: VLM did not return a description for page {page_num}.*"
                        progress_callback(current_progress, f"Page {page_num}: VLM returned no description.")
                        logging.warning(f"VLM returned no description for page {page_num}.")

                except (ValueError, ConnectionError, TimeoutError, ImportError) as api_err:
                    error_msg = f"API Error on page {page_num}: {api_err}. Aborting."
                    progress_callback(current_progress, error_msg)
                    logging.error(error_msg)
                    raise ConnectionError(error_msg)

                except Exception as vlm_err:
                    error_msg = f"Unexpected error during VLM call for page {page_num}: {vlm_err}. Skipping page."
                    progress_callback(current_progress, error_msg)
                    logging.exception(error_msg)
                    page_description = f"*Error: Failed to get VLM description for page {page_num} due to an unexpected error.*"

                all_descriptions.append(page_description if page_description else "*No description available.*")

            except Exception as page_err:
                error_msg = f"Unexpected error processing page {page_num}: {page_err}. Skipping page."
                progress_callback(current_progress, error_msg)
                logging.exception(error_msg)
                all_descriptions.append(f"*Error: An unexpected error occurred while processing page {page_num}.*")

        # Generate final markdown
        final_progress = 0.99
        progress_callback(final_progress, "Combining page descriptions into final Markdown...")
        final_markdown = format_markdown_output(all_descriptions, original_filename)
        logging.info("Final Markdown content assembled.")

        # Report completion
        end_time = time.time()
        duration = end_time - start_time
        final_status = f"Conversion completed successfully in {duration:.2f} seconds."
        progress_callback(1.0, final_status)
        logging.info(final_status)

        return final_status, final_markdown

    except ConnectionError as critical_api_err:
        return str(critical_api_err), None

    except Exception as e:
        error_msg = f"Critical Error during conversion: {e}"
        progress_callback(0.0, error_msg)
        logging.exception(error_msg)
        return error_msg, None

    finally:
        logging.debug("Performing final cleanup...")
        # Clean up PDF document
        if pdf_doc:
            try:
                pdf_doc.close()
                logging.debug("Closed main PDF document.")
            except Exception as e:
                logging.warning(f"Error closing PDF document: {e}")

        # Clean up any leftover temporary files
        for temp_f in temp_page_files:
            if os.path.exists(temp_f):
                try:
                    os.remove(temp_f)
                    logging.debug(f"Cleaned up leftover temporary page PDF: {temp_f}")
                except OSError as e:
                    logging.warning(f"Could not remove leftover temporary page PDF {temp_f}: {e}")