from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .constants import CONFIGS_DIR


def load_model_config(model_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load model configuration from model.yaml
    
    Args:
        model_config_path: Path to model config file, defaults to configs/model.yaml
    
    Returns:
        Dictionary with model configuration
    """
    if model_config_path is None:
        model_config_path = CONFIGS_DIR / "model.yaml"
    
    if not model_config_path.exists():
        return {}
    
    with open(model_config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def merge_model_config(base_config: Dict[str, Any], model_config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Merge model configuration into base configuration.
    Model config values are used as defaults, base_config overrides them.
    
    Args:
        base_config: Base configuration dictionary
        model_config_path: Path to model config file
    
    Returns:
        Merged configuration dictionary
    """
    model_cfg = load_model_config(model_config_path)
    
    # Deep merge: model_cfg as base, base_config overrides
    result = dict(model_cfg)
    
    for key, value in base_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_client_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract client configuration from merged config.
    
    Returns dict with keys:
        - base_url
        - api_key
        - model
        - timeout_s
        - max_retries
        - use_chat_for_fim
        - prefix_key
        - suffix_key
        - max_concurrent
        - rate_limit_per_second
    """
    api_cfg = config.get("api", {})
    models_cfg = config.get("models", {})
    concurrency_cfg = api_cfg.get("concurrency", {})
    fim_cfg = api_cfg.get("fim", {})
    
    return {
        "base_url": api_cfg.get("base_url", "http://localhost:8000"),
        "api_key": api_cfg.get("api_key", "EMPTY"),
        "model": models_cfg.get("default", "Qwen2.5-Coder-32B"),
        "timeout_s": api_cfg.get("timeout_s", 60),
        "max_retries": api_cfg.get("max_retries", 3),
        "use_chat_for_fim": fim_cfg.get("use_chat_for_fim", False),
        "prefix_key": fim_cfg.get("prefix_key", "prefix"),
        "suffix_key": fim_cfg.get("suffix_key", "suffix"),
        "max_concurrent": concurrency_cfg.get("max_concurrent_requests", 10),
        "rate_limit_per_second": concurrency_cfg.get("rate_limit_per_second"),
    }

