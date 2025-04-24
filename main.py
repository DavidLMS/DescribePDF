from describepdf import ui
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

if __name__ == "__main__":
    logging.info("Starting DescribePDF...")

    try:
        app_ui = ui.create_ui()
        app_ui.launch()
    except ImportError as e:
         logging.error(f"Failed to start UI, likely a missing dependency: {e}")
         print(f"\nError: Failed to start UI. Please ensure all dependencies from requirements.txt are installed.\nDetails: {e}\n")
    except Exception as e:
        logging.error(f"An unexpected error occurred during application startup: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}\n")

    logging.info("DescribePDF application stopped.")