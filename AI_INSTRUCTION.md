# AI Instruction: Applying Meta-Labeling to Other Countries

## Purpose

This document provides step-by-step instructions for applying the meta-labeling system to other country sector rotation projects (e.g., Sector-Rotation-USA, Sector-Rotation-Japan).

## Prerequisites

1. Existing sector rotation project structure
2. Backtest results available
3. Feature data sources (Fiedler, regime, UCS_LRS if available)
4. Python environment with required packages

## Step-by-Step Implementation

### Step 1: Copy Core Files

Copy these files from `Sector-Rotation-KRX/backtest/` to the target country's backtest directory:

```bash
# Core system files
cp Sector-Rotation-KRX/backtest/meta_labeler.py Sector-Rotation-{COUNTRY}/backtest/
cp Sector-Rotation-KRX/backtest/feature_engineering.py Sector-Rotation-{COUNTRY}/backtest/
cp Sector-Rotation-KRX/backtest/meta_labeling_filter.py Sector-Rotation-{COUNTRY}/backtest/

# Training and evaluation
cp Sector-Rotation-KRX/backtest/train_meta_labeler.py Sector-Rotation-{COUNTRY}/backtest/
cp Sector-Rotation-KRX/backtest/compare_meta_labeling_simple.py Sector-Rotation-{COUNTRY}/backtest/

# Monitoring tools
cp Sector-Rotation-KRX/backtest/monitor_meta_labeling.py Sector-Rotation-{COUNTRY}/backtest/
cp Sector-Rotation-KRX/backtest/track_performance.py Sector-Rotation-{COUNTRY}/backtest/
cp Sector-Rotation-KRX/backtest/retrain_meta_labeler.sh Sector-Rotation-{COUNTRY}/backtest/
```

### Step 2: Update Configuration

#### 2.1 Update `feature_engineering.py`

Modify paths to match the target country:

```python
# In feature_engineering.py, update:
class FeatureEngineer:
    def __init__(self, ucs_lrs_dir: Optional[Path] = None):
        if ucs_lrs_dir is None:
            # Update this path for target country
            self.ucs_lrs_dir = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/Filter/UCS_LRS")
        else:
            self.ucs_lrs_dir = Path(ucs_lrs_dir)
```

#### 2.2 Update `config.py` (if exists)

Ensure paths point to target country data:

```python
# Update these paths
AUTOGLUON_BASE_DIR = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}")
DB_FILE = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/DB/db_final.csv")
REGIME_DIR = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/regime_data")
```

### Step 3: Adapt Feature Engineering

#### 3.1 Check Data Availability

Verify what data sources are available:

```python
# Check for UCS_LRS data
ucs_files = list(Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/Filter/UCS_LRS").glob("com*.json"))
print(f"UCS_LRS files: {len(ucs_files)}")

# Check for regime data
regime_files = list(Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/regime_data").glob("*.csv"))
print(f"Regime files: {len(regime_files)}")

# Check database
db_file = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/DB/db_final.csv")
print(f"Database exists: {db_file.exists()}")
```

#### 3.2 Adapt Feature Extraction

If data structure differs, update `extract_ticker_features()`:

```python
# Example: If UCS_LRS structure is different
def extract_ticker_features(self, ticker: str, date: datetime) -> Dict:
    features = {}
    
    # Adapt based on actual data structure
    ucs_data = self.load_ucs_data_for_date(date)
    
    # Check structure and adapt accordingly
    if ticker in ucs_data:
        ticker_data = ucs_data[ticker]
        # Extract features based on actual structure
        # ...
    
    return features
```

### Step 4: Generate Training Data

#### 4.1 Run Backtest

Generate backtest results for training:

```bash
cd Sector-Rotation-{COUNTRY}
python3 backtest/run_backtest.py \
    --start-date YYYY-MM-DD \
    --end-date YYYY-MM-DD \
    --holding-period 12
```

This creates `backtest/results/signal_performance_YYYYMMDD.csv`

#### 4.2 Verify Results Format

Ensure results CSV has required columns:
- `signal_date` or `date`
- `theme` or `sector`
- `signal_type`
- `signal_strength`
- `total_return`
- `tier` (if available)
- `fiedler_change` (if available)
- `leadership_gap` (if available)

### Step 5: Train Meta-Labeler

#### 5.1 Initial Training (Quick Test)

```bash
python3 backtest/train_meta_labeler.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --model-type xgboost \
    --sample-size 5000 \
    --skip-ucs
```

#### 5.2 Full Training

