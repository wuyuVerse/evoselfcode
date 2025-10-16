from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


def ensure_dir(path: Path) -> None:
	path.mkdir(parents=True, exist_ok=True)


def read_jsonl(path: Path) -> Iterator[Dict]:
	with open(path, "r", encoding="utf-8") as f:
		for line in f:
			line = line.strip()
			if not line:
				continue
			yield json.loads(line)


def write_jsonl(path: Path, records: Iterable[Dict]) -> None:
	ensure_dir(path.parent)
	with open(path, "w", encoding="utf-8") as f:
		for rec in records:
			f.write(json.dumps(rec, ensure_ascii=False) + "\n")


@dataclass
class Sample:
	prompt: str
	code: str
	meta: Optional[Dict] = None


def normalize_record(obj: Dict) -> Sample:
	prompt = obj.get("prompt") or obj.get("description") or obj.get("docstring") or ""
	code = obj.get("code") or obj.get("solution") or ""
	meta_keys = [k for k in obj.keys() if k not in {"prompt", "description", "docstring", "code", "solution"}]
	meta = {k: obj[k] for k in meta_keys}
	return Sample(prompt=prompt, code=code, meta=meta or None)


def read_samples(path: Path) -> List[Sample]:
	return [normalize_record(r) for r in read_jsonl(path)]

