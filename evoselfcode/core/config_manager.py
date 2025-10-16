from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """
    Unified configuration manager.
    Handles loading, merging, and accessing configurations.
    """
    
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self._config = config_dict or {}
    
    @classmethod
    def from_file(cls, config_path: Path) -> "ConfigManager":
        """Load configuration from YAML file"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return cls(config)
    
    @classmethod
    def from_files(cls, *config_paths: Path) -> "ConfigManager":
        """Load and merge multiple configuration files"""
        merged = {}
        for path in config_paths:
            with open(path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                merged = cls._deep_merge(merged, cfg)
        return cls(merged)
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = dict(base)
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-separated path.
        
        Examples:
            config.get("api.base_url")
            config.get("datagen.namegen.temperature", 0.4)
        """
        current = self._config
        for part in key_path.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value"""
        parts = key_path.split(".")
        current = self._config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary"""
        return dict(self._config)
    
    def merge(self, other: "ConfigManager") -> "ConfigManager":
        """Merge with another ConfigManager"""
        merged = self._deep_merge(self._config, other._config)
        return ConfigManager(merged)

