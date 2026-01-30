# Report Automation Guide - Investment Reports

## Overview

This document identifies all useful investment reports and their recommended generation frequency.

---

## 📊 CURRENT REPORTS STATUS

### ✅ Already Automated

1. **Weekly Synthesis Report** (`reports/weekly_synthesis_YYYYMMDD.md`)
   - **Script**: `generate_weekly_synthesis.py`
   - **Frequency**: Weekly (via `run_weekly_analysis.sh`)
   - **Content**: 4-tier classification, timing predictions, sector rankings, actionable items
   - **Status**: ✅ Fully automated

2. **Daily Abnormal Sectors** (`reports/ABNORMAL_SECTORS_YYYYMMDD.md`)
   - **Script**: `Jobs/analyze_daily_abnormal_sectors.py`
   - **Frequency**: Daily
   - **Content**: Unusual Fiedler changes, disconnections, new formations
   - **Status**: ✅ Fully automated (updated to use dynamic dates)

---

## 📋 REPORTS NEEDING AUTOMATION

### 1. **Naver Theme Cohesion Report** (Weekly)

**File**: `reports/NAVER_THEME_COHESION_REPORT_YYYYMMDD.md`

**Current Script**: `analyze_naver_theme_cohesion.py`
- Generates CSV files but doesn't create markdown report
- Needs enhancement to generate markdown report

**Content Should Include**:
- Top 20 themes with strongest cohesion enhancement
- Fiedler values and changes
- Stock counts per theme
- Status indicators (VERY STRONG, STRONG, MODERATE, WEAK)

**Recommended**: Generate weekly (Sunday) as part of weekly analysis pipeline

---

### 2. **Investment Implications Report** (Weekly)

**File**: `reports/INVESTMENT_IMPLICATIONS_YYYYMMDD.md`

**Current Status**: Manual generation (example: `INVESTMENT_IMPLICATIONS_20251107.md`)

**Content Should Include**:
- Current market state with sector Fiedler rankings
- TIER 1-4 classifications with investment actions
- Risk-adjusted strategy recommendations
- Portfolio allocation guidance
- Large-cap vs small-cap leadership analysis

**Recommended**: Generate weekly (Sunday) combining:
- 4-tier analysis results
- Sector rankings
- Regime analysis
- Within-theme leadership

---

### 3. **Executive Summary** (Weekly)

**File**: `reports/EXECUTIVE_SUMMARY_YYYYMMDD.md`

**Current Status**: Manual generation (example: `EXECUTIVE_SUMMARY.md`)

**Content Should Include**:
- Critical findings (cohesion vs regime mismatch)
- Safe to invest themes
- Watchlist themes
- Avoid themes
- Key insights and warnings

**Recommended**: Generate weekly (Sunday) as critical decision-making summary

---

### 4. **Within-Theme Leadership Report** (Weekly)

**File**: `reports/WITHIN_THEME_LEADERSHIP_YYYYMMDD.md`

**Current Script**: `analyze_within_theme_leadership.py`
- Generates analysis but doesn't create markdown report
- Needs enhancement to generate markdown report

**Content Should Include**:
- Themes "next to turn investable"
- Large-cap leadership gaps
- Regime shift signals
- Early entry opportunities

**Recommended**: Generate weekly (Sunday) as part of weekly analysis

---

### 5. **Top Investment Themes** (Weekly)

**File**: `reports/TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md`

**Current Status**: Manual generation (example: `TOP_THEMES_INVESTMENT_READY.md`)

**Content Should Include**:
- Top themes ranked by three-layer framework
- Large-cap leadership details
- Mid-cap and small-cap opportunities
- Investment actions and allocations

**Recommended**: Generate weekly (Sunday) as actionable investment guide

---

## 🔄 RECOMMENDED AUTOMATION STRUCTURE

### Weekly Reports (Sunday 18:00)

```bash
./run_weekly_analysis.sh  # Already exists
```

**Should Generate**:
1. ✅ `reports/weekly_synthesis_YYYYMMDD.md` (already automated)
2. ⚠️ `reports/NAVER_THEME_COHESION_REPORT_YYYYMMDD.md` (needs enhancement)
3. ⚠️ `reports/INVESTMENT_IMPLICATIONS_YYYYMMDD.md` (needs creation)
4. ⚠️ `reports/EXECUTIVE_SUMMARY_YYYYMMDD.md` (needs creation)
5. ⚠️ `reports/WITHIN_THEME_LEADERSHIP_YYYYMMDD.md` (needs enhancement)
6. ⚠️ `reports/TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md` (needs creation)

### Daily Reports (Weekdays 18:30)

```bash
./Jobs/run_daily_abnormal_sectors.sh  # Already exists
```

**Generates**:
1. ✅ `reports/ABNORMAL_SECTORS_YYYYMMDD.md` (already automated)

---

## 📝 IMPLEMENTATION PRIORITY

### Priority 1: High-Value Investment Reports

1. **INVESTMENT_IMPLICATIONS_YYYYMMDD.md** - Most comprehensive, actionable
2. **EXECUTIVE_SUMMARY_YYYYMMDD.md** - Critical decision-making summary
3. **TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md** - Actionable investment guide

### Priority 2: Supporting Analysis Reports

4. **NAVER_THEME_COHESION_REPORT_YYYYMMDD.md** - Structural understanding
5. **WITHIN_THEME_LEADERSHIP_YYYYMMDD.md** - Early signal detection

---

## 🛠️ NEXT STEPS

1. **Enhance existing scripts** to generate markdown reports:
   - `analyze_naver_theme_cohesion.py` → Add markdown report generation
   - `analyze_within_theme_leadership.py` → Add markdown report generation

2. **Create new report generators**:
   - `generate_investment_implications.py` - Comprehensive investment report
   - `generate_executive_summary.py` - Critical findings summary
   - `generate_top_themes_report.py` - Investment-ready themes

3. **Update weekly pipeline**:
   - Integrate all report generators into `run_weekly_analysis.sh`
   - Ensure all reports use consistent date formatting
   - Add report generation status messages

4. **Create report index**:
   - `reports/README.md` - Index of all reports with descriptions
   - Links to latest reports
   - Report generation schedule

---

## 📊 REPORT USAGE GUIDE

### For Daily Monitoring
- **ABNORMAL_SECTORS_YYYYMMDD.md** - Check for unusual sector movements

### For Weekly Investment Decisions
- **EXECUTIVE_SUMMARY_YYYYMMDD.md** - Start here for critical findings
- **INVESTMENT_IMPLICATIONS_YYYYMMDD.md** - Comprehensive investment guide
- **TOP_THEMES_INVESTMENT_READY_YYYYMMDD.md** - Actionable theme rankings
- **weekly_synthesis_YYYYMMDD.md** - Complete weekly analysis

### For Deep Analysis
- **NAVER_THEME_COHESION_REPORT_YYYYMMDD.md** - Theme structure understanding
- **WITHIN_THEME_LEADERSHIP_YYYYMMDD.md** - Early signal detection

---

## 🎯 SUCCESS CRITERIA

✅ All reports generated automatically with date stamps
✅ Consistent formatting across all reports
✅ All reports saved to `reports/` directory
✅ Weekly pipeline generates all weekly reports
✅ Daily pipeline generates daily reports
✅ Reports are self-contained and actionable

