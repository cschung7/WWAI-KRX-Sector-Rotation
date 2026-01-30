# Sector Rotation Analysis Framework - Korean Market (KRX)

**Location**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX`

## Overview

Early detection system for sector rotation opportunities in the Korean stock market using three-layer analysis:

1. **Cohesion Layer**: Network formation via Fiedler eigenvalues
2. **Regime Layer**: Bull/Bear states via Hidden Markov Models  
3. **Market Cap Layer**: Small → Mid → Large cap leadership progression

**Investment Horizon**: 12-18 months early detection before themes become mainstream investable.

---

## Quick Start

```bash
# Navigate to project
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX

# Generate weekly synthesis report
./run_weekly_analysis.sh

# View report
cat reports/weekly_synthesis_$(date +%Y%m%d).md
```

---

## Key Features

✅ **4-Tier Investment Framework**
- TIER 1: Buy NOW (baseline >15, change >5)
- TIER 2: Accumulate 6-12mo (baseline 5-15, change >2)  
- TIER 3: Research 12-18mo (baseline 2-8, change >1.5)
- TIER 4: Monitor 18-24mo (baseline 0.5-3, high % change)

✅ **Weekly Synthesis Reporting**
- Automated pipeline combining all analysis components
- Date-specific reports with actionable recommendations
- Portfolio allocation guidance
- Week-over-week comparison

✅ **Timing Predictions**
- Estimates when TIER 3 themes become TIER 1 investable
- Velocity-based forecasting with confidence intervals
- Fast/Medium/Slow classification

✅ **Detailed Sector Rankings**
- Ticker-level analysis within each theme
- Cohesion × Regime × Market Cap composite scoring
- Bull/Bear regime status by market cap tier

---

## System Components

### Core Scripts

- `run_weekly_analysis.sh` - Automated weekly pipeline
- `generate_weekly_synthesis.py` - Report generator
- `analyze_4_tier_themes.py` - 4-tier classifier
- `predict_timing.py` - Timing predictor
- `generate_sector_rankings.py` - Detailed sector analysis

### Data

- 273 CSV files in `data/` directory
- Weekly cohesion data, 4-tier classifications
- Sector rankings, timing predictions

### Reports

- Weekly synthesis reports in `reports/`
- Markdown format, 190+ lines per report
- Includes executive summary, actionable items, risk alerts

### Documentation

- `WEEKLY_REPORTING_GUIDE.md` (11KB) - Complete usage guide
- `SYNTHESIS_REPORTING_COMPLETE.md` (14KB) - System summary
- `TIMING_ESTIMATION_BRAINSTORM.md` (18KB) - Methodology
- `Jobs/generate_4_tier_investment_theme.md` (27KB) - Framework guide
- `Jobs/how_to_run_sector_tickers_ordering.md` (16KB) - Sector rankings guide
- `LOCATION_UPDATE.md` - Move history
- `QUICK_REFERENCE.md` - One-liner commands

---

## Current Week Snapshot (2025-10-27)

```
TIER 1 (BUY NOW):             2 themes  → 철도, 반도체 장비
TIER 2 (ACCUMULATE 6-12mo):  11 themes  → 온디바이스 AI, 모바일솔루션, etc.
TIER 3 (RESEARCH 12-18mo):   14 themes  → 해운, 조림사업, etc.
TIER 4 (MONITOR 18-24mo):     8 themes  → 손해보험, 맥신(MXene), etc.

Total themes tracked: 35
```

---

## Usage Examples

### Generate Weekly Report

```bash
# For today
./run_weekly_analysis.sh

# For specific date
./run_weekly_analysis.sh 20251027
```

### Analyze Specific Theme

```bash
python3 generate_sector_rankings.py --sector "철도"
python3 generate_sector_rankings.py --sector "해운"
```

### Check Timing Predictions

```bash
cat data/tier3_timing_predictions_$(date +%Y%m%d).json | grep -A 10 "해운"
```

### View TIER 1 Themes Only

```bash
grep -A 30 "TIER 1: BUY NOW" reports/weekly_synthesis_$(date +%Y%m%d).md
```

---

## Automation

Set up weekly cron job:

```bash
crontab -e

# Add:
0 18 * * 0 cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && ./run_weekly_analysis.sh >> logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

