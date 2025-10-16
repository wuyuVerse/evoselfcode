from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

from ..config import RunConfig
from ..io_utils import read_samples, write_jsonl
from ..constants import GENERATED_DIR, RAW_DIR

logger = logging.getLogger(__name__)


def _mock_generate(prompt: str, num_samples: int) -> List[Dict]:
	# Placeholder for real generation logic with HF Transformers
	return [
		{"prompt": prompt, "code": f"def auto_gen_{i}():\n    pass\n", "score": None}
		for i in range(num_samples)
	]


def cmd_generate(config_path: Path | None) -> None:
	run = RunConfig.from_file(config_path)
	num_samples = int(run.get("generation.num_samples_per_prompt", 4))
	input_path = Path(run.get("paths.raw_dir", str(RAW_DIR))) / "sample_train.jsonl"
	output_path = Path(run.get("paths.generated_dir", str(GENERATED_DIR))) / "candidates.jsonl"

	logger.info("Reading prompts from %s", input_path)
	samples = read_samples(input_path)

	logger.info("Generating %d samples per prompt...", num_samples)
	candidates: List[Dict] = []
	for s in samples:
		candidates.extend(_mock_generate(s.prompt, num_samples))

	logger.info("Writing candidates to %s", output_path)
	write_jsonl(output_path, candidates)
	logger.info("Done; total candidates: %d", len(candidates))


