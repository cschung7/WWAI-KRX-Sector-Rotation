# Frontend Implementation Recommendations

## Overview

This document provides recommendations for implementing a frontend interface for the meta-labeling system.

## Recommended Approach: Web Dashboard

### Architecture

```
┌─────────────────┐
│  Frontend (UI)  │  React/Vue.js + Tailwind CSS
└────────┬────────┘
         │ REST API
┌────────▼────────┐
│  FastAPI Backend│  Python FastAPI
└────────┬────────┘
         │
┌────────▼────────┐
│ Meta-Labeling   │  Existing Python modules
│ System          │
└─────────────────┘
```

## Implementation Options

### Option 1: Streamlit Dashboard (Quickest)

**Pros:**
- Fastest to implement
- Python-only (no separate frontend)
- Built-in widgets and charts
- Good for internal use

**Cons:**
- Less customizable
- Not ideal for external users
- Limited real-time features

**Implementation:**

```python
# dashboard/meta_labeling_dashboard.py
import streamlit as st
import pandas as pd
from backtest.meta_labeling_filter import MetaLabelingFilter
from backtest.monitor_meta_labeling import compare_with_baseline

st.set_page_config(page_title="Meta-Labeling Dashboard", layout="wide")

st.title("🎯 Meta-Labeling System Dashboard")

# Sidebar
st.sidebar.header("Configuration")
model_path = st.sidebar.text_input("Model Path", "backtest/models/meta_labeler_xgboost_20251113")
use_meta_labeling = st.sidebar.checkbox("Enable Meta-Labeling", True)

# Main content
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Win Rate", "81.2%", "+13.5 pp")
with col2:
    st.metric("Avg Return", "19.93%", "+49.9%")
with col3:
    st.metric("Sharpe Ratio", "1.52", "+0.52")
with col4:
    st.metric("Signals", "11,633", "-25.6%")

# Performance chart
st.subheader("Performance Over Time")
# Add chart here

# Signal filtering
st.subheader("Filter Signals")
uploaded_file = st.file_uploader("Upload signals CSV")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if use_meta_labeling:
        filter_obj = MetaLabelingFilter(model_path=model_path)
        filtered_df = filter_obj.filter_dataframe(df)
        st.write(f"Filtered: {len(df)} → {len(filtered_df)} signals")
        st.dataframe(filtered_df)
```

### Option 2: FastAPI + React (Recommended for Production)

**Pros:**
- Professional, scalable
- Separates frontend/backend
- Real-time updates possible
- Good for external users

**Cons:**
- More complex setup
- Requires frontend development
- More maintenance

**Backend (FastAPI):**

```python
# api/meta_labeling_api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import pandas as pd

from backtest.meta_labeling_filter import MetaLabelingFilter
from backtest.monitor_meta_labeling import compare_with_baseline

app = FastAPI(title="Meta-Labeling API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

filter_obj = MetaLabelingFilter()

class Signal(BaseModel):
    theme: str
    signal_type: str
    signal_strength: float
    tier: int = None
    # ... other fields

class FilterRequest(BaseModel):
    signals: List[Signal]
    date: str

@app.post("/api/filter-signals")
async def filter_signals(request: FilterRequest):
    """Filter signals using meta-labeler"""
    try:
        signal_date = pd.to_datetime(request.date)
        signals_dict = [s.dict() for s in request.signals]
        filtered = filter_obj.filter_signals(signals_dict, signal_date)
        return {
            "success": True,
            "original_count": len(request.signals),
            "filtered_count": len(filtered),
            "reduction_pct": (1 - len(filtered) / len(request.signals)) * 100,
            "filtered_signals": filtered
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/performance")
async def get_performance():
    """Get current performance metrics"""
    # Load latest comparison results
    # Return metrics
    return {
        "win_rate_improvement": 13.5,
        "avg_return_improvement": 49.9,
        "sharpe_improvement": 0.52
    }

@app.get("/api/model-info")
async def get_model_info():
    """Get current model information"""
    return {
        "model_path": str(filter_obj.model_path),
        "model_type": filter_obj.meta_labeler.model_type if filter_obj.meta_labeler else None,
        "n_features": len(filter_obj.meta_labeler.feature_names) if filter_obj.meta_labeler and filter_obj.meta_labeler.feature_names else 0
    }
```

**Frontend (React):**

