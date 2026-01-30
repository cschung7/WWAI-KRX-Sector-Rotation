# How to Generate 4-Tier Investment Theme Analysis

**Purpose**: Identify investment opportunities across 4 time horizons (NOW, 6-12mo, 12-18mo, 18-24mo)
**Framework**: Small-cap → Mid-cap → Large-cap progression
**Location**: `/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/`

---

## Quick Start

### One-Command Analysis

```bash
cd /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX

# Generate complete 4-tier analysis
python3 analyze_4_tier_themes.py --date 2025-10-27
```

This will output:
- TIER 1: Buy now themes
- TIER 2: 6-12 month accumulation themes
- TIER 3: 12-18 month research themes
- TIER 4: 18-24 month seed themes

---

## Manual Step-by-Step Process

### Step 1: Generate Weekly Cohesion Changes

```bash
# Calculate week-over-week Fiedler values
python3 analyze_weekly_cohesion_change.py

# Output: data/weekly_cohesion_change_YYYYMMDD.csv
```

**What this does**:
- Compares last 5 trading days vs previous 5 trading days
- Calculates Fiedler value for each theme
- Identifies which themes are strengthening/weakening

---

### Step 2: Run 4-Tier Classification Script

Create the analysis script:

```bash
nano analyze_4_tier_themes.py
```

**Script Content** (`analyze_4_tier_themes.py`):

