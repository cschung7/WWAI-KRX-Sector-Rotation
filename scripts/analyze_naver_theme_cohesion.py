#!/usr/bin/env python3
"""
Naver Theme Cohesion Analysis - Enhanced Fiedler Value Detection
Analyzes which Naver themes show enhanced cohesion as of 2025-10-27

Data Sources (configured via config.py):
- Price data: External (configurable via KRX_PRICE_DATA_DIR env var)
- Theme database: External (configurable via AUTOGLUON_BASE_DIR env var)
- Local data: data/theme_to_tickers.json

Output:
- Rolling Fiedler values for each theme
- Themes with enhanced cohesion (increasing Fiedler)
- Current cohesion ranking as of 2025-10-27
"""

import pandas as pd
import numpy as np
import networkx as nx
from pathlib import Path
from datetime import datetime, timedelta
import ast
import warnings
from scipy.sparse.linalg import eigsh
from scipy.sparse import csr_matrix
warnings.filterwarnings('ignore')

# Configuration - use config module for self-contained project
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import PRICE_DATA_DIR, DB_FILE, DATA_DIR, AUTOGLUON_BASE_DIR, REPORTS_DIR
import argparse

PRICE_DIR = PRICE_DATA_DIR
OUTPUT_DIR = DATA_DIR
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Analysis parameters
THRESHOLD = 0.25  # Correlation threshold for network edges
WINDOW = 20       # Rolling window in days
MIN_OVERLAP = 15  # Minimum overlapping data points
STEP = 5          # Step size for rolling window
MIN_STOCKS = 3    # Minimum stocks required per theme
LOOKBACK_DAYS = 30  # Days to look back for cohesion change


def load_naver_themes():
    """Load and parse Naver theme database with ticker->name mapping"""
    print("Loading Naver theme database...")

    df = pd.read_csv(DB_FILE)

    # Parse naverTheme column - use Korean name for CSV file matching
    theme_stocks = {}
    stock_themes = {}
    ticker_map = {}

    for _, row in df.iterrows():
        ticker = row['tickers']
        stock_name = row['name']  # Korean name to match CSV files
        themes_str = row['naverTheme']

        if pd.isna(themes_str) or pd.isna(stock_name):
            continue

        # Store ticker->name mapping
        ticker_map[ticker] = stock_name

        try:
            themes = ast.literal_eval(themes_str)
            if isinstance(themes, list):
                for theme in themes:
                    if theme not in theme_stocks:
                        theme_stocks[theme] = []
                    theme_stocks[theme].append(stock_name)  # Store name not ticker

                    if stock_name not in stock_themes:
                        stock_themes[stock_name] = []
                    stock_themes[stock_name].append(theme)
        except:
            continue

    # Filter themes with minimum stocks
    theme_stocks = {k: v for k, v in theme_stocks.items() if len(v) >= MIN_STOCKS}

    print(f"Found {len(theme_stocks)} themes with >={MIN_STOCKS} stocks")
    print(f"Total stocks: {len(stock_themes)}")

    return theme_stocks, stock_themes, ticker_map


def load_price_data(stock_names):
    """Load price data for given stock names (Korean names)"""
    print(f"\nLoading price data for {len(stock_names)} stocks...")

    data_dict = {}
    missing = []

    for stock_name in stock_names:
        csv_file = PRICE_DIR / f"{stock_name}.csv"
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                close_col = 'Close' if 'Close' in df.columns else 'close'

                if close_col in df.columns:
                    df = df[df.index >= '2024-01-01']
                    if len(df) >= 50:
                        data_dict[stock_name] = df[close_col]
            except:
                missing.append(stock_name)
        else:
            missing.append(stock_name)

    print(f"Loaded: {len(data_dict)}, Missing: {len(missing)}")
    return data_dict


