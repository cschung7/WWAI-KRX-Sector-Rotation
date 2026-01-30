#!/bin/bash
###############################################################################
# Stop Dashboard Server
# 
# This script stops the FastAPI backend server
# 
# Usage:
#   ./stop_dashboard.sh [port]
#
# Arguments:
#   port    Port number (default: 8000)
###############################################################################

set -e

PORT=${1:-8000}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Stopping dashboard server on port $PORT...${NC}"

# Find and kill process on the port
PID=$(lsof -ti:$PORT 2>/dev/null || true)

if [ -z "$PID" ]; then
    echo -e "${YELLOW}No process found running on port $PORT${NC}"
    exit 0
fi

echo -e "${YELLOW}Found process: $PID${NC}"
kill $PID

# Wait a bit and check if it's still running
sleep 2

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}Process still running, forcing kill...${NC}"
    kill -9 $PID
    sleep 1
fi

if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${RED}Failed to stop server on port $PORT${NC}"
    exit 1
else
    echo -e "${GREEN}Server stopped successfully${NC}"
fi