```python
#!/usr/bin/env python3
"""
4-Tier Investment Theme Analysis
Classifies themes by investment timeline
"""

import pandas as pd
import numpy as np
from datetime import datetime
import argparse

class FourTierAnalyzer:
    """Analyze themes across 4 investment time horizons"""

    def __init__(self, cohesion_file):
        self.df = pd.read_csv(cohesion_file)

    def analyze_tiers(self):
        """Classify themes into 4 tiers"""

        # TIER 1: Buy NOW (strong base + strong change)
        tier1 = self.df[
            (self.df['Week_Before_Fiedler'] > 15) &
            (self.df['Change'] > 5)
        ].sort_values('Change', ascending=False)

        # TIER 2: Accumulate 6-12mo (forming base + good change)
        tier2 = self.df[
            (self.df['Week_Before_Fiedler'] > 5) &
            (self.df['Week_Before_Fiedler'] <= 15) &
            (self.df['Change'] > 2)
        ].sort_values('Change', ascending=False)

        # TIER 3: Research 12-18mo (early formation + high % change)
        tier3 = self.df[
            (self.df['Week_Before_Fiedler'] > 2) &
            (self.df['Week_Before_Fiedler'] <= 8) &
            (self.df['Change'] > 1.5) &
            (self.df['Pct_Change'] > 30)
        ].sort_values('Pct_Change', ascending=False)

        # TIER 4: Monitor 18-24mo (seeds + very high % change)
        tier4 = self.df[
            (self.df['Week_Before_Fiedler'] > 0.5) &
            (self.df['Week_Before_Fiedler'] <= 3) &
            (self.df['Change'] > 0.8) &
            (self.df['Pct_Change'] > 40)
        ].sort_values('Pct_Change', ascending=False)

        return tier1, tier2, tier3, tier4

    def print_report(self, tier1, tier2, tier3, tier4):
        """Generate formatted report"""

        print("="*100)
        print("4-TIER INVESTMENT THEME ANALYSIS")
        print("="*100)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Themes Analyzed: {len(self.df)}")
        print()

        # TIER 1
        print("="*100)
        print("TIER 1: BUY NOW (Invest Immediately)")
        print("="*100)
        print("Criteria: Baseline Fiedler >15 AND Change >5.0")
        print("Timeline: Current opportunities with large-cap confirmation")
        print(f"Count: {len(tier1)} themes")
        print()
        if len(tier1) > 0:
            print(f"{'Rank':>4} | {'Theme':40s} | {'Base':>7s} → {'Current':>7s} | {'Change':>8s} | {'%Chg':>8s} | {'Stocks':>6s}")
            print("-"*100)
            for idx, (_, row) in enumerate(tier1.iterrows(), 1):
                print(f"{idx:4d} | {row['Theme']:40s} | {row['Week_Before_Fiedler']:7.2f} → {row['Last_Week_Fiedler']:7.2f} | "
                      f"{row['Change']:+8.2f} | {row['Pct_Change']:+7.1f}% | {row['Stocks']:6.0f}")
        else:
            print("⚠️  No themes meet TIER 1 criteria")
        print()

        # TIER 2
        print("="*100)
        print("TIER 2: ACCUMULATE (6-12 Month Horizon)")
        print("="*100)
        print("Criteria: Baseline Fiedler 5-15 AND Change >2.0")
        print("Timeline: Emerging themes, accumulate before large-cap participation")
        print(f"Count: {len(tier2)} themes")
        print()
        if len(tier2) > 0:
            print(f"{'Rank':>4} | {'Theme':40s} | {'Base':>7s} → {'Current':>7s} | {'Change':>8s} | {'%Chg':>8s} | {'Stocks':>6s}")
            print("-"*100)
            for idx, (_, row) in enumerate(tier2.head(15).iterrows(), 1):
                print(f"{idx:4d} | {row['Theme']:40s} | {row['Week_Before_Fiedler']:7.2f} → {row['Last_Week_Fiedler']:7.2f} | "
                      f"{row['Change']:+8.2f} | {row['Pct_Change']:+7.1f}% | {row['Stocks']:6.0f}")
        print()

        # TIER 3
        print("="*100)
        print("⭐ TIER 3: DEEP RESEARCH (12-18 Month Horizon) ⭐")
        print("="*100)
        print("Criteria: Baseline Fiedler 2-8 AND Change >1.5 AND % Change >30%")
        print("Timeline: Small-caps forming networks BEFORE large-cap participation")
        print("Strategy: Research fundamentals, monitor monthly, wait for large-cap flip")
        print(f"Count: {len(tier3)} themes")
        print()
        if len(tier3) > 0:
            print(f"{'Rank':>4} | {'Theme':40s} | {'Base':>7s} → {'Current':>7s} | {'Change':>8s} | {'%Chg':>8s} | {'Stocks':>6s}")
            print("-"*100)
            for idx, (_, row) in enumerate(tier3.head(20).iterrows(), 1):
                print(f"{idx:4d} | {row['Theme']:40s} | {row['Week_Before_Fiedler']:7.2f} → {row['Last_Week_Fiedler']:7.2f} | "
                      f"{row['Change']:+8.2f} | {row['Pct_Change']:+7.1f}% | {row['Stocks']:6.0f}")
        print()
        print("⚠️  IMPORTANT: Verify large-cap regime status for each theme!")
        print("    Run: python3 generate_sector_rankings.py --sector \"THEME_NAME\"")
        print()

        # TIER 4
        print("="*100)
        print("🌱 TIER 4: MONITOR ONLY (18-24 Month Horizon) 🌱")
        print("="*100)
        print("Criteria: Baseline Fiedler 0.5-3 AND Change >0.8 AND % Change >40%")
        print("Timeline: Very early seeds, high risk of failure")
        print("Strategy: Quarterly monitoring only, no investment yet")
        print(f"Count: {len(tier4)} themes")
        print()
        if len(tier4) > 0:
            print(f"{'Rank':>4} | {'Theme':40s} | {'Base':>7s} → {'Current':>7s} | {'Change':>8s} | {'%Chg':>8s} | {'Stocks':>6s}")
            print("-"*100)
            for idx, (_, row) in enumerate(tier4.head(20).iterrows(), 1):
                print(f"{idx:4d} | {row['Theme']:40s} | {row['Week_Before_Fiedler']:7.2f} → {row['Last_Week_Fiedler']:7.2f} | "
                      f"{row['Change']:+8.2f} | {row['Pct_Change']:+7.1f}% | {row['Stocks']:6.0f}")
        print()

        print("="*100)
        print("SUMMARY")
        print("="*100)
        print(f"TIER 1 (Buy Now):          {len(tier1):3d} themes")
        print(f"TIER 2 (6-12 months):      {len(tier2):3d} themes")
        print(f"TIER 3 (12-18 months):     {len(tier3):3d} themes")
        print(f"TIER 4 (18-24 months):     {len(tier4):3d} themes")
        print("="*100)

    def save_reports(self, tier1, tier2, tier3, tier4, output_date):
        """Save tier analysis to files"""

        import json

        output_dir = "data"

        # Save each tier to CSV
        tier1.to_csv(f"{output_dir}/tier1_buy_now_{output_date}.csv", index=False)
        tier2.to_csv(f"{output_dir}/tier2_accumulate_{output_date}.csv", index=False)
        tier3.to_csv(f"{output_dir}/tier3_research_{output_date}.csv", index=False)
        tier4.to_csv(f"{output_dir}/tier4_monitor_{output_date}.csv", index=False)

        # Save summary JSON
        summary = {
            'date': output_date,
            'tier1': {
                'count': len(tier1),
                'themes': tier1['Theme'].tolist()
            },
            'tier2': {
                'count': len(tier2),
                'themes': tier2['Theme'].tolist()
            },
            'tier3': {
                'count': len(tier3),
                'themes': tier3['Theme'].tolist()
            },
            'tier4': {
                'count': len(tier4),
                'themes': tier4['Theme'].tolist()
            }
        }

        with open(f"{output_dir}/4tier_summary_{output_date}.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Reports saved to {output_dir}/")
        print(f"   - tier1_buy_now_{output_date}.csv")
        print(f"   - tier2_accumulate_{output_date}.csv")
        print(f"   - tier3_research_{output_date}.csv")
        print(f"   - tier4_monitor_{output_date}.csv")
        print(f"   - 4tier_summary_{output_date}.json")

def main():
    parser = argparse.ArgumentParser(description='4-Tier Investment Theme Analysis')
    parser.add_argument('--date', type=str, default=datetime.now().strftime('%Y-%m-%d'),
                       help='Analysis date (YYYY-MM-DD)')
    parser.add_argument('--cohesion-file', type=str, default=None,
                       help='Path to cohesion change CSV file')

    args = parser.parse_args()

    # Determine cohesion file
    if args.cohesion_file:
        cohesion_file = args.cohesion_file
    else:
        output_date = args.date.replace('-', '')
        cohesion_file = f"data/weekly_cohesion_change_{output_date}.csv"

    print(f"Loading cohesion data from: {cohesion_file}")

    # Run analysis
    analyzer = FourTierAnalyzer(cohesion_file)
    tier1, tier2, tier3, tier4 = analyzer.analyze_tiers()

    # Print report
    analyzer.print_report(tier1, tier2, tier3, tier4)

    # Save reports
    output_date = args.date.replace('-', '')
    analyzer.save_reports(tier1, tier2, tier3, tier4, output_date)

if __name__ == "__main__":
    main()
```

