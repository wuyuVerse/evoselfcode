from __future__ import annotations

import logging
from pathlib import Path

from ..config import RunConfig
from ..constants import PROCESSED_DIR

logger = logging.getLogger(__name__)


def cmd_train_d2c(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	train_path = Path(run.get("paths.processed_dir", str(PROCESSED_DIR))) / "train_d2c.jsonl"
	logger.info("[D2C] (stub) training on %s", train_path)
	# TODO: integrate HF Trainer/Accelerate here
	logger.info("[D2C] training complete (stub)")


