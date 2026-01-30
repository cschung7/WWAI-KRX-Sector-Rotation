#!/usr/bin/env python3
"""
Configuration file for Sector-Rotation-KRX project.
Allows project to be self-contained with configurable external dependencies.
"""

import os
from pathlib import Path

# Project root directory (parent of this config file)
PROJECT_ROOT = Path(__file__).parent

# Data directories (relative to project root)
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# External data dependencies (configurable via environment variables)
# Price data directory - can be overridden with KRX_PRICE_DATA_DIR env var
PRICE_DATA_DIR = Path(
    os.getenv("KRX_PRICE_DATA_DIR", "/mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED")
)

# AutoGluon base directory - can be overridden with AUTOGLUON_BASE_DIR env var
AUTOGLUON_BASE_DIR = Path(
    os.getenv("AUTOGLUON_BASE_DIR", "/mnt/nas/AutoGluon/AutoML_Krx")
)

# Database file path
DB_FILE = AUTOGLUON_BASE_DIR / "DB" / "db_final.csv"

# Regime results directory
REGIME_DIR = AUTOGLUON_BASE_DIR / "regime" / "results" / "regime_queries"

# Local data files (self-contained)
THEME_TO_TICKERS_FILE = DATA_DIR / "theme_to_tickers.json"
NAVER_THEME_ANALYSIS_FILE = DATA_DIR / "naver_theme_analysis.json"

# Default analysis parameters
START_DATE = "2025-01-01"
LOOKBACK_DAYS = 60
CORRELATION_THRESHOLD = 0.25
MIN_STOCKS = 3

# Print configuration on import (for debugging)
if __name__ == "__main__":
    print("=" * 80)
    print("SECTOR-ROTATION-KRX CONFIGURATION")
    print("=" * 80)
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Reports Directory: {REPORTS_DIR}")
    print(f"Logs Directory: {LOGS_DIR}")
    print(f"\nExternal Dependencies:")
    print(f"  Price Data: {PRICE_DATA_DIR} {'(EXISTS)' if PRICE_DATA_DIR.exists() else '(NOT FOUND)'}")
    print(f"  AutoGluon Base: {AUTOGLUON_BASE_DIR} {'(EXISTS)' if AUTOGLUON_BASE_DIR.exists() else '(NOT FOUND)'}")
    print(f"  DB File: {DB_FILE} {'(EXISTS)' if DB_FILE.exists() else '(NOT FOUND)'}")
    print(f"\nLocal Files:")
    print(f"  Theme Mapping: {THEME_TO_TICKERS_FILE} {'(EXISTS)' if THEME_TO_TICKERS_FILE.exists() else '(NOT FOUND)'}")
    print(f"  Naver Analysis: {NAVER_THEME_ANALYSIS_FILE} {'(EXISTS)' if NAVER_THEME_ANALYSIS_FILE.exists() else '(NOT FOUND)'}")
    print("=" * 80)
    print("\nTo override external paths, set environment variables:")
    print("  export KRX_PRICE_DATA_DIR=/path/to/price/data")
    print("  export AUTOGLUON_BASE_DIR=/path/to/autogluon")
    print("=" * 80)

