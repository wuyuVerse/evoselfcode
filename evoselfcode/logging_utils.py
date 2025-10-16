from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(log_dir: Optional[Path] = None, level: int = logging.INFO) -> None:
	handlers = [RichHandler(console=Console(), show_time=True, show_path=False)]
	if log_dir:
		log_dir.mkdir(parents=True, exist_ok=True)
		file_handler = logging.FileHandler(log_dir / "run.log", encoding="utf-8")
		file_handler.setLevel(level)
		handlers.append(file_handler)

	logging.basicConfig(
		level=level,
		format="%(asctime)s %(levelname)s %(name)s: %(message)s",
		handlers=handlers,
	)

