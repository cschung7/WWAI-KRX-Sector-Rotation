# Meta-Labeling Integration Guide

## Overview

This guide explains how to integrate meta-labeling into your existing workflow and how to extend it to other components.

## Current Integration

### ✅ Already Integrated

1. **Focused Portfolio Generation** (`backtest/generate_focused_portfolio.py`)
   - Meta-labeling applied automatically
   - Use `--no-meta-labeling` to disable

2. **Backtest Engine** (`backtest/backtest_engine.py`)
   - Optional meta-labeler parameter
   - Pass model path when initializing

## How to Integrate into Other Components

### Option 1: Use MetaLabelingFilter Class

```python
from backtest.meta_labeling_filter import MetaLabelingFilter

# Initialize (auto-loads latest model)
filter_obj = MetaLabelingFilter()

# Filter signals
filtered_signals = filter_obj.filter_signals(signals, signal_date)

# Or filter DataFrame
filtered_df = filter_obj.filter_dataframe(signals_df, date_col='date')
```

### Option 2: Use BacktestEngine with Meta-Labeling

```python
from backtest.backtest_engine import BacktestEngine

# Initialize with meta-labeler
engine = BacktestEngine(
    start_date='2025-02-01',
    end_date='2025-08-01',
    meta_labeler_path='backtest/models/meta_labeler_xgboost_20251113'
)

# Run backtest (signals automatically filtered)
results = engine.run_backtest()
```

### Option 3: Integrate into Weekly Analysis

Add to `run_weekly_analysis.sh`:

```bash
# After generating 4-tier classification, apply meta-labeling
echo -e "${YELLOW}[X/13]${NC} Applying meta-labeling filter..."
python3 backtest/apply_meta_labeling.py \
    --input-file data/4tier_themes_${DATE}.csv \
    --output-file data/4tier_themes_filtered_${DATE}.csv \
    --model backtest/models/meta_labeler_xgboost_20251113
```

## Integration Examples

### Example 1: Filter Investment Implications Report

```python
# In generate_investment_implications.py
from backtest.meta_labeling_filter import MetaLabelingFilter

# After loading tier data
if use_meta_labeling:
    filter_obj = MetaLabelingFilter()
    
    # Convert tier data to signal format
    signals = []
    for _, row in tier_df.iterrows():
        signal = {
            'theme': row['Theme'],
            'signal_type': 'tier',
            'signal_strength': calculate_strength(row),
            'tier': row['Tier'],
            # ... other fields
        }
        signals.append(signal)
    
    # Filter
    filtered_signals = filter_obj.filter_signals(signals, analysis_date)
    
    # Update tier_df with filtered results
    filtered_themes = {s['theme'] for s in filtered_signals}
    tier_df = tier_df[tier_df['Theme'].isin(filtered_themes)]
```

### Example 2: Filter Executive Dashboard

```python
# In generate_executive_dashboard.py
from backtest.meta_labeling_filter import MetaLabelingFilter

# After generating dashboard data
if use_meta_labeling:
    filter_obj = MetaLabelingFilter()
    
    # Filter themes before displaying
    dashboard_themes = filter_obj.filter_signals(
        dashboard_data['themes'],
        dashboard_date
    )
    
    # Update dashboard with filtered themes
    dashboard_data['themes'] = dashboard_themes
    dashboard_data['meta_labeling_applied'] = True
```

### Example 3: Add to Daily Analysis

```python
# In analyze_daily_abnormal_sectors.py
from backtest.meta_labeling_filter import MetaLabelingFilter

# After identifying abnormal sectors
if apply_meta_labeling:
    filter_obj = MetaLabelingFilter()
    
    # Convert sectors to signals
    signals = [{'theme': sector, ...} for sector in abnormal_sectors]
    
    # Filter
    filtered_signals = filter_obj.filter_signals(signals, today)
    
    # Use filtered sectors
    abnormal_sectors = [s['theme'] for s in filtered_signals]
```

## Configuration

### Environment Variables

Create `.env` or set environment variables:

```bash
# Meta-labeling configuration
META_LABELER_MODEL_PATH=backtest/models/meta_labeler_xgboost_20251113
META_LABELING_ENABLED=true
META_LABELING_USE_BASIC_FEATURES=true
```

### Config File

Add to `config.py`:

```python
# Meta-labeling configuration
META_LABELER_DIR = Path(__file__).parent / "backtest" / "models"
META_LABELING_ENABLED = True
META_LABELING_USE_BASIC_FEATURES = True  # Fast, for production
```

## Frontend Integration Options

### Option 1: REST API

Create `api/meta_labeling.py`:

```python
from fastapi import FastAPI, HTTPException
from backtest.meta_labeling_filter import MetaLabelingFilter

app = FastAPI()
filter_obj = MetaLabelingFilter()

@app.post("/api/filter-signals")
async def filter_signals(signals: List[Dict], date: str):
    try:
        signal_date = pd.to_datetime(date)
        filtered = filter_obj.filter_signals(signals, signal_date)
        return {"filtered_signals": filtered, "count": len(filtered)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Option 2: Streamlit Dashboard

Create `dashboard/meta_labeling_dashboard.py`:

```python
import streamlit as st
from backtest.meta_labeling_filter import MetaLabelingFilter
from backtest.monitor_meta_labeling import compare_with_baseline

st.title("Meta-Labeling Dashboard")

# Filter signals
if st.button("Filter Signals"):
    filter_obj = MetaLabelingFilter()
    signals = load_signals()
    filtered = filter_obj.filter_signals(signals, datetime.now())
    st.write(f"Filtered {len(signals)} → {len(filtered)} signals")

# Monitor performance
if st.button("Monitor Performance"):
    comparison = compare_with_baseline(baseline_df, filtered_df)
    st.metric("Win Rate Improvement", f"+{comparison['improvements']['win_rate_improvement_pp']:.1f} pp")
```

### Option 3: Web Dashboard (React/Vue)

Create API endpoints and build frontend:

```javascript
// Frontend API call
async function filterSignals(signals, date) {
  const response = await fetch('/api/filter-signals', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({signals, date})
  });
  return response.json();
}
```

## Best Practices

1. **Always Check Availability**: Handle cases where meta-labeler unavailable
2. **Log Filtering**: Log how many signals were filtered
3. **Monitor Performance**: Track metrics over time
4. **Retrain Regularly**: Update model monthly/quarterly
5. **A/B Testing**: Compare with/without meta-labeling

## Testing Integration

```python
# Test script
def test_meta_labeling_integration():
    from backtest.meta_labeling_filter import MetaLabelingFilter
    
    # Test initialization
    filter_obj = MetaLabelingFilter()
    assert filter_obj.meta_labeler is not None
    
    # Test filtering
    test_signals = [{'theme': 'Test', 'signal_type': 'tier', ...}]
    filtered = filter_obj.filter_signals(test_signals, datetime.now())
    assert len(filtered) <= len(test_signals)
    
    print("✅ Integration test passed")
```

## Troubleshooting

### Model Not Found
- Check `backtest/models/` directory
- Ensure model file exists
- Use `--model` flag to specify path

### Feature Extraction Fails
- Check UCS_LRS data availability
- Use `use_basic_features=True` for faster processing
- Verify theme mapping loaded correctly

### Performance Issues
- Use basic features instead of full features
- Reduce sample size for training
- Process in smaller batches

