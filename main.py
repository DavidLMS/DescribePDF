import gradio as gr
from anypdf2md import ui, config # Importar desde el paquete
import logging

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')

if __name__ == "__main__":
    logging.info("Starting AnyPDF2MD application...")
    # Cargar configuración inicial (asegura que .env y config.json se lean)
    config.load_config()

    # Crear la interfaz de usuario
    app_ui = ui.create_ui()

    # Lanzar la aplicación Gradio
    app_ui.launch()
    logging.info("AnyPDF2MD application stopped.")