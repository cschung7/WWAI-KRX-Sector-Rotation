# Reconciliation: Cohesion Rankings vs Investment Tiers

## Problem Statement

**Issue**: NAVER_THEME_COHESION_REPORT shows 104 themes with strong cohesion enhancement, but INVESTMENT_IMPLICATIONS_REPORT shows 0 "Buy Now" (TIER 1) themes.

## Root Cause Analysis

### 4-Tier Classification Criteria (Too Strict)

The 4-tier classification uses **very strict criteria** that don't match actual Fiedler value ranges:

**TIER 1 (Buy NOW)**:
- Criteria: `Week_Before_Fiedler > 15` AND `Change > 5`
- Problem: Most themes have Fiedler values in 0.5-5.0 range, not >15
- Result: **0 themes qualify**

**TIER 2 (Accumulate)**:
- Criteria: `Week_Before_Fiedler 5-15` AND `Change > 2`
- Problem: Most themes have baseline Fiedler <5
- Result: **0 themes qualify**

**TIER 3 (Research)**:
- Criteria: `Week_Before_Fiedler 2-8` AND `Change > 1.5` AND `Pct_Change > 30%`
- Result: **3 themes qualify** (matches actual Fiedler ranges)

**TIER 4 (Monitor)**:
- Criteria: `Week_Before_Fiedler 0.5-3` AND `Change > 0.8` AND `Pct_Change > 40%`
- Result: **21 themes qualify**

### Actual Fiedler Value Ranges

From `enhanced_cohesion_themes_20251112.csv`:
- **Current Fiedler**: Typically 0.5-5.0 (mean ~1.2, max ~8.5)
- **Historical Fiedler**: Typically 0.2-3.0 (baseline before change)
- **Fiedler Change**: Typically 0.5-2.5 (most changes are <3.0)

### Top Cohesion Themes vs Tier Criteria

**Top 5 Cohesion Themes**:
1. OLED: Current=4.58, Historical=2.28, Change=+2.30
   - ❌ TIER 1: Historical (2.28) < 15
   - ❌ TIER 2: Historical (2.28) < 5
   - ✅ TIER 3: Historical (2.28) in 2-8 range, Change (2.30) > 1.5, Pct (101%) > 30%

2. 수소차: Current=3.58, Historical=1.31, Change=+2.27
   - ❌ TIER 1: Historical (1.31) < 15
   - ❌ TIER 2: Historical (1.31) < 5
   - ❌ TIER 3: Historical (1.31) < 2
   - ✅ TIER 4: Historical (1.31) in 0.5-3 range, Change (2.27) > 0.8, Pct (172%) > 40%

3. 유리 기판: Current=3.05, Historical=1.16, Change=+1.88
   - ✅ TIER 4: Historical (1.16) in 0.5-3 range, Change (1.88) > 0.8, Pct (161%) > 40%

## Solution: Adjust Tier Criteria

### Option 1: Scale Down Criteria (Recommended)

Adjust criteria to match actual Fiedler value ranges:

**TIER 1 (Buy NOW)** - Revised:
- `Week_Before_Fiedler > 2.0` AND `Change > 1.5` AND `Current_Fiedler > 3.0`
- Rationale: Strong baseline (>2.0) + significant improvement (>1.5) + high current cohesion (>3.0)

**TIER 2 (Accumulate)** - Revised:
- `Week_Before_Fiedler > 1.0` AND `Week_Before_Fiedler <= 2.0` AND `Change > 1.0`
- Rationale: Moderate baseline (1-2) + good improvement (>1.0)

**TIER 3 (Research)** - Keep Current:
- `Week_Before_Fiedler 0.5-2.0` AND `Change > 1.0` AND `Pct_Change > 30%`
- Rationale: Early formation + high % change

**TIER 4 (Monitor)** - Keep Current:
- `Week_Before_Fiedler 0.2-0.5` AND `Change > 0.5` AND `Pct_Change > 40%`
- Rationale: Seeds + very high % change

### Option 2: Use Percentile-Based Criteria

Use percentile-based thresholds instead of absolute values:
- **TIER 1**: Top 10% by current Fiedler AND top 20% by change
- **TIER 2**: Top 25% by current Fiedler AND top 30% by change
- **TIER 3**: Top 50% by current Fiedler AND top 40% by % change
- **TIER 4**: Remaining themes with positive change

