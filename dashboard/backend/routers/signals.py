"""
KRX Sector Rotation Dashboard - Signals Router
Signal quality analysis and filtering endpoints

KRX uses 266 Naver themes with higher Fiedler thresholds than USA:
  Tier 1: Fiedler > 50  (BUY NOW)
  Tier 2: Fiedler > 20  (ACCUMULATE)
  Tier 3: Fiedler > 5   (RESEARCH)
  Tier 4: Fiedler <= 5   (MONITOR)

Data sources:
  actionable_tickers_*.csv:  ticker, strategy, score, stage, themes, priority
  tier*_*.csv:               Theme, Tier, Bull_Pct, Bear_Pct, Trend, Fiedler, Fiedler_Change, Stocks, Status
  4tier_summary_*.json:      per-tier theme lists with criteria
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List
import pandas as pd
import json
import math
import ast
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import DATA_DIR

router = APIRouter()


def _safe(v, default=0):
    """Return default if v is None/NaN. Always returns native Python type."""
    if v is None:
        return default
    try:
        if math.isnan(v):
            return default
    except (TypeError, ValueError):
        pass
    # Convert numpy types to native Python
    if hasattr(v, "item"):
        return v.item()
    return v


def _parse_themes(themes_str: str) -> List[str]:
    """Parse the themes column which may be '[]' or a stringified list."""
    if not themes_str or themes_str == "[]":
        return []
    try:
        parsed = ast.literal_eval(themes_str)
        if isinstance(parsed, list):
            return parsed
        return [str(parsed)]
    except (ValueError, SyntaxError):
        return [themes_str] if themes_str else []


def get_latest_actionable():
    """Load latest actionable_tickers CSV."""
    csv_files = sorted(DATA_DIR.glob("actionable_tickers_*.csv"), reverse=True)
    if not csv_files:
        raise HTTPException(status_code=404, detail="No actionable_tickers files found")
    df = pd.read_csv(csv_files[0])

    # Rename 'themes' column -> 'theme' for consistency
    # KRX 'themes' is a stringified list; explode to one row per theme
    if "themes" in df.columns and "theme" not in df.columns:
        df = df.rename(columns={"themes": "theme_raw"})
    elif "theme" not in df.columns and "theme_raw" not in df.columns:
        df["theme_raw"] = "[]"

    return df


def get_tier_data():
    """Load and combine all 4 tier CSV files into a single DataFrame.

    Returns a DataFrame with columns:
      Theme, Tier, Bull_Pct, Bear_Pct, Trend, Fiedler, Fiedler_Change, Stocks, Status
    """
    frames = []
    tier_files = {
        "tier1_buy_now": "Tier 1",
        "tier2_accumulate": "Tier 2",
        "tier3_research": "Tier 3",
        "tier4_monitor": "Tier 4",
    }
    for prefix, tier_label in tier_files.items():
        files = sorted(DATA_DIR.glob(f"{prefix}_*.csv"), reverse=True)
        if files:
            df = pd.read_csv(files[0])
            # Normalize Tier column
            df["Tier"] = tier_label
            frames.append(df)

    if not frames:
        raise HTTPException(status_code=404, detail="No tier CSV files found")

    combined = pd.concat(frames, ignore_index=True)
    return combined


def get_latest_4tier_summary():
    """Load latest 4tier_summary JSON."""
    files = sorted(DATA_DIR.glob("4tier_summary_*.json"), reverse=True)
    if not files:
        raise HTTPException(status_code=404, detail="No 4tier_summary files found")
    with open(files[0]) as f:
        return json.load(f)


def _enrich_actionable_with_tiers(df: pd.DataFrame, tier_df: pd.DataFrame) -> pd.DataFrame:
    """Expand actionable tickers by themes and enrich with tier/fiedler data.

    Each ticker may belong to multiple themes. This function:
    1. Parses the theme_raw column (stringified list)
    2. Explodes to one row per ticker-theme pair
    3. Joins with tier_df to add Tier, Fiedler, Bull_Pct, Trend, Status
    """
    # Parse themes
    if "theme_raw" in df.columns:
        df["theme_list"] = df["theme_raw"].apply(_parse_themes)
    else:
        df["theme_list"] = df["theme"].apply(lambda x: [x] if pd.notna(x) else [])

    # Explode: one row per ticker-theme pair
    exploded = df.explode("theme_list")
    exploded = exploded.rename(columns={"theme_list": "theme"})
    # Remove rows with empty/nan theme
    exploded = exploded[exploded["theme"].notna() & (exploded["theme"] != "")]

    if exploded.empty:
        # Fallback: if no themes mapped, return original df with defaults
        df["theme"] = ""
        df["tier"] = "Tier 4"
        df["fiedler"] = 0.0
        df["bull_ratio"] = 0.0
        df["trend"] = 0.0
        df["status"] = "MONITOR"
        return df

    # Build theme lookup from tier_df
    theme_lookup = {}
    for _, row in tier_df.iterrows():
        theme_lookup[row["Theme"]] = {
            "tier": row.get("Tier", "Tier 4"),
            "fiedler": _safe(row.get("Fiedler", 0)),
            "bull_ratio": _safe(row.get("Bull_Pct", 0)),
            "trend": _safe(row.get("Trend", 0)),
            "status": row.get("Status", "MONITOR"),
        }

    # Enrich
    exploded["tier"] = exploded["theme"].map(lambda t: theme_lookup.get(t, {}).get("tier", "Tier 4"))
    exploded["fiedler"] = exploded["theme"].map(lambda t: theme_lookup.get(t, {}).get("fiedler", 0.0))
    exploded["bull_ratio"] = exploded["theme"].map(lambda t: theme_lookup.get(t, {}).get("bull_ratio", 0.0))
    exploded["trend"] = exploded["theme"].map(lambda t: theme_lookup.get(t, {}).get("trend", 0.0))
    exploded["status"] = exploded["theme"].map(lambda t: theme_lookup.get(t, {}).get("status", "MONITOR"))

    return exploded


def get_enriched_data():
    """Load actionable tickers enriched with tier/Fiedler from tier CSVs."""
    df = get_latest_actionable()
    tier_df = get_tier_data()
    enriched = _enrich_actionable_with_tiers(df, tier_df)
    return enriched, tier_df


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/quality")
async def signal_quality():
    """Get overall signal quality metrics for KRX themes."""
    try:
        enriched, tier_df = get_enriched_data()

        total = len(enriched)
        unique_tickers = enriched["ticker"].nunique()

        # Tier distribution
        tier_dist = enriched.groupby("tier").size().to_dict()

        # Quality score: proportion of Tier 1-2
        high_quality = len(enriched[enriched["tier"].isin(["Tier 1", "Tier 2"])])
        quality_score = (high_quality / total * 100) if total > 0 else 0

        # Trend strength (KRX uses 'Trend' from tier CSVs, not per-ticker momentum)
        avg_trend = _safe(tier_df["Trend"].mean()) * 100 if "Trend" in tier_df.columns else 0
        positive_trend = int((tier_df["Trend"] > 0).sum()) if "Trend" in tier_df.columns else 0
        total_themes = len(tier_df)
        trend_ratio = (positive_trend / total_themes * 100) if total_themes > 0 else 0

        # Cohesion strength (strong = Fiedler >= 20 for KRX)
        avg_fiedler = _safe(tier_df["Fiedler"].mean()) if "Fiedler" in tier_df.columns else 0
        strong_cohesion = int((tier_df["Fiedler"] >= 20).sum()) if "Fiedler" in tier_df.columns else 0
        cohesion_ratio = (strong_cohesion / total_themes * 100) if total_themes > 0 else 0

        return {
            "total_signals": total,
            "unique_tickers": unique_tickers,
            "quality_score": round(quality_score, 1),
            "tier_distribution": tier_dist,
            "momentum": {
                "average_pct": round(avg_trend, 2),
                "positive_count": positive_trend,
                "positive_ratio": round(trend_ratio, 1),
            },
            "cohesion": {
                "average_fiedler": round(avg_fiedler, 2),
                "strong_count": strong_cohesion,
                "strong_ratio": round(cohesion_ratio, 1),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/filter-funnel")
async def filter_funnel():
    """Get signal filtering funnel -- from all themes to actionable."""
    try:
        enriched, tier_df = get_enriched_data()

        total_themes = len(tier_df)
        total_signals = len(enriched)

        stages = [
            {"stage": "All Themes", "count": total_themes,
             "description": "Total Naver themes in analysis"},
            {"stage": "All Tickers", "count": total_signals,
             "description": "Theme-ticker combinations with data"},
            {"stage": "Positive Trend",
             "count": int((tier_df["Trend"] > 0).sum()) if "Trend" in tier_df.columns else 0,
             "description": "Themes with positive trend"},
            {"stage": "HIGH Priority", "count": int((enriched["priority"] == "HIGH").sum()),
             "description": "High priority signals"},
            {"stage": "TIER 1-3",
             "count": int(enriched["tier"].isin(["Tier 1", "Tier 2", "Tier 3"]).sum()),
             "description": "Actionable signals (Tier 1-3)"},
            {"stage": "TIER 1-2",
             "count": int(enriched["tier"].isin(["Tier 1", "Tier 2"]).sum()),
             "description": "High conviction signals"},
            {"stage": "TIER 1",
             "count": int((enriched["tier"] == "Tier 1").sum()),
             "description": "Buy now signals"},
        ]

        return {"funnel": stages}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/momentum-cohesion")
async def momentum_vs_cohesion():
    """Get momentum vs cohesion scatter plot data (theme level).

    Uses tier CSV data which has per-theme Trend and Fiedler values.
    """
    try:
        tier_df = get_tier_data()

        result = []
        for _, row in tier_df.iterrows():
            result.append({
                "theme": row["Theme"],
                "momentum": round(_safe(row.get("Trend", 0)) * 100, 2),
                "fiedler": round(_safe(row.get("Fiedler", 0)), 2),
                "tier": row.get("Tier", "Tier 4"),
                "bull_ratio": round(_safe(row.get("Bull_Pct", 0)), 1),
                "stocks": int(_safe(row.get("Stocks", 0))),
            })

        return {"data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tier-breakdown")
async def tier_breakdown():
    """Get detailed TIER breakdown with theme info."""
    try:
        tier_df = get_tier_data()

        breakdown = {}
        for tier in ["Tier 1", "Tier 2", "Tier 3", "Tier 4"]:
            t_df = tier_df[tier_df["Tier"] == tier]
            themes = t_df["Theme"].dropna().unique().tolist()
            total_stocks = int(t_df["Stocks"].sum()) if "Stocks" in t_df.columns and len(t_df) > 0 else 0

            breakdown[tier] = {
                "theme_count": len(themes),
                "themes": themes,
                "total_stocks": total_stocks,
                "avg_trend": round(_safe(t_df["Trend"].mean()) * 100, 2) if len(t_df) > 0 else 0,
                "avg_cohesion": round(_safe(t_df["Fiedler"].mean()), 2) if len(t_df) > 0 else 0,
                "avg_bull_pct": round(_safe(t_df["Bull_Pct"].mean()), 1) if len(t_df) > 0 else 0,
            }

        return breakdown
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-signals")
async def top_signals(limit: int = 20):
    """Get top signals ranked by score.

    Returns enriched ticker data sorted by score descending.
    """
    try:
        enriched, _ = get_enriched_data()

        top = enriched.nlargest(limit, "score")
        cols = ["ticker", "theme", "tier", "score", "stage", "fiedler", "bull_ratio", "priority"]
        available = [c for c in cols if c in top.columns]

        records = top[available].fillna("").to_dict("records")
        # Round numeric fields
        for r in records:
            if "fiedler" in r and isinstance(r["fiedler"], float):
                r["fiedler"] = round(r["fiedler"], 2)
            if "bull_ratio" in r and isinstance(r["bull_ratio"], float):
                r["bull_ratio"] = round(r["bull_ratio"], 1)
        return records
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-tier/{tier}")
async def signals_by_tier(tier: str, limit: int = 50):
    """Get signals filtered by TIER.

    Accepts tier as '1', '2', '3', '4' or 'Tier 1', etc.
    """
    try:
        tier_normalized = f"Tier {tier}" if tier.isdigit() else tier
        tier_df = get_tier_data()

        filtered = tier_df[tier_df["Tier"] == tier_normalized]
        if filtered.empty:
            return {"tier": tier_normalized, "count": 0, "signals": []}

        cols = ["Theme", "Fiedler", "Bull_Pct", "Bear_Pct", "Trend", "Stocks",
                "Fiedler_Change", "Status"]
        available = [c for c in cols if c in filtered.columns]
        result = filtered.nlargest(limit, "Fiedler")[available].fillna("").to_dict("records")

        # Rename keys to lowercase for API consistency
        clean_result = []
        for r in result:
            clean_result.append({
                "theme": r.get("Theme", ""),
                "fiedler": round(_safe(r.get("Fiedler", 0)), 2),
                "bull_pct": round(_safe(r.get("Bull_Pct", 0)), 1),
                "bear_pct": round(_safe(r.get("Bear_Pct", 0)), 1),
                "trend": round(_safe(r.get("Trend", 0)) * 100, 2),
                "stocks": int(_safe(r.get("Stocks", 0))),
                "fiedler_change": round(_safe(r.get("Fiedler_Change", 0)), 2),
                "status": r.get("Status", ""),
            })

        return {
            "tier": tier_normalized,
            "count": len(filtered),
            "signals": clean_result,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/theme-signals/{theme}")
async def theme_signals(theme: str):
    """Get all signals for a specific Naver theme.

    Returns theme-level metrics and tickers belonging to that theme.
    """
    try:
        tier_df = get_tier_data()

        # Find theme in tier data
        theme_row = tier_df[tier_df["Theme"] == theme]
        if theme_row.empty:
            raise HTTPException(status_code=404, detail=f"Theme '{theme}' not found")

        theme_info = theme_row.iloc[0]

        # Get tickers for this theme from actionable data
        df = get_latest_actionable()
        theme_col = "theme_raw" if "theme_raw" in df.columns else "theme"

        # Filter tickers that contain this theme in their themes list
        def _has_theme(raw_val):
            themes = _parse_themes(str(raw_val))
            return theme in themes

        if theme_col in df.columns:
            matched = df[df[theme_col].apply(_has_theme)]
        else:
            matched = pd.DataFrame()

        cols = ["ticker", "score", "stage", "priority"]
        available = [c for c in cols if c in matched.columns]
        signals = matched[available].fillna("").to_dict("records") if not matched.empty else []

        return {
            "theme": theme,
            "tier": theme_info.get("Tier", "Tier 4"),
            "fiedler": round(_safe(theme_info.get("Fiedler", 0)), 2),
            "trend": round(_safe(theme_info.get("Trend", 0)) * 100, 2),
            "bull_pct": round(_safe(theme_info.get("Bull_Pct", 0)), 1),
            "bear_pct": round(_safe(theme_info.get("Bear_Pct", 0)), 1),
            "fiedler_change": round(_safe(theme_info.get("Fiedler_Change", 0)), 2),
            "status": theme_info.get("Status", ""),
            "stock_count": int(_safe(theme_info.get("Stocks", 0))),
            "matched_tickers": len(signals),
            "signals": signals,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
