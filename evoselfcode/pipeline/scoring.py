from __future__ import annotations

import logging
from math import log
from pathlib import Path
from typing import Dict, Iterable, List

from ..config import RunConfig
from ..constants import GENERATED_DIR
from ..io_utils import read_jsonl, write_jsonl

logger = logging.getLogger(__name__)


def _mock_perplexity(code: str) -> float:
	# Placeholder scoring; replace with LM perplexity
	length = max(1, len(code))
	return 100.0 / (1.0 + log(length))


def cmd_score(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	candidates_path = Path(run.get("paths.generated_dir", str(GENERATED_DIR))) / "candidates.jsonl"
	scored_path = Path(run.get("paths.generated_dir", str(GENERATED_DIR))) / "scored.jsonl"

	logger.info("Scoring candidates from %s", candidates_path)
	items: List[Dict] = []
	for obj in read_jsonl(candidates_path):
		obj["ppl"] = _mock_perplexity(obj.get("code", ""))
		items.append(obj)

	logger.info("Writing scored candidates to %s", scored_path)
	write_jsonl(scored_path, items)
	logger.info("Done; total scored: %d", len(items))


