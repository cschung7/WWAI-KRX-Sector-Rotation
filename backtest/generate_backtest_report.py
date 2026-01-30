#!/usr/bin/env python3
"""
Backtest Report Generator

Generates comprehensive markdown report from backtest results
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict

try:
    from .statistical_analysis import StatisticalAnalyzer
except ImportError:
    from statistical_analysis import StatisticalAnalyzer

def generate_backtest_report(results_df: pd.DataFrame, analysis_summary: Dict,
                             output_file: Path, date_str: str):
    """
    Generate comprehensive backtest report
    
    Args:
        results_df: DataFrame with backtest results
        analysis_summary: Summary from StatisticalAnalyzer
        output_file: Path to output markdown file
        date_str: Date string for report
    """
    print(f"\nGenerating backtest report: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Backtest Report: Investment Signal Performance\n\n")
        f.write(f"**Report Date**: {date_str}\n")
        f.write(f"**Analysis Period**: {results_df['signal_date'].min().date()} to {results_df['signal_date'].max().date()}\n")
        f.write(f"**Holding Period**: 12 weeks (3 months)\n")
        f.write(f"**Total Signals**: {len(results_df)}\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## 📊 Executive Summary\n\n")
        
        overall = analysis_summary.get('overall_metrics', {})
        if overall:
            f.write("### Overall Performance\n\n")
            f.write(f"- **Total Signals**: {overall.get('total_signals', 0)}\n")
            f.write(f"- **Win Rate**: {overall.get('win_rate', 0):.1f}%\n")
            f.write(f"- **Average Return**: {overall.get('avg_return', 0):.2f}% (over holding period, NOT annualized)\n")
            if 'annualized_return' in overall:
                f.write(f"- **Annualized Return**: {overall.get('annualized_return', 0):.2f}%\n")
            f.write(f"- **Median Return**: {overall.get('median_return', 0):.2f}%\n")
            f.write(f"- **Sharpe Ratio**: {overall.get('sharpe_ratio', 0):.2f} (annualized)\n")
            f.write(f"- **Maximum Drawdown**: {overall.get('max_drawdown', 0):.2f}%\n")
            f.write(f"- **Positive Signals**: {overall.get('positive_signals', 0)}\n")
            f.write(f"- **Negative Signals**: {overall.get('negative_signals', 0)}\n\n")
            
            # Key finding
            if overall.get('win_rate', 0) > 50:
                f.write("✅ **Key Finding**: Signals show positive predictive power (win rate >50%)\n\n")
            else:
                f.write("⚠️ **Key Finding**: Signals do not show clear predictive power (win rate ≤50%)\n\n")
        
        f.write("---\n\n")
        
        # Performance by Signal Type
        f.write("## 📈 Performance by Signal Type\n\n")
        
        by_type = analysis_summary.get('by_signal_type', {})
        if by_type:
            f.write("| Signal Type | Count | Win Rate | Avg Return | Median Return |\n")
            f.write("|-------------|-------|----------|------------|---------------|\n")
            
            for signal_type, metrics in by_type.items():
                f.write(f"| {signal_type} | {metrics.get('count', 0)} | "
                       f"{metrics.get('win_rate', 0):.1f}% | "
                       f"{metrics.get('avg_return', 0):.2f}% | "
                       f"{metrics.get('median_return', 0):.2f}% |\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Performance by Tier
        f.write("## 🎯 Performance by Tier (Tier Signals Only)\n\n")
        
        by_tier = analysis_summary.get('by_tier', {})
        if by_tier:
            f.write("| Tier | Count | Win Rate | Avg Return | Median Return |\n")
            f.write("|------|-------|----------|------------|---------------|\n")
            
            for tier, metrics in by_tier.items():
                f.write(f"| {tier} | {metrics.get('count', 0)} | "
                       f"{metrics.get('win_rate', 0):.1f}% | "
                       f"{metrics.get('avg_return', 0):.2f}% | "
                       f"{metrics.get('median_return', 0):.2f}% |\n")
            f.write("\n")
        else:
            f.write("No tier signals found in results.\n\n")
        
        f.write("---\n\n")
        
        # Time Decay Analysis
        f.write("## ⏱️ Time Decay Analysis\n\n")
        f.write("Returns over different holding periods:\n\n")
        
        time_decay = analysis_summary.get('time_decay', {})
        if time_decay:
            f.write("| Period | Count | Win Rate | Avg Return | Median Return |\n")
            f.write("|--------|-------|----------|------------|---------------|\n")
            
            for period, metrics in sorted(time_decay.items()):
                f.write(f"| {period} | {metrics.get('count', 0)} | "
                       f"{metrics.get('win_rate', 0):.1f}% | "
                       f"{metrics.get('avg_return', 0):.2f}% | "
                       f"{metrics.get('median_return', 0):.2f}% |\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Correlation Analysis
        f.write("## 🔗 Correlation Analysis\n\n")
        
        correlations = analysis_summary.get('correlations', {})
        if correlations:
            f.write("Correlation between signal metrics and returns:\n\n")
            for metric, corr in correlations.items():
                f.write(f"- **{metric}**: {corr:.3f}\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Statistical Significance
        f.write("## 📊 Statistical Significance\n\n")
        
        significance = analysis_summary.get('statistical_significance', {})
        if significance:
            f.write("| Test | t-Statistic | p-Value | Significant (p<0.05) |\n")
            f.write("|------|-------------|---------|---------------------|\n")
            
            for test_name, stats in significance.items():
                sig_mark = "✅" if stats.get('significant', False) else "❌"
                f.write(f"| {test_name} | {stats.get('t_statistic', 0):.3f} | "
                       f"{stats.get('p_value', 1):.4f} | {sig_mark} |\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Theme vs Ticker Analysis
        f.write("## 🎯 Theme-Level vs Ticker-Level Performance\n\n")
        
        theme_vs_ticker = analysis_summary.get('theme_vs_ticker', {})
        if theme_vs_ticker:
            f.write("| Level | Count | Win Rate | Avg Return | Median Return |\n")
            f.write("|-------|-------|----------|------------|---------------|\n")
            
            for level, metrics in theme_vs_ticker.items():
                f.write(f"| {level} | {metrics.get('count', 0)} | "
                       f"{metrics.get('win_rate', 0):.1f}% | "
                       f"{metrics.get('avg_return', 0):.2f}% | "
                       f"{metrics.get('median_return', 0):.2f}% |\n")
            f.write("\n")
        
        f.write("---\n\n")
        
        # Top Performing Signals
        f.write("## 🏆 Top 20 Performing Signals\n\n")
        
        top_signals = results_df.nlargest(20, 'total_return')[
            ['signal_date', 'theme', 'signal_type', 'signal_strength', 'total_return']
        ]
        
        f.write("| Date | Theme | Signal Type | Strength | Return (%) |\n")
        f.write("|------|-------|-------------|----------|------------|\n")
        
        for _, row in top_signals.iterrows():
            f.write(f"| {row['signal_date'].date()} | {row['theme'][:30]} | "
                   f"{row['signal_type']} | {row['signal_strength']:.2f} | "
                   f"{row['total_return']:.2f}% |\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        # Bottom Performing Signals
        f.write("## ⚠️ Bottom 20 Performing Signals\n\n")
        
        bottom_signals = results_df.nsmallest(20, 'total_return')[
            ['signal_date', 'theme', 'signal_type', 'signal_strength', 'total_return']
        ]
        
        f.write("| Date | Theme | Signal Type | Strength | Return (%) |\n")
        f.write("|------|-------|-------------|----------|------------|\n")
        
        for _, row in bottom_signals.iterrows():
            f.write(f"| {row['signal_date'].date()} | {row['theme'][:30]} | "
                   f"{row['signal_type']} | {row['signal_strength']:.2f} | "
                   f"{row['total_return']:.2f}% |\n")
        f.write("\n")
        
        f.write("---\n\n")
        
        # Conclusions
        f.write("## 💡 Conclusions\n\n")
        
        if overall.get('win_rate', 0) > 55:
            f.write("✅ **Strong Evidence**: Signals show statistically significant predictive power.\n\n")
        elif overall.get('win_rate', 0) > 50:
            f.write("⚠️ **Weak Evidence**: Signals show slight predictive power but may not be statistically significant.\n\n")
        else:
            f.write("❌ **No Evidence**: Signals do not show predictive power for 3-month returns.\n\n")
        
        # Recommendations
        f.write("### Recommendations\n\n")
        
        best_signal_type = None
        best_win_rate = 0
        for signal_type, metrics in by_type.items():
            if metrics.get('win_rate', 0) > best_win_rate:
                best_win_rate = metrics.get('win_rate', 0)
                best_signal_type = signal_type
        
        if best_signal_type:
            f.write(f"1. **Best Signal Type**: {best_signal_type} (win rate: {best_win_rate:.1f}%)\n")
        
        if time_decay:
            # Find optimal holding period
            best_period = None
            best_return = -999
            for period, metrics in time_decay.items():
                if metrics.get('avg_return', -999) > best_return:
                    best_return = metrics.get('avg_return', -999)
                    best_period = period
            
            if best_period:
                f.write(f"2. **Optimal Holding Period**: {best_period} (avg return: {best_return:.2f}%)\n")
        
        f.write("\n---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"  Report saved: {output_file}")

