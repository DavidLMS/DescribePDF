import gradio as gr
import os
import tempfile
import logging
from . import config # Importa el módulo de config simplificado
from . import core

# --- Funciones de Callback de Gradio ---

def update_summary_model_visibility(use_summary_checkbox):
    """Actualiza la visibilidad del campo del modelo de resumen."""
    return gr.update(visible=use_summary_checkbox)


def generate(pdf_file_obj, ui_api_key, ui_vlm_model, ui_lang, ui_use_md, ui_use_sum, ui_sum_model, progress=gr.Progress(track_tqdm=True)):
    """Función wrapper para llamar al core y manejar la UI de Gradio."""
    if pdf_file_obj is None:
        # Devolver valores para todos los outputs esperados
        return "Please upload a PDF file.", gr.update(value=None, visible=False), None

    # Obtener configuración base cargada desde .env al inicio
    env_config = config.get_config()

    # Construir la configuración para ESTA ejecución:
    # Prioridad: Valor de la UI > Valor de .env (cargado en env_config)
    current_run_config = {
        # API Key: Si el usuario escribe algo en la UI, usar eso. Si no, usar la de .env.
        "openrouter_api_key": ui_api_key if ui_api_key else env_config.get("openrouter_api_key"),
        # Resto de valores: Tomar directamente de la UI
        "vlm_model": ui_vlm_model,
        "output_language": ui_lang,
        "use_markitdown": ui_use_md,
        "use_summary": ui_use_sum,
        "summary_llm_model": ui_sum_model
    }

    # Validar que la API key exista finalmente
    if not current_run_config.get("openrouter_api_key"):
         error_msg = "Error: OpenRouter API Key is missing. Provide it in the UI or set OPENROUTER_API_KEY in the .env file."
         logging.error(error_msg)
         # Devuelve 3 valores como espera la salida
         return error_msg, gr.update(value=None, visible=False), None


    # Crear función de callback para el progreso que acepta valor y texto
    def progress_callback_gradio(progress_value, status):
        # Asegurar que progress_value esté entre 0 y 1
        clamped_progress = max(0.0, min(1.0, progress_value))
        progress(clamped_progress, desc=status) # Actualizar barra y texto
        logging.info(f"Progress: {status} ({clamped_progress*100:.1f}%)")

    # Llamar a la lógica principal con la configuración de esta ejecución
    status_message, result_markdown = core.convert_pdf_to_markdown(
        pdf_file_obj,
        current_run_config, # Pasar la configuración construida
        progress_callback_gradio
    )

    # Preparar archivo para descarga si éxito
    download_file = None
    if result_markdown:
        try:
            # Usar el nombre original del PDF para el archivo descargado
            base_name = os.path.splitext(os.path.basename(pdf_file_obj.name))[0]
            download_filename = f"{base_name}_description.md"
            # Guardar en un directorio temporal que Gradio pueda servir
            temp_dir = tempfile.gettempdir()
            # Asegurar que el nombre de archivo sea único para evitar colisiones si se procesan varios archivos rápidamente
            download_filepath = os.path.join(temp_dir, f"{base_name}_{os.urandom(4).hex()}.md")


            with open(download_filepath, "w", encoding="utf-8") as md_file:
                md_file.write(result_markdown)
            download_file = download_filepath # Devolver la ruta completa
            logging.info(f"Markdown result saved to temporary file for download: {download_file}")
            # Devolver un objeto gr.File con el nombre deseado para la descarga en el navegador
            # Esto requiere que Gradio >= 3.15 (aproximadamente)
            # Si usas una versión anterior, solo devolver download_filepath puede funcionar,
            # pero el nombre del archivo descargado será el temporal.
            download_button_update = gr.update(value=download_filepath, visible=True, label=f"Download '{download_filename}'")

        except Exception as e:
            logging.error(f"Error creating temporary file for download: {e}")
            status_message += " (Error creating download file)"
            download_button_update = gr.update(value=None, visible=False)
    else:
        download_button_update = gr.update(value=None, visible=False)


    # Actualizar UI - Devuelve 3 valores en el orden correcto
    return (
        status_message, # Para progress_output
        download_button_update, # Para download_button
        result_markdown if result_markdown else "" # Para markdown_output
    )


# --- Creación de la Interfaz Gradio ---

