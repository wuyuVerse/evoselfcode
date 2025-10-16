from __future__ import annotations

from typing import Dict, Literal, Tuple

from .config_manager import ConfigManager


class PromptBuilder:
    """
    Prompt template builder.
    Constructs prompts from configuration templates.
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.prompts_cfg = config.get_section("prompts")
        self.fim_cfg = config.get_section("api").get("fim", {})
    
    def build_funcname_fim(self) -> str:
        """
        Build FIM mode function name generation prompt using special tokens.
        Returns complete FIM prompt string.
        """
        funcname_cfg = self.prompts_cfg.get("funcname", {}).get("fim", {})
        prefix_content = funcname_cfg.get("prefix", "This is an algorithm function.\n\ndef ")
        suffix_content = funcname_cfg.get("suffix", "():\n")
        
        # Get FIM tokens
        prefix_token = self.fim_cfg.get("prefix_token", "<|fim_prefix|>")
        suffix_token = self.fim_cfg.get("suffix_token", "<|fim_suffix|>")
        middle_token = self.fim_cfg.get("middle_token", "<|fim_middle|>")
        
        # Build FIM prompt: <|fim_prefix|>content<|fim_suffix|>content<|fim_middle|>
        fim_prompt = f"{prefix_token}{prefix_content}{suffix_token}{suffix_content}{middle_token}"
        return fim_prompt
    
    def build_funcname_l2r(self) -> str:
        """
        Build L2R mode function name generation prompt.
        Returns prompt string.
        """
        l2r_cfg = self.prompts_cfg.get("funcname", {}).get("l2r", {})
        return l2r_cfg.get("prompt", "This is an algorithm function.\n\ndef ")
    
    def build_codegen(self, func_name: str, description: str) -> str:
        """
        Build code generation prompt.
        """
        template = self.prompts_cfg.get("codegen", {}).get("template", """This is an algorithm function.

def {func_name}():
    \"\"\"
    {description}
    \"\"\"""")
        
        return template.format(func_name=func_name, description=description)
    
    def extract_funcname_and_desc(self, text: str, mode: Literal["FIM", "L2R"]) -> tuple[str, str]:
        """
        Extract function name and description from generated text.
        
        Both FIM and L2R now use the same format:
            <description text>
            
            Function name:
            
            def <function_name>():
        
        The only difference is how they're generated (FIM fills middle, L2R continues).
        
        Returns:
            (func_name, description)
        """
        text = text.strip()
        if not text:
            return "", ""
        
        func_name = ""
        description = ""
        
        # Both modes use the same format: description first, then "Function name:\n\ndef <name>"
        if "Function name:" in text:
            parts = text.split("Function name:", 1)
            description = parts[0].strip()
            
            if len(parts) > 1:
                func_part = parts[1].strip()
                # Extract "def <name>" from the function part
                if func_part.startswith("def "):
                    name_part = func_part[4:].strip()  # Skip "def "
                    # Find the end of the function name (stop at '(', ':', space, or newline)
                    for i, ch in enumerate(name_part):
                        if not (ch.isalnum() or ch == '_'):
                            func_name = name_part[:i]
                            break
                    else:
                        func_name = name_part  # No delimiter found
        else:
            # No "Function name:" marker, treat whole text as description
            description = text
        
        return func_name, description
    
    def extract_funcname(self, text: str, mode: Literal["FIM", "L2R"]) -> str:
        """
        Extract function name only (for backward compatibility).
        """
        func_name, _ = self.extract_funcname_and_desc(text, mode)
        return func_name

