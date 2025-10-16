#!/usr/bin/env python
"""
Script to generate function names using FIM or L2R mode
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from evoselfcode.services.datagen_service import DataGenService
from evoselfcode.utils.logger import setup_task_logger, LoggerManager


def main():
    parser = argparse.ArgumentParser(
        description="Generate function names using FIM or L2R mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate using FIM mode
  python scripts/generate_funcnames.py --mode fim
  
  # Generate using L2R mode
  python scripts/generate_funcnames.py --mode l2r
  
  # Use custom config
  python scripts/generate_funcnames.py --mode fim --config my_config.yaml
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["fim", "l2r"],
        required=True,
        help="Generation mode: 'fim' (Fill-in-Middle) or 'l2r' (Left-to-Right)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to config file (default: configs/datagen/{mode}.yaml)"
    )
    
    args = parser.parse_args()
    
    # Determine config path
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = project_root / f"configs/datagen/{args.mode}.yaml"
    
    # Check if config exists
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    # Setup logging
    log_dir = project_root / "logs"
    LoggerManager.setup_base_dir(log_dir)
    logger = setup_task_logger("datagen", args.mode)
    
    mode_name = "Fill-in-Middle (FIM)" if args.mode == "fim" else "Left-to-Right (L2R)"
    logger.info("=" * 60)
    logger.info(f"Function Name Generation - {mode_name}")
    logger.info("=" * 60)
    logger.info(f"Config: {config_path}")
    logger.info(f"Mode: {args.mode.upper()}")
    
    # Run generation
    try:
        asyncio.run(run_generation(config_path, args.mode, logger))
    except Exception as e:
        logger.exception(f"Error during generation: {e}")
        sys.exit(1)
    
    # Print summary
    logger.info("")
    logger.info("=" * 60)
    logger.info(f"{mode_name} Generation completed!")
    logger.info("=" * 60)
    
    out_dir = project_root / f"data/generated/names/{args.mode}"
    logger.info(f"Output directory: {out_dir}")
    
    if args.mode == "fim":
        logger.info("Note: FIM mode uses special tokens for fill-in-middle completion")
    else:
        logger.info("Note: L2R mode uses standard left-to-right completion")
    
    # Close loggers
    LoggerManager.close_all()


async def run_generation(config_path: Path, mode: str, logger):
    """Run the generation process"""
    import json
    
    # Create service
    service = DataGenService.from_config_path(config_path, task=mode, logger=logger)
    
    # Generate function names
    mode_upper = "FIM" if mode == "fim" else "L2R"
    results = await service.generate_function_names(mode=mode_upper)
    
    # Save results
    out_dir = project_root / f"data/generated/names/{mode}"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = out_dir / f"{mode}_results.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    
    logger.info(f"Saved {len(results)} results to: {output_file}")


if __name__ == "__main__":
    main()
