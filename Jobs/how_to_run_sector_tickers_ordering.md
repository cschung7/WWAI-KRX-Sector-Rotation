# How to Run Sector Ticker Ordering

**Script**: `generate_sector_rankings.py`
**Purpose**: Generate sector-based ticker rankings using Three-Layer Framework (Cohesion × Regime × Market Cap)
**Location**: `/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/`

---

## Quick Start

### Basic Usage

```bash
# Navigate to script directory
cd /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX

# Run with default settings (today's date, all sectors)
python3 generate_sector_rankings.py

# Specify date
python3 generate_sector_rankings.py --date 2025-10-27

# Top 10 sectors only
python3 generate_sector_rankings.py --date 2025-10-27 --top-sectors 10

# Specific sector analysis
python3 generate_sector_rankings.py --date 2025-10-27 --sector "반도체 장비"
```

---

## Command-Line Options

### `--date DATE`
**Format**: `YYYY-MM-DD`
**Default**: Today's date
**Example**: `--date 2025-10-27`

**Purpose**: Specify which date's data to analyze
- Loads cohesion changes for that date
- Uses latest available regime data

```bash
python3 generate_sector_rankings.py --date 2025-10-27
```

---

### `--top-sectors N`
**Type**: Integer
**Default**: None (analyze all sectors)
**Example**: `--top-sectors 10`

**Purpose**: Limit analysis to top N sectors by cohesion change
- Sectors sorted by absolute cohesion change (descending)
- Useful for quick overview of strongest signals

```bash
# Analyze only top 10 sectors
python3 generate_sector_rankings.py --date 2025-10-27 --top-sectors 10

# Top 5 sectors
python3 generate_sector_rankings.py --top-sectors 5
```

---

### `--sector "SECTOR_NAME"`
**Type**: String (must match exact sector name)
**Default**: None (analyze all sectors)
**Example**: `--sector "반도체 장비"`

**Purpose**: Deep-dive analysis on ONE specific sector
- Must use exact name including spaces and special characters
- Case-sensitive
- Use quotes around sector name

```bash
# Semiconductor equipment
python3 generate_sector_rankings.py --sector "반도체 장비"

# Railway
python3 generate_sector_rankings.py --sector "철도"

# Robotics (with parentheses)
python3 generate_sector_rankings.py --sector "로봇(산업용/협동로봇 등)"

# 5G (with parentheses)
python3 generate_sector_rankings.py --sector "5G(5세대 이동통신)"
```

**⚠️ Common Mistakes:**
```bash
# WRONG - No quotes
python3 generate_sector_rankings.py --sector 반도체 장비

# WRONG - Wrong spacing
python3 generate_sector_rankings.py --sector "반도체장비"

# WRONG - Missing parentheses
python3 generate_sector_rankings.py --sector "로봇"

# CORRECT
python3 generate_sector_rankings.py --sector "반도체 장비"
```

---

## Output Files

The script generates **3 output files** in `KRX/data/`:

### 1. JSON Format
**File**: `sector_rankings_YYYYMMDD.json`
**Use**: Machine-readable, API integration, custom processing

```json
{
  "sector": "반도체 장비",
  "date": "2025-10-27",
  "cohesion_info": {
    "stocks": 97,
    "week_before": 46.36,
    "last_week": 52.05,
    "change": 5.69,
    "pct_change": 12.3
  },
  "tickers": [
    {
      "tier": "Tier 1 (≥5T)",
      "ticker": "042700",
      "name": "한미반도체",
      "market_cap": 143000000000000,
      "regime": "Bull Quiet",
      "bull_pct": 100.0,
      "trend": 0.640,
      "composite_score": 1.000
    }
  ]
}
```

---

### 2. Markdown Format
**File**: `sector_rankings_YYYYMMDD.md`
**Use**: Documentation, reports, GitHub README

**Example**:
```markdown
## 반도체 장비

**Cohesion Metrics**:
- Total Stocks: 97
- Week Before Fiedler: 46.360
- Last Week Fiedler: 52.050
- Change: +5.690 (+12.3%)

📈 **Status**: Strong cohesion increase

### Tier 1 (≥5T)

| Ticker | Name | Market Cap | Regime | Bull % | Trend | Score |
|--------|------|------------|--------|--------|-------|-------|
| 042700 | 한미반도체 | 14.3T | Bull Quiet | 100.0% | 0.640 | 1.000 |
```

---

### 3. Plain Text Format
**File**: `sector_rankings_YYYYMMDD.txt`
**Use**: Quick viewing, terminal display, email reports

