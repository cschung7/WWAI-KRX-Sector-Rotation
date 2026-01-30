#!/usr/bin/env python3
"""
Improved ETF-Style Strategy with Relaxed Signal Validity

Strategy variations:
1. Relaxed validity: Buy remaining 80% if signal is still positive (even if weakened)
2. Alternative allocation: 20% week 1, 20% week 2, 60% week 7
3. Buy after 8 weeks: Skip gradual entry, buy 100% at week 8
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class ImprovedETFStrategy:
    """Improved ETF-style strategy with multiple variants"""
    
    def __init__(self, 
                 strategy_type: str = 'relaxed',
                 week1_allocation: float = 0.10,
                 week2_allocation: float = 0.10,
                 week7_allocation: float = 0.80,
                 week8_allocation: float = 1.0,  # For "buy_after_8w" strategy
                 exit_target_return: float = 20.0,
                 exit_weeks: int = 12,
                 min_signal_strength_week7: float = 0.0):  # Relaxed: just check if positive
        """
        Args:
            strategy_type: 'relaxed', 'alternative', or 'buy_after_8w'
            week1_allocation: Position size at week 1
            week2_allocation: Position size at week 2
            week7_allocation: Position size at week 7 if signal valid
            week8_allocation: Position size at week 8 (for buy_after_8w)
            exit_target_return: Exit if return reaches this %
            exit_weeks: Maximum holding period in weeks
            min_signal_strength_week7: Minimum signal strength (relaxed: 0.0 = just positive)
        """
        self.strategy_type = strategy_type
        self.week1_allocation = week1_allocation
        self.week2_allocation = week2_allocation
        self.week7_allocation = week7_allocation
        self.week8_allocation = week8_allocation
        self.exit_target_return = exit_target_return
        self.exit_weeks = exit_weeks
        self.min_signal_strength_week7 = min_signal_strength_week7
        
        # Adjust allocations based on strategy type
        if strategy_type == 'alternative':
            self.week1_allocation = 0.20
            self.week2_allocation = 0.20
            self.week7_allocation = 0.60
        elif strategy_type == 'buy_after_8w':
            self.week1_allocation = 0.0
            self.week2_allocation = 0.0
            self.week7_allocation = 0.0
    
    def calculate_strategy_return(self, 
                                 price_series: pd.Series,
                                 signal_date: datetime,
                                 signal_strength: float,
                                 check_signal_validity: callable = None) -> Dict:
        """Calculate return using improved ETF-style strategy"""
        price_series = price_series.sort_index()
        signal_dt = pd.to_datetime(signal_date)
        
        if self.strategy_type == 'buy_after_8w':
            return self._calculate_buy_after_8w(price_series, signal_dt, signal_strength, check_signal_validity)
        else:
            return self._calculate_gradual_entry(price_series, signal_dt, signal_strength, check_signal_validity)
    
    def _calculate_buy_after_8w(self, price_series, signal_dt, signal_strength, check_signal_validity):
        """Buy 100% at week 8, exit at 12 weeks or 20% return"""
        week8_dt = signal_dt + timedelta(weeks=8)
        week12_dt = signal_dt + timedelta(weeks=self.exit_weeks)
        
        # Get signal price (for reference)
        signal_prices = price_series[price_series.index <= signal_dt]
        if len(signal_prices) == 0:
            return None
        signal_price = signal_prices.iloc[-1]
        
        # Get week 8 price (entry)
        week8_prices = price_series[price_series.index <= week8_dt]
        if len(week8_prices) == 0:
            return None
        week8_price = week8_prices.iloc[-1]
        
        # Check signal validity at week 8
        signal_still_valid = True
        week8_signal_strength = signal_strength
        
        if check_signal_validity:
            is_valid, new_strength = check_signal_validity(signal_dt, week8_dt)
            signal_still_valid = is_valid and (new_strength >= self.min_signal_strength_week7)
            week8_signal_strength = new_strength if is_valid else 0
        
        if not signal_still_valid:
            return None  # Don't enter if signal invalid
        
        # Find exit
        exit_date = None
        exit_price = None
        exit_reason = None
        
        for week in range(9, self.exit_weeks + 1):
            check_dt = signal_dt + timedelta(weeks=week)
            check_prices = price_series[price_series.index <= check_dt]
            if len(check_prices) == 0:
                continue
            
            check_price = check_prices.iloc[-1]
            current_return = ((check_price - week8_price) / week8_price) * 100 if week8_price > 0 else 0
            
            if current_return >= self.exit_target_return:
                exit_date = check_dt
                exit_price = check_price
                exit_reason = f"Target return ({self.exit_target_return}%) reached at week {week}"
                break
        
        if exit_date is None:
            week12_prices = price_series[price_series.index <= week12_dt]
            if len(week12_prices) == 0:
                return None
            exit_date = week12_dt
            exit_price = week12_prices.iloc[-1]
            exit_reason = f"Maximum holding period ({self.exit_weeks} weeks)"
        
        portfolio_return = ((exit_price - week8_price) / week8_price) * 100 if week8_price > 0 else 0
        
        return {
            'strategy': 'buy_after_8w',
            'signal_date': signal_dt,
            'entry_date': week8_dt,
            'exit_date': exit_date,
            'exit_reason': exit_reason,
            'signal_still_valid_week8': signal_still_valid,
            'week8_signal_strength': week8_signal_strength,
            'total_return': portfolio_return,
            'entry_price': week8_price,
            'exit_price': exit_price,
            'holding_weeks': (exit_date - week8_dt).days / 7,
        }
    
    def _calculate_gradual_entry(self, price_series, signal_dt, signal_strength, check_signal_validity):
        """Gradual entry: 10% week 1, 10% week 2, 80% week 7 (if valid)"""
        week1_dt = signal_dt + timedelta(weeks=1)
        week2_dt = signal_dt + timedelta(weeks=2)
        week7_dt = signal_dt + timedelta(weeks=7)
        week12_dt = signal_dt + timedelta(weeks=self.exit_weeks)
        
        # Get prices
        signal_prices = price_series[price_series.index <= signal_dt]
        if len(signal_prices) == 0:
            return None
        signal_price = signal_prices.iloc[-1]
        
        week1_prices = price_series[price_series.index <= week1_dt]
        if len(week1_prices) == 0:
            return None
        week1_price = week1_prices.iloc[-1]
        
        week2_prices = price_series[price_series.index <= week2_dt]
        if len(week2_prices) == 0:
            return None
        week2_price = week2_prices.iloc[-1]
        
        week7_prices = price_series[price_series.index <= week7_dt]
        if len(week7_prices) == 0:
            return None
        week7_price = week7_prices.iloc[-1]
        
        # Check signal validity (relaxed: just check if positive)
        signal_still_valid = True
        week7_signal_strength = signal_strength
        
        if check_signal_validity:
            is_valid, new_strength = check_signal_validity(signal_dt, week7_dt)
            # Relaxed: accept if signal is still positive (even if weakened)
            signal_still_valid = is_valid and (new_strength >= self.min_signal_strength_week7)
            week7_signal_strength = new_strength if is_valid else 0
        
        # Calculate weighted entry price
        if signal_still_valid:
            weighted_entry = (
                self.week1_allocation * signal_price +
                self.week2_allocation * week1_price +
                self.week7_allocation * week7_price
            )
            total_allocation = self.week1_allocation + self.week2_allocation + self.week7_allocation
        else:
            # Only partial allocation
            weighted_entry = (
                self.week1_allocation * signal_price +
                self.week2_allocation * week1_price
            ) / (self.week1_allocation + self.week2_allocation)
            total_allocation = self.week1_allocation + self.week2_allocation
        
        # Find exit
        exit_date = None
        exit_price = None
        exit_reason = None
        
        for week in range(1, self.exit_weeks + 1):
            check_dt = signal_dt + timedelta(weeks=week)
            check_prices = price_series[price_series.index <= check_dt]
            if len(check_prices) == 0:
                continue
            
            check_price = check_prices.iloc[-1]
            current_return = ((check_price - weighted_entry) / weighted_entry) * 100 if weighted_entry > 0 else 0
            
            if not signal_still_valid and week > 2:
                current_return = current_return * total_allocation
            
            if current_return >= self.exit_target_return:
                exit_date = check_dt
                exit_price = check_price
                exit_reason = f"Target return ({self.exit_target_return}%) reached at week {week}"
                break
        
        if exit_date is None:
            week12_prices = price_series[price_series.index <= week12_dt]
            if len(week12_prices) == 0:
                return None
            exit_date = week12_dt
            exit_price = week12_prices.iloc[-1]
            exit_reason = f"Maximum holding period ({self.exit_weeks} weeks)"
        
        # Final return
        portfolio_return = ((exit_price - weighted_entry) / weighted_entry) * 100 if weighted_entry > 0 else 0
        
        if not signal_still_valid:
            portfolio_return = portfolio_return * total_allocation
        
        return {
            'strategy': self.strategy_type,
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
        }
    
    def calculate_theme_strategy_return(self,
                                       theme_name: str,
                                       theme_tickers: List[str],
                                       price_data: Dict[str, pd.DataFrame],
                                       signal_date: datetime,
                                       signal_strength: float,
                                       check_signal_validity: callable = None) -> Dict:
        """Calculate strategy return for a theme"""
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
        
        # Average returns across tickers
        avg_return = np.mean([r['total_return'] for r in ticker_returns])
        avg_holding_weeks = np.mean([r['holding_weeks'] for r in ticker_returns])
        valid_count = sum([1 for r in ticker_returns if r.get('signal_still_valid_week7', False) or r.get('signal_still_valid_week8', False)])
        
        return {
            'theme': theme_name,
            'strategy': self.strategy_type,
            'signal_date': signal_date,
            'total_return': avg_return,
            'holding_weeks': avg_holding_weeks,
            'n_stocks': len(ticker_returns),
            'signal_still_valid_pct': (valid_count / len(ticker_returns)) * 100 if ticker_returns else 0,
        }

