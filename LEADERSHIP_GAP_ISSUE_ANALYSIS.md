# Leadership Gap Calculation Issue Analysis

## Problem Statement

The current leadership gap calculation has a **critical flaw**: it doesn't account for stocks that are classified in multiple themes, leading to misleading leadership gaps.

### Examples from User Feedback:

1. **비료 (Fertilizer) Sector**:
   - KG케미칼 is classified in 7+ categories
   - Its momentum might be driven by "2차전지" (secondary battery), not 비료
   - This creates a false leadership gap for 비료 sector

2. **태양광 (Solar) Sector**:
   - OCI is a true solar leader → genuine leadership gap
   - 원익IPS is more related to OLED, semiconductor equipment, 3D NAND → false signal for solar

## Root Cause

**Multi-Category Classification Problem**:
- Some stocks appear in 20-67 different themes
- Current calculation includes ALL stocks in a theme, regardless of:
  - How many other themes they're in
  - Whether their momentum is theme-specific or general
  - Whether they're a "pure play" or diversified conglomerate

## Current Calculation Method

```python
# Current approach (FLAWED):
for ticker in theme_stocks:  # Includes ALL stocks in theme
    # Calculate leadership gap
    # Problem: Doesn't filter by theme relevance
```

**Issues**:
1. No filtering by theme count (stocks in 10+ themes included)
2. No weighting by theme relevance
3. No consideration of theme-specific vs general momentum
4. Conglomerates (SK, LG, 삼성전자) skew results

## Proposed Solutions

### Solution 1: Theme Purity Filtering (RECOMMENDED)
**Filter out stocks that are in too many themes**

```python
# Only include stocks that are in ≤5 themes (configurable)
MAX_THEMES_PER_STOCK = 5

if stock_theme_count <= MAX_THEMES_PER_STOCK:
    # Include in calculation
else:
    # Exclude (likely conglomerate or multi-sector stock)
```

**Pros**:
- Simple to implement
- Removes obvious conglomerates
- Focuses on "pure play" stocks

**Cons**:
- May exclude some legitimate multi-sector stocks
- Threshold is arbitrary

### Solution 2: Theme Relevance Weighting
**Weight stocks by inverse of theme count**

```python
# Weight = 1 / theme_count
# Stock in 1 theme: weight = 1.0 (100% relevant)
# Stock in 5 themes: weight = 0.2 (20% relevant)
# Stock in 20 themes: weight = 0.05 (5% relevant)

weighted_bull = sum(stock_bull * weight) / sum(weights)
```

**Pros**:
- More nuanced than filtering
- Still includes all stocks but weights appropriately

**Cons**:
- More complex
- May still include irrelevant stocks

### Solution 3: Primary Theme Detection
**Identify primary theme for each stock**

```python
# Primary theme = theme where stock has highest market cap share
# Or: theme where stock's momentum correlates best with theme momentum

if stock_primary_theme == current_theme:
    # Include with full weight
elif stock_primary_theme != current_theme:
    # Exclude or weight very low
```

**Pros**:
- Most accurate
- Handles multi-sector stocks correctly

**Cons**:
- Requires additional calculation
- May need historical correlation analysis

### Solution 4: Hybrid Approach (BEST)
**Combine filtering + weighting + primary theme**

```python
# Step 1: Filter out stocks in >10 themes (conglomerates)
if stock_theme_count > 10:
    exclude()

# Step 2: For stocks in 5-10 themes, weight by inverse
elif stock_theme_count > 5:
    weight = 1.0 / stock_theme_count

# Step 3: For stocks in ≤5 themes, check if current theme is primary
elif is_primary_theme(stock, current_theme):
    weight = 1.0
else:
    weight = 0.5  # Secondary theme
```

## Recommended Implementation

### Phase 1: Quick Fix (Immediate)
1. **Add theme count filtering**
   - Exclude stocks in >10 themes from leadership calculation
   - Configurable threshold (default: 10)

2. **Add theme count to output**
   - Show theme count for each large-cap leader
   - Flag stocks with high theme count (>5)

### Phase 2: Enhanced (Next)
3. **Add theme relevance weighting**
   - Weight stocks by 1/theme_count
   - Recalculate leadership gap with weights

4. **Add primary theme detection**
   - Calculate market cap share per theme
   - Identify primary theme for each stock

### Phase 3: Advanced (Future)
5. **Theme-specific momentum correlation**
   - Calculate correlation between stock momentum and theme momentum
   - Only include stocks with high correlation

6. **Sector-specific filtering**
   - For each theme, identify related themes
   - Exclude stocks whose momentum is better explained by related themes

## Implementation Plan

### Step 1: Add Theme Count Tracking
```python
# In analyze_theme_leadership():
theme_count_map = {}  # ticker -> theme_count

for ticker in all_tickers:
    themes = get_themes_for_ticker(ticker)
    theme_count_map[ticker] = len(themes)
```

### Step 2: Filter by Theme Count
```python
# Filter stocks
filtered_stocks = [
    ticker for ticker in theme_stocks
    if theme_count_map.get(ticker, 0) <= MAX_THEMES_PER_STOCK
]
```

### Step 3: Add Theme Count to Output
```python
# In result dictionary:
'Top_Large_Caps': top_large_caps_with_theme_count,
'Filtered_Stocks_Count': len(filtered_stocks),
'Excluded_Stocks_Count': len(theme_stocks) - len(filtered_stocks)
```

## Expected Impact

### Before Fix:
- 비료 sector: High leadership gap (due to KG케미칼 in 7 themes)
- 태양광 sector: Mixed signals (OCI + 원익IPS)

### After Fix:
- 비료 sector: Lower/more accurate leadership gap
- 태양광 sector: Clear signal from OCI (true solar leader)
- More accurate identification of "next to turn" themes

## Configuration

Add to config.py:
```python
# Leadership gap calculation parameters
MAX_THEMES_PER_STOCK = 10  # Exclude stocks in more themes
THEME_COUNT_WEIGHT_THRESHOLD = 5  # Start weighting below this
PRIMARY_THEME_WEIGHT = 1.0  # Full weight for primary theme
SECONDARY_THEME_WEIGHT = 0.5  # Reduced weight for secondary
```

