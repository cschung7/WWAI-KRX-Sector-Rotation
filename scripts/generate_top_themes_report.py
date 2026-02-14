#!/usr/bin/env python3
"""
Generate Top Investment Themes Report
Three-Layer Framework: Cohesion × Regime × Large-Cap Leadership
"""

import pandas as pd
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
            'bear_pct': regime_row.iloc[0]['Bear_Pct'],
            'trend': regime_row.iloc[0]['Trend_Strength'],
            'momentum': regime_row.iloc[0]['Momentum_Score'],
            'regime': regime_row.iloc[0]['Regime']
        }
    return None

def calculate_theme_score(theme_name, cohesion_row, leadership_row, db_df, regime_summary):
    """Calculate composite score for theme"""
    # Cohesion score (0-3)
    fiedler = cohesion_row.get('current_fiedler', 0) if not cohesion_row.empty else 0
    cohesion_score = min(fiedler / 2.0, 3.0)  # Cap at 3.0
    
    # Leadership score (0-3)
    if not leadership_row.empty and 'Leadership_Gap' in leadership_row.columns:
        gap_str = str(leadership_row['Leadership_Gap'].iloc[0])
        gap = float(gap_str.replace('%', '')) if '%' in gap_str else float(gap_str)
        leadership_score = min(gap / 20.0, 3.0)  # Cap at 3.0
    else:
        leadership_score = 0
    
    # Regime score (0-4)
    theme_stocks = get_theme_stocks(theme_name, db_df)
    if not theme_stocks.empty:
        # Get large-cap stocks (>=5T)
        # Note: market_cap in DB is in units of 100B (천억), so 5T = 50
        large_caps = theme_stocks[theme_stocks['market_cap'] >= 50]
        if not large_caps.empty:
            bull_pcts = []
            for _, stock in large_caps.iterrows():
                regime = get_stock_regime(stock['name'], regime_summary)
                if regime:
                    bull_pcts.append(regime['bull_pct'])
            if bull_pcts:
                avg_bull = sum(bull_pcts) / len(bull_pcts)
                regime_score = min(avg_bull / 25.0, 4.0)  # Cap at 4.0
            else:
                regime_score = 0
        else:
            regime_score = 0
    else:
        regime_score = 0
    
    total_score = cohesion_score + leadership_score + regime_score
    return total_score, cohesion_score, leadership_score, regime_score

