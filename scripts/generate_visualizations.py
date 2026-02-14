#!/usr/bin/env python3
"""
Generate Enhanced Visualizations for Reports
Creates charts and visual summaries
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import argparse
from pathlib import Path
from datetime import datetime
import glob
import json

# Configuration
import sys
sys.path.insert(0, str(Path(__file__).parent))
from config import DATA_DIR, REPORTS_DIR

REPORTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

# Set Korean font for matplotlib
def setup_korean_font():
    """Setup Korean font for matplotlib"""
    # Find Korean fonts by searching for Nanum fonts first
    korean_font_obj = None
    
    # Search for NanumGothic (preferred, not Coding version)
    for font_obj in fm.fontManager.ttflist:
        font_lower = font_obj.name.lower()
        if 'nanum' in font_lower and 'gothic' in font_lower and 'coding' not in font_lower:
            korean_font_obj = font_obj
            break
    
    # If no NanumGothic, try other Nanum fonts
    if not korean_font_obj:
        for font_obj in fm.fontManager.ttflist:
            font_lower = font_obj.name.lower()
            if 'nanum' in font_lower:
                korean_font_obj = font_obj
                break
    
    # If still not found, try other Korean fonts
    if not korean_font_obj:
        for font_obj in fm.fontManager.ttflist:
            font_lower = font_obj.name.lower()
            if any(kw in font_lower for kw in ['malgun', 'gulim', 'batang', 'gungsuh']):
                korean_font_obj = font_obj
                break
    
    if korean_font_obj:
        # Create FontProperties from font file path
        prop = fm.FontProperties(fname=korean_font_obj.fname)
        plt.rcParams['font.family'] = korean_font_obj.name
        plt.rcParams['font.sans-serif'] = [korean_font_obj.name] + plt.rcParams['font.sans-serif']
        print(f"  Using Korean font: {korean_font_obj.name}")
        return prop
    else:
        # Fallback
        plt.rcParams['font.family'] = 'DejaVu Sans'
        print(f"  Warning: Korean font not found, using DejaVu Sans (may not display Korean correctly)")
        return None

# Setup Korean font and get font properties
KOREAN_FONT_PROP = setup_korean_font()
plt.rcParams['axes.unicode_minus'] = False

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def find_latest_file(pattern, default_date=None):
    """Find latest file matching pattern"""
    files = glob.glob(str(DATA_DIR / pattern))
    if files:
        return Path(sorted(files)[-1])
    if default_date:
        return DATA_DIR / pattern.replace('*', default_date)
    return None

def load_cohesion_data(date_str):
    """Load cohesion data"""
    cohesion_file = find_latest_file(f"enhanced_cohesion_themes_*.csv", f"enhanced_cohesion_themes_{date_str}.csv")
    if cohesion_file and cohesion_file.exists():
        return pd.read_csv(cohesion_file)
    return pd.DataFrame()

def load_leadership_data():
    """Load leadership data"""
    leadership_file = DATA_DIR / "within_theme_leadership_ranking.csv"
    if leadership_file.exists():
        return pd.read_csv(leadership_file)
    return pd.DataFrame()

def create_fiedler_distribution_chart(cohesion_df, date_str):
    """Create Fiedler value distribution chart"""
    if cohesion_df.empty or 'current_fiedler' not in cohesion_df.columns:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create histogram
    cohesion_df['current_fiedler'].hist(bins=30, ax=ax, color='#2563eb', alpha=0.7, edgecolor='black')
    
    # Add vertical lines for thresholds
    ax.axvline(x=2.0, color='green', linestyle='--', linewidth=2, label='Very Strong (≥2.0)')
    ax.axvline(x=1.0, color='orange', linestyle='--', linewidth=2, label='Strong (≥1.0)')
    ax.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='Moderate (≥0.5)')
    
    ax.set_xlabel('Fiedler Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Themes', fontsize=12, fontweight='bold')
    ax.set_title('Distribution of Fiedler Values (Theme Cohesion)', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    output_file = REPORTS_DIR / f"fiedler_distribution_{date_str}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file

def create_leadership_gap_chart(leadership_df, date_str):
    """Create leadership gap chart"""
    if leadership_df.empty or 'Leadership_Gap' not in leadership_df.columns:
        return None
    
    # Parse percentage strings
    gaps = leadership_df['Leadership_Gap'].astype(str).str.replace('%', '').astype(float)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Sort and take top 20
    top_gaps = gaps.nlargest(20)
    top_themes = leadership_df.loc[top_gaps.index, 'Theme'].head(20)
    
    # Create horizontal bar chart
    colors = ['#16a34a' if g > 60 else '#f59e0b' if g > 40 else '#ef4444' for g in top_gaps]
    bars = ax.barh(range(len(top_gaps)), top_gaps.values, color=colors, alpha=0.7, edgecolor='black')
    
    # Customize
    ax.set_yticks(range(len(top_themes)))
    # Use Korean font for theme labels
    theme_labels = [t[:30] + '...' if len(t) > 30 else t for t in top_themes]
    if KOREAN_FONT_PROP:
        ax.set_yticklabels(theme_labels, fontsize=9, fontproperties=KOREAN_FONT_PROP)
    else:
        ax.set_yticklabels(theme_labels, fontsize=9)
    ax.set_xlabel('Leadership Gap (%)', fontsize=12, fontweight='bold')
    if KOREAN_FONT_PROP:
        ax.set_xlabel('Leadership Gap (%)', fontsize=12, fontweight='bold', fontproperties=KOREAN_FONT_PROP)
        ax.set_title('Top 20 Themes by Large-Cap Leadership Gap', fontsize=14, fontweight='bold', fontproperties=KOREAN_FONT_PROP)
    else:
        ax.set_xlabel('Leadership Gap (%)', fontsize=12, fontweight='bold')
        ax.set_title('Top 20 Themes by Large-Cap Leadership Gap', fontsize=14, fontweight='bold')
    ax.axvline(x=60, color='green', linestyle='--', linewidth=2, label='Extreme (>60%)')
    ax.axvline(x=40, color='orange', linestyle='--', linewidth=2, label='Strong (>40%)')
    if KOREAN_FONT_PROP:
        ax.legend(prop=KOREAN_FONT_PROP)
    else:
        ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    
    output_file = REPORTS_DIR / f"leadership_gap_{date_str}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file

def create_tier_composition_chart(summary, date_str):
    """Create tier composition pie chart"""
    if not summary:
        return None
    
    tier1_count = summary.get('tier1', {}).get('count', 0)
    tier2_count = summary.get('tier2', {}).get('count', 0)
    tier3_count = summary.get('tier3', {}).get('count', 0)
    tier4_count = summary.get('tier4', {}).get('count', 0)
    
    if tier1_count + tier2_count + tier3_count + tier4_count == 0:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    sizes = [tier1_count, tier2_count, tier3_count, tier4_count]
    labels = ['TIER 1\n(BUY NOW)', 'TIER 2\n(ACCUMULATE)', 'TIER 3\n(RESEARCH)', 'TIER 4\n(MONITOR)']
    colors = ['#16a34a', '#f59e0b', '#3b82f6', '#6b7280']
    explode = (0.1, 0, 0, 0)  # Explode TIER 1
    
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', shadow=True, startangle=90,
                                       textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    # Customize autopct
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax.set_title('Theme Distribution by Investment Tier', fontsize=14, fontweight='bold', pad=20)
    
    # Add legend with counts
    legend_labels = [f'{label} ({count})' for label, count in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    
    output_file = REPORTS_DIR / f"tier_composition_{date_str}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file

def create_fiedler_change_chart(cohesion_df, date_str):
    """Create Fiedler change scatter plot"""
    if cohesion_df.empty or 'fiedler_change' not in cohesion_df.columns or 'current_fiedler' not in cohesion_df.columns:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create scatter plot
    scatter = ax.scatter(cohesion_df['current_fiedler'], cohesion_df['fiedler_change'],
                        s=100, alpha=0.6, c=cohesion_df['current_fiedler'],
                        cmap='RdYlGn', edgecolors='black', linewidth=0.5)
    
    # Add quadrant lines
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1, alpha=0.3)
    ax.axvline(x=2.0, color='green', linestyle='--', linewidth=2, alpha=0.5)
    ax.axvline(x=1.0, color='orange', linestyle='--', linewidth=2, alpha=0.5)
    
    # Add quadrant labels
    ax.text(0.5, 2.5, 'Low Cohesion\nRising', fontsize=10, ha='center', 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax.text(3.0, 2.5, 'High Cohesion\nRising', fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    ax.text(0.5, -1.0, 'Low Cohesion\nFalling', fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
    ax.text(3.0, -1.0, 'High Cohesion\nFalling', fontsize=10, ha='center',
            bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
    
    ax.set_xlabel('Current Fiedler Value', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fiedler Change', fontsize=12, fontweight='bold')
    ax.set_title('Theme Cohesion: Current vs Change', fontsize=14, fontweight='bold')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Current Fiedler Value', fontsize=10)
    
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_file = REPORTS_DIR / f"fiedler_change_{date_str}.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_file

def load_4tier_summary(date_str):
    """Load 4-tier summary"""
    summary_file = DATA_DIR / f"4tier_summary_{date_str}.json"
    if not summary_file.exists():
        files = glob.glob(str(DATA_DIR / "4tier_summary_*.json"))
        if files:
            summary_file = Path(sorted(files)[-1])
        else:
            return None
    
    with open(summary_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description='Generate Visualizations')
    parser.add_argument('--date', type=str, default=None,
                       help='Date in YYYYMMDD format (default: today)')
    args = parser.parse_args()
    
    if args.date:
        date_str = args.date.replace('-', '')
    else:
        date_str = datetime.now().strftime('%Y%m%d')
    
    print("="*80)
    print("GENERATING VISUALIZATIONS")
    print("="*80)
    print(f"Date: {date_str}")
    print()
    
    # Load data
    print("Loading data...")
    cohesion_df = load_cohesion_data(date_str)
    leadership_df = load_leadership_data()
    summary = load_4tier_summary(date_str)
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    
    charts = []
    
    print("  [1/4] Fiedler distribution chart...")
    chart1 = create_fiedler_distribution_chart(cohesion_df, date_str)
    if chart1:
        charts.append(chart1)
        print(f"      ✓ {chart1.name}")
    
    print("  [2/4] Leadership gap chart...")
    chart2 = create_leadership_gap_chart(leadership_df, date_str)
    if chart2:
        charts.append(chart2)
        print(f"      ✓ {chart2.name}")
    
    print("  [3/4] Tier composition chart...")
    chart3 = create_tier_composition_chart(summary, date_str)
    if chart3:
        charts.append(chart3)
        print(f"      ✓ {chart3.name}")
    
    print("  [4/4] Fiedler change scatter plot...")
    chart4 = create_fiedler_change_chart(cohesion_df, date_str)
    if chart4:
        charts.append(chart4)
        print(f"      ✓ {chart4.name}")
    
    print(f"\n✅ Generated {len(charts)} visualizations")
    print("="*80)
    
    return charts

if __name__ == '__main__':
    main()

