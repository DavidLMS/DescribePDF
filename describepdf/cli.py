"""
Command-line interface for DescribePDF.

This module provides the CLI functionality for converting PDF files to markdown descriptions.
"""

import argparse
import os
import logging
import sys
from typing import Dict, Any, Callable
from tqdm import tqdm

from . import config
from . import core
from . import ollama_client

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
    last_progress = 0
    
    def callback(progress_value: float, status: str) -> None:
        """
        Display progress in the command line.
        
        Args:
            progress_value (float): Progress value between 0.0 and 1.0
            status (str): Current status message
        """
        nonlocal last_progress
        
        current_progress = int(progress_value * 100)
        progress_diff = current_progress - last_progress
        
        if progress_diff > 0:
            progress_bar.update(progress_diff)
            last_progress = current_progress
        
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
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
    
    # Validate input file exists
    if not os.path.exists(args.pdf_file) or not os.path.isfile(args.pdf_file):
        print(f"Error: The PDF file '{args.pdf_file}' does not exist or is not a valid file.")
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
    vlm_model = args.vlm_model
    summary_model = args.summary_model
    
    if provider == "openrouter":
        run_config["openrouter_api_key"] = args.api_key if args.api_key else env_config.get("openrouter_api_key")
        
        if not vlm_model:
            vlm_model = env_config.get("or_vlm_model")
        
        if not summary_model and run_config["use_summary"]:
            summary_model = env_config.get("or_summary_model")
            
        if not run_config.get("openrouter_api_key"):
            print("Error: An OpenRouter API key is required. Provide one with --api-key or configure it in the .env file")
            sys.exit(1)
    
    elif provider == "ollama":
        run_config["ollama_endpoint"] = args.endpoint if args.endpoint else env_config.get("ollama_endpoint")
        
        if not vlm_model:
            vlm_model = env_config.get("ollama_vlm_model")
        
        if not summary_model and run_config["use_summary"]:
            summary_model = env_config.get("ollama_summary_model")
        
        if not ollama_client.OLLAMA_AVAILABLE:
            print("Error: Ollama Python client not installed. Install with 'pip install ollama'")
            sys.exit(1)
            
        if not ollama_client.check_ollama_availability(run_config["ollama_endpoint"]):
            print(f"Error: Could not connect to Ollama at {run_config['ollama_endpoint']}. Make sure it is running.")
            sys.exit(1)
    
    run_config["vlm_model"] = vlm_model
    if run_config["use_summary"]:
        run_config["summary_llm_model"] = summary_model
    
    # Print configuration summary
    print(f"Processing PDF: {os.path.basename(args.pdf_file)}")
    print(f"Provider: {run_config['provider']}")
    
    if run_config['provider'] == 'openrouter':
        if run_config['openrouter_api_key']:
            masked_key = '*' * 8 + run_config['openrouter_api_key'][-5:] if len(run_config['openrouter_api_key']) > 5 else '*****'
            print(f"OpenRouter API Key: {masked_key}")
        else:
            print("OpenRouter API Key: Not provided")
    else:
        print(f"Ollama Endpoint: {run_config['ollama_endpoint']}")
    
    print(f"VLM Model: {run_config['vlm_model']}")
    print(f"Language: {run_config['output_language']}")
    print(f"Markitdown: {'Yes' if run_config['use_markitdown'] else 'No'}")
    print(f"Summary: {'Yes' if run_config['use_summary'] else 'No'}")
    if run_config['use_summary']:
        print(f"Summary model: {run_config['summary_llm_model']}")
    print("")
    
    # Create progress callback
    progress_callback = create_progress_callback()
    
    # Run conversion
    status, markdown_result = core.convert_pdf_to_markdown(
        args.pdf_file,
        run_config,
        progress_callback
    )
    
    if not markdown_result:
        print(f"\nError: {status}")
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
        print(f"\nConversion completed. Result saved to: {output_filename}")
    except Exception as e:
        print(f"\nError saving output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_cli()