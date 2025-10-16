from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from ..config import RunConfig
from ..constants import GENERATED_DIR
from ..io_utils import read_jsonl, write_jsonl

logger = logging.getLogger(__name__)


def cmd_filter(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	keep_ratio = float(run.get("filtering.keep_ratio", 0.5))
	min_code_len = int(run.get("filtering.min_code_len", 16))
	scored_path = Path(run.get("paths.generated_dir", str(GENERATED_DIR))) / "scored.jsonl"
	filtered_path = Path(run.get("paths.generated_dir", str(GENERATED_DIR))) / "filtered.jsonl"

	items: List[Dict] = list(read_jsonl(scored_path))
	items = [x for x in items if len(x.get("code", "")) >= min_code_len]
	items.sort(key=lambda x: x.get("ppl", 1e9))
	n_keep = max(1, int(len(items) * keep_ratio))
	kept = items[:n_keep]

	logger.info("Filtered %d -> %d", len(items), len(kept))
	write_jsonl(filtered_path, kept)
	logger.info("Wrote %s", filtered_path)


