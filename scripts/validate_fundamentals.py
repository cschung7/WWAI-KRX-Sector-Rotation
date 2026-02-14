#!/usr/bin/env python3
"""
Fundamental Validation Layer for Sector Rotation Analysis
Reconciles quantitative (Fiedler cohesion) signals with fundamental data

This script adds Layer 4 (Fundamental Validation) to the existing 3-layer framework:
- Layer 1: Fiedler Cohesion (price correlation network)
- Layer 2: Regime Detection (bull/bear classification)
- Layer 3: Leadership Gap (large-cap vs small-cap)
- Layer 4: Fundamental Validation (earnings, macro, sentiment) [NEW]

Usage:
    python3 validate_fundamentals.py --date 20260109 --top-themes 10
"""

import pandas as pd
import numpy as np
import json
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import glob

# Configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR, DB_FILE, REGIME_DIR
from regime_utils import calculate_theme_regime_stats, load_regime_data, load_db_data, load_cohesion_data

REPORTS_DIR.mkdir(exist_ok=True)


# =============================================================================
# SECTOR-MACRO MAPPING: Define fundamental indicators for each sector
# =============================================================================

SECTOR_FUNDAMENTAL_MAP = {
    # Energy & Resources
    "도시가스": {
        "category": "Energy",
        "positive_indicators": [
            "Natural gas prices rising",
            "Cold winter forecast",
            "LNG demand increasing",
            "Utility rate hikes approved"
        ],
        "negative_indicators": [
            "Natural gas prices falling",
            "Mild weather forecast",
            "Renewable energy substitution",
            "Price cap regulations"
        ],
        "key_earnings_drivers": ["Gas sales volume", "Unit margins", "Distribution costs"],
        "macro_sensitivity": "HIGH",
        "earnings_lag": "1Q"  # Earnings reflect changes with 1 quarter lag
    },
    "LNG(액화천연가스)": {
        "category": "Energy",
        "positive_indicators": [
            "Global LNG prices rising",
            "New LNG terminal contracts",
            "Energy security concerns",
            "Coal-to-gas switching"
        ],
        "negative_indicators": [
            "LNG oversupply",
            "Mild global weather",
            "Nuclear restart (Japan)",
            "Spot prices falling"
        ],
        "key_earnings_drivers": ["LNG import volume", "Term contract margins", "Spot trading gains"],
        "macro_sensitivity": "HIGH",
        "earnings_lag": "1Q"
    },
    "정유": {
        "category": "Energy",
        "positive_indicators": [
            "Oil prices rising",
            "Refining margins expanding",
            "Sanctions on Russia/Iran",
            "PX margins improving",
            "Gasoline demand strong"
        ],
        "negative_indicators": [
            "Oil prices falling",
            "Refining overcapacity",
            "EV adoption accelerating",
            "Petrochemical margins weak"
        ],
        "key_earnings_drivers": ["Refining margin", "PX-Naphtha spread", "Inventory gains/losses"],
        "macro_sensitivity": "VERY HIGH",
        "earnings_lag": "IMMEDIATE"
    },

    # Heavy Industry
    "조선": {
        "category": "Heavy Industry",
        "positive_indicators": [
            "Shipbuilding orders increasing",
            "LNG carrier demand strong",
            "Ship prices rising",
            "US Navy contracts",
            "Backlog growing"
        ],
        "negative_indicators": [
            "Order cancellations",
            "China competition intensifying",
            "Steel prices spiking",
            "Labor disputes"
        ],
        "key_earnings_drivers": ["Order backlog", "Ship prices", "Delivery schedule", "Steel costs"],
        "macro_sensitivity": "MEDIUM",
        "earnings_lag": "2-3Y"  # Long construction cycle
    },
    "건설기계": {
        "category": "Heavy Industry",
        "positive_indicators": [
            "Infrastructure spending up",
            "Mining activity increasing",
            "Emerging market growth",
            "Replacement cycle demand"
        ],
        "negative_indicators": [
            "Construction slowdown",
            "Mining capex cuts",
            "China dumping equipment",
            "Currency headwinds"
        ],
        "key_earnings_drivers": ["Unit sales", "Parts/service revenue", "FX rates"],
        "macro_sensitivity": "HIGH",
        "earnings_lag": "2Q"
    },

    # Defense
    "방위산업/전쟁 및 테러": {
        "category": "Defense",
        "positive_indicators": [
            "Defense budget increase",
            "Geopolitical tensions rising",
            "Export contract wins",
            "NATO spending commitments",
            "Middle East orders"
        ],
        "negative_indicators": [
            "Defense budget cuts",
            "Peace negotiations",
            "Export restrictions",
            "Program cancellations"
        ],
        "key_earnings_drivers": ["Domestic orders", "Export contracts", "R&D funding"],
        "macro_sensitivity": "LOW",  # Government-backed, less cyclical
        "earnings_lag": "1-2Y"
    },

    # Financial
    "증권": {
        "category": "Financial",
        "positive_indicators": [
            "Bull market/KOSPI rising",
            "Trading volume increasing",
            "IPO pipeline strong",
            "Interest rate spreads",
            "Wealth management growth"
        ],
        "negative_indicators": [
            "Bear market/KOSPI falling",
            "Trading volume declining",
            "IPO market frozen",
            "Margin call risks",
            "Regulatory tightening"
        ],
        "key_earnings_drivers": ["Brokerage commissions", "Proprietary trading", "IB fees"],
        "macro_sensitivity": "VERY HIGH",
        "earnings_lag": "IMMEDIATE"
    },

    # Technology
    "뉴로모픽 반도체": {
        "category": "Technology",
        "positive_indicators": [
            "AI chip demand growing",
            "Edge AI adoption",
            "Data center expansion",
            "Government R&D support"
        ],
        "negative_indicators": [
            "Semiconductor cycle downturn",
            "Alternative architectures",
            "Supply chain issues",
            "Funding pullback"
        ],
        "key_earnings_drivers": ["R&D progress", "Partnership announcements", "Sample shipments"],
        "macro_sensitivity": "MEDIUM",
        "earnings_lag": "LONG"  # Emerging technology
    },
    "유리 기판": {
        "category": "Technology",
        "positive_indicators": [
            "Advanced packaging demand",
            "AI server growth",
            "HBM adoption",
            "Technology leadership"
        ],
        "negative_indicators": [
            "Semiconductor slowdown",
            "Technology obsolescence",
            "Competition from alternatives",
            "Customer concentration risk"
        ],
        "key_earnings_drivers": ["Volume shipments", "ASP trends", "Yield improvements"],
        "macro_sensitivity": "MEDIUM",
        "earnings_lag": "2Q"
    },
    "전력저장장치(ESS)": {
        "category": "Technology",
        "positive_indicators": [
            "Renewable energy growth",
            "Grid storage mandates",
            "Battery cost declines",
            "Electric grid instability"
        ],
        "negative_indicators": [
            "Safety incidents",
            "Subsidy cuts",
            "Chinese competition",
            "Raw material spikes"
        ],
        "key_earnings_drivers": ["Project backlog", "Battery costs", "Government support"],
        "macro_sensitivity": "MEDIUM",
        "earnings_lag": "1Q"
    },
    "2차전지(생산)": {
        "category": "Technology",
        "positive_indicators": [
            "EV sales growth",
            "Battery demand exceeding supply",
            "Technology breakthroughs",
            "IRA benefits (US)"
        ],
        "negative_indicators": [
            "EV demand slowdown",
            "Chinese oversupply",
            "LFP vs NCA competition",
            "Raw material volatility"
        ],
        "key_earnings_drivers": ["Capacity utilization", "Cell prices", "Customer orders"],
        "macro_sensitivity": "HIGH",
        "earnings_lag": "1Q"
    },

    # Other common themes
    "스마트팩토리(스마트공장)": {
        "category": "Industrial Tech",
        "positive_indicators": [
            "Manufacturing automation trend",
            "Labor shortage in factories",
            "Industry 4.0 investment",
            "Government subsidies"
        ],
        "negative_indicators": [
            "Capex cuts by manufacturers",
            "Economic recession fears",
            "Integration complexity",
            "ROI skepticism"
        ],
        "key_earnings_drivers": ["Project wins", "Recurring revenue", "System integration"],
        "macro_sensitivity": "MEDIUM",
        "earnings_lag": "1-2Q"
    }
}

