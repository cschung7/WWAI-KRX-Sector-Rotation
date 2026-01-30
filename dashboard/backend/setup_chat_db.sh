#!/bin/bash
# KRX Sector Rotation Dashboard - Chat Database Setup Script
# Usage: ./setup_chat_db.sh [postgres_password]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="$SCRIPT_DIR/setup_db.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== KRX Chat Database Setup ===${NC}"
echo ""

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: PostgreSQL client (psql) is not installed${NC}"
    exit 1
fi

# Database configuration
DB_NAME="krx_chat"
DB_USER="${PGUSER:-postgres}"
DB_HOST="${PGHOST:-localhost}"
DB_PORT="${PGPORT:-5432}"

echo "Configuration:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo ""

# Function to run psql with credentials
run_psql() {
    if [ -n "$PGPASSWORD" ]; then
        PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$@"
    elif [ -n "$1" ] && [ "$1" = "-d" ]; then
        # Try peer auth for local connections
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$@"
    else
        psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$@"
    fi
}

# Check if password is provided as argument
if [ -n "$1" ]; then
    export PGPASSWORD="$1"
    echo -e "${YELLOW}Using provided password${NC}"
elif [ -z "$PGPASSWORD" ]; then
    echo -e "${YELLOW}No password provided. Set PGPASSWORD environment variable or pass as argument.${NC}"
    echo "Usage: PGPASSWORD=yourpassword ./setup_chat_db.sh"
    echo "   or: ./setup_chat_db.sh yourpassword"
    echo ""
    read -sp "Enter PostgreSQL password for user $DB_USER: " PGPASSWORD
    echo ""
    export PGPASSWORD
fi

# Check connection
echo -e "${YELLOW}Testing database connection...${NC}"
if ! PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "SELECT 1;" postgres > /dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to PostgreSQL server${NC}"
    echo "Please check your credentials and that PostgreSQL is running."
    exit 1
fi
echo -e "${GREEN}Connection successful!${NC}"

# Check if database exists
echo -e "${YELLOW}Checking if database '$DB_NAME' exists...${NC}"
DB_EXISTS=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" postgres)

if [ "$DB_EXISTS" = "1" ]; then
    echo -e "${GREEN}Database '$DB_NAME' already exists${NC}"
else
    echo -e "${YELLOW}Creating database '$DB_NAME'...${NC}"
    PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" postgres
    echo -e "${GREEN}Database created!${NC}"
fi

# Run setup SQL
echo -e "${YELLOW}Running setup SQL script...${NC}"
PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE"

# Verify tables
echo ""
echo -e "${YELLOW}Verifying tables...${NC}"
TABLES=$(PGPASSWORD="$PGPASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")

echo "Tables found:"
echo "$TABLES" | while read -r table; do
    if [ -n "$table" ]; then
        echo "  - $table"
    fi
done

# Check for required tables
if echo "$TABLES" | grep -q "conversations" && echo "$TABLES" | grep -q "messages"; then
    echo ""
    echo -e "${GREEN}=== Setup Complete! ===${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Create .env file from .env.example:"
    echo "   cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
    echo ""
    echo "2. Edit .env with your settings:"
    echo "   DATABASE_URL=postgresql+asyncpg://$DB_USER:YOUR_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
    echo "   OPENROUTER_API_KEY=sk-or-v1-your-api-key"
    echo ""
    echo "3. Start the backend:"
    echo "   cd $SCRIPT_DIR && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
else
    echo -e "${RED}Error: Required tables not found!${NC}"
    exit 1
fi