### Option 3: Hybrid Approach (Best)

Combine absolute thresholds with percentile ranking:

**TIER 1 (Buy NOW)**:
- Current Fiedler > 3.0 (absolute threshold) OR
- Top 10% by current Fiedler (percentile) AND
- Change > 1.5 AND
- Pct_Change > 50%

**TIER 2 (Accumulate)**:
- Current Fiedler > 2.0 OR
- Top 25% by current Fiedler AND
- Change > 1.0 AND
- Pct_Change > 30%

## Recommended Implementation

### Step 1: Update `analyze_4_tier_themes.py`

Modify the `analyze_tiers()` method to use scaled criteria:

```python
def analyze_tiers(self):
    """Classify themes into 4 tiers with adjusted criteria"""
    
    # TIER 1: Buy NOW (strong base + strong change + high current)
    tier1 = self.df[
        (self.df['Week_Before_Fiedler'] > 2.0) &
        (self.df['Change'] > 1.5) &
        (self.df['Last_Week_Fiedler'] > 3.0)
    ].sort_values('Change', ascending=False)
    
    # TIER 2: Accumulate (moderate base + good change)
    tier2 = self.df[
        (self.df['Week_Before_Fiedler'] > 1.0) &
        (self.df['Week_Before_Fiedler'] <= 2.0) &
        (self.df['Change'] > 1.0)
    ].sort_values('Change', ascending=False)
    
    # TIER 3: Research (early formation + high % change)
    tier3 = self.df[
        (self.df['Week_Before_Fiedler'] > 0.5) &
        (self.df['Week_Before_Fiedler'] <= 2.0) &
        (self.df['Change'] > 1.0) &
        (self.df['Pct_Change'] > 30)
    ].sort_values('Pct_Change', ascending=False)
    
    # TIER 4: Monitor (seeds + very high % change)
    tier4 = self.df[
        (self.df['Week_Before_Fiedler'] > 0.2) &
        (self.df['Week_Before_Fiedler'] <= 0.5) &
        (self.df['Change'] > 0.5) &
        (self.df['Pct_Change'] > 40)
    ].sort_values('Pct_Change', ascending=False)
    
    return tier1, tier2, tier3, tier4
```

### Step 2: Add Reconciliation Section to Investment Implications Report

Add a section explaining the relationship between cohesion rankings and investment tiers:

```markdown
## 🔄 RECONCILIATION: COHESION RANKINGS vs INVESTMENT TIERS

### Why Strong Cohesion ≠ "Buy Now"

**Cohesion Rankings** (from NAVER_THEME_COHESION_REPORT):
- Focus: Themes with **strongest Fiedler enhancement** (change)
- Top themes: OLED (+2.30), 수소차 (+2.27), 유리 기판 (+1.88)

**Investment Tiers** (from this report):
- Focus: Themes with **strong baseline + strong change + high current**
- TIER 1 requires: Baseline >2.0 AND Change >1.5 AND Current >3.0

**Key Insight**: A theme can have strong **enhancement** (high % change from low base) but still not qualify for "Buy Now" if:
1. Baseline Fiedler is too low (<2.0)
2. Current Fiedler is not high enough (<3.0)
3. Change is not substantial enough (<1.5)

**Example**: 수소차 has +172% change, but baseline is only 1.31 → TIER 4 (Monitor), not TIER 1
```

## Expected Impact

### Before Fix:
- TIER 1: 0 themes
- TIER 2: 0 themes
- TIER 3: 3 themes
- TIER 4: 21 themes

### After Fix (with scaled criteria):
- TIER 1: ~5-10 themes (OLED, 전기차, 증권, etc.)
- TIER 2: ~10-15 themes
- TIER 3: ~15-20 themes
- TIER 4: ~20-30 themes

## Next Steps

1. **Update tier criteria** in `analyze_4_tier_themes.py`
2. **Regenerate 4-tier classification** for 2025-11-12
3. **Regenerate Investment Implications report**
4. **Add reconciliation section** to explain the relationship
5. **Test with historical data** to ensure criteria are appropriate

