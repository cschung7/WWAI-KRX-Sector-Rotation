"""
Decomposed Fiedler Regime API Router

Provides endpoints for stress + divergence regime framework:
- /regime/current - Current regime classification with alerts
- /regime/timeseries - Historical sector decomposition
- /regime/compute - Trigger recomputation
"""

import json
import sys
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR

router = APIRouter()

LATEST_JSON = DATA_DIR / "decomposed_latest.json"
TIMESERIES_CSV = DATA_DIR / "sector_fiedler_timeseries.csv"


def _load_latest() -> dict:
    """Load the latest computed decomposition, computing if needed."""
    if not LATEST_JSON.exists():
        _recompute()
    if not LATEST_JSON.exists():
        raise HTTPException(status_code=404, detail="Decomposed analysis not available")
    with open(LATEST_JSON, encoding='utf-8') as f:
        return json.load(f)


def _recompute():
    """Run the computation pipeline."""
    try:
        from api.compute_decomposed import compute
        compute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Computation failed: {e}")


@router.get("/current")
async def get_current_regime():
    """
    Get current market regime with stress/divergence metrics and alerts.

    Returns:
    - regime: STRESS_EVENT | CAUTION | MOMENTUM | DIFFERENTIATED
    - risk_score: 0-100
    - metrics: within_sector, cross_sector, stress_index, divergence, stress_accel
    - alerts: list of active alerts
    - regime_description: en/ko descriptions with color and action
    """
    data = _load_latest()
    return data


@router.get("/timeseries")
async def get_regime_timeseries(
    limit: Optional[int] = Query(None, description="Limit to last N rows"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)")
):
    """
    Get historical sector decomposition timeseries.

    Returns within_sector, cross_sector, stress_index, divergence per date.
    """
    if not TIMESERIES_CSV.exists():
        _recompute()
    if not TIMESERIES_CSV.exists():
        raise HTTPException(status_code=404, detail="Timeseries data not available")

    df = pd.read_csv(TIMESERIES_CSV)

    if start_date:
        df = df[df['date'] >= start_date]

    if limit:
        df = df.tail(limit)

    # Classify regime for each row
    from api.compute_decomposed import classify_regime
    regimes = []
    for _, row in df.iterrows():
        reg = classify_regime(
            row['within_sector'], row['cross_sector'],
            row['stress_index'], row['divergence']
        )
        regimes.append(reg)
    df['regime'] = regimes

    records = df.to_dict(orient='records')
    # Round floats for JSON
    for r in records:
        for k, v in r.items():
            if isinstance(v, float):
                r[k] = round(v, 4)

    return {
        "timeseries": records,
        "count": len(records),
    }


@router.post("/compute")
async def trigger_compute():
    """Trigger recomputation of decomposed Fiedler analysis."""
    _recompute()
    data = _load_latest()
    return {"status": "ok", "result": data}
