#!/usr/bin/env python3
"""
Lightweight Daily Price Update Script
=====================================
Updates actionable tickers based on daily price changes.
Uses existing weekly regime + daily classified_trends data.

Data Flow:
  classified_trends_*.csv (from AutoML_Krx)
       ↓
  Filter by Trend_Stage + Deviation_BB
       ↓
  Apply scoring & ranking
       ↓
  Output actionable_tickers_*.csv

Usage:
    python daily_price_update.py
    python daily_price_update.py --date 2026-01-30
    python daily_price_update.py --dry-run
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import numpy as np

# Optional: for colored output
try:
    from termcolor import colored, cprint
except ImportError:
    def colored(text, color=None, **kwargs): return text
    def cprint(text, color=None, **kwargs): print(text)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
PROJECT_DIR = Path("/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX")
AUTOML_DIR = Path("/mnt/nas/AutoGluon/AutoML_Krx")
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "data"
SUPERTREND_DIR = AUTOML_DIR / "superTrend"

# Input files from AutoML_Krx pipeline
CLASSIFIED_TRENDS_PATTERN = "classified_trends_*.csv"
DAILY_PICKS_PATTERN = "daily_top_picks_*.csv"
THEME_ANALYSIS_FILE = "theme_trend_stage_analysis.csv"

# Scoring weights
REGIME_SCORE = {
    "Transition": 40,
    "Bull Quiet": 30,
    "Ranging": 20,
    "Bear Quiet": 10,
    "Bull Volatile": 15,
    "Bear Volatile": 0
}

STAGE_SCORE = {
    "Early Breakout": 30,
    "Super Trend": 25,
    "Burgeoning": 20,
    "Healthy Correction": 10,
    "Bearish": 0
}

# Filters
MIN_DEVIATION_BB = 0.0  # Minimum % above BB for breakout
MIN_TREND_STRENGTH = 0.0  # Minimum trend strength
EXCLUDED_PATTERNS = ["스팩", "SPAC", "우B", "우선주"]  # Exclude SPACs and preferred

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_latest_file(directory: Path, pattern: str) -> Optional[Path]:
    """Find the most recent file matching pattern."""
    files = sorted(directory.glob(pattern), reverse=True)
    return files[0] if files else None


def is_excluded(ticker: str) -> bool:
    """Check if ticker should be excluded."""
    return any(pat in ticker for pat in EXCLUDED_PATTERNS)


def load_classified_trends(date_str: Optional[str] = None) -> pd.DataFrame:
    """Load classified trends from AutoML_Krx."""
    if date_str:
        # Convert YYYYMMDD to YYYY-MM-DD if needed
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        trends_file = SUPERTREND_DIR / f"classified_trends_{date_str}.csv"
    else:
        trends_file = find_latest_file(SUPERTREND_DIR, CLASSIFIED_TRENDS_PATTERN)

    if not trends_file or not trends_file.exists():
        cprint(f"❌ No classified_trends file found!", "red")
        return pd.DataFrame()

    df = pd.read_csv(trends_file)
    file_date = trends_file.stem.split("_")[-1]
    cprint(f"✅ Loaded {len(df)} tickers from {trends_file.name}", "green")

    return df, file_date


def load_daily_picks(date_str: Optional[str] = None) -> pd.DataFrame:
    """Load daily top picks (has theme info)."""
    if date_str:
        if len(date_str) == 8:
            date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        picks_file = SUPERTREND_DIR / f"daily_top_picks_{date_str}.csv"
    else:
        picks_file = find_latest_file(SUPERTREND_DIR, DAILY_PICKS_PATTERN)

    if picks_file and picks_file.exists():
        df = pd.read_csv(picks_file)
        cprint(f"✅ Loaded {len(df)} daily picks from {picks_file.name}", "green")
        return df

    return pd.DataFrame()


def load_theme_analysis() -> pd.DataFrame:
    """Load theme trend stage analysis for theme scoring."""
    theme_file = SUPERTREND_DIR / THEME_ANALYSIS_FILE

    if theme_file.exists():
        df = pd.read_csv(theme_file)
        cprint(f"✅ Loaded {len(df)} theme analysis records", "green")
        return df

    return pd.DataFrame()


def load_previous_key_players() -> Dict[str, float]:
    """Load PageRank scores from previous analysis."""
    key_players_file = find_latest_file(DATA_DIR, "tier1_key_players_*.json")

    if key_players_file and key_players_file.exists():
        with open(key_players_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        scores = {}

        # Handle nested structure: {theme_results: {theme: [stocks]}}
        if isinstance(data, dict) and "theme_results" in data:
            for theme, stocks in data["theme_results"].items():
                for item in stocks:
                    if isinstance(item, dict):
                        stock = item.get("stock", "")
                        pagerank = item.get("pagerank", 0) or item.get("total_pagerank", 0)
                        scores[stock] = pagerank * 100
        # Handle flat list structure: [{stock, pagerank}]
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    scores[item.get("stock", "")] = item.get("total_pagerank", 0) * 100

        cprint(f"✅ Loaded {len(scores)} key player scores", "green")
        return scores

    return {}


def calculate_score(row: pd.Series, pagerank_scores: Dict[str, float]) -> int:
    """Calculate total score for a ticker."""
    regime_score = REGIME_SCORE.get(row.get("Regime", ""), 0)
    stage_score = STAGE_SCORE.get(row.get("Trend_Stage", ""), 0)

    # Bonus for strong deviation above BB
    dev_bb = row.get("Deviation_BB", 0)
    if isinstance(dev_bb, (int, float)) and dev_bb > 0:
        bb_bonus = min(int(dev_bb * 100), 10)  # Max 10 bonus points
    else:
        bb_bonus = 0

    # Bonus for PageRank (key players)
    ticker = row.get("Ticker", "")
    pagerank_bonus = int(pagerank_scores.get(ticker, 0))

    # Theme bonus (if in trending themes)
    theme_bonus = 5  # Default

    total = regime_score + stage_score + bb_bonus + min(pagerank_bonus, 10) + theme_bonus
    return total


def assign_priority(row: pd.Series) -> str:
    """Assign priority based on stage and metrics."""
    stage = row.get("Trend_Stage", "")
    regime = row.get("Regime", "")
    dev_bb = row.get("Deviation_BB", 0)

    if stage == "Early Breakout" and regime == "Transition":
        return "HIGH"
    elif stage == "Super Trend" and regime == "Bull Quiet":
        return "HIGH"
    elif stage in ["Early Breakout", "Super Trend", "Burgeoning"]:
        return "MEDIUM"
    elif stage == "Healthy Correction":
        return "MEDIUM"
    else:
        return "LOW"


def format_strategy(row: pd.Series) -> str:
    """Format strategy description."""
    stage = row.get("Trend_Stage", "Unknown")
    regime = row.get("Regime", "Unknown")

    if stage == "Early Breakout":
        return f"Early Breakout ({regime})"
    elif stage == "Super Trend":
        return "Super Trend (Bull Quiet)"
    else:
        return f"{stage} ({regime})"


# =============================================================================
# MAIN UPDATE FUNCTION
# =============================================================================

def run_daily_update(target_date: Optional[str] = None, dry_run: bool = False) -> pd.DataFrame:
    """Run the daily price update."""

    today = target_date or datetime.now().strftime("%Y%m%d")
    if "-" in today:
        today = today.replace("-", "")

    cprint(f"\n{'='*60}", "cyan")
    cprint(f"  Daily Price Update - {today}", "cyan")
    cprint(f"{'='*60}\n", "cyan")

    # Step 1: Load classified trends (main data source)
    cprint("📊 Step 1: Loading classified trends...", "blue")
    result = load_classified_trends(target_date)
    if isinstance(result, tuple):
        trends_df, data_date = result
    else:
        trends_df = result
        data_date = today

    if trends_df.empty:
        cprint("❌ No trends data. Exiting.", "red")
        return pd.DataFrame()

    # Step 2: Load supplementary data
    cprint("\n📋 Step 2: Loading supplementary data...", "blue")
    daily_picks_df = load_daily_picks(target_date)
    pagerank_scores = load_previous_key_players()

    # Step 3: Filter and exclude unwanted tickers
    cprint("\n🔍 Step 3: Filtering tickers...", "blue")
    initial_count = len(trends_df)

    # Exclude SPACs and preferred shares
    trends_df = trends_df[~trends_df["Ticker"].apply(is_excluded)]
    cprint(f"   After SPAC/preferred filter: {len(trends_df)} (removed {initial_count - len(trends_df)})", "white")

    # Filter for actionable stages
    actionable_stages = ["Early Breakout", "Super Trend", "Burgeoning", "Healthy Correction"]
    trends_df = trends_df[trends_df["Trend_Stage"].isin(actionable_stages)]
    cprint(f"   After stage filter: {len(trends_df)}", "white")

    if trends_df.empty:
        cprint("⚠️  No actionable tickers after filtering.", "yellow")
        return pd.DataFrame()

    # Step 4: Calculate scores and priorities
    cprint("\n📈 Step 4: Calculating scores...", "blue")

    trends_df["score"] = trends_df.apply(lambda row: calculate_score(row, pagerank_scores), axis=1)
    trends_df["priority"] = trends_df.apply(assign_priority, axis=1)
    trends_df["strategy"] = trends_df.apply(format_strategy, axis=1)

    # Add theme info from daily picks if available
    if not daily_picks_df.empty and "Themes" in daily_picks_df.columns:
        theme_map = dict(zip(daily_picks_df["Ticker"], daily_picks_df["Themes"]))
        trends_df["themes"] = trends_df["Ticker"].map(theme_map).fillna("[]")
    else:
        trends_df["themes"] = "[]"

    # Step 5: Sort and rank
    cprint("\n🏆 Step 5: Ranking tickers...", "blue")

    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    trends_df["priority_rank"] = trends_df["priority"].map(priority_order)
    trends_df = trends_df.sort_values(["priority_rank", "score"], ascending=[True, False])
    trends_df = trends_df.reset_index(drop=True)

    # Step 6: Prepare output
    output_df = trends_df[[
        "Ticker", "strategy", "score", "Trend_Stage", "themes", "priority",
        "Regime", "Deviation_BB", "Trend_Strength", "Momentum"
    ]].copy()

    output_df.columns = [
        "ticker", "strategy", "score", "stage", "themes", "priority",
        "regime", "dev_bb_pct", "trend_strength", "momentum"
    ]

    # Convert dev_bb_pct to percentage
    output_df["dev_bb_pct"] = (output_df["dev_bb_pct"] * 100).round(2)

    # Step 7: Summary
    cprint(f"\n📊 Summary:", "blue")
    cprint(f"   Total actionable: {len(output_df)}", "white")
    cprint(f"   HIGH priority: {len(output_df[output_df['priority'] == 'HIGH'])}", "green")
    cprint(f"   MEDIUM priority: {len(output_df[output_df['priority'] == 'MEDIUM'])}", "yellow")
    cprint(f"   LOW priority: {len(output_df[output_df['priority'] == 'LOW'])}", "red")

    # Stage breakdown
    cprint(f"\n   By Stage:", "white")
    for stage in actionable_stages:
        count = len(output_df[output_df["stage"] == stage])
        if count > 0:
            cprint(f"     {stage}: {count}", "white")

    # Top picks
    cprint(f"\n🎯 Top 10 Picks:", "cyan")
    for i, row in output_df.head(10).iterrows():
        emoji = "🔥" if row["priority"] == "HIGH" else "📈"
        cprint(f"   {emoji} {row['ticker']}: {row['score']} pts | {row['stage']} | BB: {row['dev_bb_pct']}%", "white")

    # Step 8: Save results
    if not dry_run:
        cprint(f"\n💾 Saving results...", "blue")

        # Actionable tickers (simple)
        simple_cols = ["ticker", "strategy", "score", "stage", "themes", "priority"]
        output_file = OUTPUT_DIR / f"actionable_tickers_{today}.csv"
        output_df[simple_cols].to_csv(output_file, index=False, encoding="utf-8")
        cprint(f"   ✅ {output_file}", "green")

        # Detailed results
        detailed_file = OUTPUT_DIR / f"daily_update_detailed_{today}.csv"
        output_df.to_csv(detailed_file, index=False, encoding="utf-8")
        cprint(f"   ✅ {detailed_file}", "green")

        # Copy to superTrend
        supertrend_output = SUPERTREND_DIR / f"actionable_tickers_{today}.csv"
        output_df[simple_cols].to_csv(supertrend_output, index=False, encoding="utf-8")
        cprint(f"   ✅ {supertrend_output}", "green")

        # JSON summary
        summary = {
            "date": today,
            "data_source_date": data_date,
            "total_tickers": len(output_df),
            "high_priority": len(output_df[output_df["priority"] == "HIGH"]),
            "medium_priority": len(output_df[output_df["priority"] == "MEDIUM"]),
            "low_priority": len(output_df[output_df["priority"] == "LOW"]),
            "stage_breakdown": output_df["stage"].value_counts().to_dict(),
            "top_10": output_df.head(10)[["ticker", "score", "stage", "priority"]].to_dict(orient="records")
        }

        summary_file = OUTPUT_DIR / f"daily_update_summary_{today}.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        cprint(f"   ✅ {summary_file}", "green")

    else:
        cprint(f"\n🔍 DRY RUN - No files saved", "yellow")

    cprint(f"\n{'='*60}", "cyan")
    cprint(f"  Update Complete!", "cyan")
    cprint(f"{'='*60}\n", "cyan")

    return output_df


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Lightweight Daily Price Update for KRX Sector Rotation"
    )
    parser.add_argument(
        "--date", "-d",
        type=str,
        default=None,
        help="Target date (YYYY-MM-DD or YYYYMMDD). Default: today"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without saving files"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=10,
        help="Number of top picks to display"
    )

    args = parser.parse_args()

    try:
        results = run_daily_update(
            target_date=args.date,
            dry_run=args.dry_run
        )

        sys.exit(0)

    except Exception as e:
        cprint(f"\n❌ Error: {e}", "red")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
