from __future__ import annotations

import logging
from typing import Optional

from ..clients import AsyncOpenAICompletionClient, OpenAIScoringClient
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class ClientManager:
    """
    Client factory and manager.
    Creates and manages API clients based on configuration.
    """
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self._completion_client: Optional[AsyncOpenAICompletionClient] = None
        self._scoring_client: Optional[OpenAIScoringClient] = None
    
    @property
    def completion_client(self) -> AsyncOpenAICompletionClient:
        """Get or create completion client"""
        if self._completion_client is None:
            self._completion_client = self._create_completion_client()
        return self._completion_client
    
    @property
    def scoring_client(self) -> OpenAIScoringClient:
        """Get or create scoring client"""
        if self._scoring_client is None:
            self._scoring_client = self._create_scoring_client()
        return self._scoring_client
    
    def _create_completion_client(self) -> AsyncOpenAICompletionClient:
        """Create async completion client from configuration"""
        api_cfg = self.config.get_section("api")
        models_cfg = self.config.get_section("models")
        concurrency_cfg = api_cfg.get("concurrency", {})
        fim_cfg = api_cfg.get("fim", {})
        
        logger.debug(f"[ClientManager] api_cfg keys: {list(api_cfg.keys())}")
        logger.debug(f"[ClientManager] api_cfg.base_url = {api_cfg.get('base_url')}")
        
        import os
        base_url = os.environ.get("EVOCODE_BASE_URL", api_cfg.get("base_url", "http://localhost:8000"))
        api_key = api_cfg.get("api_key", "EMPTY")
        model = models_cfg.get("default", "Qwen2.5-Coder-32B")
        timeout_s = api_cfg.get("timeout_s", 60)
        max_retries = api_cfg.get("max_retries", 3)
        use_chat_for_fim = fim_cfg.get("use_chat_for_fim", False)
        prefix_key = fim_cfg.get("prefix_key", "prefix")
        suffix_key = fim_cfg.get("suffix_key", "suffix")
        max_concurrent = concurrency_cfg.get("max_concurrent_requests", 10)
        
        logger.info(f"Creating completion client: {base_url}, model={model}, max_concurrent={max_concurrent}")
        
        return AsyncOpenAICompletionClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_s=timeout_s,
            max_retries=max_retries,
            use_chat_for_fim=use_chat_for_fim,
            prefix_key=prefix_key,
            suffix_key=suffix_key,
            max_concurrent=max_concurrent,
        )
    
    def _create_scoring_client(self) -> OpenAIScoringClient:
        """Create scoring client from configuration"""
        api_cfg = self.config.get_section("api")
        models_cfg = self.config.get_section("models")
        
        base_url = api_cfg.get("base_url", "http://localhost:8000")
        api_key = api_cfg.get("api_key", "EMPTY")
        model = models_cfg.get("default", "Qwen2.5-Coder-32B")
        timeout_s = api_cfg.get("timeout_s", 60)
        
        logger.info(f"Creating scoring client: {base_url}, model={model}")
        
        return OpenAIScoringClient(
            base_url=base_url,
            api_key=api_key,
            model=model,
            timeout_s=timeout_s,
        )
    
    def close(self):
        """Close all clients and release resources"""
        # AsyncOpenAI will handle cleanup automatically
        self._completion_client = None
        self._scoring_client = None

