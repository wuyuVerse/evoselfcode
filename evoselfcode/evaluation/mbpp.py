from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def cmd_eval(ckpt: Path, config_path: Path | None) -> None:
	logger.info("[MBPP] evaluating checkpoint %s (stub)", ckpt)
	logger.info("[MBPP] pass@1=0.0 (stub)")


