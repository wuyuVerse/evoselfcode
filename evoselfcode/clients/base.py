from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CompletionClient(ABC):
    """Abstract interface: Code generation client"""

    @abstractmethod
    def complete(
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
        """
        Complete generation request.

        Return format: [{"text": str, "logprobs": [...], "tokens": [...]}]
        Actual fields vary by service, guaranteed by concrete implementation.
        """
        pass

    @abstractmethod
    def complete_fim(
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
        """
        FIM (Fill-in-the-Middle) generation request.

        Return format same as complete().
        """
        pass


class ScoringClient(ABC):
    """Abstract interface: Model scoring client"""

    @abstractmethod
    def perplexity(self, text: str) -> float:
        """Calculate text perplexity"""
        pass

    @abstractmethod
    def token_logprobs(self, text: str) -> List[float]:
        """Return list of log probabilities for each token"""
        pass