def calculate_fiedler_value(returns_df, threshold=0.25):
    """Calculate Fiedler value for correlation network (optimized with sparse solver)"""

    if len(returns_df.columns) < 2:
        return 0.0, 0, 0.0, 0.0, False

    # Calculate correlation
    corr_matrix = returns_df.corr()

    # Build network
    G = nx.Graph()
    G.add_nodes_from(corr_matrix.index)

    n_edges = 0
    for i in range(len(corr_matrix)):
        for j in range(i+1, len(corr_matrix)):
            if abs(corr_matrix.iloc[i, j]) >= threshold:
                G.add_edge(corr_matrix.index[i], corr_matrix.index[j],
                          weight=abs(corr_matrix.iloc[i, j]))
                n_edges += 1

    # Calculate Fiedler
    if n_edges == 0:
        return 0.0, len(corr_matrix), 0, 0.0, False

    try:
        # Use sparse Laplacian and sparse eigenvalue solver (5-10x faster)
        L_sparse = nx.laplacian_matrix(G, weight='weight')
        n = L_sparse.shape[0]
        
        # Only calculate 2 smallest eigenvalues (we only need the 2nd one)
        if n > 1:
            eigenvalues = eigsh(L_sparse, k=min(2, n-1), which='SM', return_eigenvectors=False)
            eigenvalues = np.sort(eigenvalues)
            fiedler = float(eigenvalues[1]) if len(eigenvalues) >= 2 else 0.0
        else:
            fiedler = 0.0
        
        is_connected = nx.is_connected(G)
        density = nx.density(G)

        # Calculate mean correlation
        corr_values = corr_matrix.values[np.triu_indices_from(corr_matrix.values, k=1)]
        mean_corr = np.mean(corr_values)

        return fiedler, len(corr_matrix), n_edges, mean_corr, is_connected
    except:
        return 0.0, len(corr_matrix), n_edges, 0.0, False


def calculate_rolling_theme_fiedler(theme_name, stock_names, data_dict, target_date=None, incremental=True):
    """Calculate rolling Fiedler values for a theme (with incremental update support)"""

    # Filter to stocks in this theme that have data
    available_stocks = [s for s in stock_names if s in data_dict]

    if len(available_stocks) < MIN_STOCKS:
        return pd.DataFrame()

    # Create returns dataframe
    returns_dict = {}
    for stock_name in available_stocks:
        returns = data_dict[stock_name].pct_change().dropna()
        if len(returns) >= 30:
            returns_dict[stock_name] = returns

    if len(returns_dict) < MIN_STOCKS:
        return pd.DataFrame()

    returns_df = pd.DataFrame(returns_dict).dropna()

    # Filter to 2025
    returns_df = returns_df[returns_df.index >= '2025-01-01']

    if len(returns_df) < WINDOW:
        return pd.DataFrame()

    # Try to load previous results for incremental update
    prev_results = pd.DataFrame()
    if incremental and target_date:
        safe_name = theme_name.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')[:50]
        prev_file = OUTPUT_DIR / f'theme_{safe_name}_timeseries.csv'
        if prev_file.exists():
            try:
                prev_results = pd.read_csv(prev_file, parse_dates=['date'])
                prev_results['date'] = pd.to_datetime(prev_results['date'])
                last_date = prev_results['date'].max()
                target_dt = pd.to_datetime(target_date)
                
                # If we have recent data, only calculate new windows
                if last_date >= target_dt - timedelta(days=10):
                    # Only calculate windows after last_date
                    returns_df = returns_df[returns_df.index > last_date]
                    if len(returns_df) < WINDOW:
                        # No new data, return previous results
                        return prev_results
            except:
                prev_results = pd.DataFrame()

    # Calculate rolling Fiedler
    results = []

    for i in range(0, len(returns_df) - WINDOW + 1, STEP):
        window_data = returns_df.iloc[i:i+WINDOW]

        if len(window_data) < MIN_OVERLAP:
            continue

        date = window_data.index[-1]

        fiedler, n_stocks, n_edges, mean_corr, is_connected = calculate_fiedler_value(window_data, THRESHOLD)

        results.append({
            'date': date,
            'fiedler': fiedler,
            'n_stocks': n_stocks,
            'n_edges': n_edges,
            'mean_correlation': mean_corr,
            'is_connected': is_connected
        })

    new_results = pd.DataFrame(results)
    
    # Combine with previous results if available
    if not prev_results.empty and not new_results.empty:
        combined = pd.concat([prev_results, new_results], ignore_index=True)
        combined = combined.drop_duplicates(subset=['date'], keep='last')
        combined = combined.sort_values('date')
        return combined
    elif not prev_results.empty:
        return prev_results
    else:
        return new_results


def analyze_cohesion_change(ts_df, target_date, lookback_days=30):
    """Analyze if cohesion has increased recently"""

    if len(ts_df) < 2:
        return None

    ts_df = ts_df.sort_values('date')

    # Get target date data
    target = pd.to_datetime(target_date)
    ts_df['date'] = pd.to_datetime(ts_df['date'])

    # Find closest date to target
    recent_data = ts_df[ts_df['date'] <= target]
    if len(recent_data) == 0:
        return None

    current = recent_data.iloc[-1]

    # Get lookback period
    lookback_date = target - timedelta(days=lookback_days)
    historical_data = ts_df[ts_df['date'] <= lookback_date]

    if len(historical_data) == 0:
        return None

    historical_mean = historical_data['fiedler'].mean()

    change = current['fiedler'] - historical_mean
    pct_change = (change / historical_mean * 100) if historical_mean > 0 else 0

    return {
        'current_fiedler': current['fiedler'],
        'current_date': current['date'],
        'historical_fiedler': historical_mean,
        'fiedler_change': change,
        'pct_change': pct_change,
        'is_enhanced': change > 0 and current['fiedler'] > 0.5
    }


