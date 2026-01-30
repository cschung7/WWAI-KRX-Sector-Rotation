#!/usr/bin/env python3
"""
Train Meta-Labeler

Trains a meta-labeler on historical backtest results to filter trading signals.
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, DB_FILE

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from meta_labeler import MetaLabeler
from data_loader import DataLoader
from feature_engineering import FeatureEngineer

def load_backtest_results(results_file: Path) -> pd.DataFrame:
    """Load historical backtest results"""
    print(f"Loading backtest results from {results_file}...")
    df = pd.read_csv(results_file)
    
    # Check for date column (could be 'date' or 'signal_date')
    date_col = None
    if 'date' in df.columns:
        date_col = 'date'
    elif 'signal_date' in df.columns:
        date_col = 'signal_date'
    else:
        raise ValueError(f"No date column found. Available columns: {list(df.columns)}")
    
    # Ensure date column is datetime
    df[date_col] = pd.to_datetime(df[date_col])
    
    # Rename to 'date' for consistency
    if date_col != 'date':
        df['date'] = df[date_col]
    
    print(f"  Loaded {len(df)} signals")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    if 'total_return' in df.columns:
        print(f"  Positive returns: {(df['total_return'] > 0).sum()} ({(df['total_return'] > 0).mean()*100:.1f}%)")
    
    return df

def prepare_labels(signals_df: pd.DataFrame, threshold: float = 0.0) -> pd.Series:
    """
    Prepare binary labels for meta-labeling
    
    Args:
        signals_df: DataFrame with 'total_return' column
        threshold: Minimum return to consider as positive (default: 0.0)
        
    Returns:
        Series with binary labels (1 = take trade, 0 = skip)
    """
    labels = (signals_df['total_return'] > threshold).astype(int)
    return labels

def main():
    parser = argparse.ArgumentParser(description='Train meta-labeler on historical backtest results')
    parser.add_argument('--results-file', type=str, required=True,
                       help='Path to backtest results CSV file (signal_performance_*.csv)')
    parser.add_argument('--model-type', type=str, default='xgboost',
                       choices=['xgboost', 'random_forest'],
                       help='Model type (default: xgboost)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory for trained model (default: backtest/models)')
    parser.add_argument('--return-threshold', type=float, default=0.0,
                       help='Minimum return to consider as positive label (default: 0.0)')
    parser.add_argument('--use-cv', action='store_true',
                       help='Use cross-validation during training')
    parser.add_argument('--sample-size', type=int, default=None,
                       help='Use a random sample of signals for training (for testing)')
    parser.add_argument('--skip-ucs', action='store_true',
                       help='Skip UCS_LRS feature extraction (faster, less features)')
    
    args = parser.parse_args()
    
    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = backtest_dir / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("TRAIN META-LABELER")
    print("="*80)
    print(f"Results file: {args.results_file}")
    print(f"Model type: {args.model_type}")
    print(f"Return threshold: {args.return_threshold}")
    print(f"Output directory: {output_dir}")
    print("="*80)
    
    # Load backtest results
    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"Error: Results file not found: {results_file}")
        return 1
    
    signals_df = load_backtest_results(results_file)
    
    # Sample if requested
    if args.sample_size and args.sample_size < len(signals_df):
        print(f"\nSampling {args.sample_size} signals from {len(signals_df)} total...")
        signals_df = signals_df.sample(n=args.sample_size, random_state=42).reset_index(drop=True)
        print(f"  Using {len(signals_df)} signals for training")
    
    # Prepare labels
    print("\nPreparing labels...")
    labels = prepare_labels(signals_df, threshold=args.return_threshold)
    print(f"  Positive labels (take trade): {labels.sum()} ({labels.mean()*100:.1f}%)")
    print(f"  Negative labels (skip trade): {(~labels.astype(bool)).sum()} ({(1-labels.mean())*100:.1f}%)")
    
    # Load theme mapping and database
    print("\nLoading theme mapping and database...")
    loader = DataLoader()
    theme_mapping = loader.load_theme_mapping()
    
    # Load database for ticker-to-name mapping
    db_df = None
    if DB_FILE.exists():
        print(f"  Loading database from {DB_FILE}...")
        db_df = pd.read_csv(DB_FILE)
        print(f"  Loaded {len(db_df)} stocks")
    else:
        print(f"  Warning: Database file not found: {DB_FILE}")
    
    # Prepare features
    print("\nPreparing features...")
    feature_engineer = FeatureEngineer()
    
    # Extract features for all signals (in batches to manage memory)
    features_list = []
    dates_list = []
    valid_indices = []
    
    batch_size = 1000
    total_signals = len(signals_df)
    
    print(f"  Processing {total_signals} signals in batches of {batch_size}...")
    
    for batch_start in range(0, total_signals, batch_size):
        batch_end = min(batch_start + batch_size, total_signals)
        batch_df = signals_df.iloc[batch_start:batch_end]
        
        if (batch_start // batch_size + 1) % 5 == 0:
            print(f"    Progress: {batch_start}/{total_signals} signals processed...")
        
        for idx, row in batch_df.iterrows():
            theme = row['theme']
            signal_date = pd.to_datetime(row['date'])
            signal_dict = row.to_dict()
            
            # Get theme tickers
            theme_tickers = theme_mapping.get(theme, [])
            
            # Extract all features
            try:
                if args.skip_ucs:
                    # Extract only basic features (signal + time, no UCS_LRS)
                    basic_features = feature_engineer.extract_signal_features(signal_dict)
                    time_features = feature_engineer.extract_time_features(signal_date)
                    all_features = {**basic_features, **time_features}
                else:
                    all_features = feature_engineer.extract_all_features(
                        signal_dict,
                        theme,
                        theme_tickers,
                        signal_date,
                        db_df=db_df
                    )
                features_list.append(all_features)
                dates_list.append(signal_date)
                valid_indices.append(idx)
            except Exception as e:
                # Only print first few errors to avoid spam
                if len(features_list) < 10:
                    print(f"  Warning: Failed to extract features for {theme} on {signal_date}: {e}")
                continue
    
    if len(features_list) == 0:
        print("Error: No features extracted!")
        return 1
    
    print(f"  Successfully extracted features for {len(features_list)}/{total_signals} signals")
    
    features_df = pd.DataFrame(features_list)
    dates_series = pd.Series(dates_list, index=valid_indices)
    
    # Align labels with features (using valid_indices)
    labels_aligned = labels.loc[valid_indices].reset_index(drop=True)
    features_df = features_df.reset_index(drop=True)
    dates_series = dates_series.reset_index(drop=True)
    
    print(f"\nFeature extraction complete:")
    print(f"  Samples: {len(features_df)}")
    print(f"  Features: {len(features_df.columns)}")
    print(f"  Feature names: {list(features_df.columns)[:10]}...")
    
    # Train meta-labeler
    print("\n" + "="*80)
    meta_labeler = MetaLabeler(model_type=args.model_type)
    
    metrics = meta_labeler.train(
        features_df=features_df,
        labels=labels_aligned,
        dates=dates_series,
        use_cv=args.use_cv
    )
    
    # Save model
    model_file = output_dir / f"meta_labeler_{args.model_type}_{datetime.now().strftime('%Y%m%d')}"
    meta_labeler.save(model_file)
    
    # Save training summary
    summary = {
        'training_date': datetime.now().isoformat(),
        'results_file': str(results_file),
        'model_type': args.model_type,
        'return_threshold': args.return_threshold,
        'n_samples': len(features_df),
        'n_features': len(features_df.columns),
        'positive_labels': int(labels_aligned.sum()),
        'negative_labels': int((~labels_aligned.astype(bool)).sum()),
        'metrics': metrics
    }
    
    summary_file = output_dir / f"training_summary_{datetime.now().strftime('%Y%m%d')}.json"
    import json
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nTraining summary saved to {summary_file}")
    print("\n" + "="*80)
    print("TRAINING COMPLETE")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    exit(main())

