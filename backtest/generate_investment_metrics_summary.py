#!/usr/bin/env python3
"""
Generate Investment Metrics Summary

Creates a comprehensive investment metrics summary for portfolio themes
"""

import argparse
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DB_FILE

# Add backtest directory to path
backtest_dir = Path(__file__).parent
sys.path.insert(0, str(backtest_dir))

def calculate_investment_score(theme):
    """Calculate composite investment score (0-100)"""
    score = 0
    
    # Tier priority (40 points max)
    if theme['tier'] == 1:
        score += 40
    elif theme['tier'] == 2:
        score += 25
    else:
        score += 10
    
    # Signal strength (20 points max)
    score += min(theme['signal_strength'] / 3.0 * 20, 20)
    
    # Regime metrics (30 points max)
    if 'regime_avg_bull_pct' in theme and theme.get('regime_avg_bull_pct') is not None:
        bull_pct = theme['regime_avg_bull_pct']
        score += min(bull_pct / 100 * 15, 15)  # Up to 15 points for bull %
        
        trend = theme.get('regime_avg_trend') or 0
        if trend is not None and trend > 0:
            score += min(trend / 1.0 * 10, 10)  # Up to 10 points for positive trend
        
        momentum = theme.get('regime_avg_momentum') or 0
        if momentum is not None and momentum > 0:
            score += min(momentum / 1.0 * 5, 5)  # Up to 5 points for momentum
    
    # Fiedler change bonus (10 points max)
    if theme.get('fiedler_change'):
        if theme['fiedler_change'] > 2.0:
            score += 10
        elif theme['fiedler_change'] > 1.5:
            score += 5
    
    return min(score, 100)

def categorize_risk_level(theme):
    """Categorize risk level based on metrics"""
    risk_factors = 0
    
    # Low bull % = higher risk
    if 'regime_avg_bull_pct' in theme:
        if theme['regime_avg_bull_pct'] < 30:
            risk_factors += 2
        elif theme['regime_avg_bull_pct'] < 40:
            risk_factors += 1
    
    # Negative trend = higher risk
    trend = theme.get('regime_avg_trend')
    if trend is not None and trend < 0:
        risk_factors += 1
    
    # Low momentum = higher risk
    momentum = theme.get('regime_avg_momentum')
    if momentum is not None and momentum < 0.3:
        risk_factors += 1
    
    # Not valid at week 7 = higher risk (can't deploy full position)
    if not theme.get('valid_at_week7', False):
        risk_factors += 1
    
    if risk_factors <= 1:
        return "LOW"
    elif risk_factors <= 3:
        return "MEDIUM"
    else:
        return "HIGH"

def categorize_investment_horizon(theme):
    """Categorize recommended investment horizon"""
    if theme['tier'] == 1:
        return "IMMEDIATE (0-3 months)"
    elif theme['tier'] == 2:
        return "SHORT-TERM (3-6 months)"
    else:
        return "MEDIUM-TERM (6-12 months)"