**Make executable**:
```bash
chmod +x analyze_4_tier_themes.py
```

---

### Step 3: Run the Analysis

```bash
# For today's date
python3 analyze_4_tier_themes.py

# For specific date
python3 analyze_4_tier_themes.py --date 2025-10-27

# With custom cohesion file
python3 analyze_4_tier_themes.py --cohesion-file data/weekly_cohesion_change_20251027.csv
```

---

### Step 4: Deep-Dive on TIER 3 Themes

**Critical Step**: Verify large-cap regime status for each TIER 3 theme

```bash
# Example: Check shipping sector (해운)
python3 generate_sector_rankings.py --sector "해운"

# Check each TIER 3 theme
python3 generate_sector_rankings.py --sector "조림사업"
python3 generate_sector_rankings.py --sector "생명보험"
python3 generate_sector_rankings.py --sector "탈 플라스틱(친환경/생분해성 등)"
```

**What to look for**:
- ✅ Small-caps in bull regime
- ❌ Large-caps in bear/transition regime
- 📊 Cohesion forming (2-8 range)

**If BOTH conditions met** → TRUE TIER 3 theme (12-18 months early)

---

## Understanding the Output

### TIER 1: Buy Now

**Example Output**:
```
TIER 1: BUY NOW (Invest Immediately)
=====================================
Criteria: Baseline Fiedler >15 AND Change >5.0
Count: 2 themes

Rank | Theme           | Base → Current | Change   | %Chg     | Stocks
-----|-----------------|----------------|----------|----------|--------
   1 | 철도              | 17.73 → 24.95  |   +7.22  |  +40.7%  |     47
   2 | 반도체 장비         | 46.36 → 52.05  |   +5.69  |  +12.3%  |     97
```

