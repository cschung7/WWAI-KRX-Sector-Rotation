# Investment Reports Summary

## Overview

This document summarizes all useful investment reports and their recommended generation schedule.

---

## ✅ CURRENTLY AUTOMATED REPORTS

### 1. Weekly Synthesis Report
**File**: `reports/weekly_synthesis_YYYYMMDD.md`  
**Script**: `generate_weekly_synthesis.py`  
**Frequency**: Weekly (Sunday)  
**Status**: ✅ Fully automated via `run_weekly_analysis.sh`

**Content**:
- Market overview with TIER 1-4 counts
- TIER 1 actionable recommendations
- TIER 2 accumulation strategies
- TIER 3 research opportunities
- Timing predictions
- Sector rankings

**Investment Value**: ⭐⭐⭐⭐⭐ (Essential weekly decision-making)

---

### 2. Daily Abnormal Sectors Report
**File**: `reports/ABNORMAL_SECTORS_YYYYMMDD.md`  
**Script**: `Jobs/analyze_daily_abnormal_sectors.py`  
**Frequency**: Daily (Weekdays)  
**Status**: ✅ Fully automated (updated with dynamic dates)

**Content**:
- Unusual sector strengthening (>+20% Fiedler increase)
- Unusual sector weakening (<-20% Fiedler decrease)
- Sector disconnections (loss of cohesion)
- New sector formations (new cohesion emergence)
- Investment implications per abnormality type

**Investment Value**: ⭐⭐⭐⭐ (Daily monitoring for rapid changes)

---

## 📋 MANUAL REPORTS (Should Be Automated)

### 3. Investment Implications Report
**File**: `INVESTMENT_IMPLICATIONS_YYYYMMDD.md` (currently in root, should be in `reports/`)  
**Current Example**: `INVESTMENT_IMPLICATIONS_20251107.md`  
**Frequency**: Weekly  
**Status**: ⚠️ Manual generation needed

**Content** (from existing example):
- Current market state with sector Fiedler rankings
- TIER 1-4 classifications with detailed metrics
- Risk-adjusted strategy recommendations
- Portfolio allocation guidance (50-60% TIER 1, 30-35% TIER 2, etc.)
- Large-cap vs small-cap leadership analysis
- Three-tier investment strategy details
- High-conviction opportunities with market cap totals

**Investment Value**: ⭐⭐⭐⭐⭐ (Most comprehensive investment guide)

**Recommendation**: Create `generate_investment_implications.py` to automate

---

### 4. Executive Summary Report
**File**: `EXECUTIVE_SUMMARY.md` (should be `reports/EXECUTIVE_SUMMARY_YYYYMMDD.md`)  
**Frequency**: Weekly  
**Status**: ⚠️ Manual generation needed

**Content** (from existing example):
- Critical findings (cohesion vs regime mismatch warnings)
- Safe to invest themes (with regime probabilities)
- Watchlist themes (wait for regime shift)
- Avoid themes (strong bear regimes)
- Key insights and warnings
- Composite scoring formula
- Immediate action required items

**Investment Value**: ⭐⭐⭐⭐⭐ (Critical decision-making summary - read first)

**Recommendation**: Create `generate_executive_summary.py` to automate

---

### 5. Naver Theme Cohesion Report
**File**: `NAVER_THEME_COHESION_REPORT_YYYYMMDD.md` (should be in `reports/`)  
**Current Example**: `NAVER_THEME_COHESION_REPORT_20251027.md`  
**Script**: `analyze_naver_theme_cohesion.py` (generates CSV, not markdown)  
**Frequency**: Weekly  
**Status**: ⚠️ Script exists but doesn't generate markdown report

**Content** (from existing example):
- Executive summary with total themes analyzed
- Top 20 themes with strongest cohesion enhancement
- Fiedler values, changes, and percentage changes
- Stock counts per theme
- Status indicators (VERY STRONG, STRONG, MODERATE, WEAK)
- Date of peak cohesion

**Investment Value**: ⭐⭐⭐⭐ (Structural understanding of theme cohesion)

**Recommendation**: Enhance `analyze_naver_theme_cohesion.py` to generate markdown report

---

### 6. Within-Theme Leadership Report
**File**: `WITHIN_THEME_LEADERSHIP_REPORT.md` (should be `reports/WITHIN_THEME_LEADERSHIP_YYYYMMDD.md`)  
**Script**: `analyze_within_theme_leadership.py`  
**Frequency**: Weekly  
**Status**: ⚠️ Script exists but doesn't generate markdown report

**Content** (from existing example):
- Executive summary with key findings
- Themes "next to turn investable" (46 themes identified)
- Large-cap leadership gaps (>60%, 50-60%, 40-50%)
- Regime shift signals
- Early entry opportunities (6-18 month lead time)
- Methodology explanation

**Investment Value**: ⭐⭐⭐⭐ (Early signal detection for regime shifts)

**Recommendation**: Enhance `analyze_within_theme_leadership.py` to generate markdown report

---

### 7. Top Investment Themes Report
**File**: `TOP_THEMES_INVESTMENT_READY.md` (should be `reports/TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md`)  
**Frequency**: Weekly  
**Status**: ⚠️ Manual generation needed

