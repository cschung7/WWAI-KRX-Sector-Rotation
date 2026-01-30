#!/usr/bin/env python3
"""
Shared Regime Utilities for Three-Layer Framework
Used by all report generation scripts to ensure consistent recommendations.

Three-Layer Framework:
- Layer 1: Cohesion (Fiedler values)
- Layer 2: Regime (Bull/Bear/Transition probabilities)
- Layer 3: Trend (Momentum direction)

Investment Criteria:
- BUY NOW: Bull >60% AND Trend >0.1
- WATCHLIST: Bull 40-60% AND Trend >-0.2
- AVOID: Bear >60% OR Trend <-0.3
"""

import pandas as pd
import ast
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REGIME_DIR, DB_FILE


def load_regime_data() -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Load latest regime data and return summary by stock name"""
    # Try regime_prob files first (newer format, more recent data)
    regime_prob_files = list(REGIME_DIR.glob("regime_prob_202*.csv"))
    all_regimes_files = list(REGIME_DIR.glob("all_regimes_*.csv"))

    # Prefer regime_prob files if they exist and are more recent
    if regime_prob_files:
        # Sort by date in filename (regime_prob_YYYY-MM-DD.csv)
        latest_file = sorted(regime_prob_files, key=lambda x: x.stem.replace('regime_prob_', ''))[-1]
        df = pd.read_csv(latest_file)
        latest_date = df['Date'].max()
        df = df[df['Date'] == latest_date].copy()
    elif all_regimes_files:
        latest_file = sorted(all_regimes_files)[-1]
        df = pd.read_csv(latest_file)
        latest_date = df['Date'].max()
        df = df[df['Date'] == latest_date].copy()
    else:
        return None, None

    regime_summary = df.groupby('Ticker', group_keys=False).apply(
        lambda x: pd.Series({
            'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Transition_Pct': (x['Is_Transition'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})

    return regime_summary, latest_date


def load_cohesion_data(date_str: str) -> pd.DataFrame:
    """Load cohesion data for a specific date, fallback to latest"""
    specific_file = DATA_DIR / f"enhanced_cohesion_themes_{date_str}.csv"
    if specific_file.exists():
        return pd.read_csv(specific_file)

    files = glob.glob(str(DATA_DIR / "enhanced_cohesion_themes_*.csv"))
    if files:
        return pd.read_csv(sorted(files)[-1])
    return pd.DataFrame()


def load_db_data() -> pd.DataFrame:
    """Load stock database"""
    return pd.read_csv(DB_FILE)


def calculate_theme_regime_stats(theme_name: str, db_df: pd.DataFrame,
                                  regime_summary: pd.DataFrame) -> Optional[Dict]:
    """
    Calculate regime statistics for a theme by aggregating stock-level data.

    Returns dict with:
    - avg_bull_pct: Average bull regime percentage
    - avg_bear_pct: Average bear regime percentage
    - avg_trend: Average trend strength
    - stock_count: Number of stocks with regime data
    - large_cap_bull: Bull % for large-caps (≥5T)
    - large_cap_stocks: List of large-cap stock details
    """
    theme_stocks = []
    for _, row in db_df.iterrows():
        themes_str = row.get('naverTheme', '[]')
        try:
            themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
            if isinstance(themes, list) and theme_name in themes:
                theme_stocks.append({
                    'name': row['name'],
                    'ticker': str(row['tickers']).zfill(6),
                    'market_cap': row['시가총액']
                })
        except:
            continue

    if not theme_stocks:
        return None

    regime_stats = []
    large_cap_stocks = []
    large_cap_threshold = 50  # 5T KRW (50 * 100B)

    for stock in theme_stocks:
        regime_row = regime_summary[regime_summary['Stock_Name'] == stock['name']]
        if not regime_row.empty:
            bull_pct = regime_row.iloc[0]['Bull_Pct']
            bear_pct = regime_row.iloc[0]['Bear_Pct']
            trend = regime_row.iloc[0]['Trend_Strength']
            momentum = regime_row.iloc[0]['Momentum_Score']

            regime_stats.append({
                'bull_pct': bull_pct,
                'bear_pct': bear_pct,
                'trend': trend,
                'momentum': momentum,
                'market_cap': stock['market_cap']
            })

            if stock['market_cap'] >= large_cap_threshold:
                large_cap_stocks.append({
                    'name': stock['name'],
                    'ticker': stock['ticker'],
                    'market_cap': stock['market_cap'] * 0.1,  # Convert to T
                    'bull_pct': bull_pct,
                    'trend': trend,
                    'momentum': momentum
                })

    if not regime_stats:
        return None

    stats_df = pd.DataFrame(regime_stats)
    large_cap_df = stats_df[stats_df['market_cap'] >= large_cap_threshold]

    # Sort large caps by market cap
    large_cap_stocks.sort(key=lambda x: x['market_cap'], reverse=True)

    return {
        'theme': theme_name,
        'avg_bull_pct': stats_df['bull_pct'].mean(),
        'avg_bear_pct': stats_df['bear_pct'].mean(),
        'avg_trend': stats_df['trend'].mean(),
        'avg_momentum': stats_df['momentum'].mean(),
        'stock_count': len(stats_df),
        'large_cap_bull': large_cap_df['bull_pct'].mean() if len(large_cap_df) > 0 else 0,
        'large_cap_count': len(large_cap_df),
        'large_cap_stocks': large_cap_stocks,
        'leadership_gap': (large_cap_df['bull_pct'].mean() - stats_df['bull_pct'].mean()) if len(large_cap_df) > 0 else 0
    }


def classify_themes_with_regime(cohesion_df: pd.DataFrame,
                                 regime_summary: pd.DataFrame,
                                 db_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Classify themes using Three-Layer Framework (Cohesion × Regime × Trend).

    Returns:
    - buy_now: Bull >60% AND Trend >0.1 (regime-validated BUY)
    - watchlist: Bull 40-60% AND Trend >-0.2 (watch for regime shift)
    - avoid: Bear >60% OR Trend <-0.3 (avoid long positions)
    - all_stats: All theme statistics for reference
    """
    if cohesion_df.empty or regime_summary is None:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    theme_data = []

    for _, row in cohesion_df.iterrows():
        theme_name = row.get('theme', row.get('Theme', 'Unknown'))
        stats = calculate_theme_regime_stats(theme_name, db_df, regime_summary)

        if stats:
            stats['fiedler'] = row.get('current_fiedler', row.get('Last_Week_Fiedler', 0))
            stats['fiedler_change'] = row.get('fiedler_change', row.get('Change', 0))
            stats['pct_change'] = row.get('pct_change', row.get('Pct_Change', 0))
            stats['n_stocks'] = row.get('n_stocks', row.get('Stocks', 0))
            theme_data.append(stats)

    if not theme_data:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    all_stats = pd.DataFrame(theme_data)

    # BUY NOW: Bull >60% AND Trend >0.1
    buy_now = all_stats[
        (all_stats['avg_bull_pct'] > 60) &
        (all_stats['avg_trend'] > 0.1)
    ].sort_values('avg_bull_pct', ascending=False).copy()

    # WATCHLIST: Bull 40-60% AND Trend >-0.2
    watchlist = all_stats[
        (all_stats['avg_bull_pct'] >= 40) &
        (all_stats['avg_bull_pct'] <= 60) &
        (all_stats['avg_trend'] > -0.2)
    ].sort_values('avg_bull_pct', ascending=False).copy()

    # AVOID: Bear >60% OR Trend <-0.3
    avoid = all_stats[
        (all_stats['avg_bear_pct'] > 60) |
        (all_stats['avg_trend'] < -0.3)
    ].sort_values('avg_bear_pct', ascending=False).copy()

    return buy_now, watchlist, avoid, all_stats


