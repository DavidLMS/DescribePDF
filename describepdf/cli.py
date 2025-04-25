"""
Command-line interface for DescribePDF.

This module provides the CLI functionality for converting PDF files to markdown descriptions.
"""

import argparse
import os
import sys
import logging
from typing import Dict, Any, Callable, Optional
from tqdm import tqdm

from . import config
from . import core
from . import ollama_client

# Get logger from config module
logger = logging.getLogger('describepdf')

def setup_cli_parser() -> argparse.ArgumentParser:
    """
    Set up the command line argument parser.
    
    Returns:
        argparse.ArgumentParser: Configured parser for command line arguments
    """
    parser = argparse.ArgumentParser(
        description="DescribePDF - Convert PDF files to detailed Markdown descriptions",
        epilog="Example: describepdf input.pdf -o output.md -l Spanish"
    )
    
    parser.add_argument(
        "pdf_file", 
        help="Path to the PDF file to process"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Path to the output Markdown file (default: [pdf_name]_description.md)"
    )
    
    parser.add_argument(
        "-k", "--api-key", 
        help="OpenRouter API Key (overrides the one in .env file)"
    )
    
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local Ollama instead of OpenRouter"
    )
    
    parser.add_argument(
        "--endpoint",
        help="Ollama endpoint URL (default: http://localhost:11434)"
    )
    
    parser.add_argument(
        "-m", "--vlm-model", 
        help="VLM model to use (default: configured in .env)"
    )
    
    parser.add_argument(
        "-l", "--language", 
        help="Output language (default: configured in .env)"
    )
    
    parser.add_argument(
        "--use-markitdown", 
        action="store_true", 
        help="Use Markitdown for enhanced text extraction"
    )
    
    parser.add_argument(
        "--use-summary", 
        action="store_true", 
        help="Generate and use a PDF summary"
    )
    
    parser.add_argument(
        "--summary-model", 
        help="Model to generate the summary (default: configured in .env)"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Verbose mode (show debug messages)"
    )

    return parser

def create_progress_callback() -> Callable[[float, str], None]:
    """
    Create a progress callback function that displays progress with tqdm.
    
    Returns:
        Callable[[float, str], None]: Progress callback function
    """
    progress_bar = tqdm(total=100, desc="Processing", unit="%")
    
    def callback(progress_value: float, status: str) -> None:
        """
        Display progress in the command line.
        
        Args:
            progress_value (float): Progress value between 0.0 and 1.0
            status (str): Current status message
        """
        nonlocal progress_bar
        
        current_progress = int(progress_value * 100)
        last_progress = progress_bar.n
        progress_diff = current_progress - last_progress
        
        if progress_diff > 0:
            progress_bar.update(progress_diff)
        
        progress_bar.set_description(status)
        
        if progress_value >= 1.0:
            progress_bar.close()
    
    return callback

def run_cli() -> None:
    """
    Main function for the command line interface.
    
    This function parses arguments, configures the application based on 
    provided parameters, and runs the PDF to Markdown conversion.
    """
    # Parse command line arguments
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate input file exists
    if not os.path.exists(args.pdf_file) or not os.path.isfile(args.pdf_file):
        logger.error(f"The PDF file '{args.pdf_file}' does not exist or is not a valid file.")
        logger.info("Exiting with error code 1")
        sys.exit(1)
    
    # Load configuration from environment
    env_config = config.get_config()
    
    # Determine provider
    provider = "ollama" if args.local else "openrouter"
    
    # Prepare run configuration by merging environment config and CLI args
    run_config: Dict[str, Any] = {
        "provider": provider,
        "output_language": args.language if args.language else env_config.get("output_language"),
        "use_markitdown": args.use_markitdown if args.use_markitdown is not None else env_config.get("use_markitdown"),
        "use_summary": args.use_summary if args.use_summary is not None else env_config.get("use_summary"),
    }
    
    # Configure provider-specific settings
    vlm_model: Optional[str] = args.vlm_model
    summary_model: Optional[str] = args.summary_model
    
    if provider == "openrouter":
        run_config["openrouter_api_key"] = args.api_key if args.api_key else env_config.get("openrouter_api_key")
        
        if not vlm_model:
            vlm_model = env_config.get("or_vlm_model")
        
        if not summary_model and run_config["use_summary"]:
            summary_model = env_config.get("or_summary_model")
            
        if not run_config.get("openrouter_api_key"):
            logger.error("An OpenRouter API key is required. Provide one with --api-key or configure it in the .env file")
            logger.info("Exiting with error code 1")
            sys.exit(1)
    
    elif provider == "ollama":
        run_config["ollama_endpoint"] = args.endpoint if args.endpoint else env_config.get("ollama_endpoint")
        
        if not vlm_model:
            vlm_model = env_config.get("ollama_vlm_model")
        
        if not summary_model and run_config["use_summary"]:
            summary_model = env_config.get("ollama_summary_model")
        
        if not ollama_client.OLLAMA_AVAILABLE:
            logger.error("Ollama Python client not installed. Install with 'pip install ollama'")
            logger.info("Exiting with error code 1")
            sys.exit(1)
            
        if not ollama_client.check_ollama_availability(run_config["ollama_endpoint"]):
            logger.error(f"Could not connect to Ollama at {run_config['ollama_endpoint']}. Make sure it is running.")
            logger.info("Exiting with error code 1")
            sys.exit(1)
    
    run_config["vlm_model"] = vlm_model
    if run_config["use_summary"]:
        run_config["summary_llm_model"] = summary_model
    
    # Print configuration summary
    logger.info(f"Processing PDF: {os.path.basename(args.pdf_file)}")
    logger.info(f"Provider: {run_config['provider']}")
    
    if run_config['provider'] == 'openrouter':
        if run_config.get('openrouter_api_key'):
            masked_key = '*' * 8 + run_config['openrouter_api_key'][-5:] if len(run_config['openrouter_api_key']) > 5 else '*****'
            logger.info(f"OpenRouter API Key: {masked_key}")
        else:
            logger.info("OpenRouter API Key: Not provided")
    else:
        logger.info(f"Ollama Endpoint: {run_config['ollama_endpoint']}")
    
    logger.info(f"VLM Model: {run_config['vlm_model']}")
    logger.info(f"Language: {run_config['output_language']}")
    logger.info(f"Markitdown: {'Yes' if run_config['use_markitdown'] else 'No'}")
    logger.info(f"Summary: {'Yes' if run_config['use_summary'] else 'No'}")
    if run_config.get('use_summary') and run_config.get('summary_llm_model'):
        logger.info(f"Summary model: {run_config['summary_llm_model']}")
    
    # Create progress callback
    progress_callback = create_progress_callback()
    
    # Run conversion
    status, markdown_result = core.convert_pdf_to_markdown(
        args.pdf_file,
        run_config,
        progress_callback
    )
    
    if not markdown_result:
        logger.error(f"Error: {status}")
        logger.info("Exiting with error code 1")
        sys.exit(1)
    
    # Determine output filename
    output_filename = args.output
    if not output_filename:
        base_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
        output_filename = f"{base_name}_description.md"
    
    # Save output file
    try:
        with open(output_filename, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_result)
        logger.info(f"Conversion completed. Result saved to: {output_filename}")
    except Exception as e:
        logger.error(f"Error saving output file: {e}")
        logger.info("Exiting with error code 1")
        sys.exit(1)