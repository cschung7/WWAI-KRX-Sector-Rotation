#!/bin/bash
##############################################################################
# KRX Sector Rotation - Complete Daily Pipeline & Deployment
##############################################################################
# Purpose: Run complete data pipeline and deploy to Railway
# Usage: ./daily_deploy_krx.sh [--skip-update] [--skip-deploy]
# Cron: 0 22 * * * /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/Jobs/daily_deploy_krx.sh >> /mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/Jobs/logs/cron_$(date +\%Y-\%m-\%d).log 2>&1
##############################################################################

set -e

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AUTOML_DIR="/mnt/nas/AutoGluon/AutoML_Krx"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Log file
LOG_FILE="$LOG_DIR/daily_deploy_$(date '+%Y-%m-%d_%H-%M-%S').log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
SKIP_UPDATE=false
SKIP_DEPLOY=false
for arg in "$@"; do
    case $arg in
        --skip-update) SKIP_UPDATE=true ;;
        --skip-deploy) SKIP_DEPLOY=true ;;
    esac
done

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log_section() {
    log ""
    log "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    log "${BLUE}   $1${NC}"
    log "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    log ""
}

# Error handler
handle_error() {
    log "${RED}✗ Error in phase: $1${NC}"
    log "${RED}Check log: $LOG_FILE${NC}"
    exit 1
}

# Start
log_section "🚀 KRX Sector Rotation - Daily Pipeline"
log "Started: $(date '+%Y-%m-%d %H:%M:%S')"
log "Log file: $LOG_FILE"

##############################################################################
# Phase 1: Data Updates (30-45 minutes)
##############################################################################
if [ "$SKIP_UPDATE" = false ]; then
    log_section "📊 Phase 1: Data Updates"
    log "${CYAN}Running: daily_update_all.sh${NC}"

    cd "$AUTOML_DIR"
    if bash daily_update_all.sh >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✓ Data updates completed${NC}"
    else
        handle_error "Phase 1 - Data Updates"
    fi
else
    log_section "⏭️  Phase 1: Skipped (--skip-update)"
fi

##############################################################################
# Phase 2: Dashboard Data Preparation (5 minutes)
##############################################################################
if [ "$SKIP_UPDATE" = false ]; then
    log_section "🎯 Phase 2: Dashboard Data Preparation"
    log "${CYAN}Running: filter_sector_rotation_krx.sh${NC}"

    cd "$AUTOML_DIR"
    if bash filter_sector_rotation_krx.sh >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✓ Dashboard data prepared${NC}"
    else
        handle_error "Phase 2 - Dashboard Preparation"
    fi
else
    log_section "⏭️  Phase 2: Skipped (--skip-update)"
fi

##############################################################################
# Phase 3: Theme Analysis (10 minutes)
##############################################################################
if [ "$SKIP_UPDATE" = false ]; then
    log_section "🔬 Phase 3: Theme Analysis"
    log "${CYAN}Running: run_daily_theme_analysis.sh${NC}"

    cd "$AUTOML_DIR"
    if bash run_daily_theme_analysis.sh >> "$LOG_FILE" 2>&1; then
        log "${GREEN}✓ Theme analysis completed${NC}"
    else
        log "${YELLOW}⚠ Theme analysis failed (non-critical)${NC}"
    fi
else
    log_section "⏭️  Phase 3: Skipped (--skip-update)"
fi

##############################################################################
# Phase 4: Deploy to Railway (2-3 minutes)
##############################################################################
if [ "$SKIP_DEPLOY" = false ]; then
    log_section "🚀 Phase 4: Deploy to Railway"

    cd "$PROJECT_ROOT"

    # Check if there are changes
    if git diff --quiet && git diff --cached --quiet; then
        log "${YELLOW}⚠ No changes to deploy${NC}"
        log "Data files are already up to date on Railway."
    else
        # Show what will be deployed
        log "${YELLOW}📝 Files to be deployed:${NC}"
        git status --short | tee -a "$LOG_FILE"
        log ""

        # Add data files
        log "${CYAN}Adding data files...${NC}"
        git add data/*.csv data/*.json data/rankings/ data/bb_filter/ 2>/dev/null || true

        # Create commit message
        TODAY=$(date '+%Y-%m-%d')
        COMMIT_MSG="Data update: $TODAY

- Updated daily market data
- Refreshed dashboard data
- Updated rankings and filters

Auto-deployed via daily_deploy_krx.sh
"

        # Commit
        log "${CYAN}Committing changes...${NC}"
        if git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1; then
            log "${GREEN}✓ Changes committed${NC}"
        else
            handle_error "Phase 4 - Git Commit"
        fi

        # Push to GitHub
        log "${CYAN}Pushing to GitHub...${NC}"
        if git push origin main >> "$LOG_FILE" 2>&1; then
            log "${GREEN}✓ Pushed to GitHub${NC}"
        else
            handle_error "Phase 4 - Git Push"
        fi

        log ""
        log "${GREEN}✅ Deployment Initiated!${NC}"
        log ""
        log "Railway is now building and deploying..."
        log "⏱  Build time: ~2-3 minutes"
        log "🌐 URL: https://web-production-e5d7.up.railway.app"
    fi
else
    log_section "⏭️  Phase 4: Skipped (--skip-deploy)"
fi

##############################################################################
# Summary
##############################################################################
log_section "📋 Pipeline Summary"
log "Completed: $(date '+%Y-%m-%d %H:%M:%S')"
log "Log file: $LOG_FILE"
log ""

if [ "$SKIP_UPDATE" = false ] && [ "$SKIP_DEPLOY" = false ]; then
    log "${GREEN}✅ Complete pipeline executed successfully!${NC}"
elif [ "$SKIP_UPDATE" = true ] && [ "$SKIP_DEPLOY" = false ]; then
    log "${GREEN}✅ Deployment completed (data updates skipped)${NC}"
elif [ "$SKIP_UPDATE" = false ] && [ "$SKIP_DEPLOY" = true ]; then
    log "${GREEN}✅ Data pipeline completed (deployment skipped)${NC}"
else
    log "${YELLOW}⚠ All phases skipped${NC}"
fi

log ""
log "${YELLOW}Verify deployment:${NC}"
log "  curl https://web-production-e5d7.up.railway.app/api/sector-rotation/themes"
log ""
