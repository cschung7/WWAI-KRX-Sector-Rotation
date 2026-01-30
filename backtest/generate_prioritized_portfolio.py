#!/usr/bin/env python3
"""
Generate Prioritized Portfolio Report

Filters and ranks themes by signal strength, tier, and other criteria
to create a focused portfolio
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

def calculate_theme_score(item):
    """Calculate composite score for ranking themes"""
    score = 0
    
    # Tier signals get highest priority
    if item['tier'] == 1:
        score += 100
    elif item['tier'] == 2:
        score += 50
    
    # Signal strength (0-3 scale, multiply by 20)
    score += item['signal_strength'] * 20
    
    # Signal type priority: tier > cohesion > leadership
    if item['signal_type'] == 'tier':
        score += 30
    elif item['signal_type'] == 'cohesion':
        score += 20
    elif item['signal_type'] == 'leadership':
        score += 10
    
    # Valid at week 7 gets bonus
    if item['valid_at_week7']:
        score += 15
    
    # Fiedler change bonus
    if item['fiedler_change']:
        if item['fiedler_change'] > 2.0:
            score += 10
        elif item['fiedler_change'] > 1.5:
            score += 5
    
    return score

def generate_prioritized_portfolio(start_date, max_themes=30, output_file=None):
    """Generate prioritized portfolio report"""
    
    print("="*80)
    print("PRIORITIZED PORTFOLIO REPORT: Alternative Allocation (20/20/60)")
    print("="*80)
    print(f"Analysis Date: {start_date}")
    print(f"Max Themes: {max_themes}")
    print()
    
    # Initialize backtest engine
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(weeks=12)).strftime('%Y-%m-%d')
    
    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        holding_period_weeks=12
    )
    
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
        
        if actual_theme not in engine.theme_mapping:
            continue
        
        tickers = engine.theme_mapping[actual_theme]
        
        # For each signal
        for signal in signals:
            signal_strength = signal.get('signal_strength', 0)
            
            def check_validity(signal_date, check_date):
                return check_signal_validity(
                    signal_calc, actual_theme, fiedler_ts, signal_date, check_date
                )
            
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
                'tickers': tickers,
                'valid_at_week7': is_valid_week7,
                'week7_signal_strength': week7_strength
            })
    
    print(f"Found {len(portfolio_themes)} total signals/themes")
    
    # Calculate scores and rank
    for item in portfolio_themes:
        item['score'] = calculate_theme_score(item)
    
    # Sort by score
    portfolio_themes.sort(key=lambda x: x['score'], reverse=True)
    
    # Take top themes
    top_themes = portfolio_themes[:max_themes]
    
    print(f"Selected top {len(top_themes)} themes for portfolio")
    
    # Load stock names
    db_df = pd.read_csv(DB_FILE)
    ticker_to_name = dict(zip(db_df['tickers'], db_df['name']))
    
    # Generate report
    if output_file is None:
        date_str = start_date.replace('-', '')
        output_file = backtest_dir / "reports" / f"prioritized_portfolio_{date_str}.md"
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Prioritized Portfolio: Alternative Allocation (20/20/60) Strategy\n\n")
        f.write(f"**Analysis Date**: {start_date}\n")
        f.write(f"**Strategy**: Alternative Allocation (20% week 1, 20% week 2, 60% week 7 if valid)\n")
        f.write(f"**Exit Target**: 20% return or 12 weeks\n")
        f.write(f"**Total Themes Selected**: {len(top_themes)} (from {len(portfolio_themes)} total signals)\n")
        f.write(f"**Selection Criteria**: Ranked by composite score (Tier > Signal Strength > Signal Type > Week 7 Validity)\n\n")
        f.write("---\n\n")
        
        # Summary by tier
        tier1_themes = [t for t in top_themes if t['tier'] == 1]
        tier2_themes = [t for t in top_themes if t['tier'] == 2]
        other_themes = [t for t in top_themes if t['tier'] is None]
        
        f.write("## Portfolio Summary\n\n")
        f.write(f"- **TIER 1 Themes**: {len(tier1_themes)} (Highest Priority)\n")
        f.write(f"- **TIER 2 Themes**: {len(tier2_themes)}\n")
        f.write(f"- **Other Signals**: {len(other_themes)}\n")
        f.write(f"- **Themes Valid at Week 7**: {sum(1 for t in top_themes if t['valid_at_week7'])} ({sum(1 for t in top_themes if t['valid_at_week7'])/len(top_themes)*100:.1f}%)\n\n")
        
        # Get all unique tickers
        all_tickers = set()
        for theme in top_themes:
            all_tickers.update(theme['tickers'])
        f.write(f"- **Total Unique Tickers**: {len(all_tickers)}\n\n")
        
        f.write("---\n\n")
        
        # Top themes table
        f.write("## Top Themes Portfolio\n\n")
        f.write("| Rank | Theme | Signal Type | Tier | Score | Strength | Valid W7 | Tickers |\n")
        f.write("|------|-------|-------------|------|-------|----------|----------|---------|\n")
        
        for rank, theme in enumerate(top_themes, 1):
            tier_str = f"TIER {int(theme['tier'])}" if theme['tier'] else "-"
            valid_str = "✅" if theme['valid_at_week7'] else "❌"
            f.write(f"| {rank} | {theme['theme'][:35]} | {theme['signal_type']} | {tier_str} | "
                   f"{theme['score']:.0f} | {theme['signal_strength']:.2f} | {valid_str} | "
                   f"{theme['n_tickers']} |\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        # Detailed theme information
        f.write("## Detailed Theme Information\n\n")
        
        for rank, theme in enumerate(top_themes, 1):
            f.write(f"### {rank}. {theme['theme']}\n\n")
            f.write(f"- **Signal Type**: {theme['signal_type']}\n")
            tier_display = f"TIER {int(theme['tier'])}" if theme['tier'] else 'N/A'
            f.write(f"- **Tier**: {tier_display}\n")
            f.write(f"- **Composite Score**: {theme['score']:.0f}\n")
            f.write(f"- **Signal Strength**: {theme['signal_strength']:.2f}\n")
            if theme['fiedler_change']:
                f.write(f"- **Fiedler Change**: {theme['fiedler_change']:.2f} ({theme['pct_change']:.1f}%)\n")
            if theme['leadership_gap']:
                f.write(f"- **Leadership Gap**: {theme['leadership_gap']:.1f}%\n")
            f.write(f"- **Valid at Week 7**: {'✅ Yes' if theme['valid_at_week7'] else '❌ No'}\n")
            f.write(f"- **Number of Tickers**: {theme['n_tickers']}\n\n")
            
            f.write("**Tickers**:\n")
            ticker_list = []
            for ticker in theme['tickers'][:30]:  # Limit to 30 for readability
                stock_name = ticker_to_name.get(ticker, ticker)
                ticker_list.append(f"{ticker} ({stock_name})")
            
            # Display in columns
            for i in range(0, len(ticker_list), 3):
                row = ticker_list[i:i+3]
                f.write("- " + " | ".join(row) + "\n")
            
            if len(theme['tickers']) > 30:
                f.write(f"- ... and {len(theme['tickers']) - 30} more tickers\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        
        # All tickers list
        f.write("## Complete Ticker List\n\n")
        f.write(f"**Total Unique Tickers**: {len(all_tickers)}\n\n")
        
        ticker_list_sorted = sorted([(t, ticker_to_name.get(t, t)) for t in all_tickers])
        
        for i in range(0, len(ticker_list_sorted), 5):
            row = ticker_list_sorted[i:i+5]
            ticker_str = " | ".join([f"{t[0]} ({t[1]})" for t in row])
            f.write(f"- {ticker_str}\n")
        
        f.write("\n---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\nPrioritized portfolio report saved: {output_file}")
    print(f"Selected {len(top_themes)} themes from {len(portfolio_themes)} total signals")
    print(f"Total unique tickers: {len(all_tickers)}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate prioritized portfolio report')
    parser.add_argument('--date', type=str, default='2025-08-01',
                       help='Start date for portfolio (YYYY-MM-DD)')
    parser.add_argument('--max-themes', type=int, default=30,
                       help='Maximum number of themes to include (default: 30)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path')
    
    args = parser.parse_args()
    
    generate_prioritized_portfolio(args.date, args.max_themes, args.output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