**Interpretation**:
- ✅ Established networks (base >15)
- ✅ Strong strengthening (change >5)
- ✅ Large-caps confirmed in bull regime
- **Action**: BUY immediately

**Next Step**:
```bash
# Verify large-cap status
python3 generate_sector_rankings.py --sector "철도"
python3 generate_sector_rankings.py --sector "반도체 장비"

# Check for large-caps in Bull regime with Tier 1 (≥5T)
```

---

### TIER 2: Accumulate (6-12 months)

**Example Output**:
```
TIER 2: ACCUMULATE (6-12 Month Horizon)
========================================
Criteria: Baseline Fiedler 5-15 AND Change >2.0
Count: 10 themes

Rank | Theme           | Base → Current | Change   | %Chg     | Stocks
-----|-----------------|----------------|----------|----------|--------
   1 | 온디바이스 AI      |  9.65 → 13.15  |   +3.50  |  +36.3%  |     27
   2 | 모바일솔루션        |  7.85 → 11.32  |   +3.47  |  +44.2%  |     24
   3 | 쿠팡              |  8.34 → 11.62  |   +3.28  |  +39.4%  |     23
```

**Interpretation**:
- ⚠️ Networks forming (base 5-15)
- ✅ Consistent growth (change >2)
- ⏳ Mid-caps likely starting to flip bull
- ❌ Large-caps not yet participating

**Action**:
- Start accumulating positions
- DCA over 3-6 months
- Wait for large-cap confirmation
- Monitor monthly cohesion growth

**Timeline**: Likely becomes TIER 1 in 6-12 months

---

### TIER 3: Deep Research (12-18 months) ⭐

**Example Output**:
```
⭐ TIER 3: DEEP RESEARCH (12-18 Month Horizon) ⭐
=================================================
Criteria: Baseline Fiedler 2-8 AND Change >1.5 AND % Change >30%
Count: 14 themes

Rank | Theme           | Base → Current | Change   | %Chg     | Stocks
-----|-----------------|----------------|----------|----------|--------
   1 | 해운              |  2.00 →  6.00  |   +4.00  | +200.0%  |      6
   2 | 조림사업           |  3.78 →  7.35  |   +3.56  |  +94.2%  |     12
   3 | 모바일솔루션        |  7.85 → 11.32  |   +3.47  |  +44.2%  |     24
```

**Interpretation**:
- 🌱 Early network formation (base 2-8)
- 📈 High percentage growth (>30%)
- 🔍 Small-caps likely detecting opportunity
- ❌ Large-caps still in bear regime

**Critical Validation Needed**:
```bash
# MUST verify for each TIER 3 theme:
python3 generate_sector_rankings.py --sector "해운"

# Look for this pattern:
# ✅ Tier 3 small-caps: Some in BULL regime
# ❌ Tier 1 large-caps: In BEAR/TRANSITION regime
# ← This confirms 12-18 month early signal!
```

