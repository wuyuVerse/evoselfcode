from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
	result = dict(base)
	for key, value in override.items():
		if (
			key in result
			and isinstance(result[key], dict)
			and isinstance(value, dict)
		):
			result[key] = _deep_merge_dict(result[key], value)
		else:
			result[key] = value
	return result


def load_yaml(path: Path) -> Dict[str, Any]:
	with open(path, "r", encoding="utf-8") as f:
		return yaml.safe_load(f) or {}


def load_config(config_path: Optional[Path]) -> Dict[str, Any]:
	"""Load configuration from a YAML file (no base config merging)"""
	if config_path is None:
		return {}
	return load_yaml(config_path)


@dataclass
class RunConfig:
	config: Dict[str, Any]
	config_path: Optional[Path] = None

	@classmethod
	def from_file(cls, config_path: Optional[str | Path]) -> "RunConfig":
		path_obj = Path(config_path) if config_path else None
		cfg = load_config(path_obj)
		return cls(config=cfg, config_path=path_obj)

	def get(self, dotted_key: str, default: Any = None) -> Any:
		current: Any = self.config
		for part in dotted_key.split("."):
			if not isinstance(current, dict) or part not in current:
				return default
			current = current[part]
		return current

