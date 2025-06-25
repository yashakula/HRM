"""
Seed data management for HRM application.
Creates consistent test data for development and testing.
"""

from sqlalchemy.orm import Session
from . import models, crud, schemas
from .auth import get_password_hash
import logging

logger = logging.getLogger(__name__)

# Standard seed users
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

# Standard seed employees
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

# Standard seed departments
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

# Standard seed assignment types
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

def user_exists(db: Session, username: str) -> bool:
    """Check if a user already exists"""
    return db.query(models.User).filter(models.User.username == username).first() is not None

def employee_exists(db: Session, full_name: str) -> bool:
    """Check if an employee already exists"""
    return db.query(models.Employee).join(models.People).filter(
        models.People.full_name == full_name
    ).first() is not None

def department_exists(db: Session, name: str) -> bool:
    """Check if a department already exists"""
    return db.query(models.Department).filter(models.Department.name == name).first() is not None

def assignment_type_exists(db: Session, description: str, department_id: int) -> bool:
    """Check if an assignment type already exists for a department"""
    return db.query(models.AssignmentType).filter(
        models.AssignmentType.description == description,
        models.AssignmentType.department_id == department_id
    ).first() is not None

def create_seed_users(db: Session) -> dict:
    """Create seed users if they don't exist"""
    created_users = {}
    
    for user_data in SEED_USERS:
        if not user_exists(db, user_data["username"]):
            # Create user directly (bypassing API authentication)
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
            # Get existing user
            existing_user = db.query(models.User).filter(
                models.User.username == user_data["username"]
            ).first()
            created_users[user_data["username"]] = existing_user
            logger.info(f"Seed user already exists: {user_data['username']}")
    
    return created_users

def create_seed_employees(db: Session) -> list:
    """Create seed employees if they don't exist"""
    created_employees = []
    
    for emp_data in SEED_EMPLOYEES:
        if not employee_exists(db, emp_data["person"]["full_name"]):
            # Convert to Pydantic schema
            employee_schema = schemas.EmployeeCreate(**emp_data)
            
            # Create employee using existing CRUD function
            db_employee = crud.create_employee(db=db, employee=employee_schema)
            created_employees.append(db_employee)
            logger.info(f"Created seed employee: {emp_data['person']['full_name']}")
        else:
            # Get existing employee
            existing_employee = db.query(models.Employee).join(models.People).filter(
                models.People.full_name == emp_data["person"]["full_name"]
            ).first()
            created_employees.append(existing_employee)
            logger.info(f"Seed employee already exists: {emp_data['person']['full_name']}")
    
    return created_employees

def create_seed_departments(db: Session) -> list:
    """Create seed departments if they don't exist"""
    created_departments = []
    
    for dept_data in SEED_DEPARTMENTS:
        if not department_exists(db, dept_data["name"]):
            # Convert to Pydantic schema
            department_schema = schemas.DepartmentCreate(**dept_data)
            
            # Create department using CRUD function
            db_department = crud.create_department(db=db, department=department_schema)
            created_departments.append(db_department)
            logger.info(f"Created seed department: {dept_data['name']}")
        else:
            # Get existing department
            existing_department = db.query(models.Department).filter(
                models.Department.name == dept_data["name"]
            ).first()
            created_departments.append(existing_department)
            logger.info(f"Seed department already exists: {dept_data['name']}")
    
    return created_departments

def create_seed_assignment_types(db: Session) -> list:
    """Create seed assignment types if they don't exist"""
    created_assignment_types = []
    
    for at_data in SEED_ASSIGNMENT_TYPES:
        # Get department by name
        department = db.query(models.Department).filter(
            models.Department.name == at_data["department_name"]
        ).first()
        
        if not department:
            logger.error(f"Department not found: {at_data['department_name']}")
            continue
            
        if not assignment_type_exists(db, at_data["description"], department.department_id):
            # Convert to Pydantic schema
            assignment_type_schema = schemas.AssignmentTypeCreate(
                description=at_data["description"],
                department_id=department.department_id
            )
            
            # Create assignment type using CRUD function
            db_assignment_type = crud.create_assignment_type(db=db, assignment_type=assignment_type_schema)
            created_assignment_types.append(db_assignment_type)
            logger.info(f"Created seed assignment type: {at_data['description']} in {at_data['department_name']}")
        else:
            # Get existing assignment type
            existing_assignment_type = db.query(models.AssignmentType).filter(
                models.AssignmentType.description == at_data["description"],
                models.AssignmentType.department_id == department.department_id
            ).first()
            created_assignment_types.append(existing_assignment_type)
            logger.info(f"Seed assignment type already exists: {at_data['description']}")
    
    return created_assignment_types

def create_all_seed_data(db: Session) -> dict:
    """Create all seed data (users, employees, departments, assignment types)"""
    logger.info("Starting seed data creation...")
    
    try:
        # Create seed users first
        users = create_seed_users(db)
        
        # Create seed departments
        departments = create_seed_departments(db)
        
        # Create seed assignment types (depends on departments)
        assignment_types = create_seed_assignment_types(db)
        
        # Create seed employees
        employees = create_seed_employees(db)
        
        result = {
            "users": users,
            "departments": departments,
            "assignment_types": assignment_types,
            "employees": employees,
            "success": True,
            "message": f"Seed data created: {len(users)} users, {len(departments)} departments, {len(assignment_types)} assignment types, {len(employees)} employees"
        }
        
        logger.info(result["message"])
        return result
        
    except Exception as e:
        logger.error(f"Error creating seed data: {str(e)}")
        db.rollback()
        return {
            "users": {},
            "departments": [],
            "assignment_types": [],
            "employees": [],
            "success": False,
            "error": str(e)
        }

def reset_seed_data(db: Session) -> dict:
    """Delete all seed data and recreate it"""
    logger.info("Resetting seed data...")
    
    try:
        # Delete seed employees first (due to foreign key constraints)
        for emp_data in SEED_EMPLOYEES:
            db.query(models.Employee).join(models.People).filter(
                models.People.full_name == emp_data["person"]["full_name"]
            ).delete(synchronize_session=False)
        
        # Delete associated people records
        for emp_data in SEED_EMPLOYEES:
            db.query(models.People).filter(
                models.People.full_name == emp_data["person"]["full_name"]
            ).delete(synchronize_session=False)
        
        # Delete seed users
        for user_data in SEED_USERS:
            db.query(models.User).filter(
                models.User.username == user_data["username"]
            ).delete(synchronize_session=False)
        
        db.commit()
        logger.info("Seed data deleted")
        
        # Recreate seed data
        return create_all_seed_data(db)
        
    except Exception as e:
        logger.error(f"Error resetting seed data: {str(e)}")
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

# Utility functions for tests
def get_seed_user_credentials(username: str) -> dict:
    """Get login credentials for seed users"""
    user_data = next((u for u in SEED_USERS if u["username"] == username), None)
    if user_data:
        return {
            "username": user_data["username"],
            "password": user_data["password"]
        }
    return None

def get_seed_employee_by_name(name: str) -> dict:
    """Get seed employee data by name"""
    return next((emp for emp in SEED_EMPLOYEES if emp["person"]["full_name"] == name), None)