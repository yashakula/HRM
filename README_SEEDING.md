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
# Easy seeding with the CLI script (NEW: Direct database access)
python seed_db.py seed   # Create seed data
python seed_db.py reset  # Delete and recreate all data
python seed_db.py help   # Show usage info
```

### Automatic Seeding

Seed data is automatically created when the backend starts (controlled by `CREATE_SEED_DATA` environment variable).

### Manual Seeding

Use the provided CLI script for the easiest experience:

```bash
# Make sure containers are running (only database required)
docker-compose up -d

# Seed the database (runs directly in Docker container)
python seed_db.py seed
```

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

### Seed Data Location
- **Configuration**: `/backend/scripts/seed_database.py` (standalone script)
- **Management**: Auto-startup + Direct database CLI script

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