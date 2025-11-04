#!/bin/bash

echo "🛑 Stopping HRM Application..."
echo ""

# Kill processes on ports 3000 and 8000
echo "Stopping frontend (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || echo "Frontend not running"

echo "Stopping backend (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "Backend not running"

echo ""
echo "✓ All services stopped"
echo ""
echo "Note: PostgreSQL service is still running in the background."
echo "To stop it: brew services stop postgresql@15"
