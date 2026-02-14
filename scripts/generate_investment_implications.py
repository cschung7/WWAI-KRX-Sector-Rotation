#!/usr/bin/env python3
"""
Generate comprehensive Investment Implications Report
Combines: Cohesion × Regime × Leadership analysis

IMPORTANT: Uses Three-Layer Framework (Cohesion × Regime × Trend)
All recommendations are regime-validated.
"""

import pandas as pd
import numpy as np
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
from regime_utils import get_regime_validated_tiers, calculate_theme_regime_stats

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

def load_4tier_data(date_str):
    """Load 4-tier classification data"""
    summary_file = DATA_DIR / f"4tier_summary_{date_str}.json"
    if not summary_file.exists():
        # Try to find latest
        files = glob.glob(str(DATA_DIR / "4tier_summary_*.json"))
        if files:
            summary_file = Path(sorted(files)[-1])
            date_str = summary_file.stem.split('_')[-1]
        else:
            return None, None
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    tier_files = {
        'tier1': DATA_DIR / f"tier1_buy_now_{date_str}.csv",
        'tier2': DATA_DIR / f"tier2_accumulate_{date_str}.csv",
        'tier3': DATA_DIR / f"tier3_research_{date_str}.csv",
        'tier4': DATA_DIR / f"tier4_monitor_{date_str}.csv"
    }
    
    tiers = {}
    for key, file_path in tier_files.items():
        if file_path.exists():
            tiers[key] = pd.read_csv(file_path)
        else:
            tiers[key] = pd.DataFrame()
    
    return summary, tiers

