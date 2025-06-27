from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status, Request, Response
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
import secrets
import functools

from .database import get_db
from .models import User, UserRole, Employee, Assignment, AssignmentSupervisor, People, PersonalInformation
from . import schemas

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
SESSION_EXPIRE_HOURS = 24

# Cookie configuration (environment-aware for tunnel deployment)
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")
COOKIE_DOMAIN = os.getenv("COOKIE_DOMAIN", None)
TUNNEL_MODE = os.getenv("TUNNEL_MODE", "false").lower() == "true"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session serializer
session_serializer = URLSafeTimedSerializer(SECRET_KEY)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_session_token(user_id: int) -> str:
    """Create signed session token"""
    return session_serializer.dumps({"user_id": user_id, "created_at": datetime.utcnow().isoformat()})

def verify_session_token(token: str) -> Optional[dict]:
    """Verify and decode session token"""
    try:
        # Verify signature and expiry (24 hours)
        data = session_serializer.loads(token, max_age=SESSION_EXPIRE_HOURS * 3600)
        return data
    except (BadSignature, SignatureExpired):
        return None

def get_cookie_config() -> dict:
    """Get environment-aware cookie configuration"""
    config = {
        "httponly": True,
        "secure": COOKIE_SECURE,
        "samesite": COOKIE_SAMESITE
    }
    
    # Add domain if specified (for tunnel deployment)
    if COOKIE_DOMAIN:
        config["domain"] = COOKIE_DOMAIN
    
    # In tunnel mode, ensure secure and samesite=none for cross-origin
    if TUNNEL_MODE:
        config["secure"] = True
        config["samesite"] = "none"
    
    return config

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username, User.is_active == True).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.user_id == user_id, User.is_active == True).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Authenticate user with username and password"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current authenticated user from session"""
    # Check for session token in cookies
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Verify session token
    session_data = verify_session_token(session_token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    # Get user from database
    user = get_user_by_id(db, session_data["user_id"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Role-based access control decorators
def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}"
            )
        return current_user
    return role_checker

def require_hr_admin():
    """Require HR Admin role"""
    return require_role(UserRole.HR_ADMIN)

def require_supervisor_or_admin():
    """Require Supervisor or HR Admin role"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.SUPERVISOR, UserRole.HR_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required role: Supervisor or HR Admin"
            )
        return current_user
    return role_checker

def require_employee_or_admin():
    """Require Employee or HR Admin role (for personal data access)"""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in [UserRole.EMPLOYEE, UserRole.HR_ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Required role: Employee or HR Admin"
            )
        return current_user
    return role_checker

# Response filtering utility functions
def get_employee_by_user_id(db: Session, user_id: int) -> Optional[Employee]:
    """Query employee table by user relationship"""
    return db.query(Employee).options(
        joinedload(Employee.person).joinedload(People.personal_information)
    ).filter(Employee.user_id == user_id).first()

def check_employee_ownership(current_user: User, employee_id: int, db: Session) -> bool:
    """Check if current user owns the employee record"""
    if current_user.role == UserRole.HR_ADMIN:
        return True  # HR_ADMIN can access any record
    
    user_employee = get_employee_by_user_id(db, current_user.user_id)
    if user_employee and user_employee.employee_id == employee_id:
        return True  # User owns this employee record
    
    return False

def check_supervisor_relationship(current_user: User, employee_id: int, db: Session) -> bool:
    """Check if supervisor has authority over the specified employee"""
    if current_user.role != UserRole.SUPERVISOR:
        return False
    
    # Get supervisor's employee record
    supervisor_employee = get_employee_by_user_id(db, current_user.user_id)
    if not supervisor_employee:
        return False
    
    # Check if supervisor supervises any of the target employee's assignments
    assignment = db.query(Assignment).join(AssignmentSupervisor).filter(
        Assignment.employee_id == employee_id,
        AssignmentSupervisor.supervisor_id == supervisor_employee.employee_id
    ).first()
    
    return assignment is not None

def filter_employee_response(
    employee_data: Employee, 
    current_user: User, 
    db: Session
) -> Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]:
    """
    Central filtering function that returns appropriately filtered employee response
    based on user role and ownership
    """
    # HR_ADMIN gets full access
    if current_user.role == UserRole.HR_ADMIN:
        return schemas.EmployeeResponseHR.model_validate(employee_data)
    
    # Check if user owns the employee record
    is_owner = check_employee_ownership(current_user, employee_data.employee_id, db)
    if is_owner:
        return schemas.EmployeeResponseOwner.model_validate(employee_data)
    
    # Check if supervisor has access (optional - for viewing only)
    is_supervisor = check_supervisor_relationship(current_user, employee_data.employee_id, db)
    if is_supervisor:
        return schemas.EmployeeResponseBasic.model_validate(employee_data)
    
    # Default to basic schema for all other cases
    return schemas.EmployeeResponseBasic.model_validate(employee_data)

def determine_employee_response_schema(
    current_user: User, 
    employee_id: int, 
    db: Session
) -> type:
    """
    Helper function to determine which schema class to use based on user role and ownership
    """
    # HR_ADMIN gets full access
    if current_user.role == UserRole.HR_ADMIN:
        return schemas.EmployeeResponseHR
    
    # Check ownership
    is_owner = check_employee_ownership(current_user, employee_id, db)
    if is_owner:
        return schemas.EmployeeResponseOwner
    
    # Check supervisor relationship
    is_supervisor = check_supervisor_relationship(current_user, employee_id, db)
    if is_supervisor:
        return schemas.EmployeeResponseBasic
    
    # Default to basic schema
    return schemas.EmployeeResponseBasic

# Ownership validation middleware
def create_access_denied_response(resource_type: str, resource_id: int, user_role: str) -> HTTPException:
    """Create standardized access denied HTTP exception"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "Access Denied",
            "message": f"Insufficient permissions to access {resource_type} {resource_id}",
            "user_role": user_role,
            "required_permissions": ["HR_ADMIN", "resource_owner", "supervisor"]
        }
    )

