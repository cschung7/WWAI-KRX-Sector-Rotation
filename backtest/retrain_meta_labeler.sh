#!/bin/bash
# Retrain Meta-Labeler Script
# Automates the retraining process with latest backtest results

set -e

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKTEST_DIR="/mnt/nas/WWAI/Sector-Rotation/Sector-Rotation-KRX/backtest"
RESULTS_DIR="${BACKTEST_DIR}/results"
MODELS_DIR="${BACKTEST_DIR}/models"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  META-LABELER RETRAINING${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Find latest results file
LATEST_RESULTS=$(ls -t ${RESULTS_DIR}/signal_performance_*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_RESULTS" ]; then
    echo -e "${YELLOW}Error: No backtest results found in ${RESULTS_DIR}${NC}"
    exit 1
fi

echo -e "${GREEN}Using latest results: $(basename ${LATEST_RESULTS})${NC}"
echo ""

# Check if we should use full dataset or sample
if [ "$1" == "--full" ]; then
    SAMPLE_SIZE=""
    echo -e "${BLUE}Training on FULL dataset${NC}"
else
    SAMPLE_SIZE="--sample-size 10000"
    echo -e "${BLUE}Training on SAMPLE (10,000 signals)${NC}"
    echo -e "${YELLOW}Use --full to train on all data${NC}"
fi

# Determine if we should use UCS features
if [ "$2" == "--with-ucs" ]; then
    SKIP_UCS=""
    echo -e "${BLUE}Including UCS_LRS features${NC}"
else
    SKIP_UCS="--skip-ucs"
    echo -e "${BLUE}Using basic features only (faster)${NC}"
    echo -e "${YELLOW}Use --with-ucs to include UCS_LRS features${NC}"
fi

# Run training
echo ""
echo -e "${BLUE}Starting training...${NC}"
echo ""

cd "${BACKTEST_DIR}/.."

python3 backtest/train_meta_labeler.py \
    --results-file "${LATEST_RESULTS}" \
    --model-type xgboost \
    ${SAMPLE_SIZE} \
    ${SKIP_UCS} \
    --use-cv

echo ""
echo -e "${GREEN}✅ Training complete!${NC}"
echo ""
echo -e "Model saved to: ${MODELS_DIR}/"
echo -e "Latest model: $(ls -t ${MODELS_DIR}/meta_labeler_*.pkl 2>/dev/null | head -1)"
echo ""

