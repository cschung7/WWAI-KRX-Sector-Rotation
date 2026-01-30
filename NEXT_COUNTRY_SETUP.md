# Next Country Setup Guide

## Current Status Summary

### ✅ **Sector-Rotation-KRX** (Korea) - COMPLETE
- ✅ Full 3-layer analysis system
- ✅ 4-tier investment classification
- ✅ Meta-labeling system with backtesting
- ✅ Dashboard (FastAPI + React/HTML)
- ✅ Weekly analysis automation
- ✅ All reports and visualizations

### 📊 **Sector-Rotation-USA** - PARTIAL
- ✅ Basic structure exists
- ✅ 4-tier sector analysis
- ✅ Data processing scripts
- ❌ **Missing**: Dashboard
- ❌ **Missing**: Meta-labeling system
- ❌ **Missing**: Backtesting framework
- ❌ **Missing**: Dashboard management scripts

### 🌏 **Other Countries** - BASIC SETUP
- **Sector-Rotation-China**: Basic structure
- **Sector-Rotation-Japan**: Basic structure  
- **Sector-Rotation-India**: Basic structure
- **Sector-Rotation-Hongkong**: Basic structure
- **Sector-Rotation-Crypto**: Basic structure

---

## Recommended Next Steps

### Option 1: Complete USA Setup (Recommended)
**Why**: USA has the most complete structure after KRX, making it easiest to enhance.

**What to add**:
1. Copy dashboard from KRX → USA
2. Copy meta-labeling system from KRX → USA
3. Copy backtesting framework from KRX → USA
4. Adapt configuration for USA market
5. Update data paths and market-specific settings

**Estimated Time**: 2-3 hours

### Option 2: Set Up New Country from Scratch
**Choose a country**: China, Japan, India, Hong Kong, or Crypto

**What to do**:
1. Copy entire KRX structure as template
2. Update all market-specific settings
3. Adapt data sources
4. Configure sector/theme classifications
5. Set up data pipelines

**Estimated Time**: 4-6 hours

---

## Quick Setup Commands

### For USA (Recommended)

```bash
# 1. Copy dashboard
cp -r Sector-Rotation-KRX/dashboard Sector-Rotation-USA/

# 2. Copy backtest system
cp -r Sector-Rotation-KRX/backtest Sector-Rotation-USA/

# 3. Copy dashboard management scripts
cp Sector-Rotation-KRX/Jobs/start_dashboard.sh Sector-Rotation-USA/Jobs/
cp Sector-Rotation-KRX/Jobs/stop_dashboard.sh Sector-Rotation-USA/Jobs/
cp Sector-Rotation-KRX/Jobs/check_dashboard.sh Sector-Rotation-USA/Jobs/

# 4. Update configuration
# Edit Sector-Rotation-USA/dashboard/backend/routers/*.py
# Edit Sector-Rotation-USA/config.py (if exists)
```

### For New Country

```bash
# 1. Create base structure
mkdir -p Sector-Rotation-{COUNTRY}/{data,reports,Jobs,logs,backtest,dashboard}

# 2. Copy core files from KRX
cp -r Sector-Rotation-KRX/dashboard Sector-Rotation-{COUNTRY}/
cp -r Sector-Rotation-KRX/backtest Sector-Rotation-{COUNTRY}/
cp Sector-Rotation-KRX/config.py Sector-Rotation-{COUNTRY}/
cp Sector-Rotation-KRX/analyze_4_tier_themes.py Sector-Rotation-{COUNTRY}/

# 3. Update all paths and market-specific settings
```

---

## Configuration Changes Needed

### 1. Update `config.py`
```python
# Change market-specific paths
AUTOGLUON_BASE_DIR = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}")
DB_FILE = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/DB/db_final.csv")
PRICE_DATA_DIR = Path("/mnt/nas/AutoGluon/AutoML_{COUNTRY}/KRXNOTTRAINED")
```

### 2. Update Dashboard Backend
- `dashboard/backend/routers/sector_rotation.py`: Update data file patterns
- `dashboard/backend/routers/portfolio.py`: Update backtest results paths
- `dashboard/backend/routers/meta_labeling.py`: Update model paths

### 3. Update Feature Engineering
- `backtest/feature_engineering.py`: Update UCS_LRS paths
- Update ticker format if different (e.g., USA uses tickers, KRX uses codes)

### 4. Market-Specific Adaptations

**USA**:
- Sectors: GICS 8 sectors (not themes)
- Market cap: USD thresholds
- Ticker format: Standard tickers (AAPL, MSFT)

**Japan**:
- Sectors: TOPIX 33 sectors
- Market cap: JPY thresholds
- Ticker format: TSE codes

**China**:
- Sectors: CSRC sectors
- Market cap: CNY thresholds
- Ticker format: SSE/SZSE codes

---

## Which Country Should We Set Up?

Please specify:
1. **USA** - Complete the dashboard and meta-labeling (recommended)
2. **China** - Full setup from scratch
3. **Japan** - Full setup from scratch
4. **India** - Full setup from scratch
5. **Other** - Specify country

Once you choose, I'll:
1. Copy necessary files from KRX
2. Update all configurations
3. Adapt market-specific settings
4. Test the setup
5. Create documentation

