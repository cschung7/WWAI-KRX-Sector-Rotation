# Daily Run Guide - Abnormal Sector Analysis

## Overview

The **daily abnormal sector analysis** identifies sectors showing unusual Fiedler eigenvalue patterns compared to the weekly baseline. This helps detect:
- Unusual sector strengthening (>+20% Fiedler increase)
- Unusual sector weakening (<-20% Fiedler decrease)
- Sector disconnections (loss of cohesion)
- New sector formations (new cohesion emergence)

## Daily Script

**File**: `Jobs/analyze_daily_abnormal_sectors.py`

**Purpose**: 
- Compares today's Fiedler values against the most recent weekly baseline
- Identifies abnormal sectors that deviate significantly from normal patterns
- Generates daily reports with actionable insights

## How to Run

### Option 1: Direct Python Execution

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
python3 Jobs/analyze_daily_abnormal_sectors.py
```

### Option 2: Using Shell Script (Recommended)

```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
./Jobs/run_daily_abnormal_sectors.sh
```

The shell script provides:
- Automatic logging to `logs/daily_abnormal_sectors_YYYYMMDD.log`
- Better error handling
- Summary of generated files

## Output Files

For each run (date: YYYYMMDD):

1. **CSV Data**: `data/abnormal_sectors_YYYYMMDD.csv`
   - Contains all abnormal sectors with metrics
   - Columns: theme, abnormality, fiedler_today, fiedler_baseline, change, etc.

2. **Markdown Report**: `reports/ABNORMAL_SECTORS_YYYYMMDD.md`
   - Comprehensive analysis report
   - Categorized by abnormality type
   - Investment implications

3. **Log File**: `logs/daily_abnormal_sectors_YYYYMMDD.log`
   - Execution log with timestamps
   - Error messages if any

## Prerequisites

Before running daily analysis, ensure:

1. **Weekly baseline exists**: The script automatically finds the most recent `weekly_cohesion_change_YYYYMMDD.csv` file in the `data/` directory
2. **Price data available**: External price data directory must be accessible (configured via `KRX_PRICE_DATA_DIR` env var or default path)
3. **Theme mapping exists**: `data/theme_to_tickers.json` must be present

## Automation (Cron Job)

To run daily at 18:30 KST (after market close):

```bash
crontab -e
```

Add this line:

```cron
30 18 * * * cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && ./Jobs/run_daily_abnormal_sectors.sh >> logs/cron_daily_abnormal_$(date +\%Y\%m\%d).log 2>&1
```

Or for 18:00 KST:

```cron
0 18 * * * cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && ./Jobs/run_daily_abnormal_sectors.sh >> logs/cron_daily_abnormal_$(date +\%Y\%m\%d).log 2>&1
```

## Configuration

The script uses `config.py` for path management. Key settings:

- **PRICE_DATA_DIR**: Price data location (default: `/mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED`)
- **DATA_DIR**: Local data directory (default: `data/`)
- **REPORTS_DIR**: Reports directory (default: `reports/`)

Override via environment variables:

```bash
export KRX_PRICE_DATA_DIR=/path/to/price/data
```

## Abnormality Thresholds

The script identifies abnormalities using these thresholds:

- **LARGE_INCREASE**: Fiedler increase ≥ +20%
- **LARGE_DECREASE**: Fiedler decrease ≤ -20%
- **DISCONNECTION**: Fiedler drops from ≥1.0 to <0.1
- **NEW_CONNECTION**: Fiedler jumps from <0.1 to ≥3.0

## Example Output

```
================================================================================
KRX DAILY ABNORMAL SECTOR ANALYSIS
================================================================================
Analysis Date: 2025-11-11
Lookback Window: 60 days
Correlation Threshold: 0.25
Price Data: /mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED
================================================================================

1. Loading Naver theme structure...
   Loaded 35 themes

2. Loading weekly baseline (20251027)...
   Loaded baseline for 35 themes

3. Loading daily price data...
   Loaded 2500 stocks with valid data

...

SUMMARY
================================================================================
Total themes analyzed: 35
Abnormal sectors found: 3

Abnormality Breakdown:
  LARGE_INCREASE: 1
  LARGE_DECREASE: 1
  NEW_CONNECTION: 1
```

## Troubleshooting

### Error: Baseline file not found

**Solution**: Run the weekly analysis first to generate baseline data:
```bash
./run_weekly_analysis.sh
```

### Error: Price data not found

**Solution**: Check that `KRX_PRICE_DATA_DIR` is set correctly:
```bash
python3 config.py  # Check configuration
export KRX_PRICE_DATA_DIR=/correct/path/to/data
```

### Error: Theme mapping not found

**Solution**: Generate theme mapping:
```bash
python3 Jobs/build_theme_to_ticker_mapping.py
```

## Integration with Weekly Analysis

The daily analysis complements the weekly analysis:

- **Weekly**: Comprehensive sector rotation analysis, 4-tier classification, timing predictions
- **Daily**: Real-time monitoring of abnormal sector movements

Run weekly analysis on Sundays, daily analysis on weekdays for continuous monitoring.

