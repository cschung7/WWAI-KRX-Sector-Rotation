#!/usr/bin/env python3
"""
Analyze week-over-week cohesion changes for Naver themes.

Compares Fiedler values between last week (M-F) and the week before.
Ranks themes by increase in cohesion.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import ast
from scipy.linalg import eigh
import warnings
warnings.filterwarnings('ignore')

# Paths - use config module for self-contained project
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import PRICE_DATA_DIR, DB_FILE, DATA_DIR, AUTOGLUON_BASE_DIR

BASE_DIR = AUTOGLUON_BASE_DIR
PRICE_DIR = PRICE_DATA_DIR
OUTPUT_DIR = DATA_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

def load_naver_themes():
    """Load and parse Naver theme database"""
    print("Loading Naver themes from database...")
    df = pd.read_csv(DB_FILE)

    theme_stocks = {}
    stock_themes = {}
    ticker_map = {}

    for _, row in df.iterrows():
        ticker = row['tickers']
        stock_name = row['name']
        themes_str = row['naverTheme']

        ticker_map[ticker] = stock_name

        try:
            themes = ast.literal_eval(themes_str)
            if isinstance(themes, list):
                for theme in themes:
                    if theme not in theme_stocks:
                        theme_stocks[theme] = []
                    theme_stocks[theme].append(stock_name)

                    if stock_name not in stock_themes:
                        stock_themes[stock_name] = []
                    stock_themes[stock_name].append(theme)
        except:
            continue

    print(f"Loaded {len(theme_stocks)} themes")
    print(f"Loaded {len(stock_themes)} stocks with theme assignments")

    return theme_stocks, stock_themes, ticker_map

def load_price_data(stock_names):
    """Load price data for multiple stocks"""
    price_data = {}
    missing = []
    loaded_count = 0

    for stock_name in stock_names:
        file_path = PRICE_DIR / f"{stock_name}.csv"

        if not file_path.exists():
            missing.append(stock_name)
            continue

        try:
            df = pd.read_csv(file_path, index_col=0)
            df.index = pd.to_datetime(df.index)
            df.index.name = 'Date'

            # Column might be 'close' or 'Close'
            close_col = None
            if 'close' in df.columns:
                close_col = 'close'
            elif 'Close' in df.columns:
                close_col = 'Close'

            if close_col is not None:
                df = df.sort_index()
                price_data[stock_name] = df[[close_col]].rename(columns={close_col: 'Close'})
                loaded_count += 1
                if loaded_count % 500 == 0:
                    print(f"  Loaded {loaded_count} files...")
        except Exception as e:
            missing.append(stock_name)
            continue

    print(f"Loaded: {len(price_data)}, Missing: {len(missing)}")
    return price_data

def calculate_fiedler_for_period(price_data, stocks, start_date, end_date):
    """Calculate Fiedler value for a specific time period"""
    # Get price data for the period
    returns_dict = {}

    for stock in stocks:
        if stock not in price_data:
            continue

        stock_data = price_data[stock]
        period_data = stock_data[(stock_data.index >= start_date) & (stock_data.index <= end_date)]

        if len(period_data) < 2:
            continue

        returns = period_data['Close'].pct_change().dropna()
        if len(returns) >= 2:
            returns_dict[stock] = returns

    if len(returns_dict) < 3:
        return None

    # Align returns by date
    returns_df = pd.DataFrame(returns_dict)
    returns_df = returns_df.dropna(axis=1, thresh=len(returns_df)*0.5)

    if len(returns_df.columns) < 3:
        return None

    # Calculate correlation matrix
    corr_matrix = returns_df.corr()

    # Build adjacency matrix (correlation > 0.25)
    threshold = 0.25
    adj_matrix = (corr_matrix.abs() > threshold).astype(float)
    np.fill_diagonal(adj_matrix.values, 0)

    # Calculate degree matrix
    degree = adj_matrix.sum(axis=1)
    if degree.sum() == 0:
        return None

    # Laplacian matrix
    D = np.diag(degree)
    L = D - adj_matrix.values

    # Calculate eigenvalues
    try:
        eigenvalues = eigh(L, eigvals_only=True)
        eigenvalues = np.sort(eigenvalues)

        # Fiedler value is second smallest eigenvalue
        if len(eigenvalues) > 1:
            fiedler = eigenvalues[1]
            return fiedler
    except:
        return None

    return None

def get_week_dates(price_data):
    """Get date ranges for last week and week before"""
    # Get all available dates
    all_dates = set()
    for stock_data in price_data.values():
        all_dates.update(stock_data.index)

    all_dates = sorted(list(all_dates))

    if len(all_dates) < 10:
        return None, None, None, None

    # Get most recent date
    most_recent = all_dates[-1]

    # Find last complete week (last 5 trading days)
    last_week_end = most_recent
    last_week_dates = [d for d in all_dates if d <= last_week_end][-5:]
    last_week_start = last_week_dates[0]

    # Find week before (5 trading days before last week)
    week_before_dates = [d for d in all_dates if d < last_week_start][-5:]
    if len(week_before_dates) < 5:
        return None, None, None, None

    week_before_start = week_before_dates[0]
    week_before_end = week_before_dates[-1]

    return week_before_start, week_before_end, last_week_start, last_week_end

def main():
    """Main analysis"""
    # Load themes
    theme_stocks, stock_themes, ticker_map = load_naver_themes()

    # Get all unique stock names
    all_stocks = set()
    for stocks in theme_stocks.values():
        all_stocks.update(stocks)

    print(f"\nTotal unique stocks: {len(all_stocks)}")
    print(f"Sample stock names: {list(all_stocks)[:10]}")

    # Load price data
    print("\nLoading price data...")
    price_data = load_price_data(all_stocks)

    if len(price_data) == 0:
        print("\nERROR: No price data loaded! Checking first few stocks...")
        for stock in list(all_stocks)[:5]:
            file_path = PRICE_DIR / f"{stock}.csv"
            print(f"  {stock}: exists={file_path.exists()}, path={file_path}")
        return

    # Get week date ranges
    print("\nDetermining week ranges...")
    week_before_start, week_before_end, last_week_start, last_week_end = get_week_dates(price_data)

    if week_before_start is None:
        print("ERROR: Not enough data for week-over-week comparison")
        return

    print(f"\nWeek Before: {week_before_start.date()} to {week_before_end.date()}")
    print(f"Last Week:   {last_week_start.date()} to {last_week_end.date()}")

    # Calculate Fiedler for each theme for both weeks
    results = []

    print("\nAnalyzing themes...")
    for theme_name, stocks in theme_stocks.items():
        if len(stocks) < 3:
            continue

        # Calculate Fiedler for week before
        fiedler_before = calculate_fiedler_for_period(
            price_data, stocks, week_before_start, week_before_end
        )

        # Calculate Fiedler for last week
        fiedler_last = calculate_fiedler_for_period(
            price_data, stocks, last_week_start, last_week_end
        )

        if fiedler_before is not None and fiedler_last is not None:
            change = fiedler_last - fiedler_before
            pct_change = (change / fiedler_before * 100) if fiedler_before > 0 else 0

            results.append({
                'Theme': theme_name,
                'Stocks': len(stocks),
                'Week_Before_Fiedler': fiedler_before,
                'Last_Week_Fiedler': fiedler_last,
                'Change': change,
                'Pct_Change': pct_change
            })

    # Sort by change (descending)
    results.sort(key=lambda x: x['Change'], reverse=True)

    # Create DataFrame
    df = pd.DataFrame(results)

    # Save full results
    output_file = OUTPUT_DIR / f'weekly_cohesion_change_{last_week_end.strftime("%Y%m%d")}.csv'
    df.to_csv(output_file, index=False, encoding='utf-8-sig')

    # Display top gainers
    print("\n" + "="*120)
    print("TOP 30 THEMES WITH INCREASED COHESION (Week-over-Week)")
    print("="*120)
    print(f"Week Before: {week_before_start.date()} to {week_before_end.date()}")
    print(f"Last Week:   {last_week_start.date()} to {last_week_end.date()}")
    print("="*120)

    top_gainers = df.head(30)
    for idx, row in top_gainers.iterrows():
        print(f"\n{idx+1}. {row['Theme']} ({row['Stocks']} stocks)")
        print(f"   Week Before: {row['Week_Before_Fiedler']:.3f}")
        print(f"   Last Week:   {row['Last_Week_Fiedler']:.3f}")
        print(f"   Change:      {row['Change']:+.3f} ({row['Pct_Change']:+.1f}%)")

        if row['Pct_Change'] > 50:
            print(f"   📈 STRONG INCREASE - Cohesion strengthening rapidly")
        elif row['Pct_Change'] > 20:
            print(f"   ✅ MODERATE INCREASE - Theme consolidating")
        elif row['Pct_Change'] > 10:
            print(f"   🟢 SLIGHT INCREASE - Positive trend")

    # Display top decliners
    print("\n" + "="*120)
    print("TOP 20 THEMES WITH DECREASED COHESION (Week-over-Week)")
    print("="*120)

    top_decliners = df.tail(20).iloc[::-1]
    for idx, row in top_decliners.iterrows():
        print(f"\n{row['Theme']} ({row['Stocks']} stocks)")
        print(f"   Week Before: {row['Week_Before_Fiedler']:.3f}")
        print(f"   Last Week:   {row['Last_Week_Fiedler']:.3f}")
        print(f"   Change:      {row['Change']:+.3f} ({row['Pct_Change']:+.1f}%)")

        if row['Pct_Change'] < -30:
            print(f"   ⚠️ SHARP DECLINE - Theme fragmenting")
        elif row['Pct_Change'] < -15:
            print(f"   ❌ MODERATE DECLINE - Losing cohesion")

    # Summary statistics
    print("\n" + "="*120)
    print("SUMMARY STATISTICS")
    print("="*120)
    print(f"Total themes analyzed: {len(df)}")
    print(f"Themes with increased cohesion: {len(df[df['Change'] > 0])} ({len(df[df['Change'] > 0])/len(df)*100:.1f}%)")
    print(f"Themes with decreased cohesion: {len(df[df['Change'] < 0])} ({len(df[df['Change'] < 0])/len(df)*100:.1f}%)")
    print(f"Average change: {df['Change'].mean():.3f} ({df['Pct_Change'].mean():.1f}%)")
    print(f"Median change: {df['Change'].median():.3f} ({df['Pct_Change'].median():.1f}%)")

    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    main()
