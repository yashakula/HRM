from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session
from typing import Optional

from .. import schemas
from ..auth import (
    authenticate_user, 
    create_session_token, 
    get_password_hash,
    get_current_active_user,
    get_employee_by_user_id,
    check_employee_ownership,
    check_supervisor_relationship,
    get_cookie_config
)
from ..database import get_db
from .. import models
from ..models import User, UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=schemas.UserResponse)
def register_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (admin only in production)"""
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    
    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login")
def login_user(
    user_credentials: schemas.UserLogin,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login user and set session cookie"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create session token
    session_token = create_session_token(user.user_id)
    
    # Set secure session cookie with environment-aware configuration
    cookie_config = get_cookie_config()
    response.set_cookie(
        key="session_token",
        value=session_token,
        **cookie_config
        # No max_age = session cookie (expires when browser closes)
    )
    
    return {"message": "Login successful", "user": {
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role.value
    }}

@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get current user information with associated employee if exists"""
    # Fetch the associated employee for this user
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user.user_id).first()
    
    # Create response with employee info if available
    user_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "employee": employee
    }
    
    return user_data

@router.post("/logout")
def logout_user(response: Response):
    """Logout user by clearing session cookie"""
    cookie_config = get_cookie_config()
    response.delete_cookie(
        key="session_token",
        **cookie_config
    )
    return {"message": "Successfully logged out"}

@router.post("/validate-page-access", response_model=schemas.PageAccessResponse)
def validate_page_access(
    request: schemas.PageAccessRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate user access permissions for specific pages and resources.
    Returns detailed access information for frontend route protection.
    """
    page_id = request.page_identifier
    resource_id = request.resource_id
    user_role = current_user.role
    
    # Define page access rules
    permissions = _get_page_permissions(page_id, resource_id, current_user, db)
    
    return schemas.PageAccessResponse(
        page_identifier=page_id,
        resource_id=resource_id,
        permissions=permissions,
        access_granted=permissions.can_view
    )

def _get_page_permissions(
    page_identifier: str, 
    resource_id: Optional[int], 
    current_user: User, 
    db: Session
) -> schemas.PageAccessPermissions:
    """
    Internal function to determine user permissions for specific pages.
    Implements comprehensive page-level access control logic.
    """
    user_role = current_user.role
    
    # Employee creation page - HR Admin only
    if page_identifier == "employees/create":
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=True, can_delete=False,
                message="HR Admin can create employees",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="Only HR Admin can create employees",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
    
    # Departments management - HR Admin and Supervisors only
    elif page_identifier == "departments" or page_identifier.startswith("departments/"):
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=True, can_delete=True,
                message="HR Admin has full department management access",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        elif user_role == UserRole.SUPERVISOR:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="Supervisors can view departments",
                user_role=user_role.value,
                required_permissions=["SUPERVISOR"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="Only HR Admin and Supervisors can access departments",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN", "SUPERVISOR"]
            )
    
    # Employee profile pages with specific employee ID
    elif page_identifier == "employees/view" and resource_id:
        employee_id = resource_id
        
        # HR Admin can view any employee
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="HR Admin can view and edit any employee",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        
        # Check if user owns the employee record
        is_owner = check_employee_ownership(current_user, employee_id, db)
        if is_owner:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="Employee can view and edit their own profile",
                user_role=user_role.value,
                required_permissions=["resource_owner"]
            )
        
        # Check if supervisor has access
        if user_role == UserRole.SUPERVISOR:
            is_supervisor = check_supervisor_relationship(current_user, employee_id, db)
            if is_supervisor:
                return schemas.PageAccessPermissions(
                    can_view=True, can_edit=False, can_create=False, can_delete=False,
                    message="Supervisor can view supervisee profiles",
                    user_role=user_role.value,
                    required_permissions=["supervisor"]
                )
        
        # Default deny
        return schemas.PageAccessPermissions(
            can_view=False, can_edit=False, can_create=False, can_delete=False,
            message="Insufficient permissions to access this employee profile",
            user_role=user_role.value,
            required_permissions=["HR_ADMIN", "resource_owner", "supervisor"]
        )
    
    # Employee edit pages
    elif page_identifier == "employees/edit" and resource_id:
        employee_id = resource_id
        
        # HR Admin can edit any employee
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="HR Admin can edit any employee",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        
        # Check if user owns the employee record
        is_owner = check_employee_ownership(current_user, employee_id, db)
        if is_owner:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="Employee can edit their own profile",
                user_role=user_role.value,
                required_permissions=["resource_owner"]
            )
        
        # Supervisors cannot edit employee records
        return schemas.PageAccessPermissions(
            can_view=False, can_edit=False, can_create=False, can_delete=False,
            message="Only HR Admin or employee themselves can edit employee profiles",
            user_role=user_role.value,
            required_permissions=["HR_ADMIN", "resource_owner"]
        )
    
    # Assignment management - HR Admin only
    elif page_identifier == "assignments" or page_identifier.startswith("assignments/create"):
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=True, can_delete=True,
                message="HR Admin has full assignment management access",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="Users can view assignments but cannot manage them",
                user_role=user_role.value,
                required_permissions=["authenticated"]
            )
    
    # Profile page - all authenticated users can access their own profile
    elif page_identifier == "profile":
        return schemas.PageAccessPermissions(
            can_view=True, can_edit=True, can_create=False, can_delete=False,
            message="All authenticated users can view and edit their own profile",
            user_role=user_role.value,
            required_permissions=["authenticated"]
        )
    
    # Search page (employee and assignment search) - HR Admin and Supervisors only  
    elif page_identifier == "search" or page_identifier == "employees" or page_identifier == "employees/search":
        if user_role == UserRole.HR_ADMIN:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="HR Admin can search all employees and assignments",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN"]
            )
        elif user_role == UserRole.SUPERVISOR:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="Supervisors can search employees and assignments",
                user_role=user_role.value,
                required_permissions=["SUPERVISOR"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="Only HR Admin and Supervisors can access search functionality",
                user_role=user_role.value,
                required_permissions=["HR_ADMIN", "SUPERVISOR"]
            )
    
    # Default case - authenticated users can view
    else:
        return schemas.PageAccessPermissions(
            can_view=True, can_edit=False, can_create=False, can_delete=False,
            message="Basic page access for authenticated users",
            user_role=user_role.value,
            required_permissions=["authenticated"]
        )