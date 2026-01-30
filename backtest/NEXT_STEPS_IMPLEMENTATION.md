# Next Steps Implementation ✅

## Overview

Monitoring and maintenance tools have been created to support meta-labeling in production.

## Tools Created

### 1. **Performance Monitoring** (`monitor_meta_labeling.py`)

**Purpose**: Track key metrics for meta-labeling performance

**Usage**:
```bash
python3 backtest/monitor_meta_labeling.py \
    --baseline-results backtest/results/baseline_YYYYMMDD.csv \
    --filtered-results backtest/results/filtered_YYYYMMDD.csv \
    --output backtest/monitoring/report_YYYYMMDD.md
```

**Output**:
- Monitoring report with comparison metrics
- Status assessment (Excellent/Good/Marginal/Needs Review)
- Detailed baseline vs filtered metrics

### 2. **Model Retraining Automation** (`retrain_meta_labeler.sh`)

**Purpose**: Automate retraining process with latest backtest results

**Usage**:
```bash
# Quick retrain (sample, basic features)
./backtest/retrain_meta_labeler.sh

# Full dataset retrain
./backtest/retrain_meta_labeler.sh --full

# With UCS_LRS features
./backtest/retrain_meta_labeler.sh --with-ucs

# Full dataset with UCS features
./backtest/retrain_meta_labeler.sh --full --with-ucs
```

**Features**:
- Automatically finds latest backtest results
- Supports sample or full dataset
- Supports basic or full features
- Includes cross-validation

### 3. **Performance Tracking** (`track_performance.py`)

**Purpose**: Maintain history of performance metrics over time

**Usage**:
```bash
# Add performance entry
python3 backtest/track_performance.py --add comparison_results.json

# View trends
python3 backtest/track_performance.py --trends
```

**Features**:
- Maintains performance history (last 100 entries)
- Tracks trends over time
- Provides status assessment

## Recommended Workflow

### Weekly Monitoring

1. **Generate Portfolio with Meta-Labeling**:
```bash
python3 backtest/generate_focused_portfolio.py --date YYYY-MM-DD
```

2. **Compare Performance** (if baseline available):
```bash
python3 backtest/compare_meta_labeling_simple.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --meta-labeler backtest/models/meta_labeler_xgboost_YYYYMMDD
```

3. **Monitor Performance**:
```bash
python3 backtest/monitor_meta_labeling.py \
    --baseline-results baseline.csv \
    --filtered-results filtered.csv
```

4. **Track Performance**:
```bash
python3 backtest/track_performance.py --add comparison_results.json
python3 backtest/track_performance.py --trends
```

### Monthly Retraining

1. **Run Backtest** to generate new results:
```bash
python3 backtest/run_backtest.py \
    --start-date YYYY-MM-DD \
    --end-date YYYY-MM-DD
```

2. **Retrain Model**:
```bash
./backtest/retrain_meta_labeler.sh --full
```

3. **Compare New vs Old Model**:
```bash
# Test new model
python3 backtest/compare_meta_labeling_simple.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --meta-labeler backtest/models/meta_labeler_xgboost_NEWDATE

# Compare with old model
python3 backtest/compare_meta_labeling_simple.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --meta-labeler backtest/models/meta_labeler_xgboost_OLDDATE
```

4. **Deploy if Better**: If new model performs better, update production to use it

## Key Metrics to Track

### Performance Metrics
- **Signal Reduction Rate**: Should be ~20-30%
- **Win Rate Improvement**: Should be >5 percentage points
- **Average Return Improvement**: Should be >10%
- **Sharpe Ratio Improvement**: Should be >0.1

### Model Health Metrics
- **Model Age**: Retrain if >3 months old
- **Performance Degradation**: Retrain if metrics declining
- **Data Drift**: Retrain if market conditions changed significantly

## Alert Thresholds

### Excellent Performance
- Win Rate Improvement: >10 pp
- Sharpe Improvement: >0.2
- Status: Continue monitoring

### Good Performance
- Win Rate Improvement: 5-10 pp
- Sharpe Improvement: 0.1-0.2
- Status: Continue monitoring

### Marginal Performance
- Win Rate Improvement: 0-5 pp
- Sharpe Improvement: 0-0.1
- Status: Review model, consider retraining

### Needs Review
- Win Rate Improvement: <0 pp
- Sharpe Improvement: <0
- Status: **Retrain immediately**

## Automation Opportunities

### Cron Job for Weekly Monitoring

```bash
# Add to crontab
0 9 * * 1 cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && \
    python3 backtest/generate_focused_portfolio.py --date $(date +%Y-%m-%d) && \
    python3 backtest/monitor_meta_labeling.py \
        --baseline-results backtest/results/baseline_$(date +%Y%m%d).csv \
        --filtered-results backtest/results/filtered_$(date +%Y%m%d).csv
```

### Monthly Retraining

```bash
# Add to crontab (first day of month)
0 2 1 * * cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && \
    ./backtest/retrain_meta_labeler.sh --full
```

## Files Created

- `backtest/monitor_meta_labeling.py` - Performance monitoring
- `backtest/retrain_meta_labeler.sh` - Automated retraining
- `backtest/track_performance.py` - Performance history tracking
- `backtest/NEXT_STEPS_IMPLEMENTATION.md` - This document

## Status

✅ **All Next Steps Tools Implemented**

The system is now ready for:
1. ✅ Production use with meta-labeling
2. ✅ Performance monitoring
3. ✅ Automated retraining
4. ✅ Performance tracking over time

## Next Actions

1. **Set up monitoring**: Run first monitoring report
2. **Schedule retraining**: Set up monthly retraining
3. **Track performance**: Start building performance history
4. **Iterate**: Use insights to improve model

