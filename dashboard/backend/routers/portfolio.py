"""
Portfolio Performance Dashboard API Endpoints
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

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "backtest"))

router = APIRouter()

try:
    from backtest.statistical_analysis import StatisticalAnalyzer
    HAS_ANALYZER = True
except ImportError:
    HAS_ANALYZER = False

@router.get("/performance")
async def get_portfolio_performance(
    results_file: Optional[str] = Query(None, description="Backtest results CSV file"),
    start_date: Optional[str] = Query(None, description="Start date"),
    end_date: Optional[str] = Query(None, description="End date")
):
    """Get portfolio performance metrics"""
    try:
        if results_file:
            df = pd.read_csv(results_file)
        else:
            # Find latest backtest results
            results_files = sorted(glob.glob(str(Path(__file__).parent.parent.parent.parent / "backtest" / "results" / "signal_performance_*.csv")))
            if not results_files:
                raise HTTPException(status_code=404, detail="No backtest results found")
            df = pd.read_csv(results_files[-1])
        
        # Filter by date if provided
        if 'date' in df.columns or 'signal_date' in df.columns:
            date_col = 'date' if 'date' in df.columns else 'signal_date'
            df[date_col] = pd.to_datetime(df[date_col])
            if start_date:
                df = df[df[date_col] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df[date_col] <= pd.to_datetime(end_date)]
        
        if HAS_ANALYZER:
            analyzer = StatisticalAnalyzer(df)
            metrics = analyzer.calculate_performance_metrics()
        else:
            # Calculate manually
            metrics = {
                'n_signals': len(df),
                'win_rate': (df['total_return'] > 0).mean() if 'total_return' in df.columns else 0,
                'avg_return': df['total_return'].mean() if 'total_return' in df.columns else 0,
                'median_return': df['total_return'].median() if 'total_return' in df.columns else 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        return {
            "metrics": metrics,
            "period": {
                "start": start_date or df[date_col].min().strftime('%Y-%m-%d') if date_col in df.columns else None,
                "end": end_date or df[date_col].max().strftime('%Y-%m-%d') if date_col in df.columns else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/returns-timeseries")
async def get_returns_timeseries(
    results_file: Optional[str] = Query(None, description="Backtest results CSV file"),
    period: str = Query("weekly", description="Aggregation period: daily, weekly, monthly")
):
    """Get cumulative returns time series"""
    try:
        if results_file:
            df = pd.read_csv(results_file)
        else:
            results_files = sorted(glob.glob(str(Path(__file__).parent.parent.parent.parent / "backtest" / "results" / "signal_performance_*.csv")))
            if not results_files:
                raise HTTPException(status_code=404, detail="No backtest results found")
            df = pd.read_csv(results_files[-1])
        
        # Get date column
        date_col = 'date' if 'date' in df.columns else 'signal_date'
        if date_col not in df.columns:
            raise HTTPException(status_code=400, detail="No date column found")
        
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)
        
        # Aggregate by period
        if period == "daily":
            df_grouped = df.groupby(date_col)
        elif period == "weekly":
            df[date_col + '_week'] = df[date_col].dt.to_period('W')
            df_grouped = df.groupby(date_col + '_week')
        elif period == "monthly":
            df[date_col + '_month'] = df[date_col].dt.to_period('M')
            df_grouped = df.groupby(date_col + '_month')
        else:
            df_grouped = df.groupby(date_col)
        
        # Calculate cumulative returns
        returns = []
        cumulative = 0
        
        for period_key, group in df_grouped:
            period_return = group['total_return'].mean() if 'total_return' in group.columns else 0
            cumulative += period_return
            
            returns.append({
                "date": str(period_key),
                "period_return": period_return,
                "cumulative_return": cumulative
            })
        
        return {
            "timeseries": returns,
            "period": period,
            "total_return": cumulative
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drawdown")
async def get_drawdown(
    results_file: Optional[str] = Query(None, description="Backtest results CSV file")
):
    """Get drawdown analysis"""
    try:
        if results_file:
            df = pd.read_csv(results_file)
        else:
            results_files = sorted(glob.glob(str(Path(__file__).parent.parent.parent.parent / "backtest" / "results" / "signal_performance_*.csv")))
            if not results_files:
                raise HTTPException(status_code=404, detail="No backtest results found")
            df = pd.read_csv(results_files[-1])
        
        if 'total_return' not in df.columns:
            raise HTTPException(status_code=400, detail="No return data found")
        
        # Calculate drawdown
        returns = df['total_return'].values
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        
        return {
            "max_drawdown": float(drawdown.min()),
            "max_drawdown_pct": float((drawdown.min() / running_max.max()) * 100) if running_max.max() > 0 else 0,
            "current_drawdown": float(drawdown[-1]),
            "drawdown_timeseries": [
                {"index": i, "drawdown": float(dd)} 
                for i, dd in enumerate(drawdown)
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-signal-type")
async def get_performance_by_signal_type(
    results_file: Optional[str] = Query(None, description="Backtest results CSV file")
):
    """Get performance breakdown by signal type"""
    try:
        if results_file:
            df = pd.read_csv(results_file)
        else:
            results_files = sorted(glob.glob(str(Path(__file__).parent.parent.parent.parent / "backtest" / "results" / "signal_performance_*.csv")))
            if not results_files:
                raise HTTPException(status_code=404, detail="No backtest results found")
            df = pd.read_csv(results_files[-1])
        
        if 'signal_type' not in df.columns or 'total_return' not in df.columns:
            raise HTTPException(status_code=400, detail="Required columns not found")
        
        # Group by signal type
        performance_by_type = []
        for signal_type in df['signal_type'].unique():
            type_df = df[df['signal_type'] == signal_type]
            performance_by_type.append({
                "signal_type": signal_type,
                "count": len(type_df),
                "win_rate": (type_df['total_return'] > 0).mean() * 100,
                "avg_return": type_df['total_return'].mean(),
                "median_return": type_df['total_return'].median(),
                "sharpe_ratio": type_df['total_return'].mean() / type_df['total_return'].std() if type_df['total_return'].std() > 0 else 0
            })
        
        return {
            "performance_by_type": sorted(performance_by_type, key=lambda x: x['avg_return'], reverse=True),
            "total_signals": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/by-tier")
async def get_performance_by_tier(
    results_file: Optional[str] = Query(None, description="Backtest results CSV file")
):
    """Get performance breakdown by tier"""
    try:
        if results_file:
            df = pd.read_csv(results_file)
        else:
            results_files = sorted(glob.glob(str(Path(__file__).parent.parent.parent.parent / "backtest" / "results" / "signal_performance_*.csv")))
            if not results_files:
                raise HTTPException(status_code=404, detail="No backtest results found")
            df = pd.read_csv(results_files[-1])
        
        if 'tier' not in df.columns or 'total_return' not in df.columns:
            raise HTTPException(status_code=400, detail="Required columns not found")
        
        # Group by tier
        performance_by_tier = []
        for tier in sorted(df['tier'].dropna().unique()):
            tier_df = df[df['tier'] == tier]
            performance_by_tier.append({
                "tier": int(tier),
                "count": len(tier_df),
                "win_rate": (tier_df['total_return'] > 0).mean() * 100,
                "avg_return": tier_df['total_return'].mean(),
                "median_return": tier_df['total_return'].median()
            })
        
        return {
            "performance_by_tier": performance_by_tier,
            "total_signals": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

