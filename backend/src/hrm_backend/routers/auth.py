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
from ..models import User

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
        password_hash=hashed_password
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
        "roles": user.role_names
    }}

@router.get("/me", response_model=schemas.UserResponse)
def read_current_user(current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """Get current user information with associated employee if exists"""
    # Fetch the associated employee for this user
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user.user_id).first()
    
    # Get user permissions based on their role(s) - multi-role aware
    user_permissions = current_user.get_all_permissions()
    
    # Create response with employee info and permissions (multi-role system)
    user_data = {
        "user_id": current_user.user_id,
        "username": current_user.username,
        "email": current_user.email,
        "roles": current_user.role_names,
        "permissions": user_permissions,
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
    user_roles = current_user.role_names
    
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
    user_roles = current_user.role_names
    
    # Employee creation page - HR Admin only
    if page_identifier == "employees/create":
        if current_user.has_permission("employee.create"):
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=True, can_delete=False,
                message="User can create employees",
                user_role=",".join(user_roles),
                required_permissions=["employee.create"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="User does not have permission to create employees",
                user_role=",".join(user_roles),
                required_permissions=["employee.create"]
            )
    
    # Departments management - Permission-based access
    elif page_identifier == "departments" or page_identifier.startswith("departments/"):
        can_create = current_user.has_permission("department.create")
        can_update = current_user.has_permission("department.update") 
        can_delete = current_user.has_permission("department.delete")
        can_read = current_user.has_permission("department.read")
        
        if can_read:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=can_update, can_create=can_create, can_delete=can_delete,
                message="User has department access based on permissions",
                user_role=",".join(user_roles),
                required_permissions=["department.read"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="User does not have permission to access departments",
                user_role=",".join(user_roles),
                required_permissions=["department.read"]
            )
    
    # Employee profile pages with specific employee ID
    elif page_identifier == "employees/view" and resource_id:
        employee_id = resource_id
        
        # Check various permission levels
        can_read_all = current_user.has_permission("employee.read.all")
        can_update_all = current_user.has_permission("employee.update.all")
        
        if can_read_all:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=can_update_all, can_create=False, can_delete=False,
                message="User can view all employee profiles",
                user_role=",".join(user_roles),
                required_permissions=["employee.read.all"]
            )
        
        # Check if user owns the employee record
        is_owner = check_employee_ownership(current_user, employee_id, db)
        if is_owner and current_user.has_permission("employee.read.own"):
            can_update_own = current_user.has_permission("employee.update.own")
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=can_update_own, can_create=False, can_delete=False,
                message="Employee can view their own profile",
                user_role=",".join(user_roles),
                required_permissions=["employee.read.own"]
            )
        
        # Check if supervisor has access
        is_supervisor = check_supervisor_relationship(current_user, employee_id, db)
        if is_supervisor and current_user.has_permission("employee.read.supervised"):
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="Supervisor can view supervisee profiles",
                user_role=",".join(user_roles),
                required_permissions=["employee.read.supervised"]
            )
        
        # Default deny
        return schemas.PageAccessPermissions(
            can_view=False, can_edit=False, can_create=False, can_delete=False,
            message="Insufficient permissions to access this employee profile",
            user_role=",".join(user_roles),
            required_permissions=["employee.read.all", "employee.read.own", "employee.read.supervised"]
        )
    
    # Employee edit pages
    elif page_identifier == "employees/edit" and resource_id:
        employee_id = resource_id
        
        # Check if user can edit all employees
        if current_user.has_permission("employee.update.all"):
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="User can edit all employee profiles",
                user_role=",".join(user_roles),
                required_permissions=["employee.update.all"]
            )
        
        # Check if user owns the employee record and can edit own
        is_owner = check_employee_ownership(current_user, employee_id, db)
        if is_owner and current_user.has_permission("employee.update.own"):
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=True, can_create=False, can_delete=False,
                message="Employee can edit their own profile",
                user_role=",".join(user_roles),
                required_permissions=["employee.update.own"]
            )
        
        # Default deny
        return schemas.PageAccessPermissions(
            can_view=False, can_edit=False, can_create=False, can_delete=False,
            message="Insufficient permissions to edit employee profile",
            user_role=",".join(user_roles),
            required_permissions=["employee.update.all", "employee.update.own"]
        )
    
    # Assignment management - Permission-based access
    elif page_identifier == "assignments" or page_identifier.startswith("assignments/create"):
        can_create = current_user.has_permission("assignment.create")
        can_update = current_user.has_permission("assignment.update.all") 
        can_delete = current_user.has_permission("assignment.delete")
        can_read = (current_user.has_permission("assignment.read.all") or 
                   current_user.has_permission("assignment.read.supervised") or
                   current_user.has_permission("assignment.read.own"))
        
        return schemas.PageAccessPermissions(
            can_view=can_read, can_edit=can_update, can_create=can_create, can_delete=can_delete,
            message="Assignment access based on user permissions",
            user_role=",".join(user_roles),
            required_permissions=["assignment.read.*"]
        )
    
    # Profile page - all authenticated users can access their own profile
    elif page_identifier == "profile":
        return schemas.PageAccessPermissions(
            can_view=True, can_edit=True, can_create=False, can_delete=False,
            message="All authenticated users can view and edit their own profile",
            user_role=",".join(user_roles),
            required_permissions=["authenticated"]
        )
    
    # Search page (employee and assignment search) - Permission-based access
    elif page_identifier == "search" or page_identifier == "employees" or page_identifier == "employees/search":
        can_search = current_user.has_permission("employee.search")
        
        if can_search:
            return schemas.PageAccessPermissions(
                can_view=True, can_edit=False, can_create=False, can_delete=False,
                message="User can search employees and assignments",
                user_role=",".join(user_roles),
                required_permissions=["employee.search"]
            )
        else:
            return schemas.PageAccessPermissions(
                can_view=False, can_edit=False, can_create=False, can_delete=False,
                message="User does not have permission to search",
                user_role=",".join(user_roles),
                required_permissions=["employee.search"]
            )
    
    # Default case - authenticated users can view
    else:
        return schemas.PageAccessPermissions(
            can_view=True, can_edit=False, can_create=False, can_delete=False,
            message="Basic page access for authenticated users",
            user_role=",".join(user_roles),
            required_permissions=["authenticated"]
        )