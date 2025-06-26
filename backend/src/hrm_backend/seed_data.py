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

# Standard seed employees (linked to users for proper ownership validation)
SEED_EMPLOYEES = [
    {
        "person": {"full_name": "Alice Johnson", "date_of_birth": "1985-03-15"},
        "personal_information": {
            "personal_email": "alice.johnson@personal.com",
            "ssn": "123-45-6789",
            "bank_account": "ACC123456789"
        },
        "work_email": "alice.johnson@company.com",
        "effective_start_date": "2020-01-15",
        "linked_username": "employee1"  # Links to employee1 user
    },
    {
        "person": {"full_name": "Bob Smith", "date_of_birth": "1990-07-22"},
        "personal_information": {
            "personal_email": "bob.smith@personal.com", 
            "ssn": "234-56-7890",
            "bank_account": "ACC234567890"
        },
        "work_email": "bob.smith@company.com",
        "effective_start_date": "2021-03-01",
        "linked_username": "supervisor1"  # Links to supervisor1 user
    },
    {
        "person": {"full_name": "Charlie Brown", "date_of_birth": "1988-11-08"},
        "personal_information": {
            "personal_email": "charlie.brown@personal.com",
            "ssn": "345-67-8901",
            "bank_account": "ACC345678901"
        },
        "work_email": "charlie.brown@company.com",
        "effective_start_date": "2019-06-10",
        "linked_username": "hr_admin"  # Links to hr_admin user
    },
    {
        "person": {"full_name": "Diana Wilson", "date_of_birth": "1992-04-30"},
        "personal_information": {
            "personal_email": "diana.wilson@personal.com",
            "ssn": "456-78-9012",
            "bank_account": "ACC456789012"
        },
        "work_email": "diana.wilson@company.com", 
        "effective_start_date": "2022-08-15"
        # No linked_username - this employee has no user account
    },
    {
        "person": {"full_name": "Edward Davis", "date_of_birth": "1983-12-03"},
        "personal_information": {
            "personal_email": "edward.davis@personal.com",
            "ssn": "567-89-0123",
            "bank_account": "ACC567890123"
        },
        "work_email": "edward.davis@company.com",
        "effective_start_date": "2018-02-20",
        "effective_end_date": "2023-12-31"  # Inactive employee
        # No linked_username - this employee has no user account
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

# Standard seed assignments (employee -> role mappings)
SEED_ASSIGNMENTS = [
    {"employee_name": "Alice Johnson", "assignment_type": "Senior Software Engineer", "department_name": "Engineering", "supervisor_name": "Bob Smith", "start_date": "2020-01-15"},
    {"employee_name": "Bob Smith", "assignment_type": "Engineering Manager", "department_name": "Engineering", "start_date": "2021-03-01"},
    {"employee_name": "Charlie Brown", "assignment_type": "Marketing Manager", "department_name": "Marketing", "start_date": "2019-06-10"},
    {"employee_name": "Diana Wilson", "assignment_type": "HR Specialist", "department_name": "Human Resources", "supervisor_name": "Charlie Brown", "start_date": "2022-08-15"},
    {"employee_name": "Edward Davis", "assignment_type": "Financial Analyst", "department_name": "Finance", "start_date": "2018-02-20", "end_date": "2023-12-31"},
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
            # Get linked user if specified
            user_id = None
            if emp_data.get("linked_username"):
                linked_user = db.query(models.User).filter(
                    models.User.username == emp_data["linked_username"]
                ).first()
                if linked_user:
                    user_id = linked_user.user_id
                else:
                    logger.warning(f"Linked user not found: {emp_data['linked_username']}")
            
            # Create employee data without linked_username (not part of schema)
            emp_data_clean = {k: v for k, v in emp_data.items() if k != "linked_username"}
            employee_schema = schemas.EmployeeCreate(**emp_data_clean)
            
            # Create employee using existing CRUD function
            db_employee = crud.create_employee(db=db, employee=employee_schema)
            
            # Link to user if specified
            if user_id:
                db_employee.user_id = user_id
                db.commit()
                db.refresh(db_employee)
                logger.info(f"Linked employee {emp_data['person']['full_name']} to user {emp_data['linked_username']}")
            
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

def create_seed_assignments(db: Session) -> list:
    """Create seed assignments (employee-role mappings) if they don't exist"""
    created_assignments = []
    
    for assignment_data in SEED_ASSIGNMENTS:
        # Get employee by name
        employee = db.query(models.Employee).join(models.People).filter(
            models.People.full_name == assignment_data["employee_name"]
        ).first()
        
        if not employee:
            logger.error(f"Employee not found: {assignment_data['employee_name']}")
            continue
        
        # Get assignment type by description and department
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
            logger.error(f"Assignment type not found: {assignment_data['assignment_type']} in {assignment_data['department_name']}")
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
            else:
                logger.warning(f"Supervisor not found: {assignment_data['supervisor_name']}")
        
        # Create assignment schema
        assignment_schema = schemas.AssignmentCreate(
            employee_id=employee.employee_id,
            assignment_type_id=assignment_type.assignment_type_id,
            description=f"{assignment_data['assignment_type']} role",
            effective_start_date=assignment_data["start_date"],
            effective_end_date=assignment_data.get("end_date"),
            supervisor_ids=supervisor_ids
        )
        
        # Create assignment using CRUD function
        try:
            db_assignment = crud.create_assignment(db=db, assignment=assignment_schema)
            created_assignments.append(db_assignment)
            logger.info(f"Created assignment: {assignment_data['employee_name']} -> {assignment_data['assignment_type']}")
        except Exception as e:
            logger.error(f"Error creating assignment for {assignment_data['employee_name']}: {str(e)}")
    
    return created_assignments

def create_all_seed_data(db: Session) -> dict:
    """Create all seed data (users, employees, departments, assignment types, assignments)"""
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
        
        # Create seed assignments (depends on employees and assignment types)
        assignments = create_seed_assignments(db)
        
        result = {
            "users": users,
            "departments": departments,
            "assignment_types": assignment_types,
            "employees": employees,
            "assignments": assignments,
            "success": True,
            "message": f"Seed data created: {len(users)} users, {len(departments)} departments, {len(assignment_types)} assignment types, {len(employees)} employees, {len(assignments)} assignments"
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
            "assignments": [],
            "success": False,
            "error": str(e)
        }

def reset_seed_data(db: Session) -> dict:
    """Delete all seed data and recreate it"""
    logger.info("Resetting seed data...")
    
    try:
        # Delete in reverse dependency order to handle foreign keys
        
        # 1. Delete assignments first (depends on employees and assignment types)
        for assignment_data in SEED_ASSIGNMENTS:
            employee = db.query(models.Employee).join(models.People).filter(
                models.People.full_name == assignment_data["employee_name"]
            ).first()
            if employee:
                # Delete assignments for this employee
                db.query(models.Assignment).filter(
                    models.Assignment.employee_id == employee.employee_id
                ).delete()
        
        # 2. Delete assignment supervisor relationships
        for assignment_data in SEED_ASSIGNMENTS:
            employee = db.query(models.Employee).join(models.People).filter(
                models.People.full_name == assignment_data["employee_name"]
            ).first()
            if employee:
                # This is handled by cascade delete from assignments
                pass
        
        # 3. Delete assignment types
        for at_data in SEED_ASSIGNMENT_TYPES:
            department = db.query(models.Department).filter(
                models.Department.name == at_data["department_name"]
            ).first()
            if department:
                db.query(models.AssignmentType).filter(
                    models.AssignmentType.description == at_data["description"],
                    models.AssignmentType.department_id == department.department_id
                ).delete()
        
        # 4. Delete departments
        for dept_data in SEED_DEPARTMENTS:
            db.query(models.Department).filter(
                models.Department.name == dept_data["name"]
            ).delete()
        
        # 5. Delete employees (and their personal information via cascade)
        for emp_data in SEED_EMPLOYEES:
            employee = db.query(models.Employee).join(models.People).filter(
                models.People.full_name == emp_data["person"]["full_name"]
            ).first()
            if employee:
                # Delete personal information first if it exists
                if employee.person.personal_information:
                    db.delete(employee.person.personal_information)
                # Delete people record (will cascade to employee)
                db.delete(employee.person)
        
        # 6. Delete users last
        for user_data in SEED_USERS:
            db.query(models.User).filter(
                models.User.username == user_data["username"]
            ).delete()
        
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