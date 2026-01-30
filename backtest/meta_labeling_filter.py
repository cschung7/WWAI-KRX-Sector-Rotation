#!/usr/bin/env python3
"""
Meta-Labeling Filter for Production

Applies trained meta-labeler to filter investment signals in production.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import sys

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from meta_labeler import MetaLabeler
from feature_engineering import FeatureEngineer
from data_loader import DataLoader
from config import DB_FILE

class MetaLabelingFilter:
    """Production filter for applying meta-labeling to signals"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Args:
            model_path: Path to trained meta-labeler model. If None, tries to find latest.
        """
        self.model_path = model_path
        self.meta_labeler = None
        self.feature_engineer = FeatureEngineer()
        self.theme_mapping = None
        self.db_df = None
        
        # Load model
        if model_path:
            self.load_model(model_path)
        else:
            self.load_latest_model()
        
        # Load supporting data
        self._load_supporting_data()
    
    def load_model(self, model_path: str):
        """Load meta-labeler model"""
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.meta_labeler = MetaLabeler()
        self.meta_labeler.load(model_path)
        self.model_path = model_path
        print(f"Meta-labeler loaded from {model_path}")
    
    def load_latest_model(self):
        """Load latest meta-labeler model from models directory"""
        models_dir = backtest_dir / "models"
        if not models_dir.exists():
            raise FileNotFoundError(f"Models directory not found: {models_dir}")
        
        # Find latest model
        model_files = list(models_dir.glob("meta_labeler_*.pkl"))
        if not model_files:
            raise FileNotFoundError(f"No meta-labeler models found in {models_dir}")
        
        latest_model = sorted(model_files, key=lambda x: x.stat().st_mtime)[-1]
        self.load_model(latest_model)
    
    def _load_supporting_data(self):
        """Load theme mapping and database"""
        loader = DataLoader()
        self.theme_mapping = loader.load_theme_mapping()
        
        if DB_FILE.exists():
            self.db_df = pd.read_csv(DB_FILE)
        else:
            print(f"Warning: Database file not found: {DB_FILE}")
    
    def filter_signals(self, signals: List[Dict], signal_date: datetime, 
                      use_basic_features: bool = True) -> List[Dict]:
        """
        Filter signals using meta-labeler
        
        Args:
            signals: List of signal dictionaries
            signal_date: Date of signals
            use_basic_features: If True, use only basic features (faster, no UCS_LRS)
            
        Returns:
            Filtered list of signals (only those predicted as "take trade")
        """
        if self.meta_labeler is None:
            raise ValueError("Meta-labeler not loaded. Call load_model() first.")
        
        if len(signals) == 0:
            return []
        
        # Extract features for all signals
        features_list = []
        valid_signals = []
        
        for signal in signals:
            theme = signal.get('theme', '')
            theme_tickers = self.theme_mapping.get(theme, []) if self.theme_mapping else []
            
            try:
                if use_basic_features:
                    # Extract only basic features (faster)
                    basic_features = self.feature_engineer.extract_signal_features(signal)
                    time_features = self.feature_engineer.extract_time_features(signal_date)
                    all_features = {**basic_features, **time_features}
                else:
                    # Extract all features including UCS_LRS
                    all_features = self.feature_engineer.extract_all_features(
                        signal,
                        theme,
                        theme_tickers,
                        signal_date,
                        db_df=self.db_df
                    )
                
                features_list.append(all_features)
                valid_signals.append(signal)
            except Exception as e:
                # Skip signals where feature extraction fails
                continue
        
        if len(features_list) == 0:
            print("Warning: No features extracted, returning all signals")
            return signals
        
        # Predict which signals to take
        features_df = pd.DataFrame(features_list)
        predictions = self.meta_labeler.predict(features_df)
        
        # Filter signals based on predictions
        filtered_signals = [sig for sig, pred in zip(valid_signals, predictions) if pred == 1]
        
        if len(filtered_signals) < len(signals):
            reduction_pct = (1 - len(filtered_signals) / len(signals)) * 100
            print(f"Meta-labeler filtered {len(signals)} -> {len(filtered_signals)} signals ({reduction_pct:.1f}% reduction)")
        
        return filtered_signals
    
    def filter_dataframe(self, signals_df: pd.DataFrame, date_col: str = 'date',
                        use_basic_features: bool = True) -> pd.DataFrame:
        """
        Filter signals DataFrame using meta-labeler
        
        Args:
            signals_df: DataFrame with signals
            date_col: Name of date column
            use_basic_features: If True, use only basic features
            
        Returns:
            Filtered DataFrame
        """
        if self.meta_labeler is None:
            raise ValueError("Meta-labeler not loaded. Call load_model() first.")
        
        if len(signals_df) == 0:
            return signals_df
        
        # Convert to list of signal dicts
        signals = signals_df.to_dict('records')
        
        # Get signal date (use first signal's date)
        if date_col in signals_df.columns:
            signal_date = pd.to_datetime(signals_df[date_col].iloc[0])
        else:
            signal_date = datetime.now()
        
        # Filter signals
        filtered_signals = self.filter_signals(signals, signal_date, use_basic_features)
        
        # Convert back to DataFrame
        if len(filtered_signals) > 0:
            filtered_df = pd.DataFrame(filtered_signals)
            return filtered_df
        else:
            return pd.DataFrame(columns=signals_df.columns)

def apply_meta_labeling_to_portfolio(portfolio_file: str, output_file: str = None,
                                     model_path: str = None, use_basic_features: bool = True):
    """
    Apply meta-labeling filter to a portfolio report
    
    Args:
        portfolio_file: Path to portfolio markdown file
        output_file: Path to output file (default: adds _filtered suffix)
        model_path: Path to meta-labeler model (default: latest)
        use_basic_features: Use only basic features (faster)
    """
    portfolio_file = Path(portfolio_file)
    if not portfolio_file.exists():
        raise FileNotFoundError(f"Portfolio file not found: {portfolio_file}")
    
    # Initialize filter
    filter_obj = MetaLabelingFilter(model_path=model_path)
    
    # Parse portfolio file (this would need to be implemented based on format)
    # For now, this is a placeholder
    print(f"Applying meta-labeling to {portfolio_file}...")
    print("Note: Portfolio file parsing needs to be implemented based on format")
    
    if output_file is None:
        output_file = portfolio_file.parent / f"{portfolio_file.stem}_filtered{portfolio_file.suffix}"
    
    print(f"Filtered portfolio would be saved to {output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply meta-labeling filter to signals')
    parser.add_argument('--model', type=str, default=None,
                       help='Path to meta-labeler model (default: latest)')
    parser.add_argument('--test', action='store_true',
                       help='Run test with sample signals')
    
    args = parser.parse_args()
    
    if args.test:
        # Test the filter
        print("Testing meta-labeling filter...")
        filter_obj = MetaLabelingFilter(model_path=args.model)
        
        # Create sample signals
        sample_signals = [
            {
                'theme': '반도체',
                'signal_type': 'tier',
                'signal_strength': 2.5,
                'tier': 1,
                'current_fiedler': 3.5,
                'week_before_fiedler': 2.0,
                'change': 1.5,
                'pct_change': 75.0
            },
            {
                'theme': '2차전지',
                'signal_type': 'cohesion',
                'signal_strength': 1.8,
                'tier': None,
                'current_fiedler': 2.5,
                'week_before_fiedler': 1.0,
                'change': 1.5,
                'pct_change': 150.0
            }
        ]
        
        filtered = filter_obj.filter_signals(sample_signals, datetime.now())
        print(f"\nFiltered {len(sample_signals)} -> {len(filtered)} signals")
        print("Test complete!")

