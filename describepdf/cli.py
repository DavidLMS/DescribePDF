import argparse
import os
import logging
import sys
from tqdm import tqdm
from . import config
from . import core

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
    
    run_config = {
        "openrouter_api_key": args.api_key if args.api_key else env_config.get("openrouter_api_key"),
        "vlm_model": args.vlm_model if args.vlm_model else env_config.get("vlm_model"),
        "output_language": args.language if args.language else env_config.get("output_language"),
        "use_markitdown": args.use_markitdown if args.use_markitdown else env_config.get("use_markitdown"),
        "use_summary": args.use_summary if args.use_summary else env_config.get("use_summary"),
        "summary_llm_model": args.summary_model if args.summary_model else env_config.get("summary_llm_model")
    }
    
    if not run_config.get("openrouter_api_key"):
        print("Error: An OpenRouter API key is required. Provide one with --api-key or configure it in the .env file")
        sys.exit(1)
    
    class FileObj:
        def __init__(self, path):
            self.name = path
    
    pdf_file_obj = FileObj(args.pdf_file)
    
    print(f"Processing PDF: {os.path.basename(args.pdf_file)}")
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