# DescribePDF

Una herramienta que convierte archivos PDF en descripciones detalladas en formato Markdown utilizando modelos de visión-lenguaje (VLM).

## Características

- Análisis página por página con descripción completa
- Soporte para múltiples idiomas
- Integración con Markitdown para mejor extracción de texto
- Opción de generar resúmenes del documento
- Compatible con modelos VLM a través de OpenRouter
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
│   ├── summarizer.py       # Lógica de resumen
│   ├── core.py             # Orquestador principal de conversión
│   ├── ui.py               # Definición de la UI Gradio
│   └── cli.py              # Interfaz de línea de comandos
├── prompts/
│   ├── summary_prompt.md
│   ├── vlm_prompt_base.md
│   ├── vlm_prompt_with_markdown.md
│   ├── vlm_prompt_with_summary.md
│   └── vlm_prompt_full.md
├── main.py                 # Punto de entrada para lanzar la app
├── setup.py                # Script de instalación
├── .env                    # Para la API Key (¡Añadir a .gitignore!)
└── requirements.txt        # Dependencias
```

## Instalación

### Requisitos previos

- Python 3.8 o superior
- Una API key de OpenRouter

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

Crea un archivo `.env` en el directorio raíz con tu API key de OpenRouter:

```
OPENROUTER_API_KEY="tu_api_key_aquí"

# Opcional: configuración predeterminada
#DEFAULT_VLM_MODEL="qwen/qwen2.5-vl-72b-instruct"
#DEFAULT_LANGUAGE="Spanish"
#DEFAULT_USE_MARKITDOWN="true"
#DEFAULT_USE_SUMMARY="false"
#DEFAULT_SUMMARY_MODEL="google/gemini-2.5-flash-preview"
```

## Uso

### Interfaz Web

Puedes iniciar la interfaz web de dos maneras:

```bash
# Método 1: usando el script main.py con la opción --web
python main.py --web

# Método 2: usando el punto de entrada instalado
describepdf-web
```

### Línea de Comandos

La herramienta de línea de comandos se puede usar así:

```bash
# Uso básico
describepdf documento.pdf

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
usage: describepdf [-h] [-o OUTPUT] [-k API_KEY] [-m VLM_MODEL] [-l LANGUAGE]
                   [--use-markitdown] [--use-summary] [--summary-model SUMMARY_MODEL]
                   [-v]
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