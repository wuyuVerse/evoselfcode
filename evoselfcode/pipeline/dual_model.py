from __future__ import annotations

import logging
from pathlib import Path

from ..config import RunConfig
from ..constants import PROCESSED_DIR

logger = logging.getLogger(__name__)


def cmd_train_c2d(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	train_path = Path(run.get("paths.processed_dir", str(PROCESSED_DIR))) / "train_c2d.jsonl"
	logger.info("[C2D] (stub) training on %s", train_path)
	logger.info("[C2D] training complete (stub)")


