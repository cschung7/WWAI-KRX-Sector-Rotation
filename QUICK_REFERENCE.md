# Quick Reference - Weekly Synthesis Reporting

**Project**: Sector Rotation Analysis Framework - Korean Market (KRX)
**Location**: `/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX`
**Previous Locations**:
- `countryrisk/KRX` → `countryrisk/Sector-Rotation` → `Sector-Rotation-KRX`

## One-Liners

```bash
# Generate today's synthesis report
./run_weekly_analysis.sh

# Generate for specific date
./run_weekly_analysis.sh 20251027

# View latest report
cat reports/weekly_synthesis_$(date +%Y%m%d).md

# View TIER 1 themes only
grep -A 30 "TIER 1: BUY NOW" reports/weekly_synthesis_$(date +%Y%m%d).md

# Check this week's action items
grep -A 40 "THIS WEEK'S ACTION ITEMS" reports/weekly_synthesis_$(date +%Y%m%d).md

# Analyze specific theme
python3 generate_sector_rankings.py --sector "철도"

# Check timing prediction
cat data/tier3_timing_predictions_$(date +%Y%m%d).json | grep -A 10 "해운"
```

## Files Location

```bash
# All synthesis reports
ls -lh reports/weekly_synthesis_*.md

# Latest 4-tier data
ls -lh data/tier*_$(date +%Y%m%d).csv

# Sector rankings
ls -lh data/sector_rankings_*.txt
```

## Weekly Workflow

```bash
# Sunday 18:00 - Generate report
./run_weekly_analysis.sh

# Sunday 18:15 - Quick review
cat reports/weekly_synthesis_$(date +%Y%m%d).md | less

# Monday - Execute TIER 1 buys
python3 generate_sector_rankings.py --sector "철도"
python3 generate_sector_rankings.py --sector "반도체 장비"

# Tuesday-Friday - DCA TIER 2 themes
# (Set up automated buy orders)
```

## Documentation

- **Usage Guide**: `WEEKLY_REPORTING_GUIDE.md` (11KB)
- **Timing Analysis**: `TIMING_ESTIMATION_BRAINSTORM.md` (15KB)
- **Completion Summary**: `SYNTHESIS_REPORTING_COMPLETE.md` (14KB)

## Support

For questions or issues, refer to the comprehensive guides:
1. `WEEKLY_REPORTING_GUIDE.md` - Complete usage documentation
2. `Jobs/generate_4_tier_investment_theme.md` - 4-tier framework
3. `Jobs/how_to_run_sector_tickers_ordering.md` - Sector rankings
