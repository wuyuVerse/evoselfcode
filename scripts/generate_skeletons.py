#!/usr/bin/env python3
"""
Script to generate Python function skeletons from algorithm problem descriptions.

Usage:
    python scripts/generate_skeletons.py --source fim
    python scripts/generate_skeletons.py --source l2r
    python scripts/generate_skeletons.py --source fim --num-samples 100
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.services.datagen_service import DataGenService
from evoselfcode.utils.logger import LoggerManager


async def main(source: str = "fim", num_samples: int = None):
    """Main function to run skeleton generation.

    Args:
        source (str): Source mode, either 'fim' or 'l2r'.
        num_samples (int, optional): Number of samples to process. None means all.
    """
    # Setup logger
    logger = LoggerManager.get_logger(
        name="generate_skeletons",
        module="scripts",
        task=f"skeleton_{source}"
    )
    
    logger.info(f"Starting function skeleton generation for source: {source.upper()}")
    if num_samples:
        logger.info(f"Limited to {num_samples} samples")
    
    # Determine config path
    config_path = PROJECT_ROOT / "configs" / "skeleton.yaml"
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Create service
    service = DataGenService.from_config_path(config_path, task=source, logger=logger)
    
    # Generate skeletons
    results = await service.generate_skeletons(
        source_mode=source,
        num_samples=num_samples
    )
    
    logger.info(f"✅ Generated {len(results)} unique function skeletons")
    
    # Show sample results
    if results:
        logger.info("\n=== Sample Results ===")
        for i, res in enumerate(results[:3], 1):
            logger.info(f"\n--- Skeleton {i} ---")
            logger.info(f"UID: {res['uid']}")
            logger.info(f"Function: {res['function_name']}")
            logger.info(f"Valid: {res['valid']}")
            logger.info(f"Code preview:\n{res['skeleton_code'][:300]}...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate function skeletons from problem descriptions")
    parser.add_argument(
        "--source",
        type=str,
        choices=["fim", "l2r"],
        required=True,
        help="Source mode: 'fim' or 'l2r'"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to process (default: all)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(source=args.source, num_samples=args.num_samples))
