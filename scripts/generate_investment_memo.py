#!/usr/bin/env python3
"""
Generate Investment Memo - 2-3 Page Decision-Ready Document
Target: Investment Committee, Analysts
Frequency: Weekly

IMPORTANT: Uses Three-Layer Framework (Cohesion × Regime × Trend)
All recommendations are regime-validated.
"""

import pandas as pd
import json
import argparse
from pathlib import Path
from datetime import datetime
import glob
import ast

# Configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR, AUTOGLUON_BASE_DIR, DB_FILE, REGIME_DIR
from regime_utils import get_regime_validated_tiers, load_db_data

REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

def find_latest_file(pattern, default_date=None):
    """Find latest file matching pattern"""
    files = glob.glob(str(DATA_DIR / pattern))
    if files:
        return Path(sorted(files)[-1])
    if default_date:
        return DATA_DIR / pattern.replace('*', default_date)
    return None

def load_4tier_summary(date_str):
    """Load 4-tier summary"""
    summary_file = DATA_DIR / f"4tier_summary_{date_str}.json"
    if not summary_file.exists():
        files = glob.glob(str(DATA_DIR / "4tier_summary_*.json"))
        if files:
            summary_file = Path(sorted(files)[-1])
        else:
            return None
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_cohesion_data(date_str):
    """Load cohesion data"""
    cohesion_file = find_latest_file(f"enhanced_cohesion_themes_*.csv", f"enhanced_cohesion_themes_{date_str}.csv")
    if cohesion_file and cohesion_file.exists():
        return pd.read_csv(cohesion_file)
    return pd.DataFrame()

def load_leadership_data():
    """Load leadership data"""
    leadership_file = DATA_DIR / "within_theme_leadership_ranking.csv"
    if leadership_file.exists():
        return pd.read_csv(leadership_file)
    return pd.DataFrame()

