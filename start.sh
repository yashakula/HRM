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
if ! docker ps | grep -q hrm-postgres; then
    echo "Starting PostgreSQL container..."
    docker run --name hrm-postgres \
        -e POSTGRES_PASSWORD=mysecretpassword \
        -e POSTGRES_DB=hrms \
        -p 5432:5432 \
        -d postgres:15 2>/dev/null || docker start hrm-postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
else
    echo "PostgreSQL is already running"
fi
echo -e "${GREEN}✓ PostgreSQL ready${NC}"
echo ""

# Seed roles and permissions
echo -e "${BLUE}[2/6] Seeding roles...${NC}"
cd backend
uv run python scripts/seed_roles.py
echo -e "${GREEN}✓ Roles seeded${NC}"
echo ""

echo -e "${BLUE}[3/6] Seeding permissions...${NC}"
uv run python scripts/seed_permissions.py
echo -e "${GREEN}✓ Permissions seeded${NC}"
echo ""

# Start backend
echo -e "${BLUE}[4/6] Starting backend server...${NC}"
uv run uvicorn hrm_backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
cd ..
sleep 3
echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
echo ""

# Install frontend dependencies and start
echo -e "${BLUE}[5/6] Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    bun install
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Start frontend
echo -e "${BLUE}[6/6] Starting frontend server...${NC}"
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
