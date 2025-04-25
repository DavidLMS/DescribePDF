"""
Configuration module for DescribePDF.

This module manages loading configuration from environment variables
and prompt templates from files.
"""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Setup central logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
logger = logging.getLogger('describepdf')

# Directory containing prompt templates
PROMPTS_DIR = "prompts"

# Default configuration values if not found in environment
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

# Mapping of prompt template identifiers to their file names
PROMPT_FILES = {
    "summary": "summary_prompt.md",
    "vlm_base": "vlm_prompt_base.md",
    "vlm_markdown": "vlm_prompt_with_markdown.md",
    "vlm_summary": "vlm_prompt_with_summary.md",
    "vlm_full": "vlm_prompt_full.md"
}

# Global configuration storage
_app_config: Dict[str, Any] = {}
_prompt_templates: Dict[str, str] = {}

def load_env_config() -> Dict[str, Any]:
    """
    Load configuration exclusively from environment variables (.env file).
    
    Returns:
        Dict[str, Any]: Dictionary with the loaded configuration
    """
    global _app_config

    load_dotenv()

    loaded_config = {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY") or FALLBACK_DEFAULTS["openrouter_api_key"],
        "or_vlm_model": os.getenv("DEFAULT_OR_VLM_MODEL") or FALLBACK_DEFAULTS["or_vlm_model"],
        "or_summary_model": os.getenv("DEFAULT_OR_SUMMARY_MODEL") or FALLBACK_DEFAULTS["or_summary_model"],
        
        "ollama_endpoint": os.getenv("OLLAMA_ENDPOINT") or FALLBACK_DEFAULTS["ollama_endpoint"],
        "ollama_vlm_model": os.getenv("DEFAULT_OLLAMA_VLM_MODEL") or FALLBACK_DEFAULTS["ollama_vlm_model"],
        "ollama_summary_model": os.getenv("DEFAULT_OLLAMA_SUMMARY_MODEL") or FALLBACK_DEFAULTS["ollama_summary_model"],
        
        "output_language": os.getenv("DEFAULT_LANGUAGE") or FALLBACK_DEFAULTS["output_language"],
        "use_markitdown": str(os.getenv("DEFAULT_USE_MARKITDOWN", str(FALLBACK_DEFAULTS["use_markitdown"]))).lower() == 'true',
        "use_summary": str(os.getenv("DEFAULT_USE_SUMMARY", str(FALLBACK_DEFAULTS["use_summary"]))).lower() == 'true'
    }

    _app_config = loaded_config
    logger.info("Configuration loaded from environment variables.")
    
    # Log configuration without sensitive data
    log_config = _app_config.copy()
    if "openrouter_api_key" in log_config and log_config["openrouter_api_key"]:
        log_config["openrouter_api_key"] = f"***{log_config['openrouter_api_key'][-5:]}" if len(log_config['openrouter_api_key']) > 5 else "*****"
    logger.debug(f"Effective configuration: {log_config}")
    
    return _app_config

def load_prompt_templates() -> Dict[str, str]:
    """
    Load prompt templates from the prompts directory.
    
    Returns:
        Dict[str, str]: Dictionary with loaded prompt templates
    """
    global _prompt_templates
    templates = {}
    
    if not os.path.isdir(PROMPTS_DIR):
        logger.error(f"Prompts directory '{PROMPTS_DIR}' not found.")
        return templates

    for key, filename in PROMPT_FILES.items():
        filepath = os.path.join(PROMPTS_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                templates[key] = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error reading prompt file {filepath}: {e}")
    
    logger.info(f"Loaded {len(templates)} prompt templates.")
    _prompt_templates = templates
    return templates

def get_config() -> Dict[str, Any]:
    """
    Get the currently loaded configuration from .env.
    
    Returns:
        Dict[str, Any]: Current configuration dictionary
    """
    if not _app_config:
        load_env_config()
    return _app_config

def get_prompts() -> Dict[str, str]:
    """
    Get the currently loaded prompt templates.
    
    Returns:
        Dict[str, str]: Dictionary with loaded prompt templates
    """
    if not _prompt_templates:
        load_prompt_templates()
    return _prompt_templates

def get_required_prompts_for_config(cfg: Dict[str, Any]) -> Dict[str, str]:
    """
    Get only the prompt templates required for the given configuration.
    
    Args:
        cfg (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, str]: Dictionary with required prompt templates
    """
    prompts = get_prompts()
    required_keys = ["vlm_base"]
    
    has_markdown = cfg.get("use_markitdown", False)
    has_summary = cfg.get("use_summary", False)
    
    if has_markdown and has_summary:
        required_keys.append("vlm_full")
    elif has_markdown:
        required_keys.append("vlm_markdown")
    elif has_summary:
        required_keys.append("vlm_summary")
        
    if has_summary:
        required_keys.append("summary")
        
    # Check if all required prompts are available
    missing = [key for key in required_keys if key not in prompts]
    if missing:
        logger.error(f"Missing required prompt templates: {', '.join(missing)}")
        return {}
        
    return {key: prompts[key] for key in required_keys if key in prompts}

# Load configuration and prompt templates at module import
load_env_config()
load_prompt_templates()