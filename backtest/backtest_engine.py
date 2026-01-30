#!/usr/bin/env python3
"""
Backtest Engine Module

Main walk-forward backtesting logic
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

try:
    from .data_loader import DataLoader
    from .signal_calculator import SignalCalculator
    from .return_calculator import ReturnCalculator
    from .meta_labeler import MetaLabeler
except ImportError:
    from data_loader import DataLoader
    from signal_calculator import SignalCalculator
    from return_calculator import ReturnCalculator
    try:
        from meta_labeler import MetaLabeler
    except ImportError:
        MetaLabeler = None

class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(self, start_date: str, end_date: str, holding_period_weeks: int = 12,
                 meta_labeler_path: Optional[str] = None):
        """
        Args:
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
            holding_period_weeks: Holding period in weeks (default: 12 = 3 months)
            meta_labeler_path: Path to trained meta-labeler model (optional)
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.holding_period_weeks = holding_period_weeks
        
        self.loader = DataLoader()
        self.signal_calc = SignalCalculator()
        
        # Load meta-labeler if provided
        self.meta_labeler = None
        if meta_labeler_path and MetaLabeler is not None:
            try:
                print(f"\nLoading meta-labeler from {meta_labeler_path}...")
                self.meta_labeler = MetaLabeler()
                self.meta_labeler.load(Path(meta_labeler_path))
                print("  Meta-labeler loaded successfully")
            except Exception as e:
                print(f"  Warning: Failed to load meta-labeler: {e}")
                print("  Continuing without meta-labeling...")
        
        # Load database for feature engineering
        self.db_df = None
        try:
            from config import DB_FILE
            if DB_FILE.exists():
                self.db_df = pd.read_csv(DB_FILE)
        except Exception as e:
            print(f"  Warning: Could not load database: {e}")
        
        # Load data
        print("="*80)
        print("Loading Data for Backtest")
        print("="*80)
        self.fiedler_timeseries = self.loader.load_fiedler_timeseries()
        self.theme_mapping = self.loader.load_theme_mapping()
        self.leadership_data = self.loader.load_historical_leadership_data()
        
        # Map theme names from timeseries to actual theme names
        self.theme_name_mapping = self.loader.get_theme_tickers_from_timeseries(self.fiedler_timeseries)
        
        # Load price data for all tickers
        all_tickers = []
        for tickers in self.theme_mapping.values():
            all_tickers.extend(tickers)
        all_tickers = list(set(all_tickers))
        
        print(f"\nLoading price data for {len(all_tickers)} unique tickers...")
        self.price_data = self.loader.load_stock_prices(
            tickers=all_tickers,
            start_date=start_date,
            end_date=(pd.to_datetime(end_date) + timedelta(weeks=holding_period_weeks)).strftime('%Y-%m-%d')
        )
        
        self.return_calc = ReturnCalculator(self.price_data, self.theme_mapping)
        
        # Results storage
        self.signals = []
        self.returns = []
        self.signal_return_pairs = []
    
    def run_backtest(self, evaluation_frequency: str = 'weekly'):
        """
        Run walk-forward backtest
        
        Args:
            evaluation_frequency: 'weekly' or 'daily'
        """
        print("\n" + "="*80)
        print("Running Backtest")
        print("="*80)
        print(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        print(f"Holding period: {self.holding_period_weeks} weeks")
        print(f"Evaluation frequency: {evaluation_frequency}")
        print()
        
        # Generate evaluation dates
        # End date for evaluation should be holding_period_weeks before the actual end_date
        # to ensure we have forward return data
        eval_end_date = self.end_date - timedelta(weeks=self.holding_period_weeks)
        
        if eval_end_date <= self.start_date:
            print(f"  Warning: Evaluation period too short. Start: {self.start_date.date()}, "
                  f"End (minus holding period): {eval_end_date.date()}")
            print(f"  Need at least {self.holding_period_weeks} weeks between start and end dates.")
            return pd.DataFrame()
        
        if evaluation_frequency == 'weekly':
            eval_dates = pd.date_range(
                self.start_date,
                eval_end_date,
                freq='W'
            )
        else:
            eval_dates = pd.date_range(
                self.start_date,
                eval_end_date,
                freq='D'
            )
        
        print(f"Evaluating {len(eval_dates)} dates...")
        
        # Process each date
        for i, eval_date in enumerate(eval_dates):
            if (i + 1) % 10 == 0:
                print(f"  Progress: {i+1}/{len(eval_dates)} dates...")
            
            # For each theme with Fiedler data
            for safe_theme_name, fiedler_ts in self.fiedler_timeseries.items():
                # Find actual theme name
                actual_theme = None
                for actual, safe in self.theme_name_mapping.items():
                    if safe_theme_name.replace(' ', '_') in actual.replace(' ', '_') or \
                       actual.replace(' ', '_') in safe_theme_name.replace(' ', '_'):
                        actual_theme = actual
                        break
                
                if actual_theme is None:
                    # Try direct match
                    if safe_theme_name in self.theme_mapping:
                        actual_theme = safe_theme_name
                    else:
                        continue
                
                # Calculate all individual signals
                all_signals = self.signal_calc.calculate_all_signals_for_date(
                    actual_theme,
                    fiedler_ts,
                    eval_date,
                    self.leadership_data
                )
                
                # Create signal combinations as specified in plan:
                # - Individual signals (Tier only, Cohesion only, Leadership only)
                # - Combined signals (Tier + Cohesion, Tier + Leadership, All three)
                signals = []
                
                # Add individual signals
                signals.extend(all_signals)
                
                # Create combined signals
                tier_signal = next((s for s in all_signals if s['signal_type'] == 'tier'), None)
                cohesion_signal = next((s for s in all_signals if s['signal_type'] == 'cohesion'), None)
                leadership_signals = [s for s in all_signals if s['signal_type'] == 'leadership']
                
                # Tier + Cohesion
                if tier_signal and cohesion_signal:
                    combined = {
                        'theme': actual_theme,
                        'date': eval_date,
                        'signal_type': 'tier+cohesion',
                        'signal_strength': (tier_signal.get('signal_strength', 0) + cohesion_signal.get('signal_strength', 0)) / 2,
                        'tier': tier_signal.get('tier', None),
                        'fiedler_change': cohesion_signal.get('change', None),
                        'pct_change': cohesion_signal.get('pct_change', None),
                        'current_fiedler': tier_signal.get('current_fiedler', None),
                        'week_before_fiedler': tier_signal.get('week_before_fiedler', None),
                        'change': tier_signal.get('change', None)
                    }
                    signals.append(combined)
                
                # Tier + Leadership (use strongest leadership signal)
                if tier_signal and leadership_signals:
                    strongest_leadership = max(leadership_signals, key=lambda x: x.get('signal_strength', 0))
                    combined = {
                        'theme': actual_theme,
                        'date': eval_date,
                        'signal_type': 'tier+leadership',
                        'signal_strength': (tier_signal.get('signal_strength', 0) + strongest_leadership.get('signal_strength', 0)) / 2,
                        'tier': tier_signal.get('tier', None),
                        'leadership_gap': strongest_leadership.get('leadership_gap', None),
                        'current_fiedler': tier_signal.get('current_fiedler', None),
                        'week_before_fiedler': tier_signal.get('week_before_fiedler', None),
                        'change': tier_signal.get('change', None)
                    }
                    signals.append(combined)
                
                # All three (Tier + Cohesion + Leadership)
                if tier_signal and cohesion_signal and leadership_signals:
                    strongest_leadership = max(leadership_signals, key=lambda x: x.get('signal_strength', 0))
                    combined = {
                        'theme': actual_theme,
                        'date': eval_date,
                        'signal_type': 'tier+cohesion+leadership',
                        'signal_strength': (
                            tier_signal.get('signal_strength', 0) + 
                            cohesion_signal.get('signal_strength', 0) + 
                            strongest_leadership.get('signal_strength', 0)
                        ) / 3,
                        'tier': tier_signal.get('tier', None),
                        'fiedler_change': cohesion_signal.get('change', None),
                        'pct_change': cohesion_signal.get('pct_change', None),
                        'leadership_gap': strongest_leadership.get('leadership_gap', None),
                        'current_fiedler': tier_signal.get('current_fiedler', None),
                        'week_before_fiedler': tier_signal.get('week_before_fiedler', None),
                        'change': tier_signal.get('change', None)
                    }
                    signals.append(combined)
                
                # Apply meta-labeling filter if available
                if self.meta_labeler is not None:
                    try:
                        from feature_engineering import FeatureEngineer
                        feature_engineer = FeatureEngineer()
                        
                        # Extract features for all signals
                        signal_features_list = []
                        valid_signals = []
                        
                        for signal in signals:
                            try:
                                theme_tickers = self.theme_mapping.get(actual_theme, [])
                                features = feature_engineer.extract_all_features(
                                    signal,
                                    actual_theme,
                                    theme_tickers,
                                    eval_date,
                                    db_df=self.db_df
                                )
                                signal_features_list.append(features)
                                valid_signals.append(signal)
                            except Exception as e:
                                # Skip signals where feature extraction fails
                                continue
                        
                        if len(signal_features_list) > 0:
                            # Predict which signals to take
                            features_df = pd.DataFrame(signal_features_list)
                            predictions = self.meta_labeler.predict(features_df)
                            
                            # Filter signals based on predictions
                            filtered_signals = [sig for sig, pred in zip(valid_signals, predictions) if pred == 1]
                            
                            if len(filtered_signals) < len(signals):
                                print(f"    Meta-labeler filtered {len(signals)} -> {len(filtered_signals)} signals for {actual_theme}")
                            
                            signals = filtered_signals
                    except Exception as e:
                        print(f"    Warning: Meta-labeling failed: {e}, using all signals")
                
                # For each signal, calculate returns
                for signal in signals:
                    # Calculate theme-level return
                    theme_return = self.return_calc.calculate_theme_return(
                        actual_theme,
                        eval_date,
                        self.holding_period_weeks
                    )
                    
                    if theme_return:
                        # Store signal-return pair
                        pair = {
                            'signal_date': eval_date,
                            'theme': actual_theme,
                            'signal_type': signal['signal_type'],
                            'signal_strength': signal.get('signal_strength', 0),
                            'tier': signal.get('tier', None),
                            'leadership_gap': signal.get('leadership_gap', None),
                            'fiedler_change': signal.get('change', None),
                            'pct_change': signal.get('pct_change', None),
                            'total_return': theme_return['total_return'],
                            'n_stocks': theme_return['n_stocks'],
                            'return_1w': theme_return['intermediate_returns'].get('1w', None),
                            'return_2w': theme_return['intermediate_returns'].get('2w', None),
                            'return_4w': theme_return['intermediate_returns'].get('4w', None),
                            'return_8w': theme_return['intermediate_returns'].get('8w', None),
                            'return_12w': theme_return['total_return']
                        }
                        self.signal_return_pairs.append(pair)
                    
                    # Also calculate ticker-level returns
                    if actual_theme in self.theme_mapping:
                        tickers = self.theme_mapping[actual_theme]
                        for ticker in tickers[:10]:  # Limit to first 10 tickers per theme
                            ticker_return = self.return_calc.calculate_ticker_return(
                                ticker,
                                eval_date,
                                self.holding_period_weeks
                            )
                            
                            if ticker_return:
                                ticker_pair = {
                                    'signal_date': eval_date,
                                    'theme': actual_theme,
                                    'ticker': ticker,
                                    'signal_type': signal['signal_type'],
                                    'signal_strength': signal.get('signal_strength', 0),
                                    'tier': signal.get('tier', None),
                                    'leadership_gap': signal.get('leadership_gap', None),
                                    'fiedler_change': signal.get('change', None),
                                    'total_return': ticker_return['total_return'],
                                    'return_1w': ticker_return['intermediate_returns'].get('1w', None),
                                    'return_2w': ticker_return['intermediate_returns'].get('2w', None),
                                    'return_4w': ticker_return['intermediate_returns'].get('4w', None),
                                    'return_8w': ticker_return['intermediate_returns'].get('8w', None),
                                    'return_12w': ticker_return['total_return']
                                }
                                self.signal_return_pairs.append(ticker_pair)
        
        print(f"\nBacktest complete!")
        print(f"  Total signal-return pairs: {len(self.signal_return_pairs)}")
        
        return pd.DataFrame(self.signal_return_pairs)
    
    def get_results(self) -> pd.DataFrame:
        """Get backtest results as DataFrame"""
        if not self.signal_return_pairs:
            return pd.DataFrame()
        return pd.DataFrame(self.signal_return_pairs)

if __name__ == "__main__":
    # Test backtest engine
    print("="*80)
    print("Testing Backtest Engine")
    print("="*80)
    
    engine = BacktestEngine(
        start_date='2025-02-01',
        end_date='2025-08-01',  # Shorter period for testing
        holding_period_weeks=12
    )
    
    results = engine.run_backtest(evaluation_frequency='weekly')
    print(f"\nResults shape: {results.shape}")
    if len(results) > 0:
        print(f"\nSample results:")
        print(results.head())

