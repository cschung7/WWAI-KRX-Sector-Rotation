#!/usr/bin/env python3
"""
ETF-Style Gradual Entry Strategy

Based on time decay analysis showing:
- Low returns in weeks 1-4 (0.1-0.2%)
- Significant pickup at 8 weeks (5.0%)
- Peak performance at 12 weeks (12.7%)

Strategy:
- Week 1: Buy 10% of position
- Week 2: Buy 10% of position
- Weeks 3-7: Hold 80% cash, monitor signal validity
- Week 7: If signal still valid, go long with remaining 80%
- Exit: 12 weeks OR 20% return (whichever comes first)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class ETFStyleStrategy:
    """ETF-style gradual entry with cash management"""
    
    def __init__(self, 
                 week1_allocation: float = 0.10,
                 week2_allocation: float = 0.10,
                 week7_allocation: float = 0.80,
                 exit_target_return: float = 20.0,
                 exit_weeks: int = 12,
                 min_signal_strength_week7: float = 0.5):
        """
        Args:
            week1_allocation: Position size at week 1 (default: 10%)
            week2_allocation: Position size at week 2 (default: 10%)
            week7_allocation: Position size at week 7 if signal valid (default: 80%)
            exit_target_return: Exit if return reaches this % (default: 20%)
            exit_weeks: Maximum holding period in weeks (default: 12)
            min_signal_strength_week7: Minimum signal strength at week 7 to go long (default: 0.5)
        """
        self.week1_allocation = week1_allocation
        self.week2_allocation = week2_allocation
        self.week7_allocation = week7_allocation
        self.exit_target_return = exit_target_return
        self.exit_weeks = exit_weeks
        self.min_signal_strength_week7 = min_signal_strength_week7
    
    def calculate_strategy_return(self, 
                                 price_series: pd.Series,
                                 signal_date: datetime,
                                 signal_strength: float,
                                 check_signal_validity: callable = None) -> Dict:
        """
        Calculate return using ETF-style gradual entry strategy
        
        Args:
            price_series: Historical price series (indexed by date)
            signal_date: Date when signal occurred
            signal_strength: Initial signal strength
            check_signal_validity: Function to check if signal is still valid at week 7
                                  (signal_date, check_date) -> (is_valid, new_strength)
        
        Returns:
            dict with strategy performance metrics
        """
        price_series = price_series.sort_index()
        signal_dt = pd.to_datetime(signal_date)
        
        # Get prices at key dates
        week1_dt = signal_dt + timedelta(weeks=1)
        week2_dt = signal_dt + timedelta(weeks=2)
        week7_dt = signal_dt + timedelta(weeks=7)
        week12_dt = signal_dt + timedelta(weeks=self.exit_weeks)
        
        # Get signal price
        signal_prices = price_series[price_series.index <= signal_dt]
        if len(signal_prices) == 0:
            return None
        
        signal_price = signal_prices.iloc[-1]
        
        # Get week 1 price
        week1_prices = price_series[price_series.index <= week1_dt]
        if len(week1_prices) == 0:
            return None
        week1_price = week1_prices.iloc[-1]
        
        # Get week 2 price
        week2_prices = price_series[price_series.index <= week2_dt]
        if len(week2_prices) == 0:
            return None
        week2_price = week2_prices.iloc[-1]
        
        # Check signal validity at week 7
        week7_prices = price_series[price_series.index <= week7_dt]
        if len(week7_prices) == 0:
            return None
        week7_price = week7_prices.iloc[-1]
        
        # Check if signal is still valid at week 7
        signal_still_valid = True
        week7_signal_strength = signal_strength
        
        if check_signal_validity:
            is_valid, new_strength = check_signal_validity(signal_dt, week7_dt)
            signal_still_valid = is_valid and (new_strength >= self.min_signal_strength_week7)
            week7_signal_strength = new_strength if is_valid else 0
        
        # Calculate returns for each position
        # Week 1 position (10%)
        week1_return = ((week1_price - signal_price) / signal_price) * 100 if signal_price > 0 else 0
        
        # Week 2 position (10%)
        week2_return = ((week2_price - signal_price) / signal_price) * 100 if signal_price > 0 else 0
        
        # Determine exit date and price
        exit_date = None
        exit_price = None
        exit_reason = None
        
        # Check for early exit due to target return
        # We need to check prices at each week to see if we hit 20% return
        for week in range(1, self.exit_weeks + 1):
            check_dt = signal_dt + timedelta(weeks=week)
            check_prices = price_series[price_series.index <= check_dt]
            if len(check_prices) == 0:
                continue
            
            check_price = check_prices.iloc[-1]
            
            # Calculate weighted average entry price
            # Week 1: 10% at signal_price
            # Week 2: 10% at week1_price
            # Week 7: 80% at week7_price (if signal valid)
            if signal_still_valid:
                weighted_entry = (
                    self.week1_allocation * signal_price +
                    self.week2_allocation * week1_price +
                    self.week7_allocation * week7_price
                )
            else:
                # Only 20% invested
                weighted_entry = (
                    self.week1_allocation * signal_price +
                    self.week2_allocation * week1_price
                ) / (self.week1_allocation + self.week2_allocation)
            
            current_return = ((check_price - weighted_entry) / weighted_entry) * 100 if weighted_entry > 0 else 0
            
            if current_return >= self.exit_target_return:
                exit_date = check_dt
                exit_price = check_price
                exit_reason = f"Target return ({self.exit_target_return}%) reached at week {week}"
                break
        
        # If no early exit, use week 12
        if exit_date is None:
            week12_prices = price_series[price_series.index <= week12_dt]
            if len(week12_prices) == 0:
                return None
            exit_date = week12_dt
            exit_price = week12_prices.iloc[-1]
            exit_reason = f"Maximum holding period ({self.exit_weeks} weeks)"
        
        # Calculate final return
        if signal_still_valid:
            # Weighted average entry price
            weighted_entry = (
                self.week1_allocation * signal_price +
                self.week2_allocation * week1_price +
                self.week7_allocation * week7_price
            )
            total_allocation = self.week1_allocation + self.week2_allocation + self.week7_allocation
        else:
            # Only 20% invested, 80% cash (0% return on cash)
            weighted_entry = (
                self.week1_allocation * signal_price +
                self.week2_allocation * week1_price
            ) / (self.week1_allocation + self.week2_allocation)
            total_allocation = self.week1_allocation + self.week2_allocation
        
        portfolio_return = ((exit_price - weighted_entry) / weighted_entry) * 100 if weighted_entry > 0 else 0
        
        # Adjust for cash position (if signal invalid, 80% cash earns 0%)
        if not signal_still_valid:
            portfolio_return = portfolio_return * total_allocation
        
        # Calculate intermediate returns for tracking
        intermediate_returns = {}
        for week in [1, 2, 4, 7, 8]:
            if week <= self.exit_weeks:
                check_dt = signal_dt + timedelta(weeks=week)
                check_prices = price_series[price_series.index <= check_dt]
                if len(check_prices) > 0:
                    check_price = check_prices.iloc[-1]
                    if signal_still_valid or week <= 2:
                        if week == 1:
                            entry = signal_price
                        elif week == 2:
                            entry = (self.week1_allocation * signal_price + 
                                    self.week2_allocation * week1_price) / (self.week1_allocation + self.week2_allocation)
                        else:
                            entry = weighted_entry
                        
                        inter_return = ((check_price - entry) / entry) * 100 if entry > 0 else 0
                        if not signal_still_valid and week > 2:
                            inter_return = inter_return * total_allocation
                        intermediate_returns[f'{week}w'] = inter_return
        
        return {
            'strategy': 'etf_style',
            'signal_date': signal_dt,
            'exit_date': exit_date,
            'exit_reason': exit_reason,
            'signal_still_valid_week7': signal_still_valid,
            'week7_signal_strength': week7_signal_strength,
            'total_return': portfolio_return,
            'weighted_entry_price': weighted_entry,
            'exit_price': exit_price,
            'total_allocation': total_allocation,
            'holding_weeks': (exit_date - signal_dt).days / 7,
            'intermediate_returns': intermediate_returns,
            'week1_return': week1_return,
            'week2_return': week2_return
        }
    
    def calculate_theme_strategy_return(self,
                                       theme_name: str,
                                       theme_tickers: List[str],
                                       price_data: Dict[str, pd.DataFrame],
                                       signal_date: datetime,
                                       signal_strength: float,
                                       check_signal_validity: callable = None) -> Dict:
        """
        Calculate ETF-style return for a theme (equal-weighted portfolio)
        
        Args:
            theme_name: Name of the theme
            theme_tickers: List of tickers in the theme
            price_data: Dict of {ticker: DataFrame with price data}
            signal_date: Date when signal occurred
            signal_strength: Initial signal strength
            check_signal_validity: Function to check signal validity at week 7
        
        Returns:
            dict with theme-level strategy performance
        """
        ticker_returns = []
        
        for ticker in theme_tickers:
            if ticker not in price_data:
                continue
            
            df = price_data[ticker]
            if 'Close' in df.columns:
                price_series = df['Close']
            elif len(df.columns) > 0:
                price_series = df.iloc[:, 0]
            else:
                continue
            
            ticker_result = self.calculate_strategy_return(
                price_series,
                signal_date,
                signal_strength,
                check_signal_validity
            )
            
            if ticker_result:
                ticker_returns.append(ticker_result)
        
        if len(ticker_returns) == 0:
            return None
        
        # Average returns across tickers (equal-weighted portfolio)
        avg_return = np.mean([r['total_return'] for r in ticker_returns])
        avg_holding_weeks = np.mean([r['holding_weeks'] for r in ticker_returns])
        valid_count = sum([1 for r in ticker_returns if r['signal_still_valid_week7']])
        
        # Aggregate intermediate returns
        intermediate_returns = {}
        for week in ['1w', '2w', '4w', '7w', '8w']:
            week_returns = [r['intermediate_returns'].get(week, 0) for r in ticker_returns if week in r['intermediate_returns']]
            if week_returns:
                intermediate_returns[week] = np.mean(week_returns)
        
        return {
            'theme': theme_name,
            'strategy': 'etf_style',
            'signal_date': signal_date,
            'total_return': avg_return,
            'holding_weeks': avg_holding_weeks,
            'n_stocks': len(ticker_returns),
            'signal_still_valid_week7_pct': (valid_count / len(ticker_returns)) * 100 if ticker_returns else 0,
            'intermediate_returns': intermediate_returns
        }

if __name__ == "__main__":
    # Test strategy
    print("="*80)
    print("Testing ETF-Style Strategy")
    print("="*80)
    
    # Create sample price data
    dates = pd.date_range('2025-01-01', '2025-12-31', freq='D')
    prices = pd.Series(
        100 + np.cumsum(np.random.randn(len(dates)) * 0.5),
        index=dates
    )
    
    strategy = ETFStyleStrategy()
    
    signal_date = pd.to_datetime('2025-06-01')
    result = strategy.calculate_strategy_return(
        prices,
        signal_date,
        signal_strength=2.0
    )
    
    print(f"\nStrategy Result:")
    print(f"  Total Return: {result['total_return']:.2f}%")
    print(f"  Holding Weeks: {result['holding_weeks']:.1f}")
    print(f"  Exit Reason: {result['exit_reason']}")
    print(f"  Signal Valid Week 7: {result['signal_still_valid_week7']}")