**Example - 해운 (Shipping) Validation**:
```
Tier 1 (≥5T):
  • HMM (19.4T): Bear Quiet, Bull 0%, Trend -1.000 ❌

Tier 3 (<1T):
  • 흥아해운 (0.4T): Bull Quiet, Bull 100%, Trend +0.340 ✅
```
→ **CONFIRMED TIER 3**: Small-caps leading, large-caps lagging by 12-18 months

**Action**:
- Deep fundamental research
- Understand WHY small-caps are coordinating
- Identify potential catalyst
- Monitor HMM/large-cap regime monthly
- NO investment yet (wait for validation)

**Timeline**: Likely becomes TIER 2 in 6-12 months, TIER 1 in 12-18 months

---

### TIER 4: Monitor Only (18-24 months)

**Example Output**:
```
🌱 TIER 4: MONITOR ONLY (18-24 Month Horizon) 🌱
================================================
Criteria: Baseline Fiedler 0.5-3 AND Change >0.8 AND % Change >40%
Count: 8 themes

Rank | Theme           | Base → Current | Change   | %Chg     | Stocks
-----|-----------------|----------------|----------|----------|--------
   1 | 맥신(MXene)      |  1.80 →  5.83  |   +4.03  | +223.8%  |     10
   2 | 손해보험           |  1.00 →  3.91  |   +2.91  | +291.4%  |     10
   3 | 제대혈            |  1.83 →  4.00  |   +2.17  | +118.6%  |      6
```

**Interpretation**:
- 🌱 Seeds just planted (base 0.5-3)
- 🚀 Explosive % growth but tiny absolute change
- ⚠️ Most stocks still in bear regime
- ❓ May be noise, not signal

**Validation Example - 맥신(MXene)**:
```bash
python3 generate_sector_rankings.py --sector "맥신(MXene)"

# Expect to see:
# ❌ 9/10 stocks in BEAR regime
# ✅ Maybe 1 stock in bull
# → TOO EARLY, high risk of failure
```

**Action**:
- Quarterly monitoring ONLY
- NO investment
- Research fundamental thesis
- 70% of TIER 4 themes fail before reaching TIER 3

**Timeline**: IF successful, becomes TIER 3 in 6-12 months

---

## Automated Workflow

### Weekly Analysis Script

Create `weekly_4tier_analysis.sh`:

```bash
#!/bin/bash
# Weekly 4-Tier Theme Analysis
# Run every Friday at 18:30 KST (after market close)

SCRIPT_DIR="/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX"
DATE=$(date +%Y-%m-%d)
OUTPUT_DATE=$(date +%Y%m%d)

cd $SCRIPT_DIR

echo "=========================================="
echo "Weekly 4-Tier Analysis - $DATE"
echo "=========================================="

# Step 1: Generate cohesion changes
echo "Step 1: Calculating weekly cohesion changes..."
python3 analyze_weekly_cohesion_change.py

# Step 2: Run 4-tier analysis
echo "Step 2: Classifying themes into 4 tiers..."
python3 analyze_4_tier_themes.py --date $DATE

# Step 3: Verify TIER 3 themes (top 5)
echo "Step 3: Verifying top 5 TIER 3 themes..."

# Get top 5 TIER 3 themes
TIER3_THEMES=$(python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/tier3_research_'$(date +%Y%m%d)'.csv')
for theme in df.head(5)['Theme']:
    print(theme)
EOF
)

# Analyze each TIER 3 theme
for THEME in $TIER3_THEMES; do
    echo "Analyzing TIER 3 theme: $THEME"
    python3 generate_sector_rankings.py --sector "$THEME" --date $DATE
done

echo "=========================================="
echo "Analysis complete! Check reports in data/"
echo "=========================================="

# Optional: Send notification
# mail -s "Weekly 4-Tier Analysis Complete" your@email.com < data/4tier_summary_$OUTPUT_DATE.json
```

