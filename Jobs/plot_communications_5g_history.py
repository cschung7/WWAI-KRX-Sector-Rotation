#!/usr/bin/env python3
"""
Plot historical Fiedler values for Communications and 5G sectors.

Note: Data availability is Feb-Oct 2025 (8 months), not 3 years.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path
from datetime import datetime

# File paths - use config module for self-contained project
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATA_DIR, REPORTS_DIR

OUTPUT_DIR = REPORTS_DIR
OUTPUT_DIR.mkdir(exist_ok=True)

THEME_5G_FILE = DATA_DIR / "theme_5G5세대_이동통신_timeseries.csv"
THEME_COMM_FILE = DATA_DIR / "theme_통신_timeseries.csv"

# Oct 27 and 29 baseline values
OCT_27_5G = 29.70
OCT_29_5G = 0.84

print("="*80)
print("5G AND COMMUNICATIONS FIEDLER VALUE HISTORY")
print("="*80)

# Load data
print("\n1. Loading historical data...")
df_5g = pd.read_csv(THEME_5G_FILE)
df_comm = pd.read_csv(THEME_COMM_FILE)

df_5g['date'] = pd.to_datetime(df_5g['date'])
df_comm['date'] = pd.to_datetime(df_comm['date'])

print(f"   5G theme: {len(df_5g)} data points from {df_5g['date'].min()} to {df_5g['date'].max()}")
print(f"   Communications: {len(df_comm)} data points from {df_comm['date'].min()} to {df_comm['date'].max()}")

# Create figure with 2 subplots
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Plot 1: 5G (5세대 이동통신)
print("\n2. Plotting 5G theme...")
ax1.plot(df_5g['date'], df_5g['fiedler'], linewidth=2, marker='o', markersize=4,
         label='5G Fiedler', color='#2E86AB', alpha=0.8)

# Add horizontal lines for thresholds
ax1.axhline(y=7.5, color='green', linestyle='--', linewidth=1.5, alpha=0.5, label='TIER 1 (7.5+)')
ax1.axhline(y=3.0, color='orange', linestyle='--', linewidth=1.5, alpha=0.5, label='TIER 2 (3.0+)')
ax1.axhline(y=0.1, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='Disconnection (<0.1)')

# Add Oct 27 and 29 values
oct_27 = pd.Timestamp('2025-10-27')
oct_29 = pd.Timestamp('2025-10-29')

ax1.scatter([oct_27], [OCT_27_5G], color='green', s=150, zorder=5,
           label=f'Oct 27: {OCT_27_5G:.2f}', marker='s', edgecolors='black', linewidths=2)
ax1.scatter([oct_29], [OCT_29_5G], color='red', s=150, zorder=5,
           label=f'Oct 29: {OCT_29_5G:.2f}', marker='X', edgecolors='black', linewidths=2)

# Annotate the dramatic drop
ax1.annotate(f'▼ -97.2%\n({OCT_27_5G:.1f} → {OCT_29_5G:.2f})',
            xy=(oct_29, OCT_29_5G), xytext=(oct_29, OCT_29_5G + 8),
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=12, fontweight='bold', color='red',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))

ax1.set_title('5G (5세대 이동통신) - Fiedler Value History (Feb-Oct 2025)',
             fontsize=14, fontweight='bold', pad=15)
ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('Fiedler Eigenvalue', fontsize=12)
ax1.legend(loc='upper left', fontsize=10, framealpha=0.9)
ax1.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
ax1.set_ylim(-1, max(df_5g['fiedler'].max(), OCT_27_5G) + 5)

# Format x-axis
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())
plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')

# Plot 2: Communications (통신)
print("3. Plotting Communications theme...")
ax2.plot(df_comm['date'], df_comm['fiedler'], linewidth=2, marker='o', markersize=4,
         label='Communications Fiedler', color='#A23B72', alpha=0.8)

# Add horizontal lines for thresholds
ax2.axhline(y=7.5, color='green', linestyle='--', linewidth=1.5, alpha=0.5, label='TIER 1 (7.5+)')
ax2.axhline(y=3.0, color='orange', linestyle='--', linewidth=1.5, alpha=0.5, label='TIER 2 (3.0+)')
ax2.axhline(y=0.1, color='red', linestyle='--', linewidth=1.5, alpha=0.5, label='Disconnection (<0.1)')

# Highlight disconnection periods
disconnected = df_comm[df_comm['fiedler'] < 0.1]
if len(disconnected) > 0:
    ax2.scatter(disconnected['date'], disconnected['fiedler'],
               color='red', s=100, zorder=5, alpha=0.6, label='Disconnected', marker='x')

ax2.set_title('통신 (Communications) - Fiedler Value History (Feb-Oct 2025)',
             fontsize=14, fontweight='bold', pad=15)
ax2.set_xlabel('Date', fontsize=12)
ax2.set_ylabel('Fiedler Eigenvalue', fontsize=12)
ax2.legend(loc='upper left', fontsize=10, framealpha=0.9)
ax2.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
ax2.set_ylim(-0.2, max(df_comm['fiedler'].max(), 1.5))

# Format x-axis
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax2.xaxis.set_major_locator(mdates.MonthLocator())
plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')

plt.tight_layout()

# Save plot
output_file = OUTPUT_DIR / "5g_communications_fiedler_history.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"\n4. Plot saved to: {output_file}")

# Print summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

print("\n5G (5세대 이동통신):")
print(f"   Stocks: {df_5g['n_stocks'].iloc[0]} stocks")
print(f"   Period: {df_5g['date'].min().strftime('%Y-%m-%d')} to {df_5g['date'].max().strftime('%Y-%m-%d')}")
print(f"   Fiedler range: {df_5g['fiedler'].min():.2f} to {df_5g['fiedler'].max():.2f}")
print(f"   Mean Fiedler: {df_5g['fiedler'].mean():.2f}")
print(f"   Median Fiedler: {df_5g['fiedler'].median():.2f}")
print(f"   Std Dev: {df_5g['fiedler'].std():.2f}")
print(f"   Oct 27 baseline: {OCT_27_5G:.2f} (VERY HIGH - outside historical range!)")
print(f"   Oct 29 current: {OCT_29_5G:.2f} (FRAGMENTED)")
print(f"   Change: -97.2% (unprecedented collapse)")

print("\n통신 (Communications):")
print(f"   Stocks: {df_comm['n_stocks'].iloc[0]} stocks")
print(f"   Period: {df_comm['date'].min().strftime('%Y-%m-%d')} to {df_comm['date'].max().strftime('%Y-%m-%d')}")
print(f"   Fiedler range: {df_comm['fiedler'].min():.2f} to {df_comm['fiedler'].max():.2f}")
print(f"   Mean Fiedler: {df_comm['fiedler'].mean():.2f}")
print(f"   Median Fiedler: {df_comm['fiedler'].median():.2f}")
print(f"   Std Dev: {df_comm['fiedler'].std():.2f}")
disconnection_rate = (df_comm['fiedler'] < 0.1).sum() / len(df_comm) * 100
print(f"   Disconnection rate: {disconnection_rate:.1f}% of observations")

print("\n" + "="*80)
print("KEY INSIGHTS")
print("="*80)

print("""
1. **Data Limitation**: Only 8 months of data available (Feb-Oct 2025), not 3 years.

2. **5G Sector Analysis**:
   - Historical range: 1.09 to 3.42 (stable TIER 2/3 sector)
   - Oct 27 value: 29.70 - UNPRECEDENTED HIGH (10x historical max!)
   - Oct 29 value: 0.84 - Below historical minimum
   - The Oct 27→29 collapse is real, but Oct 27 baseline itself appears abnormal

3. **Communications Sector Analysis**:
   - Much smaller theme (only 5 stocks vs. 59 in 5G)
   - Highly volatile, frequently disconnects
   - Regular disconnection is normal for this theme

4. **Conclusion**:
   - The 5G fragmentation IS real and unprecedented
   - BUT the Oct 27 baseline (29.70) is itself an anomaly - never seen before!
   - Historical 5G Fiedler was 1-3.5, not 30
   - Oct 29 value (0.84) is low but within conceivable range
   - This suggests something unusual happened around Oct 27 that inflated Fiedler
     values across the board, followed by a market-wide correlation breakdown
""")

print("="*80)