**Example**:
```
====================================================================================================
SECTOR RANKINGS - 2025-10-27
====================================================================================================

1. 반도체 장비 (97 stocks)
----------------------------------------------------------------------------------------------------
Cohesion: 52.05 (change: +5.69, +12.3%)

  Tier 1 (≥5T):
    • 한미반도체 (042700): 14.3T | Bull Quiet | Bull 100.0% | Trend +0.640 | Score 1.000
    • 한화 (000880): 7.1T | Bull Quiet | Bull 100.0% | Trend +0.220 | Score 0.940
```

---

## Understanding the Output

### Three-Tier Structure

**Tier 1: Large-Caps (≥5T)**
- Market cap ≥ 5 trillion won (50 in DB units)
- Sector leaders and institutional favorites
- Highest liquidity, lowest volatility
- **Investment**: Core portfolio positions

**Tier 2: Mid-Caps (1-5T)**
- Market cap 1-5 trillion won (10-50 in DB units)
- Growth potential with reasonable liquidity
- Higher beta than large-caps
- **Investment**: Balanced portfolio positions

**Tier 3: Small-Caps (<1T)**
- Market cap < 1 trillion won (<10 in DB units)
- Highest growth potential
- Lower liquidity, higher volatility
- **Investment**: Speculative/high-risk positions

---

### Interpreting Scores

#### Composite Score (0.0 - 1.0)
Weighted combination of three factors:
- **Regime Score (40%)**: Bull=1.0, Transition=0.5, Bear=0.0
- **Market Cap Score (30%)**: Larger cap = higher score
- **Cohesion Score (30%)**: Normalized cohesion change

**Score Ranges**:
- **0.9 - 1.0**: 🟢 Excellent - Large-cap bulls with positive cohesion
- **0.8 - 0.9**: 🟢 Good - Mid-cap bulls or large-caps in transition
- **0.6 - 0.8**: 🟡 Moderate - Mixed signals
- **0.4 - 0.6**: 🟠 Weak - Bear regime or negative factors
- **< 0.4**: 🔴 Avoid - Multiple negative signals

#### Regime Types
- **Bull Quiet**: Strong uptrend, low volatility ✅
- **Bull Volatile**: Uptrend with high volatility ⚠️
- **Transition**: Changing regime, uncertain direction ⚠️
- **Bear Quiet**: Downtrend, low volatility ❌
- **Bear Volatile**: Downtrend with high volatility ❌
- **Ranging**: Sideways movement ⚠️
- **Unknown**: No regime data available ⚠️

#### Trend Strength (-1.0 to +1.0)
- **+0.6 to +1.0**: Very strong uptrend
- **+0.3 to +0.6**: Strong uptrend
- **+0.0 to +0.3**: Weak uptrend
- **-0.3 to +0.0**: Weak downtrend
- **-0.6 to -0.3**: Strong downtrend
- **-1.0 to -0.6**: Very strong downtrend

---

## Investment Decision Framework

### Step 1: Check Cohesion Change
Look for sectors with:
- **Baseline Fiedler > 15** (established network)
- **Change > +5.0** (strong strengthening)
- **OR Change > +3.0 with baseline > 25** (incremental strengthening)

**Example**:
```
반도체 장비: 46.36 → 52.05 (+5.69)  ✅ Strong signal
철도: 17.73 → 24.95 (+7.22)         ✅ Strong signal
수소차: 0.00 → 43.51 (+43.51)       ⚠️ No baseline, risky
```

---

### Step 2: Verify Large-Cap Leadership
Check Tier 1 stocks:
- **Requirement**: ≥50% of large-caps in Bull regime
- **Ideal**: 100% of large-caps in Bull regime

**Example - Strong Signal**:
```
반도체 장비 - Tier 1:
✅ 한미반도체 (14.3T): Bull Quiet, Bull 100%
✅ 한화 (7.1T): Bull Quiet, Bull 100%
→ 2/2 = 100% Bull Leadership ✅
```

**Example - Weak Signal**:
```
로봇 - Tier 1:
✅ 두산 (13.2T): Bull Quiet, Bull 100%
❌ LIG넥스원 (10.7T): Bear Quiet, Bull 0%
✅ LS (6.7T): Bull Quiet, Bull 100%
✅ 레인보우로보틱스 (6.6T): Bull Quiet, Bull 100%
→ 3/4 = 75% Bull Leadership ⚠️
```

---

### Step 3: Check Mid-Cap Confirmation
Tier 2 validation:
- **Strong**: ≥70% of mid-caps in Bull regime
- **Moderate**: 50-70% in Bull regime
- **Weak**: <50% in Bull regime

---

### Step 4: Investment Decision

| Cohesion | Large-Cap Bulls | Mid-Cap Bulls | Decision |
|----------|----------------|---------------|----------|
| >+5.0 | 100% | >70% | 🟢 **STRONG BUY** |
| >+5.0 | ≥75% | >50% | 🟢 **BUY** |
| >+3.0 | 100% | >70% | 🟢 **BUY** |
| >+3.0 | ≥50% | >50% | 🟡 **WATCH** |
| <+3.0 | Any | Any | ⚠️ **WAIT** |
| Negative | Any | Any | 🔴 **AVOID** |

