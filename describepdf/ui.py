"""
Web UI module for DescribePDF with OpenRouter.

This module implements the Gradio-based web interface for the OpenRouter
provider version of DescribePDF.
"""

import gradio as gr
import os
import tempfile
import logging
import secrets
from typing import Tuple, Optional, Dict, Any, List

from . import config
from . import core

theme = gr.themes.Soft(
    primary_hue="red",
    secondary_hue="rose",
    spacing_size="lg",
)

def convert_pdf_to_descriptive_markdown(
    pdf_file_obj: Optional[gr.File], 
    ui_api_key: str, 
    ui_vlm_model: str, 
    ui_lang: str, 
    ui_use_md: bool, 
    ui_use_sum: bool, 
    ui_sum_model: str, 
    ui_page_selection: str,
    progress: gr.Progress = gr.Progress(track_tqdm=True)
) -> Tuple[str, gr.update, Optional[str]]:
    """
    Convert a PDF file to detailed page-by-page Markdown descriptions using Vision-Language Models.
    
    This function processes the uploaded PDF, analyzing the visual and textual content of each page
    using OpenRouter's Vision-Language Models (VLMs). It generates rich, contextual descriptions in
    Markdown format that capture both the visual elements and text content of the document, making
    the PDF accessible and searchable in contexts where traditional text extraction would fail.
    
    Args:
        pdf_file_obj: Gradio File object for the uploaded PDF
        ui_api_key: OpenRouter API key from UI
        ui_vlm_model: VLM model name from UI (e.g., qwen/qwen2.5-vl-72b-instruct)
        ui_lang: Output language for descriptions (e.g., English, Spanish)
        ui_use_md: Whether to use Markitdown for enhanced text extraction
        ui_use_sum: Whether to generate a document summary for context
        ui_sum_model: Summary model name from UI (e.g., google/gemini-2.5-flash-preview)
        ui_page_selection: Optional page selection string (e.g., "1,3,5-10")
        progress: Gradio progress tracker
        
    Returns:
        Tuple containing:
        - str: Status message indicating success or failure
        - gr.update: Download button update with the result file
        - Optional[str]: Markdown result content
    """
    # Validate input file
    if pdf_file_obj is None:
        return "Please upload a PDF file.", gr.update(value=None, visible=False), None

    # Load environment config
    env_config = config.get_config()

    # Prepare configuration for this run
    api_key = ui_api_key.strip() if ui_api_key.strip() else env_config.get("openrouter_api_key")

    current_run_config: Dict[str, Any] = {
        "provider": "openrouter",
        "openrouter_api_key": api_key,
        "vlm_model": ui_vlm_model,
        "output_language": ui_lang,
        "use_markitdown": ui_use_md,
        "use_summary": ui_use_sum,
        "summary_llm_model": ui_sum_model if ui_sum_model else env_config.get("or_summary_model"),
        "page_selection": ui_page_selection.strip() if ui_page_selection.strip() else None
    }

    # Validate API key
    if not current_run_config.get("openrouter_api_key"):
        error_msg = "Error: OpenRouter API Key is missing. Provide it in the UI or set OPENROUTER_API_KEY in the .env file."
        logging.error(error_msg)
        return error_msg, gr.update(value=None, visible=False), None

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
    Create and return the Gradio interface for OpenRouter.
    
    This function sets up a Gradio web interface with tabs for PDF conversion
    and configuration. It loads initial settings from the environment config
    and provides UI components for adjusting settings for each conversion run.
    
    Returns:
        gr.Blocks: Configured Gradio interface ready to be launched
    """
    # Load initial config from environment
    initial_env_config = config.get_config()

    # Define suggested model lists and languages
    suggested_vlms: List[str] = [
        "qwen/qwen2.5-vl-72b-instruct", 
        "google/gemini-2.5-pro-preview-03-25",
        "openai/chatgpt-4o-latest"
    ]
    
    suggested_llms: List[str] = [
        "google/gemini-2.5-flash-preview", 
        "openai/chatgpt-4o-latest",
        "anthropic/claude-3.5-sonnet"
    ]
    
    suggested_languages: List[str] = [
        "English", "Spanish", "French", "German", 
        "Chinese", "Japanese", "Italian", 
        "Portuguese", "Russian", "Korean"
    ]

    # Set initial values from config
    initial_vlm = initial_env_config.get("or_vlm_model")
    initial_llm = initial_env_config.get("or_summary_model")
    initial_lang = initial_env_config.get("output_language")
    initial_use_md = initial_env_config.get("use_markitdown")
    initial_use_sum = initial_env_config.get("use_summary")
    
    has_env_api_key = bool(initial_env_config.get("openrouter_api_key"))

    # Create the Gradio interface
    with gr.Blocks(title="DescribePDF", theme=theme) as iface:
        gr.Markdown("<center><img src='https://davidlms.github.io/DescribePDF/assets/poster.png' alt='Describe PDF Logo' width='600px'/></center>")
        gr.Markdown(
            """<div style="display: flex;align-items: center;justify-content: center">
            [<a href="https://davidlms.github.io/DescribePDF/">Project Page</a>] | [<a href="https://github.com/DavidLMS/describepdf">Github</a>]</div>
            """
        )
        gr.Markdown(
            "DescribePDF is an open-source tool designed to convert PDF files into detailed page-by-page descriptions in Markdown format using Vision-Language Models (VLMs). Unlike traditional PDF extraction tools that focus on replicating the text layout, DescribePDF generates rich, contextual descriptions of each page's content, making it perfect for visually complex documents like catalogs, scanned documents, and presentations."
            "\n\n"
            "Upload a PDF, adjust settings, and click 'Describe'. "
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
                            "Describe", 
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
            with gr.TabItem("Settings", id=1):
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
                    label="VLM Model", 
                    choices=suggested_vlms,
                    value=initial_vlm,
                    allow_custom_value=True,
                    info="Select or type the OpenRouter VLM model name"
                )
                output_language_input = gr.Dropdown(
                    label="Output Language", 
                    choices=suggested_languages,
                    value=initial_lang,
                    allow_custom_value=True,
                    info="Select or type the desired output language (e.g., English, Spanish)"
                )
                page_selection_input = gr.Textbox(
                    label="Page Selection (Optional)", 
                    value="",
                    placeholder="Example: 1,3,5-10,15 (leave empty for all pages)",
                    info="Specify individual pages or ranges to process"
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
                    info="Select or type the OpenRouter LLM model name for summaries"
                )

        # Connect UI components
        conversion_inputs = [
            pdf_input, api_key_input, vlm_model_input, output_language_input,
            use_markitdown_checkbox, use_summary_checkbox, summary_llm_model_input, page_selection_input
        ]
        conversion_outputs = [
            progress_output, download_button, markdown_output
        ]
        convert_button.click(
            fn=convert_pdf_to_descriptive_markdown,
            inputs=conversion_inputs,
            outputs=conversion_outputs
        )

    return iface

def launch_app() -> None:
    """
    Start the application from the command line.
    
    This function creates the Gradio UI and launches it.
    """
    app: gr.Blocks = create_ui()
    app.launch()
    
if __name__ == "__main__":
    launch_app()