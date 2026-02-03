# Revision History - 2026-02-03

## Summary

KRX Sector Rotation dashboard fixes and automation improvements for Railway deployment.

---

## 1. Fixed: Daily Summary Endpoint for Railway

**Problem**: `/api/breakout/daily-summary` returned 404 on Railway because it looked for files in NAS path which doesn't exist on Railway.

**Solution**: Updated `breakout.py` to check local `data/` folder first, then NAS fallback.

**Files Changed**:
- `dashboard/backend/routers/breakout.py`
  - Added `LOCAL_RANKINGS_DIR` path
  - Added `get_daily_summary_files()` function with local-first logic

**Commit**: `Fix daily-summary endpoint for Railway deployment`

---

## 2. Fixed: BB Crossover Filter Path

**Problem**: BB filter data was saved to wrong location (`data/bb_filtered_tickers.json` instead of `data/bb_filter/bb_filtered_tickers.json`).

**Solution**: Created correct directory structure and moved file.

**Files Changed**:
- Created `data/bb_filter/` directory
- Moved `bb_filtered_tickers.json` to correct location

**Commit**: `Fix BB filter path - move to data/bb_filter/`

---

## 3. Fixed: Theme Column Empty in SuperTrend Table

**Problem**: Theme column showed empty `[]` for all tickers because theme mapping file (`db_final.csv`) was only on NAS, not accessible from Railway.

**Solution**:
1. Created local `theme_mapping.csv` from `db_final.csv` (2,347 tickers with themes)
2. Updated `breakout.py` to use local file first, NAS fallback

**Files Changed**:
- Created `data/theme_mapping.csv` (extracted from db_final.csv)
- `dashboard/backend/routers/breakout.py`
  - Added `LOCAL_THEME_MAPPING` path
  - Updated `get_theme_mapping()` with local-first logic

**Commit**: `Add local theme mapping for Railway deployment`

---

## 4. Generated: 2026-02-03 Data

**Problem**: Breakout page showed 2026-02-02 data instead of 2026-02-03.

**Solution**: Ran full data generation pipeline (Steps 9-12).

**Pipeline Executed**:
| Step | Task | Result |
|------|------|--------|
| 9 | Regime Analysis | classified_trends_2026-02-03.csv (967 tickers) |
| 10 | Copy to superTrend | Done |
| 11 | actionable_tickers | 694 tickers |
| 12 | BB Filter | 131 crossover tickers |

**Files Generated**:
- `data/actionable_tickers_20260203.csv`
- `data/daily_update_detailed_20260203.csv`
- `data/daily_update_summary_20260203.json`
- `data/bb_filter/bb_filtered_tickers.json`

**Stage Distribution**:
- Super Trend: 223
- Early Breakout: 17
- Burgeoning: 181
- Healthy Correction: 273

**Commit**: `Daily update 2026-02-03`

---

## 5. Created: Standalone Filter Script

**Problem**: `daily_update_all.sh` sometimes gets stuck, making manual updates difficult.

**Solution**: Created standalone script that only runs Sector Rotation data generation steps (9-12) + deployment.

**File Created**: `/mnt/nas/AutoGluon/AutoML_Krx/filter_sector_rotation_krx.sh`

**6 Steps**:
1. Regime/Theme Analysis → classified_trends
2. Copy to superTrend directory
3. Generate actionable_tickers
4. BB(220, 2.0) Crossover filter
5. Copy results to dashboard repo
6. Deploy to Railway (git commit + push)

**Usage**:
```bash
cd /mnt/nas/AutoGluon/AutoML_Krx
./filter_sector_rotation_krx.sh              # Today's date
./filter_sector_rotation_krx.sh 2026-02-03   # Specific date
```

**Execution Time**: ~21 seconds (excluding deployment)

---

## 6. Created: Individual Deployment Scripts

**Location**: `/mnt/nas/WWAI/Sector-Rotation/Jobs/`

**Scripts Created**:
| Script | Market | Dashboard URL |
|--------|--------|---------------|
| `daily_deploy_krx.sh` | Korea | https://web-production-e5d7.up.railway.app |
| `daily_deploy_usa.sh` | USA | https://wwai-usa-sector-rotation-production.up.railway.app |
| `daily_deploy_japan.sh` | Japan | https://web-production-5e98f.up.railway.app |
| `daily_deploy_china.sh` | China | https://web-production-14009.up.railway.app |
| `daily_deploy_india.sh` | India | https://wwai-india-sector-rotation-production.up.railway.app |
| `daily_deploy_hongkong.sh` | Hong Kong | https://backend-production-be465.up.railway.app |
| `daily_deploy_all.sh` | All markets | Runs all above + landing page |

**Features**:
- Copies daily_summary files from Rankings (KRX only)
- Checks for changes before committing
- Auto-push to trigger Railway deployment

---

## Files Summary

### Modified Files
| File | Change |
|------|--------|
| `dashboard/backend/routers/breakout.py` | Local-first paths for daily_summary, BB filter, theme mapping |

