import logging
import argparse

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
    logging.info("Starting DescribePDF...")

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--web', action='store_true', help='Start in web mode with Gradio (OpenRouter)')
    parser.add_argument('--web-ollama', action='store_true', help='Start in web mode with Gradio (Ollama local)')
    
    args, _ = parser.parse_known_args()
    
    try:
        if args.web:
            from describepdf import ui
            logging.info("Starting in WEB mode with Gradio interface for OpenRouter...")
            app_ui = ui.create_ui()
            app_ui.launch()
        elif args.web_ollama:
            from describepdf import ui_ollama
            logging.info("Starting in WEB mode with Gradio interface for Ollama...")
            app_ui = ui_ollama.create_ui()
            app_ui.launch()
        else:
            from describepdf import cli
            logging.info("Starting in CLI mode...")
            cli.run_cli()
            
    except ImportError as e:
        logging.error(f"Failed to start, likely a missing dependency: {e}")
        print(f"\nError: Failed to start. Please ensure all dependencies from requirements.txt are installed.\nDetails: {e}\n")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}\n")

    logging.info("DescribePDF application stopped.")