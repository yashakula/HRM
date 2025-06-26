# HRM Database Seeding Guide

## Overview

Your HRM system has a comprehensive, elegant database seeding solution that creates realistic test data for development and testing.

## What Gets Seeded

### 👥 Users (3)
- **HR Admin**: `hr_admin` / `admin123` (Full system access)
- **Supervisor**: `supervisor1` / `super123` (Team management)  
- **Employee**: `employee1` / `emp123` (Self-service access)

### 🏢 Departments (5)
- Engineering (Software development and technical infrastructure)
- Marketing (Product marketing and customer acquisition)
- Human Resources (People operations and talent management)
- Finance (Financial planning and accounting)
- Operations (Business operations and logistics)

### 👔 Assignment Types (15)
Realistic job roles across all departments:
- **Engineering**: Software Engineer, Senior Software Engineer, Engineering Manager, DevOps Engineer
- **Marketing**: Marketing Specialist, Marketing Manager, Content Creator
- **HR**: HR Specialist, HR Manager, Recruiter
- **Finance**: Financial Analyst, Accountant, Finance Manager
- **Operations**: Operations Coordinator, Operations Manager

### 👤 Employees (5)
- Alice Johnson (Senior Software Engineer, supervised by Bob Smith)
- Bob Smith (Engineering Manager)
- Charlie Brown (Marketing Manager)
- Diana Wilson (HR Specialist, supervised by Charlie Brown)
- Edward Davis (Financial Analyst, assignment ended)

### 📋 Assignments (5)
Employee-role mappings with supervisor relationships:
- Realistic effective dates
- Some with end dates (terminated assignments)
- Proper supervisor hierarchies

## How to Use

### Quick Commands

```bash
# Use the CLI wrapper from project root (RECOMMENDED)
python seed_db.py seed   # Create seed data
python seed_db.py reset  # Delete and recreate all data
python seed_db.py help   # Show usage info
```

**Note**: Always use `python seed_db.py` from the project root, not the internal script directly.

### Automatic Seeding

Seed data is automatically created when the backend starts (controlled by `CREATE_SEED_DATA` environment variable).

### Manual Seeding

Use the provided CLI wrapper from the project root:

```bash
# Make sure containers are running (only database required)
docker-compose up -d

# Seed the database using the wrapper script
python seed_db.py seed
```

**Important**: 
- Run `python seed_db.py` from the project root directory
- The script automatically checks if containers are running
- It handles all Docker container orchestration for you

## Testing Different Scenarios

### Filter Testing
With the seeded data, you can test assignment filtering by:
- **Department**: Engineering, Marketing, HR, Finance, Operations
- **Assignment Type**: Any of the 15 different roles
- **Employee Name**: Search for "Alice", "Bob", "Charlie", etc.

### Role-Based Access Testing
Login with different user roles to test access control:
- **HR Admin**: Can create/edit employees, manage all assignments
- **Supervisor**: Can view assignments, limited editing rights
- **Employee**: Read-only access to directory

### Assignment Management Testing
The seeded assignments include:
- Active assignments (ongoing roles)
- Ended assignments (historical data)
- Supervisor relationships
- Cross-department scenarios

## Implementation Details

### Seeding Architecture
The HRM seeding system uses a two-file architecture for optimal user experience:

1. **`/seed_db.py` (Recommended Interface)**
   - **Purpose**: User-friendly CLI wrapper for the project root
   - **Usage**: `python seed_db.py [seed|reset|help]` 
   - **Function**: Orchestrates Docker container execution
   - **Benefits**: Easy to use, handles container management automatically

2. **`/backend/scripts/seed_database.py` (Implementation)**
   - **Purpose**: Actual seeding script with database operations
   - **Function**: Direct SQLAlchemy operations, no FastAPI dependencies
   - **Execution**: Runs inside Docker container via the wrapper
   - **Benefits**: Self-contained, proper dependency isolation

### How It Works
```bash
# When you run this from project root:
python seed_db.py seed

# It internally executes:
docker-compose exec backend uv run python scripts/seed_database.py seed
```

### Why This Architecture?
- **User-Friendly**: Simple commands from project root
- **Container-Aware**: Automatically handles Docker execution
- **Environment Isolation**: Runs with proper UV dependencies inside container
- **Error Handling**: Checks container status and provides helpful messages

### Smart Seeding
- **Idempotent**: Only creates data that doesn't already exist
- **Dependency Aware**: Creates data in proper order (users → departments → assignment types → employees → assignments)
- **Comprehensive**: Covers all major entities and relationships

### Reset Capability
- **Clean Reset**: Properly handles foreign key constraints
- **Complete Recreation**: Ensures fresh, consistent data
- **No Orphaned Data**: Careful deletion order prevents constraint violations

## Benefits

✅ **Realistic Data**: Representative of actual HR scenarios  
✅ **Comprehensive Coverage**: All user stories and features testable  
✅ **Easy Management**: Simple commands for seeding/resetting  
✅ **Development Ready**: Perfect for testing filtering, search, and CRUD operations  
✅ **Role Testing**: Multiple user types with proper access control  
✅ **Relationship Testing**: Complex supervisor/assignment hierarchies  
✅ **Direct Database Access**: No web server dependency, faster execution  
✅ **Container Integration**: Runs seamlessly in Docker environment  

This seeding system eliminates the need for manual data entry during development and provides a consistent baseline for testing all features of your HRM system.