# Weekly/Daily Investment Synthesis Reporting Guide

## Overview

Complete automated system for generating dated investment synthesis reports that combine:
- **4-Tier Framework** (Buy Now, Accumulate, Research, Monitor)
- **Timing Predictions** (6-24 month estimates)
- **Sector Rankings** (Cohesion × Regime × Market Cap)
- **Actionable Recommendations** (Portfolio allocation + specific actions)

---

## Quick Start

### Generate Today's Report

```bash
# Run complete analysis pipeline
./run_weekly_analysis.sh

# Or specify a date
./run_weekly_analysis.sh 20251027
```

**Output**: `reports/weekly_synthesis_YYYYMMDD.md`

### View Report

```bash
# View in terminal
cat reports/weekly_synthesis_20251027.md

# View in browser (requires pandoc)
pandoc reports/weekly_synthesis_20251027.md -o reports/weekly_synthesis_20251027.html
open reports/weekly_synthesis_20251027.html

# Email report
mail -s "Weekly Investment Synthesis 2025-10-27" investor@example.com < reports/weekly_synthesis_20251027.md
```

---

## System Components

### Component 1: 4-Tier Theme Classification

**Script**: `analyze_4_tier_themes.py`

**What It Does**:
- Classifies Naver themes into 4 investment tiers based on cohesion patterns
- TIER 1: Buy NOW (baseline >15, change >5)
- TIER 2: Accumulate 6-12mo (baseline 5-15, change >2)
- TIER 3: Research 12-18mo (baseline 2-8, change >1.5, % >30%)
- TIER 4: Monitor 18-24mo (baseline 0.5-3, % >40%)

**Usage**:
```bash
python3 analyze_4_tier_themes.py
```

**Outputs**:
```
data/tier1_buy_now_20251027.csv
data/tier2_accumulate_20251027.csv
data/tier3_research_20251027.csv
data/tier4_monitor_20251027.csv
data/4tier_summary_20251027.json
```

**When to Run**: Weekly (every Sunday after market close)

---

### Component 2: Timing Predictions

**Script**: `predict_timing.py`

**What It Does**:
- Predicts months until TIER 3 themes become TIER 1 investable
- Uses Fiedler velocity extrapolation
- Provides confidence intervals and acceleration status

**Usage**:
```bash
python3 predict_timing.py
```

**Outputs**:
```
data/tier3_timing_predictions_20251027.json
```

**Current Limitation**:
⚠️ Only uses 1-week velocity snapshot (needs weekly timeseries for accuracy)

**Next Step**:
Build `aggregate_naver_theme_fiedler_history.py` for realistic predictions

**When to Run**: Weekly (after 4-tier classification)

---

### Component 3: Sector Rankings

**Script**: `generate_sector_rankings.py`

**What It Does**:
- Generates detailed ticker rankings within each theme
- Combines cohesion + regime + market cap + composite score
- Identifies top investment candidates

**Usage**:
```bash
# Analyze specific theme
python3 generate_sector_rankings.py --sector "철도"

# Analyze all top themes
python3 generate_sector_rankings.py --top-sectors 10

# Generate for specific date
python3 generate_sector_rankings.py --sector "반도체 장비" --date 20251027
```

**Outputs**:
```
data/sector_rankings_20251027.txt
data/sector_rankings_20251027.md
data/sector_rankings_20251027.json
```

**When to Run**:
- Weekly for TIER 1 themes
- Monthly for TIER 2 themes
- On-demand for research

---

### Component 4: Weekly Synthesis Report

**Script**: `generate_weekly_synthesis.py`

**What It Does**:
- Combines all analysis components into unified report
- Provides executive summary, actionable recommendations, risk alerts
- Week-over-week comparison (if previous data exists)

**Usage**:
```bash
# Generate for today
python3 generate_weekly_synthesis.py

# Generate for specific date
python3 generate_weekly_synthesis.py --date 20251027

# Save to file
python3 generate_weekly_synthesis.py --date 20251027 > reports/weekly_synthesis_20251027.md
```

**Output Sections**:
1. **Executive Summary** - Market overview, theme counts
2. **TIER 1 Actionable** - Immediate buy recommendations
3. **TIER 2 Accumulation** - Dollar-cost averaging strategy
4. **TIER 3 Research** - Early-stage opportunities with timing
5. **TIER 4 Monitoring** - Speculative watchlist
6. **Portfolio Allocation** - Risk-balanced allocation strategy
7. **Weekly Actions** - Specific tasks for this week
8. **Risk Alerts** - Warnings and limitations
9. **Historical Comparison** - Week-over-week changes

**When to Run**: Weekly (after all other components)

---

