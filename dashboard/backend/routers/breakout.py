"""
Breakout Scanner API Endpoints
Covers Q1, Q11, Q13 from investment Q&A
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import glob
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import DATA_DIR

# Debug: Print DATA_DIR at module load time
print(f"[breakout module] DATA_DIR at import: {DATA_DIR}", flush=True)
print(f"[breakout module] DATA_DIR exists: {DATA_DIR.exists()}", flush=True)
_csv_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
print(f"[breakout module] CSV files found at import: {_csv_files}", flush=True)

router = APIRouter()

@router.get("/debug")
async def debug_files():
    """Debug endpoint to check file availability"""
    files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
    cache_exists = (DATA_DIR / "dashboard_cache.json").exists()
    return {
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists(),
        "csv_files": files,
        "cache_exists": cache_exists
    }

# DB path for theme lookup
DB_FINAL_PATH = Path("/mnt/nas/AutoGluon/AutoML_Krx/DB/db_final.csv")

# Cache for theme mapping
_theme_cache = None

def get_theme_mapping() -> dict:
    """Load and cache theme mapping from db_final.csv"""
    global _theme_cache
    if _theme_cache is None:
        try:
            df = pd.read_csv(DB_FINAL_PATH)
            # Create mapping: name -> naverTheme
            _theme_cache = dict(zip(df['name'], df['naverTheme']))
        except Exception as e:
            print(f"Error loading theme data: {e}")
            _theme_cache = {}
    return _theme_cache

def load_latest_actionable_tickers(date: Optional[str] = None) -> pd.DataFrame:
    """Load actionable tickers data from CSV or JSON cache fallback"""
    import sys
    print(f"[breakout] FUNCTION CALLED, DATA_DIR={DATA_DIR}", file=sys.stderr, flush=True)

    # Try CSV files first
    if date:
        date_str = date.replace('-', '')
        ticker_file = DATA_DIR / f"actionable_tickers_{date_str}.csv"
        print(f"[breakout] Dated file: {ticker_file}, exists={ticker_file.exists()}", file=sys.stderr, flush=True)
        if ticker_file.exists():
            return pd.read_csv(ticker_file)
    else:
        ticker_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
        print(f"[breakout] CSV files: {ticker_files}", file=sys.stderr, flush=True)
        if ticker_files:
            print(f"[breakout] Loading: {ticker_files[-1]}", file=sys.stderr, flush=True)
            return pd.read_csv(ticker_files[-1])

    # Fallback to dashboard_cache.json (for Railway deployment)
    cache_file = DATA_DIR / "dashboard_cache.json"
    print(f"[breakout] Cache fallback: {cache_file}, exists={cache_file.exists()}", file=sys.stderr, flush=True)
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
            if 'actionable_tickers' in cache_data and cache_data['actionable_tickers']:
                print(f"[breakout] Loaded {len(cache_data['actionable_tickers'])} from cache", file=sys.stderr, flush=True)
                return pd.DataFrame(cache_data['actionable_tickers'])
        except Exception as e:
            print(f"[breakout] Cache error: {e}", file=sys.stderr, flush=True)

    print("[breakout] NO DATA FOUND!", file=sys.stderr, flush=True)
    raise HTTPException(status_code=404, detail="No actionable tickers data found")


@router.get("/candidates")
async def get_breakout_candidates(
    date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD)"),
    stage: Optional[str] = Query(None, description="Filter by stage (Early Breakout, Super Trend, etc.)"),
    min_score: Optional[int] = Query(None, description="Minimum score filter"),
    priority: Optional[str] = Query(None, description="Filter by priority (HIGH, MEDIUM, LOW)"),
    theme: Optional[str] = Query(None, description="Filter by theme name"),
    limit: Optional[int] = Query(100, description="Max results to return")
):
    """
    Get breakout candidates with filtering
    Covers Q1: Which stocks have highest breakout potential today?
    """
    import sys
    print(f"[candidates] ENDPOINT CALLED, date={date}", file=sys.stderr, flush=True)

    # Direct file check inside endpoint
    csv_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
    print(f"[candidates] Direct glob result: {csv_files}", file=sys.stderr, flush=True)

    try:
        df = load_latest_actionable_tickers(date)

        # Apply filters
        if stage:
            df = df[df['stage'].str.contains(stage, case=False, na=False)]

        if min_score:
            df = df[df['score'] >= min_score]

        if priority:
            df = df[df['priority'].str.upper() == priority.upper()]

        if theme:
            df = df[df['themes'].str.contains(theme, case=False, na=False)]

        # Sort by score descending
        df = df.sort_values('score', ascending=False).head(limit)

        # Get theme mapping
        theme_map = get_theme_mapping()

        # Convert to list of dicts
        candidates = []
        for _, row in df.iterrows():
            ticker_name = row['ticker']
            # Look up theme from db_final.csv, fallback to existing themes column
            themes = theme_map.get(ticker_name, row.get('themes', '[]'))
            if pd.isna(themes) or themes == '[]' or themes == 'nan':
                themes = '[]'

            candidates.append({
                "ticker": ticker_name,
                "strategy": row.get('strategy', ''),
                "score": int(row['score']),
                "stage": row['stage'],
                "themes": themes,
                "priority": row['priority']
            })

        # Calculate stage distribution
        full_df = load_latest_actionable_tickers(date)
        stage_counts = full_df['stage'].value_counts().to_dict()

        return {
            "candidates": candidates,
            "count": len(candidates),
            "total_available": len(full_df),
            "stage_distribution": stage_counts,
            "filters_applied": {
                "stage": stage,
                "min_score": min_score,
                "priority": priority,
                "theme": theme
            },
            "date": date or Path(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv"))[-1]).stem.split('_')[-1]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stages")
async def get_stage_distribution(
    date: Optional[str] = Query(None, description="Analysis date")
):
    """
    Get stage distribution for pie/bar chart
    """
    try:
        df = load_latest_actionable_tickers(date)

        stage_counts = df['stage'].value_counts().to_dict()
        priority_counts = df['priority'].value_counts().to_dict()

        return {
            "stages": [
                {"name": stage, "count": count}
                for stage, count in stage_counts.items()
            ],
            "priorities": [
                {"name": priority, "count": count}
                for priority, count in priority_counts.items()
            ],
            "total": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expected-returns")
async def get_expected_returns():
    """
    Get historical expected returns by stage
    Covers Q13, Q14, Q15: Historical performance by stage
    """
    # Pre-computed from backtest results
    returns_data = {
        "stages": [
            {"stage": "Early Breakout", "return_20d": 7.93, "win_rate": 43.0, "sample_size": 172, "recommendation": "BUY"},
            {"stage": "Transition", "return_20d": 4.24, "win_rate": 40.9, "sample_size": 556, "recommendation": "BUY"},
            {"stage": "Super Trend", "return_20d": 2.10, "win_rate": 38.0, "sample_size": 1234, "recommendation": "HOLD"},
            {"stage": "Burgeoning", "return_20d": 1.50, "win_rate": 36.0, "sample_size": 890, "recommendation": "HOLD"},
            {"stage": "Healthy Correction", "return_20d": 1.20, "win_rate": 36.0, "sample_size": 780, "recommendation": "HOLD"},
            {"stage": "Super Trend (Bear)", "return_20d": -0.39, "win_rate": 37.1, "sample_size": 445, "recommendation": "CAUTION"},
            {"stage": "Bear Quiet", "return_20d": -2.15, "win_rate": 33.2, "sample_size": 320, "recommendation": "AVOID"},
            {"stage": "Bear Volatile", "return_20d": -7.23, "win_rate": 28.6, "sample_size": 156, "recommendation": "AVOID"}
        ],
        "source": "Backtest 2024-01-05 to 2025-12-16"
    }
    return returns_data


@router.get("/top-picks")
async def get_top_picks(
    date: Optional[str] = Query(None, description="Analysis date"),
    limit: int = Query(10, description="Number of top picks")
):
    """
    Get top N breakout picks
    Covers Q1: Top breakout potential
    """
    try:
        df = load_latest_actionable_tickers(date)

        # Filter to Early Breakout only
        early_breakout = df[df['stage'] == 'Early Breakout'].sort_values('score', ascending=False).head(limit)

        # Get theme mapping
        theme_map = get_theme_mapping()

        picks = []
        for rank, (_, row) in enumerate(early_breakout.iterrows(), 1):
            ticker_name = row['ticker']
            themes = theme_map.get(ticker_name, row.get('themes', '[]'))
            if pd.isna(themes) or themes == '[]' or themes == 'nan':
                themes = '[]'

            picks.append({
                "rank": rank,
                "ticker": ticker_name,
                "score": int(row['score']),
                "strategy": row.get('strategy', ''),
                "themes": themes
            })

        return {
            "picks": picks,
            "count": len(picks),
            "stage": "Early Breakout",
            "expected_return": "+7.93% (20D avg)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supertrend-candidates")
async def get_supertrend_candidates(
    date: Optional[str] = Query(None, description="Analysis date"),
    limit: int = Query(50, description="Max results")
):
    """
    Get SuperTrend candidates - tickers in Super Trend stage
    These are stocks showing strong trend momentum in bull regime
    """
    try:
        df = load_latest_actionable_tickers(date)

        # Filter to Super Trend stage only
        supertrend_df = df[df['stage'].str.contains('Super Trend', case=False, na=False)]
        supertrend_df = supertrend_df.sort_values('score', ascending=False).head(limit)

        # Get theme mapping
        theme_map = get_theme_mapping()

        candidates = []
        for _, row in supertrend_df.iterrows():
            ticker_name = row['ticker']
            themes = theme_map.get(ticker_name, row.get('themes', '[]'))
            if pd.isna(themes) or themes == '[]' or themes == 'nan':
                themes = '[]'

            candidates.append({
                "ticker": ticker_name,
                "score": int(row['score']),
                "stage": row['stage'],
                "priority": row['priority'],
                "strategy": row.get('strategy', ''),
                "themes": themes
            })

        # Get date from file
        ticker_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
        data_date = Path(ticker_files[-1]).stem.split('_')[-1] if ticker_files else None

        return {
            "candidates": candidates,
            "count": len(candidates),
            "total_supertrend": len(df[df['stage'].str.contains('Super Trend', case=False, na=False)]),
            "date": data_date,
            "expected_return": "+2.10% (20D avg)",
            "note": "Super Trend = Strong momentum in bull regime"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Daily Summary - try local data/ first (Railway), then NAS (local dev)
LOCAL_RANKINGS_DIR = Path(__file__).parent.parent.parent.parent / "data"
NAS_RANKINGS_DIR = Path("/mnt/nas/AutoGluon/AutoML_Krx/Backtest/Rankings")


def get_daily_summary_files():
    """Find daily summary files, checking local first then NAS"""
    # Try local data/ folder first (Railway deployment)
    local_files = sorted(glob.glob(str(LOCAL_RANKINGS_DIR / "daily_summary_*.json")))
    if local_files:
        return local_files
    # Fallback to NAS (local development)
    nas_files = sorted(glob.glob(str(NAS_RANKINGS_DIR / "daily_summary_*.json")))
    return nas_files


@router.get("/daily-summary")
async def get_daily_summary(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    Get daily summary from AutoML Rankings
    Includes top performers and hidden gems with composite scores
    """
    try:
        if date:
            # Check local first, then NAS
            summary_file = LOCAL_RANKINGS_DIR / f"daily_summary_{date}.json"
            if not summary_file.exists():
                summary_file = NAS_RANKINGS_DIR / f"daily_summary_{date}.json"
        else:
            # Find latest
            summary_files = get_daily_summary_files()
            if not summary_files:
                raise HTTPException(status_code=404, detail="No daily summary data found")
            summary_file = Path(summary_files[-1])

        if not summary_file.exists():
            raise HTTPException(status_code=404, detail=f"Summary not found: {summary_file.name}")

        with open(summary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "date": data.get("date"),
            "generated_at": data.get("generated_at"),
            "total_tickers": data.get("total_tickers", 0),
            "top_performers": data.get("top_performers", [])[:10],
            "hidden_gems": data.get("hidden_gems", [])[:5],
            "note": data.get("note", "")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# BB Filter Paths - try local first (Railway), then NAS (local dev)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
LOCAL_BB_FILTER_PATH = PROJECT_ROOT / "data" / "bb_filter" / "bb_filtered_tickers.json"
NAS_BB_FILTER_PATH = Path("/mnt/nas/AutoGluon/AutoML_Krx/working_filter_BB/Filter/bb_filtered_tickers.json")

def get_bb_filter_path():
    """Get BB filter path - local first, then NAS"""
    if LOCAL_BB_FILTER_PATH.exists():
        return LOCAL_BB_FILTER_PATH
    return NAS_BB_FILTER_PATH


@router.get("/bb-crossover")
async def get_bb_crossover_tickers(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """
    Get BB(220, 2.0) crossover tickers - stocks that crossed above upper Bollinger Band
    These are momentum breakout signals based on BB upper band crossover
    """
    try:
        bb_filter_path = get_bb_filter_path()
        if not bb_filter_path.exists():
            raise HTTPException(status_code=404, detail="BB filter data not found")

        with open(bb_filter_path, 'r', encoding='utf-8') as f:
            bb_data = json.load(f)

        # Get tickers for requested date or latest
        if date:
            target_date = date
        else:
            # Find latest date in the data
            if not bb_data:
                raise HTTPException(status_code=404, detail="No BB crossover data available")
            target_date = max(bb_data.keys())

        tickers = bb_data.get(target_date, [])

        # Get theme mapping for enrichment
        theme_map = get_theme_mapping()

        # Enrich tickers with theme info
        enriched_tickers = []
        for item in tickers:
            # Handle both old format (string) and new format (dict with deviation)
            if isinstance(item, dict):
                ticker = item.get('ticker', '')
                deviation_pct = item.get('deviation_pct', 0)
            else:
                ticker = item
                deviation_pct = 0

            themes = theme_map.get(ticker, '[]')
            if pd.isna(themes) or themes == 'nan':
                themes = '[]'
            enriched_tickers.append({
                "ticker": ticker,
                "themes": themes,
                "signal": "BB Upper Crossover",
                "deviation_pct": deviation_pct
            })

        return {
            "date": target_date,
            "tickers": enriched_tickers,
            "count": len(enriched_tickers),
            "description": "Tickers that crossed above BB(220, 2.0) upper band",
            "note": "Yesterday: below or at upper BB → Today: above upper BB"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
