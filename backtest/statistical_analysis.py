#!/usr/bin/env python3
"""
Statistical Analysis Module for Backtesting

Performs statistical tests on backtest results
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple

class StatisticalAnalyzer:
    """Perform statistical analysis on backtest results"""
    
    def __init__(self, results_df: pd.DataFrame):
        """
        Args:
            results_df: DataFrame with signal-return pairs from backtest
        """
        self.results = results_df.copy()
    
    def calculate_performance_metrics(self) -> Dict:
        """Calculate overall performance metrics"""
        if len(self.results) == 0:
            return {}
        
        metrics = {
            'total_signals': len(self.results),
            'win_rate': (self.results['total_return'] > 0).mean() * 100,
            'avg_return': self.results['total_return'].mean(),
            'median_return': self.results['total_return'].median(),
            'std_return': self.results['total_return'].std(),
            'min_return': self.results['total_return'].min(),
            'max_return': self.results['total_return'].max(),
            'positive_signals': (self.results['total_return'] > 0).sum(),
            'negative_signals': (self.results['total_return'] < 0).sum(),
        }
        
        # Calculate annualized return if holding_period_weeks is available
        if 'holding_weeks' in self.results.columns:
            avg_holding_weeks = self.results['holding_weeks'].mean()
            if avg_holding_weeks > 0:
                metrics['annualized_return'] = metrics['avg_return'] * (52 / avg_holding_weeks)
            else:
                metrics['annualized_return'] = 0
        else:
            # Default to 12 weeks if not available
            metrics['annualized_return'] = metrics['avg_return'] * (52 / 12)
        
        # Sharpe ratio (annualized, assuming 52 weeks/year)
        if metrics['std_return'] > 0:
            # Use actual holding period if available, else default to 12 weeks
            if 'holding_weeks' in self.results.columns:
                avg_holding_weeks = self.results['holding_weeks'].mean()
                if avg_holding_weeks > 0:
                    metrics['sharpe_ratio'] = (metrics['avg_return'] / metrics['std_return']) * np.sqrt(52 / avg_holding_weeks)
                else:
                    metrics['sharpe_ratio'] = (metrics['avg_return'] / metrics['std_return']) * np.sqrt(52/12)
            else:
                metrics['sharpe_ratio'] = (metrics['avg_return'] / metrics['std_return']) * np.sqrt(52/12)
        else:
            metrics['sharpe_ratio'] = 0
        
        # Maximum drawdown
        cumulative = (1 + self.results['total_return'] / 100).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max * 100
        metrics['max_drawdown'] = drawdown.min()
        
        return metrics
    
    def analyze_by_signal_type(self) -> Dict[str, Dict]:
        """Analyze performance by signal type"""
        analysis = {}
        
        for signal_type in self.results['signal_type'].unique():
            signal_data = self.results[self.results['signal_type'] == signal_type]
            
            analysis[signal_type] = {
                'count': len(signal_data),
                'win_rate': (signal_data['total_return'] > 0).mean() * 100,
                'avg_return': signal_data['total_return'].mean(),
                'median_return': signal_data['total_return'].median(),
                'std_return': signal_data['total_return'].std(),
            }
        
        return analysis
    
    def analyze_by_tier(self) -> Dict[str, Dict]:
        """Analyze performance by tier (for tier signals)"""
        tier_data = self.results[self.results['tier'].notna()]
        
        if len(tier_data) == 0:
            return {}
        
        analysis = {}
        for tier in sorted(tier_data['tier'].unique()):
            tier_results = tier_data[tier_data['tier'] == tier]
            
            analysis[f'Tier {int(tier)}'] = {
                'count': len(tier_results),
                'win_rate': (tier_results['total_return'] > 0).mean() * 100,
                'avg_return': tier_results['total_return'].mean(),
                'median_return': tier_results['total_return'].median(),
            }
        
        return analysis
    
    def analyze_by_signal_strength(self, bins: int = 3) -> Dict[str, Dict]:
        """Analyze performance by signal strength"""
        if 'signal_strength' not in self.results.columns:
            return {}
        
        # Create bins
        self.results['strength_bin'] = pd.cut(
            self.results['signal_strength'],
            bins=bins,
            labels=[f'Low', 'Medium', 'High'][:bins]
        )
        
        analysis = {}
        for bin_label in self.results['strength_bin'].cat.categories:
            bin_data = self.results[self.results['strength_bin'] == bin_label]
            
            analysis[bin_label] = {
                'count': len(bin_data),
                'win_rate': (bin_data['total_return'] > 0).mean() * 100,
                'avg_return': bin_data['total_return'].mean(),
                'median_return': bin_data['total_return'].median(),
            }
        
        return analysis
    
    def time_decay_analysis(self) -> Dict[str, float]:
        """Analyze how returns change over time (1w, 2w, 4w, 8w, 12w)"""
        time_periods = ['1w', '2w', '4w', '8w', '12w']
        analysis = {}
        
        for period in time_periods:
            col_name = f'return_{period}'
            if col_name in self.results.columns:
                period_data = self.results[col_name].dropna()
                if len(period_data) > 0:
                    analysis[period] = {
                        'count': len(period_data),
                        'win_rate': (period_data > 0).mean() * 100,
                        'avg_return': period_data.mean(),
                        'median_return': period_data.median(),
                    }
        
        return analysis
    
    def correlation_analysis(self) -> Dict[str, float]:
        """Calculate correlations between signal strength and returns"""
        correlations = {}
        
        if 'signal_strength' in self.results.columns:
            corr = self.results['signal_strength'].corr(self.results['total_return'])
            correlations['signal_strength_vs_return'] = corr
        
        if 'fiedler_change' in self.results.columns:
            corr = self.results['fiedler_change'].corr(self.results['total_return'])
            correlations['fiedler_change_vs_return'] = corr
        
        if 'leadership_gap' in self.results.columns:
            gap_data = self.results[self.results['leadership_gap'].notna()]
            if len(gap_data) > 0:
                corr = gap_data['leadership_gap'].corr(gap_data['total_return'])
                correlations['leadership_gap_vs_return'] = corr
        
        return correlations
    
    def statistical_significance(self) -> Dict[str, Dict]:
        """Test statistical significance of signals"""
        significance = {}
        
        # Test if average return is significantly different from zero
        if len(self.results) > 1:
            t_stat, p_value = stats.ttest_1samp(self.results['total_return'], 0)
            significance['mean_return'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        # Test by signal type
        for signal_type in self.results['signal_type'].unique():
            signal_data = self.results[self.results['signal_type'] == signal_type]
            if len(signal_data) > 1:
                t_stat, p_value = stats.ttest_1samp(signal_data['total_return'], 0)
                significance[f'{signal_type}_mean'] = {
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'significant': p_value < 0.05
                }
        
        return significance
    
    def theme_vs_ticker_analysis(self) -> Dict[str, Dict]:
        """Compare theme-level vs ticker-level returns"""
        theme_results = self.results[self.results['ticker'].isna()]
        ticker_results = self.results[self.results['ticker'].notna()]
        
        analysis = {}
        
        if len(theme_results) > 0:
            analysis['theme_level'] = {
                'count': len(theme_results),
                'win_rate': (theme_results['total_return'] > 0).mean() * 100,
                'avg_return': theme_results['total_return'].mean(),
                'median_return': theme_results['total_return'].median(),
            }
        
        if len(ticker_results) > 0:
            analysis['ticker_level'] = {
                'count': len(ticker_results),
                'win_rate': (ticker_results['total_return'] > 0).mean() * 100,
                'avg_return': ticker_results['total_return'].mean(),
                'median_return': ticker_results['total_return'].median(),
            }
        
        return analysis
    
    def generate_summary(self) -> Dict:
        """Generate comprehensive analysis summary"""
        return {
            'overall_metrics': self.calculate_performance_metrics(),
            'by_signal_type': self.analyze_by_signal_type(),
            'by_tier': self.analyze_by_tier(),
            'by_signal_strength': self.analyze_by_signal_strength(),
            'time_decay': self.time_decay_analysis(),
            'correlations': self.correlation_analysis(),
            'statistical_significance': self.statistical_significance(),
            'theme_vs_ticker': self.theme_vs_ticker_analysis()
        }

if __name__ == "__main__":
    # Test statistical analysis
    print("="*80)
    print("Testing Statistical Analyzer")
    print("="*80)
    
    # Create sample results
    np.random.seed(42)
    sample_results = pd.DataFrame({
        'signal_date': pd.date_range('2025-02-01', periods=100, freq='W'),
        'theme': ['Theme1'] * 50 + ['Theme2'] * 50,
        'signal_type': ['tier'] * 30 + ['cohesion'] * 40 + ['leadership'] * 30,
        'signal_strength': np.random.uniform(0.5, 3.0, 100),
        'tier': [1] * 20 + [2] * 10 + [None] * 70,
        'total_return': np.random.normal(5, 15, 100),
        'return_1w': np.random.normal(1, 5, 100),
        'return_2w': np.random.normal(2, 7, 100),
        'return_4w': np.random.normal(3, 10, 100),
        'return_8w': np.random.normal(4, 12, 100),
        'return_12w': np.random.normal(5, 15, 100),
        'ticker': [None] * 100
    })
    
    analyzer = StatisticalAnalyzer(sample_results)
    summary = analyzer.generate_summary()
    
    print("\nOverall Metrics:")
    for key, value in summary['overall_metrics'].items():
        print(f"  {key}: {value}")