### Component 5: Master Pipeline

**Script**: `run_weekly_analysis.sh`

**What It Does**:
- Orchestrates all components in correct sequence
- Handles errors gracefully
- Generates complete synthesis report

**Usage**:
```bash
# Run for today
./run_weekly_analysis.sh

# Run for specific date
./run_weekly_analysis.sh 20251027
```

**Pipeline Steps**:
1. Check theme cohesion data
2. Generate 4-tier classification
3. Calculate timing predictions
4. Generate sector rankings for TIER 1 themes
5. Create weekly synthesis report

**When to Run**: Weekly (automated via cron)

---

## Automation Setup

### Weekly Cron Job

```bash
# Edit crontab
crontab -e

# Add weekly execution (every Sunday at 18:00)
0 18 * * 0 cd /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX && ./run_weekly_analysis.sh >> logs/weekly_$(date +\%Y\%m\%d).log 2>&1
```

### Monthly Snapshot Collection

```bash
# Save monthly UCS_LRS situation data
cat > scripts/save_monthly_snapshot.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m)
mkdir -p snapshots/
cp /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_*.json \
   snapshots/situation_${DATE}.json
echo "Snapshot saved: situation_${DATE}.json"
EOF

chmod +x scripts/save_monthly_snapshot.sh

# Add to crontab (1st of each month at 18:00)
0 18 1 * * /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/scripts/save_monthly_snapshot.sh
```

---

## Report Usage Scenarios

### Scenario 1: Weekly Portfolio Review (Every Sunday)

```bash
# 1. Generate latest report
./run_weekly_analysis.sh

# 2. Review TIER 1 themes
cat reports/weekly_synthesis_$(date +%Y%m%d).md | grep -A 20 "TIER 1: BUY NOW"

# 3. Check week-over-week changes
cat reports/weekly_synthesis_$(date +%Y%m%d).md | grep -A 10 "WEEK-OVER-WEEK COMPARISON"

# 4. Execute action items
# (see "THIS WEEK'S ACTION ITEMS" section)
```

### Scenario 2: Deep Dive on Specific Theme

```bash
# 1. Check if theme is in TIER 1 or TIER 2
grep "철도" data/tier1_buy_now_$(date +%Y%m%d).csv

# 2. Generate detailed sector rankings
python3 generate_sector_rankings.py --sector "철도"

# 3. Review top tickers
cat data/sector_rankings_$(date +%Y%m%d).txt | grep -A 50 "철도"

# 4. Check regime status
cat data/sector_rankings_$(date +%Y%m%d).txt | grep "Bull Quiet"
```

### Scenario 3: Historical Analysis

```bash
# Generate report for specific past date
./run_weekly_analysis.sh 20251020

# Compare with current week
diff <(grep "TIER 1" reports/weekly_synthesis_20251020.md) \
     <(grep "TIER 1" reports/weekly_synthesis_20251027.md)

# Track theme progression over time
for date in 20251001 20251008 20251015 20251022; do
    echo "=== Week of $date ==="
    grep "해운" data/tier*_${date}.csv 2>/dev/null || echo "Not in any tier"
done
```

### Scenario 4: Research New TIER 3 Theme

```bash
# 1. Check timing prediction
cat data/tier3_timing_predictions_$(date +%Y%m%d).json | grep -A 10 "해운"

# 2. Generate sector rankings
python3 generate_sector_rankings.py --sector "해운"

# 3. Verify small-cap vs large-cap split
cat data/sector_rankings_$(date +%Y%m%d).txt | grep -A 30 "해운" | grep "Tier"

# 4. Check if large-caps still in bear (confirms TIER 3 status)
cat data/sector_rankings_$(date +%Y%m%d).txt | grep -A 30 "해운" | grep "Bear Quiet"

# 5. Set monthly reminder to track regime flips
# (add to calendar: check 해운 monthly for mid-cap bull regime)
```

---

## Report Interpretation Guide

### Reading TIER 1 Recommendations

**Example**:
```
1. 철도 (47 stocks)
   📈 Cohesion: 17.73 → 24.95 (+7.22, +40.7%)
   💡 Investment Thesis: Strong established network with accelerating momentum
```

**What This Means**:
- **Baseline 17.73**: Already had established network (>15 threshold)
- **Change +7.22**: Strong weekly growth (>5.0 threshold)
- **47 stocks**: Large theme with many investment options
- **Action**: Review sector rankings to find top 3-5 large-cap tickers

**How to Execute**:
1. Run: `python3 generate_sector_rankings.py --sector "철도"`
2. Look for: Tier 1 large-caps (≥5T won) with Bull Quiet regime
3. Check: Composite score >0.80 and positive trend
4. Allocate: 20-30% of theme budget (e.g., 5M won → 1-1.5M won)
5. Diversify: 3-5 stocks × 200-500K won each