def generate_markdown_report(enhanced_df, ranking_df, stats, theme_stocks, data_dict, target_date):
    """Generate markdown report for Naver theme cohesion analysis"""
    
    report_file = REPORTS_DIR / f"NAVER_THEME_COHESION_REPORT_{target_date.replace('-', '')}.md"
    date_str = datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y-%m-%d')
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Naver Theme Cohesion Analysis Report\n")
        f.write(f"**Date**: {date_str}\n")
        f.write("**Analysis**: Enhanced Cohesion Detection for Naver Investment Themes\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## 📊 Executive Summary\n\n")
        f.write(f"**Total Themes Analyzed**: {stats['total_themes_analyzed']}\n")
        f.write(f"**Themes with Enhanced Cohesion**: {stats['enhanced_cohesion_themes']} ({stats['pct_enhanced']:.1f}%)\n")
        f.write(f"**Stocks Loaded**: {stats.get('loaded_stocks', len(data_dict))} / {stats.get('total_stocks', sum(len(v) for v in theme_stocks.values()))} ({stats.get('loaded_pct', 0):.1f}%)\n")
        f.write(f"**Analysis Period**: 2025 YTD with {LOOKBACK_DAYS}-day lookback\n\n")
        f.write("---\n\n")
        
        # Top 20 Themes with Strongest Cohesion Enhancement
        if len(enhanced_df) > 0:
            f.write("## 🔥 TOP 20 THEMES WITH STRONGEST COHESION ENHANCEMENT\n\n")
            
            for rank, (idx, row) in enumerate(enhanced_df.head(20).iterrows(), 1):
                # Determine status
                if row['current_fiedler'] > 2.0:
                    status = "🔥 VERY STRONG"
                elif row['current_fiedler'] > 1.0:
                    status = "✅ STRONG"
                elif row['current_fiedler'] > 0.5:
                    status = "✓ MODERATE"
                else:
                    status = "⚠️  WEAK"
                
                # Use target_date (analysis date) instead of actual current_date from data
                # This ensures consistency - all themes show the same analysis date
                # Note: The Fiedler value is calculated from the most recent available data <= target_date
                f.write(f"### Rank {rank}: **{row['theme']}**\n")
                f.write(f"- **Stocks**: {int(row['n_stocks'])}\n")
                f.write(f"- **Current Fiedler**: {row['current_fiedler']:.2f}\n")
                f.write(f"- **Fiedler Change**: {row['fiedler_change']:+.2f} ({row['pct_change']:+.1f}%)\n")
                f.write(f"- **Status**: {status}\n")
                f.write(f"- **Analysis Date**: {date_str}\n\n")
        
        # Summary Statistics
        f.write("---\n\n")
        f.write("## 📈 Summary Statistics\n\n")
        f.write(f"- **Total Themes Analyzed**: {stats['total_themes_analyzed']}\n")
        f.write(f"- **Themes with Sufficient Data**: {stats['themes_with_data']}\n")
        f.write(f"- **Themes with Enhanced Cohesion**: {stats['enhanced_cohesion_themes']} ({stats['pct_enhanced']:.1f}%)\n")
        f.write(f"- **Mean Current Fiedler**: {stats['mean_current_fiedler']:.3f}\n")
        f.write(f"- **Median Current Fiedler**: {stats['median_current_fiedler']:.3f}\n")
        f.write(f"- **Mean Fiedler Change**: {stats['mean_fiedler_change']:+.3f}\n\n")
        
        # Top 30 Most Cohesive Themes (Current Ranking)
        f.write("---\n\n")
        f.write("## 🏆 TOP 30 MOST COHESIVE THEMES (Current Ranking)\n\n")
        f.write("| Rank | Theme | Stocks | Current Fiedler | Change | Status |\n")
        f.write("|------|-------|--------|-----------------|--------|--------|\n")
        
        for rank, (idx, row) in enumerate(ranking_df.head(30).iterrows(), 1):
            status_icon = "📈" if row['fiedler_change'] > 0 else "📉"
            if row['current_fiedler'] > 2.0:
                strength = "🔥 VERY STRONG"
            elif row['current_fiedler'] > 1.0:
                strength = "✅ STRONG"
            elif row['current_fiedler'] > 0.5:
                strength = "✓ MODERATE"
            else:
                strength = "⚠️  WEAK"
            
            f.write(f"| {rank} | {row['theme'][:40]} | {int(row['n_stocks'])} | {row['current_fiedler']:.2f} | {row['fiedler_change']:+.2f} | {status_icon} {strength} |\n")
        
        f.write("\n---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Framework**: Fiedler Eigenvalue Network Analysis\n")
        f.write(f"**Methodology**: Rolling window correlation analysis with {THRESHOLD} correlation threshold\n")
    
    return report_file


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Naver Theme Cohesion Analysis')
    parser.add_argument('--date', type=str, default=None,
                       help='Target date in YYYY-MM-DD format (default: from libPath.txt or today)')
    args = parser.parse_args()
    
    # Set target date - priority: 1) command line arg, 2) libPath.txt, 3) today
    if args.date:
        TARGET_DATE = args.date
    else:
        # Try to read from libPath.txt
        libpath_file = AUTOGLUON_BASE_DIR / "libPath.txt"
        if libpath_file.exists():
            try:
                import json
                with open(libpath_file, 'r', encoding='utf-8') as f:
                    libpath_data = json.load(f)
                    is_date = libpath_data.get('isDate', '')
                    if is_date:
                        TARGET_DATE = is_date  # Already in YYYY-MM-DD format
                        print(f"Using date from libPath.txt: {TARGET_DATE}")
                    else:
                        TARGET_DATE = datetime.now().strftime('%Y-%m-%d')
            except Exception as e:
                print(f"Warning: Could not read libPath.txt, using today's date: {e}")
                TARGET_DATE = datetime.now().strftime('%Y-%m-%d')
        else:
            TARGET_DATE = datetime.now().strftime('%Y-%m-%d')
    
    print("="*80)
    print("Naver Theme Cohesion Analysis")
    print(f"Target Date: {TARGET_DATE}")
    print("="*80)

    # Load theme data with ticker->name mapping
    theme_stocks, stock_themes, ticker_map = load_naver_themes()

    # Get all unique stock names
    all_stock_names = set()
    for stock_names in theme_stocks.values():
        all_stock_names.update(stock_names)

    # Load price data (using Korean names as filenames)
    data_dict = load_price_data(list(all_stock_names))
    
    # Store for report generation
    total_stocks_in_themes = sum(len(v) for v in theme_stocks.values())

    # Calculate rolling Fiedler for each theme
    print("\n" + "="*80)
    print("Calculating Rolling Fiedler Values for Each Theme")
    print("="*80)

    theme_timeseries = {}
    theme_changes = {}

    for i, (theme, tickers) in enumerate(theme_stocks.items(), 1):
        if i % 20 == 0:
            print(f"Progress: {i}/{len(theme_stocks)} themes...")

        # Use incremental calculation (only calculate new windows)
        ts_df = calculate_rolling_theme_fiedler(theme, tickers, data_dict, TARGET_DATE, incremental=True)

        if len(ts_df) > 0:
            theme_timeseries[theme] = ts_df

            # Analyze cohesion change
            change_info = analyze_cohesion_change(ts_df, TARGET_DATE, LOOKBACK_DAYS)
            if change_info:
                theme_changes[theme] = change_info

    print(f"\nAnalyzed {len(theme_timeseries)} themes with sufficient data")

    # Save individual theme timeseries
    print("\n" + "="*80)
    print("Saving Theme Timeseries Data")
    print("="*80)

    for theme, ts_df in theme_timeseries.items():
        safe_name = theme.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')[:50]
        ts_df.to_csv(OUTPUT_DIR / f'theme_{safe_name}_timeseries.csv', index=False)

    print(f"Saved {len(theme_timeseries)} theme timeseries files")

    # Create summary report
    print("\n" + "="*80)
    print(f"Themes with Enhanced Cohesion (as of {TARGET_DATE})")
    print("="*80)

    enhanced_themes = []
    for theme, change in theme_changes.items():
        if change['is_enhanced']:
            enhanced_themes.append({
                'theme': theme,
                'n_stocks': len(theme_stocks[theme]),
                'current_fiedler': change['current_fiedler'],
                'historical_fiedler': change['historical_fiedler'],
                'fiedler_change': change['fiedler_change'],
                'pct_change': change['pct_change'],
                'current_date': change['current_date']
            })

    enhanced_df = pd.DataFrame(enhanced_themes)

    if len(enhanced_df) > 0:
        enhanced_df = enhanced_df.sort_values('fiedler_change', ascending=False)
        enhanced_df.to_csv(OUTPUT_DIR / f'enhanced_cohesion_themes_{TARGET_DATE.replace("-", "")}.csv', index=False)

        print(f"\nFound {len(enhanced_df)} themes with enhanced cohesion\n")
        print("Top 20 Themes with Strongest Cohesion Enhancement:")
        print("-" * 100)

        for i, row in enhanced_df.head(20).iterrows():
            print(f"{i+1:3d}. {row['theme'][:50]:50s} | "
                  f"Stocks={row['n_stocks']:3d} | "
                  f"F={row['current_fiedler']:6.3f} | "
                  f"ΔF={row['fiedler_change']:+6.3f} ({row['pct_change']:+6.1f}%)")
    else:
        print("\nNo themes found with enhanced cohesion")

    # Overall ranking by current Fiedler value
    print("\n" + "="*80)
    print(f"Current Theme Cohesion Ranking (as of {TARGET_DATE})")
    print("="*80)

    current_rankings = []
    for theme, change in theme_changes.items():
        current_rankings.append({
            'theme': theme,
            'n_stocks': len(theme_stocks[theme]),
            'current_fiedler': change['current_fiedler'],
            'fiedler_change': change['fiedler_change'],
            'pct_change': change['pct_change']
        })

    ranking_df = pd.DataFrame(current_rankings)
    ranking_df = ranking_df.sort_values('current_fiedler', ascending=False)
    ranking_df.to_csv(OUTPUT_DIR / f'theme_cohesion_ranking_{TARGET_DATE.replace("-", "")}.csv', index=False)

    print(f"\nTop 30 Most Cohesive Themes:\n")
    print("-" * 100)

    for i, row in ranking_df.head(30).iterrows():
        status = "📈" if row['fiedler_change'] > 0 else "📉"
        if row['current_fiedler'] > 2.0:
            strength = "🔥 VERY STRONG"
        elif row['current_fiedler'] > 1.0:
            strength = "✅ STRONG"
        elif row['current_fiedler'] > 0.5:
            strength = "✓ MODERATE"
        else:
            strength = "⚠️  WEAK"

        print(f"{status} {i+1:3d}. {row['theme'][:45]:45s} | "
              f"N={row['n_stocks']:3d} | "
              f"F={row['current_fiedler']:6.3f} | "
              f"ΔF={row['fiedler_change']:+6.3f} | "
              f"{strength}")

    # Calculate statistics
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)

    stats = {
        'total_themes_analyzed': len(theme_timeseries),
        'themes_with_data': len(theme_changes),
        'enhanced_cohesion_themes': len(enhanced_themes),
        'mean_current_fiedler': ranking_df['current_fiedler'].mean(),
        'median_current_fiedler': ranking_df['current_fiedler'].median(),
        'mean_fiedler_change': ranking_df['fiedler_change'].mean(),
        'pct_enhanced': len(enhanced_themes) / len(theme_changes) * 100 if len(theme_changes) > 0 else 0
    }

    print(f"\nTotal themes analyzed: {stats['total_themes_analyzed']}")
    print(f"Themes with sufficient data: {stats['themes_with_data']}")
    print(f"Themes with enhanced cohesion: {stats['enhanced_cohesion_themes']} ({stats['pct_enhanced']:.1f}%)")
    print(f"Mean current Fiedler: {stats['mean_current_fiedler']:.3f}")
    print(f"Median current Fiedler: {stats['median_current_fiedler']:.3f}")
    print(f"Mean Fiedler change: {stats['mean_fiedler_change']:+.3f}")

    # Generate markdown report
    print("\n" + "="*80)
    print("Generating Markdown Report")
    print("="*80)
    
    # Calculate loaded percentage for report
    loaded_pct = (len(data_dict) / total_stocks_in_themes * 100) if total_stocks_in_themes > 0 else 0
    
    report_file = generate_markdown_report(
        enhanced_df if len(enhanced_df) > 0 else pd.DataFrame(),
        ranking_df,
        {**stats, 'loaded_pct': loaded_pct, 'total_stocks': total_stocks_in_themes, 'loaded_stocks': len(data_dict)},
        theme_stocks,
        data_dict,
        TARGET_DATE
    )
    
    print(f"\nMarkdown report generated: {report_file}")
    
    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)
    print(f"\nOutput Files:")
    print(f"  {OUTPUT_DIR}/enhanced_cohesion_themes_{TARGET_DATE.replace('-', '')}.csv")
    print(f"  {OUTPUT_DIR}/theme_cohesion_ranking_{TARGET_DATE.replace('-', '')}.csv")
    print(f"  {OUTPUT_DIR}/theme_*_timeseries.csv (individual theme files)")
    print(f"  {report_file}")


if __name__ == '__main__':
    main()