---

## Real-World Examples

### Example 1: Strong Buy Signal

```bash
python3 generate_sector_rankings.py --sector "반도체 장비"
```

**Output Analysis**:
```
Cohesion: 52.05 (change: +5.69, +12.3%)

Tier 1 (≥5T):
  • 한미반도체 (042700): 14.3T | Bull Quiet | Bull 100.0% | Trend +0.640 | Score 1.000
  • 한화 (000880): 7.1T | Bull Quiet | Bull 100.0% | Trend +0.220 | Score 0.940

Tier 2 (1-5T):
  • GS (078930): 4.6T | Bull Quiet | Bull 100.0%
  • 리노공업 (058470): 4.4T | Bull Quiet | Bull 100.0%
  • 원익IPS (240810): 3.0T | Bull Quiet | Bull 100.0%
  [... 10/10 mid-caps ALL BULL ...]
```

**Decision**: 🟢 **STRONG BUY**
- ✅ High baseline (46.36) + strong increase (+5.69)
- ✅ 100% large-cap bull leadership
- ✅ 100% mid-cap bull confirmation
- ✅ High composite scores (1.000, 0.940)

**Action**:
- Buy 한미반도체 (042700) - primary position
- Buy 원익IPS (240810) - highest trend mid-cap
- Diversify with mid-cap basket

---

### Example 2: Watch Signal

```bash
python3 generate_sector_rankings.py --sector "로봇(산업용/협동로봇 등)"
```

**Output Analysis**:
```
Cohesion: 30.60 (change: +3.75, +14.0%)

Tier 1 (≥5T):
  • 두산 (000150): 13.2T | Bull Quiet | Bull 100.0% | Score 1.000
  • LIG넥스원 (079550): 10.7T | Bear Quiet | Bull 0.0% | Score 0.562
  • LS (006260): 6.7T | Bull Quiet | Bull 100.0% | Score 0.940
  • 레인보우로보틱스 (277810): 6.6T | Bull Quiet | Bull 100.0% | Score 0.902
```

**Decision**: 🟡 **WATCH**
- ✅ Good cohesion increase (+3.75)
- ⚠️ 75% large-cap bull (LIG넥스원 in bear)
- ⚠️ Mixed signals

**Action**:
- Add to watchlist
- Wait for LIG넥스원 to flip to bull
- OR buy only confirmed bulls (두산, LS, 레인보우로보틱스)

---

### Example 3: Avoid Signal

```bash
python3 generate_sector_rankings.py --sector "2차전지"
```

**Expected Output** (from previous analysis):
```
Cohesion: 38.47 (change: -4.22, -9.9%)
```

**Decision**: 🔴 **AVOID**
- ❌ Negative cohesion change (-4.22)
- ❌ Network fragmenting
- ❌ Stocks diverging

**Action**:
- Avoid new positions
- Reduce or exit existing positions
- Wait for cohesion to stabilize

---

## Automation & Scheduling

### Daily Report Generation

Create a shell script `daily_sector_rankings.sh`:

```bash
#!/bin/bash
# Daily Sector Rankings Report
# Run daily at 18:30 KST (after market close + regime update)

DATE=$(date +%Y-%m-%d)
SCRIPT_DIR="/mnt/nas/gpt/Naver/three_layers/countryrisk/KRX"
OUTPUT_DIR="$SCRIPT_DIR/data"

cd $SCRIPT_DIR

# Generate top 20 sectors
python3 generate_sector_rankings.py --date $DATE --top-sectors 20

# Email or Slack notification (optional)
echo "Sector rankings generated for $DATE" | mail -s "Daily Sector Report" your@email.com

# Archive old reports (keep last 30 days)
find $OUTPUT_DIR -name "sector_rankings_*.txt" -mtime +30 -delete
```

Make executable:
```bash
chmod +x daily_sector_rankings.sh
```

Add to crontab:
```bash
crontab -e

# Add this line (run daily at 18:30 KST)
30 18 * * * /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/daily_sector_rankings.sh
```

---

### Specific Sector Monitoring

Monitor key sectors every week:

```bash
#!/bin/bash
# Weekly Sector Monitor
# Run: Friday 18:00 KST

DATE=$(date +%Y-%m-%d)

# Key sectors to monitor
SECTORS=(
  "반도체 장비"
  "철도"
  "5G(5세대 이동통신)"
  "로봇(산업용/협동로봇 등)"
)

for SECTOR in "${SECTORS[@]}"; do
  echo "Analyzing: $SECTOR"
  python3 generate_sector_rankings.py --date $DATE --sector "$SECTOR"
done
```

