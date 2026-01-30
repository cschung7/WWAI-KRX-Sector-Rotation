#!/usr/bin/env python3
"""
Test Fiedler database builder with 3 themes and plot results.
Includes Korean font support for matplotlib.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
import json
import warnings
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager, rc

warnings.filterwarnings('ignore')

# Configure Korean font for matplotlib
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font_name)
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display

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

# Test with 3 themes
TEST_THEMES = ["5G(5세대 이동통신)", "통신", "반도체"]

print("="*80)
print("FIEDLER DATABASE TEST (3 THEMES)")
print("="*80)
print(f"Test themes: {TEST_THEMES}")
print(f"Start date: {START_DATE.strftime('%Y-%m-%d')}")
print(f"Lookback window: {LOOKBACK_DAYS} days")
print("="*80)

# Load Naver themes
print("\n1. Loading Naver theme mappings...")
with open(THEME_FILE, 'r', encoding='utf-8') as f:
    all_themes = json.load(f)

# Filter to test themes
theme_to_tickers = {k: v for k, v in all_themes.items() if k in TEST_THEMES}
print(f"   Selected {len(theme_to_tickers)} themes for testing")

# Load price data
print("\n2. Loading price data...")
all_tickers = set()
for tickers in theme_to_tickers.values():
    all_tickers.update(tickers)

print(f"   Total tickers needed: {len(all_tickers)}")

price_data = {}
for ticker in all_tickers:
    file_path = PRICE_DATA_DIR / f"{ticker}.csv"
    if not file_path.exists():
        continue

    try:
        df = pd.read_csv(file_path)

        if 'Unnamed: 0' in df.columns:
            df['Unnamed: 0'] = pd.to_datetime(df['Unnamed: 0'])
            df = df.set_index('Unnamed: 0')
            df.index.name = 'Date'

        if 'close' in df.columns:
            df = df[['close']].rename(columns={'close': 'Close'})
            df = df[df.index >= START_DATE - pd.Timedelta(days=LOOKBACK_DAYS*2)]
            price_data[ticker] = df.sort_index()
    except:
        continue

print(f"   Loaded {len(price_data)} stocks")

def calculate_fiedler_eigenvalue(returns_df):
    """Calculate Fiedler eigenvalue."""
    if len(returns_df) < 2 or len(returns_df.columns) < MIN_STOCKS:
        return None, 0, 0, 0.0

    corr_matrix = returns_df.corr()
    n = len(corr_matrix)
    adj_matrix = np.zeros((n, n))
    edge_count = 0

    for i in range(n):
        for j in range(i+1, n):
            if abs(corr_matrix.iloc[i, j]) >= CORRELATION_THRESHOLD:
                adj_matrix[i, j] = 1
                adj_matrix[j, i] = 1
                edge_count += 1

    degrees = adj_matrix.sum(axis=1)
    if np.any(degrees == 0):
        return 0.0, edge_count, False, corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()

    degree_matrix = np.diag(degrees)
    laplacian = degree_matrix - adj_matrix

    try:
        laplacian_sparse = csr_matrix(laplacian)
        eigenvalues = eigsh(laplacian_sparse, k=min(n-1, 10), which='SM', return_eigenvectors=False)
        eigenvalues = np.sort(eigenvalues)
        fiedler = float(eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0
        mean_corr = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()
        return fiedler, edge_count, True, mean_corr
    except:
        return 0.0, edge_count, False, corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)].mean()

def calculate_theme_fiedler(theme_tickers, start_date, end_date):
    """Calculate Fiedler for a theme over date range."""
    valid_tickers = [t for t in theme_tickers if t in price_data]

    if len(valid_tickers) < MIN_STOCKS:
        return None

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

    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.dropna()

    if len(returns_df) < 2 or len(returns_df.columns) < MIN_STOCKS:
        return None

    fiedler, n_edges, is_connected, mean_corr = calculate_fiedler_eigenvalue(returns_df)

    return {
        'fiedler': fiedler,
        'n_stocks': len(returns_df.columns),
        'n_edges': n_edges,
        'mean_correlation': mean_corr,
        'is_connected': is_connected
    }

# Get trading dates
print("\n3. Identifying trading dates...")
all_dates = set()
for df in price_data.values():
    all_dates.update(df.index)

all_dates = sorted([d for d in all_dates if d >= START_DATE])
print(f"   Found {len(all_dates)} trading days from {all_dates[0].strftime('%Y-%m-%d')} to {all_dates[-1].strftime('%Y-%m-%d')}")

# Generate weekly periods
print("\n4. Generating weekly periods...")
weekly_periods = []
current_date = all_dates[0]

while current_date <= all_dates[-1]:
    week_dates = [d for d in all_dates if d >= current_date and d < current_date + pd.Timedelta(days=7)]

    if len(week_dates) >= 3:
        weekly_periods.append({
            'start': week_dates[0],
            'end': week_dates[-1],
            'label': f"{week_dates[-1].strftime('%Y-%m-%d')}"
        })

    current_date = current_date + pd.Timedelta(days=7)

print(f"   Generated {len(weekly_periods)} weekly periods")

# Calculate weekly Fiedler
print("\n5. Calculating weekly Fiedler values...")
weekly_results = []

for i, period in enumerate(weekly_periods):
    print(f"   Week {i+1}/{len(weekly_periods)}: {period['label']}")

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

# Save results
weekly_df = pd.DataFrame(weekly_results)
output_file = OUTPUT_DIR / "test_weekly_fiedler_3themes.csv"
weekly_df.to_csv(output_file, index=False)
print(f"\n6. Saved results: {output_file}")

# Print summary
print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80)

for theme in TEST_THEMES:
    theme_data = weekly_df[weekly_df['theme'] == theme]
    if len(theme_data) > 0:
        print(f"\n{theme}:")
        print(f"  Data points: {len(theme_data)}")
        print(f"  Fiedler range: {theme_data['fiedler'].min():.2f} - {theme_data['fiedler'].max():.2f}")
        print(f"  Mean: {theme_data['fiedler'].mean():.2f}")
        print(f"  Last value: {theme_data['fiedler'].iloc[-1]:.2f} ({theme_data['date'].iloc[-1].strftime('%Y-%m-%d')})")

# Create plot
print("\n7. Creating visualization...")
fig, axes = plt.subplots(len(TEST_THEMES), 1, figsize=(14, 4*len(TEST_THEMES)))

if len(TEST_THEMES) == 1:
    axes = [axes]

for idx, theme in enumerate(TEST_THEMES):
    ax = axes[idx]
    theme_data = weekly_df[weekly_df['theme'] == theme].sort_values('date')

    if len(theme_data) > 0:
        ax.plot(theme_data['date'], theme_data['fiedler'],
               linewidth=2, marker='o', markersize=5, label='Weekly Fiedler')

        # Add threshold lines
        ax.axhline(y=7.5, color='green', linestyle='--', alpha=0.5, label='TIER 1 (7.5+)')
        ax.axhline(y=3.0, color='orange', linestyle='--', alpha=0.5, label='TIER 2 (3.0+)')
        ax.axhline(y=0.1, color='red', linestyle='--', alpha=0.5, label='Disconnection (<0.1)')

        ax.set_title(f'{theme} - Weekly Fiedler Values (2025)',
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Fiedler Eigenvalue', fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)

        # Format x-axis
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()

plot_file = OUTPUT_DIR / "../reports/test_3themes_weekly_fiedler.png"
plot_file.parent.mkdir(exist_ok=True)
plt.savefig(plot_file, dpi=300, bbox_inches='tight')
print(f"   Plot saved: {plot_file}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
