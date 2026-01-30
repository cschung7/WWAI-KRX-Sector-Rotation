# Timing Estimation Brainstorm: Refining the 12-18 Month Framework

## Executive Summary

**Current Challenge**: The 4-tier framework uses "12-18 months" as a general estimate for TIER 3 themes to become investable (TIER 1). Can we be more precise?

**Available Data Sources**:
1. **Historical Fiedler Values**: Weekly timeseries from Feb 2025 - Oct 2025 (~8 months)
2. **Score Percentage Data**: `/mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_2025-10-28.json`
   - Per-ticker overall_assessment with score_percentage (0-100)
   - Measures current regime quality and momentum
3. **Regime Transition History**: Bull/Bear regime flips tracked in weekly LRS data
4. **Market Cap & Theme Membership**: Known from Naver theme classification

**Goal**: Build a predictive model to estimate:
- When will a TIER 3 theme reach TIER 1 status?
- Which TIER 3 themes will mature faster (6-9 months) vs slower (18-24 months)?
- Early warning signals that a theme is accelerating or stalling

---

## Method 1: Historical Fiedler Trajectory Analysis

### Concept
Track actual progression of themes through tiers over time and measure average velocities.

### Implementation

#### Step 1: Calculate Fiedler Growth Velocity
```python
# For each Naver theme
velocity = (current_fiedler - fiedler_8_weeks_ago) / 8 weeks
acceleration = (current_velocity - velocity_4_weeks_ago) / 4 weeks

# Classify growth patterns
if acceleration > 0.1:
    status = "ACCELERATING"  # Estimate: 6-9 months
elif acceleration < -0.1:
    status = "DECELERATING"  # Estimate: 18-24 months
else:
    status = "STEADY"  # Estimate: 12-15 months
```

#### Step 2: Extrapolate to Threshold
```python
# TIER 3 → TIER 1 requires reaching baseline > 15
current_fiedler = 4.5
target_fiedler = 15.0
gap = target_fiedler - current_fiedler  # 10.5

# Using velocity
weekly_velocity = 0.3  # +0.3 per week
weeks_to_target = gap / weekly_velocity  # 35 weeks = 8.75 months

# Adjust for acceleration
if acceleration > 0:
    adjusted_weeks = weeks_to_target * 0.8  # Faster
else:
    adjusted_weeks = weeks_to_target * 1.2  # Slower
```

#### Step 3: Confidence Intervals
```python
# Calculate historical volatility of velocity
velocity_std = std(past_8_weeks_velocities)

# 95% confidence interval
lower_bound = (gap / (velocity + 1.96*velocity_std)) * 0.9
upper_bound = (gap / (velocity - 1.96*velocity_std)) * 1.1

# Example output
# Estimated timing: 9 months (95% CI: 6-12 months)
```

### Required Data
- Weekly fiedler values for all Naver themes (last 8 months minimum)
- Current status: We have sector data, need to aggregate by Naver theme

### Validation Approach
```python
# Backtest on themes that already transitioned
# Example: Find themes that were TIER 3 in May 2025, now TIER 1
tier3_may = themes[(fiedler_may > 2) & (fiedler_may < 8)]
tier1_oct = themes[(fiedler_oct > 15)]
transitioned = tier3_may[tier3_may.index.isin(tier1_oct.index)]

# Measure actual time taken
actual_months = 5  # May → Oct
predicted_months = calculate_velocity_estimate(fiedler_may)
prediction_error = abs(actual_months - predicted_months)
```

**Pros**:
- Direct measure of theme momentum
- Simple to calculate and interpret
- Can detect acceleration/deceleration early

**Cons**:
- Only 8 months of data (need 18+ months for full validation)
- Fiedler growth may not be linear
- External shocks can disrupt patterns

---

## Method 2: Score Percentage Peak Timing Analysis

### Concept
Use AutoGluon UCS_LRS score_percentage data to identify when tickers within a theme are reaching peak quality scores. Hypothesis: Themes transition to TIER 1 when 50%+ of member tickers reach score_percentage > 70.

### Implementation

#### Step 1: Aggregate Score by Theme
```python
# Load complete_situation_results
with open('/mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_2025-10-28.json') as f:
    situation_data = json.load(f)

# For each Naver theme
def calculate_theme_readiness(theme_name):
    theme_tickers = get_naver_theme_tickers(theme_name)

    scores = []
    for ticker in theme_tickers:
        ticker_data = situation_data.get(ticker, {})
        assessment = ticker_data.get('overall_assessment', {})
        score_pct = assessment.get('score_percentage', 0)
        scores.append(score_pct)

    # Readiness metrics
    avg_score = np.mean(scores)
    median_score = np.median(scores)
    pct_above_70 = len([s for s in scores if s > 70]) / len(scores)
    pct_above_80 = len([s for s in scores if s > 80]) / len(scores)

    return {
        'avg_score': avg_score,
        'median_score': median_score,
        'pct_above_70': pct_above_70,
        'pct_above_80': pct_above_80,
        'readiness_index': avg_score * pct_above_70  # Composite
    }
```

