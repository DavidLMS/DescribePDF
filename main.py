"""
Main entry point for DescribePDF application.

This module handles command-line argument parsing and routes to the appropriate
UI or CLI functionality based on the provided arguments.
"""

import logging
import argparse
import sys
from typing import List, Optional

from describepdf.config import logger

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
    # Logging is already configured in config.py, we just need to use the logger
    logger.info("Starting DescribePDF...")
    
    # Parse arguments
    parsed_args = parse_arguments(args)
    
    try:
        # Start in the appropriate mode
        if parsed_args.web:
            # Start web UI with OpenRouter
            from describepdf import ui
            logger.info("Starting in WEB mode with Gradio interface for OpenRouter...")
            app_ui = ui.create_ui()
            app_ui.launch()
            logger.info("Web UI stopped.")
            return 0
            
        elif parsed_args.web_ollama:
            # Start web UI with Ollama
            from describepdf import ui_ollama
            logger.info("Starting in WEB mode with Gradio interface for Ollama...")
            app_ui = ui_ollama.create_ui()
            app_ui.launch()
            logger.info("Web UI (Ollama) stopped.")
            return 0
            
        else:
            # Start CLI mode
            from describepdf import cli
            logger.info("Starting in CLI mode...")
            cli.run_cli()
            return 0
            
    except ImportError as e:
        logger.error(f"Failed to start, likely a missing dependency: {e}")
        logger.error(f"Details: {e}")
        return 1
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user.")
        return 0
        
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)