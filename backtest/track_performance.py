#!/usr/bin/env python3
"""
Track Meta-Labeling Performance Over Time

Maintains a history of meta-labeling performance metrics.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add backtest directory to path
backtest_dir = Path(__file__).parent

PERFORMANCE_HISTORY_FILE = backtest_dir / "monitoring" / "performance_history.json"

def load_performance_history() -> List[Dict]:
    """Load performance history"""
    if PERFORMANCE_HISTORY_FILE.exists():
        with open(PERFORMANCE_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_performance_history(history: List[Dict]):
    """Save performance history"""
    PERFORMANCE_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERFORMANCE_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, default=str)

def add_performance_entry(metrics: Dict):
    """Add new performance entry"""
    history = load_performance_history()
    
    entry = {
        'date': datetime.now().isoformat(),
        'metrics': metrics
    }
    
    history.append(entry)
    
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[-100:]
    
    save_performance_history(history)
    return entry

def get_performance_trends() -> Dict:
    """Analyze performance trends"""
    history = load_performance_history()
    
    if len(history) < 2:
        return {'status': 'insufficient_data', 'message': 'Need at least 2 entries'}
    
    # Extract metrics over time
    dates = [pd.to_datetime(e['date']) for e in history]
    win_rates = [e['metrics'].get('win_rate_improvement_pp', 0) for e in history]
    sharpe_improvements = [e['metrics'].get('sharpe_improvement', 0) for e in history]
    
    # Calculate trends
    recent_avg_win_rate = np.mean(win_rates[-5:]) if len(win_rates) >= 5 else np.mean(win_rates)
    recent_avg_sharpe = np.mean(sharpe_improvements[-5:]) if len(sharpe_improvements) >= 5 else np.mean(sharpe_improvements)
    
    # Determine status
    if recent_avg_win_rate > 5 and recent_avg_sharpe > 0.1:
        status = 'excellent'
    elif recent_avg_win_rate > 0 and recent_avg_sharpe > 0:
        status = 'good'
    else:
        status = 'needs_review'
    
    return {
        'status': status,
        'recent_avg_win_rate_improvement': recent_avg_win_rate,
        'recent_avg_sharpe_improvement': recent_avg_sharpe,
        'n_entries': len(history),
        'latest_date': dates[-1].isoformat() if dates else None
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Track meta-labeling performance')
    parser.add_argument('--add', type=str, default=None,
                       help='Add performance entry from comparison JSON')
    parser.add_argument('--trends', action='store_true',
                       help='Show performance trends')
    
    args = parser.parse_args()
    
    if args.add:
        # Load comparison results
        with open(args.add, 'r') as f:
            comparison = json.load(f)
        
        metrics = comparison.get('improvements', {})
        entry = add_performance_entry(metrics)
        print(f"Added performance entry: {entry['date']}")
    
    if args.trends:
        trends = get_performance_trends()
        print("Performance Trends:")
        print(json.dumps(trends, indent=2))

