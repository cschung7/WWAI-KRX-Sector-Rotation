# Meta-Labeling System - Quick Reference

## 🚀 Quick Start

```bash
# Generate portfolio with meta-labeling (default)
python3 backtest/generate_focused_portfolio.py --date 2025-11-13

# Train model
python3 backtest/train_meta_labeler.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv

# Monitor performance
python3 backtest/monitor_meta_labeling.py \
    --baseline-results baseline.csv \
    --filtered-results filtered.csv
```

## 📊 Results

- **Win Rate**: 67.7% → 81.2% (+13.5 pp)
- **Returns**: 13.30% → 19.93% (+49.9%)
- **Sharpe**: 1.00 → 1.52 (+51.5%)

## 📚 Documentation

- **META_LABELING_MASTER_SUMMARY.md** - Complete overview
- **AI_INSTRUCTION.md** - Apply to other countries
- **FRONTEND_RECOMMENDATIONS.md** - Frontend options
- **INTEGRATION_GUIDE.md** - Integration examples

## 🔧 Integration

```python
from backtest.meta_labeling_filter import MetaLabelingFilter

filter_obj = MetaLabelingFilter()
filtered_signals = filter_obj.filter_signals(signals, signal_date)
```

## 🌍 Apply to Other Countries

See `AI_INSTRUCTION.md` for step-by-step guide.

## 📈 Status: ✅ PRODUCTION READY
