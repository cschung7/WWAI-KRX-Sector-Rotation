#!/usr/bin/env python3
"""
Visualization Module for Backtesting

Generates charts and plots for backtest results
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from pathlib import Path
from typing import Dict, Optional

def setup_korean_font():
    """Setup Korean font for matplotlib"""
    korean_font_obj = None
    
    # Search for NanumGothic (preferred)
    for font_obj in fm.fontManager.ttflist:
        font_lower = font_obj.name.lower()
        if 'nanum' in font_lower and 'gothic' in font_lower and 'coding' not in font_lower:
            korean_font_obj = font_obj
            break
    
    if not korean_font_obj:
        for font_obj in fm.fontManager.ttflist:
            font_lower = font_obj.name.lower()
            if 'nanum' in font_lower:
                korean_font_obj = font_obj
                break
    
    if korean_font_obj:
        prop = fm.FontProperties(fname=korean_font_obj.fname)
        plt.rcParams['font.family'] = korean_font_obj.name
        plt.rcParams['font.sans-serif'] = [korean_font_obj.name] + plt.rcParams['font.sans-serif']
        return prop
    else:
        plt.rcParams['font.family'] = 'DejaVu Sans'
        return None

KOREAN_FONT_PROP = setup_korean_font()
plt.rcParams['axes.unicode_minus'] = False

def plot_signal_vs_return_scatter(results_df: pd.DataFrame, output_file: Path):
    """Plot signal strength vs return scatter plot"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Overall scatter
    ax = axes[0]
    if 'signal_strength' in results_df.columns and 'total_return' in results_df.columns:
        ax.scatter(results_df['signal_strength'], results_df['total_return'], alpha=0.5, s=20)
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        ax.axvline(x=0, color='r', linestyle='--', alpha=0.5)
        
        if KOREAN_FONT_PROP:
            ax.set_xlabel('Signal Strength', fontproperties=KOREAN_FONT_PROP)
            ax.set_ylabel('Total Return (%)', fontproperties=KOREAN_FONT_PROP)
            ax.set_title('Signal Strength vs Return', fontproperties=KOREAN_FONT_PROP)
        else:
            ax.set_xlabel('Signal Strength')
            ax.set_ylabel('Total Return (%)')
            ax.set_title('Signal Strength vs Return')
    
    # By signal type
    ax = axes[1]
    if 'signal_type' in results_df.columns:
        for signal_type in results_df['signal_type'].unique():
            type_data = results_df[results_df['signal_type'] == signal_type]
            if 'signal_strength' in type_data.columns and 'total_return' in type_data.columns:
                ax.scatter(type_data['signal_strength'], type_data['total_return'],
                          label=signal_type, alpha=0.5, s=20)
        
        ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
        if KOREAN_FONT_PROP:
            ax.set_xlabel('Signal Strength', fontproperties=KOREAN_FONT_PROP)
            ax.set_ylabel('Total Return (%)', fontproperties=KOREAN_FONT_PROP)
            ax.set_title('Signal Strength vs Return by Type', fontproperties=KOREAN_FONT_PROP)
            ax.legend(prop=KOREAN_FONT_PROP)
        else:
            ax.set_xlabel('Signal Strength')
            ax.set_ylabel('Total Return (%)')
            ax.set_title('Signal Strength vs Return by Type')
            ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_file}")

