#!/bin/bash
# KRX Sector Rotation Dashboard - Chat Database Setup (Sudo Version)
# Usage: sudo -u postgres ./setup_chat_db_sudo.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="$SCRIPT_DIR/setup_db.sql"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

DB_NAME="krx_chat"

echo -e "${GREEN}=== KRX Chat Database Setup (Sudo Mode) ===${NC}"
echo ""

# Check if running as postgres
if [ "$(whoami)" != "postgres" ]; then
    echo -e "${YELLOW}Not running as postgres user.${NC}"
    echo "Run with: sudo -u postgres $0"
    echo ""
    echo "Or run these commands manually:"
    echo "  sudo -u postgres createdb krx_chat"
    echo "  sudo -u postgres psql -d krx_chat -f $SQL_FILE"
    exit 1
fi

# Check if database exists
if psql -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
    echo -e "${GREEN}Database '$DB_NAME' already exists${NC}"
else
    echo -e "${YELLOW}Creating database '$DB_NAME'...${NC}"
    createdb "$DB_NAME"
    echo -e "${GREEN}Database created!${NC}"
fi

# Run setup SQL
echo -e "${YELLOW}Running setup SQL script...${NC}"
psql -d "$DB_NAME" -f "$SQL_FILE"

# Verify tables
echo ""
echo -e "${YELLOW}Verifying tables...${NC}"
psql -d "$DB_NAME" -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;"

# Create application user with password
echo ""
echo -e "${YELLOW}Setting up application user...${NC}"
psql -d "$DB_NAME" <<EOF
-- Create application user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'krxchat') THEN
        CREATE ROLE krxchat WITH LOGIN PASSWORD 'krxchat123';
    END IF;
END
\$\$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE krx_chat TO krxchat;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO krxchat;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO krxchat;
GRANT USAGE ON SCHEMA public TO krxchat;

-- Allow future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO krxchat;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO krxchat;

SELECT 'Application user krxchat configured!' AS status;
EOF

echo ""
echo -e "${GREEN}=== Setup Complete! ===${NC}"
echo ""
echo "Database Connection String:"
echo "  postgresql+asyncpg://krxchat:krxchat123@localhost:5432/krx_chat"
echo ""
echo "Next steps:"
echo "1. Create .env file:"
echo "   cp $SCRIPT_DIR/.env.example $SCRIPT_DIR/.env"
echo ""
echo "2. Update .env with:"
echo "   DATABASE_URL=postgresql+asyncpg://krxchat:krxchat123@localhost:5432/krx_chat"
echo "   OPENROUTER_API_KEY=your-api-key"
echo ""
echo "3. Start the backend:"
echo "   cd $SCRIPT_DIR && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
