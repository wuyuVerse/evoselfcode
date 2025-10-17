"""
Generate Quality Ratings for Function Implementations

This script generates quality ratings for function implementations using LLM evaluation.

Usage:
    python scripts/datagen/generate_ratings.py --source fim
    python scripts/datagen/generate_ratings.py --source l2r
    python scripts/datagen/generate_ratings.py --source fim --num-samples 100
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.services.datagen_service import DataGenService
from evoselfcode.utils.logger import LoggerManager


async def main(source: str = "fim", num_samples: int = None):
    """Main function to run rating generation.

    Args:
        source (str): Source mode, either 'fim' or 'l2r'.
        num_samples (int, optional): Number of samples to process. None means all.
    """
    # Determine config path
    config_path = PROJECT_ROOT / "configs" / "datagen" / "rating.yaml"
    
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)
    
    # Load config to get log level
    from evoselfcode.core import ConfigManager
    temp_config = ConfigManager.from_file(str(config_path))
    log_level_str = temp_config.get("logging.level", "INFO")
    log_level = getattr(logging, log_level_str, logging.INFO)
    
    # Setup logger with configured level
    logger = LoggerManager.get_logger(
        name="generate_ratings",
        module="datagen",
        task=f"rating_{source}",
        level=log_level
    )
    
    logger.info(f"Starting quality rating generation for source: {source.upper()}")
    logger.info(f"Log level: {log_level_str}")
    if num_samples:
        logger.info(f"Limited to {num_samples} samples")
    
    # Create service (config_path already validated above)
    service = DataGenService.from_config_path(str(config_path), logger=logger)
    
    try:
        # Generate ratings
        results = await service.generate_ratings(
            source_mode=source,
            num_samples=num_samples
        )
        
        # Display sample results
        logger.info("=== Sample Ratings ===")
        for res in results[:3]:
            logger.info(f"Function: {res['function_name']}")
            logger.info(f"  Problem Design: {res['ratings']['problem_design']}")
            logger.info(f"  Function Definition: {res['ratings']['function_definition']}")
            logger.info(f"  Correctness: {res['ratings']['correctness']}")
            logger.info(f"  Efficiency: {res['ratings']['efficiency']}")
            logger.info(f"  Readability: {res['ratings']['readability']}")
            logger.info(f"  Summary: {res['summary'][:100]}...")
            logger.info("")
        
        logger.info("=== Generation Complete ===")
        logger.info(f"Total ratings generated: {len(results)}")
        
    except Exception as e:
        logger.error(f"Error during rating generation: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate quality ratings for function implementations"
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["fim", "l2r"],
        default="fim",
        help="Source mode: fim or l2r"
    )
    parser.add_argument(
        "--num-samples",
        type=int,
        default=None,
        help="Number of samples to process (default: all)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(main(source=args.source, num_samples=args.num_samples))

