import os
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PROMPTS_DIR = "prompts"

FALLBACK_DEFAULTS = {
    "openrouter_api_key": None,
    "or_vlm_model": "qwen/qwen2.5-vl-72b-instruct",
    "or_summary_model": "google/gemini-2.5-flash-preview",
    
    "ollama_endpoint": "http://localhost:11434",
    "ollama_vlm_model": "llama3.2-vision",
    "ollama_summary_model": "qwen2.5",
    
    "output_language": "English",
    "use_markitdown": False,
    "use_summary": False
}

PROMPT_FILES = {
    "summary": "summary_prompt.md",
    "vlm_base": "vlm_prompt_base.md",
    "vlm_markdown": "vlm_prompt_with_markdown.md",
    "vlm_summary": "vlm_prompt_with_summary.md",
    "vlm_full": "vlm_prompt_full.md"
}

app_config = {}
prompt_templates = {}

def load_env_config():
    """Carga la configuración exclusivamente desde variables de entorno (.env)."""
    global app_config

    load_dotenv()

    loaded_config = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY") or FALLBACK_DEFAULTS["openrouter_api_key"],
        "or_vlm_model": os.getenv("DEFAULT_OR_VLM_MODEL") or FALLBACK_DEFAULTS["or_vlm_model"],
        "or_summary_model": os.getenv("DEFAULT_OR_SUMMARY_MODEL") or FALLBACK_DEFAULTS["or_summary_model"],
        
        "ollama_endpoint": os.getenv("OLLAMA_ENDPOINT") or FALLBACK_DEFAULTS["ollama_endpoint"],
        "ollama_vlm_model": os.getenv("DEFAULT_OLLAMA_VLM_MODEL") or FALLBACK_DEFAULTS["ollama_vlm_model"],
        "ollama_summary_model": os.getenv("DEFAULT_OLLAMA_SUMMARY_MODEL") or FALLBACK_DEFAULTS["ollama_summary_model"],
        
        "output_language": os.getenv("DEFAULT_LANGUAGE") or FALLBACK_DEFAULTS["output_language"],
        "use_markitdown": str(os.getenv("DEFAULT_USE_MARKITDOWN", FALLBACK_DEFAULTS["use_markitdown"])).lower() == 'true',
        "use_summary": str(os.getenv("DEFAULT_USE_SUMMARY", FALLBACK_DEFAULTS["use_summary"])).lower() == 'true'
    }

    app_config = loaded_config
    logging.info("Configuration loaded from environment variables.")
    log_config = app_config.copy()
    log_config.pop("openrouter_api_key", None)
    logging.debug(f"Effective configuration (excluding API key): {log_config}")
    return app_config

def load_prompt_templates():
    """Carga las plantillas de prompt desde la carpeta prompts."""
    global prompt_templates
    templates = {}
    if not os.path.isdir(PROMPTS_DIR):
        logging.error(f"Prompts directory '{PROMPTS_DIR}' not found.")
        return templates

    for key, filename in PROMPT_FILES.items():
        filepath = os.path.join(PROMPTS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                templates[key] = f.read()
        except FileNotFoundError:
            logging.error(f"Prompt file not found: {filepath}")
        except Exception as e:
            logging.error(f"Error reading prompt file {filepath}: {e}")
    logging.info(f"Loaded {len(templates)} prompt templates.")
    prompt_templates = templates
    return templates

def get_config():
    """Devuelve la configuración cargada actualmente desde .env."""
    if not app_config:
        load_env_config()
    return app_config

def get_prompts():
    """Devuelve los prompts cargados actualmente."""
    if not prompt_templates:
        load_prompt_templates()
    return prompt_templates

load_env_config()
load_prompt_templates()