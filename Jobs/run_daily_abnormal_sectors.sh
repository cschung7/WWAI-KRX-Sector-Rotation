#!/bin/bash
# Daily Abnormal Sector Analysis - Automated Runner
# Runs daily to identify sectors showing unusual Fiedler eigenvalue patterns

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

# Create logs directory if it doesn't exist
mkdir -p logs

# Log file with date
LOG_FILE="logs/daily_abnormal_sectors_$(date +%Y%m%d).log"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  DAILY ABNORMAL SECTOR ANALYSIS${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Date: ${GREEN}$(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo -e "Project: ${GREEN}$PROJECT_ROOT${NC}"
echo -e "Log File: ${GREEN}$LOG_FILE${NC}"
echo ""

# Run the analysis
echo -e "${YELLOW}Running daily abnormal sector analysis...${NC}"
if python3 "$SCRIPT_DIR/analyze_daily_abnormal_sectors.py" 2>&1 | tee "$LOG_FILE"; then
    echo ""
    echo -e "${GREEN}✓${NC}  Daily analysis complete"
    echo ""
    echo -e "${GREEN}Generated Files:${NC}"
    DATE_STR=$(date +%Y%m%d)
    echo -e "  • CSV: data/abnormal_sectors_${DATE_STR}.csv"
    echo -e "  • Report: reports/ABNORMAL_SECTORS_${DATE_STR}.md"
    echo -e "  • Log: logs/daily_abnormal_sectors_${DATE_STR}.log"
    echo ""
    echo -e "${BLUE}======================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}✗${NC}  Daily analysis failed"
    echo -e "  Check log file: $LOG_FILE"
    echo -e "${BLUE}======================================${NC}"
    exit 1
fi

