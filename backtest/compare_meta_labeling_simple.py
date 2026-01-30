#!/usr/bin/env python3
"""
Simple Comparison: Apply Meta-Labeling to Existing Results

Instead of re-running backtest, applies meta-labeling filter to existing results
and compares filtered vs unfiltered performance.
"""

import argparse
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

from meta_labeler import MetaLabeler
from feature_engineering import FeatureEngineer
from statistical_analysis import StatisticalAnalyzer

def main():
    parser = argparse.ArgumentParser(description='Compare performance with vs without meta-labeling on existing results')
    parser.add_argument('--results-file', type=str, required=True,
                       help='Path to backtest results CSV file')
    parser.add_argument('--meta-labeler', type=str, required=True,
                       help='Path to trained meta-labeler model')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: backtest/comparisons)')
    
    args = parser.parse_args()
    
    # Output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = backtest_dir / "comparisons"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("COMPARE: Baseline vs Meta-Labeling (Simple)")
    print("="*80)
    print(f"Results file: {args.results_file}")
    print(f"Meta-labeler: {args.meta_labeler}")
    print("="*80)
    
    # Load results
    print("\nLoading backtest results...")
    results_df = pd.read_csv(args.results_file)
    
    # Check date column
    date_col = 'date' if 'date' in results_df.columns else 'signal_date'
    if date_col in results_df.columns:
        results_df[date_col] = pd.to_datetime(results_df[date_col])
        results_df['date'] = results_df[date_col]
    
    print(f"  Loaded {len(results_df)} signals")
    print(f"  Date range: {results_df['date'].min()} to {results_df['date'].max()}")
    
    # Calculate baseline metrics
    print("\nCalculating baseline metrics...")
    baseline_analyzer = StatisticalAnalyzer(results_df)
    baseline_metrics = baseline_analyzer.calculate_performance_metrics()
    
    print(f"  Baseline Win Rate: {baseline_metrics.get('win_rate', 0)*100:.1f}%")
    print(f"  Baseline Avg Return: {baseline_metrics.get('avg_return', 0):.2f}%")
    print(f"  Baseline Sharpe: {baseline_metrics.get('sharpe_ratio', 0):.2f}")
    
    # Load meta-labeler
    print("\nLoading meta-labeler...")
    meta_labeler = MetaLabeler()
    meta_labeler.load(Path(args.meta_labeler))
    print("  Meta-labeler loaded")
    
    # Load theme mapping and database for feature extraction
    print("\nLoading theme mapping and database...")
    from data_loader import DataLoader
    from config import DB_FILE
    
    loader = DataLoader()
    theme_mapping = loader.load_theme_mapping()
    
    db_df = None
    if DB_FILE.exists():
        db_df = pd.read_csv(DB_FILE)
        print(f"  Loaded {len(db_df)} stocks")
    
    # Extract features and apply meta-labeling
    print("\nExtracting features and applying meta-labeling filter...")
    feature_engineer = FeatureEngineer()
    
    features_list = []
    valid_indices = []
    
    # Process in batches
    batch_size = 1000
    total = len(results_df)
    
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch_df = results_df.iloc[batch_start:batch_end]
        
        if (batch_start // batch_size + 1) % 5 == 0:
            print(f"  Progress: {batch_start}/{total} signals processed...")
        
        for idx, row in batch_df.iterrows():
            theme = row['theme']
            signal_date = pd.to_datetime(row['date'])
            signal_dict = row.to_dict()
            
            # Get theme tickers
            theme_tickers = theme_mapping.get(theme, [])
            
            # Extract features (basic only for speed)
            try:
                basic_features = feature_engineer.extract_signal_features(signal_dict)
                time_features = feature_engineer.extract_time_features(signal_date)
                all_features = {**basic_features, **time_features}
                features_list.append(all_features)
                valid_indices.append(idx)
            except Exception as e:
                continue
    
    if len(features_list) == 0:
        print("Error: No features extracted!")
        return 1
    
    print(f"  Extracted features for {len(features_list)} signals")
    
    # Apply meta-labeling
    features_df = pd.DataFrame(features_list)
    predictions = meta_labeler.predict(features_df)
    
    # Filter results based on predictions
    filtered_indices = [idx for idx, pred in zip(valid_indices, predictions) if pred == 1]
    filtered_df = results_df.loc[filtered_indices].copy()
    
    print(f"  Meta-labeler kept {len(filtered_df)}/{len(results_df)} signals ({len(filtered_df)/len(results_df)*100:.1f}%)")
    
    # Calculate filtered metrics
    print("\nCalculating filtered metrics...")
    filtered_analyzer = StatisticalAnalyzer(filtered_df)
    filtered_metrics = filtered_analyzer.calculate_performance_metrics()
    
    print(f"  Filtered Win Rate: {filtered_metrics.get('win_rate', 0)*100:.1f}%")
    print(f"  Filtered Avg Return: {filtered_metrics.get('avg_return', 0):.2f}%")
    print(f"  Filtered Sharpe: {filtered_metrics.get('sharpe_ratio', 0):.2f}")
    
    # Compare
    print("\n" + "="*80)
    print("COMPARISON: Baseline vs Meta-Labeling")
    print("="*80)
    
    print(f"\n{'Metric':<30} {'Baseline':<20} {'Meta-Labeling':<20} {'Change':<15}")
    print("-" * 85)
    
    metrics_to_compare = [
        ('Total Signals', 'n_signals', int),
        ('Win Rate', 'win_rate', lambda x: f"{x*100:.1f}%"),
        ('Average Return', 'avg_return', lambda x: f"{x:.2f}%"),
        ('Median Return', 'median_return', lambda x: f"{x:.2f}%"),
        ('Sharpe Ratio', 'sharpe_ratio', lambda x: f"{x:.2f}"),
        ('Max Drawdown', 'max_drawdown', lambda x: f"{x:.2f}%"),
    ]
    
    comparison_data = []
    
    for label, key, formatter in metrics_to_compare:
        baseline_val = baseline_metrics.get(key, 0)
        filtered_val = filtered_metrics.get(key, 0)
        
        if isinstance(formatter, type) and formatter == int:
            change = filtered_val - baseline_val
            change_pct = (change / baseline_val * 100) if baseline_val > 0 else 0
            change_str = f"{change:+d} ({change_pct:+.1f}%)"
        else:
            change = filtered_val - baseline_val
            if isinstance(baseline_val, (int, float)) and baseline_val != 0:
                change_pct = (change / abs(baseline_val) * 100)
                change_str = f"{change:+.2f} ({change_pct:+.1f}%)"
            else:
                change_str = f"{change:+.2f}"
        
        baseline_str = formatter(baseline_val) if callable(formatter) else str(baseline_val)
        filtered_str = formatter(filtered_val) if callable(formatter) else str(filtered_val)
        
        print(f"{label:<30} {baseline_str:<20} {filtered_str:<20} {change_str:<15}")
        
        comparison_data.append({
            'metric': label,
            'baseline': baseline_val,
            'meta_labeling': filtered_val,
            'change': change,
            'change_pct': change_pct if isinstance(baseline_val, (int, float)) and baseline_val != 0 else 0
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    signal_reduction = (1 - filtered_metrics.get('n_signals', 0) / baseline_metrics.get('n_signals', 1)) * 100
    win_rate_improvement = (filtered_metrics.get('win_rate', 0) - baseline_metrics.get('win_rate', 0)) * 100
    sharpe_improvement = filtered_metrics.get('sharpe_ratio', 0) - baseline_metrics.get('sharpe_ratio', 0)
    avg_return_change = filtered_metrics.get('avg_return', 0) - baseline_metrics.get('avg_return', 0)
    
    print(f"\n📊 Signal Reduction: {signal_reduction:.1f}%")
    print(f"📈 Win Rate Improvement: {win_rate_improvement:+.1f} percentage points")
    print(f"📈 Average Return Change: {avg_return_change:+.2f}%")
    print(f"📈 Sharpe Ratio Improvement: {sharpe_improvement:+.2f}")
    
    if win_rate_improvement > 5 and sharpe_improvement > 0.1:
        print("\n🎉 Meta-labeling shows SIGNIFICANT improvement!")
    elif win_rate_improvement > 0 and sharpe_improvement > 0:
        print("\n✅ Meta-labeling shows improvement")
    elif win_rate_improvement > 0:
        print("\n✅ Meta-labeling improves win rate")
    else:
        print("\n⚠️  Meta-labeling does not show clear improvement in this test")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_file = output_dir / f"comparison_simple_{timestamp}.csv"
    comparison_df.to_csv(comparison_file, index=False)
    
    filtered_file = output_dir / f"filtered_results_{timestamp}.csv"
    filtered_df.to_csv(filtered_file, index=False)
    
    print(f"\nComparison saved to {comparison_file}")
    print(f"Filtered results saved to {filtered_file}")
    
    return 0

if __name__ == "__main__":
    exit(main())

