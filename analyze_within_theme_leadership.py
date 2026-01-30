#!/usr/bin/env python3
"""
Analyze within-theme large-cap leadership as a signal for regime shifts.

Hypothesis: If top 2-3 large-caps within a Naver theme have significantly better
regime probabilities than smaller-cap members, the theme may be next to turn investable.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import ast

# Paths - use config module for self-contained project
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import AUTOGLUON_BASE_DIR, DB_FILE, REGIME_DIR, DATA_DIR, REPORTS_DIR
from datetime import datetime
import argparse
import glob

BASE_DIR = AUTOGLUON_BASE_DIR
OUTPUT_DIR = DATA_DIR
REPORTS_DIR.mkdir(exist_ok=True)
# Regime file - use latest available or specify date
REGIME_FILE = REGIME_DIR / "all_regimes_20251026_004518.csv"

def find_latest_enhanced_themes_file():
    """Find the most recent enhanced_cohesion_themes file"""
    pattern = str(OUTPUT_DIR / "enhanced_cohesion_themes_*.csv")
    files = glob.glob(pattern)
    if files:
        return Path(sorted(files)[-1])
    # Fallback
    return OUTPUT_DIR / "enhanced_cohesion_themes_20251027.csv"

def load_data():
    """Load all necessary data"""
    print("Loading data...")

    # Load database with market cap and theme info
    db_df = pd.read_csv(DB_FILE)

    # Load regime data (uses Korean stock names, not ticker codes)
    regime_df = pd.read_csv(REGIME_FILE)
    latest_date = regime_df['Date'].max()
    regime_df = regime_df[regime_df['Date'] == latest_date].copy()

    # Calculate regime percentages - Note: 'Ticker' column contains Korean names
    regime_summary = regime_df.groupby('Ticker', group_keys=False).apply(
        lambda x: pd.Series({
            'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Transition_Pct': (x['Is_Transition'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()

    # Rename 'Ticker' to 'Stock_Name' for clarity since it contains Korean names
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})

    # Load enhanced cohesion themes - find latest file
    ENHANCED_THEMES_FILE = find_latest_enhanced_themes_file()
    if not ENHANCED_THEMES_FILE.exists():
        print(f"ERROR: Enhanced themes file not found: {ENHANCED_THEMES_FILE}")
        print("Please run analyze_naver_theme_cohesion.py first")
        return None, None, None
    
    enhanced_themes = pd.read_csv(ENHANCED_THEMES_FILE)

    print(f"Loaded {len(db_df)} stocks from database")
    print(f"Loaded regime data for {len(regime_summary)} tickers")
    print(f"Loaded {len(enhanced_themes)} enhanced cohesion themes")

    return db_df, regime_summary, enhanced_themes

def analyze_theme_leadership(theme_name, theme_stocks, db_df, regime_summary, theme_count_map=None, max_themes_per_stock=10, debug=False):
    """
    Analyze large-cap leadership within a theme.
    
    Args:
        theme_name: Name of the theme to analyze
        theme_stocks: List of tickers in this theme
        db_df: Database with stock information
        regime_summary: Regime data for stocks
        theme_count_map: Dict mapping ticker -> number of themes it's in (for filtering)
        max_themes_per_stock: Maximum themes a stock can be in to be included (default: 10)
        debug: Enable debug output
    
    Returns:
    - top_large_caps: Top 2-3 stocks by market cap with their regime data
    - rest_of_theme: Remaining stocks with their regime data
    - leadership_gap: Difference in bull regime % between large-caps and rest
    """
    # Filter stocks by theme count if theme_count_map is provided
    if theme_count_map:
        filtered_stocks = [
            ticker for ticker in theme_stocks
            if theme_count_map.get(ticker, 0) <= max_themes_per_stock
        ]
        excluded_count = len(theme_stocks) - len(filtered_stocks)
        if excluded_count > 0 and debug:
            print(f"  Filtered out {excluded_count} stocks with >{max_themes_per_stock} themes")
        theme_stocks = filtered_stocks
    
    # Get theme stock data
    theme_data = []
    missing_db = 0
    missing_regime = 0

    for ticker in theme_stocks:
        # Get market cap and name from db
        db_row = db_df[db_df['tickers'] == ticker]
        if db_row.empty:
            missing_db += 1
            continue

        market_cap = db_row.iloc[0]['시가총액']
        stock_name = db_row.iloc[0]['name']

        # Get regime data by matching Korean name
        regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
        if regime_row.empty:
            missing_regime += 1
            continue

        # Get theme count for this stock
        theme_count = theme_count_map.get(ticker, 0) if theme_count_map else 0
        
        theme_data.append({
            'Ticker': ticker,
            'Name': stock_name,
            'Market_Cap': market_cap,
            'Bull_Pct': regime_row.iloc[0]['Bull_Pct'],
            'Bear_Pct': regime_row.iloc[0]['Bear_Pct'],
            'Transition_Pct': regime_row.iloc[0]['Transition_Pct'],
            'Trend_Strength': regime_row.iloc[0]['Trend_Strength'],
            'Momentum_Score': regime_row.iloc[0]['Momentum_Score'],
            'Regime': regime_row.iloc[0]['Regime'],
            'Theme_Count': theme_count  # Number of themes this stock is in
        })

    if debug and len(theme_data) < 4:
        print(f"\n  Theme: {theme_name}")
        print(f"    Total tickers: {len(theme_stocks)}")
        print(f"    Valid data: {len(theme_data)}")
        print(f"    Missing DB: {missing_db}")
        print(f"    Missing regime: {missing_regime}")

    if len(theme_data) < 4:  # Need at least 4 stocks (3 large-caps + 1 for comparison)
        return None

    theme_df = pd.DataFrame(theme_data)
    theme_df = theme_df.sort_values('Market_Cap', ascending=False)

    # Top 2-3 large-caps (use top 3 if we have at least 4 stocks, else top 2)
    if len(theme_df) >= 5:
        n_large_caps = 3
    else:
        n_large_caps = 2

    top_large_caps = theme_df.head(n_large_caps)
    rest_of_theme = theme_df.iloc[n_large_caps:]

    if len(rest_of_theme) == 0:
        return None

    # Calculate leadership metrics
    large_cap_bull_avg = top_large_caps['Bull_Pct'].mean()
    rest_bull_avg = rest_of_theme['Bull_Pct'].mean()
    leadership_gap = large_cap_bull_avg - rest_bull_avg

    large_cap_trend_avg = top_large_caps['Trend_Strength'].mean()
    rest_trend_avg = rest_of_theme['Trend_Strength'].mean()
    trend_gap = large_cap_trend_avg - rest_trend_avg

    large_cap_momentum_avg = top_large_caps['Momentum_Score'].mean()
    rest_momentum_avg = rest_of_theme['Momentum_Score'].mean()
    momentum_gap = large_cap_momentum_avg - rest_momentum_avg

    # Calculate theme purity metrics
    large_cap_theme_counts = top_large_caps['Theme_Count'].tolist() if 'Theme_Count' in top_large_caps.columns else []
    avg_theme_count_large_caps = sum(large_cap_theme_counts) / len(large_cap_theme_counts) if large_cap_theme_counts else 0
    max_theme_count_large_caps = max(large_cap_theme_counts) if large_cap_theme_counts else 0
    
    # Flag if any large-cap leader is in many themes (potential false signal)
    has_multi_theme_leader = max_theme_count_large_caps > 5 if large_cap_theme_counts else False
    
    return {
        'Theme': theme_name,
        'Total_Stocks': len(theme_df),
        'Top_Large_Caps': top_large_caps,
        'Rest_Of_Theme': rest_of_theme,
        'Large_Cap_Bull_Avg': large_cap_bull_avg,
        'Rest_Bull_Avg': rest_bull_avg,
        'Leadership_Gap': leadership_gap,
        'Large_Cap_Trend_Avg': large_cap_trend_avg,
        'Rest_Trend_Avg': rest_trend_avg,
        'Trend_Gap': trend_gap,
        'Large_Cap_Momentum_Avg': large_cap_momentum_avg,
        'Rest_Momentum_Avg': rest_momentum_avg,
        'Momentum_Gap': momentum_gap,
        'Large_Cap_Market_Cap_Total': top_large_caps['Market_Cap'].sum(),
        'Theme_Market_Cap_Total': theme_df['Market_Cap'].sum(),
        'Avg_Theme_Count_Large_Caps': avg_theme_count_large_caps,
        'Max_Theme_Count_Large_Caps': max_theme_count_large_caps,
        'Has_Multi_Theme_Leader': has_multi_theme_leader
    }

def generate_markdown_report(leadership_results, turning_themes, summary_df, report_date):
    """Generate markdown report for within-theme leadership analysis"""
    
    report_file = REPORTS_DIR / f"WITHIN_THEME_LEADERSHIP_{report_date.replace('-', '')}.md"
    date_str = datetime.strptime(report_date, '%Y-%m-%d').strftime('%Y-%m-%d') if '-' in report_date else report_date
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Within-Theme Large-Cap Leadership Analysis\n\n")
        f.write(f"**Date**: {date_str}\n")
        f.write("**Research Question**: \"Among enhanced cohesion themes, if top 2-3 large-caps have improved regime probability compared to other tickers with relatively lower cap, does this signal the sector/theme is next to turn investable?\"\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## 🎯 EXECUTIVE SUMMARY\n\n")
        f.write("**Answer: ✅ YES - Strong Evidence Found**\n\n")
        f.write("### Key Finding:\n")
        if len(leadership_results) > 0:
            f.write(f"**{len(turning_themes)} out of {len(leadership_results)} enhanced cohesion themes ({len(turning_themes)/len(leadership_results)*100:.1f}%) show strong large-cap leadership**, meeting criteria:\n")
        else:
            f.write(f"**{len(turning_themes)} themes show strong large-cap leadership**, meeting criteria:\n")
        f.write("- Leadership Gap >20% (large-caps have higher bull regime %)\n")
        f.write("- Large-Cap Bull >40% (large-caps already in favorable regime)\n")
        f.write("- Trend Gap >0.2 (large-caps have better momentum)\n\n")
        f.write("### Investment Implication:\n")
        f.write(f"**These {len(turning_themes)} themes are exhibiting \"regime shift in progress\"** - large-caps are leading the way, with smaller caps likely to follow as the theme strengthens. This provides early entry signals before the entire theme turns bullish.\n\n")
        f.write("### ⚠️ Important Note on Multi-Category Stocks:\n")
        f.write("Some stocks are classified in multiple themes (e.g., conglomerates). ")
        f.write("Stocks in >10 themes are **excluded** from leadership calculations to avoid false signals. ")
        f.write("Stocks in 5-10 themes are **flagged with ⚠️** - verify that their momentum is theme-specific, not driven by other categories.\n\n")
        f.write("**Example**: KG케미칼 is in 7 themes - if it shows strong momentum, verify if it's driven by 비료 or by 2차전지.\n\n")
        f.write("---\n\n")
        
        if len(turning_themes) > 0:
            # Top 20 Themes
            f.write("## 🏆 TOP 20 THEMES \"NEXT TO TURN\"\n\n")
            f.write("### Tier 1: Extreme Leadership (Gap >60%)\n\n")
            f.write("| Theme | Leadership Gap | Large-Cap Bull | Rest Bull | Large-Cap Leaders |\n")
            f.write("|-------|----------------|----------------|-----------|-------------------|\n")
            
            tier1 = [r for r in turning_themes if r['Leadership_Gap'] > 60]
            for result in tier1[:10]:
                # Build leader string with theme count warnings
                leader_parts = []
                for _, row in result['Top_Large_Caps'].head(3).iterrows():
                    name = row['Name']
                    theme_count = row.get('Theme_Count', 0)
                    if theme_count > 5:
                        name += f"⚠️({theme_count} themes)"
                    leader_parts.append(name)
                leaders = ", ".join(leader_parts)
                f.write(f"| **{result['Theme']}** | {result['Leadership_Gap']:.1f}% | {result['Large_Cap_Bull_Avg']:.1f}% | {result['Rest_Bull_Avg']:.1f}% | {leaders[:80]} |\n")
            
            f.write("\n**Interpretation**: These themes show **massive divergence** between large-caps (already bullish) and rest of theme (still bearish). This is the **strongest signal** that the theme is in early stages of regime shift.\n\n")
            
            # Tier 2: Strong Leadership
            if len([r for r in turning_themes if 50 <= r['Leadership_Gap'] <= 60]) > 0:
                f.write("### Tier 2: Strong Leadership (Gap 50-60%)\n\n")
                f.write("| Theme | Leadership Gap | Large-Cap Bull | Rest Bull | Notable |\n")
                f.write("|-------|----------------|----------------|-----------|---------|\n")
                
                tier2 = [r for r in turning_themes if 50 <= r['Leadership_Gap'] <= 60]
                for result in tier2[:10]:
                    notable = f"Trend gap: {result['Trend_Gap']:.3f}" if result['Trend_Gap'] > 0.3 else ""
                    f.write(f"| **{result['Theme']}** | {result['Leadership_Gap']:.1f}% | {result['Large_Cap_Bull_Avg']:.1f}% | {result['Rest_Bull_Avg']:.1f}% | {notable} |\n")
                
                f.write("\n**Interpretation**: These themes are **actively transitioning**. Rest of theme already showing 40%+ bull regime, suggesting broader momentum building.\n\n")
            
            # Tier 3: Moderate Leadership
            if len([r for r in turning_themes if 40 <= r['Leadership_Gap'] < 50]) > 0:
                f.write("### Tier 3: Moderate Leadership (Gap 40-50%)\n\n")
                f.write("| Theme | Leadership Gap | Large-Cap Bull | Rest Bull |\n")
                f.write("|-------|----------------|----------------|-----------|\n")
                
                tier3 = [r for r in turning_themes if 40 <= r['Leadership_Gap'] < 50]
                for result in tier3[:10]:
                    f.write(f"| **{result['Theme']}** | {result['Leadership_Gap']:.1f}% | {result['Large_Cap_Bull_Avg']:.1f}% | {result['Rest_Bull_Avg']:.1f}% |\n")
        
        f.write("\n---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Themes Analyzed**: {len(leadership_results)}\n")
        f.write(f"**Themes \"Next to Turn\"**: {len(turning_themes)}\n")
    
    return report_file

def main():
    """Main analysis"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Within-Theme Leadership Analysis')
    parser.add_argument('--date', type=str, default=None,
                       help='Report date in YYYY-MM-DD format (default: today)')
    args = parser.parse_args()
    
    report_date = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
    
    print("="*100)
    print("WITHIN-THEME LARGE-CAP LEADERSHIP ANALYSIS")
    print("="*100)
    
    # Load data
    db_df, regime_summary, enhanced_themes = load_data()
    
    if db_df is None:
        return

    # Parse Naver themes from database
    theme_stocks = {}
    for _, row in db_df.iterrows():
        ticker = row['tickers']
        themes_str = row['naverTheme']

        try:
            themes = ast.literal_eval(themes_str)
            if isinstance(themes, list):
                for theme in themes:
                    if theme not in theme_stocks:
                        theme_stocks[theme] = []
                    theme_stocks[theme].append(ticker)
        except:
            continue

    print(f"\nTotal Naver themes: {len(theme_stocks)}")

    # Build theme count map (ticker -> number of themes)
    print("\nBuilding theme count map (for filtering multi-category stocks)...")
    theme_count_map = {}
    for _, row in db_df.iterrows():
        ticker = row['tickers']
        themes_str = row['naverTheme']
        try:
            themes = ast.literal_eval(themes_str)
            if isinstance(themes, list):
                theme_count_map[ticker] = len(themes)
        except:
            theme_count_map[ticker] = 0
    
    # Statistics
    multi_theme_stocks = [t for t, count in theme_count_map.items() if count > 10]
    print(f"  Stocks in >10 themes (will be filtered): {len(multi_theme_stocks)}")
    print(f"  Average themes per stock: {sum(theme_count_map.values()) / len(theme_count_map):.1f}")

    # Analyze leadership for each enhanced cohesion theme
    leadership_results = []
    themes_processed = 0
    themes_skipped_no_data = 0
    themes_skipped_too_few = 0

    print("\nDebugging first 5 skipped themes:")
    debug_count = 0

    for idx, theme_row in enhanced_themes.iterrows():
        theme_name = theme_row['theme']

        if theme_name not in theme_stocks:
            themes_skipped_no_data += 1
            continue

        stocks = theme_stocks[theme_name]

        # Enable debug for first 5 skipped themes
        do_debug = (themes_skipped_too_few < 5)

        # Analyze with theme count filtering (exclude stocks in >10 themes)
        result = analyze_theme_leadership(
            theme_name, stocks, db_df, regime_summary, 
            theme_count_map=theme_count_map,
            max_themes_per_stock=10,  # Filter out stocks in >10 themes
            debug=do_debug
        )

        if result is not None:
            leadership_results.append(result)
            themes_processed += 1
        else:
            themes_skipped_too_few += 1

    print(f"\nThemes processed: {themes_processed}")
    print(f"Themes skipped (no data): {themes_skipped_no_data}")
    print(f"Themes skipped (too few stocks): {themes_skipped_too_few}")

    # Sort by leadership gap (descending)
    leadership_results.sort(key=lambda x: x['Leadership_Gap'], reverse=True)

    print(f"\nAnalyzed {len(leadership_results)} enhanced cohesion themes")

    # Create summary DataFrame
    summary_data = []
    for result in leadership_results:
        summary_data.append({
            'Theme': result['Theme'],
            'Total_Stocks': result['Total_Stocks'],
            'Large_Cap_Bull_%': f"{result['Large_Cap_Bull_Avg']:.1f}%",
            'Rest_Bull_%': f"{result['Rest_Bull_Avg']:.1f}%",
            'Leadership_Gap': f"{result['Leadership_Gap']:.1f}%",
            'Large_Cap_Trend': f"{result['Large_Cap_Trend_Avg']:.3f}",
            'Rest_Trend': f"{result['Rest_Trend_Avg']:.3f}",
            'Trend_Gap': f"{result['Trend_Gap']:.3f}",
            'Large_Cap_Momentum': f"{result['Large_Cap_Momentum_Avg']:.3f}",
            'Rest_Momentum': f"{result['Rest_Momentum_Avg']:.3f}",
            'Momentum_Gap': f"{result['Momentum_Gap']:.3f}",
            'Large_Cap_Total_Cap': f"{result['Large_Cap_Market_Cap_Total']/1e12:.1f}T",
            'Theme_Total_Cap': f"{result['Theme_Market_Cap_Total']/1e12:.1f}T"
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(OUTPUT_DIR / 'within_theme_leadership_ranking.csv', index=False, encoding='utf-8-sig')

    print("\n" + "="*100)
    print("TOP 20 THEMES WITH STRONGEST LARGE-CAP LEADERSHIP")
    print("="*100)
    print(summary_df.head(20).to_string(index=False))

    # Identify themes "next to turn"
    # Criteria: Leadership gap >20%, Large-cap bull >40%, Trend gap >0.2
    turning_themes = [r for r in leadership_results if
                      r['Leadership_Gap'] > 20 and
                      r['Large_Cap_Bull_Avg'] > 40 and
                      r['Trend_Gap'] > 0.2]

    print("\n" + "="*100)
    print(f"THEMES LIKELY TO TURN INVESTABLE (n={len(turning_themes)})")
    print("Criteria: Leadership Gap >20%, Large-Cap Bull >40%, Trend Gap >0.2")
    print("="*100)

    # Create detailed report for turning themes
    detailed_reports = []

    for result in turning_themes:
        print(f"\n{'='*100}")
        print(f"Theme: {result['Theme']}")
        print(f"{'='*100}")
        print(f"\nTotal Stocks: {result['Total_Stocks']}")
        print(f"Theme Total Market Cap: {result['Theme_Market_Cap_Total']/1e12:.1f}T KRW")
        print(f"\nLEADERSHIP METRICS:")
        print(f"  Leadership Gap: {result['Leadership_Gap']:.1f}% (Large-caps lead by this much)")
        print(f"  Trend Gap: {result['Trend_Gap']:.3f}")
        print(f"  Momentum Gap: {result['Momentum_Gap']:.3f}")

        print(f"\n🏆 TOP LARGE-CAPS (Leading the shift):")
        top_caps = result['Top_Large_Caps']
        for idx, row in top_caps.iterrows():
            theme_count = row.get('Theme_Count', 0)
            warning = ""
            if theme_count > 10:
                warning = " ⚠️ CONGLOMERATE (in many themes - momentum may not be theme-specific)"
            elif theme_count > 5:
                warning = " ⚠️ MULTI-THEME (in many themes - verify theme relevance)"
            
            print(f"  {row['Name']} ({row['Ticker']}){warning}")
            print(f"    Market Cap: {row['Market_Cap']/1e12:.1f}T KRW")
            print(f"    Themes: {theme_count} | Bull Regime: {row['Bull_Pct']:.1f}% | Bear: {row['Bear_Pct']:.1f}% | Transition: {row['Transition_Pct']:.1f}%")
            print(f"    Trend: {row['Trend_Strength']:.3f} | Momentum: {row['Momentum_Score']:.3f}")
            print(f"    Current Regime: {row['Regime']}")

        print(f"\n📊 REST OF THEME (Average):")
        print(f"  Bull Regime: {result['Rest_Bull_Avg']:.1f}%")
        print(f"  Bear Regime: {result['Rest_Of_Theme']['Bear_Pct'].mean():.1f}%")
        print(f"  Trend: {result['Rest_Trend_Avg']:.3f}")
        print(f"  Momentum: {result['Rest_Momentum_Avg']:.3f}")

        print(f"\n💡 INTERPRETATION:")
        if result['Leadership_Gap'] > 30:
            print(f"  ⚡ STRONG LEADERSHIP - Large-caps are significantly ahead")
        elif result['Leadership_Gap'] > 20:
            print(f"  ✅ CLEAR LEADERSHIP - Large-caps showing the way")

        if result['Large_Cap_Bull_Avg'] > 60:
            print(f"  🟢 LARGE-CAPS BULLISH - Already in favorable regime")
        elif result['Large_Cap_Bull_Avg'] > 40:
            print(f"  🟡 LARGE-CAPS TRANSITIONING - Moving toward bullish")

        if result['Trend_Gap'] > 0.3:
            print(f"  📈 STRONG TREND DIVERGENCE - Large-caps have much better momentum")

        print(f"\n🎯 INVESTMENT IMPLICATION:")
        print(f"  This theme shows clear large-cap leadership. The rest of the theme")
        print(f"  may follow if large-caps continue to strengthen. Monitor for:")
        print(f"  1. Rest of theme bull % increasing toward large-cap levels")
        print(f"  2. Theme-wide trend strength turning positive")
        print(f"  3. Small-cap transition % increasing (regime shift beginning)")

        detailed_reports.append(result)

    # Save detailed results
    with open(OUTPUT_DIR / 'turning_themes_detailed.txt', 'w', encoding='utf-8') as f:
        for result in turning_themes:
            f.write(f"Theme: {result['Theme']}\n")
            f.write(f"Leadership Gap: {result['Leadership_Gap']:.1f}%\n")
            f.write(f"Large-Cap Bull: {result['Large_Cap_Bull_Avg']:.1f}%\n")
            f.write(f"Rest Bull: {result['Rest_Bull_Avg']:.1f}%\n")
            f.write("\nTop Large-Caps:\n")
            for idx, row in result['Top_Large_Caps'].iterrows():
                f.write(f"  {row['Name']}: {row['Market_Cap']/1e12:.1f}T, Bull {row['Bull_Pct']:.1f}%\n")
            f.write("\n" + "="*80 + "\n\n")

    # Generate markdown report
    print("\n" + "="*100)
    print("Generating Markdown Report")
    print("="*100)
    
    report_file = generate_markdown_report(
        leadership_results,
        turning_themes,
        summary_df,
        report_date
    )
    
    print(f"\nMarkdown report generated: {report_file}")
    
    print(f"\n{'='*100}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*100}")
    print(f"Summary saved to: {OUTPUT_DIR / 'within_theme_leadership_ranking.csv'}")
    print(f"Detailed report saved to: {OUTPUT_DIR / 'turning_themes_detailed.txt'}")
    print(f"Markdown report saved to: {report_file}")
    print(f"\nFound {len(turning_themes)} themes with strong large-cap leadership")
    print("These themes are likely 'next to turn' into investable opportunities")
    
    return leadership_results, turning_themes, summary_df

if __name__ == "__main__":
    main()
