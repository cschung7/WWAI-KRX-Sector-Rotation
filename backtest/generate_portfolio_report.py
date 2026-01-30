#!/usr/bin/env python3
"""
Generate Portfolio Report for Alternative Allocation Strategy

Shows which sectors/themes and tickers would be in portfolio
based on signals from a specific date
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, DB_FILE

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from backtest_engine import BacktestEngine
from strategy_etf_improved import ImprovedETFStrategy
from signal_calculator import SignalCalculator

def check_signal_validity(signal_calc, theme_name, fiedler_ts, signal_date, check_date):
    """Check if signal is still valid at check_date"""
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
    is_tier1 = (
        week_before_fiedler > 2.0 and
        change > 1.5 and
        current_fiedler > 3.0
    )
    
    is_tier2 = (
        week_before_fiedler > 1.0 and
        week_before_fiedler <= 2.0 and
        change > 1.0
    )
    
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

def generate_portfolio_report(start_date, output_file):
    """Generate portfolio report for Alternative Allocation strategy"""
    
    print("="*80)
    print("PORTFOLIO REPORT: Alternative Allocation (20/20/60) Strategy")
    print("="*80)
    print(f"Analysis Date: {start_date}")
    print()
    
    # Initialize backtest engine
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(weeks=12)).strftime('%Y-%m-%d')
    
    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        holding_period_weeks=12
    )
    
    # Initialize strategy
    strategy = ImprovedETFStrategy(
        strategy_type='alternative',
        exit_target_return=20.0,
        exit_weeks=12,
        min_signal_strength_week7=0.0
    )
    
    # Get signals for the start date
    signal_date = pd.to_datetime(start_date)
    signal_calc = engine.signal_calc
    
    portfolio_themes = []
    
    print("Scanning themes for signals...")
    
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
            signal_date,
            engine.leadership_data
        )
        
        if not signals:
            continue
        
        # Get theme tickers
        if actual_theme not in engine.theme_mapping:
            continue
        
        tickers = engine.theme_mapping[actual_theme]
        
        # For each signal, check if it would be in portfolio
        for signal in signals:
            signal_strength = signal.get('signal_strength', 0)
            
            # Create signal validity checker
            def check_validity(signal_date, check_date):
                return check_signal_validity(
                    signal_calc, actual_theme, fiedler_ts, signal_date, check_date
                )
            
            # Check if strategy would enter this position
            # For Alternative: 20% week 1, 20% week 2, 60% week 7 if valid
            # We'll include it if signal exists (week 1-2 entry) or if valid at week 7
            
            week7_dt = signal_date + timedelta(weeks=7)
            is_valid_week7, week7_strength = check_validity(signal_date, week7_dt)
            
            portfolio_themes.append({
                'theme': actual_theme,
                'signal_type': signal['signal_type'],
                'signal_strength': signal_strength,
                'tier': signal.get('tier', None),
                'leadership_gap': signal.get('leadership_gap', None),
                'fiedler_change': signal.get('change', None),
                'pct_change': signal.get('pct_change', None),
                'n_tickers': len(tickers),
                'tickers': tickers[:20],  # Limit to first 20 for display
                'valid_at_week7': is_valid_week7,
                'week7_signal_strength': week7_strength
            })
    
    print(f"\nFound {len(portfolio_themes)} signals/themes for portfolio")
    
    # Load stock names from database
    db_df = pd.read_csv(DB_FILE)
    ticker_to_name = dict(zip(db_df['tickers'], db_df['name']))
    
    # Generate report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Portfolio Report: Alternative Allocation (20/20/60) Strategy\n\n")
        f.write(f"**Analysis Date**: {start_date}\n")
        f.write(f"**Strategy**: Alternative Allocation (20% week 1, 20% week 2, 60% week 7 if valid)\n")
        f.write(f"**Exit Target**: 20% return or 12 weeks\n")
        f.write(f"**Total Themes in Portfolio**: {len(portfolio_themes)}\n\n")
        f.write("---\n\n")
        
        # Group by signal type
        by_type = {}
        for item in portfolio_themes:
            sig_type = item['signal_type']
            if sig_type not in by_type:
                by_type[sig_type] = []
            by_type[sig_type].append(item)
        
        f.write("## Portfolio Composition by Signal Type\n\n")
        
        for sig_type, items in sorted(by_type.items()):
            f.write(f"### {sig_type.upper()} Signals ({len(items)} themes)\n\n")
            
            # Sort by signal strength
            items_sorted = sorted(items, key=lambda x: x['signal_strength'], reverse=True)
            
            f.write("| Rank | Theme | Signal Strength | Tier | Tickers | Valid Week 7 |\n")
            f.write("|------|-------|----------------|------|---------|--------------|\n")
            
            for rank, item in enumerate(items_sorted, 1):
                tier_str = f"TIER {int(item['tier'])}" if item['tier'] else "-"
                valid_str = "✅ Yes" if item['valid_at_week7'] else "❌ No"
                ticker_count = len(item['tickers'])
                f.write(f"| {rank} | {item['theme'][:40]} | {item['signal_strength']:.2f} | "
                       f"{tier_str} | {ticker_count} | {valid_str} |\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Detailed ticker list
        f.write("## Detailed Ticker List by Theme\n\n")
        
        for item in sorted(portfolio_themes, key=lambda x: x['signal_strength'], reverse=True):
            f.write(f"### {item['theme']}\n\n")
            f.write(f"- **Signal Type**: {item['signal_type']}\n")
            f.write(f"- **Signal Strength**: {item['signal_strength']:.2f}\n")
            if item['tier']:
                f.write(f"- **Tier**: TIER {int(item['tier'])}\n")
            if item['fiedler_change']:
                f.write(f"- **Fiedler Change**: {item['fiedler_change']:.2f} ({item['pct_change']:.1f}%)\n")
            if item['leadership_gap']:
                f.write(f"- **Leadership Gap**: {item['leadership_gap']:.1f}%\n")
            f.write(f"- **Valid at Week 7**: {'✅ Yes' if item['valid_at_week7'] else '❌ No'}\n")
            f.write(f"- **Number of Tickers**: {item['n_tickers']}\n\n")
            
            f.write("**Tickers**:\n")
            ticker_list = []
            for ticker in item['tickers']:
                stock_name = ticker_to_name.get(ticker, ticker)
                ticker_list.append(f"{ticker} ({stock_name})")
            
            # Display in columns
            for i in range(0, len(ticker_list), 3):
                row = ticker_list[i:i+3]
                f.write("- " + " | ".join(row) + "\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        
        # Summary statistics
        f.write("## Portfolio Summary Statistics\n\n")
        
        total_tickers = set()
        for item in portfolio_themes:
            total_tickers.update(item['tickers'])
        
        tier1_count = sum(1 for item in portfolio_themes if item['tier'] == 1)
        tier2_count = sum(1 for item in portfolio_themes if item['tier'] == 2)
        valid_week7_count = sum(1 for item in portfolio_themes if item['valid_at_week7'])
        
        f.write(f"- **Total Themes**: {len(portfolio_themes)}\n")
        f.write(f"- **Total Unique Tickers**: {len(total_tickers)}\n")
        f.write(f"- **TIER 1 Themes**: {tier1_count}\n")
        f.write(f"- **TIER 2 Themes**: {tier2_count}\n")
        f.write(f"- **Themes Valid at Week 7**: {valid_week7_count} ({valid_week7_count/len(portfolio_themes)*100:.1f}%)\n")
        f.write(f"- **By Signal Type**:\n")
        for sig_type, items in sorted(by_type.items()):
            f.write(f"  - {sig_type}: {len(items)}\n")
        
        f.write("\n---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\nPortfolio report saved: {output_file}")
    print(f"Total themes in portfolio: {len(portfolio_themes)}")
    print(f"Total unique tickers: {len(set(t for item in portfolio_themes for t in item['tickers']))}")

def main():
    parser = argparse.ArgumentParser(description='Generate portfolio report for Alternative Allocation strategy')
    parser.add_argument('--date', type=str, default='2025-08-01',
                       help='Start date for portfolio (YYYY-MM-DD, default: 2025-08-01)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: backtest/reports/portfolio_YYYYMMDD.md)')
    
    args = parser.parse_args()
    
    if args.output:
        output_file = Path(args.output)
    else:
        date_str = args.date.replace('-', '')
        output_file = backtest_dir / "reports" / f"portfolio_{date_str}.md"
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    generate_portfolio_report(args.date, output_file)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

