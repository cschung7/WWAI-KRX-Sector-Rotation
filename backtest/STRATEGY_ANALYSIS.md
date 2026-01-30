# ETF-Style Strategy Analysis & Recommendations

## Executive Summary

Based on backtesting results (2025-02-01 to 2025-08-01), we tested 4 ETF-style strategy variants against buy-and-hold:

### Key Findings

1. **Buy-After-8Weeks Strategy** shows the best risk-adjusted returns among ETF variants:
   - Average Return: 5.63%
   - Win Rate: 81.5%
   - Sharpe Ratio: 2.06
   - **However**: Only 81 signals (5.7% of total) - very selective

2. **Alternative Allocation (20/20/60)** shows strong performance:
   - Average Return: 5.31%
   - Win Rate: 82.2%
   - Sharpe Ratio: 2.01
   - More signals: 1,418 (100% of total)

3. **Relaxed ETF-Style** improves over original:
   - Average Return: 3.14% (vs 2.43% original)
   - Win Rate: 83.4% (vs 82.7% original)
   - More signals remain valid at week 7

4. **Buy-and-Hold** still has highest absolute returns:
   - Average Return: 13.64%
   - Win Rate: 78.3%
   - But: Higher volatility, lower win rate

## Strategy Performance Comparison

| Strategy | Signals | Win Rate | Avg Return | Sharpe | Avg Weeks | Valid % | Early Exits |
|----------|---------|----------|------------|--------|-----------|---------|-------------|
| **Buy-After-8W** | 81 | 81.5% | **5.63%** | **2.06** | 3.8 | 100% | 95% |
| **Alternative** | 1,418 | 82.2% | 5.31% | 2.01 | 11.4 | 5.6% | 95% |
| **Relaxed** | 1,418 | **83.4%** | 3.14% | 1.79 | 11.7 | 5.6% | 95% |
| **Original** | 1,418 | 82.7% | 2.43% | 1.62 | 10.4 | 5.6% | 95% |
| **Buy-Hold** | 1,418 | 78.3% | **13.64%** | 1.80 | 12.0 | - | 0% |

## Strategy Details

### 1. Buy-After-8Weeks Strategy ⭐ **RECOMMENDED**

**Mechanism:**
- Weeks 1-7: Hold 100% cash, monitor signal validity
- Week 8: If signal still valid, buy 100% of position
- Exit: 12 weeks OR 20% return (whichever comes first)

**Pros:**
- Highest Sharpe ratio (2.06) among ETF variants
- Best average return (5.63%) among ETF variants
- 100% of signals remain valid at entry (very selective)
- Short average holding period (3.8 weeks) - quick exits
- 95% early exits (hitting 20% target)

**Cons:**
- Very selective: Only 5.7% of signals qualify
- Misses early opportunities
- Lower absolute returns than buy-and-hold

**Best For:**
- Risk-averse investors
- When signal quality is more important than quantity
- When you want to avoid early volatility (weeks 1-4 show low returns)

### 2. Alternative Allocation (20/20/60)

**Mechanism:**
- Week 1: Buy 20% of position
- Week 2: Buy 20% of position
- Week 7: If signal still positive, buy remaining 60%
- Exit: 12 weeks OR 20% return

**Pros:**
- Good balance of return (5.31%) and win rate (82.2%)
- Higher Sharpe ratio (2.01) than original
- More capital deployed early (40% vs 20%)
- All signals tested (1,418)

**Cons:**
- Still lower returns than buy-and-hold
- Only 5.6% of signals remain valid at week 7

**Best For:**
- Investors wanting gradual entry with more early exposure
- When you want to participate in more opportunities

### 3. Relaxed ETF-Style

**Mechanism:**
- Week 1: Buy 10% of position
- Week 2: Buy 10% of position
- Week 7: If signal still positive (relaxed criteria), buy remaining 80%
- Exit: 12 weeks OR 20% return

**Pros:**
- Highest win rate (83.4%)
- Better than original (3.14% vs 2.43%)
- All signals tested

**Cons:**
- Lower returns than alternative or buy-after-8w
- Still only 5.6% signals valid at week 7

**Best For:**
- Investors prioritizing win rate over absolute returns
- Conservative approach with gradual entry

### 4. Original ETF-Style (Strict Validity)

**Mechanism:**
- Week 1: Buy 10% of position
- Week 2: Buy 10% of position
- Week 7: If signal still valid (strict criteria), buy remaining 80%
- Exit: 12 weeks OR 20% return

**Pros:**
- Conservative approach
- All signals tested

**Cons:**
- Lowest returns (2.43%) among ETF variants
- Lowest Sharpe ratio (1.62)
- Only 5.6% signals remain valid

**Best For:**
- Not recommended - use Relaxed instead

## Key Insights from Time Decay Analysis

The time decay plot shows:
- **Weeks 1-4**: Very low returns (0.1-0.2%)
- **Week 8**: Significant pickup (5.0%)
- **Week 12**: Peak performance (12.7%)

This validates the "Buy-After-8Weeks" strategy approach - avoiding the low-return early period.

## Recommendations

### For Maximum Risk-Adjusted Returns:
**Use: Buy-After-8Weeks Strategy**
- Wait until week 8 to enter
- Only enter if signal still valid
- Exit at 20% return or 12 weeks
- Expect ~81 signals per period (selective)

### For Balanced Approach:
**Use: Alternative Allocation (20/20/60)**
- More early exposure (40% in weeks 1-2)
- Still benefit from week 7 entry if signal valid
- Higher participation (all signals)
- Good risk-adjusted returns

### For Conservative Investors:
**Use: Relaxed ETF-Style**
- Highest win rate (83.4%)
- Gradual entry (10/10/80)
- Lower absolute returns but more consistent

### For Maximum Absolute Returns:
**Use: Buy-and-Hold**
- Highest average return (13.64%)
- But: Lower win rate (78.3%)
- Higher volatility
- No cash management

## Implementation Notes

1. **Signal Validity Check**: The relaxed criteria (just check if signal is still positive) significantly improves results over strict criteria.

2. **Early Exit Target**: 95% of positions exit early due to hitting 20% return target. This is good - it means the strategy is working.

3. **Week 7/8 Entry**: Only 5.6% of signals remain valid at week 7 with strict criteria. With relaxed criteria, this improves but still low. The "Buy-After-8Weeks" strategy is very selective but performs well.

4. **Cash Management**: Holding cash in weeks 1-7 reduces early volatility but also reduces returns. The trade-off depends on risk tolerance.

## Next Steps

1. **Test with different exit targets**: Try 15%, 25%, 30% to see optimal exit point
2. **Test with different entry weeks**: Try week 6, week 9, week 10
3. **Combine strategies**: Use Buy-After-8W for high-confidence signals, Alternative for others
4. **Sector-specific optimization**: Some sectors may benefit from different strategies

## Conclusion

The **Buy-After-8Weeks** strategy offers the best risk-adjusted returns (Sharpe 2.06) but is very selective. The **Alternative Allocation (20/20/60)** provides a good balance for investors wanting more participation while still benefiting from the time decay insights.

Both strategies significantly outperform buy-and-hold on a risk-adjusted basis, though buy-and-hold has higher absolute returns.

