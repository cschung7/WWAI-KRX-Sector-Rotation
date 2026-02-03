#!/usr/bin/env python3
# Build: 20260203-v5-force-restart
"""
FastAPI Backend for Financial Market Dashboards

Provides REST API endpoints for:
1. Meta-Labeling Dashboard
2. Sector Rotation Dashboard
3. Portfolio Performance Dashboard
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backtest"))

from config import DATA_DIR, REPORTS_DIR, DB_FILE

# Try to import meta-labeling components
try:
    from backtest.meta_labeling_filter import MetaLabelingFilter
    HAS_META_LABELING = True
except ImportError:
    HAS_META_LABELING = False
    print("Warning: Meta-labeling not available")

app = FastAPI(
    title="Sector Rotation API",
    description="Financial market dashboards API",
    version="1.0.0"
)

# Database lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    # Debug: List actionable_tickers files
    import glob
    from config import DATA_DIR
    at_files = sorted(glob.glob(str(DATA_DIR / "actionable_tickers_*.csv")))
    print(f"[startup] DATA_DIR: {DATA_DIR}")
    print(f"[startup] actionable_tickers CSV files: {at_files}")
    cache_file = DATA_DIR / "dashboard_cache.json"
    print(f"[startup] dashboard_cache.json exists: {cache_file.exists()}")

    try:
        from db import init_db
        await init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Chat functionality may not work without database")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown"""
    try:
        from db import close_db
        await close_db()
        print("Database connections closed")
    except Exception as e:
        print(f"Warning: Error closing database: {e}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from routers import meta_labeling, sector_rotation, portfolio, breakout, network, chat
app.include_router(meta_labeling.router, prefix="/api/meta-labeling", tags=["Meta-Labeling"])
app.include_router(sector_rotation.router, prefix="/api/sector-rotation", tags=["Sector-Rotation"])
app.include_router(portfolio.router, prefix="/api/portfolio", tags=["Portfolio"])
app.include_router(breakout.router, prefix="/api/breakout", tags=["Breakout"])
app.include_router(network.router, prefix="/api/network", tags=["Network"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

# Frontend directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

@app.get("/")
async def root():
    """Serve main dashboard page with no-cache headers"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(
            index_file,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {
        "message": "Sector Rotation API",
        "version": "1.0.0",
        "endpoints": {
            "meta-labeling": "/api/meta-labeling",
            "sector-rotation": "/api/sector-rotation",
            "portfolio": "/api/portfolio"
        }
    }

@app.get("/theme-graph.html")
async def theme_graph():
    """Serve theme network graph page with no-cache headers"""
    return FileResponse(
        FRONTEND_DIR / "theme-graph.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/breakout.html")
async def breakout_page():
    """Serve breakout page"""
    return FileResponse(FRONTEND_DIR / "breakout.html")

@app.get("/index.html")
async def index_page():
    """Serve index page with no-cache headers"""
    return FileResponse(
        FRONTEND_DIR / "index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/signals.html")
async def signals_page():
    """Serve signals page"""
    file_path = FRONTEND_DIR / "signals.html"
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/cohesion.html")
async def cohesion_page():
    """Serve cohesion page"""
    file_path = FRONTEND_DIR / "cohesion.html"
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Page not found")

@app.get("/chat-widget.js")
async def chat_widget_js():
    """Serve chat widget JavaScript"""
    file_path = FRONTEND_DIR / "chat-widget.js"
    if file_path.exists():
        return FileResponse(file_path, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="Chat widget not found")

@app.get("/chat-test.html")
async def chat_test_page():
    """Serve chat test page"""
    file_path = FRONTEND_DIR / "chat-test.html"
    if file_path.exists():
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Test page not found")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "meta_labeling_available": HAS_META_LABELING,
        "build_id": "20260203-v4-debug-fix",
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