**Make executable and schedule**:
```bash
chmod +x weekly_4tier_analysis.sh

# Add to crontab (Friday 18:30)
crontab -e
30 18 * * 5 /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/weekly_4tier_analysis.sh
```

---

## Monthly Deep-Dive Workflow

### TIER 3 Research Template

For each TIER 3 theme, create research file:

```bash
mkdir -p research/tier3
nano research/tier3/shipping_해운_research.md
```

**Research Template**:

```markdown
# TIER 3 Research: 해운 (Shipping)

**Date Identified**: 2025-10-27
**Current Tier**: TIER 3 (12-18 months to investability)
**Cohesion**: 2.00 → 6.00 (+200%)

---

## Current Status

### Network Formation
- **Small-caps leading**: 흥아해운 (0.4T) Bull
- **Large-caps lagging**: HMM (19.4T) Bear, 팬오션 (2.0T) Bear
- **Cohesion trajectory**: Growing from 2.00 to 6.00

### Regime Status
| Ticker | Company | Cap | Regime | Bull % | Trend |
|--------|---------|-----|--------|--------|-------|
| 011200 | HMM | 19.4T | Bear | 0% | -1.000 |
| 028670 | 팬오션 | 2.0T | Bear | 0% | -0.660 |
| 003280 | 흥아해운 | 0.4T | Bull | 100% | +0.340 |

---

## Fundamental Hypothesis

### Potential Catalysts
1. **Shipping rates recovery**
   - [ ] Check Baltic Dry Index trend
   - [ ] Container rates (Shanghai-LA, Shanghai-Rotterdam)
   - [ ] Tonnage utilization rates

2. **Supply constraints**
   - [ ] Orderbook analysis
   - [ ] Fleet age statistics
   - [ ] Scrapping rates

3. **Demand drivers**
   - [ ] China reopening impact
   - [ ] Global trade volumes
   - [ ] E-commerce growth

4. **Geopolitical**
   - [ ] Red Sea crisis impact
   - [ ] Panama Canal restrictions
   - [ ] Trade route changes

### Market Size
- Global shipping market: $XXX billion
- Korea shipping market share: X%
- HMM revenue potential: $XXX billion

### Competition
- Top players: HMM, 팬오션, others
- Barriers to entry: High (capital intensive)
- Industry trends: Consolidation, digitalization

---

## Monthly Tracking

### Cohesion Trajectory
| Month | Fiedler | Change | Status |
|-------|---------|--------|--------|
| 2025-10 | 6.00 | +4.00 | ✅ Growing |
| 2025-11 | TBD | TBD | |
| 2025-12 | TBD | TBD | |

### Regime Flip Tracking
| Month | HMM | 팬오션 | Small-caps Bull |
|-------|-----|--------|------------------|
| 2025-10 | Bear | Bear | 1/4 (25%) |
| 2025-11 | | | |
| 2025-12 | | | |

### Catalyst Validation
| Catalyst | Status | Evidence |
|----------|--------|----------|
| Shipping rates | TBD | Check monthly |
| Orderbook | TBD | Research |
| China demand | TBD | Track data |

---

## Investment Timeline

### Entry Triggers
- [ ] **Trigger 1**: Cohesion reaches 8.0+
- [ ] **Trigger 2**: 팬오션 (mid-cap) flips to bull
- [ ] **Trigger 3**: ≥2 small-caps in bull regime
- [ ] **Trigger 4**: Fundamental catalyst confirmed

### Timeline Forecast
- **Month 0-6**: Research phase, no investment
- **Month 6-12**: If triggers met, start small position
- **Month 12-18**: If HMM flips bull, increase to full position

### Exit Criteria
- [ ] Cohesion drops >30% from peak
- [ ] HMM flips back to bear
- [ ] Fundamental thesis invalidated

---

## Risk Assessment

### Risks
1. **Cyclical downturn**: Shipping is highly cyclical
2. **Oversupply**: New ship orders could flood market
3. **Geopolitical**: Trade wars, route disruptions
4. **False signal**: Small-cap movement could be noise

### Mitigation
- Position size: Max 5% of portfolio
- Stop-loss: -15% on individual positions
- Monthly review: Exit if cohesion fades
- Diversification: Don't concentrate in shipping

---

**Next Review**: 2025-11-30 (monthly)
**Status**: ACTIVE RESEARCH
```

