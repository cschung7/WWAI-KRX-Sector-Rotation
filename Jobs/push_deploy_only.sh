#!/bin/bash
##############################################################################
# KRX Sector Rotation - Push & Deploy Only
##############################################################################
# Purpose: Git commit + push data/analysis/dashboard changes (no data update)
# Usage: ./push_deploy_only.sh
# Note: Cloudflare Tunnel serves from NAS; git push is for backup/version control
##############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MARKET_DIR="/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX"
MARKET_NAME="KRX"
DASHBOARD_URL="https://krx.wwai.app"
TODAY=$(date +%Y-%m-%d)

echo -e "${BLUE}=========================================================================${NC}"
echo -e "${BLUE}   ${MARKET_NAME} Sector Rotation - Push & Deploy${NC}"
echo -e "${BLUE}   $(date +"%Y-%m-%d %H:%M:%S")${NC}"
echo -e "${BLUE}=========================================================================${NC}"
echo ""

cd "$MARKET_DIR"

# Check for changes
if git diff --quiet HEAD -- data/ analysis/ dashboard/ 2>/dev/null && \
   git diff --quiet --cached -- data/ analysis/ dashboard/ 2>/dev/null && \
   [ -z "$(git ls-files --others --exclude-standard data/ analysis/ dashboard/ 2>/dev/null)" ]; then
    echo -e "${BLUE}No changes in data/, analysis/, or dashboard/${NC}"
    echo -e "${GREEN}Nothing to deploy.${NC}"
    exit 0
fi

# Stage changes
echo -e "${YELLOW}Adding changes...${NC}"
git add data/ analysis/ dashboard/ 2>/dev/null || true

# Check if there are staged changes
if git diff --cached --quiet; then
    echo -e "${BLUE}No staged changes${NC}"
    exit 0
fi

# Show what's being committed
echo -e "${YELLOW}Changes to commit:${NC}"
git diff --cached --stat

# Commit
echo -e "${YELLOW}Committing...${NC}"
git commit -m "Daily update ${TODAY}

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"

# Push
echo -e "${YELLOW}Pushing to origin...${NC}"
git push origin main

echo ""
echo -e "${GREEN}=========================================================================${NC}"
echo -e "${GREEN}   ${MARKET_NAME} pushed successfully!${NC}"
echo -e "${GREEN}   Dashboard: ${DASHBOARD_URL}${NC}"
echo -e "${GREEN}=========================================================================${NC}"
