#!/usr/bin/env python3
"""
Rating Analysis Script

Analyzes and visualizes code quality ratings from FIM and L2R generation modes.
Generates radar charts, distribution histograms, and statistical reports.

Usage:
    python scripts/datagen/analyze_ratings.py
    python scripts/datagen/analyze_ratings.py --fim-path <path> --l2r-path <path>
    python scripts/datagen/analyze_ratings.py --output-dir <path>
"""

import argparse
import logging
import sys
from pathlib import Path

# Ensure project root is in path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evoselfcode.datagen.preprocess.rating_analyzer import RatingAnalyzer
from evoselfcode.utils.logger import LoggerManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze and visualize code quality ratings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default paths
  python scripts/datagen/analyze_ratings.py

  # Custom input paths
  python scripts/datagen/analyze_ratings.py \\
    --fim-path data/generated/func_ratings/fim/ratings.jsonl \\
    --l2r-path data/generated/func_ratings/l2r/ratings.jsonl

  # Custom output directory
  python scripts/datagen/analyze_ratings.py \\
    --output-dir results/rating_analysis
        """
    )
    
    parser.add_argument(
        '--fim-path',
        type=str,
        default='data/generated/func_ratings/fim/ratings.jsonl',
        help='Path to FIM ratings.jsonl (default: data/generated/func_ratings/fim/ratings.jsonl)'
    )
    
    parser.add_argument(
        '--l2r-path',
        type=str,
        default='data/generated/func_ratings/l2r/ratings.jsonl',
        help='Path to L2R ratings.jsonl (default: data/generated/func_ratings/l2r/ratings.jsonl)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/analysis/rating_comparison',
        help='Output directory for charts and reports (default: data/analysis/rating_comparison)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup paths
    fim_path = PROJECT_ROOT / args.fim_path
    l2r_path = PROJECT_ROOT / args.l2r_path
    output_dir = PROJECT_ROOT / args.output_dir
    
    # Setup logger
    logger = LoggerManager.get_logger(
        name="analyze_ratings",
        module="datagen",
        task="rating_analysis",
        level=getattr(logging, args.log_level)
    )
    
    # Log configuration
    logger.info("=" * 60)
    logger.info("Rating Analysis Configuration")
    logger.info("=" * 60)
    logger.info(f"FIM ratings path: {fim_path}")
    logger.info(f"L2R ratings path: {l2r_path}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Log level: {args.log_level}")
    logger.info("=" * 60)
    
    # Check if input files exist
    if not fim_path.exists():
        logger.warning(f"FIM ratings file not found: {fim_path}")
    
    if not l2r_path.exists():
        logger.warning(f"L2R ratings file not found: {l2r_path}")
    
    if not fim_path.exists() and not l2r_path.exists():
        logger.error("No rating files found. Please generate ratings first.")
        logger.error("  Run: python scripts/datagen/generate_ratings.py --source fim")
        logger.error("  Run: python scripts/datagen/generate_ratings.py --source l2r")
        return 1
    
    # Create analyzer
    analyzer = RatingAnalyzer(logger=logger)
    
    try:
        # Run analysis
        analyzer.analyze_and_visualize(
            fim_ratings_path=fim_path,
            l2r_ratings_path=l2r_path,
            output_dir=output_dir
        )
        
        logger.info("\n✅ Analysis completed successfully!")
        logger.info(f"\nView results at: {output_dir}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

