![poster](assets/poster.png)

<p align="center">
  <a href="https://github.com/DavidLMS/DescribePDF/pulls">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?longCache=true" alt="Pull Requests">
  </a>
  <a href="LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-yellow.svg?longCache=true" alt="MIT License">
    </a>
</p>

# DescribePDF

DescribePDF is an open-source tool designed to convert PDF files into detailed page-by-page descriptions in Markdown format using Vision-Language Models (VLMs). Unlike traditional PDF extraction tools that focus on replicating the text layout, DescribePDF generates rich, contextual descriptions of each page's content, making it perfect for visually complex documents like catalogs, scanned documents, and presentations.

> **Important Note:** DescribePDF is designed to help you make PDF content accessible and searchable in contexts where traditional text extraction fails. It's particularly useful for creating descriptive content that can be indexed in RAG systems or for making visual documents accessible to people with visual impairments.

<p align="center">
    <a href="https://huggingface.co/spaces/davidlms/describepdf">Demo</a>
    ·
    <a href="https://github.com/DavidLMS/DescribePDF/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=%5BBUG%5D">Report Bug</a>
    ·
    <a href="https://github.com/DavidLMS/DescribePDF/issues/new?assignees=&labels=enhancement&projects=&template=feature_request.md&title=%5BREQUEST%5D">Request Feature</a>
</p>

## Table of Contents