---

## Monitoring Dashboard

### Weekly Check (Friday 18:00)

**TIER 1 Positions**:
```bash
# Check if still strong
python3 generate_sector_rankings.py --sector "철도" | grep "Cohesion:"
python3 generate_sector_rankings.py --sector "반도체 장비" | grep "Cohesion:"

# Verify large-caps still bull
```

**TIER 2 Watch**:
```bash
# Track cohesion growth
python3 analyze_4_tier_themes.py | grep -A 15 "TIER 2"

# Check if any promoted to TIER 1
```

**TIER 3 Research**:
```bash
# Update research files
# Track regime flips monthly (not weekly)
```

**TIER 4 Monitor**:
```bash
# Quarterly check only
# Most will fail, looking for survivors
```

---

### Monthly Review (Last Friday)

**Create Monthly Report**:

```bash
#!/bin/bash
# Generate monthly 4-tier comparison

CURRENT=$(date +%Y%m%d)
LAST_MONTH=$(date -d "1 month ago" +%Y%m%d)

echo "4-TIER THEME EVOLUTION"
echo "======================"
echo "From: $LAST_MONTH"
echo "To:   $CURRENT"
echo

echo "TIER 1 Changes:"
diff data/tier1_buy_now_$LAST_MONTH.csv data/tier1_buy_now_$CURRENT.csv

echo "TIER 2 Changes:"
diff data/tier2_accumulate_$LAST_MONTH.csv data/tier2_accumulate_$CURRENT.csv

echo "TIER 3 Changes:"
diff data/tier3_research_$LAST_MONTH.csv data/tier3_research_$CURRENT.csv

echo "TIER 4 Changes:"
diff data/tier4_monitor_$LAST_MONTH.csv data/tier4_monitor_$CURRENT.csv
```

**Track Promotions**:
```python
# Which themes promoted from TIER 3 → TIER 2?
# Which themes promoted from TIER 2 → TIER 1?
# Which themes failed (dropped tiers)?
```

---

## Portfolio Integration

### Position Sizing by Tier

**Conservative Portfolio**:
```
100% TIER 1
  0% TIER 2-4 (research only)
```

**Balanced Portfolio**:
```
 80% TIER 1 (core positions)
 20% TIER 2 (accumulation)
  0% TIER 3-4 (research only)
```

**Aggressive Portfolio**:
```
 50% TIER 1 (core)
 30% TIER 2 (growth)
 15% TIER 3 (early positioning)
  5% TIER 4 (speculative)
```

**Position Limits**:
- Max 10% in any single TIER 1 theme
- Max 5% in any single TIER 2 theme
- Max 2% in any single TIER 3 theme
- Max 1% in any single TIER 4 theme

---

## Advanced Analysis

### Tier Promotion Probability

Track historical promotion rates:

```python
# Analyze past 12 months
# What % of TIER 3 themes reached TIER 2?
# What % of TIER 2 themes reached TIER 1?
# Average time for promotion?

import pandas as pd
from datetime import datetime, timedelta

# Load historical tier data
months = pd.date_range(end=datetime.now(), periods=12, freq='M')

tier3_to_tier2 = []
tier2_to_tier1 = []

for month in months:
    # Load tier files
    # Track which themes promoted
    pass

print(f"TIER 3 → TIER 2 success rate: {len(tier3_to_tier2)/total:.1%}")
print(f"TIER 2 → TIER 1 success rate: {len(tier2_to_tier1)/total:.1%}")
print(f"Average promotion time: {avg_months:.1f} months")
```

