#!/usr/bin/env python
"""
Simple connectivity test for the async OpenAI-compatible client.

- Loads configs/model.yaml via ConfigManager
- Builds client via ClientManager
- Sends a single minimal completion request
  - Normal completion: "def "
  - FIM special-tokens completion: "<|fim_prefix|> def <|fim_suffix|> pass <|fim_middle|>"
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.core.config_manager import ConfigManager
from evoselfcode.core.client_manager import ClientManager
from evoselfcode.utils.logger import setup_task_logger, LoggerManager


async def test_once(client, prompt: str, label: str) -> bool:
    try:
        results = await client.complete_batch_async(
            prompts=[prompt],
            max_tokens=16,
            temperature=0.4,
            top_p=0.9,
            n=1,
            stop=["(", " ", "\n"],
        )
        text = results[0][0].get("text", "").strip()
        print(f"[{label}] OK: {text[:100]}")
        return True
    except Exception as e:
        print(f"[{label}] FAIL: {e}")
        return False


async def main():
    # Logging to logs/datagen/connectivity for convenience
    LoggerManager.setup_base_dir(PROJECT_ROOT / "logs")
    _logger = setup_task_logger("datagen", "connectivity")

    # Load model config and build client
    model_cfg_path = PROJECT_ROOT / "configs/model.yaml"
    cfg = ConfigManager.from_file(model_cfg_path)
    cm = ClientManager(cfg)
    client = cm.completion_client

    # Normal completion
    ok1 = await test_once(client, "def ", "normal")

    # FIM completion via special tokens
    fim_prompt = "<|fim_prefix|> def <|fim_suffix|> pass <|fim_middle|>"
    ok2 = await test_once(client, fim_prompt, "fim-tokens")

    # Summary exit code
    success = ok1 or ok2
    print(f"Summary: normal={ok1}, fim={ok2}")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


