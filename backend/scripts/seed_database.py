#!/usr/bin/env python3
"""
Standalone database seeding script for HRM system.
Connects directly to PostgreSQL database without requiring FastAPI server.

Usage:
    python scripts/seed_database.py seed    # Create seed data
    python scripts/seed_database.py reset   # Delete and recreate all seed data
    python scripts/seed_database.py help    # Show usage information
"""

import sys
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the src directory to Python path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hrm_backend.database import get_database_url
from hrm_backend.models import Base
from hrm_backend import models, crud, schemas

# Import password hashing directly without FastAPI dependencies
from passlib.context import CryptContext

# Password hashing configuration (same as auth.py)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

# Seed data definitions (copied from seed_data.py to avoid FastAPI imports)
SEED_USERS = [
    {
        "username": "hr_admin",
        "email": "hr.admin@company.com", 
        "password": "admin123",
        "role": models.UserRole.HR_ADMIN
    },
    {
        "username": "supervisor1",
        "email": "supervisor1@company.com",
        "password": "super123", 
        "role": models.UserRole.SUPERVISOR
    },
    {
        "username": "employee1",
        "email": "employee1@company.com",
        "password": "emp123",
        "role": models.UserRole.EMPLOYEE
    }
]

SEED_EMPLOYEES = [
    {
        "person": {"full_name": "Alice Johnson", "date_of_birth": "1985-03-15"},
        "personal_information": {
            "personal_email": "alice.johnson@personal.com",
            "ssn": "123-45-6789"
        },
        "work_email": "alice.johnson@company.com",
        "effective_start_date": "2020-01-15"
    },
    {
        "person": {"full_name": "Bob Smith", "date_of_birth": "1990-07-22"},
        "personal_information": {
            "personal_email": "bob.smith@personal.com", 
            "ssn": "234-56-7890"
        },
        "work_email": "bob.smith@company.com",
        "effective_start_date": "2021-03-01"
    },
    {
        "person": {"full_name": "Charlie Brown", "date_of_birth": "1988-11-08"},
        "work_email": "charlie.brown@company.com",
        "effective_start_date": "2019-06-10"
    },
    {
        "person": {"full_name": "Diana Wilson", "date_of_birth": "1992-04-30"},
        "personal_information": {
            "personal_email": "diana.wilson@personal.com",
            "bank_account": "ACC789012345"
        },
        "work_email": "diana.wilson@company.com", 
        "effective_start_date": "2022-08-15"
    },
    {
        "person": {"full_name": "Edward Davis", "date_of_birth": "1983-12-03"},
        "work_email": "edward.davis@company.com",
        "effective_start_date": "2018-02-20",
        "effective_end_date": "2023-12-31"  # Inactive employee
    }
]

SEED_DEPARTMENTS = [
    {
        "name": "Engineering",
        "description": "Software development and technical infrastructure"
    },
    {
        "name": "Marketing",
        "description": "Product marketing and customer acquisition"
    },
    {
        "name": "Human Resources",
        "description": "People operations and talent management"
    },
    {
        "name": "Finance",
        "description": "Financial planning and accounting"
    },
    {
        "name": "Operations",
        "description": "Business operations and logistics"
    }
]

SEED_ASSIGNMENT_TYPES = [
    # Engineering roles
    {"description": "Software Engineer", "department_name": "Engineering"},
    {"description": "Senior Software Engineer", "department_name": "Engineering"},
    {"description": "Engineering Manager", "department_name": "Engineering"},
    {"description": "DevOps Engineer", "department_name": "Engineering"},
    
    # Marketing roles
    {"description": "Marketing Specialist", "department_name": "Marketing"},
    {"description": "Marketing Manager", "department_name": "Marketing"},
    {"description": "Content Creator", "department_name": "Marketing"},
    
    # HR roles
    {"description": "HR Specialist", "department_name": "Human Resources"},
    {"description": "HR Manager", "department_name": "Human Resources"},
    {"description": "Recruiter", "department_name": "Human Resources"},
    
    # Finance roles
    {"description": "Financial Analyst", "department_name": "Finance"},
    {"description": "Accountant", "department_name": "Finance"},
    {"description": "Finance Manager", "department_name": "Finance"},
    
    # Operations roles
    {"description": "Operations Coordinator", "department_name": "Operations"},
    {"description": "Operations Manager", "department_name": "Operations"},
]

