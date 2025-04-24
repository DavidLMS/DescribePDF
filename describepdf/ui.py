import gradio as gr
import os
import tempfile
import logging
from . import config
from . import core

def generate(pdf_file_obj, ui_api_key, ui_vlm_model, ui_lang, ui_use_md, ui_use_sum, ui_sum_model, progress=gr.Progress(track_tqdm=True)):
    """Función wrapper para llamar al core y manejar la UI de Gradio."""
    if pdf_file_obj is None:
        return "Please upload a PDF file.", gr.update(value=None, visible=False), None

    env_config = config.get_config()

    api_key = ui_api_key if ui_api_key.strip() else env_config.get("openrouter_api_key")

    current_run_config = {
        "openrouter_api_key": api_key,
        "vlm_model": ui_vlm_model,
        "output_language": ui_lang,
        "use_markitdown": ui_use_md,
        "use_summary": ui_use_sum,
        "summary_llm_model": ui_sum_model
    }

    if not current_run_config.get("openrouter_api_key"):
         error_msg = "Error: OpenRouter API Key is missing. Provide it in the UI or set OPENROUTER_API_KEY in the .env file."
         logging.error(error_msg)
         return error_msg, gr.update(value=None, visible=False), None


    def progress_callback_gradio(progress_value, status):
        clamped_progress = max(0.0, min(1.0, progress_value))
        progress(clamped_progress, desc=status)
        logging.info(f"Progress: {status} ({clamped_progress*100:.1f}%)")

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
            logging.info(f"Markdown result saved to temporary file for download: {download_file}")
            download_button_update = gr.update(value=download_filepath, visible=True, label=f"Download '{download_filename}'")

        except Exception as e:
            logging.error(f"Error creating temporary file for download: {e}")
            status_message += " (Error creating download file)"
            download_button_update = gr.update(value=None, visible=False)
    else:
        download_button_update = gr.update(value=None, visible=False)


    return (
        status_message,
        download_button_update,
        result_markdown if result_markdown else ""
    )

def create_ui():
    """Crea y devuelve la interfaz de Gradio."""
    initial_env_config = config.get_config()

    suggested_vlms = [
        "qwen/qwen2.5-vl-72b-instruct", "google/gemini-2.5-pro-preview-03-25",
        "openai/chatgpt-4o-latest"
    ]
    suggested_llms = [
        "google/gemini-2.5-flash-preview", "openai/chatgpt-4o-latest",
        "anthropic/claude-3.5-sonnet"
    ]
    suggested_languages = ["English", "Spanish", "French", "German", "Chinese", "Japanese", "Italian", "Portuguese", "Russian", "Korean"]

    initial_vlm = initial_env_config.get("vlm_model")
    initial_llm = initial_env_config.get("summary_llm_model")
    initial_lang = initial_env_config.get("output_language")
    initial_use_md = initial_env_config.get("use_markitdown")
    initial_use_sum = initial_env_config.get("use_summary")
    
    has_env_api_key = bool(initial_env_config.get("openrouter_api_key"))

    with gr.Blocks(theme=gr.themes.Soft(), title="DescribePDF") as iface:
        gr.Markdown("# DescribePDF - Visual PDF to Markdown extensive description")
        gr.Markdown(
            "This application converts PDF files into Markdown format using a Vision Language Model (VLM) "
            "to describe each page's content.\n"
            "Upload a PDF, adjust settings (optional), and click 'Convert to MD'. "
            "Default settings are loaded from the `.env` file on startup. Settings chosen here apply only to the current conversion."
        )
        
        gr.Markdown(
            "> **Note**: This tool is also available as a command-line utility. "
            "Run `describepdf --help` to see available options."
        )

        with gr.Tabs():
            with gr.TabItem("Generate", id=0):
                 with gr.Row():
                    with gr.Column(scale=1):
                        pdf_input = gr.File(label="Upload PDF", file_types=['.pdf'], type="filepath")
                        convert_button = gr.Button("Convert to Markdown", variant="primary")
                        progress_output = gr.Textbox(label="Progress", interactive=False, lines=2)
                        download_button = gr.File(label="Download Markdown", visible=False, interactive=False)

                    with gr.Column(scale=2):
                        markdown_output = gr.Markdown(label="Result (Markdown)")


            with gr.TabItem("Configuration", id=1):
                gr.Markdown(
                    "Adjust settings for the *next* generation. These settings are **not** saved. "
                    "Defaults are controlled by the `.env` file."
                )
                api_key_input = gr.Textbox(
                    label="OpenRouter API Key" + (" (set in .env)" if has_env_api_key else ""),
                    type="password",
                    placeholder="Enter an API key here to override the one in .env" if has_env_api_key else "Enter your OpenRouter API key",
                    value="" 
                )
                vlm_model_input = gr.Dropdown(
                    label="VLM Model", choices=suggested_vlms,
                    value=initial_vlm,
                    allow_custom_value=True,
                    info="Select or type the OpenRouter VLM model name"
                )
                output_language_input = gr.Dropdown(
                    label="Output Language", choices=suggested_languages,
                    value=initial_lang,
                    allow_custom_value=True,
                    info="Select or type the desired output language (e.g., English, Spanish)"
                )
                with gr.Row():
                    use_markitdown_checkbox = gr.Checkbox(
                        label="Use Markitdown for extra text context",
                        value=initial_use_md
                    )
                    use_summary_checkbox = gr.Checkbox(
                        label="Use PDF summary for augmented context (requires extra LLM call)",
                        value=initial_use_sum
                    )
                summary_llm_model_input = gr.Dropdown(
                    label="LLM Model for Summary", choices=suggested_llms,
                    value=initial_llm,
                    allow_custom_value=True,
                    info="Select or type the OpenRouter LLM model name for summaries"
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

def launch_app():
    """Función para iniciar la aplicación desde la línea de comandos."""
    app = create_ui()
    app.launch()
    
if __name__ == "__main__":
    launch_app()