"""
Permission-Based Decorators

This module provides permission-based decorators that integrate with the
Enhanced Permission System while maintaining backward compatibility.
"""

import functools
import inspect
from typing import List, Union, Optional, Callable, Any
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .models import User
from .auth import get_current_active_user
from .database import get_db
from .permission_validation import (
    validate_permission,
    validate_any_permission,
    validate_all_permissions,
    create_permission_error_response,
    PermissionResult
)

def require_permission(permission: str, 
                      resource_id_param: Optional[str] = None,
                      resource_type: Optional[str] = None):
    """
    Decorator to require a specific permission for endpoint access
    
    Args:
        permission: Permission string (e.g., "employee.create", "employee.read.own")
        resource_id_param: Parameter name that contains the resource ID (e.g., "employee_id")
        resource_type: Type of resource for context (e.g., "employee", "assignment")
    
    Usage:
        @require_permission("employee.create")
        def create_employee(employee_data: schemas.EmployeeCreate, ...):
            
        @require_permission("employee.read.own", resource_id_param="employee_id")
        def get_employee(employee_id: int, current_user: User = Depends(get_current_active_user), ...):
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _permission_wrapper(
                func, permission, resource_id_param, resource_type, args, kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _permission_wrapper(
                func, permission, resource_id_param, resource_type, args, kwargs
            )
        
        # Return appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def require_any_permission(permissions: List[str],
                          resource_id_param: Optional[str] = None,
                          resource_type: Optional[str] = None):
    """
    Decorator to require ANY of the specified permissions for endpoint access
    
    Args:
        permissions: List of permission strings
        resource_id_param: Parameter name that contains the resource ID
        resource_type: Type of resource for context
    
    Usage:
        @require_any_permission(["employee.read.own", "employee.read.supervised", "employee.read.all"])
        def get_employee(employee_id: int, ...):
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _any_permission_wrapper(
                func, permissions, resource_id_param, resource_type, args, kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _any_permission_wrapper(
                func, permissions, resource_id_param, resource_type, args, kwargs
            )
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def require_all_permissions(permissions: List[str],
                           resource_id_param: Optional[str] = None,
                           resource_type: Optional[str] = None):
    """
    Decorator to require ALL of the specified permissions for endpoint access
    
    Args:
        permissions: List of permission strings
        resource_id_param: Parameter name that contains the resource ID
        resource_type: Type of resource for context
    
    Usage:
        @require_all_permissions(["employee.read.own", "employee.update.own"])
        def update_employee(employee_id: int, ...):
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _all_permissions_wrapper(
                func, permissions, resource_id_param, resource_type, args, kwargs
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _all_permissions_wrapper(
                func, permissions, resource_id_param, resource_type, args, kwargs
            )
        
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _extract_dependencies(func: Callable, args: tuple, kwargs: dict) -> tuple[User, Session, dict]:
    """
    Extract current_user, db, and resource_id from function arguments
    
    This function handles FastAPI's dependency injection by extracting
    the required dependencies from the function's arguments.
    """
    sig = inspect.signature(func)
    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()
    
    current_user = None
    db = None
    
    # Extract current_user and db from function arguments
    for param_name, param_value in bound_args.arguments.items():
        param = sig.parameters[param_name]
        
        # Check if this parameter is a User dependency
        if isinstance(param_value, User):
            current_user = param_value
        # Check if this parameter is a Session dependency
        elif isinstance(param_value, Session):
            db = param_value
        # Check if parameter has Depends annotation for User
        elif (hasattr(param, 'default') and 
              hasattr(param.default, 'dependency') and 
              param.default.dependency == get_current_active_user):
            # This will be injected by FastAPI
            continue
        # Check if parameter has Depends annotation for DB
        elif (hasattr(param, 'default') and 
              hasattr(param.default, 'dependency') and 
              param.default.dependency == get_db):
            # This will be injected by FastAPI
            continue
    
    # If dependencies not found in bound args, they should be injected by FastAPI
    # We'll need to handle this at the FastAPI level
    if current_user is None or db is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission decorator requires current_user and db dependencies"
        )
    
    return current_user, db, bound_args.arguments

def _get_resource_id(resource_id_param: Optional[str], bound_arguments: dict) -> Optional[int]:
    """Extract resource ID from function arguments"""
    if resource_id_param and resource_id_param in bound_arguments:
        resource_id = bound_arguments[resource_id_param]
        if isinstance(resource_id, int):
            return resource_id
        elif isinstance(resource_id, str) and resource_id.isdigit():
            return int(resource_id)
    return None

def _permission_wrapper(func: Callable,
                       permission: str,
                       resource_id_param: Optional[str],
                       resource_type: Optional[str],
                       args: tuple,
                       kwargs: dict) -> Any:
    """Core permission validation wrapper"""
    current_user, db, bound_arguments = _extract_dependencies(func, args, kwargs)
    resource_id = _get_resource_id(resource_id_param, bound_arguments)
    
    result = validate_permission(
        current_user, 
        permission, 
        db, 
        resource_id=resource_id,
        resource_type=resource_type
    )
    
    if not result.granted:
        raise create_permission_error_response(result)
    
    return func(*args, **kwargs)

def _any_permission_wrapper(func: Callable,
                           permissions: List[str],
                           resource_id_param: Optional[str],
                           resource_type: Optional[str],
                           args: tuple,
                           kwargs: dict) -> Any:
    """Core any permission validation wrapper"""
    current_user, db, bound_arguments = _extract_dependencies(func, args, kwargs)
    resource_id = _get_resource_id(resource_id_param, bound_arguments)
    
    result = validate_any_permission(
        current_user,
        permissions,
        db,
        resource_id=resource_id,
        resource_type=resource_type
    )
    
    if not result.granted:
        raise create_permission_error_response(result)
    
    return func(*args, **kwargs)

def _all_permissions_wrapper(func: Callable,
                            permissions: List[str],
                            resource_id_param: Optional[str],
                            resource_type: Optional[str],
                            args: tuple,
                            kwargs: dict) -> Any:
    """Core all permissions validation wrapper"""
    current_user, db, bound_arguments = _extract_dependencies(func, args, kwargs)
    resource_id = _get_resource_id(resource_id_param, bound_arguments)
    
    result = validate_all_permissions(
        current_user,
        permissions,
        db,
        resource_id=resource_id,
        resource_type=resource_type
    )
    
    if not result.granted:
        raise create_permission_error_response(result)
    
    return func(*args, **kwargs)

# FastAPI-specific decorators that handle dependency injection properly
def fastapi_require_permission(permission: str,
                              resource_id_param: Optional[str] = None,
                              resource_type: Optional[str] = None):
    """
    FastAPI-specific permission decorator that properly handles dependency injection
    
    This decorator should be used with FastAPI endpoints that use Depends() for
    current_user and db dependencies.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(
            *args,
            current_user: User = Depends(get_current_active_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            # Get resource_id from kwargs if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            # Validate permission
            result = validate_permission(
                current_user,
                permission,
                db,
                resource_id=resource_id,
                resource_type=resource_type
            )
            
            if not result.granted:
                raise create_permission_error_response(result)
            
            # Call original function with all arguments including injected dependencies
            return func(*args, current_user=current_user, db=db, **kwargs)
        
        return wrapper
    return decorator

def fastapi_require_any_permission(permissions: List[str],
                                  resource_id_param: Optional[str] = None,
                                  resource_type: Optional[str] = None):
    """FastAPI-specific any permission decorator"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(
            *args,
            current_user: User = Depends(get_current_active_user),
            db: Session = Depends(get_db),
            **kwargs
        ):
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = kwargs[resource_id_param]
            
            result = validate_any_permission(
                current_user,
                permissions,
                db,
                resource_id=resource_id,
                resource_type=resource_type
            )
            
            if not result.granted:
                raise create_permission_error_response(result)
            
            return func(*args, current_user=current_user, db=db, **kwargs)
        
        return wrapper
    return decorator

# Backward compatibility decorators that wrap existing role-based decorators
def permission_compatible_hr_admin():
    """
    Backward compatible decorator that can be used as drop-in replacement for require_hr_admin
    
    This uses permission checking but falls back to role checking for compatibility
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(
            current_user: User = Depends(get_current_active_user),
            **kwargs
        ):
            # Check if user has HR admin permissions
            if (current_user.role.value == "HR_ADMIN" or 
                current_user.has_permission("user.manage")):
                return func(current_user=current_user, **kwargs)
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. HR Admin permissions required."
                )
        return wrapper
    return decorator

def permission_compatible_supervisor_or_admin():
    """Backward compatible decorator for supervisor or admin access"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(
            current_user: User = Depends(get_current_active_user),
            **kwargs
        ):
            # Check if user has supervisor or admin permissions
            if (current_user.role.value in ["SUPERVISOR", "HR_ADMIN"] or
                current_user.has_any_permission(["employee.read.supervised", "employee.read.all"])):
                return func(current_user=current_user, **kwargs)
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied. Supervisor or Admin permissions required."
                )
        return wrapper
    return decorator