---

## Investment Strategy

### Portfolio Allocation

- **TIER 1 (50-60%)**: Immediate investment in established themes
- **TIER 2 (30-35%)**: Dollar-cost averaging over 6 months
- **TIER 3 (10-15%)**: Small pilot positions in fast-moving themes
- **CASH (0-5%)**: Opportunistic entries on pullbacks

### Weekly Workflow

**Sunday 18:00**: Run analysis and review synthesis report
**Monday**: Execute TIER 1 buy orders (3-5 large-cap stocks per theme)
**Tuesday-Friday**: Set up DCA for TIER 2 themes
**Monthly**: Deep research on top 3 TIER 3 themes

---

## Technical Details

### Three-Layer Framework

**Layer 1 - Cohesion (Fiedler Values)**:
- Measures network connectivity between stocks in a theme
- Range: 0 (disconnected) to N (fully connected)
- Threshold: >15 indicates strong established network

**Layer 2 - Regime (Hidden Markov Models)**:
- Bull Quiet, Bear Quiet, Transition, Ranging states
- Calculated per ticker with probability distribution
- Large-cap bull regime = mainstream investability

**Layer 3 - Market Cap Leadership**:
- Tier 1: ≥5T won (large-cap leaders)
- Tier 2: 1-5T won (mid-cap momentum)
- Tier 3: <1T won (small-cap early detection)

### Small → Large Cap Progression

**Pattern**: Small-caps detect opportunities 12-18 months before large-caps

**Example** (해운/Shipping):
- Small-cap (흥아해운 0.4T): Bull regime ✅
- Mid-cap (팬오션 2.1T): Bear regime ❌
- Large-cap (HMM 19.4T): Bear regime ❌

**Implication**: 12-18 months until HMM flips to bull = TIER 3 research opportunity

---

## Data Sources

- **Cohesion**: Weekly Fiedler eigenvalue calculations on correlation matrices
- **Regime**: AutoGluon LRS (Leading Regime Score) analysis
- **Market Cap**: KRX market data (DB units: 10 = 1T won)
- **Themes**: Naver Finance theme classifications

## Self-Contained Project Structure

This project is **self-contained** with all internal data and scripts within the project directory:

- ✅ All Python scripts use `config.py` for path management
- ✅ Local data files stored in `data/` directory
- ✅ All outputs go to `data/` and `reports/` directories
- ✅ External dependencies are configurable via environment variables

**External Dependencies**: See `EXTERNAL_DEPENDENCIES.md` for required external data sources and how to configure them.

---

## System Status

✅ **Production-Ready**: All components tested and working
✅ **Data Quality**: 273 CSV files, 35 themes tracked
✅ **Documentation**: 60KB+ comprehensive guides
✅ **Automation**: Ready for weekly cron execution

---

## Configuration

All paths are managed through `config.py`. To check configuration status:

```bash
python3 config.py
```

To override external data paths:

```bash
export KRX_PRICE_DATA_DIR=/path/to/price/data
export AUTOGLUON_BASE_DIR=/path/to/autogluon
```

See `EXTERNAL_DEPENDENCIES.md` for details on external dependencies.

## Support

For questions or issues, refer to:

1. `WEEKLY_REPORTING_GUIDE.md` - Complete usage documentation
2. `EXTERNAL_DEPENDENCIES.md` - External data requirements
3. `Jobs/generate_4_tier_investment_theme.md` - 4-tier framework
4. `Jobs/how_to_run_sector_tickers_ordering.md` - Sector rankings
5. `QUICK_REFERENCE.md` - One-liner commands

---

## Project History

**Original Location**: `countryrisk/KRX`  
**First Rename**: `countryrisk/Sector-Rotation`  
**Final Location**: `Sector-Rotation-KRX` (2025-10-28)

**Rationale**: Top-level project with clear naming emphasizing Korean market focus.

---

## License & Credits

**Framework**: Three-Layer Sector Rotation Analysis  
**Market**: Korea Exchange (KRX)  
**Development**: 2025-10-28  
**Status**: Production-ready for investment decision support

---

**Start Using**:
```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
./run_weekly_analysis.sh
cat reports/weekly_synthesis_$(date +%Y%m%d).md
```