def validate_employee_access(allow_supervisor_access: bool = False):
    """
    Decorator to validate employee access based on ownership and role.
    
    Args:
        allow_supervisor_access: If True, supervisors can access their supervisees' records
    
    Returns:
        Decorator function that validates employee access
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract employee_id from function arguments
            employee_id = kwargs.get('employee_id')
            if employee_id is None:
                # Try to find it in args (positional arguments)
                for arg in args:
                    if isinstance(arg, int):
                        employee_id = arg
                        break
            
            if employee_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Employee ID not found in request"
                )
            
            # Get current user (should be injected via dependency)
            current_user = kwargs.get('current_user')
            if current_user is None:
                # Look for it in function arguments
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get database session
            db = kwargs.get('db')
            if db is None:
                # Look for it in function arguments
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # HR_ADMIN can access any record
            if current_user.role == UserRole.HR_ADMIN:
                return await func(*args, **kwargs)
            
            # Check if user owns the employee record
            if check_employee_ownership(current_user, employee_id, db):
                return await func(*args, **kwargs)
            
            # Check supervisor access if allowed
            if allow_supervisor_access and current_user.role == UserRole.SUPERVISOR:
                if check_supervisor_relationship(current_user, employee_id, db):
                    return await func(*args, **kwargs)
            
            # Return 403 Forbidden using standardized response
            raise create_access_denied_response("employee", employee_id, current_user.role.value)
        
        return wrapper
    return decorator

# Assignment access control functions
def check_assignment_ownership(current_user: User, assignment_id: int, db: Session) -> bool:
    """Check if current user owns the assignment record (is the assigned employee)"""
    if current_user.role == UserRole.HR_ADMIN:
        return True  # HR_ADMIN can access any assignment
    
    # Get user's employee record
    user_employee = get_employee_by_user_id(db, current_user.user_id)
    if not user_employee:
        return False
    
    # Check if the user is the assigned employee for this assignment
    assignment = db.query(Assignment).filter(
        Assignment.assignment_id == assignment_id,
        Assignment.employee_id == user_employee.employee_id
    ).first()
    
    return assignment is not None

def check_assignment_supervisor_relationship(current_user: User, assignment_id: int, db: Session) -> bool:
    """Check if current user is a supervisor of the specified assignment"""
    if current_user.role != UserRole.SUPERVISOR:
        return False
    
    # Get supervisor's employee record
    supervisor_employee = get_employee_by_user_id(db, current_user.user_id)
    if not supervisor_employee:
        return False
    
    # Check if supervisor supervises this assignment
    assignment_supervisor = db.query(AssignmentSupervisor).filter(
        AssignmentSupervisor.assignment_id == assignment_id,
        AssignmentSupervisor.supervisor_id == supervisor_employee.employee_id
    ).first()
    
    return assignment_supervisor is not None

def validate_assignment_access(allow_supervisor_access: bool = False):
    """
    Decorator to validate assignment access based on ownership and role.
    
    Args:
        allow_supervisor_access: If True, supervisors can access assignments they supervise
    
    Returns:
        Decorator function that validates assignment access
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract assignment_id from function arguments
            assignment_id = kwargs.get('assignment_id')
            if assignment_id is None:
                # Try to find it in args (positional arguments)
                for arg in args:
                    if isinstance(arg, int):
                        assignment_id = arg
                        break
            
            if assignment_id is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignment ID not found in request"
                )
            
            # Get current user (should be injected via dependency)
            current_user = kwargs.get('current_user')
            if current_user is None:
                # Look for it in function arguments
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
            
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Get database session
            db = kwargs.get('db')
            if db is None:
                # Look for it in function arguments
                for arg in args:
                    if isinstance(arg, Session):
                        db = arg
                        break
            
            if db is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database session not available"
                )
            
            # HR_ADMIN can access any assignment
            if current_user.role == UserRole.HR_ADMIN:
                return await func(*args, **kwargs)
            
            # Check if user owns the assignment (is the assigned employee)
            if check_assignment_ownership(current_user, assignment_id, db):
                return await func(*args, **kwargs)
            
            # Check supervisor access if allowed
            if allow_supervisor_access and current_user.role == UserRole.SUPERVISOR:
                if check_assignment_supervisor_relationship(current_user, assignment_id, db):
                    return await func(*args, **kwargs)
            
            # Return 403 Forbidden using standardized response
            raise create_access_denied_response("assignment", assignment_id, current_user.role.value)
        
        return wrapper
    return decorator

def filter_assignments_by_role(current_user: User, db: Session, assignments: list) -> list:
    """
    Filter assignment list based on user role and relationships.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        assignments: List of assignment objects to filter
    
    Returns:
        Filtered list of assignments the user is authorized to see
    """
    # HR_ADMIN can see all assignments
    if current_user.role == UserRole.HR_ADMIN:
        return assignments
    
    # Get user's employee record
    user_employee = get_employee_by_user_id(db, current_user.user_id)
    if not user_employee:
        return []  # User has no employee record, cannot see any assignments
    
    filtered_assignments = []
    
    for assignment in assignments:
        # Employee can see their own assignments
        if assignment.employee_id == user_employee.employee_id:
            filtered_assignments.append(assignment)
            continue
        
        # Supervisor can see assignments they supervise
        if current_user.role == UserRole.SUPERVISOR:
            is_supervisor = db.query(AssignmentSupervisor).filter(
                AssignmentSupervisor.assignment_id == assignment.assignment_id,
                AssignmentSupervisor.supervisor_id == user_employee.employee_id
            ).first()
            
            if is_supervisor:
                filtered_assignments.append(assignment)
    
    return filtered_assignments