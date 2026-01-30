#!/usr/bin/env python3
"""
Main Backtest Runner

Runs comprehensive backtest and generates report
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, REPORTS_DIR

import sys
from pathlib import Path

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from backtest_engine import BacktestEngine
from statistical_analysis import StatisticalAnalyzer
from visualizations import generate_all_visualizations
from generate_backtest_report import generate_backtest_report

def main():
    parser = argparse.ArgumentParser(description='Run backtest for investment signals')
    parser.add_argument('--start-date', type=str, default='2025-02-01',
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date for backtest (YYYY-MM-DD, default: today - 12 weeks)')
    parser.add_argument('--holding-period', type=int, default=12,
                       help='Holding period in weeks (default: 12 = 3 months)')
    parser.add_argument('--frequency', type=str, default='weekly',
                       choices=['weekly', 'daily'],
                       help='Evaluation frequency (default: weekly)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: backtest/reports and backtest/results)')
    parser.add_argument('--meta-labeler', type=str, default=None,
                       help='Path to trained meta-labeler model (optional)')
    
    args = parser.parse_args()
    
    # Set end date if not provided (default to 12 weeks before today to ensure we have forward data)
    if args.end_date is None:
        from datetime import timedelta
        end_date = (datetime.now() - timedelta(weeks=args.holding_period)).strftime('%Y-%m-%d')
    else:
        end_date = args.end_date
    
    # Output directories
    if args.output_dir:
        output_dir = Path(args.output_dir)
        reports_dir = output_dir / "reports"
        results_dir = output_dir / "results"
    else:
        backtest_dir = Path(__file__).parent
        reports_dir = backtest_dir / "reports"
        results_dir = backtest_dir / "results"
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("BACKTEST: Investment Signal Performance")
    print("="*80)
    print(f"Start Date: {args.start_date}")
    print(f"End Date: {end_date}")
    print(f"Holding Period: {args.holding_period} weeks")
    print(f"Evaluation Frequency: {args.frequency}")
    print("="*80)
    
    # Initialize and run backtest
    engine = BacktestEngine(
        start_date=args.start_date,
        end_date=end_date,
        holding_period_weeks=args.holding_period,
        meta_labeler_path=args.meta_labeler
    )
    
    results_df = engine.run_backtest(evaluation_frequency=args.frequency)
    
    if len(results_df) == 0:
        print("\n❌ ERROR: No results generated. Check data availability.")
        return 1
    
    # Save results
    date_str = datetime.now().strftime('%Y%m%d')
    results_file = results_dir / f"signal_performance_{date_str}.csv"
    results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
    print(f"\nResults saved: {results_file}")
    
    # Statistical analysis
    print("\n" + "="*80)
    print("Performing Statistical Analysis")
    print("="*80)
    
    analyzer = StatisticalAnalyzer(results_df)
    analysis_summary = analyzer.generate_summary()
    
    # Generate visualizations
    generate_all_visualizations(results_df, reports_dir, date_str)
    
    # Generate report
    report_file = reports_dir / f"backtest_report_{date_str}.md"
    generate_backtest_report(results_df, analysis_summary, report_file, date_str)
    
    # Print summary
    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80)
    print(f"\nResults:")
    print(f"  Total Signals: {len(results_df)}")
    
    overall = analysis_summary.get('overall_metrics', {})
    if overall:
        print(f"  Win Rate: {overall.get('win_rate', 0):.1f}%")
        print(f"  Average Return: {overall.get('avg_return', 0):.2f}%")
        print(f"  Sharpe Ratio: {overall.get('sharpe_ratio', 0):.2f}")
    
    print(f"\nOutput Files:")
    print(f"  Results CSV: {results_file}")
    print(f"  Report: {report_file}")
    print(f"  Visualizations: {reports_dir}/*_{date_str}.png")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

