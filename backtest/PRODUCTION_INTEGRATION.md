# Meta-Labeling Production Integration ✅

## Integration Complete

Meta-labeling has been successfully integrated into the production signal generation workflow.

## Integration Points

### 1. **Focused Portfolio Generation** (`generate_focused_portfolio.py`)

**Status**: ✅ Integrated

**Changes**:
- Added `MetaLabelingFilter` import
- Applied meta-labeling filter after signal collection, before tier/cohesion filtering
- Added `--no-meta-labeling` flag to disable if needed

**Usage**:
```bash
# With meta-labeling (default)
python3 backtest/generate_focused_portfolio.py --date 2025-11-13

# Without meta-labeling
python3 backtest/generate_focused_portfolio.py --date 2025-11-13 --no-meta-labeling
```

### 2. **Meta-Labeling Filter Module** (`meta_labeling_filter.py`)

**Status**: ✅ Created

**Features**:
- `MetaLabelingFilter` class for production use
- Automatic loading of latest model
- Support for basic features (fast) or full features (with UCS_LRS)
- Signal filtering and DataFrame filtering methods

**Usage**:
```python
from meta_labeling_filter import MetaLabelingFilter

# Initialize (loads latest model automatically)
filter_obj = MetaLabelingFilter()

# Filter signals
filtered_signals = filter_obj.filter_signals(signals, signal_date)

# Or filter DataFrame
filtered_df = filter_obj.filter_dataframe(signals_df)
```

## Workflow Integration

### Current Production Workflow

1. **Weekly Analysis** (`run_weekly_analysis.sh`)
   - Generates cohesion analysis
   - Generates 4-tier classification
   - Generates investment reports

2. **Portfolio Generation** (NEW: with meta-labeling)
   - `generate_focused_portfolio.py` now applies meta-labeling
   - Filters out false positives before tier/cohesion filtering
   - Improves portfolio quality

### Expected Improvements in Production

Based on backtest results:
- **Win Rate**: 67.7% → 81.2% (+13.5 pp)
- **Average Return**: 13.30% → 19.93% (+49.9%)
- **Sharpe Ratio**: 1.00 → 1.52 (+51.5%)
- **Signal Reduction**: ~25% (higher quality)

## Model Management

### Model Location
- **Directory**: `backtest/models/`
- **Naming**: `meta_labeler_{type}_{date}.pkl`
- **Latest Model**: `meta_labeler_xgboost_20251113.pkl`

### Model Updates

To retrain with new data:
```bash
python3 backtest/train_meta_labeler.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --model-type xgboost \
    --sample-size 10000
```

### Model Selection

The `MetaLabelingFilter` automatically loads the latest model by default. To use a specific model:
```python
filter_obj = MetaLabelingFilter(model_path='backtest/models/meta_labeler_xgboost_20251113')
```

## Configuration

### Feature Extraction

- **Basic Features** (default): Signal + time features only (fast, ~19 features)
- **Full Features**: Includes UCS_LRS data (slower, ~50-70 features)

To use full features:
```python
filtered_signals = filter_obj.filter_signals(signals, signal_date, use_basic_features=False)
```

### Performance Considerations

- **Basic Features**: Fast, suitable for production
- **Full Features**: Slower, may require more memory
- **Recommendation**: Use basic features for production, full features for retraining

## Monitoring

### Key Metrics to Track

1. **Signal Reduction Rate**: Should be ~20-30%
2. **Win Rate**: Should improve from baseline
3. **Average Return**: Should improve from baseline
4. **Model Performance**: Monitor for degradation over time

### Retraining Schedule

**Recommended**: Retrain monthly or quarterly
- Use latest backtest results
- Compare new model performance vs current
- Deploy if performance is better

## Testing

### Test Meta-Labeling Filter

```bash
python3 backtest/meta_labeling_filter.py --test
```

### Compare With/Without Meta-Labeling

```bash
# Generate portfolio with meta-labeling
python3 backtest/generate_focused_portfolio.py --date 2025-11-13

# Generate portfolio without meta-labeling
python3 backtest/generate_focused_portfolio.py --date 2025-11-13 --no-meta-labeling

# Compare results
```

## Rollback Plan

If meta-labeling causes issues:

1. **Disable in code**: Use `--no-meta-labeling` flag
2. **Remove integration**: Comment out meta-labeling code
3. **Fallback**: System works without meta-labeling (graceful degradation)

## Next Steps

1. ✅ **Integration Complete**: Meta-labeling integrated into focused portfolio
2. **Monitor Performance**: Track metrics in production
3. **Retrain Periodically**: Update model with new data
4. **Expand Integration**: Add to other portfolio generation scripts if needed

## Files Modified

- `backtest/generate_focused_portfolio.py` - Added meta-labeling filter
- `backtest/meta_labeling_filter.py` - New production filter module

## Files Created

- `backtest/PRODUCTION_INTEGRATION.md` - This document

## Dependencies

- `meta_labeler.py` - Core meta-labeler
- `feature_engineering.py` - Feature extraction
- Trained model in `backtest/models/`

## Notes

- Meta-labeling is **optional** - system works without it
- Filtering happens **after** signal generation, **before** tier/cohesion filtering
- Uses **basic features** by default for speed
- **Graceful degradation** if model unavailable

