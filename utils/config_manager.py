import os
import json
import time
from pathlib import Path
from utils.helpers import PROJECT_ROOT, GOOGLE_API_KEY

CONFIG_PATH = PROJECT_ROOT / "configs" / "api_keys.json"

class ConfigManager:
    """Manages local JSON configuration for API keys to allow GUI editing.
    Uses in-memory caching to avoid re-reading from disk on every API call."""
    
    _cache = None
    _cache_time = 0
    _CACHE_TTL = 30  # seconds — refresh from disk at most every 30s
    
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
            
        return ConfigManager._read_from_disk()

    @staticmethod
    def _read_from_disk():
        """Read config directly from disk (bypasses cache)."""
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)

    @staticmethod
    def load_config():
        """Load config with in-memory caching."""
        now = time.time()
        if ConfigManager._cache is not None and (now - ConfigManager._cache_time) < ConfigManager._CACHE_TTL:
            return ConfigManager._cache
            
        if not CONFIG_PATH.exists():
            data = ConfigManager._init_config()
        else:
            data = ConfigManager._read_from_disk()
        
        ConfigManager._cache = data
        ConfigManager._cache_time = now
        return data

    @staticmethod
    def save_config(data):
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=4)
        # Invalidate cache so next read picks up the new data
        ConfigManager._cache = data
        ConfigManager._cache_time = time.time()
            
    @staticmethod
    def get_gemini_pool():
        return ConfigManager.load_config().get("gemini_keys", [])
        
    @staticmethod
    def get_omdb_key():
        return ConfigManager.load_config().get("omdb_key", "")

