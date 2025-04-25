"""
Summarizer module for DescribePDF.

This module handles the generation of document summaries from PDF text content
using either OpenRouter or Ollama LLM models.
"""

import logging
from typing import Optional

from . import pdf_processor
from . import openrouter_client
from . import ollama_client
from .config import get_prompts

# Constants
MAX_CHARS_FOR_PROMPT = 512000  # Maximum characters to include in prompt (128K tokens approx.)

def generate_summary_openrouter(pdf_path: str, api_key: str, model: str) -> Optional[str]:
    """
    Generate a summary of the complete textual content of a PDF using OpenRouter.

    Args:
        pdf_path: Path to the PDF file
        api_key: OpenRouter API key
        model: LLM model to use for the summary

    Returns:
        str: The generated summary, or None if any step fails
    """
    logging.info(f"Starting summary generation for '{pdf_path}' using OpenRouter model {model}.")

    # Extract text from PDF
    logging.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    
    # Handle error cases
    if full_text is None:
        logging.error("Failed to extract text for summary.")
        return None
        
    if not full_text.strip():
        logging.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logging.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    # Load and prepare prompt
    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logging.error("Summary prompt template not found.")
        return None

    # Truncate text if too long
    if len(full_text) > MAX_CHARS_FOR_PROMPT:
        logging.warning(
            f"PDF text ({len(full_text)} chars) exceeds limit ({MAX_CHARS_FOR_PROMPT}), truncating for summary."
        )
        full_text = full_text[:MAX_CHARS_FOR_PROMPT] + "\n\n[... text truncated ...]"

    # Fill prompt template
    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    # Call LLM for summary
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

def generate_summary_ollama(pdf_path: str, endpoint: str, model: str) -> Optional[str]:
    """
    Generate a summary of the complete textual content of a PDF using Ollama.

    Args:
        pdf_path: Path to the PDF file
        endpoint: Ollama API endpoint URL
        model: LLM model to use for the summary

    Returns:
        str: The generated summary, or None if any step fails
    """
    logging.info(f"Starting summary generation for '{pdf_path}' using Ollama model {model}.")

    # Extract text from PDF
    logging.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    
    # Handle error cases
    if full_text is None:
        logging.error("Failed to extract text for summary.")
        return None
        
    if not full_text.strip():
        logging.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logging.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    # Load and prepare prompt
    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logging.error("Summary prompt template not found.")
        return None

    # Truncate text if too long
    if len(full_text) > MAX_CHARS_FOR_PROMPT:
        logging.warning(
            f"PDF text ({len(full_text)} chars) exceeds limit ({MAX_CHARS_FOR_PROMPT}), truncating for summary."
        )
        full_text = full_text[:MAX_CHARS_FOR_PROMPT] + "\n\n[... text truncated ...]"

    # Fill prompt template
    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    # Call LLM for summary
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