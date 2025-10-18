#!/usr/bin/env python3
"""
Convert rated function implementations to ChatML format for fine-tuning.

This script takes rated implementations (from the rating stage) and converts them
to ChatML format suitable for LLM fine-tuning. It:
- Removes hints from problem descriptions
- Extracts function signatures
- Removes docstrings from code bodies
- Filters by quality ratings
- Uses multiprocessing for efficient conversion

Usage:
    python scripts/datagen/convert_to_chatml.py --mode fim
    python scripts/datagen/convert_to_chatml.py --mode l2r
    python scripts/datagen/convert_to_chatml.py --input data/custom/ratings.jsonl --output data/custom/chatml.jsonl
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.datagen.postprocess.converter import ChatMLConverter
from evoselfcode.core import ConfigManager
from evoselfcode.utils.logger import LoggerManager


def main(
    mode: Optional[str] = None,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    config_path: Optional[Path] = None
):
    """Main conversion function.
    
    Args:
        mode: Generation mode ('fim' or 'l2r'). Uses paths from config if provided.
        input_path: Custom input path (overrides config)
        output_path: Custom output path (overrides config)
        config_path: Custom config path (default: configs/datagen/convert.yaml)
    """
    # Load config first
    if not config_path:
        config_path = PROJECT_ROOT / "configs" / "datagen" / "convert.yaml"
    
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)
    
    config = ConfigManager.from_file(config_path)
    paths_cfg = config.get_section("paths")
    
    # Setup logger with appropriate task name for log directory
    task_name = f"convert_{mode}" if mode else "convert"
    logger = LoggerManager.get_logger(
        name="convert_chatml",
        module="datagen",
        task=task_name
    )
    
    logger.info(f"Using config: {config_path}")
    
    # Determine paths
    if mode:
        # Use paths from config
        if not input_path:
            input_rel = paths_cfg.get("input", {}).get(mode)
            if not input_rel:
                logger.error(f"No input path configured for mode: {mode}")
                sys.exit(1)
            input_path = PROJECT_ROOT / input_rel
        
        if not output_path:
            output_rel = paths_cfg.get("output", {}).get(mode)
            if not output_rel:
                logger.error(f"No output path configured for mode: {mode}")
                sys.exit(1)
            output_path = PROJECT_ROOT / output_rel
        
        logger.info(f"Converting {mode.upper()} mode data to ChatML format")
    else:
        # Custom paths must be provided
        if not input_path or not output_path:
            logger.error("Either --mode or both --input and --output must be provided")
            sys.exit(1)
        logger.info(f"Converting custom data to ChatML format")
    
    # Check input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    
    # Create converter
    converter = ChatMLConverter.from_config_path(config_path, logger=logger)
    
    # Convert file
    stats = converter.convert_file(input_path, output_path)
    
    logger.info(f"✅ Conversion complete!")
    logger.info(f"Output saved to: {output_path}")
    
    # Show sample if output exists and has content
    if output_path.exists():
        import json
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                if first_line:
                    sample = json.loads(first_line)
                    logger.info("\n=== Sample ChatML Record ===")
                    logger.info(f"UID: {sample.get('uid')}")
                    logger.info(f"\nUser message:\n{sample['messages'][0]['content'][:300]}...")
                    logger.info(f"\nAssistant message:\n{sample['messages'][1]['content'][:200]}...")
        except Exception as e:
            logger.debug(f"Could not load sample: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Convert rated implementations to ChatML format (uses multiprocessing)"
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["fim", "l2r"],
        help="Generation mode (uses paths from config)"
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Custom input JSONL file path (overrides config)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Custom output JSONL file path (overrides config)"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Custom config file path (default: configs/datagen/convert.yaml)"
    )
    
    args = parser.parse_args()
    
    main(
        mode=args.mode,
        input_path=args.input,
        output_path=args.output,
        config_path=args.config
    )

