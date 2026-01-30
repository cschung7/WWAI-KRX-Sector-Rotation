# Timing Prediction - Next Steps After POC Testing

## What We Learned

### ✅ Proof of Concept Success
The velocity-based prediction framework is **conceptually sound** but reveals **critical data requirements**.

### ❌ Current Limitation
Using only 1-week velocity snapshot (Week_Before vs Last_Week) produces unrealistic estimates:
- All TIER 3 themes predict < 1.1 months to TIER 1
- This assumes current week's velocity continues linearly
- Reality: Most themes grew over MONTHS to reach current Fiedler values

### 🎯 Root Cause
The CSV file `tier3_research_20251027.csv` contains:
```
Theme,Stocks,Week_Before_Fiedler,Last_Week_Fiedler,Change,Pct_Change
해운,6,2.00,6.00,+4.00,+200%
```

This shows TWO SNAPSHOTS, not continuous weekly history. The +4.00 change represents **cumulative growth over unknown timespan**, not 1 week of velocity.

---

## Required Data Sources

### 1. **Continuous Weekly Fiedler History** (CRITICAL)

**What We Need**: Weekly Fiedler values for each Naver theme going back 6-12 months

**Current Status**:
- ✅ Have: Sector-level weekly data in `/mnt/nas/gpt/Naver/three_layers/countryrisk/data_sectors/`
- ❌ Missing: Naver theme-level aggregation from weekly snapshots

**Example Required Format**:
```csv
theme,date,fiedler,n_stocks,mean_correlation
해운,2025-02-04,0.82,6,0.42
해운,2025-02-11,1.05,6,0.45
해운,2025-02-18,1.23,6,0.48
...
해운,2025-10-20,2.00,6,0.58
해운,2025-10-27,6.00,6,0.75
```

**Action Required**:
```bash
# Create historical aggregation script
python3 scripts/aggregate_naver_theme_fiedler_history.py

# This should:
# 1. Load weekly sector data from data_sectors/
# 2. Map tickers to Naver themes
# 3. Calculate weekly theme-level Fiedler values
# 4. Output: data/naver_theme_fiedler_timeseries.csv
```

### 2. **Monthly Score Percentage Snapshots**

**What We Need**: Historical `complete_situation_results_*.json` files saved monthly

**Current Status**:
- ✅ Have: Oct 2025 snapshot
- ❌ Missing: Feb-Sep 2025 snapshots (if they exist)

**Action Required**:
```bash
# Check if historical snapshots exist
ls -lh /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_*.json

# If found, copy to tracking directory
mkdir -p /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/snapshots/
cp /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_*.json \
   snapshots/

# Set up monthly cron job for future
# (See crontab setup in TIMING_ESTIMATION_BRAINSTORM.md)
```

### 3. **Weekly Regime Cascade Data**

**What We Need**: Weekly snapshots of bull/bear regime status by market cap tier

**Current Status**:
- ✅ Can generate: Using `generate_sector_rankings.py --sector "THEME"`
- ❌ Missing: Historical weekly execution and storage

**Action Required**:
```bash
# Create weekly cascade tracking script
cat > scripts/track_weekly_cascade.py << 'EOF'
# For each Naver theme:
#   1. Run generate_sector_rankings.py
#   2. Count bulls by tier (Tier 1, 2, 3)
#   3. Save to: data/cascade_history/YYYYMMDD_cascade.csv
# Output format:
#   date,theme,tier1_pct_bull,tier2_pct_bull,tier3_pct_bull
EOF

# Schedule weekly execution (e.g., every Sunday 18:00)
```

---

## Revised Implementation Plan

### Phase 1A: Historical Data Assembly (URGENT - Week 1)

#### Task 1.1: Aggregate Naver Theme Fiedler History
**Priority**: CRITICAL
**Effort**: 2-4 hours

Create script to aggregate weekly Fiedler values by Naver theme:

```python
#!/usr/bin/env python3
"""
Aggregate sector-level weekly Fiedler data into Naver theme timeseries
"""

import pandas as pd
from pathlib import Path
import json

def load_naver_theme_mapping():
    """Load Naver theme → ticker mapping"""
    # Use existing naver_sector_tickers.json or similar
    pass

def aggregate_weekly_fiedler(start_date, end_date):
    """
    For each week:
    1. Load sector correlation matrices
    2. Map tickers to Naver themes
    3. Calculate theme-level Fiedler values
    4. Save weekly theme snapshots
    """
    pass

# Expected output:
# data/naver_theme_fiedler_timeseries.csv (35+ weeks × 200+ themes)
```

**Deliverable**: `data/naver_theme_fiedler_timeseries.csv`

**Validation**:
- Verify 해운 (Shipping) shows gradual growth from ~1.0 → 6.0 over 8 months
- Not sudden jump from 2.0 → 6.0 in 1 week

#### Task 1.2: Search for Historical Score Snapshots
**Priority**: HIGH
**Effort**: 30 minutes

```bash
# Search entire AutoGluon directory for historical files
find /mnt/nas/AutoGluon -name "*complete_situation*" -type f 2>/dev/null

# Check backup directories
find /mnt/nas/AutoGluon -name "*backup*" -type d 2>/dev/null

# If found, organize chronologically
```

**Best Case**: Find Feb-Sep 2025 snapshots
**Worst Case**: Only have Oct 2025 (start collecting monthly from now)

#### Task 1.3: Generate Historical Cascade Data (if possible)
**Priority**: MEDIUM
**Effort**: 1-2 hours

If we have historical regime data from LRS database:

```python
# Query historical regime status
# For each (date, theme):
#   - Count bulls by market cap tier
#   - Calculate progression metrics
```

**Deliverable**: `data/historical_cascade_stages.csv`

### Phase 1B: Recalibrated Velocity Predictions (Week 2)

