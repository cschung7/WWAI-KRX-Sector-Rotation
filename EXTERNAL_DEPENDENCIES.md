# External Dependencies

This document lists all external dependencies required for the Sector-Rotation-KRX project to function.

## Required External Data

### 1. Price Data Directory
**Path**: `/mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED`  
**Purpose**: Contains CSV files with daily price data for Korean stocks  
**Format**: Each CSV file named `{stock_name}.csv` with columns: `Unnamed: 0` (Date), `close` (Close price)  
**Override**: Set environment variable `KRX_PRICE_DATA_DIR` to use a different location

```bash
export KRX_PRICE_DATA_DIR=/path/to/your/price/data
```

### 2. AutoGluon Database
**Path**: `/mnt/nas/AutoGluon/AutoML_Krx/DB/db_final.csv`  
**Purpose**: Contains stock metadata including Naver theme classifications  
**Override**: Set environment variable `AUTOGLUON_BASE_DIR` to use a different base directory

```bash
export AUTOGLUON_BASE_DIR=/path/to/autogluon
```

### 3. Regime Analysis Results
**Path**: `/mnt/nas/AutoGluon/AutoML_Krx/regime/results/regime_queries/`  
**Purpose**: Contains regime analysis results (bull/bear/transition probabilities)  
**Format**: CSV files with regime data by date

## Self-Contained Files

The following files are now included in the project's `data/` directory:

- `theme_to_tickers.json` - Theme to ticker mapping (generated from naver_theme_analysis.json)
- `naver_theme_analysis.json` - Source data for theme mappings (copied from external source)

## Configuration

All paths are configured in `config.py` and can be overridden via environment variables:

```python
# In config.py
PRICE_DATA_DIR = Path(os.getenv("KRX_PRICE_DATA_DIR", "/mnt/nas/AutoGluon/AutoML_Krx/KRXNOTTRAINED"))
AUTOGLUON_BASE_DIR = Path(os.getenv("AUTOGLUON_BASE_DIR", "/mnt/nas/AutoGluon/AutoML_Krx"))
```

## Verification

To check if all external dependencies are available, run:

```bash
python3 config.py
```

This will display the status of all external paths and local files.

## Notes

- The project is now **self-contained** for all internal data and scripts
- External dependencies are clearly documented and configurable
- All scripts use the `config.py` module for path management
- Local data files (theme mappings, analysis results) are stored in `data/` directory

