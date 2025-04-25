"""
Core module for DescribePDF.

This module contains the main orchestration logic for converting PDFs to Markdown descriptions.
"""

import os
import time
from typing import Dict, Any, Callable, Tuple, List, Optional
import contextlib
import logging

from . import config
from . import pdf_processor
from . import markitdown_processor
from . import summarizer
from . import openrouter_client
from . import ollama_client

# Get logger from config module
logger = logging.getLogger('describepdf')

class ConversionError(Exception):
    """Error raised during PDF conversion process."""
    pass

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
    logger.info("Starting conversion process...")

    # Validate provider
    provider = cfg.get("provider", "openrouter").lower()
    logger.info(f"Using provider: {provider}")

    if provider == "openrouter":
        api_key = cfg.get("openrouter_api_key")
        if not api_key:
            msg = "Error: OpenRouter API Key is missing."
            logger.error(msg)
            progress_callback(0.0, msg)
            return msg, None
    elif provider == "ollama":
        ollama_endpoint = cfg.get("ollama_endpoint", "http://localhost:11434")
        if not ollama_client.OLLAMA_AVAILABLE:
            msg = "Error: Ollama Python client not installed. Install with 'pip install ollama'."
            logger.error(msg)
            progress_callback(0.0, msg)
            return msg, None
        
        if not ollama_client.check_ollama_availability(ollama_endpoint):
            msg = f"Error: Could not connect to Ollama at {ollama_endpoint}. Make sure it is running."
            logger.error(msg)
            progress_callback(0.0, msg)
            return msg, None
    else:
        msg = f"Error: Unknown provider '{provider}'. Use 'openrouter' or 'ollama'."
        logger.error(msg)
        progress_callback(0.0, msg)
        return msg, None

    # Validate input file
    if not pdf_path or not os.path.exists(pdf_path) or not os.path.isfile(pdf_path):
        msg = "Error: Invalid or missing PDF file."
        logger.error(msg)
        progress_callback(0.0, msg)
        return msg, None

    original_filename = os.path.basename(pdf_path)
    logger.info(f"Processing file: {original_filename}")

    pdf_doc = None

    try:
        # Load required prompts
        required_prompts = config.get_required_prompts_for_config(cfg)
        if not required_prompts:
            msg = "Error: Could not load all required prompt templates. Check the 'prompts' directory."
            progress_callback(0.0, msg)
            logger.error(msg)
            return msg, None

        # Generate summary if needed
        pdf_summary = None
        summary_progress = 0.05
        if cfg.get("use_summary"):
            summary_model = cfg.get("summary_llm_model")
            progress_callback(summary_progress, f"Generating summary using {summary_model}...")
            try:
                pdf_summary = summarizer.generate_summary(
                    pdf_path, 
                    provider=provider, 
                    api_key=cfg.get("openrouter_api_key"), 
                    ollama_endpoint=cfg.get("ollama_endpoint"), 
                    model=summary_model
                )
                
                if pdf_summary:
                    progress_callback(summary_progress, "Summary generated.")
                    logger.info("PDF summary generated.")
                else:
                    progress_callback(summary_progress, "Warning: Could not generate summary (LLM might have returned empty).")
                    logger.warning("Failed to generate PDF summary or summary was empty.")
                    # Set use_summary to False since we don't have a summary
                    cfg["use_summary"] = False
            except Exception as e:
                 error_msg = f"Warning: Summary generation failed: {e}"
                 progress_callback(summary_progress, error_msg)
                 logger.warning(error_msg)
                 # Set use_summary to False since summary generation failed
                 cfg["use_summary"] = False
        else:
            summary_progress = 0.0

        # Load PDF and process pages
        pdf_load_progress = summary_progress + 0.05
        progress_callback(pdf_load_progress, "Analyzing PDF structure...")
        
        # Use context manager to ensure PDF document is closed
        with contextlib.ExitStack() as stack:
            pdf_doc, pages, total_pages = pdf_processor.get_pdf_pages(pdf_path)
            
            # Register PDF document for cleanup only if it was successfully opened
            if pdf_doc is not None:
                stack.callback(pdf_doc.close)
            else:
                msg = f"Error: Could not process PDF file: {original_filename}"
                progress_callback(pdf_load_progress, msg)
                logger.error(msg)
                return msg, None

            if not pages or total_pages == 0:
                msg = f"Error: PDF file is empty: {original_filename}"
                progress_callback(pdf_load_progress, msg)
                logger.error(msg)
                return msg, None
                
            progress_callback(pdf_load_progress, f"PDF has {total_pages} pages. Starting page processing...")

            # Process each page
            all_descriptions = []
            page_processing_progress_start = pdf_load_progress
            total_page_progress_ratio = (0.98 - page_processing_progress_start) if total_pages > 0 else 0

            for i, page in enumerate(pages):
                page_num = i + 1
                current_page_ratio = (page_num / total_pages) if total_pages > 0 else 1.0
                
                # Calculate progress for this specific page
                current_progress = page_processing_progress_start + (current_page_ratio * total_page_progress_ratio)

                # Update progress for the start of page processing 
                progress_callback(current_progress, f"Processing page {page_num}/{total_pages}...")
                logger.info(f"Processing page {page_num}/{total_pages}")

                page_description = None
                temp_page_pdf_path = None

                try:
                    # Render page to image
                    render_progress_message = f"Page {page_num}: Rendering image..."
                    progress_callback(current_progress, render_progress_message)
                    image_bytes, mime_type = pdf_processor.render_page_to_image_bytes(page, image_format="jpeg")
                    if not image_bytes:
                        logger.warning(f"Could not render image for page {page_num}. Skipping VLM call.")
                        all_descriptions.append(f"*Error: Could not render image for page {page_num}.*")
                        continue

                    # Extract markdown context if needed
                    markdown_context = None
                    if cfg.get("use_markitdown"):
                        markitdown_progress_message = f"Page {page_num}: Extracting text (Markitdown)..."
                        progress_callback(current_progress, markitdown_progress_message)
                        
                        # Verify Markitdown availability
                        if not markitdown_processor.MARKITDOWN_AVAILABLE:
                            logger.warning(f"Markitdown not available for page {page_num}. Proceeding without it.")
                            progress_callback(current_progress, f"Page {page_num}: Markitdown not available, skipping extraction.")
                        else:
                            temp_page_pdf_path = pdf_processor.save_page_as_temp_pdf(pdf_doc, i)
                            
                            if temp_page_pdf_path:
                                # Register temp file for cleanup
                                stack.callback(lambda p=temp_page_pdf_path: os.remove(p) if os.path.exists(p) else None)
                                
                                try:
                                    markdown_context = markitdown_processor.get_markdown_for_page_via_temp_pdf(temp_page_pdf_path)
                                    if markdown_context is None:
                                        logger.warning(f"Markitdown failed for page {page_num}. Proceeding without it.")
                                        progress_callback(current_progress, f"Page {page_num}: Markitdown extraction failed.")
                                    else:
                                        logger.info(f"Markitdown context extracted for page {page_num}.")
                                except Exception as markdown_err:
                                    logger.warning(f"Error extracting Markitdown for page {page_num}: {markdown_err}")
                                    progress_callback(current_progress, f"Page {page_num}: Markitdown extraction error.")
                            else:
                                logger.warning(f"Could not create temporary PDF for Markitdown on page {page_num}.")
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
                        logger.error(error_msg)
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
                    vlm_progress_message = f"Page {page_num}: Calling VLM ({vlm_model})..."
                    progress_callback(current_progress, vlm_progress_message)
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
                            logger.info(f"VLM description received for page {page_num}.")
                        else:
                            page_description = f"*Warning: VLM did not return a description for page {page_num}.*"
                            progress_callback(current_progress, f"Page {page_num}: VLM returned no description.")
                            logger.warning(f"VLM returned no description for page {page_num}.")

                    except (ValueError, ConnectionError, TimeoutError, ImportError) as api_err:
                        error_msg = f"API Error on page {page_num}: {api_err}. Aborting."
                        progress_callback(current_progress, error_msg)
                        logger.error(error_msg)
                        raise ConversionError(error_msg)

                    except Exception as vlm_err:
                        error_msg = f"Unexpected error during VLM call for page {page_num}: {vlm_err}. Skipping page."
                        progress_callback(current_progress, error_msg)
                        logger.exception(error_msg)
                        page_description = f"*Error: Failed to get VLM description for page {page_num} due to an unexpected error.*"

                    all_descriptions.append(page_description if page_description else "*No description available.*")

                except ConversionError:
                    # Let critical errors propagate up
                    raise
                except Exception as page_err:
                    error_msg = f"Unexpected error processing page {page_num}: {page_err}. Skipping page."
                    progress_callback(current_progress, error_msg)
                    logger.exception(error_msg)
                    all_descriptions.append(f"*Error: An unexpected error occurred while processing page {page_num}.*")

        # Generate final markdown
        final_progress = 0.99
        progress_callback(final_progress, "Combining page descriptions into final Markdown...")
        final_markdown = format_markdown_output(all_descriptions, original_filename)
        logger.info("Final Markdown content assembled.")

        # Report completion
        end_time = time.time()
        duration = end_time - start_time
        final_status = f"Conversion completed successfully in {duration:.2f} seconds."
        progress_callback(1.0, final_status)
        logger.info(final_status)

        return final_status, final_markdown

    except ConversionError as critical_err:
        return str(critical_err), None

    except Exception as e:
        error_msg = f"Critical Error during conversion: {e}"
        progress_callback(0.0, error_msg)
        logger.exception(error_msg)
        return error_msg, None