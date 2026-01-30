#!/usr/bin/env python3
"""
Generate Executive Summary Report
Critical findings: Safe/avoid/watchlist themes
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
            'Transition_Pct': (x['Is_Transition'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})
    
    return regime_summary, latest_date

def load_cohesion_data(date_str):
    """Load cohesion data for specific date, fallback to latest if not found"""
    # First try the specific date file
    specific_file = DATA_DIR / f"enhanced_cohesion_themes_{date_str}.csv"
    if specific_file.exists():
        return pd.read_csv(specific_file)
    
    # If specific date file doesn't exist, try to find latest
    cohesion_file = find_latest_file(f"enhanced_cohesion_themes_*.csv", f"enhanced_cohesion_themes_{date_str}.csv")
    if cohesion_file and cohesion_file.exists():
        print(f"  ⚠️  Warning: Using latest available cohesion file: {cohesion_file.name} (requested: {date_str})")
        return pd.read_csv(cohesion_file)
    return pd.DataFrame()

def load_db_data():
    """Load database"""
    return pd.read_csv(DB_FILE)

def calculate_theme_regime_stats(theme_name, db_df, regime_summary):
    """Calculate regime statistics for a theme"""
    theme_tickers = []
    for _, row in db_df.iterrows():
        themes_str = row.get('naverTheme', '[]')
        try:
            themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
            if isinstance(themes, list) and theme_name in themes:
                stock_name = row['name']
                theme_tickers.append(stock_name)
        except:
            continue
    
    if not theme_tickers:
        return None
    
    regime_stats = []
    for stock_name in theme_tickers:
        regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
        if not regime_row.empty:
            regime_stats.append({
                'bull_pct': regime_row.iloc[0]['Bull_Pct'],
                'bear_pct': regime_row.iloc[0]['Bear_Pct'],
                'trend': regime_row.iloc[0]['Trend_Strength']
            })
    
    if not regime_stats:
        return None
    
    stats_df = pd.DataFrame(regime_stats)
    
    return {
        'theme': theme_name,
        'avg_bull_pct': stats_df['bull_pct'].mean(),
        'avg_bear_pct': stats_df['bear_pct'].mean(),
        'avg_trend': stats_df['trend'].mean(),
        'stock_count': len(stats_df)
    }

def generate_executive_summary_report(date_str, cohesion_df, regime_summary, regime_date, db_df):
    """Generate executive summary report"""
    
    report_file = REPORTS_DIR / f"EXECUTIVE_SUMMARY_{date_str.replace('-', '')}.md"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str
    
    # Calculate theme regime stats
    theme_regime_stats = []
    if not cohesion_df.empty:
        for _, row in cohesion_df.iterrows():
            theme_name = row.get('theme', 'Unknown')
            stats = calculate_theme_regime_stats(theme_name, db_df, regime_summary)
            if stats:
                stats['fiedler'] = row.get('current_fiedler', 0)
                stats['fiedler_change'] = row.get('fiedler_change', 0)
                theme_regime_stats.append(stats)
    
    theme_stats_df = pd.DataFrame(theme_regime_stats)
    
    # Categorize themes
    safe_themes = theme_stats_df[
        (theme_stats_df['avg_bull_pct'] > 60) & 
        (theme_stats_df['avg_trend'] > 0.1)
    ].sort_values('avg_bull_pct', ascending=False)
    
    watchlist_themes = theme_stats_df[
        (theme_stats_df['avg_bull_pct'] >= 40) & 
        (theme_stats_df['avg_bull_pct'] < 60) &
        (theme_stats_df['avg_trend'] > -0.2)
    ].sort_values('avg_bull_pct', ascending=False)
    
    avoid_themes = theme_stats_df[
        (theme_stats_df['avg_bear_pct'] > 60) | 
        (theme_stats_df['avg_trend'] < -0.3)
    ].sort_values('avg_bear_pct', ascending=False)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Executive Summary: Cohesion vs Regime Analysis\n\n")
        f.write(f"**Date**: {date_formatted}\n")
        f.write(f"**Critical Finding**: {'MAJOR MISMATCH DETECTED' if len(avoid_themes) > len(safe_themes) else 'POSITIVE ALIGNMENT'}\n\n")
        f.write("---\n\n")
        
        # Bottom Line
        f.write("## 🚨 BOTTOM LINE\n\n")
        enhanced_count = len(cohesion_df) if not cohesion_df.empty else 0
        safe_count = len(safe_themes)
        avoid_count = len(avoid_themes)
        watchlist_count = len(watchlist_themes)
        
        f.write(f"**The enhanced cohesion analysis identified {enhanced_count} themes with strengthening internal correlations.**\n\n")
        f.write("### Critical Numbers:\n")
        f.write(f"- **{safe_count} themes** are investable (bull >60%, trend >0.1)\n")
        f.write(f"- **{watchlist_count} themes** on watchlist (bull 40-60%)\n")
        f.write(f"- **{avoid_count} themes** have >60% bear regime or strong negative trend\n")
        if not theme_stats_df.empty:
            f.write(f"- **Average**: {theme_stats_df['avg_bull_pct'].mean():.1f}% bull, {theme_stats_df['avg_bear_pct'].mean():.1f}% bear\n")
        f.write("\n")
        
        # Safe to Invest
        if not safe_themes.empty:
            f.write("## ✅ SAFE TO INVEST\n\n")
            for idx, (_, row) in enumerate(safe_themes.head(10).iterrows(), 1):
                f.write(f"### {idx}. {row['theme']}\n")
                f.write(f"- **Fiedler**: {row['fiedler']:.2f} (Cohesion: {'Strong' if row['fiedler'] > 2.0 else 'Moderate'})\n")
                f.write(f"- **Bull Regime**: {row['avg_bull_pct']:.1f}%\n")
                f.write(f"- **Trend**: {row['avg_trend']:+.3f}\n")
                f.write(f"- **Verdict**: ✅ **SAFE THEMATIC PLAY**\n\n")
        else:
            f.write("## ✅ SAFE TO INVEST\n\n")
            f.write("**No themes currently meet safe investment criteria (bull >60%, trend >0.1)**\n\n")
        
        # Watchlist
        if not watchlist_themes.empty:
            f.write("## ⚠️ WAIT FOR REGIME SHIFT\n\n")
            f.write("### Watchlist (High Cohesion, But Currently Bearish/Mixed)\n\n")
            f.write("| Theme | Fiedler | Bull % | Bear % | Trend | Status |\n")
            f.write("|-------|---------|--------|--------|-------|--------|\n")
            
            for _, row in watchlist_themes.head(10).iterrows():
                status = "⏳ WAIT"
                f.write(f"| {row['theme']} | {row['fiedler']:.2f} | {row['avg_bull_pct']:.1f}% | {row['avg_bear_pct']:.1f}% | {row['avg_trend']:+.3f} | {status} |\n")
            
            f.write("\n**Action**: Monitor daily. Enter when bull % > 60% AND trend > 0.3\n\n")
        
        # Avoid
        if not avoid_themes.empty:
            f.write("## ❌ AVOID / CONSIDER SHORTING\n\n")
            f.write("### High Cohesion BUT Strong Bear Regimes\n\n")
            f.write("| Theme | Fiedler | Bull % | Bear % | Trend | Status |\n")
            f.write("|-------|---------|--------|--------|-------|--------|\n")
            
            for _, row in avoid_themes.head(10).iterrows():
                if row['avg_bear_pct'] > 70:
                    status = "🚫 STRONG BEAR"
                elif row['avg_trend'] < -0.5:
                    status = "🚫 NEGATIVE TREND"
                else:
                    status = "⚠️ AVOID"
                f.write(f"| {row['theme']} | {row['fiedler']:.2f} | {row['avg_bull_pct']:.1f}% | {row['avg_bear_pct']:.1f}% | {row['avg_trend']:+.3f} | {status} |\n")
            
            f.write("\n**Action**: AVOID long positions. Consider shorts or inverse ETFs.\n\n")
        
        # Key Insight
        f.write("## 💡 KEY INSIGHT\n\n")
        f.write("### Enhanced Cohesion ≠ Bullish Signal\n\n")
        f.write("**What High Fiedler Values Mean**:\n")
        f.write("- ✅ Stocks move together (synchronized)\n")
        f.write("- ✅ Theme structure is strong\n")
        f.write("- ❌ **DOES NOT** mean upward movement\n")
        f.write("- ❌ **DOES NOT** mean positive returns\n\n")
        
        f.write("**Current Reality**:\n")
        if avoid_count > safe_count:
            f.write("- Themes ARE cohesive (high Fiedler)\n")
            f.write("- BUT moving TOGETHER DOWNWARD\n")
            f.write("- \"Coordinated decline\" across most themes\n\n")
        else:
            f.write("- Themes ARE cohesive (high Fiedler)\n")
            f.write("- AND showing positive regime alignment\n")
            f.write("- \"Coordinated strength\" emerging\n\n")
        
        # Recommended Framework
        f.write("## 📊 RECOMMENDED INVESTMENT FRAMEWORK\n\n")
        f.write("### Composite Scoring Formula:\n")
        f.write("```\n")
        f.write("Investment Score = (Fiedler × 0.3) + (Bull % × 0.4) + (Trend × 0.2) + (Momentum × 0.1)\n")
        f.write("```\n\n")
        f.write("**Threshold**: Score > 25 to invest\n\n")
        
        # Conclusion
        f.write("## 🎯 CONCLUSION\n\n")
        f.write(f"**Investment implications from the enhanced cohesion analysis:**\n\n")
        f.write(f"- ✅ **{safe_count} themes safe**: Investable with bull >60%\n")
        f.write(f"- ⚠️ **{watchlist_count} themes watchlist**: Monitor for regime shift\n")
        f.write(f"- ❌ **{avoid_count} themes bearish**: Avoid or short\n\n")
        f.write("**Never invest based on cohesion (Fiedler) values alone.**\n")
        f.write("**Always cross-check with regime probabilities and trend strength.**\n\n")
        
        f.write("---\n\n")
        f.write(f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Data as of**: {regime_date if regime_date else 'N/A'}\n")
    
    return report_file

def main():
    parser = argparse.ArgumentParser(description='Generate Executive Summary Report')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()
    
    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    print("="*80)
    print("GENERATING EXECUTIVE SUMMARY REPORT")
    print("="*80)
    print(f"Date: {date_str}")
    print()
    
    # Load data
    print("Loading regime data...")
    regime_summary, regime_date = load_regime_data()
    
    print("Loading cohesion data...")
    cohesion_df = load_cohesion_data(date_str)
    
    print("Loading database...")
    db_df = load_db_data()
    
    # Generate report
    print("\nGenerating report...")
    report_file = generate_executive_summary_report(
        date_str, cohesion_df, regime_summary, regime_date, db_df
    )
    
    print(f"\n✅ Report generated: {report_file}")
    print("="*80)

if __name__ == '__main__':
    main()

