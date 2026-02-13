"""
Data Freshness Monitoring Router

Reports staleness status for all data sources backing the KRX dashboard.
GET /api/freshness → comprehensive JSON report.
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from pathlib import Path
import glob
import os
import re

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import DATA_DIR

router = APIRouter()

# ── Data source definitions ─────────────────────────────────────────────────

DATA_SOURCES = [
    {
        "name": "actionable_tickers",
        "description": "모멘텀 종목 (Momentum Candidates)",
        "pattern": "actionable_tickers_*.csv",
        "date_format": "%Y%m%d",         # YYYYMMDD
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/breakout/candidates", "/api/breakout/stages", "/api/breakout/top-picks"],
    },
    {
        "name": "consolidated_analysis",
        "description": "종합 분석 (Consolidated Ticker Analysis)",
        "pattern": "consolidated_ticker_analysis_*.json",
        "date_format": "%Y%m%d",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/breakout/ranking-dates"],
    },
    {
        "name": "daily_summary",
        "description": "일간 요약 (Daily Summary)",
        "pattern": "daily_summary_*.json",
        "date_format": "%Y-%m-%d",       # YYYY-MM-DD
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/breakout/daily-summary"],
    },
    {
        "name": "signal_scores",
        "description": "시그널 점수 (Signal Scores)",
        "file": "signal_scores.json",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/network/graph-data"],
    },
    {
        "name": "decomposed_regime",
        "description": "시장 국면 (Market Regime)",
        "file": "decomposed_latest.json",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/regime/current"],
    },
    {
        "name": "market_stress",
        "description": "시장 스트레스 (Market Stress Index)",
        "file": "market_stress_index_daily.csv",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/regime/timeseries"],
    },
    {
        "name": "sector_fiedler_ts",
        "description": "섹터 피들러 시계열 (Sector Fiedler Timeseries)",
        "file": "sector_fiedler_timeseries.csv",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/regime/timeseries"],
    },
    {
        "name": "theme_ucs_scores",
        "description": "테마 UCS 점수 (Theme UCS Scores)",
        "file": "theme_ucs_scores.json",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/network/theme-ucs"],
    },
    {
        "name": "network_theme_data",
        "description": "네트워크 테마 데이터 (Network Theme Data)",
        "file": "network_theme_data.csv",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/network/graph-data", "/api/network/search"],
    },
    {
        "name": "bb_filtered",
        "description": "BB 필터 종목 (BB Filtered Tickers)",
        "file": "bb_filter/bb_filtered_tickers.json",
        "schedule": "daily",
        "stale_hours": 26,
        "endpoints": ["/api/breakout/bb-crossover"],
    },
    {
        "name": "weekly_fiedler",
        "description": "주간 피들러 (Weekly Theme Fiedler)",
        "file": "naver_themes_weekly_fiedler_2025.csv",
        "schedule": "weekly",
        "stale_hours": 192,              # 8 days
        "endpoints": ["/api/sector-rotation/themes", "/api/sector-rotation/cohesion"],
    },
    {
        "name": "tier_classification",
        "description": "TIER 분류 (TIER Classification)",
        "pattern": "4tier_summary_*.json",
        "date_format": "%Y%m%d",
        "schedule": "weekly",
        "stale_hours": 192,
        "endpoints": ["/api/sector-rotation/tier-classification"],
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _find_latest_dated_file(pattern: str, date_format: str):
    """Find the latest date-suffixed file matching *pattern* under DATA_DIR."""
    matches = sorted(glob.glob(str(DATA_DIR / pattern)))
    if not matches:
        return None, None
    latest = matches[-1]
    # Extract date string from filename
    basename = Path(latest).stem  # e.g. actionable_tickers_20260212
    # Try to pull the date suffix after the last underscore (or hyphen-date)
    m = re.search(r'(\d{4}-\d{2}-\d{2}|\d{8})$', basename)
    data_date = m.group(1) if m else None
    return latest, data_date


def _check_source(src: dict, now: datetime):
    """Return a status dict for one data source."""
    result = {
        "name": src["name"],
        "description": src["description"],
        "schedule": src["schedule"],
        "endpoints": src["endpoints"],
    }

    if "pattern" in src:
        filepath, data_date = _find_latest_dated_file(src["pattern"], src["date_format"])
    else:
        filepath = str(DATA_DIR / src["file"])
        data_date = None
        if not os.path.exists(filepath):
            filepath = None

    if filepath is None or not os.path.exists(filepath):
        result.update(
            file=None,
            last_updated=None,
            data_date=data_date,
            status="missing",
            age_hours=None,
        )
        return result

    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
    age = now - mtime
    age_hours = round(age.total_seconds() / 3600, 1)
    status = "fresh" if age_hours < src["stale_hours"] else "stale"

    result.update(
        file=Path(filepath).name,
        last_updated=mtime.isoformat(timespec="seconds"),
        data_date=data_date,
        status=status,
        age_hours=age_hours,
    )
    return result


def _market_date(now: datetime) -> str:
    """Return the most recent market date (skip weekends)."""
    d = now.date()
    # Saturday=5, Sunday=6
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.get("")
async def get_freshness():
    """Report freshness status for every data source backing the dashboard."""
    now = datetime.now()
    sources = [_check_source(src, now) for src in DATA_SOURCES]

    fresh = sum(1 for s in sources if s["status"] == "fresh")
    stale = sum(1 for s in sources if s["status"] == "stale")
    missing = sum(1 for s in sources if s["status"] == "missing")
    total = len(sources)

    if missing > 0 or stale >= 4:
        overall = "critical"
    elif stale > 0:
        overall = "warning"
    else:
        overall = "healthy"

    return {
        "checked_at": now.isoformat(timespec="seconds"),
        "market_date": _market_date(now),
        "overall_status": overall,
        "summary": {
            "total": total,
            "fresh": fresh,
            "stale": stale,
            "missing": missing,
        },
        "sources": sources,
    }