#### Step 2: Correlation with Tier Transitions
```python
# Hypothesis testing
# TIER 1 themes should have:
#   - avg_score > 65
#   - pct_above_70 > 0.4 (40% of tickers)
#   - readiness_index > 30

# TIER 3 themes should have:
#   - avg_score < 55
#   - pct_above_70 < 0.2
#   - readiness_index < 15

# Calculate for current themes
tier1_themes = ['철도', '반도체 장비']
tier3_themes = ['해운', '조림사업', '아스콘', ...]

tier1_readiness = [calculate_theme_readiness(t) for t in tier1_themes]
tier3_readiness = [calculate_theme_readiness(t) for t in tier3_themes]

# Find correlation
# If TIER 1 avg_readiness_index = 45
# And TIER 3 avg_readiness_index = 12
# Gap = 33 points

# For a TIER 3 theme currently at readiness_index = 15
# Needs to gain: 45 - 15 = 30 points
# Historical growth rate: +2 points/month (from past data)
# Estimated time: 30 / 2 = 15 months
```

#### Step 3: Early Warning Signals
```python
# Monitor monthly changes in score_percentage
def detect_acceleration(theme_name):
    current_readiness = calculate_theme_readiness(theme_name)
    past_readiness = load_past_month_readiness(theme_name)

    # Month-over-month growth
    mom_growth = current_readiness['readiness_index'] - past_readiness['readiness_index']

    if mom_growth > 3:
        return "ACCELERATING - Revise estimate to 6-9 months"
    elif mom_growth < 0.5:
        return "STALLING - Revise estimate to 18-24 months"
    else:
        return "ON TRACK - Maintain 12-15 month estimate"
```

### Required Data
- Monthly snapshots of complete_situation_results (need historical versions)
- Current status: We have Oct 2025 snapshot only

### Validation Approach
```python
# Need to collect monthly snapshots going forward
# After 6 months, can validate:
# - Did themes with high readiness_index growth transition faster?
# - What is the optimal readiness_index threshold for TIER 1?
# - Does score_percentage predict regime flips?
```

**Pros**:
- Incorporates fundamental quality signals (not just cohesion)
- Can detect regime momentum before it fully flips
- Combines technical + fundamental factors

