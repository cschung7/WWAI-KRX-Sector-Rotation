#!/usr/bin/env python3
"""
Feature Engineering Module for Meta-Labeling

Extracts features from:
- Signal data (Tier, Cohesion, Leadership Gap)
- Regime data (bull %, trend, momentum)
- UCS_LRS analysis results (ticker-level technical analysis)
- Theme characteristics
- Market context
"""

import pandas as pd
import numpy as np
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import AUTOGLUON_BASE_DIR

class FeatureEngineer:
    """Extract features for meta-labeling"""
    
    def __init__(self, ucs_lrs_dir: Optional[Path] = None):
        """
        Args:
            ucs_lrs_dir: Directory containing combined_analysis_results_*.json files
        """
        if ucs_lrs_dir is None:
            self.ucs_lrs_dir = AUTOGLUON_BASE_DIR / "Filter" / "UCS_LRS"
        else:
            self.ucs_lrs_dir = Path(ucs_lrs_dir)
        
        self.ucs_cache = {}  # Cache loaded UCS_LRS data
    
    def load_ucs_data_for_date(self, date: datetime) -> Dict:
        """
        Load UCS_LRS data for a specific date
        
        Args:
            date: Target date
            
        Returns:
            dict: {ticker: analysis_data} for the date
        """
        date_str = date.strftime('%Y-%m-%d')
        
        # Check cache first
        if date_str in self.ucs_cache:
            return self.ucs_cache[date_str]
        
        # Find matching file
        json_files = sorted(glob.glob(str(self.ucs_lrs_dir / "combined_analysis_results_*.json")))
        
        for json_file in reversed(json_files):  # Start from most recent
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                
                # Check if date is in this file
                if date_str in file_data:
                    self.ucs_cache[date_str] = file_data[date_str]
                    return file_data[date_str]
                
                # Check date range in filename
                filename = Path(json_file).name
                if 'to' in filename:
                    parts = filename.replace('combined_analysis_results_', '').replace('.json', '').split('_to_')
                    if len(parts) == 2:
                        start_date = pd.to_datetime(parts[0])
                        end_date = pd.to_datetime(parts[1])
                        if start_date <= date <= end_date:
                            # Date is in range, check if it exists
                            if date_str in file_data:
                                self.ucs_cache[date_str] = file_data[date_str]
                                return file_data[date_str]
            except Exception as e:
                continue
        
        return {}
    
    def extract_ticker_features(self, ticker: str, date: datetime) -> Dict:
        """
        Extract features for a specific ticker at a specific date
        
        Args:
            ticker: Ticker symbol or stock name
            date: Analysis date
            
        Returns:
            dict: Feature values
        """
        features = {}
        
        # Load UCS_LRS data
        ucs_data = self.load_ucs_data_for_date(date)
        
        # Try to find ticker in UCS data (may be by name or code)
        ticker_data = None
        if ticker in ucs_data:
            ticker_data = ucs_data[ticker]
        else:
            # Try to find by partial match
            for key in ucs_data.keys():
                if ticker in key or key in ticker:
                    ticker_data = ucs_data[key]
                    break
        
        if ticker_data:
            # Extract basic_info features
            if 'basic_info' in ticker_data:
                basic = ticker_data['basic_info']
                features['current_price'] = basic.get('current_price', np.nan)
                features['current_volume'] = basic.get('current_volume', np.nan)
                if 'total_days' in basic:
                    features['data_days'] = basic.get('total_days', np.nan)
            
            # Extract overall_assessment (score, score_percentage, rating)
            if 'overall_assessment' in ticker_data:
                assess = ticker_data['overall_assessment']
                features['assess_score'] = assess.get('score', np.nan)
                features['assess_score_pct'] = assess.get('score_percentage', np.nan)
                features['assess_max_score'] = assess.get('max_score', np.nan)
                # Rating as numeric (if available)
                rating = assess.get('rating', '')
                if rating:
                    rating_map = {'EXCELLENT': 5, 'GOOD': 4, 'FAIR': 3, 'POOR': 2, 'VERY_POOR': 1}
                    features['assess_rating'] = rating_map.get(rating.upper(), np.nan)
            
            # Extract daily_lrs features
            if 'daily_lrs' in ticker_data:
                lrs = ticker_data['daily_lrs']
                features['lrs_current'] = lrs.get('current_lrs', np.nan)
                features['lrs_slrs'] = lrs.get('current_slrs', np.nan)
                features['lrs_alrs'] = lrs.get('current_alrs', np.nan)
                features['lrs_100'] = lrs.get('lrs_100', np.nan)
                features['lrs_50'] = lrs.get('lrs_50', np.nan)
                features['lrs_5d_avg'] = lrs.get('lrs_5d_average', np.nan)
                features['lrs_20d_avg'] = lrs.get('lrs_20d_average', np.nan)
                features['lrs_signal_strength'] = lrs.get('signal_strength', np.nan)
                # Boolean features
                features['lrs_positive'] = 1 if lrs.get('lrs_positive', False) else 0
                features['slrs_positive'] = 1 if lrs.get('slrs_positive', False) else 0
                features['lrs_above_alrs'] = 1 if lrs.get('lrs_above_alrs', False) else 0
                features['alrs_slope_positive'] = 1 if lrs.get('alrs_slope_positive', False) else 0
                features['alrs_slope_5d_positive'] = 1 if lrs.get('alrs_slope_5d_positive', False) else 0
            
            # Extract daily_tstop_analysis features
            if 'daily_tstop_analysis' in ticker_data:
                tstop = ticker_data['daily_tstop_analysis']
                features['tstop_current_close'] = tstop.get('current_close', np.nan)
                features['tstop_current_filter'] = tstop.get('current_filter', np.nan)
                features['tstop_filter_margin'] = tstop.get('filter_margin', np.nan)
                features['tstop_periods_since_positive'] = tstop.get('periods_since_positive', np.nan)
                # Boolean features
                features['tstop_close_above_filter'] = 1 if tstop.get('close_above_filter', False) else 0
                features['tstop_turned_positive_recently'] = 1 if tstop.get('turned_positive_recently', False) else 0
            
            # Extract daily_macd_analysis features
            if 'daily_macd_analysis' in ticker_data:
                macd = ticker_data['daily_macd_analysis']
                features['macd_current_histogram'] = macd.get('current_histogram', np.nan)
                features['macd_periods_since_positive'] = macd.get('periods_since_positive', np.nan)
                # Boolean features
                features['macd_histogram_positive'] = 1 if macd.get('histogram_positive', False) else 0
                features['macd_histogram_increasing'] = 1 if macd.get('histogram_increasing', False) else 0
                features['macd_turned_positive_recently'] = 1 if macd.get('turned_positive_recently', False) else 0
            
            # Extract filter_status
            if 'filter_status' in ticker_data:
                filter_status = ticker_data['filter_status']
                features['filter_passes'] = 1 if filter_status.get('passes_filter', False) else 0
                if 'conditions' in filter_status:
                    features['filter_conditions_passed'] = len(filter_status.get('conditions', []))
                if 'failed_conditions' in filter_status:
                    features['filter_conditions_failed'] = len(filter_status.get('failed_conditions', []))
            
            # Extract economic_context features
            if 'economic_context' in ticker_data:
                econ = ticker_data['economic_context']
                if 'price_momentum' in econ:
                    features['econ_price_momentum'] = econ['price_momentum'].get('momentum', np.nan) if isinstance(econ['price_momentum'], dict) else np.nan
                if 'volatility' in econ:
                    vol = econ['volatility']
                    if isinstance(vol, dict):
                        features['econ_volatility'] = vol.get('volatility', np.nan)
            
            # Extract market_position features
            if 'market_position' in ticker_data:
                market = ticker_data['market_position']
                if 'price_levels' in market and isinstance(market['price_levels'], dict):
                    levels = market['price_levels']
                    features['market_price_vs_ma20'] = levels.get('price_vs_ma20', np.nan)
                    features['market_price_vs_ma50'] = levels.get('price_vs_ma50', np.nan)
                    features['market_price_vs_ma200'] = levels.get('price_vs_ma200', np.nan)
        
        return features
    
    def extract_theme_features(self, theme_name: str, theme_tickers: List[str], 
                              date: datetime, db_df: pd.DataFrame) -> Dict:
        """
        Extract theme-level aggregated features
        
        Args:
            theme_name: Name of the theme
            theme_tickers: List of tickers in the theme
            date: Analysis date
            db_df: Database DataFrame with ticker info
            
        Returns:
            dict: Theme-level feature values
        """
        features = {}
        
        # Get ticker features for all theme tickers
        ticker_features_list = []
        for ticker in theme_tickers[:50]:  # Limit to first 50 for performance
            ticker_feat = self.extract_ticker_features(ticker, date)
            if ticker_feat:
                ticker_features_list.append(ticker_feat)
        
        if len(ticker_features_list) > 0:
            # Aggregate ticker features to theme level
            ticker_df = pd.DataFrame(ticker_features_list)
            
            # Overall assessment features
            if 'assess_score' in ticker_df.columns:
                features['theme_assess_score_avg'] = ticker_df['assess_score'].mean()
                features['theme_assess_score_median'] = ticker_df['assess_score'].median()
                features['theme_assess_score_std'] = ticker_df['assess_score'].std()
                features['theme_assess_score_high'] = (ticker_df['assess_score'] > 70).sum() / len(ticker_df)
            
            if 'assess_score_pct' in ticker_df.columns:
                features['theme_assess_pct_avg'] = ticker_df['assess_score_pct'].mean()
                features['theme_assess_pct_high'] = (ticker_df['assess_score_pct'] > 70).sum() / len(ticker_df)
            
            # LRS features
            if 'lrs_current' in ticker_df.columns:
                features['theme_lrs_avg'] = ticker_df['lrs_current'].mean()
                features['theme_lrs_median'] = ticker_df['lrs_current'].median()
                features['theme_lrs_std'] = ticker_df['lrs_current'].std()
                features['theme_lrs_positive_ratio'] = ticker_df['lrs_positive'].mean() if 'lrs_positive' in ticker_df.columns else np.nan
            
            if 'lrs_signal_strength' in ticker_df.columns:
                features['theme_lrs_signal_avg'] = ticker_df['lrs_signal_strength'].mean()
                features['theme_lrs_signal_high'] = (ticker_df['lrs_signal_strength'] > 0.5).sum() / len(ticker_df)
            
            # TStop features
            if 'tstop_close_above_filter' in ticker_df.columns:
                features['theme_tstop_above_filter_ratio'] = ticker_df['tstop_close_above_filter'].mean()
            
            # MACD features
            if 'macd_histogram_positive' in ticker_df.columns:
                features['theme_macd_positive_ratio'] = ticker_df['macd_histogram_positive'].mean()
            
            # Filter features
            if 'filter_passes' in ticker_df.columns:
                features['theme_filter_pass_ratio'] = ticker_df['filter_passes'].mean()
            
            # Theme size
            features['theme_n_tickers'] = len(theme_tickers)
            features['theme_n_tickers_with_ucs'] = len(ticker_features_list)
            features['theme_ucs_coverage'] = len(ticker_features_list) / len(theme_tickers) if len(theme_tickers) > 0 else 0
        
        return features
    
    def extract_signal_features(self, signal: Dict) -> Dict:
        """
        Extract features from signal data
        
        Args:
            signal: Signal dictionary from SignalCalculator
            
        Returns:
            dict: Signal features
        """
        features = {}
        
        # Signal type (one-hot encoded)
        signal_type = signal.get('signal_type', '')
        features['signal_type_tier'] = 1 if 'tier' in signal_type else 0
        features['signal_type_cohesion'] = 1 if 'cohesion' in signal_type else 0
        features['signal_type_leadership'] = 1 if 'leadership' in signal_type else 0
        features['signal_type_combined'] = 1 if '+' in signal_type else 0
        
        # Signal strength
        features['signal_strength'] = signal.get('signal_strength', 0)
        
        # Tier
        features['tier'] = signal.get('tier', np.nan)
        features['is_tier1'] = 1 if signal.get('tier') == 1 else 0
        features['is_tier2'] = 1 if signal.get('tier') == 2 else 0
        
        # Fiedler features
        features['current_fiedler'] = signal.get('current_fiedler', np.nan)
        features['week_before_fiedler'] = signal.get('week_before_fiedler', np.nan)
        features['fiedler_change'] = signal.get('change', np.nan)
        features['fiedler_pct_change'] = signal.get('pct_change', np.nan)
        
        # Leadership gap
        features['leadership_gap'] = signal.get('leadership_gap', np.nan)
        
        return features
    
    def extract_time_features(self, date: datetime) -> Dict:
        """
        Extract time-based features
        
        Args:
            date: Analysis date
            
        Returns:
            dict: Time features
        """
        features = {}
        
        features['day_of_week'] = date.weekday()  # 0=Monday, 6=Sunday
        features['day_of_month'] = date.day
        features['month'] = date.month
        features['quarter'] = (date.month - 1) // 3 + 1
        features['is_month_end'] = 1 if date.day >= 25 else 0
        features['is_quarter_end'] = 1 if date.month in [3, 6, 9, 12] and date.day >= 25 else 0
        
        return features
    
    def extract_all_features(self, signal: Dict, theme_name: str, theme_tickers: List[str],
                            signal_date: datetime, regime_data: Optional[pd.DataFrame] = None,
                            db_df: Optional[pd.DataFrame] = None) -> Dict:
        """
        Extract all features for a signal
        
        Args:
            signal: Signal dictionary
            theme_name: Theme name
            theme_tickers: List of tickers in theme
            signal_date: Date of signal
            regime_data: Regime DataFrame (optional)
            db_df: Database DataFrame (optional)
            
        Returns:
            dict: All features combined
        """
        all_features = {}
        
        # Signal features
        signal_features = self.extract_signal_features(signal)
        all_features.update(signal_features)
        
        # Time features
        time_features = self.extract_time_features(signal_date)
        all_features.update(time_features)
        
        # Theme features from UCS_LRS
        if db_df is not None:
            theme_features = self.extract_theme_features(theme_name, theme_tickers, signal_date, db_df)
            all_features.update(theme_features)
        
        # Regime features (if available)
        if regime_data is not None and len(regime_data) > 0:
            # Aggregate regime data for theme tickers
            # (This would need ticker-to-name mapping)
            pass
        
        return all_features

if __name__ == "__main__":
    # Test feature engineering
    print("="*80)
    print("Testing Feature Engineering")
    print("="*80)
    
    engineer = FeatureEngineer()
    
    # Test date
    test_date = pd.to_datetime('2025-08-01')
    
    # Test ticker features
    print("\nTesting ticker feature extraction...")
    ticker_features = engineer.extract_ticker_features('삼성전자', test_date)
    print(f"Extracted {len(ticker_features)} features")
    print(f"Sample features: {list(ticker_features.keys())[:10]}")
    
    # Test signal features
    print("\nTesting signal feature extraction...")
    sample_signal = {
        'signal_type': 'tier+cohesion',
        'signal_strength': 2.5,
        'tier': 1,
        'current_fiedler': 3.5,
        'week_before_fiedler': 2.0,
        'change': 1.5,
        'pct_change': 75.0
    }
    signal_features = engineer.extract_signal_features(sample_signal)
    print(f"Signal features: {signal_features}")
    
    # Test time features
    print("\nTesting time feature extraction...")
    time_features = engineer.extract_time_features(test_date)
    print(f"Time features: {time_features}")

