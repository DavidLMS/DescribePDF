![poster](assets/poster.png)

Una herramienta que convierte archivos PDF en descripciones detalladas en formato Markdown utilizando modelos de visión-lenguaje (VLM).

## Características

- Análisis página por página con descripción completa
- Soporte para múltiples idiomas
- Integración con Markitdown para mejor extracción de texto
- Opción de generar resúmenes del documento
- Compatible con modelos VLM a través de OpenRouter (por defecto)
- Soporte para modelos locales a través de Ollama
- Disponible como interfaz web y como herramienta de línea de comandos

## Estructura del Proyecto

```
describepdf/
├── describepdf/
│   ├── __init__.py
│   ├── config.py           # Carga/Guarda config, .env, prompts
│   ├── pdf_processor.py    # Lógica de PyMuPDF
│   ├── markitdown_processor.py # Lógica de Markitdown
│   ├── openrouter_client.py # Lógica de API OpenRouter
│   ├── ollama_client.py    # Lógica de API Ollama
│   ├── summarizer.py       # Lógica de resumen
│   ├── core.py             # Orquestador principal de conversión
│   ├── ui.py               # Definición de la UI Gradio para OpenRouter
│   ├── ui_ollama.py        # Definición de la UI Gradio para Ollama
│   └── cli.py              # Interfaz de línea de comandos
├── prompts/
│   ├── summary_prompt.md
│   ├── vlm_prompt_base.md
│   ├── vlm_prompt_with_markdown.md
│   ├── vlm_prompt_with_summary.md
│   └── vlm_prompt_full.md
├── main.py                 # Punto de entrada para lanzar la app
├── setup.py                # Script de instalación
├── .env                    # Para la configuración (¡Añadir a .gitignore!)
└── requirements.txt        # Dependencias
```

## Instalación

### Requisitos previos

- Python 3.8 o superior
- Una API key de OpenRouter (si se utiliza ese proveedor)
- Ollama instalado localmente (si se utiliza ese proveedor)

### Instalación desde fuente

```bash
# Clonar el repositorio
git clone https://github.com/davidlms/describepdf.git
cd describepdf

# Instalar dependencias
pip install -r requirements.txt

# Instalar el paquete
pip install -e .
```

### Configuración

Crea un archivo `.env` en el directorio raíz con tu configuración:

```
# Si usas OpenRouter:
OPENROUTER_API_KEY="tu_api_key_aquí"

# Si usas Ollama:
OLLAMA_ENDPOINT="http://localhost:11434"  # Por defecto

# Configuración de modelos
DEFAULT_OR_VLM_MODEL="qwen/qwen2.5-vl-72b-instruct"
DEFAULT_OR_SUMMARY_MODEL="google/gemini-2.5-flash-preview"
DEFAULT_OLLAMA_VLM_MODEL="llama3.2-vision"
DEFAULT_OLLAMA_SUMMARY_MODEL="qwen2.5"

# Configuración opcional general
DEFAULT_LANGUAGE="Spanish"
DEFAULT_USE_MARKITDOWN="true"
DEFAULT_USE_SUMMARY="false"
```

## Uso

### Interfaz Web

Puedes iniciar la interfaz web de varias maneras:

```bash
# Interfaz para OpenRouter
python main.py --web
describepdf-web         # Si instalaste el paquete

# Interfaz para Ollama local
python main.py --web-ollama
describepdf-web-ollama  # Si instalaste el paquete
```

### Línea de Comandos

La herramienta de línea de comandos se puede usar así:

```bash
# Uso básico (con OpenRouter)
describepdf documento.pdf

# Usar Ollama como proveedor
describepdf documento.pdf --local --endpoint http://localhost:11434

# Especificar un archivo de salida
describepdf documento.pdf -o resultado.md

# Cambiar el idioma de salida
describepdf documento.pdf -l Spanish

# Usar Markitdown y generación de resumen
describepdf documento.pdf --use-markitdown --use-summary

# Ver todas las opciones disponibles
describepdf --help
```

### Opciones de línea de comandos

```
usage: describepdf [-h] [-o OUTPUT] [-k API_KEY] [--local] [--endpoint ENDPOINT]
                   [-m VLM_MODEL] [-l LANGUAGE] [--use-markitdown] [--use-summary]
                   [--summary-model SUMMARY_MODEL] [-v]
                   pdf_file

DescribePDF - Convierte un PDF a descripciones en formato Markdown

positional arguments:
  pdf_file              Ruta al archivo PDF a procesar

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Ruta del archivo Markdown de salida
  -k API_KEY, --api-key API_KEY
                        OpenRouter API Key (sobreescribe la del archivo .env)
  --local               Usar Ollama local en lugar de OpenRouter
  --endpoint ENDPOINT   URL del endpoint de Ollama (por defecto: http://localhost:11434)
  -m VLM_MODEL, --vlm-model VLM_MODEL
                        Modelo VLM a utilizar
  -l LANGUAGE, --language LANGUAGE
                        Idioma de salida
  --use-markitdown      Utilizar Markitdown para extracción de texto mejorada
  --use-summary         Generar y utilizar un resumen del PDF
  --summary-model SUMMARY_MODEL
                        Modelo para generar el resumen
  -v, --verbose         Modo detallado (muestra mensajes de depuración)
```

## Testing

The project includes a comprehensive test suite using pytest. The tests cover unit tests for individual components as well as integration tests for the core functionality.

### Setup Testing Environment

To set up the testing environment, install the required testing dependencies:

```bash
pip install -r test_requirements.txt
```

### Running Tests

To run all tests:

```bash
pytest
```

To run tests with coverage report:

```bash
pytest --cov=describepdf tests/
```

To run a specific test file:

```bash
pytest tests/test_pdf_processor.py
```

### Test Structure

The tests are organized in the following structure:

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and test configuration
├── test_pdf_processor.py    # Tests for PDF processing functionality
├── test_markitdown.py       # Tests for Markitdown integration
├── test_openrouter_client.py # Tests for OpenRouter API client
├── test_ollama_client.py    # Tests for Ollama API client
├── test_summarizer.py       # Tests for document summary functionality
├── test_core.py             # Tests for core conversion logic
└── test_cli.py              # Tests for command line interface
```

### Mocking External Dependencies

The tests use pytest-mock and the responses library to mock external dependencies like:
- PDF rendering (PyMuPDF)
- API calls to OpenRouter and Ollama
- File system operations

This ensures tests can run without requiring actual PDFs or API keys.