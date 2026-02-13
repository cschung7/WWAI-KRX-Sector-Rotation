#!/usr/bin/env python3
"""
Build comprehensive Fiedler value database for all Naver themes.

Weekly: Monday-Friday windows
Monthly: Day 1-30 windows
Period: 2025-01-01 onwards
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import json
import warnings
from matplotlib import font_manager, rc

warnings.filterwarnings('ignore')

# Configure Korean font for matplotlib
try:
    font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
    font_name = font_manager.FontProperties(fname=font_path).get_name()
    rc('font', family=font_name)
except:
    pass  # Font configuration optional for CSV generation

# Configuration - use config module for self-contained project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PRICE_DATA_DIR, THEME_TO_TICKERS_FILE, DATA_DIR

THEME_FILE = THEME_TO_TICKERS_FILE
OUTPUT_DIR = DATA_DIR

START_DATE = pd.Timestamp('2025-01-01')
LOOKBACK_DAYS = 60
CORRELATION_THRESHOLD = 0.25
MIN_STOCKS = 3

print("="*80)
print("NAVER THEME FIEDLER DATABASE BUILDER")
print("="*80)
print(f"Start date: {START_DATE.strftime('%Y-%m-%d')}")
print(f"Lookback window: {LOOKBACK_DAYS} days")
print(f"Correlation threshold: {CORRELATION_THRESHOLD}")
print(f"Minimum stocks per theme: {MIN_STOCKS}")
print("="*80)

# Load Naver themes
print("\n1. Loading Naver theme mappings...")
with open(THEME_FILE, 'r', encoding='utf-8') as f:
    theme_to_tickers = json.load(f)

print(f"   Loaded {len(theme_to_tickers)} themes")

# Load all price data
print("\n2. Loading price data for all stocks...")
all_tickers = set()
for tickers in theme_to_tickers.values():
    all_tickers.update(tickers)

print(f"   Total unique tickers: {len(all_tickers)}")

price_data = {}
loaded = 0
for ticker in all_tickers:
    file_path = PRICE_DATA_DIR / f"{ticker}.csv"
    if not file_path.exists():
        continue

    try:
        df = pd.read_csv(file_path)

        # Handle date column (case-insensitive)
        date_col = next((c for c in df.columns if c.lower() == 'date'), None)
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            df = df.set_index(date_col)
            df.index.name = 'Date'
        elif 'Unnamed: 0' in df.columns:
            df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'])
            df = df.set_index('Unnamed: 0')
            df.index.name = 'Date'
        else:
            continue  # Skip files without a recognizable date column

        # Handle close column (case-insensitive)
        close_col = next((c for c in df.columns if c.lower() == 'close'), None)
        if close_col:
            df = df[[close_col]].rename(columns={close_col: 'Close'})
            df = df[df.index >= START_DATE - pd.Timedelta(days=LOOKBACK_DAYS*2)]
            price_data[ticker] = df.sort_index()
            loaded += 1

            if loaded % 500 == 0:
                print(f"   Loaded {loaded} stocks...")
    except Exception as e:
        continue

print(f"   Successfully loaded {loaded} stocks")

def calculate_fiedler_eigenvalue(returns_df):
    """Calculate Fiedler eigenvalue from returns dataframe."""
    if len(returns_df) < 2 or len(returns_df.columns) < MIN_STOCKS:
        return None, 0, 0

    # Calculate correlation matrix
    corr_matrix = returns_df.corr()

    # Build adjacency matrix
    n = len(corr_matrix)
    adj_matrix = np.zeros((n, n))
    edge_count = 0

    for i in range(n):
        for j in range(i+1, n):
            if abs(corr_matrix.iloc[i, j]) >= CORRELATION_THRESHOLD:
                adj_matrix[i, j] = 1
                adj_matrix[j, i] = 1
                edge_count += 1

    # Check if connected
    degrees = adj_matrix.sum(axis=1)
    if np.any(degrees == 0):
        return 0.0, edge_count, False

    # Graph Laplacian
    degree_matrix = np.diag(degrees)
    laplacian = degree_matrix - adj_matrix

    # Calculate eigenvalues
    try:
        laplacian_sparse = csr_matrix(laplacian)
        eigenvalues = eigsh(laplacian_sparse, k=min(n-1, 10), which='SM', return_eigenvectors=False)
        eigenvalues = np.sort(eigenvalues)

        fiedler = float(eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0
        return fiedler, edge_count, True
    except:
        return 0.0, edge_count, False

def calculate_theme_fiedler(theme_tickers, start_date, end_date):
    """Calculate Fiedler value for a theme over date range."""
    # Filter tickers with data
    valid_tickers = [t for t in theme_tickers if t in price_data]

    if len(valid_tickers) < MIN_STOCKS:
        return None

    # Calculate returns for lookback period
    lookback_start = start_date - pd.Timedelta(days=LOOKBACK_DAYS)

    returns_dict = {}
    for ticker in valid_tickers:
        df = price_data[ticker]
        period_data = df[(df.index >= lookback_start) & (df.index <= end_date)]

        if len(period_data) < 2:
            continue

        returns = period_data['Close'].pct_change().dropna()
        if len(returns) >= 2:
            returns_dict[ticker] = returns

    if len(returns_dict) < MIN_STOCKS:
        return None

    # Align returns
    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.dropna()

    if len(returns_df) < 2 or len(returns_df.columns) < MIN_STOCKS:
        return None

    # Calculate Fiedler
    fiedler, n_edges, is_connected = calculate_fiedler_eigenvalue(returns_df)

    mean_corr = returns_df.corr().values[np.triu_indices_from(returns_df.corr().values, k=1)].mean()

    return {
        'fiedler': fiedler,
        'n_stocks': len(returns_df.columns),
        'n_edges': n_edges,
        'mean_correlation': mean_corr,
        'is_connected': is_connected
    }

# Get all trading dates from 2025-01-01
print("\n3. Identifying trading dates...")
all_dates = set()
for df in price_data.values():
    all_dates.update(df.index)

all_dates = sorted([d for d in all_dates if d >= START_DATE])

if len(all_dates) == 0:
    print(f"   ERROR: No trading dates found >= {START_DATE.strftime('%Y-%m-%d')}")
    print("   Exiting...")
    exit(1)

print(f"   Found {len(all_dates)} trading days from {all_dates[0].strftime('%Y-%m-%d')} to {all_dates[-1].strftime('%Y-%m-%d')}")

# Generate weekly periods (Monday-Friday)
print("\n4. Generating weekly periods (M-F)...")
weekly_periods = []
current_date = all_dates[0]

while current_date <= all_dates[-1]:
    # Find week end (next Friday or last available day)
    week_dates = [d for d in all_dates if d >= current_date and d < current_date + pd.Timedelta(days=7)]

    if len(week_dates) >= 3:  # At least 3 trading days
        weekly_periods.append({
            'start': week_dates[0],
            'end': week_dates[-1],
            'label': f"{week_dates[-1].strftime('%Y-%m-%d')}"
        })

    current_date = current_date + pd.Timedelta(days=7)

print(f"   Generated {len(weekly_periods)} weekly periods")

# Generate monthly periods (Day 1-30)
print("\n5. Generating monthly periods (1-30)...")
monthly_periods = []

for year in range(2025, 2027):
    for month in range(1, 13):
        month_start = pd.Timestamp(f'{year}-{month:02d}-01')
        if month == 12:
            month_end = pd.Timestamp(f'{year+1}-01-01') - pd.Timedelta(days=1)
        else:
            month_end = pd.Timestamp(f'{year}-{month+1:02d}-01') - pd.Timedelta(days=1)

        if month_start > all_dates[-1]:
            break

        month_dates = [d for d in all_dates if d >= month_start and d <= month_end]

        if len(month_dates) >= 5:  # At least 5 trading days
            monthly_periods.append({
                'start': month_dates[0],
                'end': month_dates[-1],
                'label': f"{year}-{month:02d}"
            })

print(f"   Generated {len(monthly_periods)} monthly periods")

# Calculate weekly Fiedler values
print("\n6. Calculating weekly Fiedler values for all themes...")
weekly_results = []

for i, period in enumerate(weekly_periods):
    if (i+1) % 5 == 0:
        print(f"   Processing week {i+1}/{len(weekly_periods)}...")

    for theme, tickers in theme_to_tickers.items():
        result = calculate_theme_fiedler(tickers, period['start'], period['end'])

        if result is not None:
            weekly_results.append({
                'date': period['end'],
                'week_label': period['label'],
                'theme': theme,
                'fiedler': result['fiedler'],
                'n_stocks': result['n_stocks'],
                'n_edges': result['n_edges'],
                'mean_correlation': result['mean_correlation'],
                'is_connected': result['is_connected']
            })

print(f"   Calculated {len(weekly_results)} weekly data points")

# Calculate monthly Fiedler values
print("\n7. Calculating monthly Fiedler values for all themes...")
monthly_results = []

for i, period in enumerate(monthly_periods):
    print(f"   Processing month {i+1}/{len(monthly_periods)}: {period['label']}...")

    for theme, tickers in theme_to_tickers.items():
        result = calculate_theme_fiedler(tickers, period['start'], period['end'])

        if result is not None:
            monthly_results.append({
                'date': period['end'],
                'month_label': period['label'],
                'theme': theme,
                'fiedler': result['fiedler'],
                'n_stocks': result['n_stocks'],
                'n_edges': result['n_edges'],
                'mean_correlation': result['mean_correlation'],
                'is_connected': result['is_connected']
            })

print(f"   Calculated {len(monthly_results)} monthly data points")

# Save to CSV
print("\n8. Saving results...")

weekly_df = pd.DataFrame(weekly_results)
monthly_df = pd.DataFrame(monthly_results)

weekly_file = OUTPUT_DIR / "naver_themes_weekly_fiedler_2025.csv"
monthly_file = OUTPUT_DIR / "naver_themes_monthly_fiedler_2025.csv"

weekly_df.to_csv(weekly_file, index=False)
monthly_df.to_csv(monthly_file, index=False)

print(f"   Weekly data: {weekly_file}")
print(f"   Monthly data: {monthly_file}")

# Print summary statistics
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

print(f"\nWeekly Database:")
print(f"  Total records: {len(weekly_df)}")
print(f"  Themes covered: {weekly_df['theme'].nunique()}")
print(f"  Date range: {weekly_df['date'].min().strftime('%Y-%m-%d')} to {weekly_df['date'].max().strftime('%Y-%m-%d')}")
print(f"  Mean Fiedler: {weekly_df['fiedler'].mean():.3f}")
print(f"  Median Fiedler: {weekly_df['fiedler'].median():.3f}")

print(f"\nMonthly Database:")
print(f"  Total records: {len(monthly_df)}")
print(f"  Themes covered: {monthly_df['theme'].nunique()}")
print(f"  Date range: {monthly_df['date'].min().strftime('%Y-%m-%d')} to {monthly_df['date'].max().strftime('%Y-%m-%d')}")
print(f"  Mean Fiedler: {monthly_df['fiedler'].mean():.3f}")
print(f"  Median Fiedler: {monthly_df['fiedler'].median():.3f}")

# Sample data for 5G theme
print("\n" + "="*80)
print("SAMPLE: 5G (5세대 이동통신) Theme")
print("="*80)

theme_name = "5G(5세대 이동통신)"
weekly_5g = weekly_df[weekly_df['theme'] == theme_name]
monthly_5g = monthly_df[monthly_df['theme'] == theme_name]

print(f"\nWeekly data points: {len(weekly_5g)}")
if len(weekly_5g) > 0:
    print(weekly_5g[['date', 'fiedler', 'n_stocks', 'is_connected']].tail(10).to_string(index=False))

print(f"\nMonthly data points: {len(monthly_5g)}")
if len(monthly_5g) > 0:
    print(monthly_5g[['date', 'fiedler', 'n_stocks', 'is_connected']].to_string(index=False))

print("\n" + "="*80)
print("DATABASE BUILD COMPLETE")
print("="*80)