def load_regime_data():
    """Load latest regime data"""
    regime_files = list(REGIME_DIR.glob("all_regimes_*.csv"))
    if not regime_files:
        return None, None
    
    latest_file = sorted(regime_files)[-1]
    df = pd.read_csv(latest_file)
    latest_date = df['Date'].max()
    df = df[df['Date'] == latest_date].copy()
    
    regime_summary = df.groupby('Ticker', group_keys=False).apply(
        lambda x: pd.Series({
            'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})
    
    return regime_summary, latest_date

def load_db_data():
    """Load database"""
    return pd.read_csv(DB_FILE)

def get_theme_stocks(theme_name, db_df):
    """Get stocks in a theme"""
    theme_stocks = []
    for _, row in db_df.iterrows():
        themes_str = row.get('naverTheme', '[]')
        try:
            themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
            if isinstance(themes, list) and theme_name in themes:
                theme_stocks.append({
                    'ticker': str(row['tickers']).zfill(6),
                    'name': row['name'],
                    'market_cap': row['시가총액']
                })
        except:
            continue
    return pd.DataFrame(theme_stocks)

def get_stock_regime(stock_name, regime_summary):
    """Get regime data for a stock"""
    regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
    if not regime_row.empty:
        return {
            'bull_pct': regime_row.iloc[0]['Bull_Pct'],
            'trend': regime_row.iloc[0]['Trend_Strength'],
            'momentum': regime_row.iloc[0]['Momentum_Score'],
            'regime': regime_row.iloc[0]['Regime']
        }
    return None

def generate_investment_memo(date_str, validated_tiers, regime_summary, regime_date, db_df):
    """Generate investment memo with regime-validated recommendations"""

    report_file = REPORTS_DIR / f"INVESTMENT_MEMO_{date_str.replace('-', '')}.md"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str

    # Get regime-validated data
    buy_now = validated_tiers.get('buy_now', pd.DataFrame())
    watchlist = validated_tiers.get('watchlist', pd.DataFrame())
    avoid = validated_tiers.get('avoid', pd.DataFrame())

    tier1_count = len(buy_now)
    tier2_count = len(watchlist)
    tier4_count = len(avoid)
    total_count = validated_tiers.get('counts', {}).get('total', 0)

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Investment Memo: KRX Sector Rotation\n\n")
        f.write(f"**Date**: {date_formatted}\n")
        f.write(f"**Data as of**: {regime_date if regime_date else 'N/A'}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Trend)\n")
        f.write("**All recommendations regime-validated**\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")

        f.write(f"**Current Market State**: {total_count} themes analyzed. ")
        f.write(f"{tier1_count} themes are regime-validated for immediate investment (Bull >60%, Trend >0.1). ")
        f.write(f"{tier2_count} themes on watchlist (Bull 40-60%). ")
        f.write(f"{tier4_count} themes in bear regime - AVOID.\n\n")

        f.write("**Key Opportunities (Regime-Validated)**:\n")
        for i, (_, row) in enumerate(buy_now.head(3).iterrows(), 1):
            f.write(f"{i}. {row['theme']} (Bull {row['avg_bull_pct']:.1f}%, Trend {row['avg_trend']:+.3f})\n")
        if buy_now.empty:
            f.write("- No themes currently meet BUY criteria\n")
        f.write("\n")

        f.write("**Recommended Action**: Focus on regime-validated BUY NOW themes only. Avoid high cohesion themes with Bear >60%.\n\n")
        f.write("---\n\n")
        
        # Top 3 Investment Themes
        f.write("## Top 3 Investment Themes (Regime-Validated)\n\n")

        for rank, (_, row) in enumerate(buy_now.head(3).iterrows(), 1):
            theme_name = row['theme']
            f.write(f"### Theme {rank}: {theme_name}\n\n")

            # Investment Thesis with regime data
            f.write("**Investment Thesis (Regime-Validated)**:\n")
            f.write(f"- **Bull Regime**: {row['avg_bull_pct']:.1f}% (>60% required)\n")
            f.write(f"- **Trend Strength**: {row['avg_trend']:+.3f} (>0.1 required)\n")
            f.write(f"- **Cohesion (Fiedler)**: {row.get('fiedler', 0):.2f}\n")
            f.write(f"- **Status**: REGIME-VALIDATED BUY\n\n")

            # Large-Cap Leaders
            large_cap_stocks = row.get('large_cap_stocks', [])
            if large_cap_stocks:
                f.write("**Large-Cap Leaders (≥5T KRW)**:\n")
                f.write("| Company | Market Cap | Bull % | Trend |\n")
                f.write("|---------|------------|--------|-------|\n")
                for stock in large_cap_stocks[:5]:
                    f.write(f"| {stock['name']} | {stock['market_cap']:.1f}T | {stock['bull_pct']:.0f}% | {stock['trend']:+.3f} |\n")
                f.write("\n")
            else:
                f.write("**Large-Cap Leaders**: See sector rankings for details\n\n")

            # Entry Strategy
            f.write("**Entry Strategy**:\n")
            f.write("- **Position Size**: 5-10% of portfolio\n")
            f.write("- **Timeline**: Enter positions this week\n")
            f.write("- **Target Horizon**: 12-18 months\n")
            f.write("- **Risk Level**: Low (regime-validated)\n\n")

            f.write("---\n\n")

        if buy_now.empty:
            f.write("**No themes currently meet BUY NOW criteria (Bull >60%, Trend >0.1)**\n\n")
            f.write("Monitor WATCHLIST themes for regime shifts.\n\n")
            f.write("---\n\n")
        
        # Portfolio Recommendations
        f.write("## Portfolio Recommendations\n\n")

        f.write("### Current Allocation Strategy\n\n")
        f.write("**BUY NOW (Regime-Validated)**: Primary allocation\n")
        f.write(f"- {tier1_count} themes with Bull >60% AND Trend >0.1\n")
        f.write("- Focus: Large-cap leaders within each theme\n")
        f.write("- Entry: This week\n\n")

        f.write("**WATCHLIST**: Monitor for entry\n")
        f.write(f"- {tier2_count} themes with Bull 40-60%\n")
        f.write("- Action: Enter when Bull >60% AND Trend >0.3\n")
        f.write("- Entry: When criteria met\n\n")

        f.write("**AVOID**: No long positions\n")
        f.write(f"- {tier4_count} themes with Bear >60%\n")
        f.write("- Action: Avoid or consider shorts\n\n")

        # Risk Metrics
        f.write("### Risk Assessment\n\n")
        f.write("**Three-Layer Validation ensures:**\n")
        f.write("- **Cohesion**: Network strength confirmed\n")
        f.write("- **Regime**: Bull probability >60% for all BUY themes\n")
        f.write("- **Trend**: Positive momentum >0.1 for all BUY themes\n\n")

        # Next Steps
        f.write("### Next Steps\n\n")
        f.write("1. **This Week**: Execute BUY NOW theme positions\n")
        f.write("2. **Daily**: Check regime changes for WATCHLIST themes\n")
        f.write("3. **Weekly**: Review AVOID list for potential shorts\n")
        f.write("4. **Ongoing**: Monitor EXECUTIVE_SUMMARY for regime shifts\n\n")

        f.write("---\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Trend)\n")
        f.write("**All recommendations regime-validated**\n")

    return report_file

def main():
    parser = argparse.ArgumentParser(description='Generate Investment Memo (Regime-Validated)')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()

    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    print("="*80)
    print("GENERATING INVESTMENT MEMO (Regime-Validated)")
    print("="*80)
    print(f"Date: {date_str}")
    print()

    # Load regime-validated tiers
    print("Loading regime-validated tiers...")
    validated_tiers = get_regime_validated_tiers(date_str)
    print(f"  BUY NOW: {validated_tiers['counts']['buy_now']} themes")
    print(f"  WATCHLIST: {validated_tiers['counts']['watchlist']} themes")
    print(f"  AVOID: {validated_tiers['counts']['avoid']} themes")

    print("Loading regime data...")
    regime_summary, regime_date = load_regime_data()

    print("Loading database...")
    db_df = load_db_data()

    # Generate memo
    print("\nGenerating memo...")
    report_file = generate_investment_memo(
        date_str, validated_tiers, regime_summary, regime_date, db_df
    )

    print(f"\n✅ Memo generated: {report_file}")
    print("="*80)

if __name__ == '__main__':
    main()