# Default template for themes not in the map
DEFAULT_FUNDAMENTAL_TEMPLATE = {
    "category": "General",
    "positive_indicators": [
        "Sector growth outlook positive",
        "Earnings estimates rising",
        "Industry tailwinds present"
    ],
    "negative_indicators": [
        "Sector headwinds emerging",
        "Earnings estimates falling",
        "Competitive pressure increasing"
    ],
    "key_earnings_drivers": ["Revenue growth", "Margin trends", "Market share"],
    "macro_sensitivity": "MEDIUM",
    "earnings_lag": "1Q"
}


# =============================================================================
# EXTERNAL VALIDATION OVERRIDES: Manual adjustments from research/web search
# =============================================================================
# This section allows incorporating findings from external research (web search,
# analyst reports, earnings data) to override the automated fundamental estimates.
#
# Format: theme_name -> {fund_score_override, reason, date_updated}
#
# Update this section when you have new fundamental information from:
# - Web search on sector news
# - Company earnings releases
# - Analyst report changes
# - Macro indicator updates

FUNDAMENTAL_OVERRIDES = {
    "도시가스": {
        "fund_score_override": 30,  # Override to LOW due to weak earnings
        "override_reason": "KOGAS earnings declining: Revenue -5.9%, Op Income -10.9%, Net Income -33.7% YoY (Q3 2025)",
        "source": "FnGuide/Web Search",
        "date_updated": "2026-01-10",
        "divergence_note": "High cohesion may indicate coordinated SELLING, not buying opportunity"
    },
    # Add more overrides as you gather fundamental data
    # Example:
    # "테마명": {
    #     "fund_score_override": 75,
    #     "override_reason": "Strong earnings beat, raised guidance",
    #     "source": "DART filings",
    #     "date_updated": "2026-01-10",
    #     "divergence_note": None
    # },
}


