#!/usr/bin/env python3
"""
4-Tier Theme Classification with Regime Validation

IMPORTANT: Uses Three-Layer Framework (Cohesion × Regime × Trend)
- Tier 1 (BUY NOW): Bull >60% AND Trend >0.1 (regime-validated)
- Tier 2 (WATCHLIST): Bull 40-60% AND Trend >-0.2
- Tier 3 (RESEARCH): Remaining themes with positive metrics
- Tier 4 (AVOID): Bear >60% OR Trend <-0.3

Previous Fiedler-only classification is DEPRECATED.
Regime validation is now REQUIRED for all tier assignments.
"""

import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime
from pathlib import Path
import glob

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR
from regime_utils import (
    load_cohesion_data,
    load_regime_data,
    load_db_data,
    calculate_theme_regime_stats
)

DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


class FourTierThemeAnalyzer:
    """
    Analyze themes using Three-Layer Framework with regime validation.

    Tier Classification:
    - TIER 1 (BUY NOW): Bull >60% AND Trend >0.1
    - TIER 2 (WATCHLIST): Bull 40-60% AND Trend >-0.2
    - TIER 3 (RESEARCH): Fiedler >1.0 AND not in other tiers
    - TIER 4 (AVOID): Bear >60% OR Trend <-0.3
    """

    def __init__(self, date_str=None):
        if date_str is None:
            date_str = datetime.now().strftime('%Y%m%d')
        self.date_str = date_str
        self.df = None
        self.regime_summary = None
        self.regime_date = None
        self.db_df = None
        self.theme_stats = {}

    def load_data(self):
        """Load cohesion, regime, and database data"""
        print("Loading data...")

        # Load cohesion data
        self.df = load_cohesion_data(self.date_str)
        if self.df.empty:
            print("  WARNING: No cohesion data found!")
            return False
        print(f"  Loaded {len(self.df)} themes with cohesion data")

        # Load regime data
        self.regime_summary, self.regime_date = load_regime_data()
        if self.regime_summary is None:
            print("  WARNING: No regime data found!")
            return False
        print(f"  Loaded regime data as of: {self.regime_date}")

        # Load database
        self.db_df = load_db_data()
        print(f"  Loaded {len(self.db_df)} stocks from database")

        return True

    def calculate_all_theme_stats(self):
        """Calculate regime statistics for all themes"""
        print("\nCalculating theme regime statistics...")

        for _, row in self.df.iterrows():
            theme_name = row.get('theme', row.get('Theme', 'Unknown'))
            stats = calculate_theme_regime_stats(theme_name, self.db_df, self.regime_summary)

            if stats:
                stats['fiedler'] = row.get('current_fiedler', row.get('Last_Week_Fiedler', 0))
                stats['fiedler_change'] = row.get('fiedler_change', row.get('Change', 0))
                stats['baseline_fiedler'] = row.get('baseline_fiedler', row.get('Week_Before_Fiedler', 0))
                stats['pct_change'] = row.get('pct_change', row.get('Pct_Change', 0))
                stats['n_stocks'] = row.get('n_stocks', row.get('Stocks', 0))
                self.theme_stats[theme_name] = stats

        print(f"  Calculated stats for {len(self.theme_stats)} themes")

    def classify_tiers(self):
        """
        Classify themes into 4 tiers using Three-Layer Framework.

        Criteria (regime-validated):
        - TIER 1 (BUY NOW): Bull >60% AND Trend >0.1
        - TIER 2 (WATCHLIST): Bull 40-60% AND Trend >-0.2
        - TIER 3 (RESEARCH): Fiedler >1.0 AND not in other tiers
        - TIER 4 (AVOID): Bear >60% OR Trend <-0.3
        """
        print("\nClassifying themes with Three-Layer Framework...")

        tier1, tier2, tier3, tier4 = [], [], [], []
        classified = set()

        for theme_name, stats in self.theme_stats.items():
            bull_pct = stats['avg_bull_pct']
            bear_pct = stats['avg_bear_pct']
            trend = stats['avg_trend']
            fiedler = stats['fiedler']

            # TIER 4 (AVOID): Bear >60% OR Trend <-0.3
            if bear_pct > 60 or trend < -0.3:
                tier4.append({
                    'Theme': theme_name,
                    'Tier': 4,
                    'Bull_Pct': bull_pct,
                    'Bear_Pct': bear_pct,
                    'Trend': trend,
                    'Fiedler': fiedler,
                    'Fiedler_Change': stats['fiedler_change'],
                    'Stocks': stats['stock_count'],
                    'Status': 'AVOID'
                })
                classified.add(theme_name)

            # TIER 1 (BUY NOW): Bull >60% AND Trend >0.1
            elif bull_pct > 60 and trend > 0.1:
                tier1.append({
                    'Theme': theme_name,
                    'Tier': 1,
                    'Bull_Pct': bull_pct,
                    'Bear_Pct': bear_pct,
                    'Trend': trend,
                    'Fiedler': fiedler,
                    'Fiedler_Change': stats['fiedler_change'],
                    'Stocks': stats['stock_count'],
                    'Large_Cap_Bull': stats['large_cap_bull'],
                    'Large_Cap_Count': stats['large_cap_count'],
                    'Status': 'BUY NOW'
                })
                classified.add(theme_name)

            # TIER 2 (WATCHLIST): Bull 40-60% AND Trend >-0.2
            elif bull_pct >= 40 and bull_pct <= 60 and trend > -0.2:
                tier2.append({
                    'Theme': theme_name,
                    'Tier': 2,
                    'Bull_Pct': bull_pct,
                    'Bear_Pct': bear_pct,
                    'Trend': trend,
                    'Fiedler': fiedler,
                    'Fiedler_Change': stats['fiedler_change'],
                    'Stocks': stats['stock_count'],
                    'Status': 'WATCHLIST'
                })
                classified.add(theme_name)

            # TIER 3 (RESEARCH): Fiedler >1.0 and not classified
            elif fiedler > 1.0:
                tier3.append({
                    'Theme': theme_name,
                    'Tier': 3,
                    'Bull_Pct': bull_pct,
                    'Bear_Pct': bear_pct,
                    'Trend': trend,
                    'Fiedler': fiedler,
                    'Fiedler_Change': stats['fiedler_change'],
                    'Stocks': stats['stock_count'],
                    'Status': 'RESEARCH'
                })
                classified.add(theme_name)

        # Sort tiers
        tier1 = sorted(tier1, key=lambda x: (-x['Bull_Pct'], -x['Trend']))
        tier2 = sorted(tier2, key=lambda x: (-x['Bull_Pct'], -x['Trend']))
        tier3 = sorted(tier3, key=lambda x: (-x['Fiedler'], -x['Fiedler_Change']))
        tier4 = sorted(tier4, key=lambda x: (-x['Bear_Pct'], x['Trend']))

        self.tier1 = pd.DataFrame(tier1)
        self.tier2 = pd.DataFrame(tier2)
        self.tier3 = pd.DataFrame(tier3)
        self.tier4 = pd.DataFrame(tier4)

        print(f"  TIER 1 (BUY NOW): {len(tier1)} themes (Bull >60%, Trend >0.1)")
        print(f"  TIER 2 (WATCHLIST): {len(tier2)} themes (Bull 40-60%, Trend >-0.2)")
        print(f"  TIER 3 (RESEARCH): {len(tier3)} themes (Fiedler >1.0)")
        print(f"  TIER 4 (AVOID): {len(tier4)} themes (Bear >60% OR Trend <-0.3)")

    def save_results(self):
        """Save tier classification results"""
        print("\nSaving results...")

        # Save CSV files
        if not self.tier1.empty:
            file = DATA_DIR / f"tier1_buy_now_{self.date_str}.csv"
            self.tier1.to_csv(file, index=False)
            print(f"  Saved: {file}")

        if not self.tier2.empty:
            file = DATA_DIR / f"tier2_accumulate_{self.date_str}.csv"
            self.tier2.to_csv(file, index=False)
            print(f"  Saved: {file}")

        if not self.tier3.empty:
            file = DATA_DIR / f"tier3_research_{self.date_str}.csv"
            self.tier3.to_csv(file, index=False)
            print(f"  Saved: {file}")

        if not self.tier4.empty:
            file = DATA_DIR / f"tier4_monitor_{self.date_str}.csv"
            self.tier4.to_csv(file, index=False)
            print(f"  Saved: {file}")

        # Save summary JSON
        summary = {
            'date': self.date_str,
            'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'framework': 'Three-Layer (Cohesion x Regime x Trend)',
            'regime_date': self.regime_date,
            'criteria': {
                'tier1': 'Bull >60% AND Trend >0.1',
                'tier2': 'Bull 40-60% AND Trend >-0.2',
                'tier3': 'Fiedler >1.0 (not in other tiers)',
                'tier4': 'Bear >60% OR Trend <-0.3'
            },
            'tier1': {
                'name': 'BUY NOW',
                'count': len(self.tier1),
                'themes': self.tier1['Theme'].tolist() if not self.tier1.empty else []
            },
            'tier2': {
                'name': 'WATCHLIST',
                'count': len(self.tier2),
                'themes': self.tier2['Theme'].tolist() if not self.tier2.empty else []
            },
            'tier3': {
                'name': 'RESEARCH',
                'count': len(self.tier3),
                'themes': self.tier3['Theme'].tolist() if not self.tier3.empty else []
            },
            'tier4': {
                'name': 'AVOID',
                'count': len(self.tier4),
                'themes': self.tier4['Theme'].tolist() if not self.tier4.empty else []
            },
            'total_themes': len(self.theme_stats)
        }

        summary_file = DATA_DIR / f"4tier_summary_{self.date_str}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {summary_file}")

    def print_summary(self):
        """Print classification summary"""
        print("\n" + "="*80)
        print("4-TIER CLASSIFICATION SUMMARY (Regime-Validated)")
        print("="*80)
        print(f"Date: {self.date_str}")
        print(f"Regime Data: {self.regime_date}")
        print(f"Framework: Three-Layer (Cohesion x Regime x Trend)")
        print()

        print("TIER 1 - BUY NOW (Bull >60%, Trend >0.1):")
        print("-"*60)
        if not self.tier1.empty:
            for _, row in self.tier1.head(5).iterrows():
                print(f"  {row['Theme']}: Bull {row['Bull_Pct']:.1f}%, Trend {row['Trend']:+.3f}, Fiedler {row['Fiedler']:.2f}")
            if len(self.tier1) > 5:
                print(f"  ... and {len(self.tier1) - 5} more")
        else:
            print("  No themes meet BUY NOW criteria")
        print()

        print("TIER 2 - WATCHLIST (Bull 40-60%, Trend >-0.2):")
        print("-"*60)
        if not self.tier2.empty:
            for _, row in self.tier2.head(5).iterrows():
                print(f"  {row['Theme']}: Bull {row['Bull_Pct']:.1f}%, Trend {row['Trend']:+.3f}")
            if len(self.tier2) > 5:
                print(f"  ... and {len(self.tier2) - 5} more")
        else:
            print("  No themes on watchlist")
        print()

        print("TIER 4 - AVOID (Bear >60% OR Trend <-0.3):")
        print("-"*60)
        if not self.tier4.empty:
            for _, row in self.tier4.head(3).iterrows():
                print(f"  {row['Theme']}: Bear {row['Bear_Pct']:.1f}%, Trend {row['Trend']:+.3f}")
            if len(self.tier4) > 3:
                print(f"  ... and {len(self.tier4) - 3} more")
        print()

    def run(self):
        """Run full analysis"""
        print("="*80)
        print("4-TIER THEME CLASSIFICATION (Regime-Validated)")
        print("="*80)
        print(f"Date: {self.date_str}")
        print()

        if not self.load_data():
            print("ERROR: Failed to load required data")
            return False

        self.calculate_all_theme_stats()
        self.classify_tiers()
        self.save_results()
        self.print_summary()

        return True


def main():
    parser = argparse.ArgumentParser(
        description='4-Tier Theme Classification with Regime Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Framework: Three-Layer (Cohesion x Regime x Trend)

Tier Classification:
  TIER 1 (BUY NOW):    Bull >60% AND Trend >0.1
  TIER 2 (WATCHLIST):  Bull 40-60% AND Trend >-0.2
  TIER 3 (RESEARCH):   Fiedler >1.0 (not in other tiers)
  TIER 4 (AVOID):      Bear >60% OR Trend <-0.3

Examples:
  python3 analyze_4_tier_themes.py
  python3 analyze_4_tier_themes.py --date 20260116
        """
    )
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()

    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    analyzer = FourTierThemeAnalyzer(date_str)
    success = analyzer.run()

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
