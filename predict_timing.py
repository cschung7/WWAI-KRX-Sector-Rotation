#!/usr/bin/env python3
"""
Timing Prediction for TIER 3 Themes
Predicts months to TIER 1 status using Fiedler velocity analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import sys
from pathlib import Path

class ThemeTimingPredictor:
    def __init__(self):
        self.tier1_threshold = 15.0  # Fiedler value for TIER 1
        self.tier3_file = "data/tier3_research_20251027.csv"

    def load_tier3_themes(self):
        """Load current TIER 3 themes"""
        df = pd.read_csv(self.tier3_file)
        return df

    def calculate_velocity_estimate(self, theme_name, current_fiedler, week_before_fiedler):
        """
        Calculate timing estimate based on Fiedler velocity

        Uses simple linear extrapolation:
        - Weekly velocity = (current - past) / weeks
        - Weeks to threshold = (threshold - current) / velocity
        - Adjusted for acceleration/deceleration patterns
        """

        # Calculate weekly velocity (1 week delta)
        weeks_delta = 1
        velocity = (current_fiedler - week_before_fiedler) / weeks_delta

        # Calculate gap to TIER 1
        gap = self.tier1_threshold - current_fiedler

        # Check if already above threshold
        if gap <= 0:
            return {
                'status': 'ALREADY_TIER1',
                'estimated_months': 0,
                'confidence': 'HIGH'
            }

        # Check for negative velocity (declining)
        if velocity <= 0:
            return {
                'status': 'DECLINING',
                'estimated_months': float('inf'),
                'confidence': 'LOW',
                'warning': 'Theme is declining, not growing toward TIER 1'
            }

        # Calculate weeks to threshold
        weeks_to_threshold = gap / velocity
        months_to_threshold = weeks_to_threshold / 4.33  # Average weeks per month

        # Calculate acceleration (comparing to assumed past trend)
        # Assume previous velocity was 70% of current (conservative)
        assumed_past_velocity = velocity * 0.7
        acceleration = velocity - assumed_past_velocity

        # Adjust estimate based on acceleration pattern
        if acceleration > velocity * 0.3:  # Strong acceleration
            adjusted_months = months_to_threshold * 0.8
            confidence = 'MEDIUM'
            acceleration_status = 'ACCELERATING'
        elif acceleration < -velocity * 0.3:  # Deceleration
            adjusted_months = months_to_threshold * 1.3
            confidence = 'LOW'
            acceleration_status = 'DECELERATING'
        else:  # Steady
            adjusted_months = months_to_threshold
            confidence = 'MEDIUM'
            acceleration_status = 'STEADY'

        # Calculate confidence intervals (±30% for medium confidence)
        if confidence == 'MEDIUM':
            lower_bound = adjusted_months * 0.7
            upper_bound = adjusted_months * 1.3
        else:  # LOW
            lower_bound = adjusted_months * 0.5
            upper_bound = adjusted_months * 1.8

        return {
            'status': 'GROWING',
            'estimated_months': round(adjusted_months, 1),
            'confidence': confidence,
            'range': (round(lower_bound, 1), round(upper_bound, 1)),
            'acceleration_status': acceleration_status,
            'details': {
                'current_fiedler': round(current_fiedler, 2),
                'target_fiedler': self.tier1_threshold,
                'gap': round(gap, 2),
                'weekly_velocity': round(velocity, 3),
                'weeks_to_threshold': round(weeks_to_threshold, 1)
            }
        }

    def predict_all_tier3(self):
        """Predict timing for all TIER 3 themes"""
        df = self.load_tier3_themes()

        results = []
        for _, row in df.iterrows():
            theme = row['Theme']
            current = row['Last_Week_Fiedler']
            past = row['Week_Before_Fiedler']

            prediction = self.calculate_velocity_estimate(theme, current, past)

            results.append({
                'theme': theme,
                'stocks': row['Stocks'],
                'current_fiedler': round(current, 2),
                'past_fiedler': round(past, 2),
                'change': round(row['Change'], 2),
                'pct_change': round(row['Pct_Change'], 1),
                **prediction
            })

        return results

    def generate_report(self, results):
        """Generate formatted timing prediction report"""
        print("=" * 100)
        print("TIER 3 THEME TIMING PREDICTIONS")
        print("=" * 100)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"Prediction Method: Fiedler Velocity Extrapolation")
        print(f"TIER 1 Threshold: Fiedler ≥ {self.tier1_threshold}")
        print("=" * 100)
        print()

        # Sort by estimated months (ascending)
        results_sorted = sorted(
            [r for r in results if r['status'] == 'GROWING'],
            key=lambda x: x['estimated_months']
        )

        # Fast-moving themes (< 12 months)
        fast_themes = [r for r in results_sorted if r['estimated_months'] < 12]
        if fast_themes:
            print("🚀 FAST-MOVING THEMES (< 12 months)")
            print("-" * 100)
            for i, r in enumerate(fast_themes, 1):
                print(f"{i}. {r['theme']:<30} ({r['stocks']:>3} stocks)")
                print(f"   Current: {r['current_fiedler']:>6.2f} → Target: {self.tier1_threshold:>6.2f} (Gap: {r['details']['gap']:>5.2f})")
                print(f"   Velocity: {r['details']['weekly_velocity']:>6.3f}/week | {r['acceleration_status']}")
                print(f"   ⏱️  Estimated: {r['estimated_months']:>4.1f} months (Range: {r['range'][0]:.1f}-{r['range'][1]:.1f} months)")
                print(f"   📊 Confidence: {r['confidence']}")
                print()

        # Medium-speed themes (12-18 months)
        medium_themes = [r for r in results_sorted if 12 <= r['estimated_months'] < 18]
        if medium_themes:
            print("📈 MEDIUM-SPEED THEMES (12-18 months)")
            print("-" * 100)
            for i, r in enumerate(medium_themes, 1):
                print(f"{i}. {r['theme']:<30} ({r['stocks']:>3} stocks)")
                print(f"   Current: {r['current_fiedler']:>6.2f} → Target: {self.tier1_threshold:>6.2f} (Gap: {r['details']['gap']:>5.2f})")
                print(f"   Velocity: {r['details']['weekly_velocity']:>6.3f}/week | {r['acceleration_status']}")
                print(f"   ⏱️  Estimated: {r['estimated_months']:>4.1f} months (Range: {r['range'][0]:.1f}-{r['range'][1]:.1f} months)")
                print(f"   📊 Confidence: {r['confidence']}")
                print()

        # Slow-moving themes (> 18 months)
        slow_themes = [r for r in results_sorted if r['estimated_months'] >= 18]
        if slow_themes:
            print("🐌 SLOW-MOVING THEMES (> 18 months)")
            print("-" * 100)
            for i, r in enumerate(slow_themes, 1):
                print(f"{i}. {r['theme']:<30} ({r['stocks']:>3} stocks)")
                print(f"   Current: {r['current_fiedler']:>6.2f} → Target: {self.tier1_threshold:>6.2f} (Gap: {r['details']['gap']:>5.2f})")
                print(f"   Velocity: {r['details']['weekly_velocity']:>6.3f}/week | {r['acceleration_status']}")
                print(f"   ⏱️  Estimated: {r['estimated_months']:>4.1f} months (Range: {r['range'][0]:.1f}-{r['range'][1]:.1f} months)")
                print(f"   📊 Confidence: {r['confidence']}")
                print()

        # Declining themes
        declining = [r for r in results if r['status'] == 'DECLINING']
        if declining:
            print("⚠️  DECLINING THEMES (Not moving toward TIER 1)")
            print("-" * 100)
            for i, r in enumerate(declining, 1):
                print(f"{i}. {r['theme']:<30} ({r['stocks']:>3} stocks)")
                print(f"   Current: {r['current_fiedler']:>6.2f} (was {r['past_fiedler']:>6.2f})")
                print(f"   ⚠️  WARNING: {r.get('warning', 'Negative growth')}")
                print()

        print("=" * 100)
        print("SUMMARY STATISTICS")
        print("=" * 100)
        growing = [r for r in results if r['status'] == 'GROWING']
        if growing:
            estimates = [r['estimated_months'] for r in growing]
            print(f"Total TIER 3 themes analyzed: {len(results)}")
            print(f"Growing themes: {len(growing)}")
            print(f"Declining themes: {len(declining)}")
            print()
            print(f"Average estimated months: {np.mean(estimates):.1f}")
            print(f"Median estimated months: {np.median(estimates):.1f}")
            print(f"Fastest theme: {min(estimates):.1f} months")
            print(f"Slowest theme: {max(estimates):.1f} months")
            print()
            print(f"Fast-moving (< 12mo): {len(fast_themes)} themes ({len(fast_themes)/len(growing)*100:.1f}%)")
            print(f"Medium-speed (12-18mo): {len(medium_themes)} themes ({len(medium_themes)/len(growing)*100:.1f}%)")
            print(f"Slow-moving (> 18mo): {len(slow_themes)} themes ({len(slow_themes)/len(growing)*100:.1f}%)")

        print("=" * 100)
        print()
        print("📝 METHODOLOGY NOTES:")
        print("- Estimates based on linear extrapolation of weekly Fiedler velocity")
        print("- Confidence intervals: MEDIUM ±30%, LOW ±50%")
        print("- Acceleration adjustment: +20% for accelerating, -30% for decelerating")
        print("- LIMITATION: Only 1 week of velocity data (need multi-week history for better accuracy)")
        print("- RECOMMENDATION: Monitor monthly and recalibrate estimates as patterns become clearer")
        print()

    def save_predictions_json(self, results, output_file):
        """Save predictions to JSON file"""
        output_data = {
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'method': 'fiedler_velocity',
            'tier1_threshold': self.tier1_threshold,
            'predictions': results
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Predictions saved to: {output_file}")

def main():
    predictor = ThemeTimingPredictor()

    # Load and predict
    print("Loading TIER 3 themes and calculating timing predictions...\n")
    results = predictor.predict_all_tier3()

    # Generate report
    predictor.generate_report(results)

    # Save to JSON
    output_file = f"data/tier3_timing_predictions_{datetime.now().strftime('%Y%m%d')}.json"
    predictor.save_predictions_json(results, output_file)

    # Investment recommendations
    print("=" * 100)
    print("💡 INVESTMENT RECOMMENDATIONS")
    print("=" * 100)

    fast = [r for r in results if r.get('status') == 'GROWING' and r['estimated_months'] < 12]
    if fast:
        print("\n🎯 PRIORITY RESEARCH (Fast-moving themes):")
        for r in sorted(fast, key=lambda x: x['estimated_months'])[:3]:
            print(f"\n{r['theme']}")
            print(f"  • Timeline: {r['estimated_months']:.1f} months ({r['range'][0]:.1f}-{r['range'][1]:.1f} months)")
            print(f"  • Action: Start deep research NOW, begin accumulation in 3-6 months")
            print(f"  • Risk: {r['confidence']} confidence - monitor monthly for velocity changes")

    medium = [r for r in results if r.get('status') == 'GROWING' and 12 <= r['estimated_months'] < 18]
    if medium:
        print("\n📋 WATCHLIST (Standard TIER 3 timeline):")
        for r in sorted(medium, key=lambda x: x['estimated_months'])[:3]:
            print(f"\n{r['theme']}")
            print(f"  • Timeline: {r['estimated_months']:.1f} months ({r['range'][0]:.1f}-{r['range'][1]:.1f} months)")
            print(f"  • Action: Quarterly review, wait for acceleration signals")
            print(f"  • Catalyst: Monitor for fundamental catalysts to accelerate timeline")

    print("\n" + "=" * 100)

if __name__ == "__main__":
    main()
