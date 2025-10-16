from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from ...services import DataGenService
from ...io_utils import write_jsonl

logger = logging.getLogger(__name__)


def run_funcname_generation_ab(config_path: Optional[Path] = None) -> None:
    """
    Run A/B test for function name generation: FIM vs L2R.
    Output results to data/generated/names/
    
    This is a simplified entry point using the DataGenService.
    """
    if config_path is None:
        config_path = Path("configs/datagen.yaml")
    
    logger.info(f"Loading configuration from: {config_path}")
    
    # Create service (auto-loads and merges model.yaml)
    service = DataGenService.from_config_path(config_path)
    
    # Run A/B test
    async def run():
        fim_candidates, l2r_candidates = await service.generate_function_names_ab_test()
        return fim_candidates, l2r_candidates
    
    fim_candidates, l2r_candidates = asyncio.run(run())
    
    # Save results
    out_dir = Path(service.config.get("io.out_names_dir", "data/generated/names"))
    out_dir.mkdir(parents=True, exist_ok=True)
    
    fim_output = out_dir / "fim_raw.jsonl"
    l2r_output = out_dir / "l2r_raw.jsonl"
    combined_output = out_dir / "combined_raw.jsonl"
    
    write_jsonl(fim_output, fim_candidates)
    write_jsonl(l2r_output, l2r_candidates)
    write_jsonl(combined_output, fim_candidates + l2r_candidates)
    
    logger.info(f"Saved results:")
    logger.info(f"  FIM: {fim_output}")
    logger.info(f"  L2R: {l2r_output}")
    logger.info(f"  Combined: {combined_output}")
