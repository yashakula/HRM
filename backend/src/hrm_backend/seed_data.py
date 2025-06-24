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

def user_exists(db: Session, username: str) -> bool:
    """Check if a user already exists"""
    return db.query(models.User).filter(models.User.username == username).first() is not None

def employee_exists(db: Session, full_name: str) -> bool:
    """Check if an employee already exists"""
    return db.query(models.Employee).join(models.People).filter(
        models.People.full_name == full_name
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

def create_all_seed_data(db: Session) -> dict:
    """Create all seed data (users and employees)"""
    logger.info("Starting seed data creation...")
    
    try:
        # Create seed users first
        users = create_seed_users(db)
        
        # Create seed employees
        employees = create_seed_employees(db)
        
        result = {
            "users": users,
            "employees": employees,
            "success": True,
            "message": f"Seed data created: {len(users)} users, {len(employees)} employees"
        }
        
        logger.info(result["message"])
        return result
        
    except Exception as e:
        logger.error(f"Error creating seed data: {str(e)}")
        db.rollback()
        return {
            "users": {},
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