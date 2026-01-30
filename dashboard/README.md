# Financial Market Dashboards - FastAPI + React

## Overview

Three specialized financial market dashboards for sector rotation analysis:

1. **Sector Focus Dashboard** - Shows which sectors are focused and performance over time
2. **Portfolio Performance Dashboard** - Returns and performance tracking
3. **Investment Focus Dashboard** - Focused opportunities and performance overview

## Key Features

### 🔒 Privacy-Focused Design
- **No sensitive data exposed**: Fiedler values, detailed statistics, and internal metrics are hidden
- **Investor-friendly**: Only shows focused sectors and performance over time
- **Clean interface**: Simple, professional presentation

### 📊 What's Shown

**Sector Focus Dashboard:**
- Which sectors are in focus (Primary, Secondary, Research, Monitor)
- Performance over time chart
- List of all focused investment themes

**Portfolio Performance Dashboard:**
- Total return summary
- Performance status (positive/negative)
- Active positions count
- Performance over time (daily/weekly/monthly views)

**Investment Focus Dashboard:**
- Average return summary
- Active positions count
- Performance status
- Performance comparison chart

## Architecture

```
dashboard/
├── backend/                    # FastAPI backend
│   ├── main.py                # Main API server
│   ├── routers/               # API route handlers
│   └── requirements.txt       # Python dependencies
├── frontend/                   # HTML dashboards
│   ├── sector-rotation/       # Sector Focus Dashboard
│   ├── portfolio-performance/ # Portfolio Performance Dashboard
│   └── meta-labeling/         # Investment Focus Dashboard
└── README.md                   # This file
```

## Quick Start

### 1. Install Backend Dependencies

```bash
cd dashboard/backend
pip install -r requirements.txt
```

### 2. Start Backend

```bash
uvicorn main:app --reload --port 8000
```

### 3. Open Dashboards

Simply open the HTML files in your browser:

```bash
# Sector Focus Dashboard
open dashboard/frontend/sector-rotation/index.html

# Portfolio Performance Dashboard
open dashboard/frontend/portfolio-performance/index.html

# Investment Focus Dashboard
open dashboard/frontend/meta-labeling/index.html
```

Or use a simple HTTP server:

```bash
cd dashboard/frontend/sector-rotation
python3 -m http.server 3000
# Visit: http://localhost:3000/index.html
```

## Technology Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Charts**: Chart.js (CDN)
- **Styling**: Custom CSS (Dark theme)

## API Endpoints

The dashboards connect to the FastAPI backend at `http://localhost:8000`:

- `/api/sector-rotation/tier-classification` - Get focused sectors
- `/api/portfolio/performance` - Get performance metrics
- `/api/portfolio/returns-timeseries` - Get returns over time
- `/api/meta-labeling/performance` - Get filtered performance

## Security Notes

- All sensitive metrics (Fiedler values, Sharpe ratios, win rates) are hidden
- Only investor-facing information is displayed
- Performance data is shown in aggregate form only

## Documentation

See `QUICK_START.md` for detailed setup instructions.
