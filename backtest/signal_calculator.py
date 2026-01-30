#!/usr/bin/env python3
"""
Signal Calculation Module for Backtesting

Calculates investment signals from historical data:
- Tier Classification signals
- Cohesion Enhancement signals
- Leadership Gap signals
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class SignalCalculator:
    """Calculate investment signals from historical data"""
    
    def __init__(self):
        # Tier classification thresholds (from analyze_4_tier_themes.py)
        self.tier1_baseline_min = 2.0
        self.tier1_change_min = 1.5
        self.tier1_current_min = 3.0
        
        self.tier2_baseline_min = 1.0
        self.tier2_baseline_max = 2.0
        self.tier2_change_min = 1.0
        
        # Cohesion enhancement thresholds
        self.cohesion_change_min = 1.5
        self.cohesion_current_min = 2.0
        self.cohesion_pct_change_min = 30.0
        self.cohesion_lookback_days = 30
        
        # Leadership gap thresholds
        self.leadership_gap_thresholds = [20.0, 40.0, 60.0]  # Test multiple thresholds
    
    def calculate_tier_signal(self, theme_name: str, fiedler_ts: pd.DataFrame, 
                              signal_date: datetime) -> Optional[Dict]:
        """
        Calculate tier classification signal for a theme at a specific date
        
        Args:
            theme_name: Name of the theme
            fiedler_ts: DataFrame with columns [date, fiedler, ...]
            signal_date: Date to calculate signal for
        
        Returns:
            dict with signal info or None if no signal
        """
        # Filter to data up to signal_date
        historical_data = fiedler_ts[fiedler_ts['date'] <= pd.to_datetime(signal_date)].copy()
        
        if len(historical_data) < 2:
            return None
        
        historical_data = historical_data.sort_values('date')
        
        # Get current and previous week Fiedler values
        current = historical_data.iloc[-1]
        if len(historical_data) >= 2:
            previous = historical_data.iloc[-2]
        else:
            return None
        
        current_fiedler = current['fiedler']
        week_before_fiedler = previous['fiedler']
        change = current_fiedler - week_before_fiedler
        pct_change = (change / week_before_fiedler * 100) if week_before_fiedler > 0 else 0
        
        # Check TIER 1 criteria
        is_tier1 = (
            week_before_fiedler > self.tier1_baseline_min and
            change > self.tier1_change_min and
            current_fiedler > self.tier1_current_min
        )
        
        # Check TIER 2 criteria
        is_tier2 = (
            week_before_fiedler > self.tier2_baseline_min and
            week_before_fiedler <= self.tier2_baseline_max and
            change > self.tier2_change_min
        )
        
        if is_tier1:
            tier = 1
            signal_strength = min(change / self.tier1_change_min, 3.0)  # Normalize to 0-3
        elif is_tier2:
            tier = 2
            signal_strength = min(change / self.tier2_change_min, 2.0)  # Normalize to 0-2
        else:
            return None  # No signal
        
        return {
            'theme': theme_name,
            'date': signal_date,
            'signal_type': 'tier',
            'tier': tier,
            'signal_strength': signal_strength,
            'current_fiedler': current_fiedler,
            'week_before_fiedler': week_before_fiedler,
            'change': change,
            'pct_change': pct_change
        }
    
    def calculate_cohesion_signal(self, theme_name: str, fiedler_ts: pd.DataFrame,
                                  signal_date: datetime) -> Optional[Dict]:
        """
        Calculate cohesion enhancement signal
        
        Args:
            theme_name: Name of the theme
            fiedler_ts: DataFrame with columns [date, fiedler, ...]
            signal_date: Date to calculate signal for
        
        Returns:
            dict with signal info or None if no signal
        """
        # Filter to data up to signal_date
        historical_data = fiedler_ts[fiedler_ts['date'] <= pd.to_datetime(signal_date)].copy()
        
        if len(historical_data) < 2:
            return None
        
        historical_data = historical_data.sort_values('date')
        
        # Get current Fiedler
        current = historical_data.iloc[-1]
        current_fiedler = current['fiedler']
        current_date = current['date']
        
        # Get lookback period (30 days before current date)
        lookback_date = current_date - timedelta(days=self.cohesion_lookback_days)
        historical_period = historical_data[historical_data['date'] <= lookback_date]
        
        if len(historical_period) == 0:
            return None
        
        historical_mean = historical_period['fiedler'].mean()
        change = current_fiedler - historical_mean
        pct_change = (change / historical_mean * 100) if historical_mean > 0 else 0
        
        # Check signal criteria
        is_signal = (
            change > self.cohesion_change_min and
            current_fiedler > self.cohesion_current_min and
            pct_change > self.cohesion_pct_change_min
        )
        
        if not is_signal:
            return None
        
        signal_strength = min(change / self.cohesion_change_min, 3.0)  # Normalize
        
        return {
            'theme': theme_name,
            'date': signal_date,
            'signal_type': 'cohesion',
            'signal_strength': signal_strength,
            'current_fiedler': current_fiedler,
            'historical_fiedler': historical_mean,
            'change': change,
            'pct_change': pct_change
        }
    
    def calculate_leadership_signal(self, theme_name: str, leadership_data: pd.DataFrame,
                                    signal_date: datetime, threshold: float = 20.0) -> Optional[Dict]:
        """
        Calculate leadership gap signal
        
        Args:
            theme_name: Name of the theme
            leadership_data: DataFrame with leadership gap data
            signal_date: Date to calculate signal for
            threshold: Minimum leadership gap for signal
        
        Returns:
            dict with signal info or None if no signal
        """
        # Filter to theme
        theme_data = leadership_data[leadership_data['Theme'] == theme_name]
        
        if len(theme_data) == 0:
            return None
        
        # Use latest available data (leadership data may not have dates)
        latest = theme_data.iloc[-1]
        
        leadership_gap = latest.get('Leadership_Gap', 0)
        
        # Handle percentage string format
        if isinstance(leadership_gap, str):
            leadership_gap = float(leadership_gap.replace('%', ''))
        
        if leadership_gap < threshold:
            return None
        
        signal_strength = min(leadership_gap / threshold, 3.0)  # Normalize
        
        return {
            'theme': theme_name,
            'date': signal_date,
            'signal_type': 'leadership',
            'signal_strength': signal_strength,
            'leadership_gap': leadership_gap,
            'threshold': threshold
        }
    
    def calculate_all_signals_for_date(self, theme_name: str, fiedler_ts: pd.DataFrame,
                                      signal_date: datetime, leadership_data: pd.DataFrame = None) -> List[Dict]:
        """
        Calculate all signals for a theme at a specific date
        
        Returns:
            list of signal dicts (can be empty)
        """
        signals = []
        
        # Tier signal
        tier_signal = self.calculate_tier_signal(theme_name, fiedler_ts, signal_date)
        if tier_signal:
            signals.append(tier_signal)
        
        # Cohesion signal
        cohesion_signal = self.calculate_cohesion_signal(theme_name, fiedler_ts, signal_date)
        if cohesion_signal:
            signals.append(cohesion_signal)
        
        # Leadership signal (if data available)
        if leadership_data is not None and len(leadership_data) > 0:
            for threshold in self.leadership_gap_thresholds:
                leadership_signal = self.calculate_leadership_signal(
                    theme_name, leadership_data, signal_date, threshold
                )
                if leadership_signal:
                    signals.append(leadership_signal)
        
        return signals

if __name__ == "__main__":
    # Test signal calculation
    print("="*80)
    print("Testing Signal Calculator")
    print("="*80)
    
    calc = SignalCalculator()
    
    # Create sample Fiedler timeseries
    dates = pd.date_range('2025-02-01', '2025-11-12', freq='W')
    sample_ts = pd.DataFrame({
        'date': dates,
        'fiedler': np.linspace(1.0, 4.5, len(dates)),
        'n_stocks': [88] * len(dates)
    })
    
    # Test tier signal
    test_date = pd.to_datetime('2025-06-01')
    tier_signal = calc.calculate_tier_signal('OLED', sample_ts, test_date)
    print(f"\nTier signal: {tier_signal}")
    
    # Test cohesion signal
    cohesion_signal = calc.calculate_cohesion_signal('OLED', sample_ts, test_date)
    print(f"Cohesion signal: {cohesion_signal}")

