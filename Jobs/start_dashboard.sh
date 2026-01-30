#!/bin/bash
###############################################################################
# Start Dashboard Server
# 
# This script starts the FastAPI backend server for the Investment Focus Dashboard
# 
# Usage:
#   ./start_dashboard.sh [options]
#
# Options:
#   --port PORT       Set the port number (default: 8000)
#   --host HOST       Set the host address (default: 0.0.0.0)
#   --reload          Enable auto-reload on code changes (default: enabled)
#   --no-reload       Disable auto-reload
#   --help            Show this help message
###############################################################################

set -e

# Default values
PORT=8000
HOST="0.0.0.0"
RELOAD=true
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DASHBOARD_DIR="$PROJECT_ROOT/dashboard"
BACKEND_DIR="$DASHBOARD_DIR/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --reload)
            RELOAD=true
            shift
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        --help|-h)
            head -20 "$0" | tail -19
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Investment Focus Dashboard Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found${NC}"
    exit 1
fi

# Check if uvicorn is installed
if ! python3 -c "import uvicorn" 2>/dev/null; then
    echo -e "${YELLOW}Warning: uvicorn not found. Installing dependencies...${NC}"
    cd "$BACKEND_DIR"
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo -e "${RED}Error: requirements.txt not found${NC}"
        exit 1
    fi
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Print configuration
echo -e "${GREEN}Configuration:${NC}"
echo "  Project Root: $PROJECT_ROOT"
echo "  Backend Dir:  $BACKEND_DIR"
echo "  Host:         $HOST"
echo "  Port:         $PORT"
echo "  Reload:       $RELOAD"
echo ""

# Check if port is already in use and auto-kill
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PID=$(lsof -ti:$PORT)
    echo -e "${YELLOW}⚠ Port $PORT is already in use (PID: $PID)${NC}"
    echo -e "${YELLOW}Stopping existing process...${NC}"
    
    # Try graceful kill first
    kill $PID 2>/dev/null || true
    sleep 2
    
    # Force kill if still running
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}Force stopping...${NC}"
        kill -9 $PID 2>/dev/null || true
        sleep 1
    fi
    
    # Clean up PID file if exists
    rm -f "/tmp/dashboard_${PORT}.pid"
    
    # Verify it's stopped
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}✗ Failed to stop existing process${NC}"
        echo "Please stop it manually: ./stop_dashboard.sh $PORT"
        exit 1
    else
        echo -e "${GREEN}✓ Stopped existing process${NC}"
        echo ""
    fi
fi

# Start the server
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo -e "${BLUE}Dashboard will be available at: http://localhost:$PORT${NC}"
echo -e "${BLUE}API documentation: http://localhost:$PORT/docs${NC}"
echo -e "${BLUE}Health check: http://localhost:$PORT/api/health${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Set PYTHONPATH for correct module imports
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
echo -e "${GREEN}PYTHONPATH set to: $PROJECT_ROOT${NC}"
echo ""

# Build uvicorn command
UVICORN_CMD="uvicorn main:app --host $HOST --port $PORT"

if [ "$RELOAD" = true ]; then
    UVICORN_CMD="$UVICORN_CMD --reload"
fi

# Run the server
exec $UVICORN_CMD