def create_ui():
    """Crea y devuelve la interfaz de Gradio."""
    # Cargar configuración inicial DESDE .ENV (via config.py) para poblar la UI
    initial_env_config = config.get_config()

    # Listas de sugerencias (puedes personalizarlas)
    suggested_vlms = [
        "qwen/qwen2.5-vl-72b-instruct", "google/gemini-2.0-pro-vision",
        "openai/gpt-4o", "anthropic/claude-3.5-sonnet-20240620", "liuhaotian/llava-yi-34b",
        "google/gemini-pro-vision" # Añadido otro común
    ]
    suggested_llms = [
        "google/gemini-2.5-flash-preview", "anthropic/claude-3-haiku-20240307",
        "mistralai/mistral-7b-instruct", "meta-llama/llama-3-8b-instruct",
        "openai/gpt-3.5-turbo", "google/gemini-pro" # Añadido otro común
    ]
    suggested_languages = ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Italian", "Portuguese", "Russian", "Korean"]

    # Obtener valores iniciales desde la config cargada de .env
    initial_vlm = initial_env_config.get("vlm_model")
    initial_llm = initial_env_config.get("summary_llm_model")
    initial_lang = initial_env_config.get("output_language")
    initial_use_md = initial_env_config.get("use_markitdown")
    initial_use_sum = initial_env_config.get("use_summary")
    initial_api_key = initial_env_config.get("openrouter_api_key")


    with gr.Blocks(theme=gr.themes.Soft(), title="AnyPDF2MD") as iface:
        gr.Markdown("# AnyPDF2MD - PDF to Accessible Markdown Converter")
        gr.Markdown(
            "This application converts PDF files into Markdown format using a Vision Language Model (VLM) "
            "to describe each page's content, aiming for accessibility for visually impaired users.\n"
            "Upload a PDF, adjust settings (optional), and click 'Convert to MD'. "
            "Default settings are loaded from the `.env` file on startup. Settings chosen here apply only to the current conversion."
        )

        with gr.Tabs():
            with gr.TabItem("Run Conversion", id=0):
                 with gr.Row():
                    with gr.Column(scale=1):
                        pdf_input = gr.File(label="Upload PDF", file_types=['.pdf'], type="filepath")
                        convert_button = gr.Button("Convert to MD", variant="primary")
                        progress_output = gr.Textbox(label="Progress", interactive=False, lines=2)
                        # Botón de descarga movido aquí
                        download_button = gr.File(label="Download MD", visible=False, interactive=False)

                    with gr.Column(scale=2):
                        markdown_output = gr.Markdown(label="Result (Markdown)")


            with gr.TabItem("Configuration", id=1):
                gr.Markdown(
                    "Adjust settings for the *next* conversion run. These settings are **not** saved. "
                    "Defaults are controlled by the `.env` file."
                )
                api_key_input = gr.Textbox(
                    label="OpenRouter API Key",
                    type="password",
                    placeholder="Using key from .env (if set). Enter value here to override for this run.",
                    value=initial_api_key
                )
                vlm_model_input = gr.Dropdown(
                    label="VLM Model", choices=suggested_vlms,
                    value=initial_vlm, # Valor inicial desde .env/fallback
                    allow_custom_value=True,
                    info="Select or type the OpenRouter VLM model name (e.g., openai/gpt-4o)"
                )
                output_language_input = gr.Dropdown(
                    label="Output Language", choices=suggested_languages,
                    value=initial_lang, # Valor inicial desde .env/fallback
                    allow_custom_value=True,
                    info="Select or type the desired output language (e.g., English, Spanish)"
                )
                with gr.Row():
                    use_markitdown_checkbox = gr.Checkbox(
                        label="Use 'Markitdown' for extra text context",
                        value=initial_use_md # Valor inicial desde .env/fallback
                    )
                    use_summary_checkbox = gr.Checkbox(
                        label="Use PDF summary for augmented context (requires extra LLM call)",
                        value=initial_use_sum # Valor inicial desde .env/fallback
                    )
                summary_llm_model_input = gr.Dropdown(
                    label="LLM Model for Summary", choices=suggested_llms,
                    value=initial_llm, # Valor inicial desde .env/fallback
                    allow_custom_value=True,
                    visible=initial_use_sum, # Visibilidad inicial desde .env/fallback
                    info="Select or type the OpenRouter LLM model for summaries"
                )

                # --- Conexiones de Eventos ---
                use_summary_checkbox.change(
                    fn=update_summary_model_visibility,
                    inputs=use_summary_checkbox,
                    outputs=summary_llm_model_input
                )

                conversion_inputs = [
                    pdf_input, api_key_input, vlm_model_input, output_language_input,
                    use_markitdown_checkbox, use_summary_checkbox, summary_llm_model_input
                ]
                conversion_outputs = [
                    progress_output, download_button, markdown_output
                ]
                convert_button.click(
                    fn=generate,
                    inputs=conversion_inputs,
                    outputs=conversion_outputs
                )

    return iface