SEED_ASSIGNMENTS = [
    {"employee_name": "Alice Johnson", "assignment_type": "Senior Software Engineer", "department_name": "Engineering", "supervisor_name": "Bob Smith", "start_date": "2020-01-15"},
    {"employee_name": "Bob Smith", "assignment_type": "Engineering Manager", "department_name": "Engineering", "start_date": "2021-03-01"},
    {"employee_name": "Charlie Brown", "assignment_type": "Marketing Manager", "department_name": "Marketing", "start_date": "2019-06-10"},
    {"employee_name": "Diana Wilson", "assignment_type": "HR Specialist", "department_name": "Human Resources", "supervisor_name": "Charlie Brown", "start_date": "2022-08-15"},
    {"employee_name": "Edward Davis", "assignment_type": "Financial Analyst", "department_name": "Finance", "start_date": "2018-02-20", "end_date": "2023-12-31"},
]

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database_session():
    """Create a direct database session"""
    try:
        # Get database URL from environment (same as main app)
        database_url = get_database_url()
        logger.info(f"Connecting to database...")
        
        # Create engine and session
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        return SessionLocal()
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        logger.error("Make sure the database container is running: docker-compose up -d database")
        return None

def create_seed_users(db):
    """Create seed users if they don't exist"""
    created_users = {}
    
    for user_data in SEED_USERS:
        existing_user = db.query(models.User).filter(models.User.username == user_data["username"]).first()
        if not existing_user:
            # Create user directly
            hashed_password = get_password_hash(user_data["password"])
            db_user = models.User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hashed_password,
                role=user_data["role"]
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            created_users[user_data["username"]] = db_user
            logger.info(f"Created seed user: {user_data['username']}")
        else:
            created_users[user_data["username"]] = existing_user
            logger.info(f"Seed user already exists: {user_data['username']}")
    
    return created_users

def create_seed_departments(db):
    """Create seed departments if they don't exist"""
    created_departments = []
    
    for dept_data in SEED_DEPARTMENTS:
        existing_dept = db.query(models.Department).filter(models.Department.name == dept_data["name"]).first()
        if not existing_dept:
            department_schema = schemas.DepartmentCreate(**dept_data)
            db_department = crud.create_department(db=db, department=department_schema)
            created_departments.append(db_department)
            logger.info(f"Created seed department: {dept_data['name']}")
        else:
            created_departments.append(existing_dept)
            logger.info(f"Seed department already exists: {dept_data['name']}")
    
    return created_departments

def create_seed_assignment_types(db):
    """Create seed assignment types if they don't exist"""
    created_assignment_types = []
    
    for at_data in SEED_ASSIGNMENT_TYPES:
        department = db.query(models.Department).filter(
            models.Department.name == at_data["department_name"]
        ).first()
        
        if not department:
            logger.error(f"Department not found: {at_data['department_name']}")
            continue
            
        existing_at = db.query(models.AssignmentType).filter(
            models.AssignmentType.description == at_data["description"],
            models.AssignmentType.department_id == department.department_id
        ).first()
        
        if not existing_at:
            assignment_type_schema = schemas.AssignmentTypeCreate(
                description=at_data["description"],
                department_id=department.department_id
            )
            db_assignment_type = crud.create_assignment_type(db=db, assignment_type=assignment_type_schema)
            created_assignment_types.append(db_assignment_type)
            logger.info(f"Created assignment type: {at_data['description']} in {at_data['department_name']}")
        else:
            created_assignment_types.append(existing_at)
            logger.info(f"Assignment type already exists: {at_data['description']}")
    
    return created_assignment_types

def create_seed_employees(db):
    """Create seed employees if they don't exist"""
    created_employees = []
    
    for emp_data in SEED_EMPLOYEES:
        existing_emp = db.query(models.Employee).join(models.People).filter(
            models.People.full_name == emp_data["person"]["full_name"]
        ).first()
        
        if not existing_emp:
            employee_schema = schemas.EmployeeCreate(**emp_data)
            db_employee = crud.create_employee(db=db, employee=employee_schema)
            created_employees.append(db_employee)
            logger.info(f"Created seed employee: {emp_data['person']['full_name']}")
        else:
            created_employees.append(existing_emp)
            logger.info(f"Seed employee already exists: {emp_data['person']['full_name']}")
    
    return created_employees

