#!/usr/bin/env python3
"""
Data Loading Module for Backtesting

Loads historical data needed for backtesting:
- Fiedler timeseries
- Stock prices and returns
- Regime data
- Theme-to-ticker mappings
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
import ast
import glob
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    DATA_DIR, PRICE_DATA_DIR, DB_FILE, REGIME_DIR,
    THEME_TO_TICKERS_FILE, AUTOGLUON_BASE_DIR
)

class DataLoader:
    """Load historical data for backtesting"""
    
    def __init__(self):
        self.data_dir = DATA_DIR
        self.price_data_dir = PRICE_DATA_DIR
        self.db_file = DB_FILE
        self.regime_dir = REGIME_DIR
        self.theme_file = THEME_TO_TICKERS_FILE
        
    def load_fiedler_timeseries(self):
        """
        Load all theme Fiedler timeseries from data/theme_*_timeseries.csv files
        
        Returns:
            dict: {theme_name: DataFrame with columns [date, fiedler, n_stocks, ...]}
        """
        print("Loading Fiedler timeseries data...")
        timeseries_files = glob.glob(str(self.data_dir / "theme_*_timeseries.csv"))
        
        theme_timeseries = {}
        for file_path in timeseries_files:
            try:
                df = pd.read_csv(file_path, parse_dates=['date'])
                df['date'] = pd.to_datetime(df['date'])
                
                # Extract theme name from filename
                # Format: theme_OLED유기_발광_다이오드_timeseries.csv
                filename = Path(file_path).stem
                theme_name = filename.replace('theme_', '').replace('_timeseries', '')
                # Try to reconstruct original theme name (approximate)
                theme_name = theme_name.replace('_', ' ')
                
                # Store with original theme name if we can find it
                theme_timeseries[theme_name] = df.sort_values('date')
            except Exception as e:
                print(f"  Warning: Could not load {file_path}: {e}")
                continue
        
        print(f"  Loaded {len(theme_timeseries)} theme timeseries")
        return theme_timeseries
    
    def load_theme_mapping(self):
        """
        Load theme-to-ticker mapping
        
        Returns:
            dict: {theme_name: [list of tickers]}
        """
        print("Loading theme-to-ticker mapping...")
        
        if not self.theme_file.exists():
            # Fallback: load from database
            return self._load_theme_mapping_from_db()
        
        with open(self.theme_file, 'r', encoding='utf-8') as f:
            theme_data = json.load(f)
        
        print(f"  Loaded {len(theme_data)} themes")
        return theme_data
    
    def _load_theme_mapping_from_db(self):
        """Load theme mapping from database as fallback"""
        print("  Loading from database...")
        db_df = pd.read_csv(self.db_file)
        
        theme_stocks = {}
        for _, row in db_df.iterrows():
            ticker = row['tickers']
            themes_str = row.get('naverTheme', '[]')
            
            try:
                themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
                if isinstance(themes, list):
                    for theme in themes:
                        if theme not in theme_stocks:
                            theme_stocks[theme] = []
                        theme_stocks[theme].append(ticker)
            except:
                continue
        
        return theme_stocks
    
    def load_stock_prices(self, tickers=None, start_date=None, end_date=None):
        """
        Load historical stock prices
        
        Args:
            tickers: List of tickers to load (None = load all)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            dict: {ticker: DataFrame with price data}
        """
        print("Loading stock price data...")
        
        if not self.price_data_dir.exists():
            print(f"  Warning: Price data directory not found: {self.price_data_dir}")
            return {}
        
        price_data = {}
        price_files = list(self.price_data_dir.glob("*.csv"))
        
        if tickers:
            # Filter to requested tickers
            ticker_set = set(tickers)
            price_files = [f for f in price_files if f.stem in ticker_set]
        
        print(f"  Found {len(price_files)} price files")
        
        for price_file in price_files:
            ticker = price_file.stem
            try:
                df = pd.read_csv(price_file, index_col=0, parse_dates=True)
                
                # Filter by date range if provided
                if start_date:
                    df = df[df.index >= pd.to_datetime(start_date)]
                if end_date:
                    df = df[df.index <= pd.to_datetime(end_date)]
                
                if len(df) > 0:
                    price_data[ticker] = df
            except Exception as e:
                continue
        
        print(f"  Loaded {len(price_data)} stock price series")
        return price_data
    
    def load_regime_data(self, date=None):
        """
        Load regime data for a specific date or latest available
        
        Args:
            date: Specific date to load (YYYY-MM-DD), None = latest
        
        Returns:
            DataFrame: Regime data with columns [Ticker, Date, Is_Bull, Is_Bear, ...]
        """
        print("Loading regime data...")
        
        if not self.regime_dir.exists():
            print(f"  Warning: Regime directory not found: {self.regime_dir}")
            return pd.DataFrame()
        
        regime_files = list(self.regime_dir.glob("all_regimes_*.csv"))
        if not regime_files:
            print("  No regime files found")
            return pd.DataFrame()
        
        # Load latest file
        latest_file = sorted(regime_files)[-1]
        df = pd.read_csv(latest_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        if date:
            target_date = pd.to_datetime(date)
            df = df[df['Date'] == target_date]
        else:
            # Use latest date
            latest_date = df['Date'].max()
            df = df[df['Date'] == latest_date]
        
        print(f"  Loaded regime data for {len(df)} stocks")
        return df
    
    def load_historical_leadership_data(self):
        """
        Load historical leadership gap data if available
        
        Returns:
            DataFrame: Historical leadership rankings or empty DataFrame
        """
        print("Loading historical leadership data...")
        
        leadership_file = self.data_dir / "within_theme_leadership_ranking.csv"
        if leadership_file.exists():
            df = pd.read_csv(leadership_file)
            print(f"  Loaded {len(df)} leadership records")
            return df
        else:
            print("  No historical leadership data found")
            return pd.DataFrame()
    
    def get_theme_tickers_from_timeseries(self, theme_timeseries):
        """
        Map theme names from timeseries files to actual theme names and tickers
        
        Args:
            theme_timeseries: dict from load_fiedler_timeseries()
        
        Returns:
            dict: {actual_theme_name: [tickers]}
        """
        theme_mapping = self.load_theme_mapping()
        
        # Create reverse mapping: safe_name -> actual_theme_name
        safe_to_actual = {}
        for actual_theme, tickers in theme_mapping.items():
            safe_name = actual_theme.replace('/', '_').replace(' ', '_').replace('(', '').replace(')', '')[:50]
            safe_to_actual[safe_name] = actual_theme
        
        # Map timeseries themes to actual themes
        result = {}
        for safe_theme_name, ts_df in theme_timeseries.items():
            # Try to find matching actual theme
            actual_theme = None
            for safe, actual in safe_to_actual.items():
                if safe_theme_name.replace(' ', '_') in safe or safe in safe_theme_name.replace(' ', '_'):
                    actual_theme = actual
                    break
            
            if actual_theme and actual_theme in theme_mapping:
                result[actual_theme] = theme_mapping[actual_theme]
            else:
                # Use safe name as fallback
                result[safe_theme_name] = []
        
        return result

if __name__ == "__main__":
    loader = DataLoader()
    
    # Test loading
    print("="*80)
    print("Testing Data Loader")
    print("="*80)
    
    fiedler_data = loader.load_fiedler_timeseries()
    print(f"\nFiedler timeseries: {len(fiedler_data)} themes")
    if fiedler_data:
        sample_theme = list(fiedler_data.keys())[0]
        print(f"  Sample theme '{sample_theme}': {len(fiedler_data[sample_theme])} data points")
        print(f"    Date range: {fiedler_data[sample_theme]['date'].min()} to {fiedler_data[sample_theme]['date'].max()}")
    
    theme_mapping = loader.load_theme_mapping()
    print(f"\nTheme mapping: {len(theme_mapping)} themes")
    if theme_mapping:
        sample_theme = list(theme_mapping.keys())[0]
        print(f"  Sample theme '{sample_theme}': {len(theme_mapping[sample_theme])} tickers")
    
    prices = loader.load_stock_prices()
    print(f"\nStock prices: {len(prices)} stocks")
    
    regime = loader.load_regime_data()
    print(f"\nRegime data: {len(regime)} records")