```jsx
// src/components/MetaLabelingDashboard.jsx
import React, { useState, useEffect } from 'react';
import { Card, Metric, LineChart } from '@tremor/react';

function MetaLabelingDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    fetch('/api/performance')
      .then(res => res.json())
      .then(data => setMetrics(data));
    
    fetch('/api/model-info')
      .then(res => res.json())
      .then(data => setModelInfo(data));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Meta-Labeling Dashboard</h1>
      
      <div className="grid grid-cols-4 gap-4 mb-6">
        <Card>
          <Metric title="Win Rate Improvement" value={`+${metrics?.win_rate_improvement || 0} pp`} />
        </Card>
        <Card>
          <Metric title="Return Improvement" value={`+${metrics?.avg_return_improvement || 0}%`} />
        </Card>
        <Card>
          <Metric title="Sharpe Improvement" value={`+${metrics?.sharpe_improvement || 0}`} />
        </Card>
        <Card>
          <Metric title="Model Type" value={modelInfo?.model_type || 'N/A'} />
        </Card>
      </div>
      
      {/* Add more components */}
    </div>
  );
}
```

### Option 3: Jupyter Notebook Dashboard

**Pros:**
- Easy for data scientists
- Interactive visualizations
- Can combine with analysis

**Cons:**
- Not suitable for production
- Requires Jupyter environment

**Implementation:**

```python
# dashboard/meta_labeling_notebook.ipynb
import ipywidgets as widgets
from IPython.display import display
from backtest.meta_labeling_filter import MetaLabelingFilter

# Create widgets
model_path_widget = widgets.Text(value="backtest/models/meta_labeler_xgboost_20251113")
filter_button = widgets.Button(description="Filter Signals")

def on_filter_click(b):
    filter_obj = MetaLabelingFilter(model_path=model_path_widget.value)
    # Filter and display results
    display("Filtering complete!")

filter_button.on_click(on_filter_click)
display(model_path_widget, filter_button)
```

## Recommended Features

### 1. Performance Dashboard
- Real-time metrics (win rate, returns, Sharpe)
- Historical performance charts
- Comparison with baseline

### 2. Signal Filtering Interface
- Upload signals CSV
- Filter in real-time
- Download filtered results
- Preview before/after

### 3. Model Management
- View current model info
- Upload new model
- Compare model versions
- Retrain model (trigger)

### 4. Monitoring & Alerts
- Performance trends
- Alert thresholds
- Automated notifications
- Performance history

### 5. Configuration
- Enable/disable meta-labeling
- Select model version
- Configure feature set
- Set filtering thresholds

## Implementation Priority

### Phase 1: Basic Dashboard (Week 1)
- Simple Streamlit dashboard
- View metrics
- Filter signals (upload CSV)
- Download results

### Phase 2: API Backend (Week 2)
- FastAPI endpoints
- REST API for filtering
- Performance endpoints
- Model management

### Phase 3: Full Frontend (Week 3-4)
- React/Vue frontend
- Real-time updates
- Advanced visualizations
- User management

## Quick Start: Streamlit Dashboard

```bash
# Install Streamlit
pip install streamlit

# Create dashboard
cat > dashboard/meta_labeling_dashboard.py << 'EOF'
import streamlit as st
# ... (code from Option 1 above)
EOF

# Run dashboard
streamlit run dashboard/meta_labeling_dashboard.py
```

Access at: `http://localhost:8501`

## Technology Stack Recommendations

### Backend
- **FastAPI**: Modern, fast, async Python framework
- **Pydantic**: Data validation
- **SQLite/PostgreSQL**: Store performance history

### Frontend
- **React** or **Vue.js**: Modern UI framework
- **Tailwind CSS**: Styling
- **Chart.js** or **Recharts**: Visualizations
- **Axios**: API calls

### Deployment
- **Docker**: Containerization
- **Nginx**: Reverse proxy
- **Gunicorn/Uvicorn**: ASGI server

## Example API Endpoints

```python
POST /api/filter-signals          # Filter signals
GET  /api/performance             # Get performance metrics
GET  /api/model-info               # Get model information
POST /api/retrain                  # Trigger model retraining
GET  /api/history                  # Get performance history
GET  /api/models                   # List available models
POST /api/models/upload            # Upload new model
```

## Security Considerations

1. **Authentication**: Add user authentication
2. **Rate Limiting**: Limit API calls
3. **Input Validation**: Validate all inputs
4. **Error Handling**: Don't expose internal errors
5. **Logging**: Log all operations

## Next Steps

1. **Choose Approach**: Streamlit (quick) or FastAPI+React (production)
2. **Implement MVP**: Basic dashboard with core features
3. **Test**: Validate with real data
4. **Deploy**: Set up production environment
5. **Iterate**: Add features based on feedback