**Content** (from existing example):
- Top themes ranked by three-layer framework
- Large-cap leadership details (Tier 1: ≥5T)
- Mid-cap opportunities (Tier 2: 1-5T)
- Small-cap high-beta plays (Tier 3: <1T)
- Investment actions and allocations
- Detailed ticker-level analysis

**Investment Value**: ⭐⭐⭐⭐⭐ (Actionable investment guide with specific tickers)

**Recommendation**: Create `generate_top_themes_report.py` to automate

---

## 📊 RECOMMENDED AUTOMATION PRIORITY

### Priority 1: High-Value Investment Reports (Create New Scripts)

1. **INVESTMENT_IMPLICATIONS_YYYYMMDD.md** ⭐⭐⭐⭐⭐
   - Most comprehensive investment guide
   - Combines all analysis layers
   - Actionable portfolio allocation guidance
   - **Action**: Create `generate_investment_implications.py`

2. **EXECUTIVE_SUMMARY_YYYYMMDD.md** ⭐⭐⭐⭐⭐
   - Critical decision-making summary
   - Warnings and immediate actions
   - **Action**: Create `generate_executive_summary.py`

3. **TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md** ⭐⭐⭐⭐⭐
   - Actionable theme rankings with tickers
   - Specific investment actions
   - **Action**: Create `generate_top_themes_report.py`

### Priority 2: Enhance Existing Scripts

4. **NAVER_THEME_COHESION_REPORT_YYYYMMDD.md** ⭐⭐⭐⭐
   - **Action**: Enhance `analyze_naver_theme_cohesion.py` to generate markdown

5. **WITHIN_THEME_LEADERSHIP_YYYYMMDD.md** ⭐⭐⭐⭐
   - **Action**: Enhance `analyze_within_theme_leadership.py` to generate markdown

---

## 🔄 RECOMMENDED WEEKLY PIPELINE

### Sunday 18:00 - Complete Weekly Analysis

```bash
./run_weekly_analysis.sh
```

**Should Generate** (in order):
1. ✅ `reports/weekly_synthesis_YYYYMMDD.md` (already automated)
2. ⚠️ `reports/NAVER_THEME_COHESION_REPORT_YYYYMMDD.md` (enhance script)
3. ⚠️ `reports/WITHIN_THEME_LEADERSHIP_YYYYMMDD.md` (enhance script)
4. ⚠️ `reports/INVESTMENT_IMPLICATIONS_YYYYMMDD.md` (create new script)
5. ⚠️ `reports/EXECUTIVE_SUMMARY_YYYYMMDD.md` (create new script)
6. ⚠️ `reports/TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md` (create new script)

### Weekdays 18:30 - Daily Monitoring

```bash
./Jobs/run_daily_abnormal_sectors.sh
```

**Generates**:
1. ✅ `reports/ABNORMAL_SECTORS_YYYYMMDD.md` (already automated)

---

## 📖 REPORT USAGE WORKFLOW

### For Weekly Investment Decisions (Sunday Evening)

1. **Start with**: `EXECUTIVE_SUMMARY_YYYYMMDD.md`
   - Critical findings and warnings
   - Safe/avoid/watchlist themes

2. **Then read**: `INVESTMENT_IMPLICATIONS_YYYYMMDD.md`
   - Comprehensive investment guide
   - Portfolio allocation recommendations

3. **For specific themes**: `TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md`
   - Detailed ticker-level analysis
   - Specific investment actions

4. **Complete picture**: `weekly_synthesis_YYYYMMDD.md`
   - Full weekly analysis summary

### For Daily Monitoring (Weekdays)

1. **Check**: `ABNORMAL_SECTORS_YYYYMMDD.md`
   - Unusual sector movements
   - Rapid changes requiring attention

### For Deep Analysis (As Needed)

1. **Theme structure**: `NAVER_THEME_COHESION_REPORT_YYYYMMDD.md`
2. **Early signals**: `WITHIN_THEME_LEADERSHIP_YYYYMMDD.md`

---

## 🎯 SUMMARY

### Currently Automated: 2 reports
- ✅ Weekly Synthesis (weekly)
- ✅ Abnormal Sectors (daily)

### Need Automation: 5 reports
- ⚠️ Investment Implications (weekly) - **HIGH PRIORITY**
- ⚠️ Executive Summary (weekly) - **HIGH PRIORITY**
- ⚠️ Top Investment Themes (weekly) - **HIGH PRIORITY**
- ⚠️ Naver Theme Cohesion (weekly) - Medium priority
- ⚠️ Within-Theme Leadership (weekly) - Medium priority

### Total Investment Reports: 7 reports
- 2 automated ✅
- 5 need automation ⚠️

---

## 📝 NEXT STEPS

1. **Create Priority 1 scripts** (3 new scripts):
   - `generate_investment_implications.py`
   - `generate_executive_summary.py`
   - `generate_top_themes_report.py`

2. **Enhance Priority 2 scripts** (2 existing scripts):
   - Add markdown generation to `analyze_naver_theme_cohesion.py`
   - Add markdown generation to `analyze_within_theme_leadership.py`

3. **Update weekly pipeline**:
   - Integrate all report generators into `run_weekly_analysis.sh`
   - Ensure consistent date formatting
   - Add generation status messages

4. **Create reports index**:
   - `reports/README.md` with links to all reports
   - Latest report indicators
   - Generation schedule

---

**Last Updated**: 2025-11-11  
**Status**: 2/7 reports automated (29% complete)

