#!/usr/bin/env python3
"""
Daily Abnormal Sector Analysis for KRX (Korean Stock Market)

Identifies sectors showing unusual Fiedler eigenvalue patterns compared to weekly baseline.

Author: Claude Code (SuperClaude Framework)
Date: 2025-10-29
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import warnings
warnings.filterwarnings('ignore')

# ================================================================================
# Configuration - use config module for self-contained project
# ================================================================================

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PRICE_DATA_DIR, THEME_TO_TICKERS_FILE, DATA_DIR, REPORTS_DIR

NAVER_THEME_FILE = THEME_TO_TICKERS_FILE

# Use today's date dynamically for daily runs
TODAY = pd.Timestamp.now().normalize()  # Today at midnight
TODAY_STR = TODAY.strftime('%Y%m%d')

# Find most recent weekly baseline file
def find_latest_baseline():
    """Find the most recent weekly_cohesion_change file"""
    baseline_files = sorted(DATA_DIR.glob("weekly_cohesion_change_*.csv"))
    if baseline_files:
        return baseline_files[-1]  # Most recent
    # Fallback to a default if none found
    return DATA_DIR / "weekly_cohesion_change_20251027.csv"

WEEKLY_BASELINE_FILE = find_latest_baseline()
OUTPUT_FILE = DATA_DIR / f"abnormal_sectors_{TODAY_STR}.csv"
REPORT_FILE = REPORTS_DIR / f"ABNORMAL_SECTORS_{TODAY_STR}.md"
LOOKBACK_DAYS = 60  # Rolling window for correlation calculation
CORRELATION_THRESHOLD = 0.25  # Minimum correlation for edge creation
MIN_STOCKS_PER_THEME = 3  # Minimum stocks required for theme analysis

# Abnormality thresholds
LARGE_INCREASE_THRESHOLD = 0.20  # +20% change is unusual strengthening
LARGE_DECREASE_THRESHOLD = -0.20  # -20% change is unusual weakening
DISCONNECTION_THRESHOLD = 0.1  # Fiedler < 0.1 considered disconnected
NEW_CONNECTION_THRESHOLD = 3.0  # Fiedler > 3.0 from previous 0.0 is new connection

# ================================================================================
# Helper Functions
# ================================================================================

def load_stock_price(csv_file):
    """Load Korean stock price from CSV file."""
    try:
        df = pd.read_csv(csv_file)
        if df.columns[0] != 'Unnamed: 0':
            return None

        df = df.rename(columns={'Unnamed: 0': 'Date'})
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.set_index('Date')

        if 'close' not in df.columns:
            return None

        prices = df['close'].dropna()
        return prices if len(prices) > 0 else None
    except Exception as e:
        return None

def calculate_returns(prices, start_date, end_date):
    """Calculate returns for the specified date range."""
    prices = prices[(prices.index >= start_date) & (prices.index <= end_date)]
    if len(prices) < 2:
        return None
    return prices.pct_change().dropna()

def calculate_fiedler_eigenvalue(correlation_matrix, threshold=0.25):
    """
    Calculate Fiedler eigenvalue (second smallest eigenvalue) of graph Laplacian.

    Graph Laplacian: L = D - A
    where D is degree matrix and A is adjacency matrix (thresholded correlations)
    """
    n = len(correlation_matrix)
    if n < 2:
        return 0.0

    # Create adjacency matrix (edges for |correlation| >= threshold)
    adj_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i+1, n):
            if abs(correlation_matrix.iloc[i, j]) >= threshold:
                adj_matrix[i, j] = 1
                adj_matrix[j, i] = 1

    # Check if graph is disconnected
    degrees = adj_matrix.sum(axis=1)
    if np.any(degrees == 0):
        return 0.0  # Disconnected graph

    # Degree matrix
    degree_matrix = np.diag(degrees)

    # Graph Laplacian
    laplacian = degree_matrix - adj_matrix

    # Calculate eigenvalues
    try:
        # Use sparse matrix for efficiency
        laplacian_sparse = csr_matrix(laplacian)
        eigenvalues = eigsh(laplacian_sparse, k=min(n-1, 10), which='SM', return_eigenvectors=False)
        eigenvalues = np.sort(eigenvalues)

        # Fiedler eigenvalue is the second smallest (first is always ~0)
        if len(eigenvalues) >= 2:
            return float(eigenvalues[1])
        else:
            return 0.0
    except:
        return 0.0

def calculate_theme_fiedler(theme_stocks, all_returns, lookback_days):
    """Calculate Fiedler eigenvalue for a theme (sector)."""
    # Filter returns to only include theme stocks
    theme_returns = all_returns[theme_stocks]

    # Calculate correlation matrix
    correlation_matrix = theme_returns.corr()

    # Calculate Fiedler eigenvalue
    fiedler = calculate_fiedler_eigenvalue(correlation_matrix, CORRELATION_THRESHOLD)

    # Count edges (number of significant correlations)
    n = len(correlation_matrix)
    edges = 0
    for i in range(n):
        for j in range(i+1, n):
            if abs(correlation_matrix.iloc[i, j]) >= CORRELATION_THRESHOLD:
                edges += 1

    return fiedler, edges, correlation_matrix.mean().mean()

# ================================================================================
# Main Analysis
# ================================================================================

def main():
    print("="*80)
    print("KRX DAILY ABNORMAL SECTOR ANALYSIS")
    print("="*80)
    print(f"Analysis Date: {TODAY.strftime('%Y-%m-%d')}")
    print(f"Lookback Window: {LOOKBACK_DAYS} days")
    print(f"Correlation Threshold: {CORRELATION_THRESHOLD}")
    print(f"Price Data: {PRICE_DATA_DIR}")
    print("="*80)
    print()

    # Load Naver theme structure
    print("1. Loading Naver theme structure...")
    with open(NAVER_THEME_FILE, 'r', encoding='utf-8') as f:
        naver_themes = json.load(f)
    print(f"   Loaded {len(naver_themes)} themes")
    print()

    # Load weekly baseline
    baseline_date = WEEKLY_BASELINE_FILE.stem.split('_')[-1] if '_' in WEEKLY_BASELINE_FILE.stem else "unknown"
    print(f"2. Loading weekly baseline ({baseline_date})...")
    if not WEEKLY_BASELINE_FILE.exists():
        print(f"   ERROR: Baseline file not found: {WEEKLY_BASELINE_FILE}")
        print(f"   Please run weekly analysis first to generate baseline data.")
        return
    baseline = pd.read_csv(WEEKLY_BASELINE_FILE)
    baseline = baseline.rename(columns={'Theme': 'theme', 'Last_Week_Fiedler': 'baseline_fiedler'})
    baseline_dict = baseline.set_index('theme')['baseline_fiedler'].to_dict()
    print(f"   Loaded baseline for {len(baseline_dict)} themes")
    print()

    # Load price data
    print("3. Loading daily price data...")
    start_date = TODAY - timedelta(days=LOOKBACK_DAYS + 30)  # Extra buffer
    end_date = TODAY

    all_returns = {}
    price_files = list(PRICE_DATA_DIR.glob('*.csv'))

    loaded_stocks = 0
    for csv_file in price_files:
        stock_name = csv_file.stem
        prices = load_stock_price(csv_file)

        if prices is not None:
            returns = calculate_returns(prices, start_date, end_date)
            if returns is not None and len(returns) >= 40:  # Need sufficient data
                all_returns[stock_name] = returns
                loaded_stocks += 1

    print(f"   Loaded {loaded_stocks} stocks with valid data")
    print()

    # Align all returns to common dates
    print("4. Aligning returns to common dates...")
    returns_df = pd.DataFrame(all_returns)
    returns_df = returns_df.dropna(axis=1, how='all')  # Drop columns with all NaN

    # Use last 60 trading days
    if len(returns_df) > LOOKBACK_DAYS:
        returns_df = returns_df.tail(LOOKBACK_DAYS)

    print(f"   Using {len(returns_df)} trading days")
    print(f"   Date range: {returns_df.index.min().strftime('%Y-%m-%d')} to {returns_df.index.max().strftime('%Y-%m-%d')}")
    print()

    # Calculate today's Fiedler values
    print("5. Calculating today's Fiedler values by theme...")
    today_fiedler = []

    for theme_name, stock_list in naver_themes.items():
        # Find stocks that exist in our data
        available_stocks = [s for s in stock_list if s in returns_df.columns]

        if len(available_stocks) < MIN_STOCKS_PER_THEME:
            continue

        # Calculate Fiedler eigenvalue
        fiedler, edges, avg_corr = calculate_theme_fiedler(
            available_stocks, returns_df, LOOKBACK_DAYS
        )

        # Get baseline value
        baseline_fiedler = baseline_dict.get(theme_name, np.nan)

        # Calculate change
        if not np.isnan(baseline_fiedler) and baseline_fiedler != 0:
            pct_change = (fiedler - baseline_fiedler) / baseline_fiedler
        elif not np.isnan(baseline_fiedler) and baseline_fiedler == 0 and fiedler > 0:
            pct_change = np.inf  # New connection
        else:
            pct_change = np.nan

        today_fiedler.append({
            'theme': theme_name,
            'num_stocks': len(available_stocks),
            'num_edges': edges,
            'avg_correlation': avg_corr,
            'fiedler_today': fiedler,
            'fiedler_baseline': baseline_fiedler,
            'fiedler_change': fiedler - baseline_fiedler if not np.isnan(baseline_fiedler) else np.nan,
            'pct_change': pct_change
        })

    today_df = pd.DataFrame(today_fiedler)
    print(f"   Calculated Fiedler for {len(today_df)} themes")
    print()

    # Identify abnormal sectors
    print("6. Identifying abnormal sectors...")
    abnormal_sectors = []

    for idx, row in today_df.iterrows():
        theme = row['theme']
        today_val = row['fiedler_today']
        baseline_val = row['fiedler_baseline']
        pct_change = row['pct_change']

        abnormality_type = []

        # Check for large increase
        if not np.isnan(pct_change) and pct_change >= LARGE_INCREASE_THRESHOLD:
            abnormality_type.append('LARGE_INCREASE')

        # Check for large decrease
        if not np.isnan(pct_change) and pct_change <= LARGE_DECREASE_THRESHOLD:
            abnormality_type.append('LARGE_DECREASE')

        # Check for disconnection (was connected, now disconnected)
        if not np.isnan(baseline_val) and baseline_val >= 1.0 and today_val < DISCONNECTION_THRESHOLD:
            abnormality_type.append('DISCONNECTION')

        # Check for new connection (was disconnected, now connected)
        if not np.isnan(baseline_val) and baseline_val < DISCONNECTION_THRESHOLD and today_val >= NEW_CONNECTION_THRESHOLD:
            abnormality_type.append('NEW_CONNECTION')

        if len(abnormality_type) > 0:
            abnormal_sectors.append({
                'theme': theme,
                'abnormality': ', '.join(abnormality_type),
                'fiedler_today': today_val,
                'fiedler_baseline': baseline_val,
                'fiedler_change': row['fiedler_change'],
                'pct_change': pct_change * 100 if not np.isinf(pct_change) else np.nan,
                'num_stocks': row['num_stocks'],
                'stock_list': ', '.join(naver_themes[theme][:10])  # First 10 stocks
            })

    abnormal_df = pd.DataFrame(abnormal_sectors)
    print(f"   Found {len(abnormal_df)} abnormal sectors")
    print()

    # Save results
    print("7. Saving results...")
    abnormal_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"   CSV saved: {OUTPUT_FILE}")

    # Generate markdown report
    generate_report(abnormal_df, today_df)
    print(f"   Report saved: {REPORT_FILE}")
    print()

    # Print summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total themes analyzed: {len(today_df)}")
    print(f"Abnormal sectors found: {len(abnormal_df)}")
    print()

    if len(abnormal_df) > 0:
        print("Abnormality Breakdown:")
        for abnormality_type in ['LARGE_INCREASE', 'LARGE_DECREASE', 'DISCONNECTION', 'NEW_CONNECTION']:
            count = abnormal_df['abnormality'].str.contains(abnormality_type).sum()
            print(f"  {abnormality_type}: {count}")
        print()

        print("Top 5 Abnormal Sectors:")
        top5 = abnormal_df.nlargest(5, 'fiedler_change')[['theme', 'fiedler_change', 'pct_change', 'abnormality']]
        for idx, row in top5.iterrows():
            print(f"  {row['theme']}: {row['fiedler_change']:.2f} ({row['pct_change']:.1f}%) - {row['abnormality']}")

    print("="*80)

def generate_report(abnormal_df, all_themes_df):
    """Generate markdown report of abnormal sectors."""
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# KRX Abnormal Sector Analysis\n\n")
        baseline_date = WEEKLY_BASELINE_FILE.stem.split('_')[-1] if '_' in WEEKLY_BASELINE_FILE.stem else "unknown"
        f.write(f"**Analysis Date**: {TODAY.strftime('%Y-%m-%d')}\n")
        f.write(f"**Baseline Date**: {baseline_date} (Weekly Fiedler)\n")
        f.write(f"**Total Themes Analyzed**: {len(all_themes_df)}\n")
        f.write(f"**Abnormal Sectors Found**: {len(abnormal_df)}\n\n")

        f.write("---\n\n")

        if len(abnormal_df) == 0:
            f.write("## No Abnormal Sectors Detected\n\n")
            f.write("All sectors are within normal ranges (±20% change) compared to weekly baseline.\n\n")
            return

        # Categorize abnormal sectors
        large_increase = abnormal_df[abnormal_df['abnormality'].str.contains('LARGE_INCREASE')]
        large_decrease = abnormal_df[abnormal_df['abnormality'].str.contains('LARGE_DECREASE')]
        disconnections = abnormal_df[abnormal_df['abnormality'].str.contains('DISCONNECTION')]
        new_connections = abnormal_df[abnormal_df['abnormality'].str.contains('NEW_CONNECTION')]

        # 1. Large Increases (Unusual Strengthening)
        if len(large_increase) > 0:
            f.write("## 🔥 Unusual Sector Strengthening (>+20% Fiedler Increase)\n\n")
            f.write("Sectors showing unusually strong cohesion increases - potential momentum plays.\n\n")

            large_increase = large_increase.sort_values('pct_change', ascending=False)

            f.write("| Theme | Fiedler Today | Baseline | Change | % Change | Stocks |\n")
            f.write("|-------|---------------|----------|---------|----------|--------|\n")

            for idx, row in large_increase.head(20).iterrows():
                f.write(f"| {row['theme']} | {row['fiedler_today']:.2f} | {row['fiedler_baseline']:.2f} | "
                       f"{row['fiedler_change']:+.2f} | {row['pct_change']:+.1f}% | {row['num_stocks']} |\n")

            f.write("\n")
            f.write("**Investment Implication**: These sectors are showing rapid cohesion increases. "
                   "Consider buying sector ETFs or top stocks within these themes as momentum may continue.\n\n")
            f.write("---\n\n")

        # 2. Large Decreases (Unusual Weakening)
        if len(large_decrease) > 0:
            f.write("## ❄️ Unusual Sector Weakening (<-20% Fiedler Decrease)\n\n")
            f.write("Sectors showing unusually weak cohesion - potential rotation out or risk.\n\n")

            large_decrease = large_decrease.sort_values('pct_change', ascending=True)

            f.write("| Theme | Fiedler Today | Baseline | Change | % Change | Stocks |\n")
            f.write("|-------|---------------|----------|---------|----------|--------|\n")

            for idx, row in large_decrease.head(20).iterrows():
                f.write(f"| {row['theme']} | {row['fiedler_today']:.2f} | {row['fiedler_baseline']:.2f} | "
                       f"{row['fiedler_change']:+.2f} | {row['pct_change']:+.1f}% | {row['num_stocks']} |\n")

            f.write("\n")
            f.write("**Investment Implication**: These sectors are losing cohesion rapidly. "
                   "Consider profit-taking or avoiding new positions. May indicate sector rotation or negative news.\n\n")
            f.write("---\n\n")

        # 3. Disconnections (Formerly Connected, Now Fragmented)
        if len(disconnections) > 0:
            f.write("## ⚠️ Sector Disconnections (Fiedler Dropped to <0.1)\n\n")
            f.write("Sectors that lost all cohesion - high risk, avoid sector plays.\n\n")

            disconnections = disconnections.sort_values('fiedler_baseline', ascending=False)

            f.write("| Theme | Previous Fiedler | Today | Change | Stocks |\n")
            f.write("|-------|------------------|-------|--------|--------|\n")

            for idx, row in disconnections.iterrows():
                f.write(f"| {row['theme']} | {row['fiedler_baseline']:.2f} | {row['fiedler_today']:.2f} | "
                       f"{row['fiedler_change']:+.2f} | {row['num_stocks']} |\n")

            f.write("\n")
            f.write("**Investment Implication**: Complete loss of sector cohesion. "
                   "Individual stock selection required - sector ETFs will not work.\n\n")
            f.write("---\n\n")

        # 4. New Connections (Formerly Fragmented, Now Cohesive)
        if len(new_connections) > 0:
            f.write("## ✨ New Sector Formations (Fiedler Jumped from ~0 to >3.0)\n\n")
            f.write("Sectors that newly formed cohesion - potential new trends.\n\n")

            new_connections = new_connections.sort_values('fiedler_today', ascending=False)

            f.write("| Theme | Previous Fiedler | Today | Change | Stocks |\n")
            f.write("|-------|------------------|-------|--------|--------|\n")

            for idx, row in new_connections.iterrows():
                f.write(f"| {row['theme']} | {row['fiedler_baseline']:.2f} | {row['fiedler_today']:.2f} | "
                       f"{row['fiedler_change']:+.2f} | {row['num_stocks']} |\n")

            f.write("\n")
            f.write("**Investment Implication**: New sector themes emerging. "
                   "Early entry opportunity - monitor if cohesion strengthens further.\n\n")
            f.write("---\n\n")

        # Summary statistics
        f.write("## Statistics\n\n")
        f.write(f"- **Mean Fiedler Change**: {abnormal_df['fiedler_change'].mean():.2f}\n")
        f.write(f"- **Median Fiedler Change**: {abnormal_df['fiedler_change'].median():.2f}\n")
        f.write(f"- **Largest Increase**: {abnormal_df['fiedler_change'].max():.2f} "
               f"({abnormal_df.loc[abnormal_df['fiedler_change'].idxmax(), 'theme']})\n")
        f.write(f"- **Largest Decrease**: {abnormal_df['fiedler_change'].min():.2f} "
               f"({abnormal_df.loc[abnormal_df['fiedler_change'].idxmin(), 'theme']})\n")
        f.write("\n")

        f.write("---\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} KST\n")
        f.write("**Framework**: Fiedler Eigenvalue Sector Cohesion Analysis\n")
        f.write("**Methodology**: Graph Laplacian eigenvalue analysis on 60-day rolling correlations\n")

if __name__ == "__main__":
    main()
