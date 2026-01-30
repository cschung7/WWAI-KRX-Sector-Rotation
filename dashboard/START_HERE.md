# Investment Focus Dashboard - Quick Start

## Overview

This is the **Investment Focus Dashboard** - a clean, investor-friendly interface showing:
- **Performance Overview**: Average return, active positions, performance status
- **Performance Over Time**: Interactive chart with daily/weekly/monthly views
- **Focused Investment Themes**: Primary and secondary focus sectors

## Quick Start

### 1. Start the Backend

```bash
cd dashboard/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Open the Dashboard

**Option A: Direct Open**
```bash
cd dashboard/frontend
open index.html
# or
xdg-open index.html
```

**Option B: HTTP Server (Recommended)**
```bash
cd dashboard/frontend
python3 -m http.server 3000
# Then visit: http://localhost:3000/index.html
```

## What You'll See

### Performance Summary Cards
- **Average Return**: Filtered portfolio performance percentage
- **Active Positions**: Number of focused opportunities
- **Performance Status**: Positive/Negative indicator

### Performance Chart
- Interactive line chart showing cumulative returns over time
- Toggle between Daily, Weekly, and Monthly views
- Color-coded (green for positive, red for negative)

### Focused Investment Themes
- Grid of all sectors currently in focus
- Shows Primary Focus and Secondary Focus themes
- Clean, card-based layout

## Features

✅ **Privacy-Focused**: No sensitive technical metrics exposed  
✅ **Investor-Friendly**: Simple, clear presentation  
✅ **Real-Time**: Connects to live backend API  
✅ **Responsive**: Works on desktop and mobile  
✅ **Dark Theme**: Professional appearance  

## API Endpoints Used

- `GET /api/meta-labeling/performance` - Performance metrics
- `GET /api/portfolio/returns-timeseries` - Returns over time
- `GET /api/sector-rotation/tier-classification` - Focused sectors

## Troubleshooting

**Dashboard not loading?**
- Check that backend is running: `curl http://localhost:8000/api/health`
- Check browser console for errors (F12)
- Ensure you're using HTTP server, not `file://` protocol

**No data showing?**
- Verify backend has access to data files
- Check that analysis has been run (weekly analysis script)
- Review backend logs for errors

**Charts not rendering?**
- Ensure internet connection (Chart.js loaded from CDN)
- Check browser console for JavaScript errors
- Try refreshing the page

## Next Steps

For production deployment:
1. Set up proper web server (nginx, Apache)
2. Configure HTTPS
3. Add authentication if needed
4. Set up automated data updates