Once we have proper weekly history:

```python
class ImprovedThemeTimingPredictor:
    def calculate_velocity_multi_week(self, theme_history):
        """
        Use 8-12 weeks of history instead of 1 week

        1. Calculate 4-week moving average velocity
        2. Detect acceleration/deceleration trends
        3. Fit polynomial or exponential growth curve
        4. Extrapolate to threshold with confidence bands
        """

        # Example with real history
        weeks = theme_history['date']
        fiedler = theme_history['fiedler']

        # 4-week velocity
        velocity_4w = (fiedler[-1] - fiedler[-5]) / 4

        # 8-week velocity for comparison
        velocity_8w = (fiedler[-1] - fiedler[-9]) / 8

        # Detect acceleration
        if velocity_4w > velocity_8w * 1.3:
            status = "ACCELERATING"
        elif velocity_4w < velocity_8w * 0.7:
            status = "DECELERATING"
        else:
            status = "STEADY"

        # Use conservative velocity estimate
        velocity_estimate = np.mean([velocity_4w, velocity_8w])

        # Calculate time to threshold
        gap = 15.0 - fiedler[-1]
        weeks_to_threshold = gap / velocity_estimate
        months_to_threshold = weeks_to_threshold / 4.33

        return {
            'estimated_months': months_to_threshold,
            'velocity_4w': velocity_4w,
            'velocity_8w': velocity_8w,
            'acceleration_status': status
        }
```

**Expected Results**:
- 해운 (Shipping): 9-15 months (not 0.4 months)
- 조림사업 (Forestry): 12-18 months
- More realistic distribution across 6-24 month range

### Phase 2: Multi-Method Integration (Week 3-4)

Once velocity method is calibrated:
1. Add score_percentage readiness method
2. Add cascade stage method
3. Create weighted ensemble
4. Validate predictions

### Phase 3: Production Deployment (Week 5-6)

1. Weekly automated predictions
2. Monthly recalibration
3. Dashboard integration
4. Alert system for acceleration/deceleration

---

## Immediate Actions (This Week)

### Action 1: Check for Historical Data
```bash
# Run comprehensive search
find /mnt/nas/AutoGluon -name "*situation*" -mtime +30 2>/dev/null
find /mnt/nas/gpt/Naver -name "*fiedler*history*" 2>/dev/null

# Check if we have weekly snapshots anywhere
ls -lh /mnt/nas/gpt/Naver/three_layers/fiedler_var/ 2>/dev/null
```

### Action 2: Create Naver Theme Historical Aggregator
```bash
# Priority script to build
touch scripts/aggregate_naver_theme_fiedler_history.py
chmod +x scripts/aggregate_naver_theme_fiedler_history.py

# This will unlock accurate velocity predictions
```

### Action 3: Set Up Monthly Snapshot Collection
```bash
# Start capturing going forward
cat > scripts/save_monthly_snapshot.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m)
cp /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_*.json \
   snapshots/situation_${DATE}.json
echo "Snapshot saved: situation_${DATE}.json"
EOF

chmod +x scripts/save_monthly_snapshot.sh

# Add to crontab: 1st of each month at 18:00
# 0 18 1 * * /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/scripts/save_monthly_snapshot.sh
```

---

## Realistic Timeline Estimates (Based on Experience)

Without proper historical data, we can provide **qualitative estimates** based on pattern recognition:

### Fast-Moving Themes (6-9 months to TIER 1)
**Characteristics**:
- Already near TIER 2 threshold (Fiedler 10-13)
- Multiple large-caps already in bull regime
- Recent catalyst or trend acceleration

**Current Candidates**:
- 모바일솔루션(스마트폰): Fiedler 11.32, already has momentum
- 온실가스(CCUS): Fiedler 9.42, strong ESG tailwind

### Standard TIER 3 (12-18 months)
**Characteristics**:
- Fiedler 5-8, solid baseline forming
- Some mid-caps in bull, large-caps mostly bear
- Fundamental thesis developing

**Current Candidates**:
- 해운 (Shipping): Fiedler 6.00, classic TIER 3 pattern
- 조림사업 (Forestry): Fiedler 7.35, ESG theme with long runway

### Slow-Moving Themes (18-24 months)
**Characteristics**:
- Fiedler 2-5, early stage formation
- Mostly small-caps, large-caps in deep bear
- Speculative or niche sector

**Current Candidates**:
- 화이자(PFIZER): Fiedler 5.00, narrow theme
- 아스콘(아스팔트): Fiedler 5.00, cyclical sector

### High-Risk Seeds (24+ months or may fail)
**Characteristics**:
- Fiedler <3, very early stage
- No large-cap participation
- Uncertain catalyst

**Current Candidates**:
- Would be in TIER 4, not TIER 3

---

## Conclusion

### ✅ Framework is Sound
The velocity-based timing prediction is **conceptually correct** and will work well once we have proper data.

### ❌ Missing Critical Input
Cannot produce accurate predictions without:
1. **Weekly Fiedler history** (8-12 months minimum)
2. **Monthly score snapshots** (for validation)
3. **Cascade progression tracking** (for multi-signal confirmation)

### 🎯 Next Priority
**Create `aggregate_naver_theme_fiedler_history.py`** to unlock the framework.

Once this is built, we can re-run `predict_timing.py` and get **realistic 6-24 month estimates** instead of the current 0.2-1.1 month unrealistic projections.

### 📊 Current Workaround
Until then, use **qualitative classification**:
- Fast (6-9mo): Fiedler >10, large-caps participating
- Medium (12-18mo): Fiedler 5-10, mid-caps leading
- Slow (18-24mo): Fiedler 2-5, small-caps only

This matches the TIER 3 research framework's original 12-18 month baseline estimate.
