"""
Sector Rotation Dashboard API Endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
from pathlib import Path
import glob
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import DATA_DIR, REPORTS_DIR

router = APIRouter()

@router.get("/themes")
async def get_themes(
    date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD)")
):
    """Get themes with Fiedler values"""
    try:
        # Load latest enhanced cohesion themes
        if date:
            date_str = date.replace('-', '')
            cohesion_file = DATA_DIR / f"enhanced_cohesion_themes_{date_str}.csv"
        else:
            # Find latest
            cohesion_files = sorted(glob.glob(str(DATA_DIR / "enhanced_cohesion_themes_*.csv")))
            if not cohesion_files:
                raise HTTPException(status_code=404, detail="No cohesion data found")
            cohesion_file = Path(cohesion_files[-1])
        
        df = pd.read_csv(cohesion_file)

        # Format for frontend (handle both column naming conventions)
        themes = []
        for _, row in df.iterrows():
            themes.append({
                "theme": row.get('theme', row.get('Theme', '')),
                "current_fiedler": float(row.get('current_fiedler', row.get('Current_Fiedler', 0))),
                "fiedler_change": float(row.get('fiedler_change', row.get('Change', 0))),
                "pct_change": float(row.get('pct_change', row.get('Pct_Change', 0))),
                "n_stocks": int(row.get('n_stocks', row.get('Stocks', 0))),
                "enhancement_score": float(row.get('enhancement_score', row.get('Enhancement_Score', 0))) if 'enhancement_score' in row or 'Enhancement_Score' in row else 0,
                "date": str(row.get('current_date', date) if date else row.get('current_date', ''))
            })
        
        return {
            "themes": themes,
            "count": len(themes),
            "date": date or cohesion_file.stem.split('_')[-1]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fiedler-timeseries")
async def get_fiedler_timeseries(
    theme: str = Query(..., description="Theme name"),
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date")
):
    """Get Fiedler value time series for a theme"""
    try:
        # Load theme timeseries
        theme_safe = theme.replace(' ', '_').replace('/', '_')
        timeseries_file = DATA_DIR / f"theme_{theme_safe}_timeseries.csv"
        
        if not timeseries_file.exists():
            raise HTTPException(status_code=404, detail=f"Timeseries not found for theme: {theme}")
        
        df = pd.read_csv(timeseries_file)
        df['date'] = pd.to_datetime(df['date'])
        
        # Filter by date range
        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]
        
        # Format for frontend
        timeseries = []
        for _, row in df.iterrows():
            timeseries.append({
                "date": row['date'].strftime('%Y-%m-%d'),
                "fiedler": float(row.get('fiedler', 0)),
                "n_stocks": int(row.get('n_stocks', 0))
            })
        
        return {
            "theme": theme,
            "timeseries": timeseries,
            "count": len(timeseries)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tier-classification")
async def get_tier_classification(
    date: Optional[str] = Query(None, description="Analysis date (YYYY-MM-DD)")
):
    """Get 4-tier classification"""
    try:
        # Determine date string
        if date:
            date_str = date.replace('-', '')
        else:
            # Find latest tier files
            tier1_files = sorted(glob.glob(str(DATA_DIR / "tier1_buy_now_*.csv")))
            if not tier1_files:
                raise HTTPException(status_code=404, detail="No tier classification data found")
            # Extract date from latest file
            latest_file = Path(tier1_files[-1])
            date_str = latest_file.stem.split('_')[-1]
        
        # Load individual tier files
        tier_files = {
            1: DATA_DIR / f"tier1_buy_now_{date_str}.csv",
            2: DATA_DIR / f"tier2_accumulate_{date_str}.csv",
            3: DATA_DIR / f"tier3_research_{date_str}.csv",
            4: DATA_DIR / f"tier4_monitor_{date_str}.csv"
        }
        
        tiers = {
            "tier1": [],
            "tier2": [],
            "tier3": [],
            "tier4": []
        }
        
        # Load each tier file
        for tier_num, tier_file in tier_files.items():
            if not tier_file.exists():
                continue  # Skip if file doesn't exist
            
            try:
                df = pd.read_csv(tier_file)
                
                # Handle different column name variations
                theme_col = None
                for col in ['Theme', 'theme', 'Sector', 'sector']:
                    if col in df.columns:
                        theme_col = col
                        break
                
                if theme_col is None:
                    continue
                
                # Extract theme data (without sensitive Fiedler values)
                for _, row in df.iterrows():
                    theme_data = {
                        "theme": row.get(theme_col, ''),
                        "tier": tier_num,
                        "n_stocks": row.get('Stocks', row.get('stocks', row.get('n_stocks', 0)))
                    }
                    
                    # Only add if theme name exists
                    if theme_data["theme"]:
                        tiers[f"tier{tier_num}"].append(theme_data)
            except Exception as e:
                print(f"Warning: Could not load {tier_file}: {e}")
                continue
        
        return {
            "tiers": tiers,
            "summary": {
                "tier1_count": len(tiers["tier1"]),
                "tier2_count": len(tiers["tier2"]),
                "tier3_count": len(tiers["tier3"]),
                "tier4_count": len(tiers["tier4"]),
                "total": len(tiers["tier1"]) + len(tiers["tier2"]) + len(tiers["tier3"]) + len(tiers["tier4"])
            },
            "date": date_str
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading tier classification: {str(e)}")

@router.get("/rotation-signals")
async def get_rotation_signals(
    date: Optional[str] = Query(None, description="Analysis date")
):
    """Get sector rotation signals (IN/OUT)"""
    try:
        # This would load from rotation signals data
        # For now, return example structure
        return {
            "signals": [
                {
                    "theme": "반도체",
                    "signal": "ROTATION_IN",
                    "date": date or "2025-11-13",
                    "fiedler": 3.5,
                    "fiedler_change": 1.5,
                    "confidence": "high"
                }
            ],
            "count": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leadership-gap")
async def get_leadership_gap(
    date: Optional[str] = Query(None, description="Analysis date")
):
    """Get leadership gap analysis"""
    try:
        # Load leadership data
        if date:
            date_str = date.replace('-', '')
            leadership_file = REPORTS_DIR / f"WITHIN_THEME_LEADERSHIP_{date_str}.md"
        else:
            leadership_files = sorted(glob.glob(str(REPORTS_DIR / "WITHIN_THEME_LEADERSHIP_*.md")))
            if not leadership_files:
                return {"themes": [], "count": 0}
            leadership_file = Path(leadership_files[-1])

        # Parse markdown (simplified)
        # In production, would parse the markdown properly
        return {
            "themes": [],
            "count": 0,
            "message": "Leadership gap data parsing not yet implemented"
        }
    except Exception as e:
        return {"themes": [], "count": 0, "error": str(e)}


@router.get("/fiedler-trends")
async def get_fiedler_trends(
    weeks: int = Query(8, description="Number of weeks for trend calculation"),
    min_data_points: int = Query(4, description="Minimum data points required")
):
    """
    Get Fiedler trend analysis for all themes.
    Calculates slope (trend direction), volatility, and categorizes themes.
    """
    try:
        # Load weekly Fiedler database
        weekly_file = DATA_DIR / "naver_themes_weekly_fiedler_2025.csv"
        if not weekly_file.exists():
            raise HTTPException(status_code=404, detail="Weekly Fiedler database not found")

        df = pd.read_csv(weekly_file)
        df['date'] = pd.to_datetime(df['date'])

        # Get latest N weeks
        latest_date = df['date'].max()
        cutoff_date = latest_date - pd.Timedelta(weeks=weeks)
        recent = df[df['date'] >= cutoff_date]

        # Calculate trends for each theme
        trends = []
        for theme in recent['theme'].unique():
            theme_data = recent[recent['theme'] == theme].sort_values('date')

            if len(theme_data) < min_data_points:
                continue

            fiedler_values = theme_data['fiedler'].values
            latest_fiedler = fiedler_values[-1]

            # Skip disconnected themes (Fiedler = 0)
            if latest_fiedler == 0 and not theme_data['is_connected'].iloc[-1]:
                continue

            # Calculate trend (slope)
            x = np.arange(len(fiedler_values))
            slope = np.polyfit(x, fiedler_values, 1)[0]

            # Calculate volatility (std dev)
            volatility = np.std(fiedler_values)

            # Calculate stats
            mean_fiedler = np.mean(fiedler_values)
            min_fiedler = np.min(fiedler_values)
            max_fiedler = np.max(fiedler_values)

            # Categorize trend
            if slope > 0.05:
                trend_direction = "increasing"
            elif slope < -0.05:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"

            # Categorize cohesion level
            if latest_fiedler > 3.0:
                cohesion_level = "very_strong"
            elif latest_fiedler >= 1.0:
                cohesion_level = "strong"
            elif latest_fiedler >= 0.5:
                cohesion_level = "moderate"
            else:
                cohesion_level = "weak"

            trends.append({
                "theme": theme,
                "latest_fiedler": round(latest_fiedler, 3),
                "slope": round(slope, 4),
                "trend_direction": trend_direction,
                "volatility": round(volatility, 3),
                "mean_fiedler": round(mean_fiedler, 3),
                "min_fiedler": round(min_fiedler, 3),
                "max_fiedler": round(max_fiedler, 3),
                "cohesion_level": cohesion_level,
                "n_stocks": int(theme_data['n_stocks'].iloc[-1]),
                "is_connected": bool(theme_data['is_connected'].iloc[-1]),
                "data_points": len(theme_data)
            })

        # Sort by slope (most increasing first)
        trends_sorted = sorted(trends, key=lambda x: x['slope'], reverse=True)

        # Summary statistics
        increasing = [t for t in trends if t['trend_direction'] == 'increasing']
        decreasing = [t for t in trends if t['trend_direction'] == 'decreasing']
        stable = [t for t in trends if t['trend_direction'] == 'stable']

        return {
            "trends": trends_sorted,
            "summary": {
                "total_themes": len(trends),
                "increasing": len(increasing),
                "decreasing": len(decreasing),
                "stable": len(stable),
                "top_increasing": [t['theme'] for t in increasing[:5]],
                "top_decreasing": [t['theme'] for t in decreasing[-5:][::-1]]
            },
            "parameters": {
                "weeks_analyzed": weeks,
                "min_data_points": min_data_points,
                "latest_date": latest_date.strftime('%Y-%m-%d')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

