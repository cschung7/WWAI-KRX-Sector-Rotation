#!/usr/bin/env python3
"""
Backtest ETF-Style Strategy

Compares ETF-style gradual entry vs simple buy-and-hold
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from backtest_engine import BacktestEngine
from strategy_etf_style import ETFStyleStrategy
from strategy_etf_improved import ImprovedETFStrategy
from statistical_analysis import StatisticalAnalyzer
from visualizations import generate_all_visualizations
from generate_backtest_report import generate_backtest_report

def check_signal_validity(signal_calc, theme_name, fiedler_ts, signal_date, check_date):
    """
    Check if signal is still valid at check_date
    
    Returns:
        (is_valid, signal_strength)
    """
    # Filter to data up to check_date
    historical_data = fiedler_ts[fiedler_ts['date'] <= pd.to_datetime(check_date)].copy()
    
    if len(historical_data) < 2:
        return False, 0.0
    
    historical_data = historical_data.sort_values('date')
    current = historical_data.iloc[-1]
    previous = historical_data.iloc[-2]
    
    current_fiedler = current['fiedler']
    week_before_fiedler = previous['fiedler']
    change = current_fiedler - week_before_fiedler
    
    # Check if still meets tier or cohesion criteria
    # Tier 1: Baseline >2.0 AND Change >1.5 AND Current >3.0
    is_tier1 = (
        week_before_fiedler > 2.0 and
        change > 1.5 and
        current_fiedler > 3.0
    )
    
    # Tier 2: Baseline 1.0-2.0 AND Change >1.0
    is_tier2 = (
        week_before_fiedler > 1.0 and
        week_before_fiedler <= 2.0 and
        change > 1.0
    )
    
    # Cohesion: Change >1.5 AND Current >2.0
    is_cohesion = (
        change > 1.5 and
        current_fiedler > 2.0
    )
    
    is_valid = is_tier1 or is_tier2 or is_cohesion
    
    if is_valid:
        signal_strength = min(change / 1.5, 3.0) if change > 0 else 0.5
    else:
        signal_strength = 0.0
    
    return is_valid, signal_strength

def main():
    parser = argparse.ArgumentParser(description='Backtest ETF-style strategy')
    parser.add_argument('--start-date', type=str, default='2025-02-01',
                       help='Start date for backtest (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date for backtest (YYYY-MM-DD)')
    parser.add_argument('--exit-target', type=float, default=20.0,
                       help='Exit target return % (default: 20.0)')
    parser.add_argument('--max-weeks', type=int, default=12,
                       help='Maximum holding period in weeks (default: 12)')
    parser.add_argument('--strategy', type=str, default='all',
                       choices=['original', 'relaxed', 'alternative', 'buy_after_8w', 'all'],
                       help='Strategy variant to test (default: all)')
    
    args = parser.parse_args()
    
    # Set end date if not provided
    if args.end_date is None:
        end_date = (datetime.now() - timedelta(weeks=args.max_weeks)).strftime('%Y-%m-%d')
    else:
        end_date = args.end_date
    
    print("="*80)
    print("BACKTEST: ETF-Style Gradual Entry Strategy")
    print("="*80)
    print(f"Start Date: {args.start_date}")
    print(f"End Date: {end_date}")
    print(f"Exit Target: {args.exit_target}%")
    print(f"Max Holding Period: {args.max_weeks} weeks")
    print("="*80)
    
    # Initialize backtest engine
    engine = BacktestEngine(
        start_date=args.start_date,
        end_date=end_date,
        holding_period_weeks=args.max_weeks
    )
    
    # Initialize strategies
    strategies_to_test = []
    if args.strategy == 'all':
        strategies_to_test = [
            ('original', ETFStyleStrategy(exit_target_return=args.exit_target, exit_weeks=args.max_weeks)),
            ('relaxed', ImprovedETFStrategy(strategy_type='relaxed', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0)),
            ('alternative', ImprovedETFStrategy(strategy_type='alternative', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0)),
            ('buy_after_8w', ImprovedETFStrategy(strategy_type='buy_after_8w', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0)),
        ]
    elif args.strategy == 'original':
        strategies_to_test = [('original', ETFStyleStrategy(exit_target_return=args.exit_target, exit_weeks=args.max_weeks))]
    elif args.strategy == 'relaxed':
        strategies_to_test = [('relaxed', ImprovedETFStrategy(strategy_type='relaxed', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0))]
    elif args.strategy == 'alternative':
        strategies_to_test = [('alternative', ImprovedETFStrategy(strategy_type='alternative', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0))]
    elif args.strategy == 'buy_after_8w':
        strategies_to_test = [('buy_after_8w', ImprovedETFStrategy(strategy_type='buy_after_8w', exit_target_return=args.exit_target, exit_weeks=args.max_weeks, min_signal_strength_week7=0.0))]
    
    # Run backtest with ETF strategy
    print("\n" + "="*80)
    print("Running ETF-Style Strategy Backtest")
    print("="*80)
    
    # Generate evaluation dates
    start_dt = pd.to_datetime(args.start_date)
    end_dt = pd.to_datetime(end_date)
    eval_end_date = end_dt - timedelta(weeks=args.max_weeks)
    eval_dates = pd.date_range(start_dt, eval_end_date, freq='W')
    
    print(f"Evaluating {len(eval_dates)} dates...")
    
    all_strategy_results = {}
    buy_hold_results = []
    
    signal_calc = engine.signal_calc
    
    for i, eval_date in enumerate(eval_dates):
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(eval_dates)} dates...")
        
        # For each theme
        for safe_theme_name, fiedler_ts in engine.fiedler_timeseries.items():
            # Find actual theme name
            actual_theme = None
            for actual, safe in engine.theme_name_mapping.items():
                if safe_theme_name.replace(' ', '_') in actual.replace(' ', '_') or \
                   actual.replace(' ', '_') in safe_theme_name.replace(' ', '_'):
                    actual_theme = actual
                    break
            
            if actual_theme is None:
                if safe_theme_name in engine.theme_mapping:
                    actual_theme = safe_theme_name
                else:
                    continue
            
            # Calculate signals
            signals = signal_calc.calculate_all_signals_for_date(
                actual_theme,
                fiedler_ts,
                eval_date,
                engine.leadership_data
            )
            
            if not signals:
                continue
            
            # Get theme tickers
            if actual_theme not in engine.theme_mapping:
                continue
            
            tickers = engine.theme_mapping[actual_theme]
            
            # For each signal, test all strategies
            for signal in signals:
                signal_strength = signal.get('signal_strength', 0)
                
                # Create signal validity checker
                def check_validity(signal_date, check_date):
                    return check_signal_validity(
                        signal_calc, actual_theme, fiedler_ts, signal_date, check_date
                    )
                
                # Test each strategy variant
                for strategy_name, strategy_obj in strategies_to_test:
                    if strategy_name not in all_strategy_results:
                        all_strategy_results[strategy_name] = []
                    
                    strategy_result = strategy_obj.calculate_theme_strategy_return(
                        actual_theme,
                        tickers,
                        engine.price_data,
                        eval_date,
                        signal_strength,
                        check_validity
                    )
                    
                    if strategy_result:
                        strategy_result.update({
                            'signal_date': eval_date,
                            'signal_type': signal['signal_type'],
                            'signal_strength': signal_strength,
                            'tier': signal.get('tier', None),
                        })
                        all_strategy_results[strategy_name].append(strategy_result)
                
                # Buy-and-hold strategy (for comparison)
                buy_hold_return = engine.return_calc.calculate_theme_return(
                    actual_theme,
                    eval_date,
                    args.max_weeks
                )
                
                if buy_hold_return:
                    buy_hold_results.append({
                        'signal_date': eval_date,
                        'theme': actual_theme,
                        'signal_type': signal['signal_type'],
                        'signal_strength': signal_strength,
                        'tier': signal.get('tier', None),
                        'total_return': buy_hold_return['total_return'],
                        'strategy': 'buy_hold'
                    })
    
    print(f"\nStrategy Results:")
    for strategy_name, results in all_strategy_results.items():
        print(f"  {strategy_name}: {len(results)} signals")
    print(f"  Buy-Hold: {len(buy_hold_results)} signals")
    
    # Convert to DataFrames
    strategy_dfs = {}
    for strategy_name, results in all_strategy_results.items():
        if len(results) > 0:
            strategy_dfs[strategy_name] = pd.DataFrame(results)
    
    buy_hold_df = pd.DataFrame(buy_hold_results)
    
    if len(strategy_dfs) == 0:
        print("\n❌ ERROR: No strategy results generated.")
        return 1
    
    # Save results
    date_str = datetime.now().strftime('%Y%m%d')
    results_dir = backtest_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nResults saved:")
    for strategy_name, df in strategy_dfs.items():
        file_path = results_dir / f"{strategy_name}_strategy_results_{date_str}.csv"
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
        print(f"  {strategy_name}: {file_path}")
    
    buy_hold_file = results_dir / f"buy_hold_comparison_{date_str}.csv"
    buy_hold_df.to_csv(buy_hold_file, index=False, encoding='utf-8-sig')
    print(f"  Buy-Hold: {buy_hold_file}")
    
    # Statistical analysis
    print("\n" + "="*80)
    print("Performance Comparison")
    print("="*80)
    
    strategy_metrics = {}
    for strategy_name, df in strategy_dfs.items():
        analyzer = StatisticalAnalyzer(df.rename(columns={'total_return': 'total_return'}))
        metrics = analyzer.calculate_performance_metrics()
        strategy_metrics[strategy_name] = {
            'metrics': metrics,
            'df': df
        }
    
    buy_hold_analyzer = StatisticalAnalyzer(buy_hold_df)
    buy_hold_metrics = buy_hold_analyzer.calculate_performance_metrics()
    
    for strategy_name, data in strategy_metrics.items():
        metrics = data['metrics']
        df = data['df']
        print(f"\n{strategy_name.upper()} Strategy:")
        print(f"  Total Signals: {metrics.get('total_signals', 0)}")
        print(f"  Win Rate: {metrics.get('win_rate', 0):.1f}%")
        if 'holding_weeks' in df.columns:
            avg_weeks = df['holding_weeks'].mean()
            print(f"  Avg Holding Weeks: {avg_weeks:.1f}")
            print(f"  Average Return: {metrics.get('avg_return', 0):.2f}% (over {avg_weeks:.1f} weeks, NOT annualized)")
            if avg_weeks > 0:
                annualized = metrics.get('avg_return', 0) * (52 / avg_weeks)
                print(f"  Annualized Return: {annualized:.2f}%")
        else:
            print(f"  Average Return: {metrics.get('avg_return', 0):.2f}% (over holding period, NOT annualized)")
        print(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f} (annualized)")
        if 'signal_still_valid_pct' in df.columns:
            print(f"  Signals Valid: {df['signal_still_valid_pct'].mean():.1f}%")
    
    print(f"\nBuy-and-Hold Strategy:")
    print(f"  Total Signals: {buy_hold_metrics.get('total_signals', 0)}")
    print(f"  Win Rate: {buy_hold_metrics.get('win_rate', 0):.1f}%")
    print(f"  Average Return: {buy_hold_metrics.get('avg_return', 0):.2f}% (over 12 weeks, NOT annualized)")
    annualized_bh = buy_hold_metrics.get('avg_return', 0) * (52 / 12)
    print(f"  Annualized Return: {annualized_bh:.2f}%")
    print(f"  Sharpe Ratio: {buy_hold_metrics.get('sharpe_ratio', 0):.2f} (annualized)")
    
    # Generate comparison report
    reports_dir = backtest_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = reports_dir / f"etf_strategy_comparison_{date_str}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# ETF-Style Strategy Variants vs Buy-and-Hold Comparison\n\n")
        f.write(f"**Report Date**: {date_str}\n")
        f.write(f"**Analysis Period**: {args.start_date} to {end_date}\n")
        f.write(f"**Exit Target**: {args.exit_target}%\n")
        f.write(f"**Max Holding Period**: {args.max_weeks} weeks\n\n")
        f.write("---\n\n")
        
        f.write("## Strategy Descriptions\n\n")
        f.write("### 1. Original ETF-Style (Strict Validity)\n")
        f.write("- Week 1: Buy 10% of position\n")
        f.write("- Week 2: Buy 10% of position\n")
        f.write("- Weeks 3-7: Hold 80% cash, monitor signal validity\n")
        f.write("- Week 7: If signal still valid (strict criteria), go long with remaining 80%\n")
        f.write(f"- Exit: {args.max_weeks} weeks OR {args.exit_target}% return\n\n")
        
        f.write("### 2. Relaxed ETF-Style\n")
        f.write("- Week 1: Buy 10% of position\n")
        f.write("- Week 2: Buy 10% of position\n")
        f.write("- Week 7: If signal still positive (relaxed criteria), go long with remaining 80%\n")
        f.write(f"- Exit: {args.max_weeks} weeks OR {args.exit_target}% return\n\n")
        
        f.write("### 3. Alternative Allocation\n")
        f.write("- Week 1: Buy 20% of position\n")
        f.write("- Week 2: Buy 20% of position\n")
        f.write("- Week 7: If signal still positive, go long with remaining 60%\n")
        f.write(f"- Exit: {args.max_weeks} weeks OR {args.exit_target}% return\n\n")
        
        f.write("### 4. Buy After 8 Weeks\n")
        f.write("- Weeks 1-7: Hold 100% cash, monitor signal validity\n")
        f.write("- Week 8: If signal still valid, buy 100% of position\n")
        f.write(f"- Exit: {args.max_weeks} weeks OR {args.exit_target}% return\n\n")
        
        f.write("### 5. Buy-and-Hold (Comparison)\n")
        f.write("- Buy 100% at signal date\n")
        f.write(f"- Hold for {args.max_weeks} weeks\n\n")
        
        f.write("---\n\n")
        
        f.write("## Performance Comparison\n\n")
        f.write("**Note**: Returns shown are over the actual holding period, NOT annualized. Annualized returns are shown in parentheses.\n\n")
        f.write("| Strategy | Signals | Win Rate | Avg Return (Annualized) | Sharpe | Avg Weeks | Valid % |\n")
        f.write("|----------|---------|----------|------------------------|--------|-----------|--------|\n")
        
        for strategy_name, data in strategy_metrics.items():
            metrics = data['metrics']
            df = data['df']
            holding_weeks = df['holding_weeks'].mean() if 'holding_weeks' in df.columns else args.max_weeks
            valid_pct = df['signal_still_valid_pct'].mean() if 'signal_still_valid_pct' in df.columns else 0
            avg_return = metrics.get('avg_return', 0)
            annualized_return = avg_return * (52 / holding_weeks) if holding_weeks > 0 else 0
            f.write(f"| {strategy_name} | {metrics.get('total_signals', 0)} | "
                   f"{metrics.get('win_rate', 0):.1f}% | "
                   f"{avg_return:.2f}% ({annualized_return:.1f}% ann.) | "
                   f"{metrics.get('sharpe_ratio', 0):.2f} | "
                   f"{holding_weeks:.1f} | "
                   f"{valid_pct:.1f}% |\n")
        
        buy_hold_return = buy_hold_metrics.get('avg_return', 0)
        buy_hold_annualized = buy_hold_return * (52 / args.max_weeks)
        f.write(f"| Buy-Hold | {buy_hold_metrics.get('total_signals', 0)} | "
               f"{buy_hold_metrics.get('win_rate', 0):.1f}% | "
               f"{buy_hold_return:.2f}% ({buy_hold_annualized:.1f}% ann.) | "
               f"{buy_hold_metrics.get('sharpe_ratio', 0):.2f} | "
               f"{args.max_weeks} | - |\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        f.write("## Key Findings\n\n")
        
        # Find best strategy
        best_strategy = None
        best_return = -999
        for strategy_name, data in strategy_metrics.items():
            return_val = data['metrics'].get('avg_return', -999)
            if return_val > best_return:
                best_return = return_val
                best_strategy = strategy_name
        
        if best_strategy:
            f.write(f"🏆 **Best Strategy by Return**: {best_strategy} ({best_return:.2f}%)\n\n")
        
        # Compare to buy-and-hold
        buy_hold_return = buy_hold_metrics.get('avg_return', 0)
        if best_return > buy_hold_return:
            f.write(f"✅ **Best strategy outperforms buy-and-hold by {best_return - buy_hold_return:.2f}%**\n\n")
        else:
            f.write(f"⚠️ **Buy-and-hold outperforms best strategy by {buy_hold_return - best_return:.2f}%**\n\n")
        
        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\nComparison report saved: {report_file}")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

