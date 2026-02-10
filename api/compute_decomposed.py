#!/usr/bin/env python3
"""
Decomposed Fiedler Analysis: Stress + Divergence Regime Framework

Computes sector-level Fiedler decomposition:
- within_sector: average Fiedler across themes (sector momentum)
- cross_sector: std dev of Fiedler across themes (cross-sector dispersion)
- stress_index: rate of change in cross-sector correlation
- divergence: cross rising while within falling (fragmentation signal)

Regime classification based on empirical analysis of 504 trading days:
- High sync = MOMENTUM (positive forward returns), NOT danger
- Stress is coincident (not leading) - spikes during/after crashes
- Divergence (cross rising + within falling) is the only useful leading signal
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR


FIEDLER_WEEKLY_CSV = DATA_DIR / "naver_themes_weekly_fiedler_2025.csv"
OUTPUT_DIR = DATA_DIR
TIMESERIES_CSV = DATA_DIR / "sector_fiedler_timeseries.csv"
STRESS_CSV = DATA_DIR / "market_stress_index_daily.csv"
LATEST_JSON = DATA_DIR / "decomposed_latest.json"


def load_fiedler_data() -> pd.DataFrame:
    """Load weekly Fiedler data for all themes."""
    if not FIEDLER_WEEKLY_CSV.exists():
        raise FileNotFoundError(f"Weekly Fiedler data not found: {FIEDLER_WEEKLY_CSV}")
    df = pd.read_csv(FIEDLER_WEEKLY_CSV)
    df['date'] = pd.to_datetime(df['date'])
    # Only use connected themes with valid Fiedler
    df = df[df['is_connected'].astype(str).str.lower() == 'true'].copy()
    df = df[df['fiedler'] > 0].copy()
    return df


def compute_sector_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute sector-level decomposition for each date.

    Returns DataFrame with columns:
    - date, within_sector, cross_sector, n_themes, mean_correlation
    """
    rows = []
    for date, group in df.groupby('date'):
        fiedler_vals = group['fiedler'].values
        if len(fiedler_vals) < 5:
            continue

        within = float(np.mean(fiedler_vals))
        cross = float(np.std(fiedler_vals))
        mean_corr = float(group['mean_correlation'].mean()) if 'mean_correlation' in group.columns else 0.0

        rows.append({
            'date': date,
            'within_sector': round(within, 4),
            'cross_sector': round(cross, 4),
            'n_themes': len(fiedler_vals),
            'mean_correlation': round(mean_corr, 4),
        })

    ts = pd.DataFrame(rows).sort_values('date').reset_index(drop=True)
    return ts


