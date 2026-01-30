#!/usr/bin/env python3
"""
Enhanced Signal Calculator with Regime Probability

Adds regime-based filtering and scoring using:
- Bull/Bear probabilities
- Trend Strength
- Momentum Score
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from signal_calculator import SignalCalculator

class EnhancedSignalCalculator(SignalCalculator):
    """Enhanced signal calculator with regime probability integration"""
    
    def __init__(self, regime_summary=None):
        """
        Args:
            regime_summary: DataFrame with regime data (Stock_Name, Bull_Pct, Trend_Strength, Momentum_Score)
        """
        super().__init__()
        self.regime_summary = regime_summary
    
    def calculate_theme_regime_metrics(self, theme_name: str, theme_tickers: List[str], 
                                      db_df: pd.DataFrame) -> Optional[Dict]:
        """
        Calculate regime metrics for a theme
        
        Args:
            theme_name: Name of the theme
            theme_tickers: List of ticker codes (e.g., ['60310', '6840'])
            db_df: Database DataFrame with columns [tickers, name, ...]
        
        Returns:
            dict with theme-level regime statistics
        """
        if self.regime_summary is None or len(self.regime_summary) == 0:
            return None
        
        # Get stock names for tickers
        # Theme tickers can be either:
        # 1. Ticker codes (numbers like 6840) - need to look up name in DB
        # 2. Stock names (strings like 'AK홀딩스') - can use directly
        theme_stocks = []
        for ticker in theme_tickers:
            # Check if ticker is already a stock name (string that's not numeric)
            if isinstance(ticker, str) and not ticker.isdigit():
                # Already a stock name, use directly
                theme_stocks.append(ticker)
            else:
                # Ticker code - need to look up name
                ticker_val = ticker
                if isinstance(ticker, str):
                    try:
                        ticker_val = int(ticker)
                    except:
                        # If can't convert, might already be a name
                        theme_stocks.append(ticker)
                        continue
                
                # Match by tickers column (can be int or string)
                db_row = db_df[db_df['tickers'] == ticker_val]
                if db_row.empty:
                    # Try string matching
                    db_row = db_df[db_df['tickers'].astype(str) == str(ticker_val)]
                
                if not db_row.empty:
                    stock_name = db_row.iloc[0]['name']
                    theme_stocks.append(stock_name)
        
        if len(theme_stocks) == 0:
            return None
        
        # Get regime data for theme stocks
        # Regime data uses Korean stock names in 'Ticker' column (renamed to 'Stock_Name' in summary)
        regime_data = []
        for stock_name in theme_stocks:
            regime_row = self.regime_summary[self.regime_summary['Stock_Name'] == stock_name]
            if not regime_row.empty:
                regime_data.append({
                    'bull_pct': regime_row.iloc[0]['Bull_Pct'],
                    'trend': regime_row.iloc[0].get('Trend_Strength', 0),
                    'momentum': regime_row.iloc[0].get('Momentum_Score', 0)
                })
        
        if len(regime_data) == 0:
            return None
        
        # Calculate theme-level averages
        avg_bull_pct = np.mean([d['bull_pct'] for d in regime_data])
        avg_trend = np.mean([d['trend'] for d in regime_data])
        avg_momentum = np.mean([d['momentum'] for d in regime_data])
        
        # Count stocks in bull regime
        bull_count = sum(1 for d in regime_data if d['bull_pct'] > 50)
        bull_ratio = bull_count / len(regime_data) if regime_data else 0
        
        return {
            'theme': theme_name,
            'avg_bull_pct': avg_bull_pct,
            'avg_trend_strength': avg_trend,
            'avg_momentum_score': avg_momentum,
            'bull_ratio': bull_ratio,
            'n_stocks_with_regime': len(regime_data)
        }
    
    def calculate_all_signals_with_regime(self, theme_name: str, fiedler_ts: pd.DataFrame,
                                         signal_date: datetime, leadership_data: pd.DataFrame = None,
                                         theme_tickers: List[str] = None, db_df: pd.DataFrame = None) -> List[Dict]:
        """
        Calculate all signals with regime metrics included
        
        Returns:
            list of signal dicts with regime metrics added
        """
        # Get base signals
        signals = self.calculate_all_signals_for_date(
            theme_name, fiedler_ts, signal_date, leadership_data
        )
        
        # Add regime metrics to each signal
        if self.regime_summary is not None and theme_tickers is not None and db_df is not None:
            regime_metrics = self.calculate_theme_regime_metrics(theme_name, theme_tickers, db_df)
            
            if regime_metrics:
                for signal in signals:
                    signal['regime_avg_bull_pct'] = regime_metrics['avg_bull_pct']
                    signal['regime_avg_trend'] = regime_metrics['avg_trend_strength']
                    signal['regime_avg_momentum'] = regime_metrics['avg_momentum_score']
                    signal['regime_bull_ratio'] = regime_metrics['bull_ratio']
        
        return signals
    
    def calculate_regime_signal(self, theme_name: str, theme_tickers: List[str],
                               db_df: pd.DataFrame, min_bull_pct: float = 40.0,
                               min_trend: float = 0.0, min_momentum: float = 0.0) -> Optional[Dict]:
        """
        Calculate regime-based signal
        
        Args:
            theme_name: Name of the theme
            theme_tickers: List of tickers in theme
            db_df: Database DataFrame
            min_bull_pct: Minimum average bull % for signal
            min_trend: Minimum trend strength for signal
            min_momentum: Minimum momentum score for signal
        
        Returns:
            dict with regime signal info or None
        """
        if self.regime_summary is None:
            return None
        
        regime_metrics = self.calculate_theme_regime_metrics(theme_name, theme_tickers, db_df)
        
        if regime_metrics is None:
            return None
        
        # Check if meets criteria
        if (regime_metrics['avg_bull_pct'] >= min_bull_pct and
            regime_metrics['avg_trend_strength'] >= min_trend and
            regime_metrics['avg_momentum_score'] >= min_momentum):
            
            # Calculate signal strength based on regime metrics
            bull_score = min(regime_metrics['avg_bull_pct'] / 100, 1.0)
            trend_score = min(regime_metrics['avg_trend_strength'] / 1.0, 1.0) if regime_metrics['avg_trend_strength'] > 0 else 0
            momentum_score = min(regime_metrics['avg_momentum_score'] / 1.0, 1.0) if regime_metrics['avg_momentum_score'] > 0 else 0
            
            signal_strength = (bull_score * 0.5 + trend_score * 0.3 + momentum_score * 0.2) * 3.0
            
            return {
                'theme': theme_name,
                'signal_type': 'regime',
                'signal_strength': signal_strength,
                'avg_bull_pct': regime_metrics['avg_bull_pct'],
                'avg_trend_strength': regime_metrics['avg_trend_strength'],
                'avg_momentum_score': regime_metrics['avg_momentum_score'],
                'bull_ratio': regime_metrics['bull_ratio']
            }
        
        return None

