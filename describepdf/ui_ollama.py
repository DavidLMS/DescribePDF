import gradio as gr
import os
import tempfile
import logging
from . import config
from . import core
from . import ollama_client

def generate(pdf_file_obj, ollama_endpoint, vlm_model, output_lang, use_md, use_sum, sum_model, progress=gr.Progress(track_tqdm=True)):
    """Función wrapper para llamar al core y manejar la UI de Gradio para Ollama."""
    if pdf_file_obj is None:
        return "Por favor, sube un archivo PDF.", gr.update(value=None, visible=False), None

    env_config = config.get_config()

    if not ollama_client.check_ollama_availability(ollama_endpoint):
        error_msg = f"Error: No se pudo conectar con Ollama en {ollama_endpoint}. Verifica que esté en ejecución."
        logging.error(error_msg)
        return error_msg, gr.update(value=None, visible=False), None

    current_run_config = {
        "provider": "ollama",
        "ollama_endpoint": ollama_endpoint,
        "vlm_model": vlm_model,
        "output_language": output_lang,
        "use_markitdown": use_md,
        "use_summary": use_sum,
        "summary_llm_model": sum_model
    }

    def progress_callback_gradio(progress_value, status):
        clamped_progress = max(0.0, min(1.0, progress_value))
        progress(clamped_progress, desc=status)
        logging.info(f"Progreso: {status} ({clamped_progress*100:.1f}%)")

    status_message, result_markdown = core.convert_pdf_to_markdown(
        pdf_file_obj,
        current_run_config,
        progress_callback_gradio
    )

    download_file = None
    if result_markdown:
        try:
            base_name = os.path.splitext(os.path.basename(pdf_file_obj.name))[0]
            download_filename = f"{base_name}_description.md"
            temp_dir = tempfile.gettempdir()
            download_filepath = os.path.join(temp_dir, f"{base_name}_{os.urandom(4).hex()}.md")

            with open(download_filepath, "w", encoding="utf-8") as md_file:
                md_file.write(result_markdown)
            download_file = download_filepath
            logging.info(f"Resultado Markdown guardado en archivo temporal para descarga: {download_file}")
            download_button_update = gr.update(value=download_filepath, visible=True, label=f"Descargar '{download_filename}'")

        except Exception as e:
            logging.error(f"Error al crear archivo temporal para descarga: {e}")
            status_message += " (Error al crear archivo de descarga)"
            download_button_update = gr.update(value=None, visible=False)
    else:
        download_button_update = gr.update(value=None, visible=False)

    return (
        status_message,
        download_button_update,
        result_markdown if result_markdown else ""
    )

def create_ui():
    """Crea y devuelve la interfaz de Gradio para Ollama."""
    initial_env_config = config.get_config()

    suggested_vlms = ["llama3.2-vision"]
    suggested_llms = ["qwen2.5", "llama3.2"]
    suggested_languages = ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Italian", "Portuguese", "Russian", "Korean"]

    initial_endpoint = initial_env_config.get("ollama_endpoint", "http://localhost:11434")
    initial_vlm = initial_env_config.get("ollama_vlm_model", "llama3.2-vision")
    initial_llm = initial_env_config.get("ollama_summary_model", "qwen2.5")
    initial_lang = initial_env_config.get("output_language", "English")
    initial_use_md = initial_env_config.get("use_markitdown", False)
    initial_use_sum = initial_env_config.get("use_summary", False)

    with gr.Blocks(theme=gr.themes.Soft(), title="DescribePDF - Ollama") as iface:
        gr.Markdown("# DescribePDF con Ollama - PDF a Markdown con modelos locales")
        gr.Markdown(
            "Esta aplicación convierte archivos PDF a formato Markdown usando un modelo de visión y lenguaje (VLM) "
            "local a través de Ollama para describir el contenido de cada página.\n"
            "Sube un PDF, ajusta los parámetros (opcional) y haz clic en 'Convertir a MD'."
        )
        
        gr.Markdown(
            "> **Nota**: Esta herramienta también está disponible como utilidad de línea de comandos. "
            "Ejecuta `describepdf --help` para ver las opciones disponibles."
        )

        with gr.Row():
            with gr.Column(scale=1):
                pdf_input = gr.File(label="Subir PDF", file_types=['.pdf'], type="filepath")
                
                with gr.Group():
                    gr.Markdown("### Configuración de Ollama")
                    ollama_endpoint = gr.Textbox(
                        label="Endpoint de Ollama",
                        value=initial_endpoint,
                        placeholder="http://localhost:11434"
                    )
                    vlm_model_input = gr.Dropdown(
                        label="Modelo de Visión", 
                        choices=suggested_vlms,
                        value=initial_vlm,
                        allow_custom_value=True,
                        info="Selecciona o escribe el nombre del modelo de visión de Ollama"
                    )
                    output_language_input = gr.Dropdown(
                        label="Idioma de Salida", 
                        choices=suggested_languages,
                        value=initial_lang,
                        allow_custom_value=True,
                        info="Selecciona o escribe el idioma deseado para la salida"
                    )
                
                with gr.Group():
                    gr.Markdown("### Opciones avanzadas")
                    with gr.Row():
                        use_markitdown_checkbox = gr.Checkbox(
                            label="Usar Markitdown para contexto adicional",
                            value=initial_use_md
                        )
                        use_summary_checkbox = gr.Checkbox(
                            label="Generar resumen del PDF",
                            value=initial_use_sum
                        )
                    
                    summary_llm_model_input = gr.Dropdown(
                        label="Modelo para Resumen", 
                        choices=suggested_llms,
                        value=initial_llm,
                        allow_custom_value=True,
                        info="Selecciona o escribe el nombre del modelo de Ollama para generar resúmenes",
                        visible=lambda: use_summary_checkbox
                    )
                
                convert_button = gr.Button("Convertir a Markdown", variant="primary")
                progress_output = gr.Textbox(label="Progreso", interactive=False, lines=2)
                download_button = gr.File(label="Descargar Markdown", visible=False, interactive=False)

            with gr.Column(scale=2):
                markdown_output = gr.Markdown(label="Resultado (Markdown)")

        conversion_inputs = [
            pdf_input, ollama_endpoint, vlm_model_input, output_language_input,
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

        use_summary_checkbox.change(
            fn=lambda x: gr.update(visible=x),
            inputs=[use_summary_checkbox],
            outputs=[summary_llm_model_input]
        )

    return iface

def launch_app():
    """Función para iniciar la aplicación desde la línea de comandos."""
    app = create_ui()
    app.launch()
    
if __name__ == "__main__":
    launch_app()