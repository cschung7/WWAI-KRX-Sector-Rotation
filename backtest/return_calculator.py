#!/usr/bin/env python3
"""
Return Calculation Module for Backtesting

Calculates forward returns for themes and individual tickers
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class ReturnCalculator:
    """Calculate forward returns for backtesting"""
    
    def __init__(self, price_data: Dict[str, pd.DataFrame], theme_mapping: Dict[str, List[str]]):
        """
        Args:
            price_data: {ticker: DataFrame with price data}
            theme_mapping: {theme_name: [list of tickers]}
        """
        self.price_data = price_data
        self.theme_mapping = theme_mapping
    
    def calculate_theme_return(self, theme_name: str, signal_date: datetime,
                              holding_period_weeks: int = 12) -> Optional[Dict]:
        """
        Calculate equal-weighted theme portfolio return
        
        Args:
            theme_name: Name of the theme
            signal_date: Date when signal occurred
            holding_period_weeks: Number of weeks to hold (default: 12 = 3 months)
        
        Returns:
            dict with return data or None if insufficient data
        """
        if theme_name not in self.theme_mapping:
            return None
        
        tickers = self.theme_mapping[theme_name]
        if not tickers:
            return None
        
        # Get prices for all tickers in theme
        theme_prices = {}
        for ticker in tickers:
            if ticker in self.price_data:
                df = self.price_data[ticker]
                if 'Close' in df.columns:
                    theme_prices[ticker] = df['Close']
                elif len(df.columns) > 0:
                    # Assume first column is price
                    theme_prices[ticker] = df.iloc[:, 0]
        
        if len(theme_prices) == 0:
            return None
        
        # Get signal date price and forward price
        signal_dt = pd.to_datetime(signal_date)
        end_dt = signal_dt + timedelta(weeks=holding_period_weeks)
        
        # Calculate returns for each ticker
        ticker_returns = {}
        for ticker, price_series in theme_prices.items():
            price_series = price_series.sort_index()
            
            # Find closest date to signal_date
            signal_prices = price_series[price_series.index <= signal_dt]
            if len(signal_prices) == 0:
                continue
            
            signal_price = signal_prices.iloc[-1]
            signal_price_date = signal_prices.index[-1]
            
            # Find closest date to end_date
            end_prices = price_series[price_series.index <= end_dt]
            if len(end_prices) == 0:
                continue
            
            # Get price at end date (or closest before)
            end_price = end_prices.iloc[-1]
            end_price_date = end_prices.index[-1]
            
            # Calculate return
            if signal_price > 0:
                return_pct = ((end_price - signal_price) / signal_price) * 100
                ticker_returns[ticker] = {
                    'return': return_pct,
                    'signal_price': signal_price,
                    'end_price': end_price,
                    'signal_date': signal_price_date,
                    'end_date': end_price_date
                }
        
        if len(ticker_returns) == 0:
            return None
        
        # Calculate equal-weighted portfolio return
        returns = [r['return'] for r in ticker_returns.values()]
        avg_return = np.mean(returns)
        
        # Also calculate at intermediate periods (1, 2, 4, 8 weeks)
        intermediate_returns = {}
        for weeks in [1, 2, 4, 8]:
            if weeks < holding_period_weeks:
                inter_dt = signal_dt + timedelta(weeks=weeks)
                inter_returns = []
                for ticker, price_series in theme_prices.items():
                    price_series = price_series.sort_index()
                    signal_prices = price_series[price_series.index <= signal_dt]
                    if len(signal_prices) == 0:
                        continue
                    signal_price = signal_prices.iloc[-1]
                    inter_prices = price_series[price_series.index <= inter_dt]
                    if len(inter_prices) == 0:
                        continue
                    inter_price = inter_prices.iloc[-1]
                    if signal_price > 0:
                        inter_return = ((inter_price - signal_price) / signal_price) * 100
                        inter_returns.append(inter_return)
                
                if inter_returns:
                    intermediate_returns[f'{weeks}w'] = np.mean(inter_returns)
        
        return {
            'theme': theme_name,
            'signal_date': signal_dt,
            'holding_period_weeks': holding_period_weeks,
            'total_return': avg_return,
            'n_stocks': len(ticker_returns),
            'intermediate_returns': intermediate_returns,
            'ticker_returns': ticker_returns
        }
    
    def calculate_ticker_return(self, ticker: str, signal_date: datetime,
                               holding_period_weeks: int = 12) -> Optional[Dict]:
        """
        Calculate individual ticker return
        
        Args:
            ticker: Ticker symbol
            signal_date: Date when signal occurred
            holding_period_weeks: Number of weeks to hold
        
        Returns:
            dict with return data or None if insufficient data
        """
        if ticker not in self.price_data:
            return None
        
        price_series = self.price_data[ticker]
        if 'Close' in price_series.columns:
            price_series = price_series['Close']
        elif len(price_series.columns) > 0:
            price_series = price_series.iloc[:, 0]
        else:
            return None
        
        price_series = price_series.sort_index()
        signal_dt = pd.to_datetime(signal_date)
        end_dt = signal_dt + timedelta(weeks=holding_period_weeks)
        
        # Get signal price
        signal_prices = price_series[price_series.index <= signal_dt]
        if len(signal_prices) == 0:
            return None
        
        signal_price = signal_prices.iloc[-1]
        signal_price_date = signal_prices.index[-1]
        
        # Get end price
        end_prices = price_series[price_series.index <= end_dt]
        if len(end_prices) == 0:
            return None
        
        end_price = end_prices.iloc[-1]
        end_price_date = end_prices.index[-1]
        
        if signal_price <= 0:
            return None
        
        total_return = ((end_price - signal_price) / signal_price) * 100
        
        # Calculate intermediate returns
        intermediate_returns = {}
        for weeks in [1, 2, 4, 8]:
            if weeks < holding_period_weeks:
                inter_dt = signal_dt + timedelta(weeks=weeks)
                inter_prices = price_series[price_series.index <= inter_dt]
                if len(inter_prices) > 0:
                    inter_price = inter_prices.iloc[-1]
                    inter_return = ((inter_price - signal_price) / signal_price) * 100
                    intermediate_returns[f'{weeks}w'] = inter_return
        
        return {
            'ticker': ticker,
            'signal_date': signal_price_date,
            'holding_period_weeks': holding_period_weeks,
            'total_return': total_return,
            'signal_price': signal_price,
            'end_price': end_price,
            'end_date': end_price_date,
            'intermediate_returns': intermediate_returns
        }

if __name__ == "__main__":
    # Test return calculation
    print("="*80)
    print("Testing Return Calculator")
    print("="*80)
    
    # Create sample price data
    dates = pd.date_range('2025-01-01', '2025-12-31', freq='D')
    sample_prices = {}
    for ticker in ['A001', 'A002', 'A003']:
        prices = pd.DataFrame({
            'Close': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'Open': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'High': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'Low': 100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
            'Volume': np.random.randint(1000, 10000, len(dates))
        }, index=dates)
        sample_prices[ticker] = prices
    
    theme_mapping = {'TestTheme': ['A001', 'A002', 'A003']}
    
    calc = ReturnCalculator(sample_prices, theme_mapping)
    
    test_date = pd.to_datetime('2025-06-01')
    theme_return = calc.calculate_theme_return('TestTheme', test_date, holding_period_weeks=12)
    print(f"\nTheme return: {theme_return}")
    
    ticker_return = calc.calculate_ticker_return('A001', test_date, holding_period_weeks=12)
    print(f"Ticker return: {ticker_return}")

