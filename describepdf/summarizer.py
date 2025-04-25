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

# Get logger from config module
logger = logging.getLogger('describepdf')

# Constants
MAX_CHARS_FOR_PROMPT = 512000  # Maximum characters to include in prompt (128K tokens approx.)

def generate_summary(
    pdf_path: str,
    provider: str = "openrouter",
    api_key: Optional[str] = None,
    ollama_endpoint: Optional[str] = None,
    model: Optional[str] = None
) -> Optional[str]:
    """
    Generate a summary of the complete textual content of a PDF using specified provider.

    Args:
        pdf_path: Path to the PDF file
        provider: Provider to use ("openrouter" or "ollama")
        api_key: OpenRouter API key (required for openrouter provider)
        ollama_endpoint: Ollama endpoint URL (required for ollama provider)
        model: LLM model to use for the summary

    Returns:
        str: The generated summary, or None if any step fails
    """
    logger.info(f"Starting summary generation for '{pdf_path}' using provider {provider} with model {model}.")

    # Extract text from PDF
    logger.info("Extracting full text from PDF...")
    full_text = pdf_processor.extract_all_text(pdf_path)
    
    # Handle error cases
    if full_text is None:
        logger.error("Failed to extract text for summary.")
        return None
        
    if not full_text.strip():
        logger.warning("PDF contains no extractable text for summary.")
        return "Document contains no extractable text."

    logger.info(f"Text extracted ({len(full_text)} characters). Preparing summary prompt...")

    # Load and prepare prompt
    prompts = get_prompts()
    summary_prompt_template = prompts.get("summary")
    if not summary_prompt_template:
        logger.error("Summary prompt template not found.")
        return None

    # Truncate text if too long
    if len(full_text) > MAX_CHARS_FOR_PROMPT:
        logger.warning(
            f"PDF text ({len(full_text)} chars) exceeds limit ({MAX_CHARS_FOR_PROMPT}), truncating for summary."
        )
        full_text = full_text[:MAX_CHARS_FOR_PROMPT] + "\n\n[... text truncated ...]"

    # Fill prompt template
    prompt_text = summary_prompt_template.replace("[FULL_PDF_TEXT]", full_text)

    # Call LLM for summary based on provider
    try:
        if provider == "openrouter":
            if not api_key:
                logger.error("OpenRouter API key is required for OpenRouter provider.")
                return None
                
            logger.info(f"Calling OpenRouter LLM for summary (model: {model})...")
            summary = openrouter_client.get_llm_summary(api_key, model, prompt_text)
            if summary:
                logger.info("Summary generated successfully via OpenRouter.")
                return summary
            else:
                logger.error("OpenRouter LLM call for summary returned no content.")
                return None
                
        elif provider == "ollama":
            if not ollama_endpoint:
                logger.error("Ollama endpoint URL is required for Ollama provider.")
                return None
                
            logger.info(f"Calling Ollama LLM for summary (model: {model})...")
            summary = ollama_client.get_llm_summary(ollama_endpoint, model, prompt_text)
            if summary:
                logger.info("Summary generated successfully via Ollama.")
                return summary
            else:
                logger.error("Ollama LLM call for summary returned no content.")
                return None
                
        else:
            logger.error(f"Unsupported provider: {provider}")
            return None
            
    except (ValueError, ConnectionError, TimeoutError, ImportError) as e:
        logger.error(f"Failed to generate summary due to API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during summary generation: {e}")
        return None