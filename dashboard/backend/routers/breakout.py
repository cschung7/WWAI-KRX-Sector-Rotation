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

router = APIRouter()

def load_latest_actionable_tickers(date: Optional[str] = None) -> pd.DataFrame:
    """Load actionable tickers data"""
    if date:
        date_str = date.replace('-', '')
        ticker_file = DATA_DIR / f"actionable_tickers_{date_str}.csv"
    else:
        # Find latest
        ticker_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
        if not ticker_files:
            raise HTTPException(status_code=404, detail="No actionable tickers data found")
        ticker_file = Path(ticker_files[-1])

    if not ticker_file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {ticker_file}")

    return pd.read_csv(ticker_file)


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

        # Convert to list of dicts
        candidates = []
        for _, row in df.iterrows():
            candidates.append({
                "ticker": row['ticker'],
                "strategy": row.get('strategy', ''),
                "score": int(row['score']),
                "stage": row['stage'],
                "themes": row.get('themes', '[]'),
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

        picks = []
        for rank, (_, row) in enumerate(early_breakout.iterrows(), 1):
            picks.append({
                "rank": rank,
                "ticker": row['ticker'],
                "score": int(row['score']),
                "strategy": row.get('strategy', ''),
                "themes": row.get('themes', '[]')
            })

        return {
            "picks": picks,
            "count": len(picks),
            "stage": "Early Breakout",
            "expected_return": "+7.93% (20D avg)"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