```bash
python3 backtest/train_meta_labeler.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --model-type xgboost \
    --sample-size 10000 \
    --use-cv
```

### Step 6: Validate Model

#### 6.1 Compare Performance

```bash
python3 backtest/compare_meta_labeling_simple.py \
    --results-file backtest/results/signal_performance_YYYYMMDD.csv \
    --meta-labeler backtest/models/meta_labeler_xgboost_YYYYMMDD
```

#### 6.2 Check Metrics

Expected improvements:
- Win Rate: +5-15 percentage points
- Average Return: +10-50%
- Sharpe Ratio: +0.1-0.5

### Step 7: Integrate into Production

#### 7.1 Update Portfolio Generation

Modify `generate_focused_portfolio.py` or equivalent:

```python
from backtest.meta_labeling_filter import MetaLabelingFilter

# After collecting signals
if use_meta_labeling:
    filter_obj = MetaLabelingFilter()
    filtered_signals = filter_obj.filter_signals(signals, signal_date)
    signals = filtered_signals
```

#### 7.2 Update Weekly Analysis

Add to `run_weekly_analysis.sh`:

```bash
# After generating reports, apply meta-labeling
echo "Applying meta-labeling filter..."
python3 backtest/apply_meta_labeling_to_reports.py \
    --date ${DATE} \
    --model backtest/models/meta_labeler_xgboost_YYYYMMDD
```

### Step 8: Set Up Monitoring

#### 8.1 Create Monitoring Schedule

Add to cron or scheduler:

```bash
# Weekly monitoring
0 9 * * 1 cd Sector-Rotation-{COUNTRY} && \
    python3 backtest/monitor_meta_labeling.py \
        --baseline-results baseline.csv \
        --filtered-results filtered.csv

# Monthly retraining
0 2 1 * * cd Sector-Rotation-{COUNTRY} && \
    ./backtest/retrain_meta_labeler.sh --full
```

## Country-Specific Adaptations

### USA Market

**Considerations:**
- Larger market, more sectors
- May need larger sample size for training
- Different data sources (e.g., S&P sectors)

**Adaptations:**
```python
# Update sector/ticker mapping
# Update data paths
# Adjust feature extraction for US data structure
```

### Japan Market

**Considerations:**
- Different market structure
- May have different regime data format
- UCS_LRS data may be structured differently

**Adaptations:**
```python
# Adapt feature extraction
# Update ticker mapping
# Adjust for Japanese market characteristics
```

## Troubleshooting

### Issue: Feature Extraction Fails

**Solution:**
1. Check data structure matches expected format
2. Use `--skip-ucs` for initial testing
3. Adapt `extract_ticker_features()` for actual data structure

### Issue: Model Performance Poor

**Solution:**
1. Increase training sample size
2. Include more features (if available)
3. Check data quality
4. Try different model types (Random Forest vs XGBoost)

### Issue: Integration Breaks Existing Code

**Solution:**
1. Use `--no-meta-labeling` flag to disable
2. Make meta-labeling optional (graceful degradation)
3. Test thoroughly before production deployment

## Validation Checklist

Before deploying to production:

- [ ] Core files copied and paths updated
- [ ] Feature engineering adapted for country data
- [ ] Training data generated and validated
- [ ] Model trained and validated
- [ ] Performance improvements confirmed (>5 pp win rate)
- [ ] Integration tested in portfolio generation
- [ ] Monitoring tools configured
- [ ] Documentation updated

## Expected Timeline

- **Setup**: 1-2 days (copy files, update paths)
- **Adaptation**: 2-3 days (adapt feature engineering)
- **Training**: 1 day (generate data, train model)
- **Validation**: 1 day (test and compare)
- **Integration**: 1-2 days (integrate into workflow)
- **Total**: ~1 week

## Success Criteria

Meta-labeling is successfully applied when:
- ✅ Model trains without errors
- ✅ Win rate improves by >5 percentage points
- ✅ Sharpe ratio improves by >0.1
- ✅ Integration works without breaking existing code
- ✅ Monitoring shows consistent improvements

## Support Files

Reference these files for implementation:
- `IMPLEMENTATION_SUMMARY.md` - What was built
- `INTEGRATION_GUIDE.md` - How to integrate
- `PRODUCTION_INTEGRATION.md` - Production setup
- `NEXT_STEPS_IMPLEMENTATION.md` - Monitoring tools

## Notes

- Start with basic features (skip UCS_LRS) for faster implementation
- Test thoroughly before full deployment
- Monitor performance closely in first month
- Retrain monthly with new data
- Adapt feature set based on available data

