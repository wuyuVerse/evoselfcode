from __future__ import annotations

from pathlib import Path
from typing import Dict, Literal, Optional, Tuple

import yaml

from ..constants import CONFIGS_DIR


def load_prompts_config(config_path: Optional[Path] = None) -> Dict:
    """Load prompts configuration from datagen.yaml"""
    if config_path is None:
        config_path = CONFIGS_DIR / "datagen.yaml"
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config.get("prompts", {})


def build_funcname_prompt_fim(config: Optional[Dict] = None) -> Tuple[str, str]:
    """
    Build FIM mode function name generation prompt.
    Returns (prefix, suffix).
    """
    if config is None:
        config = load_prompts_config()
    
    fim_config = config.get("funcname", {}).get("fim", {})
    prefix = fim_config.get("prefix", "This is an algorithm function.\n\ndef ")
    suffix = fim_config.get("suffix", "():\n")
    
    return prefix, suffix


def build_funcname_prompt_l2r(config: Optional[Dict] = None) -> str:
    """
    Build Left-to-Right mode function name generation prompt.
    Returns prompt string.
    """
    if config is None:
        config = load_prompts_config()
    
    l2r_config = config.get("funcname", {}).get("l2r", {})
    prompt = l2r_config.get("prompt", "This is an algorithm function.\n\ndef ")
    
    return prompt


def build_codegen_prompt(func_name: str, description: str, config: Optional[Dict] = None) -> str:
    """
    Build code generation prompt (unified L2R mode).
    """
    if config is None:
        config = load_prompts_config()
    
    template = config.get("codegen", {}).get("template", """This is an algorithm function.

def {func_name}():
    \"\"\"
    {description}
    \"\"\"""")
    
    return template.format(func_name=func_name, description=description)


def extract_funcname_from_completion(text: str, mode: Literal["FIM", "L2R"]) -> str:
    """
    Extract function name from generated text.
    - FIM mode: directly return text (already filled in middle position)
    - L2R mode: extract from "def " to first "(" or whitespace
    """
    text = text.strip()
    if mode == "FIM":
        # FIM returns the function name directly
        return text.split("(")[0].split()[0].strip()
    else:
        # L2R: extract from def xxx
        if text.startswith("def "):
            text = text[4:].strip()
        return text.split("(")[0].split()[0].strip()