---

### Reading TIER 3 Research Priorities

**Example**:
```
해운 (Shipping)
  Current Fiedler: 6.00 | Target: 15.00 | Gap: 9.00
  ⏱️ Estimated: 5.6 months (Range: 4.0-7.8 months)
  📊 Velocity: 0.5/week | STEADY GROWTH
```

**What This Means**:
- **Current 6.00**: Early network formation (above TIER 4, below TIER 2)
- **Gap 9.00**: Needs to grow another 9 points to reach TIER 1
- **5.6 months**: Estimated time to become investable (with uncertainty)
- **STEADY**: Not accelerating or decelerating

**How to Research**:
1. **Verify Regime Split**:
   ```bash
   python3 generate_sector_rankings.py --sector "해운"
   # Check: Are small-caps in bull, large-caps in bear?
   ```

2. **Identify Catalyst**:
   - Why are small-caps forming network now?
   - What fundamental trend is emerging?
   - When will large-caps join?

3. **Set Monitoring Schedule**:
   - Monthly: Check for mid-cap regime flips
   - Quarterly: Re-assess timing estimate
   - Alert: When first large-cap flips to bull → start accumulation

4. **Pilot Position** (Optional):
   - 2-3% of portfolio in small-cap leaders
   - High risk, but 12-18 month early positioning

---

### Portfolio Allocation Example

**Total Portfolio**: 100M won (100%)

**Based on Synthesis Report**:
- **TIER 1 (50%)**: 50M won → 2 themes × 25M won each
  - 철도: 25M won → 5 stocks × 5M won each
  - 반도체 장비: 25M won → 5 stocks × 5M won each

- **TIER 2 (30%)**: 30M won → 5 themes × 6M won each
  - 온디바이스 AI: 6M won (DCA over 6 months = 1M/month)
  - 모바일솔루션: 6M won
  - 쿠팡: 6M won
  - 인터넷은행: 6M won
  - CCUS: 6M won

- **TIER 3 (15%)**: 15M won → 3 themes × 5M won each
  - 해운: 5M won (2-3 small-cap stocks, pilot position)
  - 조림사업: 5M won
  - 생명보험: 5M won

- **CASH (5%)**: 5M won
  - For opportunistic entries on pullbacks

**Execution Timeline**:
- **Week 1**: Buy TIER 1 stocks (50M won deployed)
- **Weeks 2-26**: DCA into TIER 2 (1.2M won/week for 25 weeks)
- **Weeks 4-8**: Build TIER 3 pilots (15M won over 5 weeks)

---

## Data Dependencies

### Required Input Files

For `run_weekly_analysis.sh` to work, you need:

1. **Naver Theme Cohesion Data** (weekly):
   - `data/naver_theme_fiedler_YYYYMMDD.csv`
   - Contains: Theme, Fiedler value, stock count
   - Source: Weekly cohesion analysis

2. **Regime Data** (weekly):
   - `/mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/` (regime status)
   - Source: AutoGluon LRS analysis

3. **Market Cap Data**:
   - Ticker market cap in DB units (10 = 1T won)
   - Source: KRX market data

4. **Naver Theme Mapping**:
   - `data/naver_sector_tickers.json` or similar
   - Maps themes → ticker codes

### Missing Data Handling

If data is missing for a specific date:

```bash
# Use most recent available data
./run_weekly_analysis.sh 20251020  # If 20251027 data not ready

# Or wait for data and run next day
./run_weekly_analysis.sh  # Uses today's date
```

The system will warn about missing files but continue where possible.

---

## Troubleshooting

### Problem: "4-tier data not found"

**Cause**: `analyze_4_tier_themes.py` hasn't been run for this date

**Solution**:
```bash
python3 analyze_4_tier_themes.py
```

---

### Problem: "Timing predictions incomplete"

**Cause**: Only 1-week velocity data available

**Expected**: This is normal until we build weekly timeseries aggregator

**Solution**:
- Reports will use qualitative estimates (Fast/Medium/Slow)
- Build `aggregate_naver_theme_fiedler_history.py` for quantitative predictions

---

### Problem: "Sector rankings not found"

**Cause**: `generate_sector_rankings.py` hasn't been run for specific themes

**Solution**:
```bash
# Run manually for TIER 1 themes
python3 generate_sector_rankings.py --sector "철도"
python3 generate_sector_rankings.py --sector "반도체 장비"

# Or let pipeline auto-generate (it will try)
./run_weekly_analysis.sh
```

---

