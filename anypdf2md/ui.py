import gradio as gr
import os
import tempfile
import logging
from . import config
from . import core

# --- Funciones de Callback de Gradio ---

def save_ui_config(api_key, vlm_model, lang, use_md, use_sum, sum_model):
    """Guarda la configuración desde la UI."""
    logging.info("Attempting to save configuration from UI...")
    new_config = {
        "openrouter_api_key": api_key if api_key else None, # Guardar None si está vacío
        "vlm_model": vlm_model,
        "output_language": lang,
        "use_markitdown": use_md,
        "use_summary": use_sum,
        "summary_llm_model": sum_model
    }
    # No guardar la clave API si es la misma que la del .env
    # (config.save_config se encarga de esta lógica ahora)
    # env_key = os.getenv("OPENROUTER_API_KEY")
    # if new_config["openrouter_api_key"] == env_key:
    #     new_config["openrouter_api_key"] = None # No persistir si viene de .env

    if config.save_config(new_config):
        return gr.update(value="Configuration saved successfully!")
    else:
        return gr.update(value="Error saving configuration.")

def update_summary_model_visibility(use_summary_checkbox):
    """Actualiza la visibilidad del campo del modelo de resumen."""
    return gr.update(visible=use_summary_checkbox)

def run_conversion_wrapper(pdf_file_obj, api_key, vlm_model, lang, use_md, use_sum, sum_model, progress=gr.Progress(track_tqdm=True)):
    """Función wrapper para llamar al core y manejar la UI de Gradio."""
    if pdf_file_obj is None:
        return "Please upload a PDF file.", None, gr.update(visible=False)

    # Usar la configuración de la UI directamente
    current_config = {
        "openrouter_api_key": api_key,
        "vlm_model": vlm_model,
        "output_language": lang,
        "use_markitdown": use_md,
        "use_summary": use_sum,
        "summary_llm_model": sum_model
    }

    # Crear función de callback para el progreso
    def progress_callback_gradio(status):
        progress(0, desc=status) # Usar desc para mostrar el texto
        logging.info(f"Progress: {status}")

    # Llamar a la lógica principal
    status_message, result_markdown = core.convert_pdf_to_markdown(
        pdf_file_obj,
        current_config,
        progress_callback_gradio
    )

    # Preparar archivo para descarga si éxito
    download_file = None
    if result_markdown:
        try:
            # Crear archivo temporal para descarga
            with tempfile.NamedTemporaryFile(delete=False, mode="w", suffix=".md", encoding="utf-8") as md_file:
                md_file.write(result_markdown)
                download_file = md_file.name
            logging.info(f"Markdown result saved to temporary file for download: {download_file}")
        except Exception as e:
            logging.error(f"Error creating temporary file for download: {e}")
            status_message += " (Error creating download file)"


    # Actualizar UI
    return (
        status_message,
        result_markdown if result_markdown else "",
        gr.update(value=download_file, visible=bool(download_file)) # Mostrar botón de descarga si hay archivo
    )


# --- Creación de la Interfaz Gradio ---

def create_ui():
    """Crea y devuelve la interfaz de Gradio."""
    # Cargar configuración inicial para poblar la UI
    initial_config = config.get_config()
    # No mostrar la clave API del .env directamente en el campo de contraseña
    # Si la clave en config es None o coincide con .env, mostrar vacío.
    # Si es diferente (usuario la pegó y guardó), mostrarla (como password).
    # Simplificación: si viene de .env, mostrar vacío. Si no, mostrar la guardada.
    env_key = os.getenv("OPENROUTER_API_KEY")
    initial_api_key_display = initial_config.get("openrouter_api_key")
    # if initial_api_key_display == env_key:
    #      initial_api_key_display = "" # No mostrar si viene de .env
    # Mejor: Siempre empezar vacío el campo password por seguridad.
    # El backend usará la clave de .env si el campo está vacío y .env existe.

    with gr.Blocks(theme=gr.themes.Soft(), title="AnyPDF2MD") as iface:
        gr.Markdown("# AnyPDF2MD - PDF to Accessible Markdown Converter")

        with gr.Tabs():
            with gr.TabItem("Run Conversion", id=0):
                with gr.Row():
                    with gr.Column(scale=1):
                        pdf_input = gr.File(label="Upload PDF", file_types=['.pdf'], type="filepath") # Usar filepath
                        convert_button = gr.Button("Convert to MD", variant="primary")
                        progress_output = gr.Textbox(label="Progress", interactive=False, lines=2)

                    with gr.Column(scale=2):
                        markdown_output = gr.Markdown(label="Result (Markdown)")
                        # Alternativa con Textbox:
                        # markdown_output_txt = gr.Textbox(label="Result (Markdown)", lines=20, interactive=False)
                        download_button = gr.File(label="Download MD", visible=False, interactive=False) # Oculto inicialmente

            with gr.TabItem("Configuration", id=1):
                gr.Markdown("Configure API access and processing options.")
                # Usar la clave guardada si existe, si no, vacío. El backend priorizará .env si está vacío.
                api_key_input = gr.Textbox(
                    label="OpenRouter API Key",
                    type="password",
                    placeholder="Leave blank to use key from .env file (if available)",
                    value=initial_config.get("openrouter_api_key") or "" # Mostrar guardada o vacío
                )
                vlm_model_input = gr.Textbox(label="VLM Model", value=initial_config.get("vlm_model"))
                output_language_input = gr.Textbox(label="Output Language", value=initial_config.get("output_language"))
                with gr.Row():
                    use_markitdown_checkbox = gr.Checkbox(label="Use 'Markitdown' for extra text context", value=initial_config.get("use_markitdown"))
                    use_summary_checkbox = gr.Checkbox(label="Use PDF summary for augmented context (requires extra LLM call)", value=initial_config.get("use_summary"))
                summary_llm_model_input = gr.Textbox(
                    label="LLM Model for Summary",
                    value=initial_config.get("summary_llm_model"),
                    visible=initial_config.get("use_summary") # Visibilidad inicial
                )
                save_button = gr.Button("Save Configuration")
                config_status_output = gr.Textbox(label="Status", interactive=False)

                # --- Conexiones de Eventos ---

                # Visibilidad condicional del modelo de resumen
                use_summary_checkbox.change(
                    fn=update_summary_model_visibility,
                    inputs=use_summary_checkbox,
                    outputs=summary_llm_model_input
                )

                # Guardar configuración
                config_inputs = [
                    api_key_input, vlm_model_input, output_language_input,
                    use_markitdown_checkbox, use_summary_checkbox, summary_llm_model_input
                ]
                save_button.click(
                    fn=save_ui_config,
                    inputs=config_inputs,
                    outputs=config_status_output
                )

                # Ejecutar conversión
                # Pasar todos los inputs de config necesarios para no depender del estado guardado
                # durante la ejecución, sino del estado actual de la UI.
                conversion_inputs = [
                    pdf_input, api_key_input, vlm_model_input, output_language_input,
                    use_markitdown_checkbox, use_summary_checkbox, summary_llm_model_input
                ]
                conversion_outputs = [
                    progress_output, markdown_output, download_button
                ]
                convert_button.click(
                    fn=run_conversion_wrapper,
                    inputs=conversion_inputs,
                    outputs=conversion_outputs
                )

    return iface