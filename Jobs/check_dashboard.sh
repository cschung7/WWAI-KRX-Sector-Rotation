#!/bin/bash
###############################################################################
# Check Dashboard Status
# 
# This script checks if the dashboard server is running and healthy
# 
# Usage:
#   ./check_dashboard.sh [port]
#
# Arguments:
#   port    Port number (default: 8000)
###############################################################################

set -e

PORT=${1:-8000}
HOST="localhost"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Checking dashboard server status...${NC}"
echo ""

# Check if port is in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PID=$(lsof -ti:$PORT)
    echo -e "${GREEN}✓ Server is running${NC}"
    echo "  Port: $PORT"
    echo "  PID:  $PID"
    echo ""
    
    # Check health endpoint
    echo -e "${BLUE}Checking health endpoint...${NC}"
    if command -v curl &> /dev/null; then
        HEALTH_RESPONSE=$(curl -s "http://$HOST:$PORT/api/health" 2>/dev/null || echo "ERROR")
        
        if [ "$HEALTH_RESPONSE" != "ERROR" ]; then
            echo -e "${GREEN}✓ Health check passed${NC}"
            echo "  Response: $HEALTH_RESPONSE"
        else
            echo -e "${YELLOW}⚠ Health check failed (server may still be starting)${NC}"
        fi
    else
        echo -e "${YELLOW}⚠ curl not available, skipping health check${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}Dashboard URLs:${NC}"
    echo "  Main:     http://$HOST:$PORT"
    echo "  API Docs: http://$HOST:$PORT/docs"
    echo "  Health:   http://$HOST:$PORT/api/health"
    
else
    echo -e "${RED}✗ Server is not running on port $PORT${NC}"
    echo ""
    echo "To start the server, run:"
    echo "  ./start_dashboard.sh"
    exit 1
fi