def get_regime_validated_tiers(date_str: str) -> Dict:
    """
    Get regime-validated tier classifications.

    Returns dict with:
    - buy_now: DataFrame of BUY NOW themes
    - watchlist: DataFrame of WATCHLIST themes
    - avoid: DataFrame of AVOID themes
    - all_stats: All theme statistics
    - regime_date: Date of regime data
    - counts: Summary counts
    """
    # Load all data
    regime_summary, regime_date = load_regime_data()
    cohesion_df = load_cohesion_data(date_str)
    db_df = load_db_data()

    if regime_summary is None or cohesion_df.empty:
        return {
            'buy_now': pd.DataFrame(),
            'watchlist': pd.DataFrame(),
            'avoid': pd.DataFrame(),
            'all_stats': pd.DataFrame(),
            'regime_date': None,
            'counts': {'buy_now': 0, 'watchlist': 0, 'avoid': 0, 'total': 0}
        }

    buy_now, watchlist, avoid, all_stats = classify_themes_with_regime(
        cohesion_df, regime_summary, db_df
    )

    return {
        'buy_now': buy_now,
        'watchlist': watchlist,
        'avoid': avoid,
        'all_stats': all_stats,
        'regime_date': regime_date,
        'counts': {
            'buy_now': len(buy_now),
            'watchlist': len(watchlist),
            'avoid': len(avoid),
            'total': len(all_stats)
        }
    }


def format_tier_summary_json(validated_tiers: Dict, date_str: str) -> Dict:
    """
    Format regime-validated tiers as JSON summary compatible with existing reports.

    Maps to old format:
    - tier1 (BUY NOW) = buy_now
    - tier2 (ACCUMULATE/WATCHLIST) = watchlist
    - tier3/tier4 = other categories
    """
    from datetime import datetime

    buy_now = validated_tiers['buy_now']
    watchlist = validated_tiers['watchlist']
    avoid = validated_tiers['avoid']

    return {
        'date': date_str,
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'framework': 'Three-Layer (Cohesion × Regime × Trend)',
        'regime_date': validated_tiers['regime_date'],
        'tier1': {
            'name': 'BUY NOW',
            'criteria': 'Bull >60% AND Trend >0.1',
            'count': len(buy_now),
            'themes': buy_now['theme'].tolist() if not buy_now.empty else []
        },
        'tier2': {
            'name': 'WATCHLIST',
            'criteria': 'Bull 40-60% AND Trend >-0.2',
            'count': len(watchlist),
            'themes': watchlist['theme'].tolist() if not watchlist.empty else []
        },
        'tier3': {
            'name': 'AVOID',
            'criteria': 'Bear >60% OR Trend <-0.3',
            'count': len(avoid),
            'themes': avoid['theme'].tolist()[:10] if not avoid.empty else []  # Top 10 only
        },
        'total_themes': validated_tiers['counts']['total']
    }
