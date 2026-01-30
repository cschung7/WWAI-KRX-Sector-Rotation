# Quick Start Guide - HTML Dashboards

## Overview

Three standalone HTML dashboards that can be opened directly in your browser:

1. **Meta-Labeling Dashboard** - Signal filtering and performance monitoring
2. **Sector Rotation Dashboard** - Fiedler values and rotation signals
3. **Portfolio Performance Dashboard** - Returns, Sharpe, drawdown analysis

## Prerequisites

1. **FastAPI Backend Running**
   ```bash
   cd dashboard/backend
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```

2. **Web Browser** (Chrome, Firefox, Safari, Edge)

## Usage

### Option 1: Open Directly in Browser

Simply open the HTML files in your browser:

```bash
# Meta-Labeling Dashboard
open dashboard/frontend/meta-labeling/index.html
# or
xdg-open dashboard/frontend/meta-labeling/index.html

# Sector Rotation Dashboard
open dashboard/frontend/sector-rotation/index.html

# Portfolio Performance Dashboard
open dashboard/frontend/portfolio-performance/index.html
```

### Option 2: Simple HTTP Server

If you encounter CORS issues, use a simple HTTP server:

```bash
# Python 3
cd dashboard/frontend/meta-labeling
python3 -m http.server 3000

# Then open: http://localhost:3000/index.html
```

## Features

### Meta-Labeling Dashboard
- ✅ Real-time performance metrics
- ✅ Signal filtering interface
- ✅ Performance comparison charts
- ✅ Model status indicator

### Sector Rotation Dashboard
- ✅ 4-Tier investment classification
- ✅ Fiedler value time series
- ✅ Rotation signals (IN/OUT)
- ✅ Theme cohesion rankings

### Portfolio Performance Dashboard
- ✅ Performance metrics (win rate, returns, Sharpe)
- ✅ Cumulative returns chart
- ✅ Drawdown analysis
- ✅ Performance breakdown by signal type and tier

## API Endpoints Required

The dashboards connect to the FastAPI backend at `http://localhost:8000`:

- `/api/meta-labeling/*` - Meta-labeling endpoints
- `/api/sector-rotation/*` - Sector rotation endpoints
- `/api/portfolio/*` - Portfolio performance endpoints

## Troubleshooting

### CORS Errors
If you see CORS errors, make sure:
1. The FastAPI backend is running
2. CORS middleware is enabled (already configured in `main.py`)
3. You're accessing via HTTP server, not `file://`

### No Data Showing
1. Check browser console for errors (F12)
2. Verify backend is running: `curl http://localhost:8000/api/health`
3. Check that data files exist in the expected locations

### Charts Not Rendering
1. Ensure internet connection (Chart.js loaded from CDN)
2. Check browser console for JavaScript errors
3. Try refreshing the page

## Next Steps

For production deployment:
1. Build React versions for better performance
2. Set up proper authentication
3. Deploy to web server (nginx, Apache)
4. Configure HTTPS

