import gradio as gr
# Al importar ui y config, se ejecutan las cargas iniciales en config.py
from anypdf2md import ui, config
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

# Opcional: Ajustar nivel de log si se necesita más detalle (ej. DEBUG)
# logging.getLogger().setLevel(logging.DEBUG)

if __name__ == "__main__":
    logging.info("Starting AnyPDF2MD application...")
    # La configuración (.env) y los prompts ya se cargaron al importar el módulo config

    # Crear la interfaz de usuario (que a su vez lee la config inicial)
    try:
        app_ui = ui.create_ui()
        # Lanzar la aplicación Gradio
        app_ui.launch()
    except ImportError as e:
         logging.error(f"Failed to start UI, likely a missing dependency: {e}")
         print(f"\nError: Failed to start UI. Please ensure all dependencies from requirements.txt are installed.\nDetails: {e}\n")
    except Exception as e:
        logging.error(f"An unexpected error occurred during application startup: {e}", exc_info=True)
        print(f"\nAn unexpected error occurred: {e}\n")

    logging.info("AnyPDF2MD application stopped.")