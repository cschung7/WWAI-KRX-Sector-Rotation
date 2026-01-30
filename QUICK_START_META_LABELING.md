# Meta-Labeling Quick Start Guide

## 🚀 5-Minute Quick Start

### 1. Generate Portfolio with Meta-Labeling

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
python3 backtest/generate_focused_portfolio.py --date 2025-11-13
```

**That's it!** Meta-labeling is automatically applied.

### 2. Check Results

```bash
# View filtered portfolio
cat backtest/reports/focused_portfolio_20251113.md
```

### 3. Monitor Performance (Optional)

```bash
python3 backtest/monitor_meta_labeling.py \
    --baseline-results backtest/results/signal_performance_20251113.csv \
    --filtered-results backtest/comparisons/filtered_results_*.csv
```

## 📊 What to Expect

- **Win Rate**: ~81% (vs 68% without filtering)
- **Returns**: ~20% average (vs 13% without)
- **Signal Reduction**: ~25% (higher quality)

## 🔧 Advanced Usage

### Disable Meta-Labeling

```bash
python3 backtest/generate_focused_portfolio.py \
    --date 2025-11-13 \
    --no-meta-labeling
```

### Train New Model

```bash
python3 backtest/train_meta_labeler.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --model-type xgboost \
    --sample-size 10000
```

### Retrain Model

```bash
./backtest/retrain_meta_labeler.sh --full
```

## 📚 More Information

- **META_LABELING_MASTER_SUMMARY.md** - Complete overview
- **AI_INSTRUCTION.md** - Apply to other countries
- **INTEGRATION_GUIDE.md** - Integration examples

## ✅ Status

**Ready to use!** Meta-labeling is integrated and working.
