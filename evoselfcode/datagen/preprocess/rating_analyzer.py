"""
Rating Analysis and Visualization Module

Analyzes quality ratings from FIM and L2R generation modes and produces:
- Radar charts comparing average scores across 5 dimensions
- Distribution histograms for each dimension
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


class RatingAnalyzer:
    """Analyzes and visualizes code quality ratings."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the rating analyzer.

        Args:
            logger: Optional logger instance. If None, creates a default logger.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Try to set a font that supports Chinese characters (for better labels)
        try:
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
        except Exception:
            pass

    def load_ratings(self, ratings_path: Path) -> List[Dict]:
        """
        Load ratings from a JSONL file.

        Args:
            ratings_path: Path to the ratings.jsonl file

        Returns:
            List of rating dictionaries
        """
        ratings = []
        
        if not ratings_path.exists():
            self.logger.warning(f"Ratings file not found: {ratings_path}")
            return ratings
        
        with open(ratings_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        if 'ratings' in data:
                            ratings.append(data)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse line: {e}")
        
        self.logger.info(f"Loaded {len(ratings)} ratings from {ratings_path}")
        return ratings

    def extract_scores(self, ratings: List[Dict]) -> Dict[str, List[float]]:
        """
        Extract scores for each dimension from ratings.

        Args:
            ratings: List of rating dictionaries

        Returns:
            Dictionary mapping dimension names to lists of scores
        """
        dimensions = {
            'problem_design': [],
            'function_definition': [],
            'correctness': [],
            'efficiency': [],
            'readability': []
        }
        
        for rating in ratings:
            rating_scores = rating.get('ratings', {})
            for dim in dimensions:
                score = rating_scores.get(dim)
                if score is not None and 1 <= score <= 5:
                    dimensions[dim].append(float(score))
        
        return dimensions

    def compute_statistics(self, scores: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Compute statistics for each dimension.

        Args:
            scores: Dictionary mapping dimension names to score lists

        Returns:
            Dictionary with mean, median, std for each dimension
        """
        stats = {}
        
        for dim, values in scores.items():
            if values:
                stats[dim] = {
                    'mean': float(np.mean(values)),
                    'median': float(np.median(values)),
                    'std': float(np.std(values)),
                    'count': len(values)
                }
            else:
                stats[dim] = {
                    'mean': 0.0,
                    'median': 0.0,
                    'std': 0.0,
                    'count': 0
                }
        
        return stats

    def plot_radar_chart(
        self,
        fim_scores: Dict[str, List[float]],
        l2r_scores: Dict[str, List[float]],
        output_path: Path
    ):
        """
        Create a radar chart comparing FIM and L2R average scores.

        Args:
            fim_scores: FIM dimension scores
            l2r_scores: L2R dimension scores
            output_path: Where to save the chart
        """
        # Dimension labels (short names for readability)
        labels = [
            'Problem\nDesign',
            'Function\nDefinition',
            'Correctness',
            'Efficiency',
            'Readability'
        ]
        
        dimensions = ['problem_design', 'function_definition', 'correctness', 'efficiency', 'readability']
        
        # Compute average scores
        fim_means = [np.mean(fim_scores[dim]) if fim_scores[dim] else 0 for dim in dimensions]
        l2r_means = [np.mean(l2r_scores[dim]) if l2r_scores[dim] else 0 for dim in dimensions]
        
        # Number of variables
        num_vars = len(labels)
        
        # Compute angle for each axis
        angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
        
        # Close the plot
        fim_means += fim_means[:1]
        l2r_means += l2r_means[:1]
        angles += angles[:1]
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        # Plot data
        ax.plot(angles, fim_means, 'o-', linewidth=2, label='FIM', color='#2E86AB')
        ax.fill(angles, fim_means, alpha=0.25, color='#2E86AB')
        
        ax.plot(angles, l2r_means, 'o-', linewidth=2, label='L2R', color='#A23B72')
        ax.fill(angles, l2r_means, alpha=0.25, color='#A23B72')
        
        # Fix axis to go from 0 to 5
        ax.set_ylim(0, 5)
        
        # Add labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, size=11)
        
        # Add gridlines
        ax.set_yticks([1, 2, 3, 4, 5])
        ax.set_yticklabels(['1', '2', '3', '4', '5'], size=9)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Add legend
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=12)
        
        # Add title
        plt.title('Code Quality Comparison: FIM vs L2R\n(5-Dimension Radar Chart)', 
                  size=16, weight='bold', pad=20)
        
        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved radar chart to {output_path}")

    def plot_distribution_histograms(
        self,
        fim_scores: Dict[str, List[float]],
        l2r_scores: Dict[str, List[float]],
        output_path: Path
    ):
        """
        Create distribution histograms for each dimension.

        Args:
            fim_scores: FIM dimension scores
            l2r_scores: L2R dimension scores
            output_path: Where to save the chart
        """
        dimensions = ['problem_design', 'function_definition', 'correctness', 'efficiency', 'readability']
        dimension_titles = [
            'Problem Design Quality',
            'Function Definition & Naming',
            'Algorithmic Correctness',
            'Algorithmic Efficiency',
            'Code Readability & Structure'
        ]
        
        # Create subplots (2 rows x 3 columns, but we only use 5)
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        axes = axes.flatten()
        
        # Bins for histogram (1, 2, 3, 4, 5)
        bins = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        
        for idx, (dim, title) in enumerate(zip(dimensions, dimension_titles)):
            ax = axes[idx]
            
            fim_data = fim_scores[dim]
            l2r_data = l2r_scores[dim]
            
            # Plot histograms
            ax.hist(fim_data, bins=bins, alpha=0.6, label='FIM', color='#2E86AB', edgecolor='black')
            ax.hist(l2r_data, bins=bins, alpha=0.6, label='L2R', color='#A23B72', edgecolor='black')
            
            # Add mean lines
            if fim_data:
                fim_mean = np.mean(fim_data)
                ax.axvline(fim_mean, color='#2E86AB', linestyle='--', linewidth=2, 
                          label=f'FIM Mean: {fim_mean:.2f}')
            
            if l2r_data:
                l2r_mean = np.mean(l2r_data)
                ax.axvline(l2r_mean, color='#A23B72', linestyle='--', linewidth=2,
                          label=f'L2R Mean: {l2r_mean:.2f}')
            
            # Styling
            ax.set_xlabel('Score', fontsize=11)
            ax.set_ylabel('Frequency', fontsize=11)
            ax.set_title(title, fontsize=12, weight='bold')
            ax.set_xticks([1, 2, 3, 4, 5])
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)
        
        # Hide the 6th subplot (we only have 5 dimensions)
        axes[5].axis('off')
        
        # Overall title
        fig.suptitle('Score Distribution by Dimension: FIM vs L2R', 
                     fontsize=16, weight='bold', y=0.995)
        
        # Save
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Saved distribution histograms to {output_path}")

    def generate_statistics_report(
        self,
        fim_scores: Dict[str, List[float]],
        l2r_scores: Dict[str, List[float]],
        output_path: Path
    ):
        """
        Generate a text report with detailed statistics.

        Args:
            fim_scores: FIM dimension scores
            l2r_scores: L2R dimension scores
            output_path: Where to save the report
        """
        fim_stats = self.compute_statistics(fim_scores)
        l2r_stats = self.compute_statistics(l2r_scores)
        
        report_lines = [
            "=" * 80,
            "CODE QUALITY RATING STATISTICS REPORT",
            "=" * 80,
            "",
            "## Overall Summary",
            "",
            f"FIM Total Samples: {fim_stats['problem_design']['count']}",
            f"L2R Total Samples: {l2r_stats['problem_design']['count']}",
            "",
            "=" * 80,
            "## Dimension-wise Statistics",
            "=" * 80,
            ""
        ]
        
        dimensions = ['problem_design', 'function_definition', 'correctness', 'efficiency', 'readability']
        dimension_names = [
            'Problem Design Quality',
            'Function Definition & Naming',
            'Algorithmic Correctness',
            'Algorithmic Efficiency',
            'Code Readability & Structure'
        ]
        
        for dim, name in zip(dimensions, dimension_names):
            report_lines.extend([
                f"### {name}",
                "",
                "FIM:",
                f"  Mean:   {fim_stats[dim]['mean']:.3f}",
                f"  Median: {fim_stats[dim]['median']:.3f}",
                f"  Std:    {fim_stats[dim]['std']:.3f}",
                f"  Count:  {fim_stats[dim]['count']}",
                "",
                "L2R:",
                f"  Mean:   {l2r_stats[dim]['mean']:.3f}",
                f"  Median: {l2r_stats[dim]['median']:.3f}",
                f"  Std:    {l2r_stats[dim]['std']:.3f}",
                f"  Count:  {l2r_stats[dim]['count']}",
                "",
                f"Difference (L2R - FIM): {l2r_stats[dim]['mean'] - fim_stats[dim]['mean']:+.3f}",
                "",
                "-" * 80,
                ""
            ])
        
        # Overall averages
        fim_overall = np.mean([fim_stats[dim]['mean'] for dim in dimensions])
        l2r_overall = np.mean([l2r_stats[dim]['mean'] for dim in dimensions])
        
        report_lines.extend([
            "=" * 80,
            "## Overall Average Across All Dimensions",
            "=" * 80,
            "",
            f"FIM Overall Average: {fim_overall:.3f}",
            f"L2R Overall Average: {l2r_overall:.3f}",
            f"Difference (L2R - FIM): {l2r_overall - fim_overall:+.3f}",
            "",
            "=" * 80
        ])
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        self.logger.info(f"Saved statistics report to {output_path}")
        
        # Also log to console
        self.logger.info("\n" + "\n".join(report_lines))

    def analyze_and_visualize(
        self,
        fim_ratings_path: Path,
        l2r_ratings_path: Path,
        output_dir: Path
    ):
        """
        Main entry point: load ratings, compute stats, and generate visualizations.

        Args:
            fim_ratings_path: Path to FIM ratings.jsonl
            l2r_ratings_path: Path to L2R ratings.jsonl
            output_dir: Directory to save outputs
        """
        self.logger.info("=" * 60)
        self.logger.info("Rating Analysis and Visualization")
        self.logger.info("=" * 60)
        
        # Load ratings
        self.logger.info("Loading ratings...")
        fim_ratings = self.load_ratings(fim_ratings_path)
        l2r_ratings = self.load_ratings(l2r_ratings_path)
        
        if not fim_ratings and not l2r_ratings:
            self.logger.error("No ratings loaded. Exiting.")
            return
        
        # Extract scores
        self.logger.info("Extracting scores...")
        fim_scores = self.extract_scores(fim_ratings)
        l2r_scores = self.extract_scores(l2r_ratings)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate visualizations
        self.logger.info("Generating radar chart...")
        radar_path = output_dir / "radar_chart.png"
        self.plot_radar_chart(fim_scores, l2r_scores, radar_path)
        
        self.logger.info("Generating distribution histograms...")
        dist_path = output_dir / "distribution_histograms.png"
        self.plot_distribution_histograms(fim_scores, l2r_scores, dist_path)
        
        self.logger.info("Generating statistics report...")
        stats_path = output_dir / "statistics_report.txt"
        self.generate_statistics_report(fim_scores, l2r_scores, stats_path)
        
        self.logger.info("=" * 60)
        self.logger.info("✅ Analysis complete!")
        self.logger.info(f"   Outputs saved to: {output_dir}")
        self.logger.info(f"   - {radar_path.name}")
        self.logger.info(f"   - {dist_path.name}")
        self.logger.info(f"   - {stats_path.name}")
        self.logger.info("=" * 60)