---

## Troubleshooting

### Error: "No regime files found"
**Cause**: Regime data not available for the date
**Solution**: Check regime data directory
```bash
ls -lh /mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/all_regimes_*.csv
```

---

### Error: "Cohesion file not found"
**Cause**: Weekly cohesion analysis not run for that date
**Solution**: Run cohesion analysis first
```bash
python3 analyze_weekly_cohesion_change.py
```

---

### Error: "Sector not found"
**Cause**: Sector name doesn't match exactly
**Solution**: Check available sector names
```bash
# List all available sectors
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/weekly_cohesion_change_20251027.csv')
print("\nAvailable Sectors:")
print("="*80)
for theme in sorted(df['Theme'].tolist()):
    print(f"  {theme}")
EOF
```

---

### Warning: "All regime data showing Unknown"
**Cause**: Ticker format mismatch (this was fixed)
**Solution**: Script should handle this automatically now
- Tickers converted to 6-digit format with leading zeros
- Korean stock names used for regime matching

---

## Data Dependencies

### Required Files

1. **Database**: `/mnt/nas/AutoGluon/AutoML_Krx/DB/db_final.csv`
   - Contains: tickers, names, market caps, Naver themes

2. **Regime Data**: `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/all_regimes_*.csv`
   - Contains: Bull/Bear/Transition probabilities, trend strength

3. **Cohesion Changes**: `KRX/data/weekly_cohesion_change_YYYYMMDD.csv`
   - Contains: Week-over-week Fiedler value changes

### Data Refresh Schedule

- **Database**: Updated weekly (Sunday)
- **Regime Data**: Updated daily (18:00 KST)
- **Cohesion Data**: Calculated weekly (Friday after market close)

---

## Advanced Usage

### Batch Analysis - Multiple Sectors

```bash
#!/bin/bash
# Analyze top performers

# Get top 5 sectors by cohesion increase
TOP_SECTORS=$(python3 << 'EOF'
import pandas as pd
df = pd.read_csv('data/weekly_cohesion_change_20251027.csv')
top5 = df.nlargest(5, 'Change')
for sector in top5['Theme']:
    print(sector)
EOF
)

# Analyze each
for SECTOR in $TOP_SECTORS; do
  echo "="*80
  echo "Analyzing: $SECTOR"
  echo "="*80
  python3 generate_sector_rankings.py --sector "$SECTOR"
done
```

---

### Custom Filtering

Want only sectors with >70% bull leadership?

```python
import json
import pandas as pd

# Load rankings
with open('data/sector_rankings_20251027.json', 'r') as f:
    data = json.load(f)

# Filter by bull percentage
strong_sectors = []
for sector in data:
    tickers = sector['tickers']
    tier1 = [t for t in tickers if t['tier'] == 'Tier 1 (≥5T)']

    if len(tier1) > 0:
        bull_pct = sum(1 for t in tier1 if t['bull_pct'] == 100.0) / len(tier1)
        if bull_pct >= 0.7:
            strong_sectors.append({
                'sector': sector['sector'],
                'cohesion_change': sector['cohesion_info']['change'],
                'bull_leadership': f"{bull_pct*100:.0f}%"
            })

df = pd.DataFrame(strong_sectors)
print(df.to_string(index=False))
```

---

## Best Practices

### Weekly Routine (Friday 18:30 KST)

1. **Run cohesion analysis**:
   ```bash
   python3 analyze_weekly_cohesion_change.py
   ```

2. **Generate top 20 sector rankings**:
   ```bash
   python3 generate_sector_rankings.py --top-sectors 20
   ```

3. **Deep-dive on top 3 sectors**:
   ```bash
   python3 generate_sector_rankings.py --sector "반도체 장비"
   python3 generate_sector_rankings.py --sector "철도"
   # ... etc
   ```

4. **Review large-cap leadership** in TXT output

5. **Update portfolio positions** based on signals

---

### Monthly Review

- Compare rankings month-over-month
- Track accuracy of sector predictions
- Adjust position sizing based on performance
- Archive reports for future reference

---

## Related Scripts

- `analyze_weekly_cohesion_change.py` - Calculates week-over-week Fiedler changes
- `../AutoML_Krx/Backtest/generate_daily_rankings.py` - Individual stock rankings
- `../AutoML_Krx/Backtest/Jobs/generate_daily_report.sh` - Daily report generation

---

## Support

For issues or questions:
1. Check this documentation
2. Review script comments in `generate_sector_rankings.py`
3. Check log output for error messages
4. Verify data dependencies are up-to-date

---

**Last Updated**: 2025-10-28
**Script Version**: 1.0
**Author**: Claude Code + Research Framework
