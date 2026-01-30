# Final Research Summary: Naver Theme Cohesion vs Regime Analysis

**Date**: 2025-10-28
**Complete Research Package**

---

## 📚 RESEARCH DOCUMENTS GENERATED

### 1. **EXECUTIVE_SUMMARY.md** (READ THIS FIRST)
Quick reference for investment decisions.

### 2. **NAVER_THEME_COHESION_REPORT_20251027.md**
Original cohesion analysis - 111 themes with enhanced cohesion.
**Use for**: Understanding theme structure and Fiedler values.

### 3. **REGIME_COHESION_MISMATCH_WARNING.md**
Critical warning about mismatch between cohesion and regime.
**Key Finding**: 19/20 themes are bearish despite high cohesion.

### 4. **LARGE_CAP_REGIME_STRATEGY.md** (NEW!)
Complete solution to the mismatch problem.
**Key Finding**: Large-caps have 28.3% higher bull regime probability.

---

## 🎯 COMPLETE RESEARCH FINDINGS

### Question 1: Which Naver themes have enhanced cohesion?
**Answer**: 111 themes out of 265 (41.9%)
- Top theme: 전기차 (EVs) - Fiedler 6.18, +212% increase
- See: `NAVER_THEME_COHESION_REPORT_20251027.md`

### Question 2: Do investment implications match regime probabilities?
**Answer**: ❌ NO - Major mismatch detected
- Only 1/20 themes is bullish: 증권 (Securities)
- Average: 26.4% bull, 57.2% bear
- See: `REGIME_COHESION_MISMATCH_WARNING.md`

### Question 3: Do large-caps have higher probability of bullish regimes?
**Answer**: ✅ YES - Strongly confirmed
- Large-caps (≥5T): 43.1% bull regime
- Small-caps (<1T): 14.7% bull regime
- Difference: **+28.3 percentage points**
- See: `LARGE_CAP_REGIME_STRATEGY.md`

---

## 💡 KEY INSIGHTS

### Insight 1: **Cohesion ≠ Direction**
- High Fiedler = stocks move together
- Can move together DOWNWARD
- Current market: "Coordinated decline"

### Insight 2: **Market Cap is THE Critical Variable**
- Large-caps decouple from theme-level bearishness
- Small-caps drag down theme statistics
- Market cap > theme affiliation

### Insight 3: **199 Large-Cap Opportunities Exist**
- Total market cap: ~38 trillion KRW
- Within bearish themes
- All with bullish or transition regimes

---

## 📊 FINAL INVESTMENT RECOMMENDATIONS

### ✅ TIER 1: MEGA-CAP LEADERS (>500T KRW)

1. **삼성전자** (5,848.6T)
   - Bull in 6 themes
   - Trend: +0.640, Momentum: 0.896
   - **Rating**: STRONG BUY

2. **SK하이닉스** (3,712.8T)
   - Bull in multiple tech themes
   - Trend: +0.460, Momentum: 0.936
   - **Rating**: BUY

3. **LG에너지솔루션** (1,151.3T)
   - Bull in EV/Battery themes
   - Trend: +0.520, Momentum: 0.894
   - **Rating**: BUY

4. **현대차** (517.0T)
   - Bull in EV/Auto themes
   - Trend: +0.640, Momentum: 0.902
   - **Rating**: BUY

### ✅ TIER 2: LARGE-CAP PLAYS (200-500T)

- **기아** (452.5T) - EV, Defense
- **한화오션** (414.3T) - Defense
- **LG화학** (283.1T) - Battery, Materials
- **삼성SDI** (236.1T) - Battery
- **포스코퓨처엠** (215.3T) - Battery Materials

### ⏳ WATCHLIST: TRANSITION STOCKS

- **POSCO홀딩스** (263.4T) - Momentum: 0.901 (very strong)
- **우리금융지주** (187.2T) - Momentum: 0.702
- **한화시스템** (103.9T) - Defense, Momentum: 0.783

### ❌ AVOID

- Small-caps (<1T) in bearish themes
- Theme-level ETFs without large-cap focus
- All themes except 증권 without market cap filter

---

## 🎓 INVESTMENT FRAMEWORK

### Three-Factor Model:

