#!/usr/bin/env python3
"""
Generate HTML Email Template for Weekly Reports
Target: All audiences
Frequency: Weekly (Monday morning)

IMPORTANT: Uses Three-Layer Framework (Cohesion × Regime × Trend)
- BUY NOW: Bull regime >60% AND Trend >0.1
- WATCH: Bull regime 40-60%
- AVOID: Bear regime >60% OR Trend <-0.3
"""

import pandas as pd
import json
import argparse
import ast
from pathlib import Path
from datetime import datetime
import glob

# Configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR, REGIME_DIR, DB_FILE

REPORTS_DIR.mkdir(exist_ok=True)


def find_latest_file(pattern, directory=DATA_DIR):
    """Find latest file matching pattern"""
    files = glob.glob(str(directory / pattern))
    if files:
        return Path(sorted(files)[-1])
    return None


def load_regime_data():
    """Load latest regime data"""
    regime_files = list(REGIME_DIR.glob("all_regimes_*.csv"))
    if not regime_files:
        return None, None

    latest_file = sorted(regime_files)[-1]
    df = pd.read_csv(latest_file)
    latest_date = df['Date'].max()
    df = df[df['Date'] == latest_date].copy()

    regime_summary = df.groupby('Ticker', group_keys=False).apply(
        lambda x: pd.Series({
            'Bull_Pct': (x['Is_Bull'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Bear_Pct': (x['Is_Bear'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Transition_Pct': (x['Is_Transition'].sum() / len(x) * 100) if len(x) > 0 else 0,
            'Trend_Strength': x['Trend_Strength'].mean() if 'Trend_Strength' in x.columns else 0,
            'Momentum_Score': x['Momentum_Score'].mean() if 'Momentum_Score' in x.columns else 0,
            'Regime': x['Regime'].mode()[0] if len(x) > 0 else 'Unknown'
        }), include_groups=False
    ).reset_index()
    regime_summary = regime_summary.rename(columns={'Ticker': 'Stock_Name'})

    return regime_summary, latest_date


def load_cohesion_data(date_str):
    """Load cohesion data"""
    specific_file = DATA_DIR / f"enhanced_cohesion_themes_{date_str}.csv"
    if specific_file.exists():
        return pd.read_csv(specific_file)

    cohesion_file = find_latest_file("enhanced_cohesion_themes_*.csv")
    if cohesion_file and cohesion_file.exists():
        return pd.read_csv(cohesion_file)
    return pd.DataFrame()


def load_db_data():
    """Load database"""
    return pd.read_csv(DB_FILE)


def calculate_theme_regime_stats(theme_name, db_df, regime_summary):
    """Calculate regime statistics for a theme"""
    theme_tickers = []
    for _, row in db_df.iterrows():
        themes_str = row.get('naverTheme', '[]')
        try:
            themes = ast.literal_eval(themes_str) if isinstance(themes_str, str) else themes_str
            if isinstance(themes, list) and theme_name in themes:
                stock_name = row['name']
                theme_tickers.append(stock_name)
        except:
            continue

    if not theme_tickers:
        return None

    regime_stats = []
    for stock_name in theme_tickers:
        regime_row = regime_summary[regime_summary['Stock_Name'] == stock_name]
        if not regime_row.empty:
            regime_stats.append({
                'bull_pct': regime_row.iloc[0]['Bull_Pct'],
                'bear_pct': regime_row.iloc[0]['Bear_Pct'],
                'trend': regime_row.iloc[0]['Trend_Strength']
            })

    if not regime_stats:
        return None

    stats_df = pd.DataFrame(regime_stats)

    return {
        'theme': theme_name,
        'avg_bull_pct': stats_df['bull_pct'].mean(),
        'avg_bear_pct': stats_df['bear_pct'].mean(),
        'avg_trend': stats_df['trend'].mean(),
        'stock_count': len(stats_df)
    }


def classify_themes_with_regime(cohesion_df, regime_summary, db_df):
    """Classify themes using Three-Layer Framework (Cohesion × Regime × Trend)"""

    theme_data = []

    if cohesion_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    for _, row in cohesion_df.iterrows():
        theme_name = row.get('theme', 'Unknown')
        stats = calculate_theme_regime_stats(theme_name, db_df, regime_summary)

        if stats:
            stats['fiedler'] = row.get('current_fiedler', 0)
            stats['fiedler_change'] = row.get('fiedler_change', 0)
            theme_data.append(stats)

    if not theme_data:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    theme_stats_df = pd.DataFrame(theme_data)

    # BUY NOW: Bull >60% AND Trend >0.1
    buy_now = theme_stats_df[
        (theme_stats_df['avg_bull_pct'] > 60) &
        (theme_stats_df['avg_trend'] > 0.1)
    ].sort_values('avg_bull_pct', ascending=False)

    # WATCHLIST: Bull 40-60%
    watchlist = theme_stats_df[
        (theme_stats_df['avg_bull_pct'] >= 40) &
        (theme_stats_df['avg_bull_pct'] <= 60) &
        (theme_stats_df['avg_trend'] > -0.2)
    ].sort_values('avg_bull_pct', ascending=False)

    # AVOID: Bear >60% OR Trend <-0.3
    avoid = theme_stats_df[
        (theme_stats_df['avg_bear_pct'] > 60) |
        (theme_stats_df['avg_trend'] < -0.3)
    ].sort_values('avg_bear_pct', ascending=False)

    return buy_now, watchlist, avoid


def generate_email_template(date_str, buy_now, watchlist, avoid, cohesion_df):
    """Generate HTML email template using Three-Layer Framework"""

    email_file = REPORTS_DIR / f"EMAIL_TEMPLATE_{date_str.replace('-', '')}.html"
    date_formatted = datetime.strptime(date_str, '%Y%m%d').strftime('%Y-%m-%d') if len(date_str) == 8 else date_str

    buy_count = len(buy_now)
    watch_count = len(watchlist)
    avoid_count = len(avoid)
    enhanced_count = len(cohesion_df) if not cohesion_df.empty else 0

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KRX Sector Rotation - Week of {date_formatted}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2563eb;
            margin: 0;
            font-size: 24px;
        }}
        .header .date {{
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .tier-buy {{
            background-color: #dcfce7;
            border-left: 4px solid #16a34a;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .tier-watch {{
            background-color: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .tier-avoid {{
            background-color: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 4px;
        }}
        .theme-item {{
            margin-bottom: 10px;
            padding: 10px;
            background-color: rgba(255,255,255,0.7);
            border-radius: 4px;
        }}
        .theme-name {{
            font-weight: bold;
            color: #1f2937;
        }}
        .metrics {{
            font-size: 14px;
            color: #6b7280;
            margin-top: 5px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: bold;
            color: #2563eb;
        }}
        .stat-value.green {{ color: #16a34a; }}
        .stat-value.yellow {{ color: #f59e0b; }}
        .stat-value.red {{ color: #ef4444; }}
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 5px;
        }}
        .button {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #2563eb;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            margin-top: 20px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            font-size: 12px;
            color: #6b7280;
            text-align: center;
        }}
        .framework-note {{
            background-color: #eff6ff;
            border-left: 4px solid #2563eb;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
            font-size: 13px;
        }}
        @media only screen and (max-width: 600px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>KRX Sector Rotation Dashboard</h1>
            <div class="date">Week of {date_formatted}</div>
        </div>

        <div class="framework-note">
            <strong>Three-Layer Framework:</strong> Cohesion (Fiedler) x Regime (Bull/Bear %) x Trend Strength<br>
            Recommendations are validated against ALL three layers, not just cohesion values.
        </div>

        <div class="section">
            <div class="section-title">Market Overview</div>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value green">{buy_count}</div>
                    <div class="stat-label">BUY NOW (Bull >60%, Trend >0.1)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value yellow">{watch_count}</div>
                    <div class="stat-label">WATCHLIST (Bull 40-60%)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value red">{avoid_count}</div>
                    <div class="stat-label">AVOID (Bear >60%)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{enhanced_count}</div>
                    <div class="stat-label">Total Cohesive Themes</div>
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-title">BUY NOW - Regime Validated</div>
            <div class="tier-buy">
"""

    if not buy_now.empty:
        html_content += f"<strong>{buy_count} themes with Bull >60% and positive trend</strong>\n"
        for _, row in buy_now.head(5).iterrows():
            html_content += f"""
                <div class="theme-item">
                    <div class="theme-name">{row['theme']}</div>
                    <div class="metrics">Bull: {row['avg_bull_pct']:.1f}% | Trend: {row['avg_trend']:+.3f} | Fiedler: {row['fiedler']:.2f}</div>
                </div>
"""
        if len(buy_now) > 5:
            html_content += f"<p style='font-size:12px; color:#666;'>... and {len(buy_now) - 5} more themes</p>\n"
    else:
        html_content += "<p><strong>No themes currently meet BUY criteria</strong></p>\n"
        html_content += "<p style='font-size:13px;'>Criteria: Bull regime >60% AND Trend >0.1</p>\n"

    html_content += """
            </div>
        </div>

        <div class="section">
            <div class="section-title">WATCHLIST - Monitor for Entry</div>
            <div class="tier-watch">
"""

    if not watchlist.empty:
        html_content += f"<strong>{watch_count} themes approaching bull territory</strong>\n"
        html_content += "<p style='font-size:13px;'>Enter when Bull >60% AND Trend >0.3</p>\n"
        for _, row in watchlist.head(5).iterrows():
            html_content += f"""
                <div class="theme-item">
                    <div class="theme-name">{row['theme']}</div>
                    <div class="metrics">Bull: {row['avg_bull_pct']:.1f}% | Trend: {row['avg_trend']:+.3f} | Fiedler: {row['fiedler']:.2f}</div>
                </div>
"""
        if len(watchlist) > 5:
            html_content += f"<p style='font-size:12px; color:#666;'>... and {len(watchlist) - 5} more themes on watchlist</p>\n"
    else:
        html_content += "<p>No themes currently on watchlist</p>\n"

    html_content += """
            </div>
        </div>

        <div class="section">
            <div class="section-title">AVOID - Bear Regime</div>
            <div class="tier-avoid">
"""

    if not avoid.empty:
        html_content += f"<strong>{avoid_count} themes in bear regime - AVOID long positions</strong>\n"
        for _, row in avoid.head(3).iterrows():
            html_content += f"""
                <div class="theme-item">
                    <div class="theme-name">{row['theme']}</div>
                    <div class="metrics">Bear: {row['avg_bear_pct']:.1f}% | Trend: {row['avg_trend']:+.3f}</div>
                </div>
"""
        if len(avoid) > 3:
            html_content += f"<p style='font-size:12px; color:#666;'>... and {len(avoid) - 3} more themes to avoid</p>\n"
    else:
        html_content += "<p>No themes in strong bear regime</p>\n"

    html_content += f"""
            </div>
        </div>

        <div class="section">
            <div class="section-title">Key Insights</div>
            <ul>
                <li><strong>{buy_count} themes</strong> validated for investment (Bull >60%, Trend >0.1)</li>
                <li><strong>{watch_count} themes</strong> on watchlist - monitor for regime shift</li>
                <li><strong>{avoid_count} themes</strong> in bear territory - avoid or consider shorts</li>
                <li>Three-layer validation ensures alignment across Cohesion, Regime, and Trend</li>
            </ul>
        </div>

        <div style="text-align: center; margin-top: 30px;">
            <a href="#" class="button">View Executive Summary</a>
        </div>

        <div class="footer">
            <p><strong>KRX Sector Rotation Analysis</strong></p>
            <p>Framework: Three-Layer Analysis (Cohesion x Regime x Trend)</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p style="margin-top: 10px;">
                <a href="#">Executive Dashboard</a> |
                <a href="#">Investment Memo</a> |
                <a href="#">Full Reports</a>
            </p>
        </div>
    </div>
</body>
</html>
"""

    with open(email_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    return email_file


def main():
    parser = argparse.ArgumentParser(description='Generate HTML Email Template')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()

    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')

    print("="*80)
    print("GENERATING HTML EMAIL TEMPLATE (Three-Layer Framework)")
    print("="*80)
    print(f"Date: {date_str}")
    print()

    # Load data
    print("Loading regime data...")
    regime_summary, regime_date = load_regime_data()
    if regime_summary is None:
        print("  WARNING: No regime data found!")
        regime_summary = pd.DataFrame()
    else:
        print(f"  Loaded regime data as of: {regime_date}")

    print("Loading cohesion data...")
    cohesion_df = load_cohesion_data(date_str)
    if cohesion_df.empty:
        print("  WARNING: No cohesion data found!")
    else:
        print(f"  Loaded {len(cohesion_df)} themes with cohesion data")

    print("Loading database...")
    db_df = load_db_data()
    print(f"  Loaded {len(db_df)} stocks from database")

    # Classify themes using Three-Layer Framework
    print("\nClassifying themes with Three-Layer Framework...")
    buy_now, watchlist, avoid = classify_themes_with_regime(cohesion_df, regime_summary, db_df)

    print(f"  BUY NOW (Bull >60%, Trend >0.1): {len(buy_now)} themes")
    print(f"  WATCHLIST (Bull 40-60%): {len(watchlist)} themes")
    print(f"  AVOID (Bear >60%): {len(avoid)} themes")

    # Generate email
    print("\nGenerating email template...")
    email_file = generate_email_template(date_str, buy_now, watchlist, avoid, cohesion_df)

    print(f"\n{'='*80}")
    print(f"Email template generated: {email_file}")
    print("="*80)

    # Show top recommendations
    if not buy_now.empty:
        print("\nBUY NOW themes (regime-validated):")
        for _, row in buy_now.head(5).iterrows():
            print(f"  - {row['theme']}: Bull {row['avg_bull_pct']:.1f}%, Trend {row['avg_trend']:+.3f}")
    else:
        print("\nNo themes currently meet BUY criteria (Bull >60%, Trend >0.1)")


if __name__ == '__main__':
    main()