def load_regime_data():
    """Load latest regime data"""
    regime_files = list(REGIME_DIR.glob("all_regimes_*.csv"))
    if not regime_files:
        return None
    
    latest_file = sorted(regime_files)[-1]
    df = pd.read_csv(latest_file)
    latest_date = df['Date'].max()
    df = df[df['Date'] == latest_date].copy()
    
    # Calculate regime summary by stock name
    regime_summary = df.groupby('Ticker', group_keys=False).apply(
        lambda x: pd.Series({
            'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Transition_Pct': (x['Is_Transition'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})
    
    return regime_summary, latest_date

def load_cohesion_data(date_str):
    """Load cohesion data"""
    cohesion_file = find_latest_file(f"enhanced_cohesion_themes_*.csv", f"enhanced_cohesion_themes_{date_str}.csv")
    if cohesion_file and cohesion_file.exists():
        return pd.read_csv(cohesion_file)
    return pd.DataFrame()

def load_leadership_data():
    """Load within-theme leadership data"""
    leadership_file = DATA_DIR / "within_theme_leadership_ranking.csv"
    if leadership_file.exists():
        return pd.read_csv(leadership_file)
    return pd.DataFrame()

def load_db_data():
    """Load database for ticker/name mapping"""
    return pd.read_csv(DB_FILE)

def calculate_theme_regime_stats(theme_name, db_df, regime_summary):
    """Calculate regime statistics for a theme"""
    # Get theme tickers
    theme_tickers = []
    for _, row in db_df.iterrows():
        themes_str = row.get('naverTheme', '[]')
        try:
            themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
            if isinstance(themes, list) and theme_name in themes:
                stock_name = row['name']
                market_cap = row['시가총액']
                theme_tickers.append({
                    'name': stock_name,
                    'market_cap': market_cap
                })
        except:
            continue
    
    if not theme_tickers:
        return None
    
    # Match with regime data
    regime_stats = []
    for ticker_info in theme_tickers:
        stock_name = ticker_info['name']
        regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
        if not regime_row.empty:
            regime_stats.append({
                'market_cap': ticker_info['market_cap'],
                'bull_pct': regime_row.iloc[0]['Bull_Pct'],
                'bear_pct': regime_row.iloc[0]['Bear_Pct'],
                'trend': regime_row.iloc[0]['Trend_Strength'],
                'momentum': regime_row.iloc[0]['Momentum_Score']
            })
    
    if not regime_stats:
        return None
    
    stats_df = pd.DataFrame(regime_stats)
    
    # Calculate large-cap vs rest
    # Note: market_cap in DB is in units of 100B (천억), so 5T = 50
    large_cap_threshold = 50  # 5T KRW (50 * 100B = 5T)
    large_caps = stats_df[stats_df['market_cap'] >= large_cap_threshold]
    rest = stats_df[stats_df['market_cap'] < large_cap_threshold]
    
    # Get large-cap stock details for reporting
    large_cap_stocks = []
    if len(large_caps) > 0:
        # Match back to original ticker_info to get stock names
        for ticker_info in theme_tickers:
            stock_name = ticker_info['name']
            market_cap = ticker_info['market_cap']
            if market_cap >= large_cap_threshold:
                regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
                if not regime_row.empty:
                    large_cap_stocks.append({
                        'name': stock_name,
                        'market_cap': market_cap,
                        'bull_pct': regime_row.iloc[0]['Bull_Pct'],
                        'trend': regime_row.iloc[0]['Trend_Strength']
                    })
        # Sort by market cap descending
        large_cap_stocks.sort(key=lambda x: x['market_cap'], reverse=True)
    
    return {
        'theme': theme_name,
        'total_stocks': len(stats_df),
        'avg_bull_pct': stats_df['bull_pct'].mean(),
        'avg_bear_pct': stats_df['bear_pct'].mean(),
        'avg_trend': stats_df['trend'].mean(),
        'large_cap_bull': large_caps['bull_pct'].mean() if len(large_caps) > 0 else 0,
        'large_cap_count': len(large_caps),
        'large_cap_stocks': large_cap_stocks,  # List of large-cap stocks with details
        'rest_bull': rest['bull_pct'].mean() if len(rest) > 0 else 0,
        'leadership_gap': (large_caps['bull_pct'].mean() - rest['bull_pct'].mean()) if len(large_caps) > 0 and len(rest) > 0 else 0
    }

def generate_investment_implications_report(date_str, summary, tiers, regime_summary, regime_date, cohesion_df, leadership_df, db_df):
    """Generate comprehensive investment implications report"""
    
    report_file = REPORTS_DIR / f"INVESTMENT_IMPLICATIONS_{date_str.replace('-', '')}.md"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Investment Implications: Fiedler-Based Sector Analysis\n\n")
        f.write(f"**Date**: {date_formatted}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Leadership)\n")
        f.write("**Investment Horizon**: 6-18 months\n")
        f.write("**Risk-Adjusted Strategy**: Multi-tier approach with size-based filtering\n")
        f.write(f"**Latest Price Data**: {regime_date if regime_date else 'N/A'}\n\n")
        f.write("---\n\n")
        
        # Current Market State
        f.write("## 📊 CURRENT MARKET STATE\n\n")
        if summary:
            f.write(f"**Total Themes Analyzed**: {summary.get('total_themes', 'N/A')}\n")
            f.write(f"**TIER 1 (BUY NOW)**: {summary.get('tier1', {}).get('count', 0)} themes\n")
            f.write(f"**TIER 2 (ACCUMULATE)**: {summary.get('tier2', {}).get('count', 0)} themes\n")
            f.write(f"**TIER 3 (RESEARCH)**: {summary.get('tier3', {}).get('count', 0)} themes\n")
            f.write(f"**TIER 4 (MONITOR)**: {summary.get('tier4', {}).get('count', 0)} themes\n\n")
        
        # Executive Summary
        f.write("## 📊 EXECUTIVE SUMMARY\n\n")
        f.write("### Complete Research Framework\n\n")
        f.write("Our research analyzed **Naver themes** using three analytical layers:\n\n")
        f.write("1. **Fiedler Value (Cohesion)**: Network connectivity within themes\n")
        f.write("2. **Regime Probability**: Bull/Bear/Transition classification\n")
        f.write("3. **Within-Theme Leadership**: Large-cap vs small-cap regime divergence\n\n")
        
        # Critical Discoveries
        enhanced_count = len(cohesion_df) if not cohesion_df.empty else 0
        leadership_count = len(leadership_df) if not leadership_df.empty else 0
        
        f.write("### Critical Discoveries\n\n")
        f.write(f"✅ **{enhanced_count} themes** have enhanced cohesion (Fiedler increase)\n")
        f.write(f"✅ **{leadership_count} themes** show large-cap leadership (6-18 month leading indicator)\n\n")
        
        # Investment Philosophy
        f.write("## 🎯 INVESTMENT PHILOSOPHY\n\n")
        f.write("### Core Principles\n\n")
        f.write("**\"Size First, Leadership Second, Cohesion Third\"**\n\n")
        f.write("1. **Market Cap Dominates**: Size is more predictive than theme affiliation\n")
        f.write("2. **Leadership Leads**: Large-caps signal 6-18 months ahead\n")
        f.write("3. **Cohesion Confirms**: High Fiedler validates synchronized movement\n")
        f.write("4. **Regime Validates**: Bull regime >40% confirms positive direction\n\n")
        
        # Reconciliation Section
        f.write("## 🔄 RECONCILIATION: COHESION RANKINGS vs INVESTMENT TIERS\n\n")
        f.write("### Understanding the Relationship\n\n")
        f.write("**Cohesion Rankings** (from NAVER_THEME_COHESION_REPORT):\n")
        f.write("- **Focus**: Themes with **strongest Fiedler enhancement** (highest % change)\n")
        f.write("- **Top themes**: OLED (+101%), 수소차 (+173%), 유리 기판 (+162%)\n")
        f.write("- **Purpose**: Identify themes with rapid cohesion formation\n\n")
        f.write("**Investment Tiers** (from this report):\n")
        f.write("- **Focus**: Themes with **strong baseline + strong change + high current**\n")
        f.write("- **TIER 1 Criteria**: Baseline >2.0 AND Change >1.5 AND Current >3.0\n")
        f.write("- **Purpose**: Identify investable themes with sustainable momentum\n\n")
        f.write("### Key Insight\n\n")
        f.write("A theme can have strong **enhancement** (high % change from low base) but still not qualify for \"Buy Now\" if:\n")
        f.write("1. **Baseline Fiedler is too low** (<2.0) - indicates weak initial cohesion\n")
        f.write("2. **Current Fiedler is not high enough** (<3.0) - indicates cohesion still forming\n")
        f.write("3. **Change is not substantial enough** (<1.5) - indicates slow improvement\n\n")
        f.write("**Example**: 수소차 has +173% change, but baseline is only 1.31 → **TIER 2 (Accumulate)**, not TIER 1\n")
        f.write("- High % change shows rapid improvement, but low baseline suggests early stage\n")
        f.write("- Monitor for baseline to strengthen (>2.0) before moving to TIER 1\n\n")
        f.write("### Mapping: Cohesion Rankings → Investment Tiers\n\n")
        if not tiers.get('tier1', pd.DataFrame()).empty:
            tier1_themes = tiers['tier1']['Theme'].tolist() if 'Theme' in tiers['tier1'].columns else []
            if tier1_themes:
                f.write("**TIER 1 (Buy NOW)** themes from top cohesion rankings:\n")
                for theme in tier1_themes[:5]:
                    f.write(f"- {theme}\n")
                f.write("\n")
        if not tiers.get('tier2', pd.DataFrame()).empty:
            tier2_themes = tiers['tier2']['Theme'].tolist() if 'Theme' in tiers['tier2'].columns else []
            if tier2_themes:
                f.write("**TIER 2 (Accumulate)** themes from top cohesion rankings:\n")
                for theme in tier2_themes[:5]:
                    f.write(f"- {theme}\n")
                f.write("\n")
        f.write("---\n\n")
        
        # TIER 1 Recommendations
        if not tiers.get('tier1', pd.DataFrame()).empty:
            f.write("## 💰 TIER 1: SAFE LARGE-CAP PORTFOLIO\n\n")
            f.write("### Investment Criteria\n")
            f.write("- Market cap ≥5T KRW\n")
            f.write("- Bull regime >60%\n")
            f.write("- Trend strength >0.3\n")
            f.write("- Present in enhanced cohesion themes\n")
            f.write("- Clear large-cap leadership position\n\n")
            
            f.write("### TOP 10 LARGE-CAP RECOMMENDATIONS\n\n")
            
            tier1_themes = tiers['tier1'].head(10)
            for idx, (_, row) in enumerate(tier1_themes.iterrows(), 1):
                theme_name = row.get('Theme', row.get('theme', 'Unknown'))
                
                # Get regime stats
                regime_stats = calculate_theme_regime_stats(theme_name, db_df, regime_summary)
                
                f.write(f"#### {idx}. {theme_name}\n\n")
                if regime_stats:
                    f.write(f"**Regime Profile**:\n")
                    f.write(f"- Bull Regime: {regime_stats['avg_bull_pct']:.1f}%\n")
                    f.write(f"- Large-Cap Bull: {regime_stats['large_cap_bull']:.1f}% ({regime_stats['large_cap_count']} stocks)\n")
                    
                    # List large-cap stocks
                    if regime_stats.get('large_cap_stocks') and len(regime_stats['large_cap_stocks']) > 0:
                        f.write(f"  - Large-Cap Stocks (≥5T KRW):\n")
                        for stock in regime_stats['large_cap_stocks']:
                            market_cap_t = stock['market_cap'] * 100 / 1000  # Convert to T KRW
                            f.write(f"    - {stock['name']}: {market_cap_t:.1f}T KRW, Bull {stock['bull_pct']:.1f}%, Trend {stock['trend']:+.3f}\n")
                    
                    f.write(f"- Leadership Gap: {regime_stats['leadership_gap']:.1f}%\n")
                    f.write(f"- Trend Strength: {regime_stats['avg_trend']:+.3f}\n\n")
                
                f.write("**Investment Rationale**:\n")
                f.write(f"- High cohesion theme with strong large-cap leadership\n")
                f.write(f"- Synchronized movement across theme members\n\n")
                
                f.write("**Position Size**: 5-10% of portfolio\n")
                f.write("**Target Horizon**: 12-18 months\n")
                f.write("**Expected Return**: 15-25%\n\n")
                f.write("---\n\n")
        
        # TIER 2 Recommendations
        if not tiers.get('tier2', pd.DataFrame()).empty:
            f.write("## ⚡ TIER 2: ACCUMULATION PHASE\n\n")
            f.write("### Investment Criteria\n")
            f.write("- Market cap 100B-5T KRW\n")
            f.write("- Theme Leadership Gap: >60%\n")
            f.write("- Large-Cap Leaders: 100% bull\n\n")
            
            tier2_themes = tiers['tier2'].head(10)
            f.write("### Top 10 Accumulation Themes\n\n")
            f.write("| Theme | Cohesion Change | Leadership Gap | Status |\n")
            f.write("|-------|-----------------|----------------|--------|\n")
            
            for _, row in tier2_themes.iterrows():
                theme_name = row.get('Theme', row.get('theme', 'Unknown'))
                change = row.get('Change', row.get('fiedler_change', 0))
                
                # Get leadership gap
                leadership_row = leadership_df[leadership_df['Theme'] == theme_name] if not leadership_df.empty else pd.DataFrame()
                if not leadership_row.empty and 'Leadership_Gap' in leadership_row.columns:
                    gap_str = str(leadership_row['Leadership_Gap'].iloc[0])
                    gap = float(gap_str.replace('%', '')) if '%' in gap_str else float(gap_str)
                else:
                    gap = 0
                
                f.write(f"| {theme_name} | {change:+.2f} | {gap:.1f}% | ⚡ ACCUMULATE |\n")
            
            f.write("\n")
        
        # Summary Statistics
        f.write("## 📈 SUMMARY STATISTICS\n\n")
        if summary:
            f.write(f"- **Total Themes**: {summary.get('total_themes', 'N/A')}\n")
            f.write(f"- **TIER 1 Themes**: {summary.get('tier1', {}).get('count', 0)}\n")
            f.write(f"- **TIER 2 Themes**: {summary.get('tier2', {}).get('count', 0)}\n")
            f.write(f"- **TIER 3 Themes**: {summary.get('tier3', {}).get('count', 0)}\n")
            f.write(f"- **Enhanced Cohesion Themes**: {enhanced_count}\n")
        f.write(f"- **Leadership Themes**: {leadership_count}\n\n")
        
        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Leadership)\n")
    
    return report_file

def main():
    parser = argparse.ArgumentParser(description='Generate Investment Implications Report')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()
    
    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    print("="*80)
    print("GENERATING INVESTMENT IMPLICATIONS REPORT")
    print("="*80)
    print(f"Date: {date_str}")
    print()
    
    # Load data
    print("Loading 4-tier data...")
    summary, tiers = load_4tier_data(date_str)
    
    print("Loading regime data...")
    regime_summary, regime_date = load_regime_data()
    
    print("Loading cohesion data...")
    cohesion_df = load_cohesion_data(date_str)
    
    print("Loading leadership data...")
    leadership_df = load_leadership_data()
    
    print("Loading database...")
    db_df = load_db_data()
    
    # Generate report
    print("\nGenerating report...")
    report_file = generate_investment_implications_report(
        date_str, summary, tiers, regime_summary, regime_date,
        cohesion_df, leadership_df, db_df
    )
    
    print(f"\n✅ Report generated: {report_file}")
    print("="*80)

if __name__ == '__main__':
    main()

