# HRM - Human Resource Management System

A modern HRM system built with Next.js (frontend with Bun) and FastAPI (backend).

## 🚀 Quick Start

### Prerequisites
- [Bun](https://bun.sh) v1.0+ installed
- [Python](https://python.org) 3.11+ with [uv](https://github.com/astral-sh/uv) installed
- [PostgreSQL](https://www.postgresql.org/) 15+ installed (via Homebrew recommended)

### Starting the Application

**One command to start everything:**
```bash
./start.sh
```

The startup script automatically:
1. ✅ Checks if PostgreSQL service is running, starts it if needed
2. ✅ Creates the `hrms` database if it doesn't exist
3. ✅ Seeds roles and permissions (idempotent - won't duplicate data)
4. ✅ Starts the backend API server (FastAPI with hot reload on port 8000)
5. ✅ Installs frontend dependencies if needed
6. ✅ Starts the frontend dev server (Bun + Next.js with Turbopack on port 3000)

**You'll see output like this:**
```
🚀 Starting HRM Application...

[1/5] Checking PostgreSQL...
✓ PostgreSQL ready

[2/5] Seeding permissions...
✓ Permissions seeded

[3/5] Starting backend server...
✓ Backend started on http://localhost:8000

[4/5] Installing frontend dependencies...
✓ Dependencies installed

[5/5] Starting frontend server...
✓ Frontend started on http://localhost:3000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎉 HRM Application is running!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Frontend: http://localhost:3000
🔧 Backend API: http://localhost:8000
📊 API Docs: http://localhost:8000/docs
🐘 Database: localhost:5432
```

### Access Points

Once started, you can access:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **PostgreSQL Database**: localhost:5432

### Demo Accounts

Log in with any of these pre-configured accounts:

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| super_user | superuser123 | Super User | Full system access + user management |
| hr_admin | admin123 | HR Admin | Employee & department management |
| supervisor1 | super123 | Supervisor | Approve leave, view supervised employees |
| employee1 | emp123 | Employee | Submit leave, view personal info |

### Stopping the Application

**Stop frontend and backend servers:**
```bash
./stop.sh
```

This will:
- Stop the frontend dev server (port 3000)
- Stop the backend API server (port 8000)
- Keep PostgreSQL service running (for faster restarts)

**To also stop PostgreSQL:**
```bash
brew services stop postgresql@15
```

**To access the database directly:**
```bash
psql hrms
```

### Troubleshooting

**Ports already in use:**
```bash
# Check what's using port 3000 or 8000
lsof -i :3000
lsof -i :8000

# Kill processes on those ports
./stop.sh
```

**PostgreSQL won't start:**
```bash
# Check PostgreSQL service status
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15

# Check PostgreSQL logs
tail -f /opt/homebrew/var/log/postgresql@15.log
```

**Database connection errors:**
```bash
# Check if database exists
psql -l | grep hrms

# Recreate database if needed
dropdb hrms && createdb hrms
./start.sh
```

**PostgreSQL not installed:**
```bash
# Install via Homebrew
brew install postgresql@15

# Start service
brew services start postgresql@15
```

## 📁 Project Structure

```
HRM/
├── backend/          # FastAPI backend
│   ├── src/         # Source code
│   ├── scripts/     # Database seeding scripts
│   └── tests/       # Test suite
├── frontend/         # Next.js frontend (with Bun)
│   ├── src/         # Source code
│   └── public/      # Static assets
├── start.sh          # Startup script
└── stop.sh           # Shutdown script
```

## 🛠 Development

### Backend Development

```bash
cd backend
uv run uvicorn hrm_backend.main:app --reload
```

### Frontend Development

```bash
cd frontend
bun dev
```

### Running Tests

Backend tests:
```bash
cd backend
uv run pytest
```

## 🗄 Database

The application uses PostgreSQL 15 installed natively via Homebrew.

**Connection Details:**
- Host: localhost
- Port: 5432
- Database: hrms
- Username: (your system username)
- Password: (none by default)

**Database location:** `/opt/homebrew/var/postgresql@15/`

To connect directly:
```bash
psql hrms
```

**Useful commands:**
```bash
# List all databases
psql -l

# Backup database
pg_dump hrms > backup.sql

# Restore database
psql hrms < backup.sql

# View database size
psql hrms -c "SELECT pg_size_pretty(pg_database_size('hrms'));"
```

## 📝 Environment Variables

### Backend (`.env`)
```
DATABASE_URL=postgresql://localhost:5432/hrms
CREATE_SEED_DATA=true
DEBUG=true
BACKEND_CORS_ORIGINS=http://localhost:3000
```

### Frontend (`.env.local`)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🎨 Tech Stack

### Frontend
- **Framework**: Next.js 15.3.4 (App Router)
- **Runtime**: Bun 1.x
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x
- **State Management**: Zustand
- **Data Fetching**: TanStack Query (React Query)
- **Forms**: React Hook Form + Zod
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy
- **Database**: PostgreSQL 15
- **Authentication**: Session-based with HTTP-only cookies
- **Password Hashing**: bcrypt
- **Testing**: pytest
- **Package Manager**: uv

## 🔒 Security

- Session-based authentication with HTTP-only cookies
- Role-based access control (RBAC)
- Secure password hashing with bcrypt
- CORS protection
- Input validation with Pydantic/Zod

## 📚 Features

### Core Functionality
- ✅ Employee Management (CRUD)
- ✅ Department Management
- ✅ Assignment Management
- ✅ Leave Request System
- ✅ Approval Workflow
- ✅ Role-Based Permissions
- ✅ User Authentication

### User Roles
- **Super User**: Full system access + user management
- **HR Admin**: Employee management, department management
- **Supervisor**: Approve leave requests, view supervised employees
- **Employee**: Submit leave requests, view personal information

## 🚧 Development Notes

This is an active development project using native PostgreSQL for faster local development. The startup script handles all database initialization automatically.

**Why native PostgreSQL?**
- ✅ Faster than Docker (no container overhead)
- ✅ Easier database management (native tools)
- ✅ Persistent data by default
- ✅ Better performance for local dev
- ✅ No Docker daemon required

## 📄 License

Private project - All rights reserved
