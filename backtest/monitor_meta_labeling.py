#!/usr/bin/env python3
"""
Monitor Meta-Labeling Performance

Tracks key metrics for meta-labeling in production:
- Signal reduction rate
- Win rate improvement
- Return improvement
- Model performance over time
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from meta_labeling_filter import MetaLabelingFilter
from statistical_analysis import StatisticalAnalyzer

def load_portfolio_results(portfolio_file: Path) -> dict:
    """Load and analyze portfolio results"""
    # This would need to be implemented based on actual portfolio format
    # For now, return placeholder
    return {
        'n_signals': 0,
        'win_rate': 0,
        'avg_return': 0,
        'sharpe_ratio': 0
    }

def compare_with_baseline(filtered_results: pd.DataFrame, baseline_results: pd.DataFrame) -> dict:
    """Compare filtered results with baseline"""
    filtered_analyzer = StatisticalAnalyzer(filtered_results)
    baseline_analyzer = StatisticalAnalyzer(baseline_results)
    
    filtered_metrics = filtered_analyzer.calculate_performance_metrics()
    baseline_metrics = baseline_analyzer.calculate_performance_metrics()
    
    comparison = {
        'baseline': baseline_metrics,
        'filtered': filtered_metrics,
        'improvements': {
            'signal_reduction_pct': (1 - filtered_metrics.get('n_signals', 0) / baseline_metrics.get('n_signals', 1)) * 100,
            'win_rate_improvement_pp': (filtered_metrics.get('win_rate', 0) - baseline_metrics.get('win_rate', 0)) * 100,
            'avg_return_improvement_pct': ((filtered_metrics.get('avg_return', 0) - baseline_metrics.get('avg_return', 0)) / abs(baseline_metrics.get('avg_return', 1)) * 100) if baseline_metrics.get('avg_return', 0) != 0 else 0,
            'sharpe_improvement': filtered_metrics.get('sharpe_ratio', 0) - baseline_metrics.get('sharpe_ratio', 0)
        }
    }
    
    return comparison

def generate_monitoring_report(comparison: dict, output_file: Path):
    """Generate monitoring report"""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Meta-Labeling Performance Monitoring Report\n\n")
        f.write(f"**Report Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        improvements = comparison['improvements']
        f.write(f"- **Signal Reduction**: {improvements['signal_reduction_pct']:.1f}%\n")
        f.write(f"- **Win Rate Improvement**: {improvements['win_rate_improvement_pp']:+.1f} percentage points\n")
        f.write(f"- **Average Return Improvement**: {improvements['avg_return_improvement_pct']:+.1f}%\n")
        f.write(f"- **Sharpe Ratio Improvement**: {improvements['sharpe_improvement']:+.2f}\n\n")
        
        # Detailed Metrics
        f.write("## Detailed Metrics\n\n")
        f.write("### Baseline (Without Meta-Labeling)\n\n")
        baseline = comparison['baseline']
        f.write(f"- Total Signals: {baseline.get('n_signals', 0):,}\n")
        f.write(f"- Win Rate: {baseline.get('win_rate', 0)*100:.1f}%\n")
        f.write(f"- Average Return: {baseline.get('avg_return', 0):.2f}%\n")
        f.write(f"- Sharpe Ratio: {baseline.get('sharpe_ratio', 0):.2f}\n\n")
        
        f.write("### Filtered (With Meta-Labeling)\n\n")
        filtered = comparison['filtered']
        f.write(f"- Total Signals: {filtered.get('n_signals', 0):,}\n")
        f.write(f"- Win Rate: {filtered.get('win_rate', 0)*100:.1f}%\n")
        f.write(f"- Average Return: {filtered.get('avg_return', 0):.2f}%\n")
        f.write(f"- Sharpe Ratio: {filtered.get('sharpe_ratio', 0):.2f}\n\n")
        
        # Status
        f.write("## Status Assessment\n\n")
        if improvements['win_rate_improvement_pp'] > 5 and improvements['sharpe_improvement'] > 0.1:
            f.write("✅ **EXCELLENT**: Meta-labeling showing significant improvements\n")
        elif improvements['win_rate_improvement_pp'] > 0 and improvements['sharpe_improvement'] > 0:
            f.write("✅ **GOOD**: Meta-labeling showing improvements\n")
        elif improvements['win_rate_improvement_pp'] > 0:
            f.write("⚠️ **MARGINAL**: Win rate improved but Sharpe ratio did not\n")
        else:
            f.write("⚠️ **REVIEW NEEDED**: Meta-labeling not showing expected improvements\n")
            f.write("   Consider retraining model or reviewing feature set.\n")
    
    print(f"Monitoring report saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Monitor meta-labeling performance')
    parser.add_argument('--baseline-results', type=str, required=True,
                       help='Path to baseline results CSV (without meta-labeling)')
    parser.add_argument('--filtered-results', type=str, required=True,
                       help='Path to filtered results CSV (with meta-labeling)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output report file (default: backtest/monitoring/report_YYYYMMDD.md)')
    
    args = parser.parse_args()
    
    print("="*80)
    print("META-LABELING PERFORMANCE MONITORING")
    print("="*80)
    
    # Load results
    print("\nLoading results...")
    baseline_df = pd.read_csv(args.baseline_results)
    filtered_df = pd.read_csv(args.filtered_results)
    
    print(f"  Baseline: {len(baseline_df)} signals")
    print(f"  Filtered: {len(filtered_df)} signals")
    
    # Compare
    print("\nComparing performance...")
    comparison = compare_with_baseline(filtered_df, baseline_df)
    
    # Generate report
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = backtest_dir / "monitoring" / f"report_{datetime.now().strftime('%Y%m%d')}.md"
    
    generate_monitoring_report(comparison, output_file)
    
    # Print summary
    print("\n" + "="*80)
    print("MONITORING SUMMARY")
    print("="*80)
    improvements = comparison['improvements']
    print(f"\nSignal Reduction: {improvements['signal_reduction_pct']:.1f}%")
    print(f"Win Rate Improvement: {improvements['win_rate_improvement_pp']:+.1f} pp")
    print(f"Avg Return Improvement: {improvements['avg_return_improvement_pct']:+.1f}%")
    print(f"Sharpe Improvement: {improvements['sharpe_improvement']:+.2f}")
    
    return 0

if __name__ == "__main__":
    exit(main())

