#!/usr/bin/env python3
"""
Script to generate algorithm problem descriptions using ProblemGen.

Supports both FIM (Fill-in-the-Middle) and L2R (Left-to-Right) generation modes.

Usage:
    python scripts/datagen/generate_problems.py --mode fim
    python scripts/datagen/generate_problems.py --mode l2r
    python scripts/datagen/generate_problems.py --mode fim --num-samples 1000
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.services.datagen_service import DataGenService
from evoselfcode.utils.logger import LoggerManager


async def main(mode: str = "fim", num_samples: int = None):
    """Main function to run problem generation.

    Args:
        mode (str): Generation mode, either 'fim' or 'l2r'.
        num_samples (int, optional): Number of samples to generate. None means use config default.
    """
    # Setup logger
    logger = LoggerManager.get_logger(
        name="generate_problems",
        module="datagen",
        task=f"problems_{mode}"
    )
    
    logger.info(f"Starting problem generation for mode: {mode.upper()}")
    if num_samples:
        logger.info(f"Target samples: {num_samples}")
    
    # Determine config path based on mode
    config_path = PROJECT_ROOT / "configs" / "datagen" / f"{mode}.yaml"
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Create service
    service = DataGenService.from_config_path(config_path, task=mode, logger=logger)
    
    # Generate problems
    results = await service.generate_problems(
        mode=mode.upper(),
        num_samples=num_samples
    )
    
    logger.info(f"✅ Generated {len(results)} unique algorithm problems")
    
    # Show sample results
    if results:
        logger.info("\n=== Sample Problems ===")
        for i, res in enumerate(results[:3], 1):
            logger.info(f"\n--- Problem {i} ---")
            logger.info(f"UID: {res['uid']}")
            logger.info(f"Preview: {res['problem_description'][:200]}...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate algorithm problem descriptions")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["fim", "l2r"],
        required=True,
        help="Generation mode: 'fim' or 'l2r'"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to generate (default: from config)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(mode=args.mode, num_samples=args.num_samples))