def compute_stress_index(ts: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Compute market stress index from sector timeseries.

    stress = rolling std of cross_sector changes (volatility of dispersion)
    Captures rapid changes in sector dispersion = stress events.
    """
    ts = ts.copy()
    ts['cross_change'] = ts['cross_sector'].diff()
    ts['within_change'] = ts['within_sector'].diff()

    # Stress = rolling volatility of cross-sector changes * amplification factor
    # Factor=5 calibrated for weekly data: median stress ~1.5, normal <2, elevated 2-5, crisis >5
    ts['stress_index'] = (
        ts['cross_change'].rolling(window=window, min_periods=2).std() * 5
    ).fillna(0).round(4)

    # Stress acceleration (5-period change in stress)
    ts['stress_accel'] = ts['stress_index'].diff(periods=min(5, len(ts) - 1)).fillna(0).round(4)

    # Divergence = cross rising while within falling
    # Positive divergence = sectors fragmenting while cross-sector tightens (bearish)
    cross_ma = ts['cross_sector'].rolling(window=3, min_periods=1).mean()
    within_ma = ts['within_sector'].rolling(window=3, min_periods=1).mean()
    cross_chg = cross_ma.diff().fillna(0)
    within_chg = within_ma.diff().fillna(0)

    # divergence > 0 means cross rising + within falling
    ts['divergence'] = (cross_chg - within_chg).round(4)

    return ts


def classify_regime(within: float, cross: float, stress: float, divergence: float) -> str:
    """
    Classify market regime using stress + divergence model.

    Regimes:
    - STRESS_EVENT: stress > 5 (active crisis, forced correlation)
    - CAUTION: stress 2-5 OR divergence > 0.2 (transition/fragmentation)
    - MOMENTUM: within > 0.8, stress < 2, divergence <= 0.2 (healthy bull)
    - DIFFERENTIATED: within <= 0.8, stress < 2 (stock-picking)
    """
    if stress > 5:
        return "STRESS_EVENT"
    if stress > 2 or divergence > 0.2:
        return "CAUTION"
    if within > 0.8 and stress < 2 and divergence <= 0.2:
        return "MOMENTUM"
    return "DIFFERENTIATED"


def compute_risk_score(stress: float, divergence: float, stress_accel: float) -> float:
    """
    Compute risk score (0-100) based on stress, divergence, and stress acceleration.

    Formula: stress_pct*0.60 + divergence_pct*0.25 + stress_accel_pct*0.15
    """
    stress_pct = min(stress / 10 * 100, 100)
    divergence_pct = min(max(divergence, 0) / 0.5 * 100, 100)
    stress_accel_pct = min(max(stress_accel, 0) / 3 * 100, 100)

    score = stress_pct * 0.60 + divergence_pct * 0.25 + stress_accel_pct * 0.15
    return round(min(max(score, 0), 100), 1)


def generate_alerts(stress: float, divergence: float, within: float) -> list:
    """
    Generate alerts based on stress/divergence model.

    Levels:
    - CRITICAL: stress > 10 (crisis in progress)
    - WARNING: stress > 5 (stress event detected)
    - CAUTION: stress 2-5 (fragility rising)
    - DIVERGENCE: divergence > 0.2 (sector fragmentation)
    - INFO: within > 1.5 (strong momentum, not danger)
    """
    alerts = []

    if stress > 10:
        alerts.append({
            "level": "CRITICAL",
            "message": "Crisis in progress — forced correlation across all sectors",
            "message_ko": "위기 진행 중 — 전 섹터 강제 상관관계",
            "value": round(stress, 2),
            "metric": "stress_index"
        })
    elif stress > 5:
        alerts.append({
            "level": "WARNING",
            "message": "Stress event detected — portfolio at risk of correlated drawdown",
            "message_ko": "스트레스 이벤트 감지 — 포트폴리오 상관 하락 위험",
            "value": round(stress, 2),
            "metric": "stress_index"
        })
    elif stress > 2:
        alerts.append({
            "level": "CAUTION",
            "message": "Connection fragility rising — review hedge positions",
            "message_ko": "연결 취약성 상승 — 헤지 포지션 검토 필요",
            "value": round(stress, 2),
            "metric": "stress_index"
        })

    if divergence > 0.2:
        alerts.append({
            "level": "DIVERGENCE",
            "message": "Sectors fragmenting while cross-sector tightens — historically weak forward returns",
            "message_ko": "섹터 분열 진행 중 — 역사적으로 부진한 선행 수익률",
            "value": round(divergence, 4),
            "metric": "divergence"
        })

    if within > 1.5 and stress <= 2:
        alerts.append({
            "level": "INFO",
            "message": "Strong sector momentum — factor-driven market",
            "message_ko": "강한 섹터 모멘텀 — 팩터 주도 시장",
            "value": round(within, 4),
            "metric": "within_sector"
        })

    return alerts


def compute() -> dict:
    """
    Main computation: load data, compute decomposition, classify regime, generate alerts.

    Returns dict with full analysis output and saves to files.
    """
    # Load and compute
    df = load_fiedler_data()
    ts = compute_sector_timeseries(df)
    ts = compute_stress_index(ts)

    # Save timeseries
    ts.to_csv(TIMESERIES_CSV, index=False)

    # Save stress data
    stress_cols = ['date', 'stress_index', 'stress_accel', 'divergence']
    ts[stress_cols].to_csv(STRESS_CSV, index=False)

    # Get latest values
    latest = ts.iloc[-1]
    within = float(latest['within_sector'])
    cross = float(latest['cross_sector'])
    stress = float(latest['stress_index'])
    stress_accel = float(latest['stress_accel'])
    divergence = float(latest['divergence'])

    # Classify and score
    regime = classify_regime(within, cross, stress, divergence)
    risk_score = compute_risk_score(stress, divergence, stress_accel)
    alerts = generate_alerts(stress, divergence, within)

    # Build output
    output = {
        "date": latest['date'].strftime('%Y-%m-%d') if hasattr(latest['date'], 'strftime') else str(latest['date']),
        "computed_at": datetime.now().isoformat(),
        "regime": regime,
        "risk_score": risk_score,
        "metrics": {
            "within_sector": round(within, 4),
            "cross_sector": round(cross, 4),
            "stress_index": round(stress, 4),
            "stress_accel": round(stress_accel, 4),
            "divergence": round(divergence, 4),
            "n_themes": int(latest['n_themes']),
            "mean_correlation": round(float(latest['mean_correlation']), 4),
        },
        "alerts": alerts,
        "regime_description": _regime_description(regime),
        "timeseries_rows": len(ts),
    }

    # Save latest
    with open(LATEST_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output


def _regime_description(regime: str) -> dict:
    """Get regime description in English and Korean."""
    descriptions = {
        "STRESS_EVENT": {
            "en": "Active stress event — correlated drawdown risk",
            "ko": "스트레스 이벤트 — 상관 하락 위험",
            "color": "red",
            "action_en": "Reduce risk exposure, maximize hedges",
            "action_ko": "리스크 노출 축소, 헤지 최대화",
        },
        "CAUTION": {
            "en": "Elevated caution — stress building",
            "ko": "경계 수준 상승 — 스트레스 누적 중",
            "color": "amber",
            "action_en": "Review hedge positions, reduce concentration",
            "action_ko": "헤지 포지션 검토, 집중도 축소",
        },
        "MOMENTUM": {
            "en": "Factor momentum — healthy sector synchronization",
            "ko": "팩터 모멘텀 — 건강한 섹터 동조화",
            "color": "blue",
            "action_en": "Ride sector trends, maintain factor exposure",
            "action_ko": "섹터 트렌드 추종, 팩터 노출 유지",
        },
        "DIFFERENTIATED": {
            "en": "Independent moves — stock-picking environment",
            "ko": "독립적 움직임 — 종목 선별 환경",
            "color": "emerald",
            "action_en": "Focus on individual stock analysis",
            "action_ko": "개별 종목 분석에 집중",
        },
    }
    return descriptions.get(regime, descriptions["DIFFERENTIATED"])


if __name__ == "__main__":
    print("Computing decomposed Fiedler analysis...")
    result = compute()
    print(f"\nRegime: {result['regime']}")
    print(f"Risk Score: {result['risk_score']}")
    print(f"Metrics: {json.dumps(result['metrics'], indent=2)}")
    print(f"Alerts: {len(result['alerts'])}")
    for a in result['alerts']:
        print(f"  [{a['level']}] {a['message']}")
    print(f"\nTimeseries: {result['timeseries_rows']} rows saved to {TIMESERIES_CSV}")
    print(f"Latest JSON saved to {LATEST_JSON}")
