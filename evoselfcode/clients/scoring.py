from __future__ import annotations

import logging
import math
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base import ScoringClient

logger = logging.getLogger(__name__)


class OpenAIScoringClient(ScoringClient):
    """
    Scoring client based on OpenAI compatible interface.
    Prioritize using logprobs/echo capability to get log probabilities.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str = "EMPTY",
        model: str = "Qwen2.5-Coder-32B",
        timeout_s: int = 60,
    ):
        if OpenAI is None:
            raise ImportError("Please install openai: pip install openai")
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout_s)
        self.model = model

    def token_logprobs(self, text: str) -> List[float]:
        """
        Try to get log probability for each token via echo + logprobs.
        If service doesn't support it, return empty list.
        """
        try:
            response = self.client.completions.create(
                model=self.model,
                prompt=text,
                max_tokens=0,
                echo=True,
                logprobs=1,
            )
            if response.choices and response.choices[0].logprobs:
                return response.choices[0].logprobs.token_logprobs or []
        except Exception as e:
            logger.warning(f"Failed to get token logprobs: {e}")
        return []

    def perplexity(self, text: str) -> float:
        """
        Calculate perplexity: exp(-mean(log_probs))
        If logprobs unavailable, return -1.0 to indicate not available.
        """
        logprobs = self.token_logprobs(text)
        if not logprobs:
            logger.warning("No logprobs available, returning -1.0")
            return -1.0
        avg_logprob = sum(logprobs) / len(logprobs)
        return math.exp(-avg_logprob)

