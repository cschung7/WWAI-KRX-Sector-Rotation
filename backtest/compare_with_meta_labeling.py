#!/usr/bin/env python3
"""
Compare Backtest Performance: With vs Without Meta-Labeling

Runs backtest twice (with and without meta-labeling) and compares results.
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, REPORTS_DIR

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from backtest_engine import BacktestEngine
from statistical_analysis import StatisticalAnalyzer

def compare_results(baseline_df: pd.DataFrame, meta_df: pd.DataFrame) -> pd.DataFrame:
    """Compare baseline vs meta-labeling results"""
    print("\n" + "="*80)
    print("COMPARISON: Baseline vs Meta-Labeling")
    print("="*80)
    
    # Calculate metrics for both
    baseline_analyzer = StatisticalAnalyzer(baseline_df)
    meta_analyzer = StatisticalAnalyzer(meta_df)
    
    baseline_metrics = baseline_analyzer.calculate_performance_metrics()
    meta_metrics = meta_analyzer.calculate_performance_metrics()
    
    # Print comparison
    print(f"\n{'Metric':<30} {'Baseline':<20} {'Meta-Labeling':<20} {'Change':<15}")
    print("-" * 85)
    
    metrics_to_compare = [
        ('Total Signals', 'n_signals', int),
        ('Win Rate', 'win_rate', lambda x: f"{x*100:.1f}%"),
        ('Average Return', 'avg_return', lambda x: f"{x:.2f}%"),
        ('Median Return', 'median_return', lambda x: f"{x:.2f}%"),
        ('Sharpe Ratio', 'sharpe_ratio', lambda x: f"{x:.2f}"),
        ('Max Drawdown', 'max_drawdown', lambda x: f"{x:.2f}%"),
    ]
    
    comparison_data = []
    
    for label, key, formatter in metrics_to_compare:
        baseline_val = baseline_metrics.get(key, 0)
        meta_val = meta_metrics.get(key, 0)
        
        if isinstance(formatter, type) and formatter == int:
            change = meta_val - baseline_val
            change_pct = (change / baseline_val * 100) if baseline_val > 0 else 0
            change_str = f"{change:+d} ({change_pct:+.1f}%)"
        else:
            change = meta_val - baseline_val
            if isinstance(baseline_val, (int, float)) and baseline_val != 0:
                change_pct = (change / abs(baseline_val) * 100)
                change_str = f"{change:+.2f} ({change_pct:+.1f}%)"
            else:
                change_str = f"{change:+.2f}"
        
        baseline_str = formatter(baseline_val) if callable(formatter) else str(baseline_val)
        meta_str = formatter(meta_val) if callable(formatter) else str(meta_val)
        
        print(f"{label:<30} {baseline_str:<20} {meta_str:<20} {change_str:<15}")
        
        comparison_data.append({
            'metric': label,
            'baseline': baseline_val,
            'meta_labeling': meta_val,
            'change': change,
            'change_pct': change_pct if isinstance(baseline_val, (int, float)) and baseline_val != 0 else 0
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    signal_reduction = (1 - meta_metrics.get('n_signals', 0) / baseline_metrics.get('n_signals', 1)) * 100
    win_rate_improvement = (meta_metrics.get('win_rate', 0) - baseline_metrics.get('win_rate', 0)) * 100
    sharpe_improvement = meta_metrics.get('sharpe_ratio', 0) - baseline_metrics.get('sharpe_ratio', 0)
    
    print(f"\n✅ Signal Reduction: {signal_reduction:.1f}%")
    print(f"✅ Win Rate Improvement: {win_rate_improvement:+.1f} percentage points")
    print(f"✅ Sharpe Ratio Improvement: {sharpe_improvement:+.2f}")
    
    if win_rate_improvement > 5 and sharpe_improvement > 0.1:
        print("\n🎉 Meta-labeling shows SIGNIFICANT improvement!")
    elif win_rate_improvement > 0 and sharpe_improvement > 0:
        print("\n✅ Meta-labeling shows improvement")
    else:
        print("\n⚠️  Meta-labeling does not show clear improvement")
    
    return comparison_df

def main():
    parser = argparse.ArgumentParser(description='Compare backtest with vs without meta-labeling')
    parser.add_argument('--start-date', type=str, default='2025-02-01',
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--holding-period', type=int, default=12,
                       help='Holding period in weeks (default: 12)')
    parser.add_argument('--meta-labeler', type=str, required=True,
                       help='Path to trained meta-labeler model')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: backtest/comparisons)')
    
    args = parser.parse_args()
    
    # Set end date if not provided
    if args.end_date is None:
        from datetime import timedelta
        end_date = (datetime.now() - timedelta(weeks=args.holding_period)).strftime('%Y-%m-%d')
    else:
        end_date = args.end_date
    
    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = backtest_dir / "comparisons"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("COMPARE: Baseline vs Meta-Labeling")
    print("="*80)
    print(f"Start Date: {args.start_date}")
    print(f"End Date: {end_date}")
    print(f"Holding Period: {args.holding_period} weeks")
    print(f"Meta-Labeler: {args.meta_labeler}")
    print("="*80)
    
    # Run baseline backtest (without meta-labeling)
    print("\n" + "="*80)
    print("RUNNING BASELINE BACKTEST (Without Meta-Labeling)")
    print("="*80)
    engine_baseline = BacktestEngine(
        start_date=args.start_date,
        end_date=end_date,
        holding_period_weeks=args.holding_period,
        meta_labeler_path=None
    )
    baseline_results = engine_baseline.run_backtest()
    
    # Run meta-labeling backtest
    print("\n" + "="*80)
    print("RUNNING META-LABELING BACKTEST (With Meta-Labeling)")
    print("="*80)
    engine_meta = BacktestEngine(
        start_date=args.start_date,
        end_date=end_date,
        holding_period_weeks=args.holding_period,
        meta_labeler_path=args.meta_labeler
    )
    meta_results = engine_meta.run_backtest()
    
    # Compare results
    comparison_df = compare_results(baseline_results, meta_results)
    
    # Save comparison
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_file = output_dir / f"comparison_{timestamp}.csv"
    comparison_df.to_csv(comparison_file, index=False)
    print(f"\nComparison saved to {comparison_file}")
    
    # Save detailed results
    baseline_file = output_dir / f"baseline_results_{timestamp}.csv"
    meta_file = output_dir / f"meta_results_{timestamp}.csv"
    baseline_results.to_csv(baseline_file, index=False)
    meta_results.to_csv(meta_file, index=False)
    print(f"Baseline results saved to {baseline_file}")
    print(f"Meta-labeling results saved to {meta_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())

