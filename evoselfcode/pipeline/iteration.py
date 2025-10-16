from __future__ import annotations

import logging
from pathlib import Path

from ..config import RunConfig

logger = logging.getLogger(__name__)


def cmd_iterate(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	# Outline of the loop, to be implemented
	logger.info("[Iter] starting iterative self-training loop (stub)")
	# 1) generate -> 2) score -> 3) filter -> 4) update datasets -> 5) train
	logger.info("[Iter] completed one iteration (stub)")


