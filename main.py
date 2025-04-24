import logging
import argparse

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
    logging.info("Starting DescribePDF...")

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--web', action='store_true', help='Iniciar en modo web con Gradio')
    
    args, _ = parser.parse_known_args()
    
    try:
        if args.web:
            # Modo interfaz web con Gradio
            from describepdf import ui
            logging.info("Starting in WEB mode with Gradio interface...")
            app_ui = ui.create_ui()
            app_ui.launch()
        else:
            # Modo línea de comandos
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