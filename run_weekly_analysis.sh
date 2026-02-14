#!/bin/bash
# Weekly Investment Analysis - Complete Pipeline
# Runs all analysis components and generates synthesis report

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get date from libPath.txt (isDate key) or use provided argument or today's date
# Priority: 1) Command line argument, 2) libPath.txt isDate, 3) Today's date
if [ -n "$1" ]; then
    # Use provided date argument
    DATE="$1"
else
    # Try to read from libPath.txt
    LIBPATH_FILE="/mnt/nas/AutoGluon/AutoML_Krx/libPath.txt"
    if [ -f "$LIBPATH_FILE" ]; then
        # Extract isDate from JSON and convert YYYY-MM-DD to YYYYMMDD
        IS_DATE=$(python3 -c "
import json
import sys
try:
    with open('$LIBPATH_FILE', 'r', encoding='utf-8') as f:
        data = json.load(f)
        is_date = data.get('isDate', '')
        # Convert YYYY-MM-DD to YYYYMMDD
        if is_date:
            print(is_date.replace('-', ''))
        else:
            sys.exit(1)
except Exception as e:
    sys.exit(1)
" 2>/dev/null)
        
        if [ -n "$IS_DATE" ]; then
            DATE="$IS_DATE"
            echo -e "${BLUE}Using date from libPath.txt: ${GREEN}${DATE}${NC}"
        else
            # Fallback to today's date
            DATE=$(date +%Y%m%d)
            echo -e "${YELLOW}Could not read isDate from libPath.txt, using today: ${GREEN}${DATE}${NC}"
        fi
    else
        # Fallback to today's date
        DATE=$(date +%Y%m%d)
        echo -e "${YELLOW}libPath.txt not found, using today: ${GREEN}${DATE}${NC}"
    fi
fi

REPORT_DIR="reports"
DATA_DIR="data"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  WEEKLY INVESTMENT ANALYSIS PIPELINE${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "Analysis Date: ${GREEN}${DATE}${NC}"
echo -e "Start Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Create directories if they don't exist
mkdir -p "${REPORT_DIR}"
mkdir -p "${DATA_DIR}"

# Step 1: Generate Naver theme cohesion analysis and report (optimized with incremental calculation)
echo -e "${YELLOW}[1/13]${NC} Generating Naver theme cohesion analysis..."
echo -e "  ${BLUE}→${NC}  Using optimized Fiedler calculation (sparse solver + incremental updates)"
DATE_FORMATTED=$(echo "${DATE}" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3/')
START_TIME=$(date +%s)
if python3 scripts/analyze_naver_theme_cohesion.py --date "${DATE_FORMATTED}" 2>&1 | tee /tmp/cohesion_analysis.log | grep -E "(Progress:|Themes with|Target Date:|Using date)" || true; then
    END_TIME=$(date +%s)
    ELAPSED=$((END_TIME - START_TIME))
    MINUTES=$((ELAPSED / 60))
    SECONDS=$((ELAPSED % 60))
    
    # Check if it was incremental (fast) or full (slower)
    if [ $ELAPSED -lt 120 ]; then
        echo -e "  ${GREEN}✓${NC}  Naver theme cohesion analysis complete (incremental: ${MINUTES}m ${SECONDS}s)"
    else
        echo -e "  ${GREEN}✓${NC}  Naver theme cohesion analysis complete (full run: ${MINUTES}m ${SECONDS}s)"
    fi
    echo -e "      - ${REPORT_DIR}/NAVER_THEME_COHESION_REPORT_${DATE}.md"
    echo -e "      - ${DATA_DIR}/enhanced_cohesion_themes_${DATE}.csv"
else
    echo -e "  ${YELLOW}⚠${NC}  Cohesion analysis incomplete (continuing with existing data)"
fi
echo ""

# Step 2: Generate 4-tier classification
echo -e "${YELLOW}[2/13]${NC} Generating 4-tier investment classification..."

# Check if cohesion file exists for this date
COHESION_FILE="${DATA_DIR}/weekly_cohesion_change_${DATE}.csv"
if [ ! -f "${COHESION_FILE}" ]; then
    echo -e "  ${YELLOW}⚠${NC}  Cohesion file not found: ${COHESION_FILE}"
    echo -e "  ${YELLOW}→${NC}  Looking for alternative cohesion data..."

    # Try enhanced_cohesion_themes file first (has historical_fiedler)
    ALT_FILE1="${DATA_DIR}/enhanced_cohesion_themes_${DATE}.csv"
    if [ -f "${ALT_FILE1}" ]; then
        COHESION_FILE="${ALT_FILE1}"
        echo -e "  ${GREEN}✓${NC}  Found alternative: ${ALT_FILE1}"
    else
        # Try theme_cohesion_ranking file as fallback
        ALT_FILE2="${DATA_DIR}/theme_cohesion_ranking_${DATE}.csv"
        if [ -f "${ALT_FILE2}" ]; then
            COHESION_FILE="${ALT_FILE2}"
            echo -e "  ${GREEN}✓${NC}  Found alternative: ${ALT_FILE2}"
        else
            echo -e "  ${RED}✗${NC}  No cohesion data available for ${DATE}"
            echo -e "  ${RED}→${NC}  Skipping 4-tier classification"
            exit 1
        fi
    fi
fi

# Convert DATE from YYYYMMDD to YYYY-MM-DD for the script
DATE_FORMATTED_TIER=$(echo "${DATE}" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3/')
if python3 scripts/analyze_4_tier_themes.py --cohesion-file "${COHESION_FILE}" --date "${DATE_FORMATTED_TIER}"; then
    echo -e "  ${GREEN}✓${NC}  4-tier classification complete"
    echo -e "      - ${DATA_DIR}/tier1_buy_now_${DATE}.csv"
    echo -e "      - ${DATA_DIR}/tier2_accumulate_${DATE}.csv"
    echo -e "      - ${DATA_DIR}/tier3_research_${DATE}.csv"
    echo -e "      - ${DATA_DIR}/tier4_monitor_${DATE}.csv"
    echo -e "      - ${DATA_DIR}/4tier_summary_${DATE}.json"
else
    echo -e "  ${RED}✗${NC}  4-tier classification failed"
    exit 1
fi
echo ""

# Step 3: Generate timing predictions
echo -e "${YELLOW}[3/13]${NC} Calculating TIER 3 timing predictions..."
if python3 scripts/predict_timing.py > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Timing predictions complete"
    echo -e "      - ${DATA_DIR}/tier3_timing_predictions_${DATE}.json"
else
    echo -e "  ${YELLOW}⚠${NC}  Timing predictions incomplete (limited data)"
    echo -e "      Continuing with qualitative estimates..."
fi
echo ""

# Step 4: Generate sector rankings for TIER 1 themes
echo -e "${YELLOW}[4/13]${NC} Generating detailed sector rankings..."

# Read TIER 1 themes from summary
TIER1_THEMES=$(python3 -c "
import json
with open('${DATA_DIR}/4tier_summary_${DATE}.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    themes = data['tier1']['themes']
    for theme in themes:
        print(theme)
" 2>/dev/null)

if [ -z "$TIER1_THEMES" ]; then
    echo -e "  ${YELLOW}⚠${NC}  No TIER 1 themes found"
else
    echo -e "  Found ${GREEN}$(echo "$TIER1_THEMES" | wc -l)${NC} TIER 1 themes"
    while IFS= read -r theme; do
        echo -e "  ${BLUE}→${NC}  Analyzing: $theme"
        python3 scripts/generate_sector_rankings.py --sector "$theme" --date "${DATE}" > /dev/null 2>&1 || true
    done <<< "$TIER1_THEMES"
    echo -e "  ${GREEN}✓${NC}  Sector rankings complete"
fi
echo ""

# Step 5: Generate weekly synthesis report
echo -e "${YELLOW}[5/14]${NC} Generating weekly synthesis report..."
REPORT_FILE="${REPORT_DIR}/weekly_synthesis_${DATE}.md"

if python3 scripts/generate_weekly_synthesis.py --date "${DATE}" > "${REPORT_FILE}"; then
    echo -e "  ${GREEN}✓${NC}  Weekly synthesis report generated"
    echo -e "      ${GREEN}→${NC}  ${REPORT_FILE}"
else
    echo -e "  ${RED}✗${NC}  Report generation failed"
    exit 1
fi
echo ""

# Step 5.5: Fundamental Validation (Layer 4)
echo -e "${YELLOW}[5.5/14]${NC} Running Fundamental Validation..."
echo -e "  ${BLUE}→${NC}  Reconciling quantitative signals with fundamental indicators"
if python3 scripts/validate_fundamentals.py --date "${DATE}" --top-themes 10 2>&1 | grep -E "(DIVERGENCE|CONFIRMED|Validation report saved)" || true; then
    echo -e "  ${GREEN}✓${NC}  Fundamental validation complete"
    echo -e "      - ${REPORT_DIR}/FUNDAMENTAL_VALIDATION_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Fundamental validation incomplete (continuing)"
fi
echo ""

# Step 6: Generate additional investment reports
echo -e "${YELLOW}[6/13]${NC} Generating additional investment reports..."

# Generate Within-Theme Leadership Report
DATE_FORMATTED=$(echo "${DATE}" | sed 's/\([0-9]\{4\}\)\([0-9]\{2\}\)\([0-9]\{2\}\)/\1-\2-\3/')
if python3 scripts/analyze_within_theme_leadership.py --date "${DATE_FORMATTED}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Within-theme leadership analysis complete"
    echo -e "      - ${REPORT_DIR}/WITHIN_THEME_LEADERSHIP_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Within-theme leadership analysis skipped (may need cohesion data first)"
fi

# Step 7: Generate Investment Implications Report
echo -e "${YELLOW}[7/13]${NC} Generating Investment Implications Report..."
if python3 scripts/generate_investment_implications.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Investment Implications report complete"
    echo -e "      - ${REPORT_DIR}/INVESTMENT_IMPLICATIONS_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Investment Implications report skipped"
fi

# Step 8: Generate Executive Summary
echo -e "${YELLOW}[8/13]${NC} Generating Executive Summary..."
if python3 scripts/generate_executive_summary.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Executive Summary complete"
    echo -e "      - ${REPORT_DIR}/EXECUTIVE_SUMMARY_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Executive Summary skipped"
fi

# Step 9: Generate Top Investment Themes
echo -e "${YELLOW}[9/13]${NC} Generating Top Investment Themes Report..."
if python3 scripts/generate_top_themes_report.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Top Investment Themes report complete"
    echo -e "      - ${REPORT_DIR}/TOP_THEMES_INVESTMENT_READY_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Top Investment Themes report skipped"
fi

# Step 10: Generate Executive Dashboard
echo -e "${YELLOW}[10/13]${NC} Generating Executive Dashboard..."
if python3 scripts/generate_executive_dashboard.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Executive Dashboard complete"
    echo -e "      - ${REPORT_DIR}/EXECUTIVE_DASHBOARD_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Executive Dashboard skipped"
fi

# Step 11: Generate Investment Memo
echo -e "${YELLOW}[11/13]${NC} Generating Investment Memo..."
if python3 scripts/generate_investment_memo.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Investment Memo complete"
    echo -e "      - ${REPORT_DIR}/INVESTMENT_MEMO_${DATE}.md"
else
    echo -e "  ${YELLOW}⚠${NC}  Investment Memo skipped"
fi

# Step 12: Generate Email Template
echo -e "${YELLOW}[12/13]${NC} Generating Email Template..."
if python3 scripts/generate_email_template.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Email template complete"
    echo -e "      - ${REPORT_DIR}/EMAIL_TEMPLATE_${DATE}.html"
else
    echo -e "  ${YELLOW}⚠${NC}  Email template skipped"
fi

# Step 13: Generate Visualizations
echo -e "${YELLOW}[13/13]${NC} Generating Visualizations..."
if python3 scripts/generate_visualizations.py --date "${DATE}" > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC}  Visualizations complete"
    echo -e "      - ${REPORT_DIR}/*_${DATE}.png"
else
    echo -e "  ${YELLOW}⚠${NC}  Visualizations skipped"
fi

echo ""

# Generate summary statistics
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  ANALYSIS COMPLETE${NC}"
echo -e "${BLUE}======================================${NC}"
echo -e "End Time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo -e "${GREEN}Generated Files:${NC}"
echo -e "  • 4-Tier CSVs:     ${DATA_DIR}/tier*_${DATE}.csv"
echo -e "  • Summary JSON:    ${DATA_DIR}/4tier_summary_${DATE}.json"
echo -e "  • Timing Data:     ${DATA_DIR}/tier3_timing_predictions_${DATE}.json"
echo -e "  • Synthesis Report: ${REPORT_FILE}"
echo -e "  • Cohesion Report: ${REPORT_DIR}/NAVER_THEME_COHESION_REPORT_${DATE}.md"
echo -e "  • Leadership Report: ${REPORT_DIR}/WITHIN_THEME_LEADERSHIP_${DATE}.md"
echo -e "  • ${YELLOW}Fundamental Validation${NC}: ${REPORT_DIR}/FUNDAMENTAL_VALIDATION_${DATE}.md"
echo -e "  • Investment Implications: ${REPORT_DIR}/INVESTMENT_IMPLICATIONS_${DATE}.md"
echo -e "  • Executive Summary: ${REPORT_DIR}/EXECUTIVE_SUMMARY_${DATE}.md"
echo -e "  • Top Investment Themes: ${REPORT_DIR}/TOP_THEMES_INVESTMENT_READY_${DATE}.md"
echo -e "  • Executive Dashboard: ${REPORT_DIR}/EXECUTIVE_DASHBOARD_${DATE}.md"
echo -e "  • Investment Memo: ${REPORT_DIR}/INVESTMENT_MEMO_${DATE}.md"
echo -e "  • Email Template: ${REPORT_DIR}/EMAIL_TEMPLATE_${DATE}.html"
echo -e "  • Visualizations: ${REPORT_DIR}/*_${DATE}.png"
echo ""
echo -e "${GREEN}Quick Actions:${NC}"
echo -e "  # View synthesis report"
echo -e "  cat ${REPORT_FILE}"
echo ""
echo -e "  # View in browser (convert to HTML)"
echo -e "  pandoc ${REPORT_FILE} -o ${REPORT_DIR}/weekly_synthesis_${DATE}.html"
echo ""
echo -e "  # Email report"
echo -e "  mail -s 'Weekly Investment Synthesis ${DATE}' user@example.com < ${REPORT_FILE}"
echo ""
echo -e "${BLUE}======================================${NC}"
