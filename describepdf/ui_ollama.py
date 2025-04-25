"""
Web UI module for DescribePDF with Ollama.

This module implements the Gradio-based web interface for the Ollama
provider version of DescribePDF.
"""

import gradio as gr
import os
import tempfile
import logging
import secrets
from typing import Tuple, Optional

from . import config
from . import core
from . import ollama_client

def generate(
    pdf_file_obj: Optional[gr.File], 
    ollama_endpoint: str, 
    ui_vlm_model: str, 
    ui_lang: str, 
    ui_use_md: bool, 
    ui_use_sum: bool, 
    ui_sum_model: str, 
    progress=gr.Progress(track_tqdm=True)
) -> Tuple[str, gr.update, Optional[str]]:
    """
    Wrapper function to call the core conversion process and handle the Gradio UI for Ollama.
    
    Args:
        pdf_file_obj: Gradio File object for the uploaded PDF
        ollama_endpoint: Ollama server endpoint URL
        ui_vlm_model: VLM model name from UI
        ui_lang: Output language from UI
        ui_use_md: Whether to use Markitdown from UI
        ui_use_sum: Whether to generate a summary from UI
        ui_sum_model: Summary model name from UI
        progress: Gradio progress tracker
        
    Returns:
        Tuple containing:
        - str: Status message
        - gr.update: Download button update
        - Optional[str]: Markdown result content
    """
    # Validate input file
    if pdf_file_obj is None:
        return "Please upload a PDF file.", gr.update(value=None, visible=False), None

    # Check Ollama availability
    if not ollama_client.check_ollama_availability(ollama_endpoint):
        error_msg = f"Error: Could not connect to Ollama at {ollama_endpoint}. Make sure it is running."
        logging.error(error_msg)
        return error_msg, gr.update(value=None, visible=False), None

    # Prepare configuration for this run
    current_run_config = {
        "provider": "ollama",
        "ollama_endpoint": ollama_endpoint,
        "vlm_model": ui_vlm_model,
        "output_language": ui_lang,
        "use_markitdown": ui_use_md,
        "use_summary": ui_use_sum,
        "summary_llm_model": ui_sum_model
    }

    # Create progress callback for Gradio
    def progress_callback_gradio(progress_value: float, status: str) -> None:
        """
        Update Gradio progress bar with current progress and status message.
        
        Args:
            progress_value (float): Progress value between 0.0 and 1.0
            status (str): Current status message to display
        """
        clamped_progress = max(0.0, min(1.0, progress_value))
        progress(clamped_progress, desc=status)
        logging.info(f"Progress: {status} ({clamped_progress*100:.1f}%)")

    # Run the conversion
    status_message, result_markdown = core.convert_pdf_to_markdown(
        pdf_file_obj.name,
        current_run_config,
        progress_callback_gradio
    )

    # Handle the download file
    if result_markdown:
        try:
            # Get base filename from the uploaded PDF
            base_name = os.path.splitext(os.path.basename(pdf_file_obj.name))[0]
            download_filename = f"{base_name}_description.md"
            
            # Create a temporary file with a random component to avoid collisions
            random_suffix = secrets.token_hex(4)
            temp_dir = tempfile.gettempdir()
            download_filepath = os.path.join(temp_dir, f"{base_name}_{random_suffix}.md")

            # Write markdown result to the temporary file
            with open(download_filepath, "w", encoding="utf-8") as md_file:
                md_file.write(result_markdown)
                
            logging.info(f"Markdown result saved to temporary file for download: {download_filepath}")
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

def create_ui() -> gr.Blocks:
    """
    Create and return the Gradio interface for Ollama.
    
    This function sets up a Gradio web interface with tabs for PDF conversion
    and configuration. It loads initial settings from the environment config
    and provides UI components for adjusting settings for each conversion run.
    
    Returns:
        gr.Blocks: Configured Gradio interface ready to be launched
    """
    # Load initial config from environment
    initial_env_config = config.get_config()

    # Define suggested model lists and languages
    suggested_vlms = ["llama3.2-vision"]
    suggested_llms = ["qwen2.5", "llama3.2"]
    suggested_languages = [
        "English", "Spanish", "French", "German", 
        "Chinese", "Japanese", "Italian", 
        "Portuguese", "Russian", "Korean"
    ]

    # Set initial values from config
    initial_endpoint = initial_env_config.get("ollama_endpoint", "http://localhost:11434")
    initial_vlm = initial_env_config.get("ollama_vlm_model", "llama3.2-vision")
    initial_llm = initial_env_config.get("ollama_summary_model", "qwen2.5")
    initial_lang = initial_env_config.get("output_language", "English")
    initial_use_md = initial_env_config.get("use_markitdown", False)
    initial_use_sum = initial_env_config.get("use_summary", False)

    # Create the Gradio interface
    with gr.Blocks(title="DescribePDF - Ollama") as iface:
        gr.Markdown("# DescribePDF with Ollama - PDF to Markdown using local models")
        gr.Markdown(
            "This application converts PDF files into Markdown format using a local Vision Language Model (VLM) "
            "through Ollama to describe each page's content.\n"
            "Upload a PDF, adjust settings (optional), and click 'Convert to MD'. "
            "Default settings are loaded from the `.env` file on startup. Settings chosen here apply only to the current conversion."
        )

        with gr.Tabs():
            # Generate tab
            with gr.TabItem("Generate", id=0):
                with gr.Row():
                    with gr.Column(scale=1):
                        pdf_input = gr.File(
                            label="Upload PDF", 
                            file_types=['.pdf'], 
                            type="filepath"
                        )
                        convert_button = gr.Button(
                            "Convert to Markdown", 
                            variant="primary"
                        )
                        progress_output = gr.Textbox(
                            label="Progress", 
                            interactive=False, 
                            lines=2
                        )
                        download_button = gr.File(
                            label="Download Markdown", 
                            visible=False, 
                            interactive=False
                        )

                    with gr.Column(scale=2):
                        markdown_output = gr.Markdown(label="Result (Markdown)")

            # Configuration tab
            with gr.TabItem("Configuration", id=1):
                gr.Markdown(
                    "Adjust settings for the *next* generation. These settings are **not** saved. "
                    "Defaults are controlled by the `.env` file."
                )
                ollama_endpoint_input = gr.Textbox(
                    label="Ollama Endpoint",
                    value=initial_endpoint,
                    placeholder="http://localhost:11434",
                    info="URL of your Ollama server"
                )
                vlm_model_input = gr.Dropdown(
                    label="VLM Model", 
                    choices=suggested_vlms,
                    value=initial_vlm,
                    allow_custom_value=True,
                    info="Select or type the Ollama vision model name"
                )
                output_language_input = gr.Dropdown(
                    label="Output Language", 
                    choices=suggested_languages,
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
                    label="LLM Model for Summary", 
                    choices=suggested_llms,
                    value=initial_llm,
                    allow_custom_value=True,
                    info="Select or type the Ollama LLM model name for summaries"
                )

        # Connect UI components
        conversion_inputs = [
            pdf_input, ollama_endpoint_input, vlm_model_input, output_language_input,
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

def launch_app() -> None:
    """
    Start the application from the command line.
    
    This function creates the Gradio UI and launches it.
    """
    app = create_ui()
    app.launch()
    
if __name__ == "__main__":
    launch_app()