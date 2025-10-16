from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

from .base import CompletionClient

logger = logging.getLogger(__name__)


class AsyncOpenAICompletionClient(CompletionClient):
    """
    Async OpenAI compatible client with high concurrency support.
    Supports:
    - Normal completion (completions.create)
    - FIM via completions.create(prompt=..., suffix=...)
    - FIM via chat.completions.create(extra_body={"prefix": ..., "suffix": ...})
    - Rate limiting and semaphore control
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "EMPTY",
        model: str = "Qwen2.5-Coder-32B",
        timeout_s: int = 60,
        max_retries: int = 3,
        use_chat_for_fim: bool = False,
        prefix_key: str = "prefix",
        suffix_key: str = "suffix",
        max_concurrent: int = 10,
    ):
        if AsyncOpenAI is None:
            raise ImportError("Please install openai: pip install openai")

        # Normalize base_url to include /v1 if missing
        normalized_base_url = base_url.rstrip("/")
        if not normalized_base_url.endswith("/v1"):
            normalized_base_url = f"{normalized_base_url}/v1"

        logger.info(f"[AsyncOpenAIClient] Initializing with base_url={normalized_base_url}, model={model}, timeout={timeout_s}s, max_concurrent={max_concurrent}")
        
        self.client = AsyncOpenAI(api_key=api_key, base_url=normalized_base_url, timeout=timeout_s)
        self.base_url = normalized_base_url
        self.model = model
        self.max_retries = max_retries
        self.use_chat_for_fim = use_chat_for_fim
        self.prefix_key = prefix_key
        self.suffix_key = suffix_key
        
        # Concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent)
        logger.info(f"[AsyncOpenAIClient] Semaphore initialized with max_concurrent={max_concurrent}")

    async def _retry_call(self, fn, *args, **kwargs):
        """Exponential backoff retry"""
        for attempt in range(self.max_retries):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} failed: {e}")
                if attempt < self.max_retries - 1:
                    # Exponential backoff with jitter
                    delay = (2 ** attempt) + (0.1 * (attempt + 1))
                    await asyncio.sleep(delay)
                else:
                    raise

    async def _complete_async(
        self,
        prompt: str,
        *,
        max_tokens: int,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[List[str]] = None,
        logprobs: Optional[int] = None,
        stream: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Async normal completion request"""
        logger.debug(f"[_complete_async] prompt={prompt[:60]}..., max_tokens={max_tokens}, n={n}")
        async with self.semaphore:
            logger.debug(f"[_complete_async] Acquired semaphore, calling completions.create(model={self.model}, base_url={self.base_url})")
            async def _call():
                kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "n": n,
                    "stream": stream,
                }
                if stop:
                    kwargs["stop"] = stop
                if logprobs is not None:
                    kwargs["logprobs"] = logprobs
                if extra:
                    kwargs.update(extra)

                logger.debug(f"[_call] Sending POST to /v1/completions with kwargs: model={kwargs['model']}, prompt_len={len(kwargs['prompt'])}, max_tokens={kwargs['max_tokens']}")
                
                if stream:
                    texts = [""] * n
                    response = await self.client.completions.create(**kwargs)
                    async for chunk in response:
                        for choice in chunk.choices:
                            idx = choice.index
                            texts[idx] += choice.text or ""
                    logger.debug(f"[_call] Streaming complete, got {len(texts)} results")
                    return [{"text": t} for t in texts]
                else:
                    response = await self.client.completions.create(**kwargs)
                    results = []
                    for choice in response.choices:
                        item = {"text": choice.text}
                        if hasattr(choice, "logprobs") and choice.logprobs:
                            item["logprobs"] = choice.logprobs
                        results.append(item)
                    logger.debug(f"[_call] Got {len(results)} results from completions.create")
                    return results

            return await self._retry_call(_call)

    async def _complete_fim_async(
        self,
        prefix: str,
        suffix: str,
        *,
        max_tokens: int,
        temperature: float = 1.0,
        top_p: float = 1.0,
        n: int = 1,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Async FIM request"""
        async with self.semaphore:
            async def _call():
                if self.use_chat_for_fim:
                    # chat.completions with extra_body
                    messages = [{"role": "user", "content": ""}]
                    extra_body = {self.prefix_key: prefix, self.suffix_key: suffix}
                    kwargs: Dict[str, Any] = {
                        "model": self.model,
                        "messages": messages,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "n": n,
                        "stream": stream,
                        "extra_body": extra_body,
                    }
                    if stop:
                        kwargs["stop"] = stop
                    if extra:
                        kwargs["extra_body"].update(extra)

                    if stream:
                        texts = [""] * n
                        response = await self.client.chat.completions.create(**kwargs)
                        async for chunk in response:
                            for choice in chunk.choices:
                                idx = choice.index
                                delta = choice.delta.content or ""
                                texts[idx] += delta
                        return [{"text": t} for t in texts]
                    else:
                        response = await self.client.chat.completions.create(**kwargs)
                        return [{"text": choice.message.content or ""} for choice in response.choices]
                else:
                    # completions with suffix
                    kwargs: Dict[str, Any] = {
                        "model": self.model,
                        "prompt": prefix,
                        "suffix": suffix,
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "top_p": top_p,
                        "n": n,
                        "stream": stream,
                    }
                    if stop:
                        kwargs["stop"] = stop
                    if extra:
                        kwargs.update(extra)

                    if stream:
                        texts = [""] * n
                        response = await self.client.completions.create(**kwargs)
                        async for chunk in response:
                            for choice in chunk.choices:
                                idx = choice.index
                                texts[idx] += choice.text or ""
                        return [{"text": t} for t in texts]
                    else:
                        response = await self.client.completions.create(**kwargs)
                        return [{"text": choice.text} for choice in response.choices]

            return await self._retry_call(_call)

    # Sync wrappers for compatibility with base class
    def complete(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Sync wrapper for complete"""
        return asyncio.run(self._complete_async(*args, **kwargs))

    def complete_fim(self, *args, **kwargs) -> List[Dict[str, Any]]:
        """Sync wrapper for complete_fim"""
        return asyncio.run(self._complete_fim_async(*args, **kwargs))

    # Batch async methods for high concurrency
    async def complete_batch_async(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch completion with high concurrency.
        Returns list of results for each prompt.
        """
        tasks = [self._complete_async(prompt, **kwargs) for prompt in prompts]
        return await asyncio.gather(*tasks)

    async def complete_fim_batch_async(
        self,
        prefix_suffix_pairs: List[tuple[str, str]],
        **kwargs
    ) -> List[List[Dict[str, Any]]]:
        """
        Batch FIM completion with high concurrency.
        Returns list of results for each (prefix, suffix) pair.
        """
        tasks = [
            self._complete_fim_async(prefix, suffix, **kwargs)
            for prefix, suffix in prefix_suffix_pairs
        ]
        return await asyncio.gather(*tasks)

    def complete_batch(self, prompts: List[str], **kwargs) -> List[List[Dict[str, Any]]]:
        """Sync wrapper for batch completion"""
        return asyncio.run(self.complete_batch_async(prompts, **kwargs))

    def complete_fim_batch(
        self,
        prefix_suffix_pairs: List[tuple[str, str]],
        **kwargs
    ) -> List[List[Dict[str, Any]]]:
        """Sync wrapper for batch FIM completion"""
        return asyncio.run(self.complete_fim_batch_async(prefix_suffix_pairs, **kwargs))

