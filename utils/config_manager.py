import os
import json
from pathlib import Path
from utils.helpers import PROJECT_ROOT, GOOGLE_API_KEY

CONFIG_PATH = PROJECT_ROOT / "configs" / "api_keys.json"

class ConfigManager:
    """Manages local JSON configuration for API keys to allow GUI editing."""
    
    @staticmethod
    def _init_config():
        """Create default config if none exists."""
        if not CONFIG_PATH.parent.exists():
            CONFIG_PATH.parent.mkdir(parents=True)
            
        if not CONFIG_PATH.exists():
            default_config = {
                "gemini_keys": [],
                "omdb_key": ""
            }
            # Fallback to .env if available
            if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_gemini_api_key_here":
                default_config["gemini_keys"].append(GOOGLE_API_KEY)
                
            ConfigManager.save_config(default_config)
            return default_config
            
        return ConfigManager.load_config()

    @staticmethod
    def load_config():
        if not CONFIG_PATH.exists():
            return ConfigManager._init_config()
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_config(data):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=4)
            
    @staticmethod
    def get_gemini_pool():
        return ConfigManager.load_config().get("gemini_keys", [])
        
    @staticmethod
    def get_omdb_key():
        return ConfigManager.load_config().get("omdb_key", "")
