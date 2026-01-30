# Directory Move Notice

## Change Summary

**Date**: 2025-10-28 20:04 KST

**Previous Location**: `/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX`

**New Location**: `/mnt/nas/gpt/Naver/three_layers/countryrisk/Sector-Rotation`

**Reason**: Renamed to better reflect the project focus on sector rotation analysis using three-layer framework (Cohesion × Regime × Market Cap).

---

## What Was Preserved

✅ All Python scripts and analysis tools
✅ Complete data directory (273 CSV files)
✅ All reports and documentation
✅ Jobs directory with comprehensive guides
✅ Weekly synthesis reporting system
✅ 4-tier investment framework
✅ Timing prediction system
✅ Git history

---

## Updated References

All references within scripts and documentation continue to work as they use relative paths.

### Scripts Working After Move
- ✅ `run_weekly_analysis.sh` - Automated pipeline
- ✅ `generate_weekly_synthesis.py` - Report generator
- ✅ `analyze_4_tier_themes.py` - 4-tier classifier
- ✅ `predict_timing.py` - Timing predictor
- ✅ `generate_sector_rankings.py` - Sector rankings

### Data Directories
- ✅ `data/` - All CSV, JSON files intact (273 files)
- ✅ `reports/` - Weekly synthesis reports
- ✅ `Jobs/` - Comprehensive guides (2 files, 43KB)
- ✅ `logs/` - Execution logs

---

## New Working Directory

```bash
cd /mnt/nas/gpt/Naver/three_layers/countryrisk/Sector-Rotation
```

---

## Usage (Unchanged)

```bash
# Generate weekly synthesis report
./run_weekly_analysis.sh

# View latest report
cat reports/weekly_synthesis_$(date +%Y%m%d).md

# Analyze specific theme
python3 generate_sector_rankings.py --sector "철도"
```

---

## Cron Job Update (If Configured)

If you set up weekly automation via cron, update the path:

```bash
# Edit crontab
crontab -e

# OLD (remove):
# 0 18 * * 0 cd /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX && ./run_weekly_analysis.sh

# NEW (add):
0 18 * * 0 cd /mnt/nas/gpt/Naver/three_layers/countryrisk/Sector-Rotation && ./run_weekly_analysis.sh >> logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

---

## Verification

All key files verified after move:

```bash
# Scripts
✓ run_weekly_analysis.sh
✓ generate_weekly_synthesis.py
✓ analyze_4_tier_themes.py
✓ predict_timing.py
✓ generate_sector_rankings.py

# Data
✓ 273 CSV files in data/
✓ tier1-4 classification files
✓ Sector rankings files
✓ Theme cohesion data

# Documentation
✓ WEEKLY_REPORTING_GUIDE.md (11KB)
✓ SYNTHESIS_REPORTING_COMPLETE.md (14KB)
✓ TIMING_ESTIMATION_BRAINSTORM.md (18KB)
✓ Jobs/generate_4_tier_investment_theme.md (27KB)
✓ Jobs/how_to_run_sector_tickers_ordering.md (16KB)

# Reports
✓ reports/weekly_synthesis_20251027.md (190 lines)
```

---

## Project Name

**Sector Rotation Analysis Framework**

Focus: Korean stock market (KRX) sector rotation opportunities using three-layer analysis:
1. **Cohesion Layer**: Network formation via Fiedler values
2. **Regime Layer**: Bull/Bear states via Hidden Markov Models
3. **Market Cap Layer**: Small → Mid → Large cap leadership progression

Investment Timeline: 12-18 months early detection of sector rotation themes.

---

## No Action Required

All functionality remains intact. Continue using the system as documented in:
- `WEEKLY_REPORTING_GUIDE.md`
- `SYNTHESIS_REPORTING_COMPLETE.md`
- `QUICK_REFERENCE.md`

The directory rename improves clarity about the project's focus on sector rotation analysis.