def generate_investment_metrics_summary(portfolio_file, output_file=None):
    """Generate investment metrics summary from portfolio report"""
    
    if not Path(portfolio_file).exists():
        print(f"Error: Portfolio file not found: {portfolio_file}")
        return None
    
    # Parse portfolio report
    with open(portfolio_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract themes from the report
    themes = []
    lines = content.split('\n')
    
    in_table = False
    for line in lines:
        if '## Focused Portfolio Themes' in line:
            in_table = True
            continue
        if in_table and line.strip().startswith('---') and '##' not in line:
            break
        if in_table and '|' in line and 'Rank' not in line and line.strip():
            parts = [p.strip() for p in line.split('|')]
            
            # Skip separator lines (all dashes or empty)
            is_separator = True
            for p in parts[1:-1] if len(parts) > 2 else parts[1:]:
                if p and not all(c in '-: ' for c in p):
                    is_separator = False
                    break
            if is_separator:
                continue
            
            # Markdown tables: | col1 | col2 | col3 |
            # After split: ['', 'col1', 'col2', 'col3', '']
            # So parts[1] is first column
            if len(parts) >= 8:
                try:
                    # Rank is at index 1 (first column after empty start)
                    rank = int(parts[1])
                    theme_name = parts[2]
                    sig_type = parts[3]
                    tier_str = parts[4]
                    strength = float(parts[5])
                    
                    # Parse tier
                    tier = None
                    if 'TIER 1' in tier_str:
                        tier = 1
                    elif 'TIER 2' in tier_str:
                        tier = 2
                    
                    # Parse regime metrics if available (check if table has regime columns)
                    bull_pct = None
                    trend = None
                    momentum = None
                    valid_w7 = False
                    n_tickers = 0
                    
                    # Check table format - if has Bull % column (at index 6)
                    if len(parts) >= 11 and '%' in parts[6]:
                        # Format: | Rank | Theme | Type | Tier | Strength | Bull % | Trend | Momentum | Valid W7 | Tickers |
                        # Index:    1      2       3      4      5          6        7       8          9         10
                        bull_pct_str = parts[6].replace('%', '').strip()
                        if bull_pct_str != '-':
                            try:
                                bull_pct = float(bull_pct_str)
                            except:
                                pass
                        
                        trend_str = parts[7].strip()
                        if trend_str != '-' and trend_str.lower() != 'nan':
                            try:
                                trend = float(trend_str)
                            except:
                                pass
                        
                        momentum_str = parts[8].strip()
                        if momentum_str != '-' and momentum_str.lower() != 'nan':
                            try:
                                momentum = float(momentum_str)
                            except:
                                pass
                        
                        valid_w7 = '✅' in parts[9]
                        n_tickers = int(parts[10])
                    else:
                        # Format: | Rank | Theme | Type | Tier | Strength | Valid W7 | Tickers |
                        # Index:    1      2       3      4      5          6           7
                        valid_w7 = '✅' in parts[6] if len(parts) > 6 else False
                        n_tickers = int(parts[7])
                    
                    themes.append({
                        'rank': rank,
                        'theme': theme_name,
                        'signal_type': sig_type,
                        'tier': tier,
                        'signal_strength': strength,
                        'regime_avg_bull_pct': bull_pct,
                        'regime_avg_trend': trend,
                        'regime_avg_momentum': momentum,
                        'valid_at_week7': valid_w7,
                        'n_tickers': n_tickers
                    })
                except Exception as e:
                    continue
    
    # Extract additional details from detailed sections
    for theme in themes:
        theme_name = theme['theme']
        # Find detailed section
        in_section = False
        for i, line in enumerate(lines):
            section_header = f"### {theme['rank']}. {theme_name}"
            if section_header in line:
                in_section = True
                continue
            if in_section and line.startswith('###'):
                break
            if in_section:
                if 'Fiedler Change' in line:
                    try:
                        # Extract change value (format: "**Fiedler Change**: 1.59 (58.1%)")
                        parts = line.split(':')
                        if len(parts) > 1:
                            change_str = parts[1].split('(')[0].strip()
                            theme['fiedler_change'] = float(change_str)
                    except:
                        pass
                if 'Leadership Gap' in line:
                    try:
                        # Extract gap value (format: "**Leadership Gap**: 10.5%")
                        parts = line.split(':')
                        if len(parts) > 1:
                            gap_str = parts[1].replace('%', '').strip()
                            theme['leadership_gap'] = float(gap_str)
                    except:
                        pass
    
    # Calculate investment metrics
    for theme in themes:
        theme['investment_score'] = calculate_investment_score(theme)
        theme['risk_level'] = categorize_risk_level(theme)
        theme['investment_horizon'] = categorize_investment_horizon(theme)
    
    # Sort by investment score
    themes.sort(key=lambda x: x['investment_score'], reverse=True)
    
    # Generate summary report
    if output_file is None:
        output_file = backtest_dir / "reports" / "investment_metrics_summary.md"
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Investment Metrics Summary\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Portfolio Date**: August 1, 2025\n")
        f.write(f"**Total Themes**: {len(themes)}\n\n")
        f.write("---\n\n")
        
        # Executive Summary
        f.write("## 📊 Executive Summary\n\n")
        
        if len(themes) == 0:
            print("Warning: No themes found in portfolio report")
            return None
        
        tier1_count = sum(1 for t in themes if t['tier'] == 1)
        tier2_count = sum(1 for t in themes if t['tier'] == 2)
        
        bull_pcts = [t.get('regime_avg_bull_pct', 0) or 0 for t in themes if t.get('regime_avg_bull_pct')]
        avg_bull_pct = sum(bull_pcts) / len(bull_pcts) if bull_pcts else 0
        
        avg_score = sum(t['investment_score'] for t in themes) / len(themes)
        
        f.write(f"- **TIER 1 Themes**: {tier1_count} (Immediate Investment)\n")
        f.write(f"- **TIER 2 Themes**: {tier2_count} (Short-term Accumulation)\n")
        f.write(f"- **Average Bull Regime %**: {avg_bull_pct:.1f}%\n")
        f.write(f"- **Average Investment Score**: {avg_score:.1f}/100\n")
        f.write(f"- **Themes with Positive Momentum**: {sum(1 for t in themes if t.get('regime_avg_momentum', 0) and t['regime_avg_momentum'] > 0)}\n")
        f.write(f"- **Themes with Positive Trend**: {sum(1 for t in themes if t.get('regime_avg_trend', 0) and t['regime_avg_trend'] > 0)}\n\n")
        
        f.write("---\n\n")
        
        # Investment Metrics Table
        f.write("## 📈 Investment Metrics by Theme\n\n")
        f.write("| Rank | Theme | Tier | Score | Risk | Bull % | Trend | Momentum | Horizon | Valid W7 |\n")
        f.write("|------|-------|------|-------|------|--------|-------|----------|---------|----------|\n")
        
        for theme in themes:
            tier_str = f"TIER {theme['tier']}" if theme['tier'] else "-"
            bull_str = f"{theme['regime_avg_bull_pct']:.1f}%" if theme.get('regime_avg_bull_pct') else "-"
            trend_str = f"{theme['regime_avg_trend']:.2f}" if theme.get('regime_avg_trend') is not None else "-"
            momentum_str = f"{theme['regime_avg_momentum']:.2f}" if theme.get('regime_avg_momentum') is not None else "-"
            valid_str = "✅" if theme['valid_at_week7'] else "❌"
            
            f.write(f"| {theme['rank']} | {theme['theme'][:25]} | {tier_str} | "
                   f"{theme['investment_score']:.0f} | {theme['risk_level']} | {bull_str} | "
                   f"{trend_str} | {momentum_str} | {theme['investment_horizon'][:15]} | {valid_str} |\n")
        
        f.write("\n---\n\n")
        
        # Detailed Analysis
        f.write("## 🔍 Detailed Investment Analysis\n\n")
        
        for theme in themes:
            f.write(f"### {theme['rank']}. {theme['theme']}\n\n")
            
            # Investment Score Breakdown
            f.write(f"**Investment Score**: {theme['investment_score']:.0f}/100\n\n")
            f.write("**Score Components**:\n")
            f.write(f"- Tier Priority: {40 if theme['tier'] == 1 else (25 if theme['tier'] == 2 else 10)}/40\n")
            f.write(f"- Signal Strength: {min(theme['signal_strength'] / 3.0 * 20, 20):.0f}/20\n")
            if theme.get('regime_avg_bull_pct') is not None:
                regime_score = min(theme['regime_avg_bull_pct'] / 100 * 15, 15)
                trend = theme.get('regime_avg_trend') or 0
                trend_score = min(max(trend, 0) / 1.0 * 10, 10) if trend is not None and trend > 0 else 0
                momentum = theme.get('regime_avg_momentum') or 0
                momentum_score = min(max(momentum, 0) / 1.0 * 5, 5) if momentum is not None and momentum > 0 else 0
                f.write(f"- Regime Metrics: {regime_score + trend_score + momentum_score:.0f}/30\n")
            f.write(f"- Fiedler Change Bonus: {10 if theme.get('fiedler_change', 0) > 2.0 else (5 if theme.get('fiedler_change', 0) > 1.5 else 0)}/10\n\n")
            
            # Risk Assessment
            f.write(f"**Risk Level**: {theme['risk_level']}\n\n")
            f.write("**Risk Factors**:\n")
            bull_pct = theme.get('regime_avg_bull_pct')
            if bull_pct is not None and bull_pct < 30:
                f.write(f"- ⚠️ Low Bull Regime ({bull_pct:.1f}%)\n")
            trend = theme.get('regime_avg_trend')
            if trend is not None and trend < 0:
                f.write(f"- ⚠️ Negative Trend ({trend:.2f})\n")
            momentum = theme.get('regime_avg_momentum')
            if momentum is not None and momentum < 0.3:
                f.write(f"- ⚠️ Low Momentum ({momentum:.2f})\n")
            if not theme['valid_at_week7']:
                f.write("- ⚠️ Signal not valid at Week 7 (limited position size)\n")
            bull_pct = theme.get('regime_avg_bull_pct')
            trend = theme.get('regime_avg_trend')
            momentum = theme.get('regime_avg_momentum')
            has_risk = (
                (bull_pct is not None and bull_pct < 30) or
                (trend is not None and trend < 0) or
                (momentum is not None and momentum < 0.3) or
                not theme['valid_at_week7']
            )
            if not has_risk:
                f.write("- ✅ Low risk profile\n")
            f.write("\n")
            
            # Investment Recommendation
            f.write(f"**Investment Horizon**: {theme['investment_horizon']}\n\n")
            
            if theme['investment_score'] >= 70:
                recommendation = "**STRONG BUY** - High confidence investment"
            elif theme['investment_score'] >= 50:
                recommendation = "**BUY** - Moderate confidence investment"
            elif theme['investment_score'] >= 30:
                recommendation = "**ACCUMULATE** - Lower confidence, gradual entry"
            else:
                recommendation = "**MONITOR** - Wait for stronger signals"
            
            f.write(f"**Recommendation**: {recommendation}\n\n")
            
            # Key Metrics
            f.write("**Key Metrics**:\n")
            f.write(f"- Signal Type: {theme['signal_type']}\n")
            f.write(f"- Signal Strength: {theme['signal_strength']:.2f}/3.00\n")
            if theme.get('regime_avg_bull_pct'):
                f.write(f"- Bull Regime %: {theme['regime_avg_bull_pct']:.1f}%\n")
            if theme.get('regime_avg_trend') is not None:
                f.write(f"- Trend Strength: {theme['regime_avg_trend']:.3f}\n")
            if theme.get('regime_avg_momentum') is not None:
                f.write(f"- Momentum Score: {theme['regime_avg_momentum']:.3f}\n")
            if theme.get('fiedler_change'):
                f.write(f"- Fiedler Change: {theme['fiedler_change']:.2f}\n")
            if theme.get('leadership_gap'):
                f.write(f"- Leadership Gap: {theme['leadership_gap']:.1f}%\n")
            f.write(f"- Number of Tickers: {theme['n_tickers']}\n")
            f.write(f"- Week 7 Validity: {'✅ Yes' if theme['valid_at_week7'] else '❌ No'}\n\n")
            
            f.write("---\n\n")
        
        # Portfolio Allocation Recommendations
        f.write("## 💼 Portfolio Allocation Recommendations\n\n")
        f.write("Based on investment scores and risk levels:\n\n")
        
        strong_buy = [t for t in themes if t['investment_score'] >= 70]
        buy = [t for t in themes if 50 <= t['investment_score'] < 70]
        accumulate = [t for t in themes if 30 <= t['investment_score'] < 50]
        
        f.write(f"### Strong Buy ({len(strong_buy)} themes) - Allocate 40-50% of portfolio\n")
        for theme in strong_buy:
            f.write(f"- **{theme['theme']}** (Score: {theme['investment_score']:.0f}, Risk: {theme['risk_level']})\n")
        f.write("\n")
        
        f.write(f"### Buy ({len(buy)} themes) - Allocate 30-40% of portfolio\n")
        for theme in buy:
            f.write(f"- **{theme['theme']}** (Score: {theme['investment_score']:.0f}, Risk: {theme['risk_level']})\n")
        f.write("\n")
        
        f.write(f"### Accumulate ({len(accumulate)} themes) - Allocate 10-20% of portfolio\n")
        for theme in accumulate:
            f.write(f"- **{theme['theme']}** (Score: {theme['investment_score']:.0f}, Risk: {theme['risk_level']})\n")
        f.write("\n")
        
        f.write("---\n\n")
        f.write(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"Investment metrics summary saved: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate investment metrics summary')
    parser.add_argument('--portfolio', type=str, 
                       default='backtest/reports/focused_portfolio_20250801.md',
                       help='Path to portfolio report file')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path')
    
    args = parser.parse_args()
    
    generate_investment_metrics_summary(args.portfolio, args.output)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