def create_seed_assignments(db):
    """Create seed assignments if they don't exist"""
    created_assignments = []
    
    for assignment_data in SEED_ASSIGNMENTS:
        # Get employee by name
        employee = db.query(models.Employee).join(models.People).filter(
            models.People.full_name == assignment_data["employee_name"]
        ).first()
        
        if not employee:
            logger.error(f"Employee not found: {assignment_data['employee_name']}")
            continue
        
        # Get assignment type
        department = db.query(models.Department).filter(
            models.Department.name == assignment_data["department_name"]
        ).first()
        
        if not department:
            logger.error(f"Department not found: {assignment_data['department_name']}")
            continue
            
        assignment_type = db.query(models.AssignmentType).filter(
            models.AssignmentType.description == assignment_data["assignment_type"],
            models.AssignmentType.department_id == department.department_id
        ).first()
        
        if not assignment_type:
            logger.error(f"Assignment type not found: {assignment_data['assignment_type']}")
            continue
        
        # Check if assignment already exists
        existing_assignment = db.query(models.Assignment).filter(
            models.Assignment.employee_id == employee.employee_id,
            models.Assignment.assignment_type_id == assignment_type.assignment_type_id
        ).first()
        
        if existing_assignment:
            logger.info(f"Assignment already exists: {assignment_data['employee_name']} -> {assignment_data['assignment_type']}")
            created_assignments.append(existing_assignment)
            continue
        
        # Get supervisor if specified
        supervisor_ids = []
        if assignment_data.get("supervisor_name"):
            supervisor = db.query(models.Employee).join(models.People).filter(
                models.People.full_name == assignment_data["supervisor_name"]
            ).first()
            if supervisor:
                supervisor_ids = [supervisor.employee_id]
        
        # Create assignment
        assignment_schema = schemas.AssignmentCreate(
            employee_id=employee.employee_id,
            assignment_type_id=assignment_type.assignment_type_id,
            description=f"{assignment_data['assignment_type']} role",
            effective_start_date=assignment_data["start_date"],
            effective_end_date=assignment_data.get("end_date"),
            supervisor_ids=supervisor_ids
        )
        
        try:
            db_assignment = crud.create_assignment(db=db, assignment=assignment_schema)
            created_assignments.append(db_assignment)
            logger.info(f"Created assignment: {assignment_data['employee_name']} -> {assignment_data['assignment_type']}")
        except Exception as e:
            logger.error(f"Error creating assignment for {assignment_data['employee_name']}: {str(e)}")
    
    return created_assignments

def seed_database():
    """Create seed data"""
    logger.info("🌱 Starting database seeding...")
    
    db = create_database_session()
    if not db:
        return False
    
    try:
        # Create seed data in proper order
        users = create_seed_users(db)
        departments = create_seed_departments(db)
        assignment_types = create_seed_assignment_types(db)
        employees = create_seed_employees(db)
        assignments = create_seed_assignments(db)
        
        message = f"Seed data created: {len(users)} users, {len(departments)} departments, {len(assignment_types)} assignment types, {len(employees)} employees, {len(assignments)} assignments"
        logger.info(f"✅ {message}")
        return True
            
    except Exception as e:
        logger.error(f"❌ Seeding failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def reset_database():
    """Reset (delete and recreate) seed data"""
    logger.info("🔄 Starting database reset...")
    
    db = create_database_session()
    if not db:
        return False
    
    try:
        # Delete all seed data (simple approach - delete all records matching seed criteria)
        logger.info("Deleting existing seed data...")
        
        # Just delete all records that match our seed data, in any order
        # SQLAlchemy/PostgreSQL will handle cascades properly
        
        # Delete all seed users by username
        for user_data in SEED_USERS:
            db.query(models.User).filter(
                models.User.username == user_data["username"]
            ).delete()
        
        # Delete all seed employees by name (will cascade to assignments)
        for emp_data in SEED_EMPLOYEES:
            people_record = db.query(models.People).filter(
                models.People.full_name == emp_data["person"]["full_name"]
            ).first()
            if people_record:
                db.delete(people_record)  # Will cascade to employee and assignments
        
        # Delete all seed departments by name (will cascade to assignment types)
        for dept_data in SEED_DEPARTMENTS:
            department = db.query(models.Department).filter(
                models.Department.name == dept_data["name"]
            ).first()
            if department:
                db.delete(department)  # Will cascade to assignment types and assignments
        
        db.commit()
        logger.info("Seed data deleted")
        
        # Recreate seed data
        return seed_database()
        
    except Exception as e:
        logger.error(f"❌ Reset failed: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

def show_help():
    """Show usage information"""
    print("""
HRM Database Seeding Tool
========================

Usage:
  python scripts/seed_database.py [command]

Commands:
  seed      Create seed data (if not exists)
  reset     Delete and recreate all seed data
  help      Show this help message

Seed Data Includes:
  👥 3 Users: hr_admin, supervisor1, employee1
  🏢 5 Departments: Engineering, Marketing, HR, Finance, Operations  
  👔 15 Assignment Types: Various roles across departments
  👤 5 Employees: Sample employee profiles
  📋 5 Assignments: Employee-role mappings with supervisors

Login Credentials:
  HR Admin:    hr_admin / admin123
  Supervisor:  supervisor1 / super123  
  Employee:    employee1 / emp123

Requirements:
  - Database container must be running: docker-compose up -d database
  - No need for backend/frontend containers to be running

Environment Variables:
  DATABASE_URL (optional) - Override default database connection
  POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB (default values)
""")

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        command = "help"
    else:
        command = sys.argv[1].lower()
    
    if command == "seed":
        success = seed_database()
        sys.exit(0 if success else 1)
    elif command == "reset":
        success = reset_database()
        sys.exit(0 if success else 1)
    elif command in ["help", "-h", "--help"]:
        show_help()
        sys.exit(0)
    else:
        logger.error(f"❌ Unknown command: {command}")
        show_help()
        sys.exit(1)

if __name__ == "__main__":
    main()