# Backtesting System for Investment Signals

## Overview

This backtesting system evaluates whether **Tier Classification**, **Cohesion Enhancement**, and **Leadership Gap** signals have predictive power for 3-month forward returns at both theme/sector and individual ticker levels.

## Features

- **Walk-Forward Analysis**: Tests signals on historical data with weekly evaluation
- **Multiple Signal Types**: 
  - Tier Classification (TIER 1, TIER 2)
  - Cohesion Enhancement (Fiedler change > threshold)
  - Leadership Gap (Large-cap vs small-cap regime divergence)
  - **Signal Combinations**: Tier+Cohesion, Tier+Leadership, All three combined
- **Dual-Level Analysis**: Both theme-level (portfolio) and ticker-level returns
- **Time Decay Analysis**: Tracks returns at 1, 2, 4, 8, and 12 weeks
- **Statistical Testing**: Win rates, Sharpe ratios, correlation analysis, significance tests
- **Comprehensive Reporting**: Markdown reports with visualizations

## Quick Start

### Basic Backtest
```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
python3 backtest/run_backtest.py --start-date 2025-02-01 --end-date 2025-08-01
```

### ETF-Style Strategy Backtest
```bash
# Test all strategy variants
python3 backtest/backtest_etf_strategy.py --start-date 2025-02-01 --end-date 2025-08-01 --strategy all

# Test specific strategy
python3 backtest/backtest_etf_strategy.py --start-date 2025-02-01 --end-date 2025-08-01 --strategy buy_after_8w --exit-target 20.0
```

### Strategy Variants
- `original`: 10% week 1, 10% week 2, 80% week 7 (strict validity)
- `relaxed`: 10% week 1, 10% week 2, 80% week 7 (relaxed validity)
- `alternative`: 20% week 1, 20% week 2, 60% week 7
- `buy_after_8w`: 100% at week 8 (if signal valid)
- `all`: Test all variants

### Full Options

```bash
python3 backtest/run_backtest.py \
  --start-date 2025-02-01 \
  --end-date 2025-11-01 \
  --holding-period 12 \
  --frequency weekly \
  --output-dir backtest/output
```

### Arguments

- `--start-date`: Start date for backtest (YYYY-MM-DD, default: 2025-02-01)
- `--end-date`: End date for backtest (YYYY-MM-DD, default: today - 12 weeks)
- `--holding-period`: Holding period in weeks (default: 12 = 3 months)
- `--frequency`: Evaluation frequency - `weekly` or `daily` (default: weekly)
- `--output-dir`: Custom output directory (default: backtest/reports and backtest/results)

## Output Files

### Results CSV
`backtest/results/signal_performance_YYYYMMDD.csv`

Contains all signal-return pairs with columns:
- `signal_date`: Date when signal occurred
- `theme`: Theme name
- `ticker`: Ticker (if ticker-level, else NaN)
- `signal_type`: Type of signal (tier, cohesion, leadership, tier+cohesion, tier+leadership, tier+cohesion+leadership)
- `signal_strength`: Normalized signal strength (0-3)
- `tier`: Tier classification (1 or 2, if tier signal)
- `leadership_gap`: Leadership gap percentage (if leadership signal)
- `fiedler_change`: Fiedler value change (if cohesion signal)
- `total_return`: 12-week forward return (%)
- `return_1w`, `return_2w`, `return_4w`, `return_8w`: Intermediate returns

### Report
`backtest/reports/backtest_report_YYYYMMDD.md`

Comprehensive markdown report including:
- Executive summary with key findings
- Performance by signal type
- Performance by tier
- Time decay analysis
- Correlation analysis
- Statistical significance tests
- Top/bottom performing signals
- Conclusions and recommendations

### Visualizations
`backtest/reports/*_YYYYMMDD.png`

- `signal_vs_return_*.png`: Scatter plots of signal strength vs returns
- `cumulative_returns_*.png`: Cumulative return curves by signal type
- `win_rate_by_strength_*.png`: Win rate by signal strength bins
- `time_decay_*.png`: Returns over different holding periods
- `performance_by_type_*.png`: Performance metrics by signal type

## Signal Definitions

### Tier Classification Signal

**TIER 1** (Buy NOW):
- Baseline Fiedler > 2.0
- Fiedler Change > 1.5
- Current Fiedler > 3.0

**TIER 2** (Accumulate):
- Baseline Fiedler 1.0-2.0
- Fiedler Change > 1.0

### Cohesion Enhancement Signal

- Fiedler change > 1.5 (over 30-day lookback)
- Current Fiedler > 2.0
- Percentage change > 30%

### Leadership Gap Signal

- Leadership gap > threshold (tested at 20%, 40%, 60%)
- Calculated as: (Large-cap Bull % - Rest Bull %)

## Performance Metrics

- **Win Rate**: Percentage of signals with positive returns
- **Average Return**: Mean return across all signals
- **Sharpe Ratio**: Risk-adjusted return (annualized)
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Statistical Significance**: t-tests for mean return ≠ 0

## Example Results

From a sample backtest (2025-02-01 to 2025-08-01):
- **Total Signals**: 14,889
- **Win Rate**: 66.9%
- **Average Return**: 12.88%
- **Sharpe Ratio**: 0.97

## Module Structure

```
backtest/
├── __init__.py
├── data_loader.py          # Load historical data
├── signal_calculator.py    # Calculate signals
├── return_calculator.py    # Calculate forward returns
├── backtest_engine.py      # Main backtest logic
├── statistical_analysis.py # Statistical tests
├── visualizations.py       # Charts and plots
├── generate_backtest_report.py  # Report generation
├── run_backtest.py         # Main entry point
├── reports/                # Generated reports and charts
└── results/                 # CSV results files
```

## Data Requirements

The backtest requires:
1. **Fiedler Timeseries**: `data/theme_*_timeseries.csv` files
2. **Stock Prices**: Price data in `PRICE_DATA_DIR` (from config.py)
3. **Theme Mapping**: `data/theme_to_tickers.json` or database
4. **Leadership Data**: `data/within_theme_leadership_ranking.csv` (optional)

## Strategy Analysis

See `STRATEGY_ANALYSIS.md` for detailed analysis of ETF-style strategy variants.

**Key Finding**: The "Buy-After-8Weeks" strategy shows the best risk-adjusted returns (Sharpe 2.06) but is very selective (only 5.7% of signals qualify). The "Alternative Allocation (20/20/60)" provides a good balance for investors wanting more participation.

## Notes

- The end date should be at least `holding_period_weeks` before today to ensure forward return data is available
- Weekly evaluation is recommended for faster execution
- Daily evaluation provides more signals but takes longer
- Results are saved with UTF-8 encoding to support Korean characters
- ETF-style strategies reduce early volatility but may reduce absolute returns compared to buy-and-hold

## Troubleshooting

**No results generated**:
- Check that start_date and end_date have at least `holding_period_weeks` difference
- Verify Fiedler timeseries files exist in `data/`
- Ensure price data is available for theme tickers

**Import errors**:
- Make sure you're running from the project root directory
- Check that all dependencies are installed (pandas, numpy, scipy, matplotlib)

**Missing data**:
- Some themes may not have sufficient historical data
- Leadership gap data is optional (signals will still work without it)

