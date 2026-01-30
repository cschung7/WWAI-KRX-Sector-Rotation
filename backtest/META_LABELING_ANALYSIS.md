# Meta-Labeling Analysis: Should We Adopt de Prado's Approach?

## Current Performance Baseline

From recent backtest (2025-02-01 to 2025-08-01):
- **Total Signals**: 15,643
- **Win Rate**: 67.7%
- **Average Return**: 13.30%
- **False Positives**: ~32.3% (signals with negative returns)

## What is Meta-Labeling?

**Meta-labeling** (from Marcos López de Prado's "Advances in Financial Machine Learning") is a two-stage approach:

1. **Primary Model**: Generates signals (our Tier/Cohesion/Leadership signals)
2. **Meta-Labeler**: Binary classifier that learns: "Given this signal, should I take the trade?"

### Key Benefits

1. **Reduces False Positives**: Filters out signals that don't lead to good returns
2. **Improves Precision**: Higher win rate by only taking high-confidence trades
3. **Better Risk Management**: Avoids trades that look good but perform poorly
4. **Preserves Information**: Doesn't modify primary signals, just filters them

## Would It Help Our System?

### ✅ **YES - Strong Case for Meta-Labeling**

**Reasons:**

1. **32.3% False Positive Rate**: We have ~5,042 signals with negative returns. If we could filter even 50% of these, we'd improve win rate from 67.7% to ~84%.

2. **Signal Strength Not Perfectly Predictive**: Current correlation between signal_strength and returns is only 0.003 - very weak. Meta-labeler could learn non-linear patterns.

3. **Feature Rich Environment**: We have many features that could help the meta-labeler:
   - Signal type (tier, cohesion, leadership, combinations)
   - Signal strength
   - Fiedler change and percentage change
   - Leadership gap
   - Regime metrics (bull %, trend, momentum)
   - Theme characteristics (number of stocks, market cap distribution)
   - Time-based features (day of week, month, market regime)

4. **Current Precision is Good but Could Be Better**: 
   - Tier signals: 82.4% win rate
   - Cohesion signals: 84.2% win rate
   - But we still have 15-18% false positives even in best signal types

### Expected Improvements

If meta-labeler can filter out 50% of false positives:

**Current:**
- Win Rate: 67.7%
- Average Return: 13.30%
- Signals Taken: 15,643

**With Meta-Labeling (50% false positive reduction):**
- Win Rate: ~84% (estimated)
- Average Return: ~16-18% (estimated, as we avoid losses)
- Signals Taken: ~11,800 (25% reduction in signals, but higher quality)

**Sharpe Ratio Improvement:**
- Current: 1.00
- Expected: 1.3-1.5 (better risk-adjusted returns)

## Implementation Approach

### 1. Feature Engineering ✅ **IMPLEMENTED**

Feature engineering module (`feature_engineering.py`) extracts features from multiple sources:

**Primary Signal Features:**
- Signal type (tier, cohesion, leadership, combined)
- Signal strength
- Tier classification (1, 2, or None)
- Fiedler values (current, week_before, change, pct_change)
- Leadership gap

**UCS_LRS Technical Analysis Features** (from `/mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/com*.json`):
- **Overall Assessment**: score, score_percentage, rating
- **LRS Analysis**: current_lrs, slrs, alrs, signal_strength, positive flags
- **TStop Analysis**: close vs filter, filter margin, periods since positive
- **MACD Analysis**: histogram value, positive/increasing flags
- **Filter Status**: passes_filter, conditions passed/failed
- **Economic Context**: price momentum, volatility
- **Market Position**: price vs MA20/50/200

**Theme-Level Aggregated Features:**
- Theme average/median/std of assessment scores
- Theme LRS statistics (avg, positive ratio, signal strength)
- Theme TStop/MACD/Filter ratios
- Theme size and UCS coverage

**Regime Features:**
- Theme-level regime metrics (bull %, trend, momentum)

**Time Features:**
- Day of week, month, quarter
- Month-end, quarter-end flags

**Total Features**: ~50-70 features per signal

### 2. Target Variable

Binary classification:
- **Label = 1**: Signal led to positive return (take the trade)
- **Label = 0**: Signal led to negative return (skip the trade)

### 3. Model Selection

Options:
- **Random Forest**: Good for non-linear patterns, feature importance
- **XGBoost/LightGBM**: Better performance, handles imbalanced data
- **Neural Network**: If we have enough data

### 4. Training Strategy

- **Walk-Forward Training**: Train on historical data, test on future
- **Purged K-Fold**: Avoid look-ahead bias (de Prado's method)
- **Time-based splits**: Train on 2025-02 to 2025-06, test on 2025-07+

## Potential Challenges

1. **Data Requirements**: Need sufficient historical data (we have ~15K signals, which is good)
2. **Overfitting Risk**: Must use proper cross-validation (purged K-fold)
3. **Regime Changes**: Model may need retraining as market conditions change
4. **Complexity**: Adds another layer to the system

## Recommendation

### ✅ **YES - Implement Meta-Labeling**

**Priority: HIGH**

**Rationale:**
1. Current false positive rate (32.3%) is significant
2. Signal strength alone is not predictive (correlation = 0.003)
3. We have rich feature set (regime, theme characteristics, time features)
4. Expected improvement: Win rate 67.7% → 80-85%, Sharpe 1.0 → 1.3-1.5

**Implementation Plan:**
1. Create feature engineering module
2. Train meta-labeler on historical backtest results
3. Integrate into backtest engine
4. Compare performance: with vs without meta-labeling
5. If successful, integrate into live signal generation

## Next Steps

1. ✅ **Feature Engineering Module**: COMPLETE - Extracts ~50-70 features including UCS_LRS data
2. **Meta-Labeler Training**: Train binary classifier (XGBoost/Random Forest) on historical results
3. **Backtest Integration**: Add meta-labeling filter to backtest engine
4. **Backtest Comparison**: Run backtest with and without meta-labeling
5. **Performance Analysis**: Compare win rates, Sharpe ratios, signal counts
6. **Production Integration**: If successful, add to live signal generation

## Expected Timeline

- Feature Engineering: 1-2 days
- Model Training & Tuning: 2-3 days
- Backtest Integration: 1 day
- Testing & Validation: 1-2 days
- **Total: ~1 week**

## Success Metrics

Meta-labeling is successful if:
- ✅ Win rate improves by >10 percentage points (67.7% → >77%)
- ✅ Sharpe ratio improves by >0.2 (1.0 → >1.2)
- ✅ Average return improves or stays similar
- ✅ Signal reduction is <30% (still have enough trades)