### Problem: "No week-over-week comparison"

**Cause**: No data from previous week

**Solution**:
- First week: No comparison (expected)
- Subsequent weeks: Comparison will appear automatically
- Requires files from 7 days ago

---

## Future Enhancements

### Phase 1: Historical Timeseries (Week 1-2)
- [ ] Build `aggregate_naver_theme_fiedler_history.py`
- [ ] Generate 8+ months of weekly history
- [ ] Enable accurate velocity-based timing predictions

### Phase 2: Multi-Signal Integration (Week 3-4)
- [ ] Add score_percentage readiness method
- [ ] Add cascade stage progression tracking
- [ ] Build composite timing predictor with confidence scoring

### Phase 3: Advanced Reporting (Week 5-8)
- [ ] HTML dashboard with charts
- [ ] Email alerts for TIER promotions/demotions
- [ ] Mobile-friendly report format
- [ ] Integration with trading platform APIs

### Phase 4: Backtesting & Validation (Month 2-3)
- [ ] Track prediction accuracy over time
- [ ] Measure actual vs predicted timing
- [ ] Refine tier thresholds based on outcomes
- [ ] Build performance attribution system

---

## File Organization

```
/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/
│
├── scripts/
│   ├── run_weekly_analysis.sh          # Master pipeline
│   └── save_monthly_snapshot.sh        # Monthly data collection
│
├── data/
│   ├── tier1_buy_now_YYYYMMDD.csv      # TIER 1 themes
│   ├── tier2_accumulate_YYYYMMDD.csv   # TIER 2 themes
│   ├── tier3_research_YYYYMMDD.csv     # TIER 3 themes
│   ├── tier4_monitor_YYYYMMDD.csv      # TIER 4 themes
│   ├── 4tier_summary_YYYYMMDD.json     # Summary JSON
│   ├── tier3_timing_predictions_YYYYMMDD.json  # Timing data
│   └── sector_rankings_YYYYMMDD.txt    # Detailed rankings
│
├── reports/
│   ├── weekly_synthesis_YYYYMMDD.md    # Main synthesis reports
│   └── weekly_synthesis_YYYYMMDD.html  # HTML versions (if converted)
│
├── snapshots/
│   └── situation_YYYYMM.json           # Monthly UCS_LRS snapshots
│
├── logs/
│   └── weekly_YYYYMMDD.log             # Execution logs
│
└── Jobs/
    ├── generate_4_tier_investment_theme.md  # 4-tier guide
    └── how_to_run_sector_tickers_ordering.md  # Sector ranking guide
```

---

## Best Practices

### 1. Weekly Routine (Every Sunday)

```bash
# 18:00 - Run analysis
cd /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX
./run_weekly_analysis.sh

# 18:05 - Review report
cat reports/weekly_synthesis_$(date +%Y%m%d).md

# 18:15 - Check TIER 1 themes
# (Review sector rankings, identify top tickers)

# 18:30 - Plan next week's trades
# (Set up buy orders, adjust allocations)
```

### 2. Monthly Deep Dive (1st Sunday of Month)

```bash
# Generate monthly comparison
for week in 1 2 3 4; do
    date=$(date -d "$week weeks ago" +%Y%m%d)
    echo "=== Week $week ($date) ==="
    grep "TIER 1" reports/weekly_synthesis_${date}.md
done

# Research TIER 3 themes
cat data/tier3_research_$(date +%Y%m%d).csv | cut -d',' -f1

# Update timing estimates
python3 predict_timing.py
```

### 3. Quarterly Review (Every 3 Months)

```bash
# Track theme progressions
# Which TIER 3 themes moved to TIER 2 or TIER 1?
# Which predictions were accurate?
# Adjust allocation strategy based on outcomes
```

---

## Summary

**Daily/Weekly Reporting System**: ✅ Complete and Ready

**Key Features**:
- Automated pipeline (`run_weekly_analysis.sh`)
- Date-specific reports (historical and current)
- Actionable recommendations (buy, accumulate, research, monitor)
- Portfolio allocation guidance
- Week-over-week tracking

**To Get Started**:
```bash
./run_weekly_analysis.sh
cat reports/weekly_synthesis_$(date +%Y%m%d).md
```

**Weekly Workflow**:
1. Sunday 18:00: Run analysis
2. Sunday 18:15: Review report
3. Sunday 18:30: Plan trades
4. Monday-Friday: Execute action items
5. Next Sunday: Repeat

**Data Quality**:
- Current: Good (4-tier classification working)
- Near-term: Will improve (with weekly timeseries)
- Long-term: Excellent (with 6+ months of tracking)

The system is **production-ready** for weekly portfolio management and investment decision support.
