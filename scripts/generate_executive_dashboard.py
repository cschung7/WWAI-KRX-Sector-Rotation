#!/usr/bin/env python3
"""
Generate Executive Dashboard - One-Page Summary
Target: C-suite, Portfolio Managers
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

# Configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR, AUTOGLUON_BASE_DIR, DB_FILE, REGIME_DIR
from regime_utils import get_regime_validated_tiers, load_cohesion_data, load_regime_data

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
    """Load 4-tier summary (regime-validated)"""
    summary_file = DATA_DIR / f"4tier_summary_{date_str}.json"
    if not summary_file.exists():
        files = glob.glob(str(DATA_DIR / "4tier_summary_*.json"))
        if files:
            summary_file = Path(sorted(files)[-1])
        else:
            return None

    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_leadership_data():
    """Load leadership data"""
    leadership_file = DATA_DIR / "within_theme_leadership_ranking.csv"
    if leadership_file.exists():
        return pd.read_csv(leadership_file)
    return pd.DataFrame()

def generate_executive_dashboard(date_str, summary, validated_tiers, cohesion_df, leadership_df, regime_date):
    """Generate one-page executive dashboard with regime-validated recommendations"""

    report_file = REPORTS_DIR / f"EXECUTIVE_DASHBOARD_{date_str.replace('-', '')}.md"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str

    # Get tier data from regime-validated tiers
    buy_now = validated_tiers.get('buy_now', pd.DataFrame())
    watchlist = validated_tiers.get('watchlist', pd.DataFrame())
    avoid = validated_tiers.get('avoid', pd.DataFrame())

    tier1_count = len(buy_now)
    tier2_count = len(watchlist)
    tier4_count = len(avoid)

    # Get leadership count
    leadership_count = len(leadership_df) if not leadership_df.empty else 0
    enhanced_count = len(cohesion_df) if not cohesion_df.empty else 0

    # Calculate market state
    if not leadership_df.empty and 'Leadership_Gap' in leadership_df.columns:
        avg_leadership_gap = leadership_df['Leadership_Gap'].str.replace('%', '').astype(float).mean()
    else:
        avg_leadership_gap = 0

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# 🎯 KRX SECTOR ROTATION DASHBOARD\n\n")
        f.write(f"**Week of**: {date_formatted} | **Data as of**: {regime_date if regime_date else 'N/A'}\n\n")
        f.write("**Framework**: Three-Layer (Cohesion × Regime × Trend) - All recommendations regime-validated\n\n")
        f.write("---\n\n")

        # Market State Summary
        f.write("## 📊 MARKET STATE\n\n")
        f.write(f"| Metric | Value |\n")
        f.write(f"|--------|-------|\n")
        f.write(f"| **BUY NOW (Bull >60%, Trend >0.1)** | {tier1_count} |\n")
        f.write(f"| **WATCHLIST (Bull 40-60%)** | {tier2_count} |\n")
        f.write(f"| **AVOID (Bear >60%)** | {tier4_count} |\n")
        f.write(f"| **Total Themes Analyzed** | {validated_tiers.get('counts', {}).get('total', 'N/A')} |\n\n")

        # BUY NOW Section
        f.write("## 🟢 BUY NOW (Regime-Validated)\n\n")
        if tier1_count > 0:
            f.write(f"**{tier1_count} themes with Bull >60% AND Trend >0.1**\n\n")
            for i, (_, row) in enumerate(buy_now.head(5).iterrows(), 1):
                theme = row['theme']
                bull_pct = row.get('avg_bull_pct', 0)
                trend = row.get('avg_trend', 0)
                fiedler = row.get('fiedler', 0)

                f.write(f"**{i}. {theme}**\n")
                f.write(f"- Bull: {bull_pct:.1f}% | Trend: {trend:+.3f} | Fiedler: {fiedler:.2f}\n")
                f.write(f"- **Action**: Enter positions this week (5-10% allocation)\n\n")
            if tier1_count > 5:
                f.write(f"*... and {tier1_count - 5} more themes*\n\n")
        else:
            f.write("**No themes currently meet BUY NOW criteria (Bull >60%, Trend >0.1)**\n\n")
        
        # WATCHLIST Section
        f.write("## ⚡ WATCHLIST (Monitor for Entry)\n\n")
        if tier2_count > 0:
            f.write(f"**{tier2_count} themes with Bull 40-60%**\n\n")
            f.write("Enter when Bull >60% AND Trend >0.3\n\n")
            for i, (_, row) in enumerate(watchlist.head(5).iterrows(), 1):
                theme = row['theme']
                bull_pct = row.get('avg_bull_pct', 0)
                trend = row.get('avg_trend', 0)

                f.write(f"**{i}. {theme}**\n")
                f.write(f"- Bull: {bull_pct:.1f}% | Trend: {trend:+.3f}\n")
                f.write(f"- **Action**: Monitor weekly, enter when Bull >60%\n\n")
            if tier2_count > 5:
                f.write(f"*... and {tier2_count - 5} more themes on watchlist*\n\n")
        else:
            f.write("**No themes currently on watchlist**\n\n")

        # AVOID Section
        f.write("## 🚫 AVOID (Bear Regime)\n\n")
        if tier4_count > 0:
            f.write(f"**{tier4_count} themes with Bear >60% - AVOID long positions**\n\n")
            for i, (_, row) in enumerate(avoid.head(3).iterrows(), 1):
                theme = row['theme']
                bear_pct = row.get('avg_bear_pct', 0)
                trend = row.get('avg_trend', 0)

                f.write(f"- {theme}: Bear {bear_pct:.1f}%, Trend {trend:+.3f}\n")
            if tier4_count > 3:
                f.write(f"\n*... and {tier4_count - 3} more themes to avoid*\n\n")
        else:
            f.write("**No themes in strong bear regime**\n\n")

        # Key Insights
        f.write("## 💡 KEY INSIGHTS\n\n")
        f.write(f"- **{tier1_count} themes** regime-validated for investment (Bull >60%, Trend >0.1)\n")
        f.write(f"- **{tier2_count} themes** on watchlist - monitor for regime shift\n")
        f.write(f"- **{tier4_count} themes** in bear territory - avoid or consider shorts\n")
        f.write("- Three-layer validation ensures alignment across Cohesion, Regime, and Trend\n\n")

        # Risk Warning
        f.write("## ⚠️  CRITICAL NOTE\n\n")
        f.write("**All recommendations are regime-validated using Three-Layer Framework:**\n")
        f.write("- Cohesion (Fiedler): Network strength\n")
        f.write("- Regime: Bull/Bear probability (>60% required for BUY)\n")
        f.write("- Trend: Momentum direction (>0.1 required for BUY)\n\n")

        # Quick Actions
        f.write("## 🎯 QUICK ACTIONS\n\n")
        f.write("1. **BUY NOW themes**: Review and enter positions this week\n")
        f.write("2. **WATCHLIST themes**: Set alerts for Bull >60%\n")
        f.write("3. **AVOID themes**: Check for short opportunities\n")
        f.write("4. **Daily Check**: Monitor ABNORMAL_SECTORS for regime changes\n\n")

        f.write("---\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("**Framework**: Three-Layer Analysis (Cohesion × Regime × Trend)\n")

    return report_file

def main():
    parser = argparse.ArgumentParser(description='Generate Executive Dashboard (Regime-Validated)')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()

    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    print("="*80)
    print("GENERATING EXECUTIVE DASHBOARD (Regime-Validated)")
    print("="*80)
    print(f"Date: {date_str}")
    print()

    # Load regime-validated tiers
    print("Loading regime-validated tiers...")
    validated_tiers = get_regime_validated_tiers(date_str)
    print(f"  BUY NOW: {validated_tiers['counts']['buy_now']} themes")
    print(f"  WATCHLIST: {validated_tiers['counts']['watchlist']} themes")
    print(f"  AVOID: {validated_tiers['counts']['avoid']} themes")

    print("Loading 4-tier summary...")
    summary = load_4tier_summary(date_str)

    print("Loading cohesion data...")
    cohesion_df = load_cohesion_data(date_str)

    print("Loading leadership data...")
    leadership_df = load_leadership_data()

    regime_date = validated_tiers.get('regime_date')

    # Generate dashboard
    print("\nGenerating dashboard...")
    report_file = generate_executive_dashboard(
        date_str, summary, validated_tiers, cohesion_df, leadership_df, regime_date
    )

    print(f"\n✅ Dashboard generated: {report_file}")
    print("="*80)

if __name__ == '__main__':
    main()

