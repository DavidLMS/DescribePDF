"""
Main entry point for DescribePDF application.

This module handles command-line argument parsing and routes to the appropriate
UI or CLI functionality based on the provided arguments.
"""

import logging
import argparse
import sys
from typing import List, Optional

def parse_arguments(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Args:
        args: List of command line arguments (default: sys.argv[1:])
        
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--web', action='store_true', help='Start in web mode with Gradio (OpenRouter)')
    parser.add_argument('--web-ollama', action='store_true', help='Start in web mode with Gradio (Ollama local)')
    
    # Parse known args to allow the rest to be processed by the CLI parser
    args, _ = parser.parse_known_args(args)
    return args

def main(args: Optional[List[str]] = None) -> int:
    """
    Main function that starts the appropriate application mode.
    
    Args:
        args: List of command line arguments (default: sys.argv[1:])
        
    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
    logging.info("Starting DescribePDF...")
    
    # Parse arguments
    parsed_args = parse_arguments(args)
    
    try:
        # Start in the appropriate mode
        if parsed_args.web:
            # Start web UI with OpenRouter
            from describepdf import ui
            logging.info("Starting in WEB mode with Gradio interface for OpenRouter...")
            app_ui = ui.create_ui()
            app_ui.launch()
            return 0
            
        elif parsed_args.web_ollama:
            # Start web UI with Ollama
            from describepdf import ui_ollama
            logging.info("Starting in WEB mode with Gradio interface for Ollama...")
            app_ui = ui_ollama.create_ui()
            app_ui.launch()
            return 0
            
        else:
            # Start CLI mode
            from describepdf import cli
            logging.info("Starting in CLI mode...")
            cli.run_cli()
            return 0
            
    except ImportError as e:
        logging.error(f"Failed to start, likely a missing dependency: {e}")
        print(f"\nError: Failed to start. Please ensure all dependencies from requirements.txt are installed.\nDetails: {e}\n")
        return 1
        
    except KeyboardInterrupt:
        logging.info("Application stopped by user.")
        return 0
        
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}\n")
        return 1

if __name__ == "__main__":
    exit_code = main()
    logging.info(f"DescribePDF application stopped with code {exit_code}.")
    sys.exit(exit_code)