# HRM Project Memory

## Project Overview
Human Resource Management (HRM) Software MVP focused on core HR functionalities. This is a greenfield project in early planning phase with no implementation code yet.

## Architecture & Tech Stack
- **Database**: PostgreSQL (containerized for development)
- **Implementation**: Not yet determined - no code files present
- **Development Setup**: Docker PostgreSQL container on port 5432

## Current Project State
- **Phase**: Planning & Design
- **Status**: Pre-implementation
- **Available Artifacts**:
  - MVP Requirements Document
  - Database ERD
  - UI Wireframes (US-01, US-02, US-03, US-05, US-06, US-07, US-08, US-10, US-11, US-12, US-13, US-16)
  - Database setup documentation

## Core Features (MVP Scope)
1. **Employee Management (CRUD)**
   - Create/Read/Update/Deactivate employee profiles
   - Assignment management with supervisor relationships
   - Multiple assignments per employee, one primary assignment

2. **Leave Request & Approval**
   - Employee leave request submission
   - Multi-supervisor approval workflow
   - Automated notifications

3. **Attendance Logging**
   - Check-in/check-out per assignment
   - Hours calculation
   - Reporting for supervisors/HR

## Database Schema Summary
**Core Entities**:
- `PEOPLE` → `PERSONAL_INFORMATION` (1:1)
- `PEOPLE` → `EMPLOYEE` (1:many)
- `EMPLOYEE` → `ASSIGNMENT` (1:many)
- `DEPARTMENT` → `ASSIGNMENT_TYPE` (1:many)
- `ASSIGNMENT_TYPE` → `ASSIGNMENT` (1:many)
- `ASSIGNMENT` → `LEAVE_REQUEST` (1:many)
- `ASSIGNMENT` → `ATTENDANCE` (1:many)
- `ASSIGNMENT` → `COMPENSATION` (1:many)

**Key Relationships**:
- Employees can have multiple assignments
- Leave requests route to all assignment supervisors
- Attendance logged per assignment
- Approval required from all relevant supervisors

## User Roles & Permissions
1. **HR Admin**: Full CRUD access, assignment management, global leave/attendance oversight
2. **Supervisor**: Manage supervisees, approve leave requests, view attendance for assigned employees
3. **Employee**: Submit leave requests, log attendance, manage personal information

## User Stories Implemented
- US-01 to US-16 covering all three user roles
- Focus on CRUD operations, leave workflow, and attendance tracking
- Role-based dashboard views

## Development Environment
```bash
# PostgreSQL Setup
docker run --name my_postgres \
  -e POSTGRES_PASSWORD=mysecretpassword \
  -p 5432:5432 \
  -d postgres

# Database Creation
docker exec -it my_postgres psql -U postgres
create database hrms;
\c hrms
```

## Implementation Progress

### Completed
1. ✅ Develop wireframes and UI prototypes
2. ✅ Choose technology stack (FastAPI + PostgreSQL + UV)
3. ✅ Implement database schema (SQLAlchemy models)
4. ✅ Set up containerization (Docker + docker-compose)
5. ✅ Build testing framework (pytest + httpx)
6. ✅ **US-01: Create Employee Profile** - Complete with API endpoint
7. ✅ **Authentication & RBAC System** - JWT auth with 3 user roles

### Authentication System Features
- JWT token-based authentication with Bearer scheme
- Role-based access control (HR_ADMIN, SUPERVISOR, EMPLOYEE)
- Secure password hashing with bcrypt
- Protected API endpoints with proper 401/403 responses
- User registration, login, and profile endpoints

### Next Steps
1. US-02: Search and view employee records (with role-based filtering)
2. US-13: Define assignments (department/role management) 
3. US-14: Assign employees to assignments
4. Enhanced authentication features (refresh tokens, password reset)

## Files Structure
```
/HRM/
├── MVPRequirementsDocument.md    # Complete feature requirements
├── erd.md                        # Database entity relationship diagram
├── IMPLEMENTATION_LOG.md         # User story implementation tracking
├── CLAUDE.md                     # This memory file
├── Wireframes/                   # UI mockups for user stories
│   ├── Database/Setup.md         # PostgreSQL development setup
│   └── *.png                     # UI wireframes (US-01 through US-16)
├── docker-compose.yml            # Container orchestration
└── backend/                      # FastAPI backend application
    ├── Dockerfile                # Backend container configuration
    ├── pyproject.toml            # UV package management
    ├── src/hrm_backend/          # Application source code
    │   ├── main.py               # FastAPI app entry point
    │   ├── models.py             # SQLAlchemy database models
    │   ├── schemas.py            # Pydantic request/response schemas
    │   ├── database.py           # Database connection & session management
    │   ├── auth.py               # Authentication & authorization logic
    │   ├── crud.py               # Database CRUD operations
    │   └── routers/              # API endpoint routers
    │       ├── auth.py           # Authentication endpoints
    │       └── employees.py      # Employee management endpoints
    └── tests/                    # Test suite
        ├── conftest.py           # Test configuration & fixtures
        ├── test_employees.py     # Employee API tests
        └── test_auth.py          # Authentication tests
```

## Key Technical Considerations
- Multi-supervisor approval workflow complexity
- Assignment-based access control
- Soft delete/deactivation patterns
- Audit trail for employee changes
- Notification system for leave status updates
- Role-based UI rendering

## Security Considerations
- SSN and bank account data protection
- Role-based access control
- Audit logging for sensitive operations
- Input validation and sanitization

This project is well-planned with clear requirements but needs technology stack selection and implementation to begin.