def plot_cumulative_returns(results_df: pd.DataFrame, output_file: Path):
    """Plot cumulative returns by signal type"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    if 'signal_type' in results_df.columns and 'total_return' in results_df.columns:
        for signal_type in results_df['signal_type'].unique():
            type_data = results_df[results_df['signal_type'] == signal_type]
            returns = type_data['total_return'].values
            cumulative = (1 + returns / 100).cumprod()
            
            ax.plot(range(len(cumulative)), cumulative, label=signal_type, linewidth=2)
        
        ax.axhline(y=1.0, color='r', linestyle='--', alpha=0.5, label='Break-even')
        
        if KOREAN_FONT_PROP:
            ax.set_xlabel('Signal Number', fontproperties=KOREAN_FONT_PROP)
            ax.set_ylabel('Cumulative Return', fontproperties=KOREAN_FONT_PROP)
            ax.set_title('Cumulative Returns by Signal Type', fontproperties=KOREAN_FONT_PROP)
            ax.legend(prop=KOREAN_FONT_PROP)
        else:
            ax.set_xlabel('Signal Number')
            ax.set_ylabel('Cumulative Return')
            ax.set_title('Cumulative Returns by Signal Type')
            ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_file}")

def plot_win_rate_by_strength(results_df: pd.DataFrame, output_file: Path):
    """Plot win rate by signal strength"""
    if 'signal_strength' not in results_df.columns:
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bins
    results_df['strength_bin'] = pd.cut(
        results_df['signal_strength'],
        bins=5,
        labels=['Very Low', 'Low', 'Medium', 'High', 'Very High']
    )
    
    win_rates = []
    bin_labels = []
    
    for bin_label in results_df['strength_bin'].cat.categories:
        bin_data = results_df[results_df['strength_bin'] == bin_label]
        if len(bin_data) > 0:
            win_rate = (bin_data['total_return'] > 0).mean() * 100
            win_rates.append(win_rate)
            bin_labels.append(bin_label)
    
    ax.bar(bin_labels, win_rates, color='steelblue', alpha=0.7)
    ax.axhline(y=50, color='r', linestyle='--', alpha=0.5, label='50% (Random)')
    
    if KOREAN_FONT_PROP:
        ax.set_xlabel('Signal Strength', fontproperties=KOREAN_FONT_PROP)
        ax.set_ylabel('Win Rate (%)', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Win Rate by Signal Strength', fontproperties=KOREAN_FONT_PROP)
        ax.legend(prop=KOREAN_FONT_PROP)
    else:
        ax.set_xlabel('Signal Strength')
        ax.set_ylabel('Win Rate (%)')
        ax.set_title('Win Rate by Signal Strength')
        ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_file}")

def plot_time_decay(results_df: pd.DataFrame, output_file: Path):
    """Plot returns over time (1w, 2w, 4w, 8w, 12w)"""
    time_periods = ['1w', '2w', '4w', '8w', '12w']
    period_cols = [f'return_{p}' for p in time_periods]
    
    available_cols = [col for col in period_cols if col in results_df.columns]
    if not available_cols:
        return
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    avg_returns = []
    win_rates = []
    period_labels = []
    
    for col in available_cols:
        period_data = results_df[col].dropna()
        if len(period_data) > 0:
            avg_returns.append(period_data.mean())
            win_rates.append((period_data > 0).mean() * 100)
            period_labels.append(col.replace('return_', ''))
    
    x = np.arange(len(period_labels))
    width = 0.35
    
    ax2 = ax.twinx()
    bars1 = ax.bar(x - width/2, avg_returns, width, label='Avg Return (%)', color='steelblue', alpha=0.7)
    bars2 = ax2.bar(x + width/2, win_rates, width, label='Win Rate (%)', color='orange', alpha=0.7)
    
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    ax2.axhline(y=50, color='r', linestyle='--', alpha=0.5)
    
    if KOREAN_FONT_PROP:
        ax.set_xlabel('Holding Period', fontproperties=KOREAN_FONT_PROP)
        ax.set_ylabel('Average Return (%)', color='steelblue', fontproperties=KOREAN_FONT_PROP)
        ax2.set_ylabel('Win Rate (%)', color='orange', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Return Time Decay Analysis', fontproperties=KOREAN_FONT_PROP)
        ax.legend(loc='upper left', prop=KOREAN_FONT_PROP)
        ax2.legend(loc='upper right', prop=KOREAN_FONT_PROP)
    else:
        ax.set_xlabel('Holding Period')
        ax.set_ylabel('Average Return (%)', color='steelblue')
        ax2.set_ylabel('Win Rate (%)', color='orange')
        ax.set_title('Return Time Decay Analysis')
        ax.legend(loc='upper left')
        ax2.legend(loc='upper right')
    
    ax.set_xticks(x)
    ax.set_xticklabels(period_labels)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_file}")

def plot_performance_by_signal_type(results_df: pd.DataFrame, output_file: Path):
    """Plot performance metrics by signal type"""
    if 'signal_type' not in results_df.columns:
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    signal_types = results_df['signal_type'].unique()
    
    # Win rate
    ax = axes[0, 0]
    win_rates = [(results_df[results_df['signal_type'] == st]['total_return'] > 0).mean() * 100
                 for st in signal_types]
    ax.bar(signal_types, win_rates, color='steelblue', alpha=0.7)
    ax.axhline(y=50, color='r', linestyle='--', alpha=0.5)
    if KOREAN_FONT_PROP:
        ax.set_ylabel('Win Rate (%)', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Win Rate by Signal Type', fontproperties=KOREAN_FONT_PROP)
    else:
        ax.set_ylabel('Win Rate (%)')
        ax.set_title('Win Rate by Signal Type')
    
    # Average return
    ax = axes[0, 1]
    avg_returns = [results_df[results_df['signal_type'] == st]['total_return'].mean()
                   for st in signal_types]
    ax.bar(signal_types, avg_returns, color='green', alpha=0.7)
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    if KOREAN_FONT_PROP:
        ax.set_ylabel('Average Return (%)', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Average Return by Signal Type', fontproperties=KOREAN_FONT_PROP)
    else:
        ax.set_ylabel('Average Return (%)')
        ax.set_title('Average Return by Signal Type')
    
    # Return distribution
    ax = axes[1, 0]
    for st in signal_types:
        type_data = results_df[results_df['signal_type'] == st]['total_return']
        ax.hist(type_data, alpha=0.5, label=st, bins=20)
    ax.axvline(x=0, color='r', linestyle='--', alpha=0.5)
    if KOREAN_FONT_PROP:
        ax.set_xlabel('Return (%)', fontproperties=KOREAN_FONT_PROP)
        ax.set_ylabel('Frequency', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Return Distribution by Signal Type', fontproperties=KOREAN_FONT_PROP)
        ax.legend(prop=KOREAN_FONT_PROP)
    else:
        ax.set_xlabel('Return (%)')
        ax.set_ylabel('Frequency')
        ax.set_title('Return Distribution by Signal Type')
        ax.legend()
    
    # Signal count
    ax = axes[1, 1]
    signal_counts = [len(results_df[results_df['signal_type'] == st]) for st in signal_types]
    ax.bar(signal_types, signal_counts, color='orange', alpha=0.7)
    if KOREAN_FONT_PROP:
        ax.set_ylabel('Signal Count', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Signal Count by Type', fontproperties=KOREAN_FONT_PROP)
    else:
        ax.set_ylabel('Signal Count')
        ax.set_title('Signal Count by Type')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_file}")

def generate_all_visualizations(results_df: pd.DataFrame, output_dir: Path, date_str: str):
    """Generate all visualizations"""
    print("\n" + "="*80)
    print("Generating Visualizations")
    print("="*80)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Signal vs Return scatter
    plot_signal_vs_return_scatter(
        results_df,
        output_dir / f"signal_vs_return_{date_str}.png"
    )
    
    # Cumulative returns
    plot_cumulative_returns(
        results_df,
        output_dir / f"cumulative_returns_{date_str}.png"
    )
    
    # Win rate by strength
    if 'signal_strength' in results_df.columns:
        plot_win_rate_by_strength(
            results_df,
            output_dir / f"win_rate_by_strength_{date_str}.png"
        )
    
    # Time decay
    plot_time_decay(
        results_df,
        output_dir / f"time_decay_{date_str}.png"
    )
    
    # Performance by signal type
    if 'signal_type' in results_df.columns:
        plot_performance_by_signal_type(
            results_df,
            output_dir / f"performance_by_type_{date_str}.png"
        )
    
    print(f"\nAll visualizations saved to {output_dir}")

if __name__ == "__main__":
    # Test visualizations
    print("="*80)
    print("Testing Visualizations")
    print("="*80)
    
    # Create sample data
    np.random.seed(42)
    sample_results = pd.DataFrame({
        'signal_type': ['tier'] * 30 + ['cohesion'] * 40 + ['leadership'] * 30,
        'signal_strength': np.random.uniform(0.5, 3.0, 100),
        'total_return': np.random.normal(5, 15, 100),
        'return_1w': np.random.normal(1, 5, 100),
        'return_2w': np.random.normal(2, 7, 100),
        'return_4w': np.random.normal(3, 10, 100),
        'return_8w': np.random.normal(4, 12, 100),
        'return_12w': np.random.normal(5, 15, 100),
    })
    
    output_dir = Path("/tmp/backtest_test")
    generate_all_visualizations(sample_results, output_dir, "20251113")