def generate_top_themes_report(date_str, cohesion_df, leadership_df, db_df, regime_summary):
    """Generate top investment themes report"""
    
    report_file = REPORTS_DIR / f"TOP_THEMES_INVESTMENT_READY_{date_str.replace('-', '')}.md"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str
    
    # Calculate scores for all themes
    theme_scores = []
    for _, cohesion_row in cohesion_df.iterrows():
        theme_name = cohesion_row.get('theme', 'Unknown')
        
        # Find matching leadership data
        leadership_row = leadership_df[leadership_df['Theme'] == theme_name] if not leadership_df.empty else pd.DataFrame()
        
        # Calculate composite score
        total_score, cohesion_score, leadership_score, regime_score = calculate_theme_score(
            theme_name, cohesion_row, leadership_row, db_df, regime_summary
        )
        
        theme_scores.append({
            'theme': theme_name,
            'total_score': total_score,
            'cohesion_score': cohesion_score,
            'leadership_score': leadership_score,
            'regime_score': regime_score,
            'fiedler': cohesion_row.get('current_fiedler', 0),
            'fiedler_change': cohesion_row.get('fiedler_change', 0),
            'cohesion_row': cohesion_row,
            'leadership_row': leadership_row
        })
    
    # Sort by total score
    theme_scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# TOP INVESTMENT THEMES\n\n")
        f.write(f"**Date**: {date_formatted}\n")
        f.write("## Based on Three-Layer Framework: Cohesion × Regime × Large-Cap Leadership\n\n")
        f.write("---\n\n")
        
        # Top 10 Themes
        for rank, theme_data in enumerate(theme_scores[:10], 1):
            theme_name = theme_data['theme']
            f.write(f"## 🥇 RANK {rank}: {theme_name} - {'STRONGEST SIGNAL' if rank == 1 else 'STRONG SIGNAL'}\n\n")
            
            # Investment Thesis
            f.write("**Investment Thesis**: ")
            if theme_data['cohesion_score'] > 2 and theme_data['leadership_score'] > 2 and theme_data['regime_score'] > 2:
                f.write("✅ ALL THREE LAYERS ALIGN PERFECTLY\n\n")
            elif theme_data['cohesion_score'] > 1.5 and theme_data['leadership_score'] > 1.5:
                f.write("✅ Strong cohesion + Leadership\n\n")
            else:
                f.write("⚠️ Partial alignment - verify regime\n\n")
            
            # Cohesion Analysis
            f.write("### Cohesion Analysis\n")
            f.write(f"- **Current Fiedler**: {theme_data['fiedler']:.2f}\n")
            f.write(f"- **Change**: {theme_data['fiedler_change']:+.2f}\n")
            if theme_data['fiedler'] > 2.0:
                f.write("- **Status**: 📈 Strong cohesion - sector forming tight network\n\n")
            elif theme_data['fiedler'] > 1.0:
                f.write("- **Status**: 📈 Moderate cohesion - network strengthening\n\n")
            else:
                f.write("- **Status**: 📊 Weak cohesion - early stage\n\n")
            
            # Large-Cap Leadership
            f.write("### Large-Cap Leadership (Tier 1: ≥5T)\n\n")
            theme_stocks = get_theme_stocks(theme_name, db_df)
            if not theme_stocks.empty:
                # Note: market_cap in DB is in units of 100B (천억), so 5T = 50
                large_caps = theme_stocks[theme_stocks['market_cap'] >= 50].sort_values('market_cap', ascending=False)
                
                if not large_caps.empty:
                    f.write("| Ticker | Company | Market Cap | Regime | Bull % | Trend | Score |\n")
                    f.write("|--------|---------|------------|--------|--------|-------|-------|\n")
                    
                    for _, stock in large_caps.head(5).iterrows():
                        regime = get_stock_regime(stock['name'], regime_summary)
                        if regime:
                            # Convert from 100B units to T (trillion)
                            market_cap_t = stock['market_cap'] * 0.1  # 100B units to T
                            score = 1.0 if regime['bull_pct'] > 80 else 0.8 if regime['bull_pct'] > 60 else 0.6
                            f.write(f"| {stock['ticker']} | **{stock['name']}** | **{market_cap_t:.1f}T** | {regime['regime']} | {regime['bull_pct']:.0f}% | {regime['trend']:+.3f} | {score:.3f} |\n")
                else:
                    f.write("**No large-cap stocks (≥5T) found in this theme**\n\n")
            else:
                f.write("**No stocks found for this theme**\n\n")
            
            # Investment Action
            f.write("### Investment Action\n")
            if theme_data['total_score'] > 7:
                f.write("✅ **STRONG BUY SIGNAL** - All three layers confirm sector rotation\n")
            elif theme_data['total_score'] > 5:
                f.write("✅ **BUY SIGNAL** - Strong confirmation from multiple layers\n")
            elif theme_data['total_score'] > 3:
                f.write("⚠️ **RESEARCH SIGNAL** - Partial alignment, verify regime shift\n")
            else:
                f.write("⏳ **MONITOR** - Early stage, wait for stronger signals\n")
            
            f.write("\n---\n\n")
        
        # Summary
        f.write("## 📊 SUMMARY\n\n")
        f.write(f"**Total Themes Analyzed**: {len(theme_scores)}\n")
        f.write(f"**Top 10 Themes**: Composite score > {theme_scores[9]['total_score']:.2f}\n")
        f.write(f"**Average Score**: {sum(t['total_score'] for t in theme_scores) / len(theme_scores):.2f}\n\n")
        
        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Leadership)\n")
    
    return report_file

def main():
    parser = argparse.ArgumentParser(description='Generate Top Investment Themes Report')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()
    
    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    print("="*80)
    print("GENERATING TOP INVESTMENT THEMES REPORT")
    print("="*80)
    print(f"Date: {date_str}")
    print()
    
    # Load data
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
    report_file = generate_top_themes_report(
        date_str, cohesion_df, leadership_df, db_df, regime_summary
    )
    
    print(f"\n✅ Report generated: {report_file}")
    print("="*80)

if __name__ == '__main__':
    main()

