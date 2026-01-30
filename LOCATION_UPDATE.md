# Location Update - Sector Rotation KRX

## Final Location

**Current Location**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX`

**Date**: 2025-11-XX (Updated to WWAI location)

---

## Move History

1. **Original**: `/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX`
   - Initial development location

2. **First Move** (2025-10-28 20:04): `/mnt/nas/gpt/Naver/three_layers/countryrisk/Sector-Rotation`
   - Renamed to reflect sector rotation focus

3. **Second Move** (2025-10-28 20:xx): `/mnt/nas/gpt/Naver/three_layers/Sector-Rotation-KRX`
   - Moved up one level (out of `countryrisk` directory)
   - Renamed to `Sector-Rotation-KRX` to emphasize Korean market focus

4. **Final Move** (2025-11-XX): `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX`
   - Moved to WWAI directory structure
   - Better organization with other WWAI projects

---

## Rationale for Final Location

**Why `/mnt/nas/WWAI/Sector-Rotation/`?**
- Better organization with other WWAI projects
- Consistent directory structure
- Easier navigation and access

**Why `Sector-Rotation-KRX`?**
- Clearly identifies the project purpose (Sector Rotation)
- Specifies the market (KRX = Korea Exchange)
- Distinguishes from potential future projects (e.g., Sector-Rotation-USA)

---

## Project Structure

```
/mnt/nas/WWAI/Sector-Rotation/
└── Sector-Rotation-KRX/          ← This project (Korean market)
    ├── run_weekly_analysis.sh
    ├── generate_weekly_synthesis.py
    ├── analyze_4_tier_themes.py
    ├── predict_timing.py
    ├── generate_sector_rankings.py
    ├── data/                     (273 CSV files)
    ├── reports/
    ├── Jobs/
    └── Documentation/
```

---

## Verification

✅ **All files preserved**:
- Scripts: All Python scripts and shell scripts intact
- Data: 273 CSV files verified
- Reports: Weekly synthesis reports intact
- Documentation: All guides preserved (60KB+ total)
- Jobs: 2 comprehensive guides (43KB)

✅ **All functionality working**:
- Weekly synthesis reporting system
- 4-tier investment framework
- Timing prediction system
- Sector rankings generator

---

## Usage (Updated Path)

```bash
# Navigate to project
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX

# Generate weekly report
./run_weekly_analysis.sh

# View latest report
cat reports/weekly_synthesis_$(date +%Y%m%d).md

# Analyze specific theme
python3 generate_sector_rankings.py --sector "철도"
```

---

## Automation Update

If you configured cron jobs, update the path:

```bash
crontab -e

# Update path to:
0 18 * * 0 cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX && ./run_weekly_analysis.sh >> logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

---

## Project Name

**Sector Rotation Analysis Framework - Korean Market (KRX)**

**Focus**: Early detection of sector rotation opportunities in Korean stock market using three-layer analysis:

1. **Cohesion Layer**: Network formation via Fiedler eigenvalues
2. **Regime Layer**: Bull/Bear states via Hidden Markov Models
3. **Market Cap Layer**: Small → Mid → Large cap leadership progression

**Investment Horizon**: 12-18 months early detection before themes become mainstream investable.

---

## Quick Reference

**Location**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX`

**Key Files**:
- `WEEKLY_REPORTING_GUIDE.md` - Complete usage guide (11KB)
- `SYNTHESIS_REPORTING_COMPLETE.md` - System summary (14KB)
- `QUICK_REFERENCE.md` - One-liner commands
- `Jobs/generate_4_tier_investment_theme.md` - 4-tier framework (27KB)
- `Jobs/how_to_run_sector_tickers_ordering.md` - Sector rankings (16KB)

**Data**: 273 CSV files in `data/` directory

**Reports**: Weekly synthesis in `reports/` directory

---

## Related Projects (Same Directory Level)

Located in `/mnt/nas/WWAI/Sector-Rotation/`:

- **Sector-Rotation-KRX** (this project) - Korean market sector rotation

---

## No Action Required

All scripts use relative paths, so functionality is preserved automatically. The directory move does not affect any internal operations.

**System Status**: ✅ Production-ready and fully operational

**Start Using**:
```bash
cd /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX
./run_weekly_analysis.sh
```
