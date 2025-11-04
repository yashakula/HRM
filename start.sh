#!/bin/bash

set -e  # Exit on error

echo "🚀 Starting HRM Application..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo -e "${BLUE}[1/5] Checking PostgreSQL...${NC}"
if ! brew services list | grep postgresql@15 | grep -q started; then
    echo "Starting PostgreSQL service..."
    brew services start postgresql@15
    echo "Waiting for PostgreSQL to be ready..."
    sleep 3
else
    echo "PostgreSQL is already running"
fi

# Verify database exists
if ! /opt/homebrew/opt/postgresql@15/bin/psql -lqt | cut -d \| -f 1 | grep -qw hrms; then
    echo "Creating hrms database..."
    /opt/homebrew/opt/postgresql@15/bin/createdb hrms
fi
echo -e "${GREEN}✓ PostgreSQL ready${NC}"
echo ""

# Create database tables
echo -e "${BLUE}[2/7] Creating database tables...${NC}"
cd backend
uv run python -c "from hrm_backend.database import create_tables; create_tables()"
echo -e "${GREEN}✓ Tables created${NC}"
echo ""

# Seed roles and permissions
echo -e "${BLUE}[3/7] Seeding roles...${NC}"
uv run python scripts/seed_roles.py
echo -e "${GREEN}✓ Roles seeded${NC}"
echo ""

echo -e "${BLUE}[4/7] Seeding permissions...${NC}"
uv run python scripts/seed_permissions.py
echo -e "${GREEN}✓ Permissions seeded${NC}"
echo ""

# Start backend
echo -e "${BLUE}[5/7] Starting backend server...${NC}"
uv run uvicorn hrm_backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..
sleep 3
echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
echo ""

# Install frontend dependencies and start
echo -e "${BLUE}[6/7] Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    bun install
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Start frontend
echo -e "${BLUE}[7/7] Starting frontend server...${NC}"
bun dev &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"
cd ..
sleep 3
echo -e "${GREEN}✓ Frontend started on http://localhost:3000${NC}"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🎉 HRM Application is running!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🐘 Database: localhost:5432"
echo ""
echo -e "${YELLOW}Demo Accounts:${NC}"
echo "  • Super User: super_user / superuser123"
echo "  • HR Admin: hr_admin / admin123"
echo "  • Supervisor: supervisor1 / super123"
echo "  • Employee: employee1 / emp123"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
