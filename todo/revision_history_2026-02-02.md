# Revision History - 2026-02-02

## Summary

KRX Sector Rotation cohesion page improvements: added fiedler_change (delta) display, last update timestamp, and graceful handling of empty declining themes.

---

## 1. Documentation: Cohesion Update Guide

**Task**: Document how to run cohesion updates in how_to_run.md

**Files Changed**:
- `docs/how_to_run.md`
  - Added "## Update Cohesion (테마 군집성 업데이트)" section
  - Included commands for checking status, running updates
  - Documented data structure and output files

**Commit**: Added to how_to_run.md

---

## 2. Feature: Cohesion Page Delta Display

**Problem**: cohesion.html showed weekly slope from `fiedler-trends` API, but user needed `fiedler_change` (30-day delta) from `themes` API for investment perspective.

**Solution**: Updated page to fetch from both APIs and display:
- **Level**: Current Fiedler value (where cohesion is)
- **Delta**: fiedler_change from themes API (how it's changing)

**Files Changed**:
- `dashboard/frontend/cohesion.html`
  - Modified `init()` to fetch both `/api/sector-rotation/fiedler-trends` and `/api/sector-rotation/themes`
  - Created `themeChangeMap` to merge `fiedler_change` and `pct_change` into trends data
  - Updated theme cards to show Level + Delta columns
  - Updated chart tooltips to show delta information

**Key Code Changes**:
```javascript
// Fetch both APIs
const [trendsResponse, themesResponse] = await Promise.all([
    fetch(`${API_BASE}/api/sector-rotation/fiedler-trends?weeks=8`),
    fetch(`${API_BASE}/api/sector-rotation/themes`)
]);

// Merge fiedler_change into trends
const themeChangeMap = {};
allThemes.forEach(t => {
    themeChangeMap[t.theme] = {
        fiedler_change: t.fiedler_change || 0,
        pct_change: t.pct_change || 0
    };
});
```

**Commit**: `Update cohesion page to show fiedler_change delta`

---

## 3. Feature: Last Update Timestamp

**Problem**: Users couldn't see when cohesion data was last updated.

**Solution**: Added "최종업데이트" / "Last Update" label in upper right corner.

**Files Changed**:
- `dashboard/frontend/cohesion.html`
  - Added `<div id="lastUpdate">` in header
  - Created `fetchLastUpdate()` function to get date from themes API
  - Language-aware label (KO: 최종업데이트, EN: Last Update)

**Commit**: `Add last update timestamp to cohesion page`

---

## 4. Fix: Empty Declining Themes Section

**Problem**: "군집성 하락 TOP 5" section showed "군집성 최소 상승 TOP 5" (lowest increase) when all themes had positive fiedler_change. User requested simpler display.

**Solution**: Show "해당 사항 없음" (No data) when no declining themes exist.

**Files Changed**:
- `dashboard/frontend/cohesion.html`
  - Updated `updateMovers()` function
  - Removed "lowest increase" fallback logic
  - Added language-aware "No data" message

**Key Code Changes**:
```javascript
function updateMovers(themes) {
    const decreasing = sorted.filter(t => (t.fiedler_change || 0) < 0);

    // Show "No data" if no declining themes exist
    if (decreasing.length === 0) {
        const noDataMsg = currentLang === 'ko' ? '해당 사항 없음' : 'No data';
        document.getElementById('decreasingList').innerHTML = `
            <li style="color: #94a3b8; font-style: italic; justify-content: center;">
                ${noDataMsg}
            </li>
        `;
    }
}
```

**Commit**: `Show 'No data' when no declining themes exist in cohesion page`

---

## 5. Meta-Labeling Model Training

**Task**: Train XGBoost meta-labeling model to filter theme signals.

**Results**:
- **Accuracy**: 79.4%
- **AUC**: 0.846
- **Training Samples**: 15,643

**Files Generated**:
- `backtest/models/meta_labeler_xgboost_20260203.pkl`

**Purpose**: Filter theme rotation signals to improve signal quality by using ML to identify which signals are likely to be profitable.

---

## 6. Cohesion Data Generation

**Task**: Generated 2026-02-03 cohesion data.

**Results**:
- **Total Themes**: 105
- **ALL themes have positive fiedler_change** (no declining themes)
- **Min Change**: +0.01 (치매)
- **Max Change**: +3.60 (스테이블코인, +298%)

**Files Generated**:
- `data/enhanced_cohesion_themes_20260203.csv`

**Top 10 Enhanced Cohesion Themes**:
| Theme | Fiedler | Change | % Change |
|-------|---------|--------|----------|
| 스테이블코인 | 4.81 | +3.60 | +298% |
| 2차전지 | 7.46 | +2.92 | +64% |
| 비철금속 | 10.95 | +2.81 | +35% |
| 원전 | 13.41 | +2.28 | +20% |
| 가상화폐/암호화폐 | 4.93 | +2.08 | +73% |

---

## Files Summary

### Modified Files
| File | Change |
|------|--------|
| `docs/how_to_run.md` | Added cohesion update documentation |
| `dashboard/frontend/cohesion.html` | Delta display, last update, no-data handling |

### New Files
| File | Purpose |
|------|---------|
| `data/enhanced_cohesion_themes_20260203.csv` | Daily cohesion data |
| `backtest/models/meta_labeler_xgboost_20260203.pkl` | Meta-labeling model |

---

## Deployment

All changes pushed to GitHub and deployed to Railway:
- **Dashboard URL**: https://web-production-e5d7.up.railway.app/cohesion.html

---

## Verification

### Cohesion Page Now Shows:
1. **Last Update**: 최종업데이트: 2026-02-03
2. **Theme Cards**: Level + Delta columns
3. **Top 5 Increasing**: 스테이블코인 +3.60 (+298%), etc.
4. **Top 5 Decreasing**: "해당 사항 없음" (all positive)

---

## Related Documentation

- [How to Run](../docs/how_to_run.md) - Full pipeline documentation including cohesion update
- [CLAUDE.md](../CLAUDE.md) - Project overview
