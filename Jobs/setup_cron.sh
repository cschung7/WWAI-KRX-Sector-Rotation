#!/bin/bash
##############################################################################
# Setup Cron Job for KRX Sector Rotation Daily Pipeline
##############################################################################
# Purpose: Configure cron to run daily_deploy_krx.sh at 22:00 JST
# Usage: ./setup_cron.sh
##############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/daily_deploy_krx.sh"
LOG_DIR="$SCRIPT_DIR/logs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   Setup Cron Job - KRX Sector Rotation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if script exists
if [ ! -f "$CRON_SCRIPT" ]; then
    echo -e "${RED}✗ Error: $CRON_SCRIPT not found${NC}"
    exit 1
fi

# Make script executable
chmod +x "$CRON_SCRIPT"
echo -e "${GREEN}✓ Script is executable${NC}"

# Create logs directory
mkdir -p "$LOG_DIR"
echo -e "${GREEN}✓ Logs directory created: $LOG_DIR${NC}"

# Cron job entry
CRON_ENTRY="0 22 * * * $CRON_SCRIPT >> $LOG_DIR/cron_\$(date +\\%Y-\\%m-\\%d).log 2>&1"

echo ""
echo -e "${YELLOW}Cron job to be added:${NC}"
echo "$CRON_ENTRY"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "daily_deploy_krx.sh"; then
    echo -e "${YELLOW}⚠ Cron job already exists${NC}"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep "daily_deploy_krx.sh"
    echo ""
    read -p "Replace existing cron job? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Aborted${NC}"
        exit 0
    fi

    # Remove old cron job
    (crontab -l 2>/dev/null | grep -v "daily_deploy_krx.sh") | crontab -
    echo -e "${GREEN}✓ Removed old cron job${NC}"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
echo -e "${GREEN}✓ Cron job added successfully${NC}"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Schedule: Daily at 22:00 JST (10 PM)"
echo "Script: $CRON_SCRIPT"
echo "Logs: $LOG_DIR/cron_YYYY-MM-DD.log"
echo ""
echo -e "${YELLOW}Verify cron job:${NC}"
echo "  crontab -l | grep daily_deploy_krx"
echo ""
echo -e "${YELLOW}Check cron status:${NC}"
echo "  sudo systemctl status cron"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  tail -f $LOG_DIR/cron_\$(date +%Y-%m-%d).log"
echo ""
echo -e "${YELLOW}Manual run:${NC}"
echo "  cd $SCRIPT_DIR && ./daily_deploy_krx.sh"
echo ""