```
Investment Score = Cohesion Factor × Regime Factor × Size Factor

Cohesion Factor (0-1):
  - High Fiedler (>2.0): 1.0
  - Medium (1-2): 0.6
  - Low (<1): 0.2

Regime Factor (0-1):
  - Bull >60%: 1.0
  - Bull 40-60%: 0.6
  - Bull <40%: 0.3

Size Factor (0-1):
  - ≥10T: 1.0
  - 5-10T: 0.8
  - 1-5T: 0.4
  - <1T: 0.2
```

**Threshold**: Score > 0.48 to invest

### Examples:

**삼성전자**:
- Cohesion: 1.0 (Fiedler 4.58 in OLED)
- Regime: 1.0 (100% bull)
- Size: 1.0 (5,848.6T)
- **Score**: 1.0 × 1.0 × 1.0 = **1.0** ✅

**Small-cap in 화장품**:
- Cohesion: 1.0 (Fiedler 5.82)
- Regime: 0.3 (8.7% bull)
- Size: 0.2 (<1T)
- **Score**: 1.0 × 0.3 × 0.2 = **0.06** ❌

---

## 📁 DATA FILES

### Generated Reports:
- `EXECUTIVE_SUMMARY.md` (4.2K)
- `NAVER_THEME_COHESION_REPORT_20251027.md` (12K)
- `REGIME_COHESION_MISMATCH_WARNING.md` (11K)
- `LARGE_CAP_REGIME_STRATEGY.md` (NEW, 413 lines)
- `SECTOR_FINDINGS.md` (8.3K)

### Data Files:
- `data/enhanced_cohesion_themes_20251027.csv` (111 themes)
- `data/theme_cohesion_ranking_20251027.csv` (265 themes)
- `data/theme_*_timeseries.csv` (265 individual theme files)

### External Data:
- Regime: `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/all_regimes_20251026_004518.csv`
- Database: `/mnt/nas/AutoGluon/AutoML_Krx/DB/db_final.csv`

### Analysis Scripts:
- `analyze_naver_theme_cohesion.py` (Reusable for daily updates)

---

## 🔄 DAILY MONITORING WORKFLOW

### Step 1: Update Regime Data
```bash
# Check latest regime file
ls -lt /mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/
```

### Step 2: Rerun Cohesion Analysis
```bash
python3 KRX/analyze_naver_theme_cohesion.py
```

### Step 3: Cross-Check Large-Caps
- Filter for ≥5T market cap
- Check bull regime %
- Verify trend > 0.3

### Step 4: Update Watchlist
- Monitor transition stocks
- Check if trend turned positive
- Update entry/exit signals

---

## ⚡ QUICK REFERENCE

### Current Market State (2025-10-26):
- **Overall**: 62.3% bear, 25.7% bull
- **Large-caps**: 43.1% bull (MUCH BETTER)
- **Small-caps**: 14.7% bull (AVOID)

### Investable Themes (with large-cap filter):
1. 증권 (Securities) - 80.8% bull ✅
2. 2차전지 (Battery) - 36 large-cap opps
3. 밸류업25년 (Value-up) - 31 large-cap opps
4. 전기차 (EVs) - 20 large-cap opps
5. OLED - 19 large-cap opps

### Top 5 Stock Picks:
1. 삼성전자 (5,848.6T)
2. SK하이닉스 (3,712.8T)
3. LG에너지솔루션 (1,151.3T)
4. 현대차 (517.0T)
5. 기아 (452.5T)

---

## 🎯 CONCLUSION

### Research Question Answered:
**"Even if current regime is not bullish, do relatively large-cap stocks (among Naver themes) have higher probability of bullish regime or regime shift?"**

### Answer:
**✅ YES - HYPOTHESIS STRONGLY CONFIRMED**

### Numerical Evidence:
- **+28.3%** higher bull regime probability
- **+3.7%** higher transition probability
- **4x better** trend strength (-0.153 vs -0.595)
- **5x better** momentum (0.372 vs 0.078)

### Practical Implication:
**Market cap is MORE important than theme affiliation for predicting regime.**

### Investment Strategy:
**Filter ALL thematic investments by market cap ≥5T. This single rule transforms bearish themes into investable opportunities.**

---

**Last Updated**: 2025-10-28
**Status**: ✅ Research Complete
**Next Steps**: Daily monitoring and portfolio implementation
