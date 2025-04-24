import os
import json
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constantes ---
CONFIG_FILE = "config.json"
PROMPTS_DIR = "prompts"
DEFAULT_CONFIG = {
    "openrouter_api_key": None,
    "vlm_model": "qwen/qwen2.5-vl-72b-instruct",
    "output_language": "English",
    "use_markitdown": False,
    "use_summary": False,
    "summary_llm_model": "google/gemini-2.5-flash-preview"
}
PROMPT_FILES = {
    "summary": "summary_prompt.md",
    "vlm_base": "vlm_prompt_base.md",
    "vlm_markdown": "vlm_prompt_with_markdown.md",
    "vlm_summary": "vlm_prompt_with_summary.md",
    "vlm_full": "vlm_prompt_full.md"
}

# --- Variables Globales ---
config_data = {}
prompt_templates = {}

# --- Funciones ---
def load_config():
    """Carga la configuración desde .env y config.json."""
    global config_data, prompt_templates

    # Cargar desde .env (principalmente para la API Key)
    load_dotenv()
    env_api_key = os.getenv("OPENROUTER_API_KEY")

    # Cargar desde config.json
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
        else:
            logging.warning(f"{CONFIG_FILE} not found. Using default configuration.")
            config_data = DEFAULT_CONFIG.copy()
            save_config(config_data) # Crear archivo inicial

    except json.JSONDecodeError:
        logging.error(f"Error decoding {CONFIG_FILE}. Using default configuration.")
        config_data = DEFAULT_CONFIG.copy()
    except Exception as e:
        logging.error(f"Error loading {CONFIG_FILE}: {e}. Using default configuration.")
        config_data = DEFAULT_CONFIG.copy()

    # Priorizar la API Key del .env si existe y no está en config.json o es None/vacía
    if env_api_key and (not config_data.get("openrouter_api_key")):
         config_data["openrouter_api_key"] = env_api_key
         # No guardamos la clave del .env en config.json por seguridad

    # Asegurar que todas las claves por defecto existan
    for key, value in DEFAULT_CONFIG.items():
        if key not in config_data:
            config_data[key] = value

    # Cargar plantillas de prompts
    prompt_templates = load_prompt_templates()

    logging.info("Configuration loaded.")
    return config_data

def save_config(new_config_data):
    """Guarda la configuración en config.json."""
    global config_data
    try:
        # No guardar la API key si vino del .env y no fue explícitamente puesta en la UI
        save_data = new_config_data.copy()
        env_key = os.getenv("OPENROUTER_API_KEY")
        if save_data.get("openrouter_api_key") == env_key:
             # Si la clave en la data a guardar es la misma que la del .env,
             # la eliminamos para no escribirla en config.json
             # Si el usuario la puso manualmente en la UI, SÍ se guardará.
             # Una forma simple de detectar esto es si la clave actual en memoria
             # (config_data) es diferente a la que se intenta guardar.
             # O más simple: si la clave a guardar es la del .env, no la guardes.
             # Esto asume que el usuario no pegará la misma clave del .env en la UI.
             # Una lógica más robusta podría requerir rastrear el origen.
             # Por simplicidad, si la clave coincide con .env, no la guardamos en json.
             if save_data.get("openrouter_api_key") == env_key:
                 save_data["openrouter_api_key"] = None # O del config_data original antes del cambio

        with open(CONFIG_FILE, 'w') as f:
            json.dump(save_data, f, indent=2)
        config_data = new_config_data # Actualizar la variable global
        logging.info(f"Configuration saved to {CONFIG_FILE}.")
        return True
    except Exception as e:
        logging.error(f"Error saving configuration to {CONFIG_FILE}: {e}")
        return False

def load_prompt_templates():
    """Carga las plantillas de prompt desde la carpeta prompts."""
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
    return templates

def get_config():
    """Devuelve la configuración cargada actualmente."""
    if not config_data:
        load_config()
    return config_data

def get_prompts():
    """Devuelve los prompts cargados actualmente."""
    if not prompt_templates:
        load_config() # Asegura que los prompts se carguen si no lo están
    return prompt_templates

# Cargar configuración al iniciar el módulo
load_config()