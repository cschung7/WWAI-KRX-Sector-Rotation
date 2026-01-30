#!/usr/bin/env python3
"""
Build theme-to-ticker mapping from Naver theme analysis data.

Input: naver_theme_analysis.json (ticker→themes mapping)
Output: theme_to_tickers.json (theme→tickers mapping)
"""

import json
from collections import defaultdict

# Use local copy for self-contained project
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "naver_theme_analysis.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "theme_to_tickers.json"

print("Loading Naver theme analysis...")
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

ticker_themes = data['ticker_themes']
print(f"Loaded {len(ticker_themes)} tickers")

# Build reverse mapping: theme → list of tickers
theme_to_tickers = defaultdict(list)

for ticker, ticker_data in ticker_themes.items():
    themes = ticker_data.get('themes', [])
    for theme in themes:
        theme_to_tickers[theme].append(ticker)

# Convert to regular dict
theme_to_tickers = dict(theme_to_tickers)

print(f"Built mappings for {len(theme_to_tickers)} themes")

# Save to JSON
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(theme_to_tickers, f, ensure_ascii=False, indent=2)

print(f"Saved to: {OUTPUT_FILE}")

# Print sample
print("\nSample themes:")
for i, (theme, tickers) in enumerate(list(theme_to_tickers.items())[:5]):
    print(f"  {theme}: {len(tickers)} stocks")
    print(f"    Sample: {tickers[:3]}")
