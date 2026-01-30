#!/usr/bin/env python3
"""
Generate Focused Portfolio Report

Creates a focused portfolio with only:
- All TIER 1 themes
- All TIER 2 themes  
- Top cohesion signals (if any slots remaining)
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_FILE

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from backtest_engine import BacktestEngine
from strategy_etf_improved import ImprovedETFStrategy
from signal_calculator import SignalCalculator
from signal_calculator_enhanced import EnhancedSignalCalculator
try:
    from meta_labeling_filter import MetaLabelingFilter
    HAS_META_LABELING = True
except ImportError:
    HAS_META_LABELING = False
    print("Warning: Meta-labeling filter not available")

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

def generate_focused_portfolio(start_date, output_file=None, use_meta_labeling=True):
    """Generate focused portfolio with only TIER 1, TIER 2, and top signals"""
    
    print("="*80)
    print("FOCUSED PORTFOLIO: Alternative Allocation (20/20/60)")
    print("="*80)
    print(f"Analysis Date: {start_date}")
    print("Focus: TIER 1 + TIER 2 + Top Cohesion Signals")
    print()
    
    # Initialize backtest engine
    end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(weeks=12)).strftime('%Y-%m-%d')
    
    engine = BacktestEngine(
        start_date=start_date,
        end_date=end_date,
        holding_period_weeks=12
    )
    
    signal_date = pd.to_datetime(start_date)
    
    # Load regime data for enhanced signal calculation
    # Use latest available data (not filtered by date) since regime data may not exist for historical dates
    print("Loading regime data...")
    regime_data = engine.loader.load_regime_data(date=None)  # Get latest available
    
    # Calculate regime summary (by stock name)
    if len(regime_data) > 0 and 'Ticker' in regime_data.columns:
        regime_summary = regime_data.groupby('Ticker', group_keys=False).apply(
            lambda x: pd.Series({
                'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
                'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
                'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
                'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
                'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
            }), include_groups=False
        ).reset_index()
        regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})
        print(f"  Loaded regime data for {len(regime_summary)} stocks")
    else:
        regime_summary = pd.DataFrame()
        print("  Warning: No regime data available")
    
    # Use enhanced signal calculator with regime data
    if len(regime_summary) > 0:
        signal_calc = EnhancedSignalCalculator(regime_summary=regime_summary)
    else:
        signal_calc = engine.signal_calc
    
    # Load database for ticker-to-name mapping
    db_df = pd.read_csv(DB_FILE)
    
    all_themes = []
    
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
        
        if actual_theme not in engine.theme_mapping:
            continue
        
        tickers = engine.theme_mapping[actual_theme]
        
        # Calculate signals (with regime if enhanced calculator)
        if isinstance(signal_calc, EnhancedSignalCalculator):
            signals = signal_calc.calculate_all_signals_with_regime(
                actual_theme,
                fiedler_ts,
                signal_date,
                engine.leadership_data,
                tickers,
                db_df
            )
        else:
            signals = signal_calc.calculate_all_signals_for_date(
                actual_theme,
                fiedler_ts,
                signal_date,
                engine.leadership_data
            )
        
        if not signals:
            continue
        
        # For each signal
        for signal in signals:
            signal_strength = signal.get('signal_strength', 0)
            
            def check_validity(signal_date, check_date):
                return check_signal_validity(
                    signal_calc, actual_theme, fiedler_ts, signal_date, check_date
                )
            
            week7_dt = signal_date + timedelta(weeks=7)
            is_valid_week7, week7_strength = check_validity(signal_date, week7_dt)
            
            theme_item = {
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
            }
            
            # Add regime metrics if available
            if 'regime_avg_bull_pct' in signal:
                theme_item['regime_avg_bull_pct'] = signal['regime_avg_bull_pct']
                theme_item['regime_avg_trend'] = signal.get('regime_avg_trend', 0)
                theme_item['regime_avg_momentum'] = signal.get('regime_avg_momentum', 0)
                theme_item['regime_bull_ratio'] = signal.get('regime_bull_ratio', 0)
            
            all_themes.append(theme_item)
    
    print(f"Found {len(all_themes)} total signals/themes")
    
    # Apply meta-labeling filter if available and enabled
    if HAS_META_LABELING and use_meta_labeling:
        try:
            print("\nApplying meta-labeling filter...")
            meta_filter = MetaLabelingFilter()
            
            # Convert theme items to signal format for filtering
            signals_for_filtering = []
            for theme_item in all_themes:
                signal = {
                    'theme': theme_item['theme'],
                    'signal_type': theme_item['signal_type'],
                    'signal_strength': theme_item['signal_strength'],
                    'tier': theme_item.get('tier'),
                    'leadership_gap': theme_item.get('leadership_gap'),
                    'change': theme_item.get('fiedler_change'),
                    'pct_change': theme_item.get('pct_change'),
                    'current_fiedler': None,  # Will be extracted from features
                    'week_before_fiedler': None
                }
                signals_for_filtering.append((signal, theme_item))
            
            # Filter signals
            filtered_signals = meta_filter.filter_signals(
                [s[0] for s in signals_for_filtering],
                signal_date,
                use_basic_features=True
            )
            
            # Keep only themes that passed meta-labeling
            filtered_theme_names = {s['theme'] for s in filtered_signals}
            all_themes = [t for t in all_themes if t['theme'] in filtered_theme_names]
            
            print(f"  Meta-labeling filtered to {len(all_themes)} themes")
        except Exception as e:
            print(f"  Warning: Meta-labeling failed: {e}, using all themes")
    
    # Filter: TIER 1, TIER 2, and top cohesion
    tier1_themes = [t for t in all_themes if t['tier'] == 1]
    tier2_themes = [t for t in all_themes if t['tier'] == 2]
    cohesion_themes = [t for t in all_themes if t['signal_type'] == 'cohesion' and t['tier'] is None]
    
    # Take top 5 cohesion by signal strength
    top_cohesion = sorted(cohesion_themes, key=lambda x: x['signal_strength'], reverse=True)[:5]
    
    focused_themes = tier1_themes + tier2_themes + top_cohesion
    
    # Remove duplicates (same theme with different signal types)
    seen_themes = set()
    unique_focused = []
    for theme in focused_themes:
        if theme['theme'] not in seen_themes:
            unique_focused.append(theme)
            seen_themes.add(theme['theme'])
    
    focused_themes = unique_focused
    
    # Sort by tier priority, then signal strength
    def sort_key(t):
        tier_priority = 0 if t['tier'] == 1 else (1 if t['tier'] == 2 else 2)
        return (tier_priority, -t['signal_strength'])
    
    focused_themes.sort(key=sort_key)
    
    print(f"\nSelected themes:")
    print(f"  TIER 1: {len(tier1_themes)}")
    print(f"  TIER 2: {len(tier2_themes)}")
    print(f"  Top Cohesion: {len(top_cohesion)}")
    print(f"  Total (unique): {len(focused_themes)}")
    
    # Load ticker data
    db_df = pd.read_csv(DB_FILE)
    ticker_to_name = dict(zip(db_df['tickers'], db_df['name']))
    
    # Get all unique tickers
    all_tickers = set()
    for theme in focused_themes:
        all_tickers.update(theme['tickers'])
    
    # Generate focused report
    if output_file is None:
        date_str = start_date.replace('-', '')
        output_file = backtest_dir / "reports" / f"focused_portfolio_{date_str}.md"
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Focused Portfolio: Alternative Allocation (20/20/60) Strategy\n\n")
        f.write(f"**Analysis Date**: {start_date}\n")
        f.write(f"**Strategy**: Alternative Allocation (20% week 1, 20% week 2, 60% week 7 if valid)\n")
        f.write(f"**Exit Target**: 20% return or 12 weeks\n")
        f.write(f"**Portfolio Focus**: TIER 1 + TIER 2 + Top 5 Cohesion Signals\n")
        f.write(f"**Total Themes**: {len(focused_themes)}\n\n")
        f.write("---\n\n")
        
        f.write("## Portfolio Summary\n\n")
        f.write(f"- **TIER 1 Themes**: {len(tier1_themes)} (Highest Priority - Buy NOW)\n")
        f.write(f"- **TIER 2 Themes**: {len(tier2_themes)} (Accumulate 6-12 months)\n")
        f.write(f"- **Top Cohesion Signals**: {len([t for t in focused_themes if t['signal_type'] == 'cohesion' and t['tier'] is None])}\n")
        f.write(f"- **Themes Valid at Week 7**: {sum(1 for t in focused_themes if t['valid_at_week7'])} ({sum(1 for t in focused_themes if t['valid_at_week7'])/len(focused_themes)*100:.1f}%)\n\n")
        f.write(f"- **Total Unique Tickers**: {len(all_tickers)}\n\n")
        
        f.write("---\n\n")
        
        # Portfolio table
        f.write("## Focused Portfolio Themes\n\n")
        if any('regime_avg_bull_pct' in t for t in focused_themes):
            f.write("| Rank | Theme | Signal Type | Tier | Strength | Bull % | Trend | Momentum | Valid W7 | Tickers |\n")
            f.write("|------|-------|-------------|------|----------|--------|-------|----------|----------|---------|\n")
            
            for rank, theme in enumerate(focused_themes, 1):
                tier_str = f"TIER {int(theme['tier'])}" if theme['tier'] else "-"
                valid_str = "✅" if theme['valid_at_week7'] else "❌"
                bull_pct = f"{theme.get('regime_avg_bull_pct', 0):.1f}%" if 'regime_avg_bull_pct' in theme else "-"
                trend = f"{theme.get('regime_avg_trend', 0):.2f}" if 'regime_avg_trend' in theme else "-"
                momentum = f"{theme.get('regime_avg_momentum', 0):.2f}" if 'regime_avg_momentum' in theme else "-"
                f.write(f"| {rank} | {theme['theme'][:30]} | {theme['signal_type']} | {tier_str} | "
                       f"{theme['signal_strength']:.2f} | {bull_pct} | {trend} | {momentum} | {valid_str} | "
                       f"{theme['n_tickers']} |\n")
        else:
            f.write("| Rank | Theme | Signal Type | Tier | Strength | Valid W7 | Tickers |\n")
            f.write("|------|-------|-------------|------|----------|----------|---------|\n")
            
            for rank, theme in enumerate(focused_themes, 1):
                tier_str = f"TIER {int(theme['tier'])}" if theme['tier'] else "-"
                valid_str = "✅" if theme['valid_at_week7'] else "❌"
                f.write(f"| {rank} | {theme['theme'][:35]} | {theme['signal_type']} | {tier_str} | "
                       f"{theme['signal_strength']:.2f} | {valid_str} | "
                       f"{theme['n_tickers']} |\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        # Detailed theme information
        f.write("## Detailed Theme Information\n\n")
        
        for rank, theme in enumerate(focused_themes, 1):
            f.write(f"### {rank}. {theme['theme']}\n\n")
            f.write(f"- **Signal Type**: {theme['signal_type']}\n")
            tier_display = f"TIER {int(theme['tier'])}" if theme['tier'] else 'N/A'
            f.write(f"- **Tier**: {tier_display}\n")
            f.write(f"- **Signal Strength**: {theme['signal_strength']:.2f}\n")
            if theme['fiedler_change']:
                f.write(f"- **Fiedler Change**: {theme['fiedler_change']:.2f} ({theme['pct_change']:.1f}%)\n")
            if theme['leadership_gap']:
                f.write(f"- **Leadership Gap**: {theme['leadership_gap']:.1f}%\n")
            if 'regime_avg_bull_pct' in theme:
                f.write(f"- **Regime Metrics**:\n")
                f.write(f"  - Average Bull %: {theme['regime_avg_bull_pct']:.1f}%\n")
                f.write(f"  - Average Trend Strength: {theme.get('regime_avg_trend', 0):.3f}\n")
                f.write(f"  - Average Momentum Score: {theme.get('regime_avg_momentum', 0):.3f}\n")
                f.write(f"  - Bull Ratio: {theme.get('regime_bull_ratio', 0)*100:.1f}%\n")
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
        f.write("## Implementation Strategy\n\n")
        f.write("For each theme in the portfolio:\n\n")
        f.write("1. **Week 1**: Buy 20% of allocated position size\n")
        f.write("2. **Week 2**: Buy additional 20% (total 40%)\n")
        f.write("3. **Week 7**: If signal still valid, buy remaining 60%\n")
        f.write("4. **Exit**: When return reaches 20% OR after 12 weeks (whichever comes first)\n\n")
        
        valid_count = sum(1 for t in focused_themes if t['valid_at_week7'])
        f.write(f"**Note**: Only {valid_count} theme(s) ({valid_count/len(focused_themes)*100:.1f}%) remain valid at week 7, ")
        f.write("so most positions will only have 40% deployed (60% cash).\n\n")
        
        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"\nFocused portfolio report saved: {output_file}")
    print(f"Selected {len(focused_themes)} focused themes")
    print(f"Total unique tickers: {len(all_tickers)}")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate focused portfolio report')
    parser.add_argument('--date', type=str, default='2025-08-01',
                       help='Start date for portfolio (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path')
    parser.add_argument('--no-meta-labeling', action='store_true',
                       help='Disable meta-labeling filter')
    
    args = parser.parse_args()
    
    generate_focused_portfolio(args.date, args.output, use_meta_labeling=not args.no_meta_labeling)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