@dataclass
class ThemeValidation:
    """Validation result for a single theme"""
    theme_name: str
    tier: int

    # Quantitative scores (from existing system)
    fiedler_change: float
    current_fiedler: float
    bull_regime_pct: float
    trend_strength: float

    # Computed scores
    quant_score: float = 0.0
    fund_score: float = 0.0  # To be filled by validation
    composite_score: float = 0.0

    # Validation flags
    has_divergence: bool = False
    divergence_type: str = ""

    # Fundamental data (to be filled)
    fundamental_data: Dict = field(default_factory=dict)
    validation_notes: List[str] = field(default_factory=list)

    # Final recommendation
    recommendation: str = ""
    action: str = ""


class FundamentalValidator:
    """Validates quantitative signals against fundamental indicators"""

    def __init__(self, date_str: str):
        self.date_str = date_str
        self.themes_data = {}
        self.validations: List[ThemeValidation] = []

    def load_tier_data(self) -> Dict:
        """Load 4-tier classification data"""
        summary_file = DATA_DIR / f"4tier_summary_{self.date_str}.json"
        if not summary_file.exists():
            # Try to find latest
            files = list(DATA_DIR.glob("4tier_summary_*.json"))
            if files:
                summary_file = sorted(files)[-1]
                self.date_str = summary_file.stem.split('_')[-1]

        if not summary_file.exists():
            raise FileNotFoundError(f"No 4tier_summary file found")

        with open(summary_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_cohesion_data(self) -> pd.DataFrame:
        """Load enhanced cohesion data"""
        pattern = f"enhanced_cohesion_themes_{self.date_str}.csv"
        files = list(DATA_DIR.glob(pattern))
        if not files:
            files = list(DATA_DIR.glob("enhanced_cohesion_themes_*.csv"))

        if files:
            return pd.read_csv(sorted(files)[-1])
        return pd.DataFrame()

    def load_regime_data(self) -> Tuple[pd.DataFrame, str]:
        """Load regime data"""
        regime_files = list(REGIME_DIR.glob("all_regimes_*.csv"))
        if not regime_files:
            return pd.DataFrame(), ""

        latest_file = sorted(regime_files)[-1]
        df = pd.read_csv(latest_file)
        latest_date = df['Date'].max()
        return df[df['Date'] == latest_date].copy(), latest_date

    def calculate_quant_score(self, theme_data: Dict) -> float:
        """Calculate quantitative score (0-100) from existing metrics"""
        # Normalize each component to 0-1 range, then scale to 100

        fiedler_score = min(theme_data.get('fiedler_change', 0) / 3.0, 1.0)  # Cap at 3.0
        bull_score = theme_data.get('bull_regime_pct', 0) / 100.0
        trend_score = (theme_data.get('trend_strength', 0) + 1) / 2.0  # -1 to 1 -> 0 to 1

        # Weighted combination
        quant_score = (
            0.30 * fiedler_score +
            0.45 * bull_score +
            0.25 * trend_score
        ) * 100

        return round(quant_score, 1)

    def get_fundamental_template(self, theme_name: str) -> Dict:
        """Get fundamental validation template for a theme"""
        return SECTOR_FUNDAMENTAL_MAP.get(theme_name, DEFAULT_FUNDAMENTAL_TEMPLATE)

    def estimate_fundamental_score(self, theme_name: str, theme_data: Dict) -> Tuple[float, List[str]]:
        """
        Estimate fundamental score based on available data and heuristics.
        Returns (score, validation_notes)

        In production, this would integrate with:
        - FnGuide API for earnings data
        - Macro data feeds
        - News sentiment APIs

        For now, uses heuristic rules based on:
        - Bull regime as proxy for price action (reflects market's fundamental view)
        - Trend strength as proxy for momentum
        - Sector category defaults
        - Manual overrides from external research (FUNDAMENTAL_OVERRIDES)
        """
        template = self.get_fundamental_template(theme_name)
        notes = []

        # Check for manual override first
        if theme_name in FUNDAMENTAL_OVERRIDES:
            override = FUNDAMENTAL_OVERRIDES[theme_name]
            fund_score = override['fund_score_override']
            notes.append(f"⚠️ MANUAL OVERRIDE APPLIED")
            notes.append(f"   Score: {fund_score}/100")
            notes.append(f"   Reason: {override['override_reason']}")
            notes.append(f"   Source: {override['source']}")
            notes.append(f"   Updated: {override['date_updated']}")
            if override.get('divergence_note'):
                notes.append(f"   Note: {override['divergence_note']}")
            notes.append("")
            return fund_score, notes

        # Base score from sector category
        category_base = {
            "Energy": 50,
            "Heavy Industry": 55,
            "Defense": 65,  # Generally stable
            "Financial": 45,  # More volatile
            "Technology": 50,
            "Industrial Tech": 50,
            "General": 50
        }

        base_score = category_base.get(template['category'], 50)
        notes.append(f"Category base ({template['category']}): {base_score}")

        # Adjust based on macro sensitivity
        # High sensitivity = more weight to recent price action
        sensitivity_mult = {
            "VERY HIGH": 1.3,
            "HIGH": 1.15,
            "MEDIUM": 1.0,
            "LOW": 0.85
        }

        mult = sensitivity_mult.get(template['macro_sensitivity'], 1.0)

        # Use regime data as a proxy for market's fundamental assessment
        bull_pct = theme_data.get('bull_regime_pct', 50)
        trend = theme_data.get('trend_strength', 0)

        # Regime-based adjustment (-25 to +25)
        regime_adj = (bull_pct - 50) / 2  # -25 to +25
        notes.append(f"Regime adjustment: {regime_adj:+.1f} (bull: {bull_pct:.1f}%)")

        # Trend-based adjustment (-15 to +15)
        trend_adj = trend * 15
        notes.append(f"Trend adjustment: {trend_adj:+.1f} (trend: {trend:+.3f})")

        # Apply sensitivity multiplier
        fund_score = base_score + (regime_adj + trend_adj) * mult

        # Clamp to 0-100
        fund_score = max(0, min(100, fund_score))

        # Add validation checklist items
        notes.append("")
        notes.append("📋 MANUAL VALIDATION CHECKLIST:")
        notes.append(f"   Sector: {template['category']}")
        notes.append(f"   Macro Sensitivity: {template['macro_sensitivity']}")
        notes.append(f"   Earnings Lag: {template['earnings_lag']}")
        notes.append("")
        notes.append("   ✅ Positive Indicators to Check:")
        for ind in template['positive_indicators'][:3]:
            notes.append(f"      □ {ind}")
        notes.append("")
        notes.append("   ❌ Negative Indicators to Check:")
        for ind in template['negative_indicators'][:3]:
            notes.append(f"      □ {ind}")
        notes.append("")
        notes.append("   📊 Key Earnings Drivers:")
        for driver in template['key_earnings_drivers']:
            notes.append(f"      • {driver}")

        return round(fund_score, 1), notes

    def detect_divergence(self, quant_score: float, fund_score: float) -> Tuple[bool, str]:
        """Detect divergence between quantitative and fundamental signals"""
        diff = abs(quant_score - fund_score)

        if diff > 30:
            if quant_score > fund_score:
                return True, "QUANT_STRONG_FUND_WEAK"
            else:
                return True, "FUND_STRONG_QUANT_WEAK"
        elif diff > 20:
            if quant_score > fund_score:
                return True, "MODERATE_DIVERGENCE_QUANT_LEADS"
            else:
                return True, "MODERATE_DIVERGENCE_FUND_LEADS"

        return False, ""

    def get_recommendation(self, composite_score: float, has_divergence: bool, divergence_type: str) -> Tuple[str, str]:
        """Generate recommendation based on composite score and divergence"""

        if has_divergence:
            if divergence_type == "QUANT_STRONG_FUND_WEAK":
                return "⚠️ DIVERGENT - VERIFY", "Wait for fundamental confirmation; potential value trap"
            elif divergence_type == "FUND_STRONG_QUANT_WEAK":
                return "⚡ EARLY ENTRY", "Fundamental strength precedes price; consider early accumulation"
            else:
                return "👁️ MONITOR", "Moderate divergence; additional research needed"

        if composite_score >= 70:
            return "✅ CONFIRMED BUY", "Strong alignment between technical and fundamental"
        elif composite_score >= 55:
            return "⚡ ACCUMULATE", "Good alignment; build position gradually"
        elif composite_score >= 40:
            return "👁️ WATCH", "Neutral; wait for clearer signal"
        elif composite_score >= 25:
            return "⏸️ HOLD", "Weak signal; maintain existing positions only"
        else:
            return "❌ AVOID", "Weak or negative signals; consider reducing exposure"

    def validate_theme(self, theme_name: str, tier: int, cohesion_row: pd.Series, regime_pct: float, trend: float) -> ThemeValidation:
        """Run full validation for a single theme"""

        # Extract quantitative data
        fiedler_change = cohesion_row.get('fiedler_change', cohesion_row.get('Change', 0))
        current_fiedler = cohesion_row.get('current_fiedler', cohesion_row.get('Last_Week_Fiedler', 0))

        theme_data = {
            'fiedler_change': fiedler_change,
            'current_fiedler': current_fiedler,
            'bull_regime_pct': regime_pct,
            'trend_strength': trend
        }

        # Calculate quantitative score
        quant_score = self.calculate_quant_score(theme_data)

        # Estimate fundamental score
        fund_score, validation_notes = self.estimate_fundamental_score(theme_name, theme_data)

        # Calculate composite score
        # Apply 30% penalty if divergent
        has_divergence, divergence_type = self.detect_divergence(quant_score, fund_score)

        if has_divergence:
            composite_score = (quant_score * 0.5 + fund_score * 0.5) * 0.7
        else:
            composite_score = quant_score * 0.5 + fund_score * 0.5

        # Get recommendation
        recommendation, action = self.get_recommendation(composite_score, has_divergence, divergence_type)

        return ThemeValidation(
            theme_name=theme_name,
            tier=tier,
            fiedler_change=fiedler_change,
            current_fiedler=current_fiedler,
            bull_regime_pct=regime_pct,
            trend_strength=trend,
            quant_score=quant_score,
            fund_score=fund_score,
            composite_score=round(composite_score, 1),
            has_divergence=has_divergence,
            divergence_type=divergence_type,
            fundamental_data=self.get_fundamental_template(theme_name),
            validation_notes=validation_notes,
            recommendation=recommendation,
            action=action
        )

    def run_validation(self, top_n: int = 10) -> List[ThemeValidation]:
        """Run validation on top themes from each tier using ACTUAL regime data"""

        print("=" * 80)
        print("FUNDAMENTAL VALIDATION LAYER (Regime-Validated)")
        print("=" * 80)
        print(f"Date: {self.date_str}")
        print()

        # Load data using regime_utils
        print("Loading data...")
        summary = self.load_tier_data()
        cohesion_df = load_cohesion_data(self.date_str)
        regime_summary, regime_date = load_regime_data()
        db_df = load_db_data()

        print(f"  - 4-tier summary loaded")
        print(f"  - Cohesion data: {len(cohesion_df)} themes")
        print(f"  - Regime data as of: {regime_date}")
        print(f"  - Database: {len(db_df)} stocks")
        print()

        # Collect themes to validate
        themes_to_validate = []

        for tier_key in ['tier1', 'tier2', 'tier3']:
            tier_num = int(tier_key[-1])
            tier_themes = summary.get(tier_key, {}).get('themes', [])
            for theme in tier_themes[:top_n]:
                themes_to_validate.append((theme, tier_num))

        print(f"Validating {len(themes_to_validate)} themes with ACTUAL regime data...")
        print()

        validations = []
        for theme_name, tier in themes_to_validate:
            # Find cohesion data for this theme
            if 'theme' in cohesion_df.columns:
                cohesion_row = cohesion_df[cohesion_df['theme'] == theme_name]
            elif 'Theme' in cohesion_df.columns:
                cohesion_row = cohesion_df[cohesion_df['Theme'] == theme_name]
            else:
                continue

            if cohesion_row.empty:
                continue

            cohesion_row = cohesion_row.iloc[0]

            # Get ACTUAL regime data for this theme
            regime_stats = calculate_theme_regime_stats(theme_name, db_df, regime_summary)

            if regime_stats:
                bull_pct = regime_stats['avg_bull_pct']
                trend = regime_stats['avg_trend']
            else:
                # Fallback to cohesion-based estimate if no regime data
                fiedler_change = cohesion_row.get('fiedler_change', cohesion_row.get('Change', 0))
                bull_pct = 50 + (fiedler_change * 10)  # Rough estimate
                trend = fiedler_change * 0.1

            validation = self.validate_theme(theme_name, tier, cohesion_row, bull_pct, trend)
            validations.append(validation)

        self.validations = validations
        return validations

    def generate_report(self) -> Path:
        """Generate divergence alerts report"""

        report_file = REPORTS_DIR / f"FUNDAMENTAL_VALIDATION_{self.date_str}.md"

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("# Fundamental Validation Report\n\n")
            f.write(f"**Date**: {self.date_str}\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("**Framework**: Four-Layer Analysis (Cohesion × Regime × Leadership × Fundamentals)\n\n")
            f.write("---\n\n")

            # Summary Statistics
            divergent_count = sum(1 for v in self.validations if v.has_divergence)
            confirmed_count = sum(1 for v in self.validations if not v.has_divergence and v.composite_score >= 55)

            f.write("## 📊 VALIDATION SUMMARY\n\n")
            f.write(f"| Metric | Count |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Total Validated | {len(self.validations)} |\n")
            f.write(f"| ✅ Confirmed (Aligned) | {confirmed_count} |\n")
            f.write(f"| ⚠️ Divergent (Conflict) | {divergent_count} |\n")
            f.write(f"| Average Composite Score | {np.mean([v.composite_score for v in self.validations]):.1f} |\n\n")

            # Divergence Alerts (Most Important)
            divergent = [v for v in self.validations if v.has_divergence]
            if divergent:
                f.write("## 🚨 DIVERGENCE ALERTS\n\n")
                f.write("**These themes show conflict between quantitative and fundamental signals:**\n\n")

                for v in sorted(divergent, key=lambda x: x.tier):
                    f.write(f"### ⚠️ {v.theme_name} (TIER {v.tier})\n\n")
                    f.write(f"| Metric | Value |\n")
                    f.write(f"|--------|-------|\n")
                    f.write(f"| Quant Score | {v.quant_score:.1f}/100 |\n")
                    f.write(f"| Fund Score | {v.fund_score:.1f}/100 |\n")
                    f.write(f"| Composite | {v.composite_score:.1f}/100 (penalized) |\n")
                    f.write(f"| Divergence Type | {v.divergence_type} |\n\n")

                    f.write(f"**Recommendation**: {v.recommendation}\n")
                    f.write(f"**Action**: {v.action}\n\n")

                    f.write("**Validation Notes**:\n")
                    for note in v.validation_notes:
                        f.write(f"{note}\n")
                    f.write("\n---\n\n")

            # Confirmed Themes
            confirmed = [v for v in self.validations if not v.has_divergence and v.composite_score >= 55]
            if confirmed:
                f.write("## ✅ CONFIRMED THEMES\n\n")
                f.write("**These themes have aligned quantitative and fundamental signals:**\n\n")

                f.write("| Theme | Tier | Quant | Fund | Composite | Recommendation |\n")
                f.write("|-------|------|-------|------|-----------|----------------|\n")

                for v in sorted(confirmed, key=lambda x: -x.composite_score):
                    f.write(f"| {v.theme_name} | {v.tier} | {v.quant_score:.0f} | {v.fund_score:.0f} | {v.composite_score:.0f} | {v.recommendation} |\n")

                f.write("\n")

            # Watchlist
            watchlist = [v for v in self.validations if not v.has_divergence and v.composite_score < 55]
            if watchlist:
                f.write("## 👁️ WATCHLIST\n\n")
                f.write("**These themes need more development before investing:**\n\n")

                f.write("| Theme | Tier | Quant | Fund | Composite | Recommendation |\n")
                f.write("|-------|------|-------|------|-----------|----------------|\n")

                for v in sorted(watchlist, key=lambda x: -x.composite_score):
                    f.write(f"| {v.theme_name} | {v.tier} | {v.quant_score:.0f} | {v.fund_score:.0f} | {v.composite_score:.0f} | {v.recommendation} |\n")

                f.write("\n")

            # Full Scoring Details
            f.write("## 📋 FULL SCORING DETAILS\n\n")

            for v in sorted(self.validations, key=lambda x: (x.tier, -x.composite_score)):
                status_emoji = "⚠️" if v.has_divergence else ("✅" if v.composite_score >= 55 else "👁️")
                f.write(f"### {status_emoji} {v.theme_name}\n\n")

                f.write(f"**Tier**: {v.tier} | **Category**: {v.fundamental_data.get('category', 'General')}\n\n")

                f.write("**Quantitative Metrics**:\n")
                f.write(f"- Fiedler Change: {v.fiedler_change:+.2f}\n")
                f.write(f"- Current Fiedler: {v.current_fiedler:.2f}\n")
                f.write(f"- Bull Regime: {v.bull_regime_pct:.1f}%\n")
                f.write(f"- Trend Strength: {v.trend_strength:+.3f}\n\n")

                f.write("**Scores**:\n")
                f.write(f"- Quant Score: {v.quant_score:.1f}/100\n")
                f.write(f"- Fund Score: {v.fund_score:.1f}/100\n")
                f.write(f"- Composite: {v.composite_score:.1f}/100")
                if v.has_divergence:
                    f.write(" (30% penalty applied)")
                f.write("\n\n")

                f.write(f"**Recommendation**: {v.recommendation}\n")
                f.write(f"**Action**: {v.action}\n\n")

                f.write("---\n\n")

            # Methodology
            f.write("## 📚 METHODOLOGY\n\n")
            f.write("### Scoring Formula\n\n")
            f.write("```\n")
            f.write("Quant Score = 0.30 × Fiedler_Change + 0.45 × Bull_Regime + 0.25 × Trend\n")
            f.write("Fund Score = Category_Base + Regime_Adj × Sensitivity + Trend_Adj × Sensitivity\n")
            f.write("Composite = (Quant × 0.5 + Fund × 0.5) × Divergence_Penalty\n")
            f.write("```\n\n")

            f.write("### Divergence Detection\n\n")
            f.write("- **Strong Divergence**: |Quant - Fund| > 30 → 30% composite penalty\n")
            f.write("- **Moderate Divergence**: |Quant - Fund| > 20 → Flagged for review\n")
            f.write("- **Aligned**: |Quant - Fund| ≤ 20 → No penalty\n\n")

            f.write("### Limitations\n\n")
            f.write("- Fund Score is currently **estimated** from price-based proxies\n")
            f.write("- For accurate fundamental validation, integrate:\n")
            f.write("  - FnGuide/DART for earnings data\n")
            f.write("  - FRED/BOK for macro indicators\n")
            f.write("  - News APIs for sentiment\n\n")

            f.write("---\n\n")
            f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        return report_file

    def print_summary(self):
        """Print summary to console"""

        print("=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        print()

        # Divergence alerts first
        divergent = [v for v in self.validations if v.has_divergence]
        if divergent:
            print("🚨 DIVERGENCE ALERTS:")
            print("-" * 60)
            for v in divergent:
                print(f"  ⚠️  {v.theme_name} (TIER {v.tier})")
                print(f"      Quant: {v.quant_score:.0f}  Fund: {v.fund_score:.0f}  Composite: {v.composite_score:.0f}")
                print(f"      Type: {v.divergence_type}")
                print(f"      → {v.action}")
                print()

        # Confirmed
        confirmed = [v for v in self.validations if not v.has_divergence and v.composite_score >= 55]
        if confirmed:
            print("✅ CONFIRMED THEMES:")
            print("-" * 60)
            for v in sorted(confirmed, key=lambda x: -x.composite_score):
                print(f"  ✅ {v.theme_name} (TIER {v.tier}) - Composite: {v.composite_score:.0f}")
            print()

        # Summary stats
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"  Total Validated: {len(self.validations)}")
        print(f"  Confirmed: {len(confirmed)}")
        print(f"  Divergent: {len(divergent)}")
        print(f"  Average Composite: {np.mean([v.composite_score for v in self.validations]):.1f}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='Fundamental Validation Layer for Sector Rotation Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate today's data
  python3 validate_fundamentals.py

  # Validate specific date
  python3 validate_fundamentals.py --date 20260109

  # Validate top 5 themes per tier
  python3 validate_fundamentals.py --top-themes 5
        """
    )
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: latest available)')
    parser.add_argument('--top-themes', type=int, default=10,
                       help='Number of top themes to validate per tier (default: 10)')

    args = parser.parse_args()

    # Determine date
    if args.date:
        date_str = args.date.replace('-', '')
    else:
        # Find latest 4tier_summary file
        files = list(DATA_DIR.glob("4tier_summary_*.json"))
        if files:
            date_str = sorted(files)[-1].stem.split('_')[-1]
        else:
            date_str = datetime.now().strftime('%Y%m%d')

    # Run validation
    validator = FundamentalValidator(date_str)

    try:
        validator.run_validation(top_n=args.top_themes)
        validator.print_summary()

        # Generate report
        report_file = validator.generate_report()
        print(f"\n✅ Validation report saved: {report_file}")

    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Please run the weekly analysis pipeline first:")
        print("   ./run_weekly_analysis.sh")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
