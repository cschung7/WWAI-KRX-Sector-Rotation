#!/usr/bin/env python3
"""
Compute per-theme UCS composite scores from UCS_LRS daily data.

Reads:
  - UCS_LRS/complete_situation_results_*.json (latest)
  - data/network_theme_data.csv (stock→theme mapping)

Outputs:
  - data/theme_ucs_scores.json
"""

import json
import ast
import os
import sys
import tempfile
from pathlib import Path
from collections import defaultdict
from datetime import date

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UCS_LRS_DIR = Path("/mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS")
THEME_CSV = DATA_DIR / "network_theme_data.csv"
OUTPUT_FILE = DATA_DIR / "theme_ucs_scores.json"


def find_latest_ucs_file():
    """Find the most recent complete_situation_results file."""
    files = sorted(UCS_LRS_DIR.glob("complete_situation_results_*.json"))
    if not files:
        print("[ERROR] No complete_situation_results_*.json found in", UCS_LRS_DIR)
        sys.exit(1)
    return files[-1]


def load_theme_mapping():
    """Load stock→themes mapping from network_theme_data.csv."""
    import csv

    theme_to_stocks = defaultdict(set)
    with open(THEME_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("name", "").strip()
            themes_str = row.get("naverTheme", "[]")
            if not name or not themes_str or themes_str == "[]":
                continue
            try:
                themes = ast.literal_eval(themes_str)
            except Exception:
                continue
            for theme in themes:
                theme_to_stocks[theme].add(name)
    return theme_to_stocks


def main():
    ucs_file = find_latest_ucs_file()
    ucs_date = ucs_file.stem.replace("complete_situation_results_", "")
    print(f"[INFO] Loading UCS data from: {ucs_file.name} ({ucs_date})")

    with open(ucs_file, "r", encoding="utf-8") as f:
        ucs_data = json.load(f)
    print(f"[INFO] Loaded {len(ucs_data)} tickers")

    theme_to_stocks = load_theme_mapping()
    print(f"[INFO] Loaded {len(theme_to_stocks)} themes from {THEME_CSV.name}")

    # Build per-theme aggregation
    themes_result = {}
    for theme, stock_names in sorted(theme_to_stocks.items()):
        scores = []
        ratings = defaultdict(int)
        top_stocks = []

        for name in stock_names:
            entry = ucs_data.get(name)
            if not entry:
                continue
            oa = entry.get("overall_assessment")
            if not oa or oa.get("status") != "SUCCESS":
                continue
            score_pct = oa.get("score_percentage")
            if score_pct is None:
                continue

            scores.append(score_pct)
            rating = oa.get("rating", "UNKNOWN")
            ratings[rating] += 1
            top_stocks.append({"name": name, "score": round(score_pct, 1)})

        if not scores:
            continue

        top_stocks.sort(key=lambda x: x["score"], reverse=True)
        avg_score = sum(scores) / len(scores)

        themes_result[theme] = {
            "avg_score": round(avg_score, 1),
            "count": len(stock_names),
            "analyzed": len(scores),
            "ratings": dict(ratings),
            "top3": top_stocks[:3],
        }

    output = {
        "date": ucs_date,
        "total_themes": len(themes_result),
        "themes": themes_result,
    }

    # Atomic write: write to temp file first, then rename to prevent corruption
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=OUTPUT_FILE.parent, suffix=".tmp", prefix="theme_ucs_"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, OUTPUT_FILE)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    print(f"[DONE] Wrote {len(themes_result)} themes to {OUTPUT_FILE}")
    print(f"  Date: {ucs_date}")
    # Show top 5 themes
    top5 = sorted(themes_result.items(), key=lambda x: x[1]["avg_score"], reverse=True)[:5]
    for name, d in top5:
        print(f"  {name}: avg={d['avg_score']}, analyzed={d['analyzed']}/{d['count']}")


if __name__ == "__main__":
    main()
