"""
Theme Network Graph API Endpoints
Integrates NaverTheme data with Fiedler co-movement analysis
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import ast
import sys
from pathlib import Path
import glob
import re

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from config import DATA_DIR

router = APIRouter()

# Data paths
NAVER_THEME_CSV = Path("/mnt/nas/WWAI/NaverTheme/webapp/backend/data/db_final.csv")
FIEDLER_WEEKLY_CSV = DATA_DIR / "naver_themes_weekly_fiedler_2025.csv"
SIGNAL_PROB_DIR = Path("/mnt/nas/AutoGluon/AutoML_Krx/predictedProbability")

# Cache for performance
_theme_cache = None
_fiedler_cache = None
_signal_prob_cache = {}
_all_themes_cache = None


def load_theme_data():
    """Load and cache NaverTheme data"""
    global _theme_cache
    if _theme_cache is None:
        if not NAVER_THEME_CSV.exists():
            raise HTTPException(status_code=404, detail="NaverTheme data not found")
        _theme_cache = pd.read_csv(NAVER_THEME_CSV)
    return _theme_cache


def load_fiedler_data():
    """Load and cache Fiedler data"""
    global _fiedler_cache
    if _fiedler_cache is None:
        if FIEDLER_WEEKLY_CSV.exists():
            df = pd.read_csv(FIEDLER_WEEKLY_CSV)
            df['date'] = pd.to_datetime(df['date'])
            # Get latest data for each theme
            latest_date = df['date'].max()
            _fiedler_cache = df[df['date'] == latest_date].set_index('theme')
    return _fiedler_cache


def get_signal_probability(stock_name: str) -> dict:
    """Load signal probability for a stock (cached)"""
    global _signal_prob_cache

    if stock_name in _signal_prob_cache:
        return _signal_prob_cache[stock_name]

    # Default values
    result = {"buy": 0.0, "neutral": 0.0, "sell": 0.0}

    try:
        file_path = SIGNAL_PROB_DIR / f"{stock_name}_pp.csv"
        if file_path.exists():
            df = pd.read_csv(file_path)
            if len(df) > 0:
                # Get last row (most recent)
                last_row = df.iloc[-1]
                result = {
                    "sell": float(last_row.get('-1', 0)) * 100,
                    "neutral": float(last_row.get('0', 0)) * 100,
                    "buy": float(last_row.get('1', 0)) * 100
                }
        _signal_prob_cache[stock_name] = result
    except Exception as e:
        pass

    return result


def get_all_themes():
    """Get all unique themes (cached)"""
    global _all_themes_cache
    if _all_themes_cache is None:
        df = load_theme_data()
        all_themes = set()
        for themes_str in df['naverTheme'].dropna():
            all_themes.update(parse_themes(themes_str))
        _all_themes_cache = sorted(list(all_themes))
    return _all_themes_cache


def fuzzy_match(query: str, text: str) -> bool:
    """Check if query matches text with partial/fuzzy matching"""
    query = query.lower().strip()
    text = text.lower()

    # Direct contains match
    if query in text:
        return True

    # Split query into words and check if all words are in text
    words = query.split()
    if len(words) > 1:
        return all(word in text for word in words)

    # Check for partial word match (at least 2 chars)
    if len(query) >= 2:
        # Remove common suffixes/prefixes for matching
        for word in text.split():
            if query in word or word in query:
                return True

    return False


def parse_themes(themes_str):
    """Parse theme list from string representation"""
    if pd.isna(themes_str) or themes_str == '[]':
        return []
    try:
        return ast.literal_eval(themes_str)
    except:
        return []


def safe_float(val, default=0.0):
    """Convert to float, handling NaN"""
    if pd.isna(val):
        return default
    try:
        return float(val)
    except:
        return default


@router.get("/stock-themes")
async def get_stock_themes(
    name: str = Query(..., description="Stock name (e.g., 삼성전자)")
):
    """Get themes for a specific stock"""
    try:
        df = load_theme_data()
        fiedler_df = load_fiedler_data()

        # Find stock
        stock_data = df[df['name'] == name]
        if len(stock_data) == 0:
            # Try partial match
            stock_data = df[df['name'].str.contains(name, na=False)]

        if len(stock_data) == 0:
            raise HTTPException(status_code=404, detail=f"Stock not found: {name}")

        row = stock_data.iloc[0]
        themes = parse_themes(row.get('naverTheme', '[]'))

        # Get Fiedler scores for themes
        theme_details = []
        for theme in themes:
            detail = {
                "theme": theme,
                "fiedler": 0.0,
                "cohesion_level": "unknown"
            }
            if fiedler_df is not None and theme in fiedler_df.index:
                fiedler_val = safe_float(fiedler_df.loc[theme, 'fiedler'])
                detail["fiedler"] = round(fiedler_val, 3)
                if fiedler_val > 3.0:
                    detail["cohesion_level"] = "very_strong"
                elif fiedler_val >= 1.0:
                    detail["cohesion_level"] = "strong"
                elif fiedler_val >= 0.5:
                    detail["cohesion_level"] = "moderate"
                else:
                    detail["cohesion_level"] = "weak"
            theme_details.append(detail)

        # Sort by Fiedler
        theme_details.sort(key=lambda x: x['fiedler'], reverse=True)

        return {
            "success": True,
            "stock_name": row['name'],
            "ticker": str(row.get('tickers', '')),
            "market": row.get('market', ''),
            "themes": theme_details,
            "theme_count": len(themes),
            "scores": {
                "bearish": safe_float(row.get('-1', 0)),
                "neutral": safe_float(row.get('0', 0)),
                "bullish": safe_float(row.get('1', 0))
            },
            "momentum": row.get('mmt', '')
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/theme-stocks")
async def get_theme_stocks(
    theme: str = Query(..., description="Theme name (e.g., 반도체)"),
    limit: int = Query(20, description="Max stocks to return")
):
    """Get stocks belonging to a theme"""
    try:
        df = load_theme_data()
        fiedler_df = load_fiedler_data()

        # Filter stocks containing theme
        mask = df['naverTheme'].apply(lambda x: theme in parse_themes(x))
        theme_stocks = df[mask].copy()

        if len(theme_stocks) == 0:
            raise HTTPException(status_code=404, detail=f"Theme not found: {theme}")

        # Calculate score and sort
        theme_stocks['total_score'] = theme_stocks['1'].fillna(0) - theme_stocks['-1'].fillna(0)
        theme_stocks = theme_stocks.sort_values('total_score', ascending=False)

        # Get Fiedler for this theme
        theme_fiedler = 0.0
        cohesion_level = "unknown"
        if fiedler_df is not None and theme in fiedler_df.index:
            theme_fiedler = safe_float(fiedler_df.loc[theme, 'fiedler'])
            if theme_fiedler > 3.0:
                cohesion_level = "very_strong"
            elif theme_fiedler >= 1.0:
                cohesion_level = "strong"
            elif theme_fiedler >= 0.5:
                cohesion_level = "moderate"
            else:
                cohesion_level = "weak"

        stocks = []
        for _, row in theme_stocks.head(limit).iterrows():
            stock_name = row['name']
            bearish = safe_float(row.get('-1', 0))
            neutral = safe_float(row.get('0', 0))
            bullish = safe_float(row.get('1', 0))
            total_score = safe_float(row.get('total_score', 0))

            # Get real signal probability
            signal_prob = get_signal_probability(stock_name)
            buy_pct = signal_prob["buy"]

            # Determine signal based on buy probability
            if buy_pct >= 70:
                signal = "strong_buy"
            elif buy_pct >= 50:
                signal = "buy"
            elif buy_pct >= 30:
                signal = "neutral"
            else:
                signal = "avoid"

            stocks.append({
                "name": stock_name,
                "ticker": str(row.get('tickers', '')),
                "market": row.get('market', ''),
                "signal_probability": {
                    "sell": round(signal_prob["sell"], 1),
                    "neutral": round(signal_prob["neutral"], 1),
                    "buy": round(signal_prob["buy"], 1)
                },
                "total_score": round(total_score, 3),
                "momentum": row.get('mmt', ''),
                "signal": signal,
                "buy_pct": round(buy_pct, 1)
            })

        return {
            "success": True,
            "theme": theme,
            "fiedler": round(theme_fiedler, 3),
            "cohesion_level": cohesion_level,
            "stock_count": len(theme_stocks),
            "stocks": stocks
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search-themes")
async def search_themes(
    q: str = Query(..., description="Search query"),
    limit: int = Query(30, description="Max results")
):
    """Search themes by name with fuzzy matching"""
    try:
        df = load_theme_data()
        fiedler_df = load_fiedler_data()
        all_themes = get_all_themes()

        # Filter by query with fuzzy matching
        matching = [t for t in all_themes if fuzzy_match(q, t)]

        # If no matches, try even more relaxed matching
        if not matching and len(q) >= 2:
            # Try matching any 2+ character substring
            matching = [t for t in all_themes if any(
                q.lower() in word.lower() or word.lower() in q.lower()
                for word in t.replace('-', ' ').replace('/', ' ').split()
            )]

        # Sort by relevance (exact match first, then by Fiedler)
        def sort_key(theme):
            # Exact match gets highest priority
            if q.lower() == theme.lower():
                return (0, 0)
            # Starts with query
            if theme.lower().startswith(q.lower()):
                return (1, 0)
            # Contains query as word
            if q.lower() in theme.lower().split():
                return (2, 0)
            # Get Fiedler for secondary sorting
            fiedler = 0.0
            if fiedler_df is not None and theme in fiedler_df.index:
                fiedler = float(fiedler_df.loc[theme, 'fiedler'])
            return (3, -fiedler)

        matching.sort(key=sort_key)

        # Add Fiedler data
        results = []
        for theme in matching[:limit]:
            result = {"theme": theme, "fiedler": 0.0, "cohesion_level": "unknown"}
            if fiedler_df is not None and theme in fiedler_df.index:
                fiedler_val = float(fiedler_df.loc[theme, 'fiedler'])
                result["fiedler"] = round(fiedler_val, 3)
                if fiedler_val > 3.0:
                    result["cohesion_level"] = "very_strong"
                elif fiedler_val >= 1.0:
                    result["cohesion_level"] = "strong"
                elif fiedler_val >= 0.5:
                    result["cohesion_level"] = "moderate"
                else:
                    result["cohesion_level"] = "weak"
            results.append(result)

        return {
            "success": True,
            "query": q,
            "themes": results,
            "count": len(results),
            "total_themes": len(all_themes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_all(
    q: str = Query(..., description="Search query"),
    limit: int = Query(20, description="Max results per type")
):
    """Search both stocks and themes with fuzzy matching"""
    try:
        df = load_theme_data()
        fiedler_df = load_fiedler_data()
        all_themes = get_all_themes()

        # Search stocks
        stock_matches = df[df['name'].apply(lambda x: fuzzy_match(q, str(x)))]
        stocks = []
        for _, row in stock_matches.head(limit).iterrows():
            stock_name = row['name']
            signal_prob = get_signal_probability(stock_name)
            stocks.append({
                "name": stock_name,
                "ticker": str(row.get('tickers', '')),
                "market": row.get('market', ''),
                "buy_pct": round(signal_prob["buy"], 1),
                "type": "stock"
            })

        # Search themes
        theme_matches = [t for t in all_themes if fuzzy_match(q, t)]
        themes = []
        for theme in theme_matches[:limit]:
            fiedler = 0.0
            if fiedler_df is not None and theme in fiedler_df.index:
                fiedler = float(fiedler_df.loc[theme, 'fiedler'])
            themes.append({
                "theme": theme,
                "fiedler": round(fiedler, 3),
                "type": "theme"
            })

        # Sort themes by Fiedler
        themes.sort(key=lambda x: x['fiedler'], reverse=True)

        return {
            "success": True,
            "query": q,
            "stocks": stocks,
            "themes": themes,
            "stock_count": len(stocks),
            "theme_count": len(themes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph-data")
async def get_graph_data(
    stock: Optional[str] = Query(None, description="Center stock name"),
    theme: Optional[str] = Query(None, description="Center theme name"),
    depth: int = Query(1, description="Expansion depth (1 or 2)")
):
    """
    Get graph data for vis.js network visualization.
    Returns nodes and edges for the theme-stock network.
    """
    try:
        df = load_theme_data()
        fiedler_df = load_fiedler_data()

        nodes = []
        edges = []
        node_ids = set()

        def get_cohesion_color(fiedler):
            """Get color based on Fiedler value"""
            if fiedler > 3.0:
                return "#10b981"  # Green - very strong
            elif fiedler >= 1.0:
                return "#3b82f6"  # Blue - strong
            elif fiedler >= 0.5:
                return "#f59e0b"  # Yellow - moderate
            else:
                return "#ef4444"  # Red - weak

        def add_stock_node(name, is_center=False):
            if f"stock_{name}" in node_ids:
                return
            node_ids.add(f"stock_{name}")

            stock_data = df[df['name'] == name]
            if len(stock_data) == 0:
                return

            row = stock_data.iloc[0]
            score = safe_float(row.get('1', 0)) - safe_float(row.get('-1', 0))
            signal = "bullish" if score > 0.3 else "neutral" if score > 0 else "bearish"

            nodes.append({
                "id": f"stock_{name}",
                "label": name,
                "type": "stock",
                "ticker": str(row.get('tickers', '')),
                "signal": signal,
                "score": round(score, 3),
                "size": 45 if is_center else 30,
                "color": "#ef4444" if signal == "bullish" else "#3b82f6" if signal == "neutral" else "#64748b",
                "isCenter": is_center
            })

        def add_theme_node(theme_name):
            if f"theme_{theme_name}" in node_ids:
                return
            node_ids.add(f"theme_{theme_name}")

            fiedler = 0.0
            if fiedler_df is not None and theme_name in fiedler_df.index:
                fiedler = float(fiedler_df.loc[theme_name, 'fiedler'])

            nodes.append({
                "id": f"theme_{theme_name}",
                "label": theme_name,
                "type": "theme",
                "fiedler": round(fiedler, 3),
                "size": 25,
                "color": get_cohesion_color(fiedler)
            })

        def add_edge(from_id, to_id):
            edge_id = f"edge_{from_id}_{to_id}"
            if edge_id not in node_ids:
                node_ids.add(edge_id)
                edges.append({
                    "id": edge_id,
                    "from": from_id,
                    "to": to_id
                })

        # Build graph based on center type
        if stock:
            # Stock-centered graph
            stock_data = df[df['name'] == stock]
            if len(stock_data) == 0:
                stock_data = df[df['name'].str.contains(stock, na=False)]

            if len(stock_data) == 0:
                raise HTTPException(status_code=404, detail=f"Stock not found: {stock}")

            row = stock_data.iloc[0]
            stock_name = row['name']
            themes = parse_themes(row.get('naverTheme', '[]'))

            # Add center stock
            add_stock_node(stock_name, is_center=True)

            # Add themes connected to stock
            for theme_name in themes:
                add_theme_node(theme_name)
                add_edge(f"stock_{stock_name}", f"theme_{theme_name}")

        elif theme:
            # Theme-centered graph
            add_theme_node(theme)

            # Get stocks in theme
            mask = df['naverTheme'].apply(lambda x: theme in parse_themes(x))
            theme_stocks = df[mask].copy()

            # Calculate score and get top stocks
            theme_stocks['total_score'] = theme_stocks['1'].fillna(0) - theme_stocks['-1'].fillna(0)
            theme_stocks = theme_stocks.sort_values('total_score', ascending=False).head(15)

            for _, row in theme_stocks.iterrows():
                stock_name = row['name']
                add_stock_node(stock_name)
                add_edge(f"theme_{theme}", f"stock_{stock_name}")

                # Depth 2: Add other themes for each stock
                if depth >= 2:
                    other_themes = parse_themes(row.get('naverTheme', '[]'))
                    for other_theme in other_themes[:5]:  # Limit to avoid clutter
                        if other_theme != theme:
                            add_theme_node(other_theme)
                            add_edge(f"stock_{stock_name}", f"theme_{other_theme}")

        else:
            # Default: Show top co-movement themes
            if fiedler_df is not None:
                top_themes = fiedler_df.nlargest(10, 'fiedler')
                for theme_name in top_themes.index:
                    add_theme_node(theme_name)

        return {
            "success": True,
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "stock_count": len([n for n in nodes if n['type'] == 'stock']),
                "theme_count": len([n for n in nodes if n['type'] == 'theme'])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