**Cons**:
- Need historical monthly snapshots (don't have yet)
- Score_percentage may lag actual transitions
- Complex multi-factor model

---

## Method 3: Regime Transition Cascade Analysis

### Concept
Track the progression: Small-cap bull → Mid-cap bull → Large-cap bull. Measure average time between each stage.

### Implementation

#### Step 1: Define Regime Cascade Stages
```python
def classify_cascade_stage(theme_name):
    rankings = generate_sector_rankings(theme_name)

    # Count bulls by market cap tier
    tier1_bulls = count_bulls(rankings['tier1'])  # Large-cap
    tier2_bulls = count_bulls(rankings['tier2'])  # Mid-cap
    tier3_bulls = count_bulls(rankings['tier3'])  # Small-cap

    tier1_pct = tier1_bulls / len(rankings['tier1'])
    tier2_pct = tier2_bulls / len(rankings['tier2'])
    tier3_pct = tier3_bulls / len(rankings['tier3'])

    # Classify stage
    if tier1_pct > 0.5:
        return "STAGE_4_MATURE"  # TIER 1 investable
    elif tier1_pct > 0.2 and tier2_pct > 0.5:
        return "STAGE_3_SPREADING"  # 3-6 months to TIER 1
    elif tier2_pct > 0.3 and tier3_pct > 0.5:
        return "STAGE_2_FORMING"  # 6-12 months to TIER 1
    elif tier3_pct > 0.3:
        return "STAGE_1_SEED"  # 12-18 months to TIER 1
    else:
        return "STAGE_0_DORMANT"  # 18+ months
```

#### Step 2: Measure Transition Velocities
```python
# Historical tracking (need weekly data)
cascade_history = {
    'week': [],
    'theme': [],
    'stage': [],
    'tier1_pct': [],
    'tier2_pct': [],
    'tier3_pct': []
}

# Track weekly for all themes
# Calculate average time in each stage:
avg_time_stage1 = 8 weeks
avg_time_stage2 = 12 weeks
avg_time_stage3 = 6 weeks

# For a theme currently in STAGE_1
estimated_weeks_to_tier1 = avg_time_stage1 + avg_time_stage2 + avg_time_stage3
                          = 26 weeks = 6.5 months

# For a theme in STAGE_2
estimated_weeks = avg_time_stage2 + avg_time_stage3
                = 18 weeks = 4.5 months
```

#### Step 3: Transition Probability Model
```python
# Use Markov chain to model transitions
# P(STAGE_1 → STAGE_2) = 0.3 per month
# P(STAGE_2 → STAGE_3) = 0.5 per month
# P(STAGE_3 → STAGE_4) = 0.7 per month

# Monte Carlo simulation
def simulate_transition_time(current_stage, n_simulations=10000):
    times = []
    for _ in range(n_simulations):
        months = 0
        stage = current_stage

        while stage != "STAGE_4_MATURE" and months < 48:
            months += 1
            # Transition probabilities
            if stage == "STAGE_1_SEED":
                if random.random() < 0.3:
                    stage = "STAGE_2_FORMING"
            elif stage == "STAGE_2_FORMING":
                if random.random() < 0.5:
                    stage = "STAGE_3_SPREADING"
            elif stage == "STAGE_3_SPREADING":
                if random.random() < 0.7:
                    stage = "STAGE_4_MATURE"

        times.append(months)

    return {
        'median_months': np.median(times),
        'p25_months': np.percentile(times, 25),
        'p75_months': np.percentile(times, 75),
        'mean_months': np.mean(times)
    }

# Example output for STAGE_1 theme
# Median: 9 months, 95% CI: 5-16 months
```

### Required Data
- Weekly regime data for all tickers in each theme
- Historical tracking of cascade progression

### Validation Approach
```python
# Backtest on completed transitions
# Find themes that reached STAGE_4 in past 6 months
# Work backwards to find when they were in STAGE_1
# Measure actual transition time vs predicted
```

**Pros**:
- Directly measures the small→large cap cascade
- Probabilistic model provides confidence intervals
- Can detect stuck themes early (remain in STAGE_1 for >12 months)

**Cons**:
- Requires continuous weekly tracking
- Transition probabilities need calibration (limited history)
- External catalysts can accelerate/decelerate transitions

---

## Method 4: Multi-Signal Composite Model

### Concept
Combine all three methods into a weighted ensemble for robust timing estimates.

### Implementation

```python
class ThemeTimingPredictor:
    def __init__(self):
        self.weights = {
            'fiedler_velocity': 0.35,
            'score_percentage': 0.30,
            'cascade_stage': 0.35
        }

    def predict_months_to_tier1(self, theme_name):
        # Method 1: Fiedler velocity
        fiedler_data = get_fiedler_timeseries(theme_name)
        velocity_estimate = self.calculate_velocity_estimate(fiedler_data)

        # Method 2: Score percentage
        score_data = calculate_theme_readiness(theme_name)
        score_estimate = self.calculate_score_estimate(score_data)

        # Method 3: Cascade stage
        cascade_data = classify_cascade_stage(theme_name)
        cascade_estimate = self.calculate_cascade_estimate(cascade_data)

        # Weighted average
        composite_estimate = (
            velocity_estimate * self.weights['fiedler_velocity'] +
            score_estimate * self.weights['score_percentage'] +
            cascade_estimate * self.weights['cascade_stage']
        )

        # Calculate confidence based on signal agreement
        estimates = [velocity_estimate, score_estimate, cascade_estimate]
        signal_std = np.std(estimates)

        if signal_std < 2:
            confidence = "HIGH"
            ci_range = (composite_estimate * 0.8, composite_estimate * 1.2)
        elif signal_std < 4:
            confidence = "MEDIUM"
            ci_range = (composite_estimate * 0.6, composite_estimate * 1.4)
        else:
            confidence = "LOW"
            ci_range = (composite_estimate * 0.5, composite_estimate * 1.8)

        return {
            'estimated_months': composite_estimate,
            'confidence': confidence,
            'range': ci_range,
            'signals': {
                'velocity': velocity_estimate,
                'score': score_estimate,
                'cascade': cascade_estimate
            }
        }
```

### Example Output

```python
# 해운 (Shipping) - Current TIER 3
predictor = ThemeTimingPredictor()
result = predictor.predict_months_to_tier1('해운')

# Output:
{
    'estimated_months': 14.2,
    'confidence': 'MEDIUM',
    'range': (8.5, 19.9),
    'signals': {
        'velocity': 12.5,  # Based on Fiedler: 2.00 → 6.00, needs to reach 15
        'score': 16.8,     # Based on low avg score_percentage (45)
        'cascade': 13.5    # Based on STAGE_1 (small-caps bull, large-caps bear)
    }
}

# Interpretation:
# Estimated timing: 14 months (medium confidence)
# Range: 9-20 months
# Recommendation: Start research now, accumulate in 6-8 months when confidence improves
```

---

## Implementation Roadmap

### Phase 1: Data Collection (Weeks 1-4)
**Goal**: Build historical database for all methods

1. **Fiedler Timeseries**
   - [x] Already have: Sector-level weekly data (Feb-Oct 2025)
   - [ ] Need: Aggregate by Naver theme
   - [ ] Need: Extend to 18+ months of history

2. **Score Percentage Tracking**
   - [x] Have: Oct 2025 snapshot
   - [ ] Need: Set up monthly cron job to save snapshots
   - [ ] Need: Build 6-month history for validation

3. **Regime Cascade Tracking**
   - [ ] Need: Weekly snapshots of regime by market cap tier
   - [ ] Need: Build transition probability database

**Actions**:
```bash
# Create monthly snapshot script
cat > /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/scripts/save_monthly_snapshot.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y-%m)
cp /mnt/nas/AutoGluon/AutoML_Krx/Filter/UCS_LRS/complete_situation_results_*.json \
   /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/snapshots/situation_${DATE}.json
EOF

# Add to crontab: 1st of each month at 18:00
# 0 18 1 * * /mnt/nas/gpt/Naver/three_layers/countryrisk/KRX/scripts/save_monthly_snapshot.sh
```

### Phase 2: Model Development (Weeks 5-8)
**Goal**: Implement all three methods and validate

1. **Method 1**: Fiedler velocity predictor
   - Calculate velocities and accelerations
   - Backtest on available 8-month data
   - Measure prediction accuracy

2. **Method 2**: Score percentage readiness
   - Aggregate scores by theme
   - Find correlation with tier status
   - Define readiness thresholds

3. **Method 3**: Cascade stage classifier
   - Classify all themes by cascade stage
   - Measure historical transition times
   - Build Markov transition matrix

**Deliverables**:
- `theme_timing_predictor.py` with all three methods
- Validation report on prediction accuracy
- Confidence interval calibration

### Phase 3: Integration & Testing (Weeks 9-12)
**Goal**: Deploy composite model and validate in real-time

1. **Composite Model**
   - Implement weighted ensemble
   - Optimize weights based on validation
   - Add confidence scoring

2. **Real-Time Monitoring**
   - Weekly updates to all TIER 3 themes
   - Alert when estimates change significantly
   - Track prediction accuracy over time

3. **Dashboard Integration**
   - Add timing estimates to 4-tier reports
   - Visualize confidence intervals
   - Show monthly progression tracking

**Deliverables**:
- Production-ready timing predictor
- Weekly monitoring dashboard
- 6-month forward estimates for all TIER 3 themes

---

## Expected Outcomes

### Short-Term (3 months)
- Basic velocity-based estimates for all TIER 3 themes
- Preliminary validation on 8-month historical data
- Identify fast-moving themes (6-9 months) vs slow themes (18+ months)

### Medium-Term (6 months)
- Score percentage history enables Method 2 validation
- Cascade transition probabilities calibrated
- Composite model with 70%+ prediction accuracy

### Long-Term (12 months)
- Full 18-month historical validation
- Proven track record of timing predictions
- Continuous refinement based on actual outcomes

---

## Risk Factors & Limitations

### Data Limitations
1. **Short History**: Only 8 months of fiedler data, need 18+ for full validation
2. **Single Score Snapshot**: Need monthly score_percentage history
3. **Market Regime Changes**: Bull/bear market shifts can invalidate patterns

### Model Assumptions
1. **Linear Growth**: Fiedler may grow non-linearly (S-curves, step functions)
2. **Cascade Consistency**: Small→large progression may skip stages
3. **External Catalysts**: Government policy, tech breakthroughs can accelerate themes

### Mitigation Strategies
1. **Conservative Estimates**: Use upper bound of confidence interval
2. **Monthly Recalibration**: Update estimates as new data arrives
3. **Signal Divergence Alerts**: Flag when methods disagree significantly
4. **Fundamental Overlay**: Always validate with sector fundamentals

---

## Conclusion

**Immediate Action**: Can implement Method 1 (Fiedler velocity) and Method 3 (Cascade stage) TODAY with existing data.

**3-Month Goal**: Build historical snapshots to enable Method 2 validation.

**6-Month Goal**: Deploy composite model with proven >70% accuracy on timing predictions.

**Key Insight**: The 12-18 month estimate is a reasonable baseline, but can be refined to:
- **Fast themes** (6-9 months): High velocity + high score_percentage + STAGE_2
- **Medium themes** (12-15 months): Medium velocity + medium scores + STAGE_1
- **Slow themes** (18-24 months): Low velocity + low scores + stuck in STAGE_0

This transforms the 4-tier framework from a qualitative classification into a **quantitative timing prediction system** with confidence intervals and early warning signals.