### New Files
| File | Purpose |
|------|---------|
| `data/theme_mapping.csv` | Local theme mapping (2,347 tickers) |
| `data/bb_filter/bb_filtered_tickers.json` | BB crossover results |
| `data/actionable_tickers_20260203.csv` | SuperTrend candidates |
| `data/daily_update_detailed_20260203.csv` | Detailed update data |
| `data/daily_update_summary_20260203.json` | Update summary |

### External Scripts
| File | Purpose |
|------|---------|
| `/mnt/nas/AutoGluon/AutoML_Krx/filter_sector_rotation_krx.sh` | Standalone filter + deploy |
| `/mnt/nas/WWAI/Sector-Rotation/Jobs/daily_deploy_*.sh` | Market-specific deployment |

---

## Verification

### API Endpoints (All showing 2026-02-03)
```
Daily Summary: 2026-02-03
SuperTrend: 20260203 (223 tickers)
BB Crossover: 2026-02-03 (131 tickers)
Candidates: 694 tickers
```

### Themes Now Showing
```
아주IB투자: ['스페이스X(SpaceX)', '창투사', '야놀자(Yanolja)']
미래에셋벤처투자: ['스페이스X(SpaceX)', '창투사', '마켓컬리(kurly)']
스피어: ['우주항공산업', '의료AI', '스페이스X(SpaceX)']
```

---

## 7. Feature: Cohesion Page - Historical Date Dropdown

**Problem**: Users could only view current cohesion data, no way to see historical trends.

**Solution**: Added date dropdown to cohesion page with 53 weeks of historical data.

**Backend Changes** (`dashboard/backend/routers/sector_rotation.py`):
- Added `GET /api/sector-rotation/cohesion-dates` - Returns available dates (53 weeks)
- Added `GET /api/sector-rotation/cohesion-history?date=YYYY-MM-DD` - Returns cohesion data for specific date

**Frontend Changes** (`dashboard/frontend/cohesion.html`):
- Added date dropdown selector in header (next to language toggle)
- `loadAvailableDates()` - Fetches available dates from API
- `loadHistoricalData(date)` - Loads cohesion data for selected date
- Updates summary, movers, chart, and theme cards for historical view

**Data Source**: `data/naver_themes_weekly_fiedler_2025.csv` (14,046 rows, 53 weeks)

**Date Range**: 2025-01-08 → 2026-01-28

**Commits**:
- `Add historical date dropdown to cohesion page`
- `Fix NaN handling in cohesion-history endpoint`
- `Fix cohesion-history: safer row access and type conversion`

---

## 8. Fix: Cohesion Page - Empty Declining Themes Section

**Problem**: "군집성 하락 TOP 5" section showed "최소 상승" when all themes had positive fiedler_change.

**Solution**: Show "해당 사항 없음" / "No data" when no declining themes exist.

**File Changed**: `dashboard/frontend/cohesion.html`
- Updated `updateMovers()` function to display "No data" message
- Language-aware: Korean "해당 사항 없음", English "No data"

**Commit**: `Show 'No data' when no declining themes exist in cohesion page`

---

## Files Summary (Updated)

### Modified Files
| File | Change |
|------|--------|
| `dashboard/backend/routers/breakout.py` | Local-first paths for daily_summary, BB filter, theme mapping |
| `dashboard/backend/routers/sector_rotation.py` | Added cohesion-dates, cohesion-history endpoints |
| `dashboard/frontend/cohesion.html` | Historical date dropdown, "No data" handling |

### New Files
| File | Purpose |
|------|---------|
| `data/theme_mapping.csv` | Local theme mapping (2,347 tickers) |
| `data/bb_filter/bb_filtered_tickers.json` | BB crossover results |
| `data/actionable_tickers_20260203.csv` | SuperTrend candidates |
| `data/daily_update_detailed_20260203.csv` | Detailed update data |
| `data/daily_update_summary_20260203.json` | Update summary |
| `todo/revision_history_2026-02-02.md` | Previous day revision history |

### External Scripts
| File | Purpose |
|------|---------|
| `/mnt/nas/AutoGluon/AutoML_Krx/filter_sector_rotation_krx.sh` | Standalone filter + deploy |
| `/mnt/nas/WWAI/Sector-Rotation/Jobs/daily_deploy_*.sh` | Market-specific deployment |

---

## New API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/sector-rotation/cohesion-dates` | List available historical dates (53 weeks) |
| `GET /api/sector-rotation/cohesion-history?date=2026-01-28` | Get cohesion data for specific date |

---

## Next Steps

1. **Daily Routine**: Use `filter_sector_rotation_krx.sh` when `daily_update_all.sh` gets stuck
2. **Weekly**: Run full `daily_update_all.sh` for complete pipeline
3. **Deployment**: Use `daily_deploy_krx.sh` or the filter script (includes deploy)
4. **Historical Analysis**: Use cohesion page date dropdown to compare past cohesion levels

---

## Related Documentation

- [How to Run](../docs/how_to_run.md) - Full pipeline documentation
- [How to Filter](../docs/how_to_filter.md) - Filter methods explanation
- [CLAUDE.md](../CLAUDE.md) - Project overview
