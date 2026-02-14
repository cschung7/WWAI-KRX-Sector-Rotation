#!/usr/bin/env python3
"""
Generate Sector/Theme-Based Ticker Rankings

Orders tickers by sector (Naver themes) with multiple ranking methodologies:
1. By cohesion change (weekly increase/decrease)
2. By regime probability (bull/bear/transition)
3. By composite score (cohesion + regime + market cap)
4. By sector momentum

Usage:
    python3 generate_sector_rankings.py --date 2025-10-27
    python3 generate_sector_rankings.py --date 2025-10-27 --top-sectors 10
    python3 generate_sector_rankings.py --date 2025-10-27 --sector "철도"
"""

import pandas as pd
import numpy as np
import json
import ast
from pathlib import Path
from datetime import datetime, timedelta
import argparse

class SectorRankingGenerator:
    """Generate sector-based ticker rankings"""

    def __init__(self, base_dir=None):
        # Use config module for self-contained project
        from config import AUTOGLUON_BASE_DIR, DB_FILE, REGIME_DIR, DATA_DIR
        
        self.base_dir = Path(base_dir) if base_dir else AUTOGLUON_BASE_DIR
        self.db_file = DB_FILE if not base_dir else self.base_dir / "DB/db_final.csv"
        self.regime_dir = REGIME_DIR if not base_dir else self.base_dir / "regime/results/regime_queries"

        # Use config data directory
        self.output_dir = DATA_DIR
        self.output_dir.mkdir(exist_ok=True)

        # Load database
        self.db_df = pd.read_csv(self.db_file)

        # Parse Naver themes
        self.theme_to_tickers = {}
        self.ticker_to_themes = {}
        self.ticker_to_name = {}
        self._parse_themes()

        print(f"Loaded {len(self.theme_to_tickers)} themes")
        print(f"Loaded {len(self.ticker_to_themes)} tickers with theme assignments")

    def _parse_themes(self):
        """Parse Naver themes from database"""
        for _, row in self.db_df.iterrows():
            ticker = str(row['tickers']).zfill(6)  # Convert to 6-digit string with leading zeros
            name = row['name']
            themes_str = row['naverTheme']
            market_cap = row['시가총액']

            self.ticker_to_name[ticker] = {
                'name': name,
                'market_cap': market_cap
            }

            try:
                themes = ast.literal_eval(themes_str)
                if isinstance(themes, list):
                    for theme in themes:
                        # Store theme -> tickers
                        if theme not in self.theme_to_tickers:
                            self.theme_to_tickers[theme] = []
                        self.theme_to_tickers[theme].append(ticker)

                        # Store ticker -> themes
                        if ticker not in self.ticker_to_themes:
                            self.ticker_to_themes[ticker] = []
                        self.ticker_to_themes[ticker].append(theme)
            except:
                continue

    def load_regime_data(self, date_str=None):
        """Load latest regime data"""
        # Always get the latest regime file (regardless of date)
        regime_files = list(self.regime_dir.glob("all_regimes_*.csv"))

        if not regime_files:
            print(f"Warning: No regime files found in {self.regime_dir}")
            return {}

        latest_file = sorted(regime_files)[-1]
        print(f"Loading regime data from: {latest_file.name}")

        df = pd.read_csv(latest_file)

        # Get latest date data
        latest_date = df['Date'].max()
        df = df[df['Date'] == latest_date].copy()

        # Build regime dictionary keyed by ticker name (Korean name)
        regime_dict = {}
        for _, row in df.iterrows():
            ticker_name = row['Ticker']  # This is Korean name
            regime_dict[ticker_name] = {
                'regime': row['Regime'],
                'is_bull': row['Is_Bull'],
                'is_bear': row['Is_Bear'],
                'is_transition': row['Is_Transition'],
                'trend': row.get('Trend_Strength', 0),
                'momentum': row.get('Momentum_Score', 0)
            }

        print(f"Loaded regime data for {len(regime_dict)} tickers")
        return regime_dict

    def load_cohesion_changes(self, date_str):
        """Load weekly cohesion changes"""
        cohesion_file = self.output_dir / f"weekly_cohesion_change_{date_str.replace('-', '')}.csv"

        if not cohesion_file.exists():
            print(f"Warning: Cohesion file not found: {cohesion_file}")
            return {}

        df = pd.read_csv(cohesion_file)

        # Build theme -> cohesion change dictionary
        cohesion_dict = {}
        for _, row in df.iterrows():
            cohesion_dict[row['Theme']] = {
                'stocks': row['Stocks'],
                'week_before': row['Week_Before_Fiedler'],
                'last_week': row['Last_Week_Fiedler'],
                'change': row['Change'],
                'pct_change': row['Pct_Change']
            }

        print(f"Loaded cohesion changes for {len(cohesion_dict)} themes")
        return cohesion_dict

    def generate_rankings(self, date_str, top_sectors=None, specific_sector=None):
        """Generate comprehensive sector rankings"""

        # Load data
        regime_data = self.load_regime_data(date_str)
        cohesion_data = self.load_cohesion_changes(date_str)

        # Build ticker rankings
        ticker_rankings = []

        for ticker, info in self.ticker_to_name.items():
            name = info['name']
            market_cap = info['market_cap']
            themes = self.ticker_to_themes.get(ticker, [])

            if not themes:
                continue

            # Get regime data by name
            regime_info = regime_data.get(name, {})

            # Calculate scores
            bull_pct = regime_info.get('is_bull', 0) * 100
            bear_pct = regime_info.get('is_bear', 0) * 100
            transition_pct = regime_info.get('is_transition', 0) * 100
            trend = regime_info.get('trend', 0)
            momentum = regime_info.get('momentum', 0)
            regime_type = regime_info.get('regime', 'Unknown')

            # Regime score (0-1): bull=1.0, transition=0.5, bear=0.0
            regime_score = (bull_pct/100 * 1.0) + (transition_pct/100 * 0.5)

            # Market cap score (0-1)
            # Note: market_cap in DB is in units of 100B (천억)
            # So 100 = 10T, 50 = 5T, 10 = 1T, 3 = 300B
            if market_cap >= 100:  # 10T
                cap_score = 1.0
                cap_tier = "Mega"
            elif market_cap >= 50:  # 5T
                cap_score = 0.8
                cap_tier = "Large"
            elif market_cap >= 10:  # 1T
                cap_score = 0.4
                cap_tier = "Mid"
            elif market_cap >= 3:  # 300B
                cap_score = 0.2
                cap_tier = "Small"
            else:
                cap_score = 0.1
                cap_tier = "Micro"

            # Get cohesion scores for all themes
            cohesion_scores = []
            for theme in themes:
                if theme in cohesion_data:
                    cohesion_scores.append({
                        'theme': theme,
                        'change': cohesion_data[theme]['change'],
                        'pct_change': cohesion_data[theme]['pct_change'],
                        'current_fiedler': cohesion_data[theme]['last_week']
                    })

            # Best cohesion theme (highest positive change)
            if cohesion_scores:
                cohesion_scores.sort(key=lambda x: x['change'], reverse=True)
                best_cohesion = cohesion_scores[0]
            else:
                best_cohesion = {
                    'theme': themes[0] if themes else 'Unknown',
                    'change': 0,
                    'pct_change': 0,
                    'current_fiedler': 0
                }

            # Cohesion score (0-1): normalize change to 0-1 range
            # Assume changes typically range from -5 to +5
            cohesion_score = max(0, min(1, (best_cohesion['change'] + 5) / 10))

            # Composite score (weighted average)
            composite_score = (
                regime_score * 0.4 +
                cap_score * 0.3 +
                cohesion_score * 0.3
            )

            ticker_rankings.append({
                'ticker': ticker,
                'name': name,
                'market_cap': market_cap,
                'cap_tier': cap_tier,
                'themes': themes,
                'primary_theme': best_cohesion['theme'],
                'regime': regime_type,
                'bull_pct': bull_pct,
                'bear_pct': bear_pct,
                'transition_pct': transition_pct,
                'trend': trend,
                'momentum': momentum,
                'cohesion_change': best_cohesion['change'],
                'cohesion_pct_change': best_cohesion['pct_change'],
                'current_fiedler': best_cohesion['current_fiedler'],
                'regime_score': regime_score,
                'cap_score': cap_score,
                'cohesion_score': cohesion_score,
                'composite_score': composite_score
            })

        # Convert to DataFrame
        rankings_df = pd.DataFrame(ticker_rankings)

        # Generate reports
        self._generate_sector_reports(rankings_df, cohesion_data, date_str, top_sectors, specific_sector)

        return rankings_df

    def _generate_sector_reports(self, rankings_df, cohesion_data, date_str, top_sectors, specific_sector):
        """Generate sector-based ranking reports"""

        output_date = date_str.replace('-', '')

        # Report 1: Top sectors by cohesion change
        print("\n" + "="*100)
        print("GENERATING SECTOR RANKINGS")
        print("="*100)

        # Filter for specific sector if requested
        if specific_sector:
            sector_tickers = rankings_df[
                rankings_df['themes'].apply(lambda x: specific_sector in x)
            ].copy()
            sectors_to_analyze = [specific_sector]
        else:
            sectors_to_analyze = list(cohesion_data.keys())
            sector_tickers = rankings_df.copy()

        # Sort sectors by cohesion change
        sorted_sectors = sorted(
            [(s, cohesion_data[s]) for s in sectors_to_analyze],
            key=lambda x: x[1]['change'],
            reverse=True
        )

        # Limit to top N if specified
        if top_sectors:
            sorted_sectors = sorted_sectors[:top_sectors]

        # Generate report for each sector
        sector_reports = []

        for sector, cohesion_info in sorted_sectors:
            # Get all tickers in this sector
            sector_df = rankings_df[
                rankings_df['themes'].apply(lambda x: sector in x)
            ].copy()

            if len(sector_df) == 0:
                continue

            # Sort by composite score
            sector_df = sector_df.sort_values('composite_score', ascending=False)

            # Generate sector report
            report = self._generate_single_sector_report(
                sector, cohesion_info, sector_df, date_str
            )
            sector_reports.append(report)

        # Save all reports
        self._save_reports(sector_reports, output_date, specific_sector)

    def _generate_single_sector_report(self, sector, cohesion_info, sector_df, date_str):
        """Generate report for a single sector"""

        report = {
            'sector': sector,
            'date': date_str,
            'cohesion_info': cohesion_info,
            'total_stocks': len(sector_df),
            'tickers': []
        }

        # Tier 1: Mega/Large caps (≥5T = 50 in DB units)
        tier1 = sector_df[sector_df['market_cap'] >= 50].head(10)

        # Tier 2: Mid caps (1-5T = 10-50 in DB units)
        tier2 = sector_df[
            (sector_df['market_cap'] >= 10) & (sector_df['market_cap'] < 50)
        ].head(10)

        # Tier 3: Small/Micro caps (<1T = <10 in DB units)
        tier3 = sector_df[sector_df['market_cap'] < 10].head(10)

        # Build ticker list with tiers
        for tier_name, tier_df in [("Tier 1 (≥5T)", tier1),
                                     ("Tier 2 (1-5T)", tier2),
                                     ("Tier 3 (<1T)", tier3)]:
            for _, row in tier_df.iterrows():
                report['tickers'].append({
                    'tier': tier_name,
                    'ticker': row['ticker'],
                    'name': row['name'],
                    'market_cap': row['market_cap'],
                    'cap_tier': row['cap_tier'],
                    'regime': row['regime'],
                    'bull_pct': row['bull_pct'],
                    'trend': row['trend'],
                    'momentum': row['momentum'],
                    'composite_score': row['composite_score']
                })

        return report

    def _save_reports(self, sector_reports, output_date, specific_sector):
        """Save sector reports to files"""

        # JSON output
        json_file = self.output_dir / f"sector_rankings_{output_date}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sector_reports, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Saved JSON: {json_file}")

        # Markdown output
        md_file = self.output_dir / f"sector_rankings_{output_date}.md"
        self._generate_markdown_report(sector_reports, md_file)
        print(f"✅ Saved Markdown: {md_file}")

        # Text output (for easy viewing)
        txt_file = self.output_dir / f"sector_rankings_{output_date}.txt"
        self._generate_text_report(sector_reports, txt_file)
        print(f"✅ Saved Text: {txt_file}")

    def _generate_markdown_report(self, sector_reports, output_file):
        """Generate markdown report"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Sector Rankings - {sector_reports[0]['date']}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Total Sectors**: {len(sector_reports)}\n\n")
            f.write("---\n\n")

            for report in sector_reports:
                sector = report['sector']
                cohesion = report['cohesion_info']

                f.write(f"## {sector}\n\n")
                f.write(f"**Cohesion Metrics**:\n")
                f.write(f"- Total Stocks: {cohesion['stocks']}\n")
                f.write(f"- Week Before Fiedler: {cohesion['week_before']:.3f}\n")
                f.write(f"- Last Week Fiedler: {cohesion['last_week']:.3f}\n")
                f.write(f"- Change: {cohesion['change']:+.3f} ({cohesion['pct_change']:+.1f}%)\n\n")

                if cohesion['change'] > 2.0:
                    f.write("📈 **Status**: Strong cohesion increase\n\n")
                elif cohesion['change'] > 0.5:
                    f.write("✅ **Status**: Moderate cohesion increase\n\n")
                elif cohesion['change'] < -2.0:
                    f.write("⚠️ **Status**: Significant cohesion decrease\n\n")
                else:
                    f.write("➖ **Status**: Stable cohesion\n\n")

                # Group by tier
                current_tier = None
                for ticker_info in report['tickers']:
                    if ticker_info['tier'] != current_tier:
                        current_tier = ticker_info['tier']
                        f.write(f"### {current_tier}\n\n")
                        f.write("| Ticker | Name | Market Cap | Regime | Bull % | Trend | Score |\n")
                        f.write("|--------|------|------------|--------|--------|-------|-------|\n")

                    # Market cap in DB is in units of 100B, so divide by 10 to get trillions
                    cap_str = f"{ticker_info['market_cap']/10:.1f}T"
                    f.write(f"| {ticker_info['ticker']} | {ticker_info['name']} | {cap_str} | "
                           f"{ticker_info['regime']} | {ticker_info['bull_pct']:.1f}% | "
                           f"{ticker_info['trend']:.3f} | {ticker_info['composite_score']:.3f} |\n")

                f.write("\n---\n\n")

    def _generate_text_report(self, sector_reports, output_file):
        """Generate plain text report"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("="*100 + "\n")
            f.write(f"SECTOR RANKINGS - {sector_reports[0]['date']}\n")
            f.write("="*100 + "\n\n")

            for idx, report in enumerate(sector_reports, 1):
                sector = report['sector']
                cohesion = report['cohesion_info']

                f.write(f"\n{idx}. {sector} ({cohesion['stocks']} stocks)\n")
                f.write("-" * 100 + "\n")
                f.write(f"Cohesion: {cohesion['last_week']:.2f} (change: {cohesion['change']:+.2f}, {cohesion['pct_change']:+.1f}%)\n\n")

                # Group by tier
                current_tier = None
                for ticker_info in report['tickers']:
                    if ticker_info['tier'] != current_tier:
                        current_tier = ticker_info['tier']
                        f.write(f"\n  {current_tier}:\n")

                    # Market cap in DB is in units of 100B, so divide by 10 to get trillions
                    cap_str = f"{ticker_info['market_cap']/10:.1f}T"
                    f.write(f"    • {ticker_info['name']} ({ticker_info['ticker']}): ")
                    f.write(f"{cap_str} | {ticker_info['regime']} | ")
                    f.write(f"Bull {ticker_info['bull_pct']:.1f}% | ")
                    f.write(f"Trend {ticker_info['trend']:+.3f} | ")
                    f.write(f"Score {ticker_info['composite_score']:.3f}\n")

                f.write("\n")

def main():
    parser = argparse.ArgumentParser(description='Generate sector-based ticker rankings')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                       help='Date for analysis (YYYY-MM-DD)')
    parser.add_argument('--top-sectors', type=int, default=None,
                       help='Number of top sectors to analyze')
    parser.add_argument('--sector', type=str, default=None,
                       help='Specific sector to analyze')

    args = parser.parse_args()

    print(f"\n{'='*100}")
    print(f"SECTOR RANKING GENERATOR")
    print(f"{'='*100}\n")
    print(f"Date: {args.date}")
    if args.top_sectors:
        print(f"Top Sectors: {args.top_sectors}")
    if args.sector:
        print(f"Specific Sector: {args.sector}")
    print()

    # Generate rankings
    generator = SectorRankingGenerator()
    rankings_df = generator.generate_rankings(
        args.date,
        top_sectors=args.top_sectors,
        specific_sector=args.sector
    )

    print(f"\n{'='*100}")
    print("RANKING GENERATION COMPLETE")
    print(f"{'='*100}\n")
    print(f"Total tickers ranked: {len(rankings_df)}")
    print(f"\nOutput files saved to: KRX/data/")

if __name__ == "__main__":
    main()
