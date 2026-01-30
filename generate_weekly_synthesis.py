#!/usr/bin/env python3
"""
Weekly Investment Synthesis Report Generator
Combines: 4-Tier Framework + Timing Predictions + Sector Rankings + Regime Analysis
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys

class WeeklySynthesisReport:
    def __init__(self, report_date=None):
        """
        Initialize weekly report generator

        Args:
            report_date: Date string in YYYYMMDD format (default: today)
        """
        if report_date is None:
            self.report_date = datetime.now().strftime('%Y%m%d')
        else:
            self.report_date = report_date

        self.report_date_obj = datetime.strptime(self.report_date, '%Y%m%d')
        self.data_dir = Path('data')
        self.reports_dir = Path('reports')
        self.validation_data = None  # Will be loaded if available

    def load_4tier_data(self):
        """Load 4-tier classification data"""
        try:
            tier1 = pd.read_csv(self.data_dir / f'tier1_buy_now_{self.report_date}.csv')
            tier2 = pd.read_csv(self.data_dir / f'tier2_accumulate_{self.report_date}.csv')
            tier3 = pd.read_csv(self.data_dir / f'tier3_research_{self.report_date}.csv')
            tier4 = pd.read_csv(self.data_dir / f'tier4_monitor_{self.report_date}.csv')

            with open(self.data_dir / f'4tier_summary_{self.report_date}.json', 'r', encoding='utf-8') as f:
                summary = json.load(f)

            return {
                'tier1': tier1,
                'tier2': tier2,
                'tier3': tier3,
                'tier4': tier4,
                'summary': summary
            }
        except FileNotFoundError as e:
            print(f"⚠️  Warning: 4-tier data not found for {self.report_date}")
            print(f"   Run: python3 analyze_4_tier_themes.py first")
            return None

    def load_timing_predictions(self):
        """Load timing prediction data"""
        try:
            with open(self.data_dir / f'tier3_timing_predictions_{self.report_date}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Warning: Timing predictions not found for {self.report_date}")
            print(f"   Run: python3 predict_timing.py first")
            return None

    def load_sector_rankings(self):
        """Load sector rankings data"""
        try:
            with open(self.data_dir / f'sector_rankings_{self.report_date}.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Warning: Sector rankings not found for {self.report_date}")
            return None

    def load_validation_data(self):
        """Load fundamental validation data if available"""
        try:
            # Try to import and run validation
            from validate_fundamentals import FundamentalValidator, FUNDAMENTAL_OVERRIDES
            validator = FundamentalValidator(self.report_date)
            validations = validator.run_validation(top_n=10)

            # Organize by theme name
            validation_map = {}
            for v in validations:
                validation_map[v.theme_name] = {
                    'quant_score': v.quant_score,
                    'fund_score': v.fund_score,
                    'composite_score': v.composite_score,
                    'has_divergence': v.has_divergence,
                    'divergence_type': v.divergence_type,
                    'recommendation': v.recommendation,
                    'action': v.action,
                    'validation_notes': v.validation_notes
                }

            self.validation_data = {
                'validations': validations,
                'validation_map': validation_map,
                'overrides': FUNDAMENTAL_OVERRIDES,
                'divergent_themes': [v.theme_name for v in validations if v.has_divergence],
                'confirmed_themes': [v.theme_name for v in validations if not v.has_divergence and v.composite_score >= 55]
            }
            return self.validation_data
        except Exception as e:
            print(f"⚠️  Warning: Fundamental validation not available: {e}")
            self.validation_data = None
            return None

    def generate_executive_summary(self, tier_data, timing_data):
        """Generate executive summary section"""
        print("=" * 120)
        print(f"WEEKLY INVESTMENT SYNTHESIS REPORT")
        print("=" * 120)
        print(f"Report Date: {self.report_date_obj.strftime('%Y-%m-%d (%A)')}")
        print(f"Analysis Period: {(self.report_date_obj - timedelta(days=7)).strftime('%Y-%m-%d')} to {self.report_date_obj.strftime('%Y-%m-%d')}")
        print(f"Framework: Three-Layer Analysis (Cohesion × Regime × Market Cap)")
        print("=" * 120)
        print()

        if tier_data:
            summary = tier_data['summary']
            print("📊 MARKET OVERVIEW")
            print("-" * 120)
            print(f"  TIER 1 (BUY NOW):           {summary['tier1']['count']:>3} themes  |  Immediate investment opportunities")
            print(f"  TIER 2 (ACCUMULATE 6-12mo): {summary['tier2']['count']:>3} themes  |  Begin position building")
            print(f"  TIER 3 (RESEARCH 12-18mo):  {summary['tier3']['count']:>3} themes  |  Early-stage opportunities")
            print(f"  TIER 4 (MONITOR 18-24mo):   {summary['tier4']['count']:>3} themes  |  Speculative watchlist")
            print()
            print(f"  Total themes tracked: {summary['tier1']['count'] + summary['tier2']['count'] + summary['tier3']['count'] + summary['tier4']['count']}")
            print()

            # Add validation summary if available
            if self.validation_data:
                divergent = self.validation_data.get('divergent_themes', [])
                confirmed = self.validation_data.get('confirmed_themes', [])
                print("🔬 FUNDAMENTAL VALIDATION SUMMARY")
                print("-" * 120)
                print(f"  ✅ Confirmed (Quant + Fund aligned):  {len(confirmed)} themes")
                print(f"  ⚠️  Divergent (Quant vs Fund conflict): {len(divergent)} themes")
                if divergent:
                    print(f"     → Divergent themes: {', '.join(divergent)}")
                print()

    def generate_divergence_alerts(self):
        """Generate fundamental divergence alerts section"""
        if not self.validation_data:
            return

        divergent = [v for v in self.validation_data['validations'] if v.has_divergence]
        if not divergent:
            return

        print("=" * 120)
        print("🚨 FUNDAMENTAL DIVERGENCE ALERTS")
        print("=" * 120)
        print("These themes show CONFLICT between quantitative signals and fundamental data.")
        print("⚠️  ACTION REQUIRED: Verify fundamentals before investing!")
        print()

        for v in divergent:
            print(f"⚠️  {v.theme_name} (TIER {v.tier})")
            print(f"   ┌─ Quantitative Score: {v.quant_score:.0f}/100 (High cohesion, strong network)")
            print(f"   ├─ Fundamental Score:  {v.fund_score:.0f}/100 (Weak earnings/macro)")
            print(f"   ├─ Composite Score:    {v.composite_score:.0f}/100 (30% penalty applied)")
            print(f"   └─ Type: {v.divergence_type}")
            print()
            print(f"   ❌ ORIGINAL TIER: {v.tier} (ACCUMULATE)")
            print(f"   ✅ ADJUSTED REC:  {v.recommendation}")
            print(f"   📋 ACTION: {v.action}")
            print()

            # Show override reason if present
            for note in v.validation_notes[:5]:
                if note.strip():
                    print(f"   {note}")
            print()
            print("-" * 120)
            print()

    def generate_tier1_actionable(self, tier_data):
        """Generate TIER 1 actionable recommendations"""
        if not tier_data or tier_data['tier1'].empty:
            print("⚠️  No TIER 1 themes identified this week")
            return

        print("=" * 120)
        print("🎯 TIER 1: BUY NOW (Immediate Action Required)")
        print("=" * 120)
        print("Criteria: Baseline Fiedler >15 + Weekly Change >5.0 + Large-cap bull participation")
        print()

        for idx, row in tier_data['tier1'].iterrows():
            print(f"{idx+1}. {row['Theme']:<40} ({row['Stocks']:>3} stocks)")
            print(f"   📈 Cohesion: {row['Week_Before_Fiedler']:>6.2f} → {row['Last_Week_Fiedler']:>6.2f} "
                  f"(+{row['Change']:>5.2f}, +{row['Pct_Change']:>5.1f}%)")
            print(f"   💡 Investment Thesis: Strong established network with accelerating momentum")
            print(f"   ⚡ Action: Review sector rankings and identify top 3-5 tickers for immediate purchase")
            print(f"   📋 Next Steps:")
            print(f"      1. Run: python3 generate_sector_rankings.py --sector \"{row['Theme']}\"")
            print(f"      2. Focus on Tier 1 large-caps with Bull Quiet regime + positive trend")
            print(f"      3. Allocate 20-30% of theme budget in next 1-2 weeks")
            print()

    def generate_tier2_accumulation(self, tier_data):
        """Generate TIER 2 accumulation strategy"""
        if not tier_data or tier_data['tier2'].empty:
            return

        print("=" * 120)
        print("📦 TIER 2: ACCUMULATE (6-12 Month Horizon)")
        print("=" * 120)
        print("Criteria: Baseline Fiedler 5-15 + Weekly Change >2.0 + Mid-cap participation")
        print()

        # Sort by change descending (strongest momentum first)
        tier2_sorted = tier_data['tier2'].sort_values('Change', ascending=False)

        # Check for divergent themes
        divergent_themes = self.validation_data.get('divergent_themes', []) if self.validation_data else []

        # Show top 5
        for idx, row in tier2_sorted.head(5).iterrows():
            theme_name = row['Theme']
            is_divergent = theme_name in divergent_themes

            # Add warning indicator for divergent themes
            if is_divergent:
                print(f"⚠️ {theme_name:<40} ({row['Stocks']:>3} stocks) ← DIVERGENT: VERIFY FUNDAMENTALS")
            else:
                print(f"• {theme_name:<40} ({row['Stocks']:>3} stocks)")

            print(f"  Cohesion: {row['Week_Before_Fiedler']:>6.2f} → {row['Last_Week_Fiedler']:>6.2f} "
                  f"(+{row['Change']:>5.2f}, +{row['Pct_Change']:>5.1f}%)")

            if is_divergent and self.validation_data:
                v_data = self.validation_data['validation_map'].get(theme_name, {})
                print(f"  ⚠️  Quant: {v_data.get('quant_score', 0):.0f} vs Fund: {v_data.get('fund_score', 0):.0f} → {v_data.get('action', 'Verify')}")
            else:
                print(f"  Strategy: Dollar-cost averaging over next 3-6 months")
            print()

        if len(tier2_sorted) > 5:
            print(f"  ... and {len(tier2_sorted) - 5} more themes")
            print()

    def generate_tier3_research(self, tier_data, timing_data):
        """Generate TIER 3 deep research priorities"""
        if not tier_data or tier_data['tier3'].empty:
            return

        print("=" * 120)
        print("🔬 TIER 3: DEEP RESEARCH (12-18 Month Horizon)")
        print("=" * 120)
        print("Criteria: Baseline Fiedler 2-8 + Change >1.5 + Small-cap leadership")
        print("Key Pattern: Small-caps in bull regime, Large-caps still in bear (12-18 month lead time)")
        print()

        # Merge with timing predictions if available
        if timing_data and 'predictions' in timing_data:
            timing_df = pd.DataFrame(timing_data['predictions'])
            timing_df = timing_df[timing_df['status'] == 'GROWING']

            print("🚀 PRIORITY RESEARCH (Fastest-Moving Themes)")
            print("-" * 120)

            # Get fast-moving themes (< 12 months estimated)
            fast_themes = timing_df[timing_df['estimated_months'] < 12].sort_values('estimated_months')

            for idx, row in fast_themes.head(3).iterrows():
                print(f"\n{idx+1}. {row['theme']:<40}")
                print(f"   Current Fiedler: {row['current_fiedler']:>6.2f} | Target: 15.00 | Gap: {row['details']['gap']:>5.2f}")
                print(f"   ⏱️  Estimated Timeline: {row['estimated_months']:>4.1f} months "
                      f"(Range: {row['range'][0]:.1f}-{row['range'][1]:.1f} months)")
                print(f"   📊 Velocity: {row['details']['weekly_velocity']:>6.3f}/week | {row['acceleration_status']}")
                print(f"   📋 Research Checklist:")
                print(f"      □ Run sector rankings to verify small-cap vs large-cap regime split")
                print(f"      □ Identify fundamental catalyst driving small-cap network formation")
                print(f"      □ Monitor monthly for mid-cap regime flips (early warning signal)")
                print(f"      □ Set alerts for when first large-cap flips to bull regime")

            print("\n")
            print("📊 STANDARD RESEARCH (12-18 Month Themes)")
            print("-" * 120)

            # Medium-speed themes
            medium_themes = timing_df[
                (timing_df['estimated_months'] >= 12) &
                (timing_df['estimated_months'] < 18)
            ].sort_values('estimated_months')

            for idx, row in medium_themes.head(3).iterrows():
                print(f"• {row['theme']:<40} | Est: {row['estimated_months']:>4.1f} months | "
                      f"Velocity: {row['details']['weekly_velocity']:>6.3f}/week")

        else:
            # Without timing data, just show themes
            print("Top TIER 3 Themes by Momentum:")
            print("-" * 120)
            for idx, row in tier_data['tier3'].sort_values('Pct_Change', ascending=False).head(5).iterrows():
                print(f"• {row['Theme']:<40} | Fiedler: {row['Last_Week_Fiedler']:>6.2f} | "
                      f"Change: +{row['Pct_Change']:>5.1f}%")

        print()

    def generate_tier4_monitoring(self, tier_data):
        """Generate TIER 4 watchlist"""
        if not tier_data or tier_data['tier4'].empty:
            return

        print("=" * 120)
        print("👀 TIER 4: MONITOR (18-24+ Month Horizon)")
        print("=" * 120)
        print("Criteria: Baseline Fiedler 0.5-3 + High % change (>40%) - Early seeds, 70% failure rate")
        print()

        print("Watchlist (check quarterly for acceleration):")
        for idx, row in tier_data['tier4'].head(5).iterrows():
            print(f"  • {row['Theme']:<40} | Fiedler: {row['Week_Before_Fiedler']:>5.2f} → "
                  f"{row['Last_Week_Fiedler']:>5.2f} (+{row['Pct_Change']:>6.1f}%)")

        print()

    def generate_portfolio_allocation(self, tier_data):
        """Generate portfolio allocation recommendations"""
        if not tier_data:
            return

        print("=" * 120)
        print("💰 SUGGESTED PORTFOLIO ALLOCATION")
        print("=" * 120)
        print()

        tier1_count = tier_data['summary']['tier1']['count']
        tier2_count = tier_data['summary']['tier2']['count']
        tier3_count = tier_data['summary']['tier3']['count']

        print("Risk-Balanced Allocation Strategy:")
        print("-" * 120)

        if tier1_count > 0:
            print(f"  TIER 1 (BUY NOW):        50-60% allocation")
            print(f"    → {tier1_count} themes × 25-30% each = {tier1_count * 27.5:.0f}% of total capital")
            print(f"    → Focus: 3-5 large-cap stocks per theme")
            print()

        if tier2_count > 0:
            print(f"  TIER 2 (ACCUMULATE):     30-35% allocation")
            print(f"    → Top 5-7 themes from {tier2_count} available")
            print(f"    → Strategy: Dollar-cost average over 6 months")
            print()

        if tier3_count > 0:
            print(f"  TIER 3 (RESEARCH):       10-15% allocation")
            print(f"    → Top 2-3 fast-moving themes from {tier3_count} available")
            print(f"    → Strategy: Small pilot positions (2-3% each)")
            print()

        print(f"  CASH RESERVE:            0-5%")
        print(f"    → For opportunistic entries on market pullbacks")
        print()

    def generate_weekly_actions(self, tier_data):
        """Generate specific weekly action items"""
        print("=" * 120)
        print("📅 THIS WEEK'S ACTION ITEMS")
        print("=" * 120)
        print()

        if not tier_data:
            print("  No actionable items - run data generation scripts first")
            return

        print("IMMEDIATE (This Week):")
        print("-" * 120)

        if not tier_data['tier1'].empty:
            for idx, row in tier_data['tier1'].iterrows():
                print(f"  □ Review {row['Theme']} sector rankings")
                print(f"    python3 generate_sector_rankings.py --sector \"{row['Theme']}\"")
                print(f"    → Identify top 3 large-cap stocks for purchase")
                print()

        print("NEAR-TERM (Next 2-4 Weeks):")
        print("-" * 120)

        if not tier_data['tier2'].empty:
            tier2_top = tier_data['tier2'].sort_values('Change', ascending=False).head(3)
            for idx, row in tier2_top.iterrows():
                print(f"  □ Begin accumulation: {row['Theme']}")
                print(f"    → Set up weekly buy orders for top 3-5 tickers")
                print()

        print("RESEARCH (Next 1-3 Months):")
        print("-" * 120)

        if not tier_data['tier3'].empty:
            tier3_top = tier_data['tier3'].sort_values('Pct_Change', ascending=False).head(3)
            for idx, row in tier3_top.iterrows():
                print(f"  □ Deep dive: {row['Theme']}")
                print(f"    → Verify small-cap vs large-cap regime split")
                print(f"    → Identify fundamental catalyst")
                print(f"    → Monitor monthly for mid-cap regime flips")
                print()

    def generate_risk_alerts(self, tier_data):
        """Generate risk alerts and warnings"""
        print("=" * 120)
        print("⚠️  RISK ALERTS & WARNINGS")
        print("=" * 120)
        print()

        # Check for declining TIER 1 themes (if we have historical data)
        print("Market Risk Factors:")
        print("-" * 120)
        print("  • Week-over-week cohesion data limited to 1-week snapshot")
        print("  • Cannot detect multi-week deceleration without historical timeseries")
        print("  • Recommendation: Monitor TIER 1 themes weekly for reversal signals")
        print()

        # Theme-specific warnings
        if tier_data and not tier_data['tier4'].empty:
            print("High-Risk TIER 4 Themes (70% failure rate):")
            print("-" * 120)
            for idx, row in tier_data['tier4'].head(3).iterrows():
                print(f"  ⚠️  {row['Theme']}: Explosive % change from low baseline "
                      f"({row['Week_Before_Fiedler']:.2f} → {row['Last_Week_Fiedler']:.2f})")
            print()
            print("  → Do NOT invest yet. Monitor quarterly for sustained growth.")
            print()

    def generate_historical_comparison(self):
        """Generate historical comparison if previous week data exists"""
        prev_date = (self.report_date_obj - timedelta(days=7)).strftime('%Y%m%d')
        prev_summary_file = self.data_dir / f'4tier_summary_{prev_date}.json'

        if prev_summary_file.exists():
            print("=" * 120)
            print("📊 WEEK-OVER-WEEK COMPARISON")
            print("=" * 120)
            print()

            with open(prev_summary_file, 'r', encoding='utf-8') as f:
                prev_summary = json.load(f)

            curr_summary_file = self.data_dir / f'4tier_summary_{self.report_date}.json'
            if curr_summary_file.exists():
                with open(curr_summary_file, 'r', encoding='utf-8') as f:
                    curr_summary = json.load(f)

                print(f"Theme Count Changes ({prev_date} → {self.report_date}):")
                print("-" * 120)

                for tier in ['tier1', 'tier2', 'tier3', 'tier4']:
                    prev_count = prev_summary[tier]['count']
                    curr_count = curr_summary[tier]['count']
                    change = curr_count - prev_count

                    tier_name = {
                        'tier1': 'BUY NOW',
                        'tier2': 'ACCUMULATE',
                        'tier3': 'RESEARCH',
                        'tier4': 'MONITOR'
                    }[tier]

                    change_str = f"+{change}" if change > 0 else str(change)
                    arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"

                    print(f"  {tier_name:>12}: {prev_count:>3} → {curr_count:>3} ({change_str:>3}) {arrow}")

                print()

                # Show themes that moved between tiers
                print("Tier Promotions/Demotions:")
                print("-" * 120)

                # This would require tracking theme movements - placeholder for now
                print("  (Requires historical theme tracking - implement in future version)")
                print()

    def generate_report(self):
        """Generate complete weekly synthesis report"""
        # Load all data
        tier_data = self.load_4tier_data()
        timing_data = self.load_timing_predictions()

        # Load fundamental validation data (Layer 4)
        self.load_validation_data()

        # Generate report sections
        self.generate_executive_summary(tier_data, timing_data)

        # Generate divergence alerts FIRST (most important for risk management)
        self.generate_divergence_alerts()

        if tier_data:
            self.generate_tier1_actionable(tier_data)
            self.generate_tier2_accumulation(tier_data)
            self.generate_tier3_research(tier_data, timing_data)
            self.generate_tier4_monitoring(tier_data)
            self.generate_portfolio_allocation(tier_data)
            self.generate_weekly_actions(tier_data)
            self.generate_risk_alerts(tier_data)
            self.generate_historical_comparison()

        # Footer
        print("=" * 120)
        print("📝 REPORT METADATA")
        print("=" * 120)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Framework Version: Three-Layer 4-Tier v1.0")
        print(f"Data Sources: Naver theme cohesion + KRX regime analysis + Market cap classification")
        print(f"Update Frequency: Weekly (every Sunday)")
        print()
        print("For detailed theme analysis, run:")
        print("  python3 generate_sector_rankings.py --sector \"THEME_NAME\"")
        print()
        print("For timing predictions:")
        print("  python3 predict_timing.py")
        print("=" * 120)

    def save_report_markdown(self, output_file=None):
        """Save report to markdown file"""
        if output_file is None:
            output_file = f"reports/weekly_synthesis_{self.report_date}.md"

        # TODO: Implement markdown export
        # For now, user can redirect stdout: python3 script.py > report.md
        pass

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate Weekly Investment Synthesis Report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate report for today
  python3 generate_weekly_synthesis.py

  # Generate report for specific date
  python3 generate_weekly_synthesis.py --date 20251027

  # Save to markdown file
  python3 generate_weekly_synthesis.py > reports/weekly_synthesis_20251027.md
        """
    )

    parser.add_argument(
        '--date',
        type=str,
        help='Report date in YYYYMMDD format (default: today)'
    )

    args = parser.parse_args()

    # Generate report
    reporter = WeeklySynthesisReport(report_date=args.date)
    reporter.generate_report()

if __name__ == "__main__":
    main()
