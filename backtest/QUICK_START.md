# Quick Start Guide: ETF-Style Strategy Backtesting

## Overview

Based on time decay analysis showing low returns in weeks 1-4 and significant pickup at week 8, we've implemented 4 ETF-style strategy variants to optimize entry timing and cash management.

## Quick Commands

### Test All Strategies
```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
python3 backtest/backtest_etf_strategy.py \
  --start-date 2025-02-01 \
  --end-date 2025-08-01 \
  --exit-target 20.0 \
  --max-weeks 12 \
  --strategy all
```

### Test Specific Strategy
```bash
# Buy-After-8Weeks (Best risk-adjusted returns)
python3 backtest/backtest_etf_strategy.py \
  --start-date 2025-02-01 \
  --end-date 2025-08-01 \
  --strategy buy_after_8w

# Alternative Allocation (Balanced approach)
python3 backtest/backtest_etf_strategy.py \
  --start-date 2025-02-01 \
  --end-date 2025-08-01 \
  --strategy alternative
```

## Strategy Summary

| Strategy | Entry | Win Rate | Avg Return | Sharpe | Signals |
|----------|-------|----------|------------|--------|---------|
| **Buy-After-8W** | 100% at week 8 | 81.5% | **5.63%** | **2.06** | 81 (5.7%) |
| **Alternative** | 20/20/60 | 82.2% | 5.31% | 2.01 | 1,418 (100%) |
| **Relaxed** | 10/10/80 | **83.4%** | 3.14% | 1.79 | 1,418 (100%) |
| **Original** | 10/10/80 (strict) | 82.7% | 2.43% | 1.62 | 1,418 (100%) |
| **Buy-Hold** | 100% at signal | 78.3% | **13.64%** | 1.80 | 1,418 (100%) |

## Key Insights

1. **Buy-After-8Weeks** has best risk-adjusted returns (Sharpe 2.06) but is very selective
2. **Alternative Allocation** provides good balance: 5.31% return with 100% signal participation
3. **Time Decay**: Returns are very low (0.1-0.2%) in weeks 1-4, pick up at week 8 (5.0%), peak at week 12 (12.7%)
4. **Early Exits**: 95% of positions exit early due to hitting 20% return target

## Recommendations

### For Maximum Risk-Adjusted Returns
**Use: Buy-After-8Weeks**
- Wait until week 8 to enter
- Only enter if signal still valid
- Expect ~81 signals per period (very selective)

### For Balanced Approach
**Use: Alternative Allocation (20/20/60)**
- More early exposure (40% in weeks 1-2)
- Still benefit from week 7 entry
- Higher participation (all signals)

### For Conservative Investors
**Use: Relaxed ETF-Style**
- Highest win rate (83.4%)
- Gradual entry (10/10/80)
- Lower absolute returns but more consistent

## Output Files

After running, check:
- `backtest/results/{strategy}_strategy_results_YYYYMMDD.csv` - Detailed results
- `backtest/reports/etf_strategy_comparison_YYYYMMDD.md` - Comparison report
- `backtest/reports/strategy_comparison_YYYYMMDD.png` - Visualization

## See Also

- `STRATEGY_ANALYSIS.md` - Detailed strategy analysis
- `README.md` - Full documentation

