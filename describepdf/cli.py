import argparse
import os
import logging
import sys
from tqdm import tqdm
from . import config
from . import core
from . import ollama_client

def setup_cli_parser():
    """Set up the command line argument parser."""
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

def cli_progress_callback(progress_value, status):
    """Callback to display progress in the command line."""
    if not hasattr(cli_progress_callback, "pbar"):
        cli_progress_callback.pbar = tqdm(total=100, desc="Processing", unit="%")
    
    current_progress = int(progress_value * 100)
    previous_progress = getattr(cli_progress_callback, "last_progress", 0)
    progress_diff = current_progress - previous_progress
    
    if progress_diff > 0:
        cli_progress_callback.pbar.update(progress_diff)
        cli_progress_callback.last_progress = current_progress
    
    cli_progress_callback.pbar.set_description(status)
    
    if progress_value >= 1.0:
        cli_progress_callback.pbar.close()

def run_cli():
    """Main function for the command line interface."""
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
    
    if not os.path.exists(args.pdf_file) or not os.path.isfile(args.pdf_file):
        print(f"Error: The PDF file '{args.pdf_file}' does not exist or is not a valid file.")
        sys.exit(1)
    
    env_config = config.get_config()
    
    provider = "ollama" if args.local else "openrouter"
    
    run_config = {
        "provider": provider,
        "output_language": args.language if args.language else env_config.get("output_language"),
        "use_markitdown": args.use_markitdown if args.use_markitdown else env_config.get("use_markitdown"),
        "use_summary": args.use_summary if args.use_summary else env_config.get("use_summary"),
    }
    
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
    
    class FileObj:
        def __init__(self, path):
            self.name = path
    
    pdf_file_obj = FileObj(args.pdf_file)
    
    print(f"Processing PDF: {os.path.basename(args.pdf_file)}")
    print(f"Provider: {run_config['provider']}")
    
    if run_config['provider'] == 'openrouter':
        print(f"OpenRouter API Key: {'*' * 8}{run_config['openrouter_api_key'][-5:] if run_config['openrouter_api_key'] else 'Not provided'}")
    else:
        print(f"Ollama Endpoint: {run_config['ollama_endpoint']}")
    
    print(f"VLM Model: {run_config['vlm_model']}")
    print(f"Language: {run_config['output_language']}")
    print(f"Markitdown: {'Yes' if run_config['use_markitdown'] else 'No'}")
    print(f"Summary: {'Yes' if run_config['use_summary'] else 'No'}")
    if run_config['use_summary']:
        print(f"Summary model: {run_config['summary_llm_model']}")
    print("")
    
    status, markdown_result = core.convert_pdf_to_markdown(
        pdf_file_obj,
        run_config,
        cli_progress_callback
    )
    
    if not markdown_result:
        print(f"\nError: {status}")
        sys.exit(1)
    
    output_filename = args.output
    if not output_filename:
        base_name = os.path.splitext(os.path.basename(args.pdf_file))[0]
        output_filename = f"{base_name}_description.md"
    
    try:
        with open(output_filename, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_result)
        print(f"\nConversion completed. Result saved to: {output_filename}")
    except Exception as e:
        print(f"\nError saving output file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_cli()