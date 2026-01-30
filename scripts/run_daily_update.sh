#!/bin/bash
# =============================================================================
# Daily Price Update Runner
# =============================================================================
# Lightweight daily update that uses existing weekly regime data
# and only recalculates price-based signals (BB position, trend stage)
#
# Usage:
#   ./run_daily_update.sh              # Run for today
#   ./run_daily_update.sh 2026-01-30   # Run for specific date
#   ./run_daily_update.sh --dry-run    # Preview without saving
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Activate conda environment if available
if command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate krx-analysis 2>/dev/null || conda activate base
fi

echo "=============================================="
echo "  KRX Sector Rotation - Daily Price Update"
echo "=============================================="
echo "  Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Project: $PROJECT_DIR"
echo "=============================================="
echo ""

# Run the Python script with any passed arguments
python "$SCRIPT_DIR/daily_price_update.py" "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Daily update completed successfully!"
    echo ""
    echo "Output files:"
    ls -la "$PROJECT_DIR/data/"actionable_tickers_*.csv 2>/dev/null | tail -3
else
    echo ""
    echo "❌ Daily update failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