---

### Cohesion Momentum

Identify themes accelerating vs decelerating:

```python
# Load last 4 weeks of cohesion data
# Calculate week-over-week momentum
# Identify accelerating TIER 3 themes

import pandas as pd

weeks = [
    'data/weekly_cohesion_change_20251027.csv',
    'data/weekly_cohesion_change_20251020.csv',
    'data/weekly_cohesion_change_20251013.csv',
    'data/weekly_cohesion_change_20251006.csv'
]

# For each TIER 3 theme:
# - Is cohesion growing consistently?
# - Is % change accelerating?
# - Is stock count stable?

for theme in tier3_themes:
    momentum = calculate_momentum(theme, weeks)
    if momentum > 0:
        print(f"✅ {theme}: Accelerating (+{momentum:.1f}%)")
    else:
        print(f"⚠️  {theme}: Decelerating ({momentum:.1f}%)")
```

---

## Troubleshooting

### Issue: No TIER 1 themes found

**Cause**: Market in correction, no strong themes

**Solution**:
- Focus on TIER 2 accumulation
- Build watchlist for when market recovers
- Defensive positioning

---

### Issue: Too many TIER 3/4 themes

**Cause**: Market frothy, many themes forming

**Solution**:
- Filter by fundamental quality
- Focus on themes with clear catalysts
- Reduce position sizes
- More selective research

---

### Issue: Theme jumped tiers (TIER 4 → TIER 2)

**Cause**: Major catalyst, rapid network formation

**Solution**:
- Immediate deep research
- Verify it's not temporary spike
- Check large-cap participation
- Consider fast-tracking investment

---

### Issue: TIER 3 theme regression (cohesion dropped)

**Cause**: Catalyst didn't materialize, false signal

**Solution**:
- Exit any positions immediately
- Stop further research
- Archive for future reference
- Learn from failure

---

## Output Files Reference

After running analysis, you'll have:

```
data/
├── weekly_cohesion_change_20251027.csv      # Raw cohesion data
├── tier1_buy_now_20251027.csv               # TIER 1 themes
├── tier2_accumulate_20251027.csv            # TIER 2 themes
├── tier3_research_20251027.csv              # TIER 3 themes
├── tier4_monitor_20251027.csv               # TIER 4 themes
├── 4tier_summary_20251027.json              # Summary JSON
└── sector_rankings_20251027.txt             # Detailed rankings

research/tier3/
├── shipping_해운_research.md                # TIER 3 research files
├── forestry_조림사업_research.md
└── ...
```

---

## Best Practices

### Weekly Routine

1. ✅ Run cohesion analysis
2. ✅ Run 4-tier classification
3. ✅ Check TIER 1 positions still valid
4. ✅ Monitor TIER 2 for promotions
5. ✅ Review TIER 3 monthly (not weekly)

### Monthly Routine

1. ✅ Deep-dive research on top 3 TIER 3 themes
2. ✅ Update regime status for all TIER 3 themes
3. ✅ Track cohesion momentum
4. ✅ Review portfolio allocation
5. ✅ Archive previous month's data

### Quarterly Routine

1. ✅ Review TIER 4 themes (most will fail)
2. ✅ Analyze tier promotion rates
3. ✅ Assess research accuracy
4. ✅ Update investment criteria if needed

---

## Related Documentation

- `how_to_run_sector_tickers_ordering.md` - Sector ranking guide
- `EARLY_STAGE_THEME_FRAMEWORK.md` - Theoretical framework
- `TOP_THEMES_CORRECTED.md` - Current top themes analysis

---

**Last Updated**: 2025-10-28
**Version**: 1.0
**Author**: KRX Investment Research Framework