[Features](#features)

[Motivation](#motivation)

[How DescribePDF Works](#how-describepdf-works)

[Comparison with Similar Tools](#comparison-with-similar-tools)

[Quick Start](#quick-start)

[Installation](#installation)

[Usage](#usage)

[Customization](#customization)

[Future Development](#future-development)

[License](#license)

[Contributing](#contributing)

## Features

- 📄 **Comprehensive Page Analysis** - Detailed descriptions of each page's visual and textual content
- 🔍 **Context-Aware Descriptions** - Generates descriptions that understand the document's overall structure and purpose
- 🌐 **Multilingual Support** - Generate descriptions in multiple languages
- 📊 **Enhanced Extraction with Markitdown** - Optional integration with Markitdown for better text extraction
- 📝 **Document Summarization** - Optional generation of overall document summaries
- ☁️ **Cloud Model Support** - Compatible with powerful VLMs through OpenRouter
- 💻 **Local Model Support** - Works with local models via Ollama
- 🖥️ **Dual Interface** - Available as both a web UI and command-line tool

## Motivation

The idea for DescribePDF was born from a practical challenge. While building a RAG-powered chatbot that needed to answer questions based on website content, I encountered catalogs in PDF format that couldn't be properly indexed using traditional text extraction methods. These catalogs contained product images, specifications, and layouts that were visually rich but difficult to extract meaningfully.

Standard OCR produced imprecise, unstructured text, while modern PDF-to-markdown converters failed to capture the essence of these visual documents. When a catalog page consisted primarily of product images with scattered text elements, these tools would either miss important visual context or produce disorganized content.

What I needed was a detailed, page-by-page description that would allow an LLM to "see" what was on each page, enabling responses like: "You can find that product and similar ones on page 12 of the catalog," along with a link. Existing tools like MinerU, MarkItDown, Nougat, and Vision Parse offered impressive conversion capabilities but weren't designed for this specific use case.

DescribePDF fills this gap by generating rich, contextual descriptions that capture both the visual and textual elements of each page, making the content accessible for RAG systems and for people with visual impairments.

## How DescribePDF Works

DescribePDF employs a methodical approach to convert visual PDF content into detailed descriptions:

1. **PDF Preparation**: The process begins by analyzing the PDF structure and rendering individual pages as high-quality images.

2. **Enhanced Text Extraction** (Optional): When enabled, DescribePDF uses the Markitdown library to extract text content that provides additional context for the description.

3. **Document Summarization** (Optional): The tool can generate an overall summary of the document to provide context for page descriptions.

4. **Vision-Language Processing**: Each page image is sent to a Vision-Language Model (VLM) with a carefully crafted prompt, which may include the extracted text and document summary.

5. **Multilingual Description Generation**: The VLM generates detailed descriptions of each page in the specified language, including visual elements, text content, and structural information.

6. **Markdown Compilation**: The individual page descriptions are compiled into a single, structured Markdown document that preserves the page-by-page organization of the original PDF.

This approach ensures that even visually complex documents like catalogs, presentations, and scanned materials can be effectively described and indexed.

## Comparison with Similar Tools

DescribePDF differentiates itself from other PDF processing tools by focusing on creating rich descriptions rather than trying to replicate the exact document structure:

| Feature | DescribePDF | [MarkItDown](https://github.com/microsoft/markitdown) | [Vision Parse](https://github.com/iamarunbrahma/vision-parse) | [MinerU](https://github.com/opendatalab/MinerU) |
|---------|-------------|--------------|--------------|-----------|
| **Primary Purpose** | Generate detailed page descriptions | Convert PDF to Markdown with structure preserved | Parse PDF to formatted Markdown | Convert PDF to machine-readable formats |
| **Output Focus** | Context-rich descriptions | Document layout and structure | Precise content replication | Structure and formula preservation |
| **Use Case** | Visual documents, catalogs, RAG indexing | Text-heavy documents, general conversion | Scientific literature, LaTeX equations | Scientific papers, complex layouts |
| **VLM Integration** | Primary feature | Not core feature | Primary feature | Supplementary feature |
| **Local Model Support** | ✅ (via Ollama) | ❌ | ✅ (via Ollama) | ✅ |
| **Cloud API Support** | ✅ (via OpenRouter) | ✅ (optional) | ✅ (OpenAI, Google, etc.) | ❌ |
| **Multilingual Support** | ✅ | ✅ | ✅ | ✅ |
| **Document Summary** | ✅ | ❌ | ❌ | ❌ |
| **Web Interface** | ✅ | ❌ | ❌ | ✅ |

## Quick Start

### Online Demo

Try DescribePDF without installation:

<a href="https://huggingface.co/spaces/davidlms/describepdf">
  <img src="https://img.shields.io/badge/Demo-HuggingFace-yellow?style=for-the-badge&logo=huggingface" alt="HuggingFace Space">
</a>

### Quick CLI Example

```bash
# Install the package
pip install describepdf

# Process a PDF with default settings (OpenRouter)
describepdf document.pdf

# Process a PDF with Ollama local models
describepdf document.pdf --local
```

## Installation

### Prerequisites

- Python 3.8 or higher
- For OpenRouter: An API key from [OpenRouter](https://openrouter.ai)
- For local models: [Ollama](https://ollama.ai) installed and running

### Option 1: Install with pip

```bash
pip install describepdf
```

### Option 2: Install with venv

```bash
# Create and activate a virtual environment
python -m venv describepdf-env
source describepdf-env/bin/activate  # On Windows: describepdf-env\Scripts\activate

# Install the package
pip install describepdf
```

### Option 3: Install with uv

```bash
# Install uv if you don't have it
pip install uv

# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package
uv pip install describepdf
```

### Configuration

Create a `.env` file in your working directory with the following settings:

```
# API Keys
OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY"

# Ollama Configuration
OLLAMA_ENDPOINT="http://localhost:11434"

# OpenRouter models
DEFAULT_OR_VLM_MODEL="qwen/qwen2.5-vl-72b-instruct"
DEFAULT_OR_SUMMARY_MODEL="google/gemini-2.5-flash-preview"

# Ollama models
DEFAULT_OLLAMA_VLM_MODEL="llama3.2-vision"
DEFAULT_OLLAMA_SUMMARY_MODEL="mistral-small3.1"

# Common Configuration
DEFAULT_LANGUAGE="English"
DEFAULT_USE_MARKITDOWN="true"
DEFAULT_USE_SUMMARY="false"
```

## Usage

### Command Line Interface

DescribePDF offers a flexible command-line interface:

```bash
# Basic usage (with OpenRouter)
describepdf document.pdf

# Use Ollama as provider
describepdf document.pdf --local --endpoint http://localhost:11434

# Specify an output file
describepdf document.pdf -o result.md

# Change the output language
describepdf document.pdf -l Spanish

# Use Markitdown and summary generation
describepdf document.pdf --use-markitdown --use-summary

# View all available options
describepdf --help
```

#### Command Line Options

```
usage: describepdf [-h] [-o OUTPUT] [-k API_KEY] [--local] [--endpoint ENDPOINT]
                   [-m VLM_MODEL] [-l LANGUAGE] [--use-markitdown] [--use-summary]
                   [--summary-model SUMMARY_MODEL] [-v]
                   pdf_file

DescribePDF - Convert a PDF to detailed Markdown descriptions

positional arguments:
  pdf_file              Path to the PDF file to process

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path to the output Markdown file
  -k API_KEY, --api-key API_KEY
                        OpenRouter API Key (overrides the one in .env file)
  --local               Use local Ollama instead of OpenRouter
  --endpoint ENDPOINT   Ollama endpoint URL (default: http://localhost:11434)
  -m VLM_MODEL, --vlm-model VLM_MODEL
                        VLM model to use
  -l LANGUAGE, --language LANGUAGE
                        Output language
  --use-markitdown      Use Markitdown for enhanced text extraction
  --use-summary         Generate and use a PDF summary
  --summary-model SUMMARY_MODEL
                        Model to generate the summary
  -v, --verbose         Verbose mode (show debug messages)
```

### Web Interface

DescribePDF provides two web interfaces powered by Gradio:

#### OpenRouter Interface

```bash
# Start the OpenRouter web interface
describepdf-web

# Alternatively
python -m describepdf.ui
```

#### Ollama Interface

```bash
# Start the Ollama web interface
describepdf-web-ollama

# Alternatively
python -m describepdf.ui_ollama
```

### Python API

You can also use DescribePDF programmatically in your Python code:

```python
from describepdf.core import convert_pdf_to_markdown

# Configure the conversion
config = {
    "provider": "openrouter",  # or "ollama"
    "openrouter_api_key": "your_api_key",  # for OpenRouter
    "ollama_endpoint": "http://localhost:11434",  # for Ollama
    "vlm_model": "qwen/qwen2.5-vl-72b-instruct",  # or any supported model
    "output_language": "English",
    "use_markitdown": True,
    "use_summary": False
}

# Define a progress callback (optional)
def progress_callback(progress_value, status):
    print(f"{status} - {progress_value*100:.0f}%")

# Convert PDF to Markdown
status, markdown = convert_pdf_to_markdown(
    "document.pdf",
    config,
    progress_callback
)

# Save the result
if markdown:
    with open("result.md", "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Success: {status}")
else:
    print(f"Error: {status}")
```

## Customization

### Prompt Templates

DescribePDF uses customizable prompt templates located in the `prompts/` directory:

- `vlm_prompt_base.md` - Base prompt for VLM description
- `vlm_prompt_with_markdown.md` - Prompt including Markitdown context
- `vlm_prompt_with_summary.md` - Prompt including document summary
- `vlm_prompt_full.md` - Combined prompt with both Markitdown and summary
- `summary_prompt.md` - Prompt for generating document summaries

You can modify these templates to customize the descriptions generated by the models.

### Model Selection

DescribePDF supports a variety of models:

#### OpenRouter Models:
- VLM: `qwen/qwen2.5-vl-72b-instruct`, `google/gemini-2.5-pro-preview`, `openai/chatgpt-4o-latest`
- Summary: `google/gemini-2.5-flash-preview`, `anthropic/claude-3.5-sonnet`

#### Ollama Models:
- VLM: `llama3.2-vision`, `bakllava` (recommended to have at least 16GB VRAM)
- Summary: `qwen2.5`, `mistral-small3.1`, `llama3.2`

## Future Development

The DescribePDF project is under active development. Future plans include:

- **Enhanced Table Detection**: Improved recognition and description of tabular data
- **Figure and Chart Analysis**: More detailed analysis of charts, graphs, and figures
- **Document Comparison**: Tools for comparing descriptions of multiple versions of a document
- **Custom Parser Integration**: Support for domain-specific parsers for specialized documents
- **API Service**: Creating a standalone API for integration with other applications
- **Batch Processing**: Tools for efficient processing of multiple PDFs
- **Text-to-Speech Integration**: Add options to generate audio narrations of descriptions
- **Fine-tuned Models**: Develop specialized models for specific document types
- **Domain-Specific Prompt Templates**: Create templates optimized for legal, medical, technical, and other specialized content

## License

DescribePDF is released under the [MIT License](https://github.com/DavidLMS/DescribePDF/blob/main/LICENSE). You are free to use, modify, and distribute the code for both commercial and non-commercial purposes.

## Contributing

Contributions to DescribePDF are welcome! Whether you're improving the code, enhancing the documentation, or suggesting new features, your input is valuable. Please check out the [CONTRIBUTING.md](https://github.com/DavidLMS/DescribePDF/blob/main/CONTRIBUTING.md) file for guidelines on how to get started and make your contributions count.