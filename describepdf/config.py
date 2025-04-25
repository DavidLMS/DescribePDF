"""
Configuration module for DescribePDF.

This module manages loading configuration from environment variables
and prompt templates from files.
"""
import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import pathlib

# Setup central logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(module)s] - %(message)s')
logger = logging.getLogger('describepdf')

# Directory containing prompt templates (making path absolute by using current file location)
SCRIPT_DIR = pathlib.Path(__file__).parent.parent.absolute()
PROMPTS_DIR = pathlib.Path(SCRIPT_DIR) / "prompts"

# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
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
PROMPT_FILES: Dict[str, str] = {
    "summary": "summary_prompt.md",
    "vlm_base": "vlm_prompt_base.md",
    "vlm_markdown": "vlm_prompt_with_markdown.md",
    "vlm_summary": "vlm_prompt_with_summary.md",
    "vlm_full": "vlm_prompt_full.md"
}

# Cache for loaded configuration
_CONFIG_CACHE: Optional[Dict[str, Any]] = None

# Cache for loaded prompts
_PROMPTS_CACHE: Optional[Dict[str, str]] = None

def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables (.env file).
    
    This function reads configuration values from environment variables,
    falling back to default values when environment variables are not set.
    
    Returns:
        Dict[str, Any]: Dictionary with the loaded configuration
    """
    load_dotenv()

    # Start with the default config
    loaded_config = DEFAULT_CONFIG.copy()
    
    # Override defaults with environment variables if present
    if os.getenv("OPENROUTER_API_KEY"):
        loaded_config["openrouter_api_key"] = os.getenv("OPENROUTER_API_KEY")
        
    if os.getenv("DEFAULT_OR_VLM_MODEL"):
        loaded_config["or_vlm_model"] = os.getenv("DEFAULT_OR_VLM_MODEL")
        
    if os.getenv("DEFAULT_OR_SUMMARY_MODEL"):
        loaded_config["or_summary_model"] = os.getenv("DEFAULT_OR_SUMMARY_MODEL")
        
    if os.getenv("OLLAMA_ENDPOINT"):
        loaded_config["ollama_endpoint"] = os.getenv("OLLAMA_ENDPOINT")
        
    if os.getenv("DEFAULT_OLLAMA_VLM_MODEL"):
        loaded_config["ollama_vlm_model"] = os.getenv("DEFAULT_OLLAMA_VLM_MODEL")
        
    if os.getenv("DEFAULT_OLLAMA_SUMMARY_MODEL"):
        loaded_config["ollama_summary_model"] = os.getenv("DEFAULT_OLLAMA_SUMMARY_MODEL")
        
    if os.getenv("DEFAULT_LANGUAGE"):
        loaded_config["output_language"] = os.getenv("DEFAULT_LANGUAGE")
        
    if os.getenv("DEFAULT_USE_MARKITDOWN"):
        loaded_config["use_markitdown"] = str(os.getenv("DEFAULT_USE_MARKITDOWN")).lower() == 'true'
        
    if os.getenv("DEFAULT_USE_SUMMARY"):
        loaded_config["use_summary"] = str(os.getenv("DEFAULT_USE_SUMMARY")).lower() == 'true'

    logger.info("Configuration loaded from environment variables.")
    
    # Log configuration without sensitive data
    log_config = loaded_config.copy()
    if "openrouter_api_key" in log_config and log_config["openrouter_api_key"]:
        log_config["openrouter_api_key"] = f"***{log_config['openrouter_api_key'][-5:]}" if len(log_config['openrouter_api_key']) > 5 else "*****"
    logger.debug(f"Effective configuration: {log_config}")
    
    return loaded_config

def load_prompt_templates() -> Dict[str, str]:
    """
    Load prompt templates from the prompts directory.
    
    This function reads template files from the prompts directory specified by
    PROMPTS_DIR and maps them to their corresponding keys in the PROMPT_FILES dictionary.
    
    Returns:
        Dict[str, str]: Dictionary with loaded prompt templates
    """
    templates: Dict[str, str] = {}
    
    if not PROMPTS_DIR.is_dir():
        logger.error(f"Prompts directory '{PROMPTS_DIR}' not found.")
        return templates

    for key, filename in PROMPT_FILES.items():
        filepath = PROMPTS_DIR / filename
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                templates[key] = f.read()
        except FileNotFoundError:
            logger.error(f"Prompt file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error reading prompt file {filepath}: {e}")
    
    logger.info(f"Loaded {len(templates)} prompt templates.")
    return templates

def get_config() -> Dict[str, Any]:
    """
    Get the configuration from .env.
    
    This function loads the configuration only once and returns the cached version
    on subsequent calls, improving efficiency and ensuring consistency.
    
    Returns:
        Dict[str, Any]: Current configuration dictionary
    """
    global _CONFIG_CACHE
    
    if _CONFIG_CACHE is None:
        _CONFIG_CACHE = load_env_config()
        
    return _CONFIG_CACHE

def reload_config() -> Dict[str, Any]:
    """
    Force reload of configuration from .env.
    
    This function can be used when configuration needs to be explicitly refreshed.
    
    Returns:
        Dict[str, Any]: Updated configuration dictionary
    """
    global _CONFIG_CACHE
    _CONFIG_CACHE = load_env_config()
    return _CONFIG_CACHE

def get_prompts() -> Dict[str, str]:
    """
    Get the prompt templates.
    
    This function loads the prompt templates only once and returns the cached version
    on subsequent calls, improving efficiency.
    
    Returns:
        Dict[str, str]: Dictionary with loaded prompt templates
    """
    global _PROMPTS_CACHE
    
    if _PROMPTS_CACHE is None:
        _PROMPTS_CACHE = load_prompt_templates()
        
    return _PROMPTS_CACHE

def get_required_prompts_for_config(cfg: Dict[str, Any]) -> Dict[str, str]:
    """
    Get only the prompt templates required for the given configuration.
    
    This function determines which prompt templates are necessary based on the
    provided configuration and returns only those templates.
    
    Args:
        cfg (Dict[str, Any]): Configuration dictionary
        
    Returns:
        Dict[str, str]: Dictionary with required prompt templates
    """
    prompts = get_prompts()
    required_keys: List[str] = ["vlm_base"]
    
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