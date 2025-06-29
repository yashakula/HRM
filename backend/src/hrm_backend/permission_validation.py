"""
Permission Validation Logic

This module provides context-aware permission validation that integrates with
existing ownership validation functions while adding enhanced permission capabilities.
"""

import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from enum import Enum
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .models import User, UserRole
from .permission_registry import ROLE_PERMISSIONS
from .auth import (
    check_employee_ownership,
    check_supervisor_relationship, 
    check_assignment_ownership,
    check_assignment_supervisor_relationship
)

# Set up logging for permission debugging
logger = logging.getLogger(__name__)

class PermissionContext(Enum):
    """Defines the context in which permission is being checked"""
    GLOBAL = "global"           # No specific resource context
    RESOURCE_OWNERSHIP = "resource_ownership"    # Checking ownership of a resource
    SUPERVISION = "supervision"  # Checking supervision relationship
    ASSIGNMENT_BASED = "assignment_based"   # Permission based on assignment relationship

class PermissionScope(Enum):
    """Defines the scope of permission access"""
    OWN = "own"                # Access to own resources
    SUPERVISED = "supervised"   # Access to supervised resources  
    ALL = "all"                # Access to all resources
    NONE = "none"              # No access

class PermissionResult:
    """Result of permission validation with debugging information"""
    
    def __init__(self, 
                 granted: bool, 
                 permission: str,
                 user_role: str,
                 context: PermissionContext,
                 reason: str,
                 resource_id: Optional[int] = None,
                 debug_info: Optional[Dict[str, Any]] = None):
        self.granted = granted
        self.permission = permission
        self.user_role = user_role
        self.context = context
        self.reason = reason
        self.resource_id = resource_id
        self.debug_info = debug_info or {}
    
    def __bool__(self) -> bool:
        return self.granted
    
    def __str__(self) -> str:
        status = "GRANTED" if self.granted else "DENIED"
        return f"Permission {status}: {self.permission} for {self.user_role} - {self.reason}"

class PermissionValidator:
    """Enhanced permission validation engine with context awareness"""
    
    def __init__(self, enable_debug: bool = False):
        self.enable_debug = enable_debug
        self.validation_cache = {}  # Simple in-memory cache
    
    def validate_permission(self,
                          user: User,
                          permission: str,
                          db: Session,
                          resource_id: Optional[int] = None,
                          resource_type: Optional[str] = None,
                          **context_data) -> PermissionResult:
        """
        Main permission validation function with context awareness
        
        Args:
            user: The user requesting permission
            permission: Permission string (e.g., "employee.read.own")
            db: Database session
            resource_id: ID of the resource being accessed (optional)
            resource_type: Type of resource (employee, assignment, etc.)
            **context_data: Additional context for validation
        
        Returns:
            PermissionResult with validation outcome and debugging info
        """
        debug_info = {
            "user_id": user.user_id,
            "username": user.username,
            "permission_requested": permission,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "context_data": context_data
        }
        
        if self.enable_debug:
            logger.info(f"Validating permission: {permission} for user {user.username}")
        
        # Step 1: Parse permission format first
        permission_parts = permission.split('.')
        if len(permission_parts) < 2:
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.GLOBAL,
                reason=f"Invalid permission format: {permission}",
                resource_id=resource_id,
                debug_info=debug_info
            )
        
        # Step 2: Check if user has the permission in their role
        if not user.has_permission(permission):
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.GLOBAL,
                reason=f"User roles {','.join(user.role_names)} do not have permission {permission}",
                resource_id=resource_id,
                debug_info=debug_info
            )
        
        resource_name = permission_parts[0]
        action = permission_parts[1]
        scope = permission_parts[2] if len(permission_parts) > 2 else None
        
        debug_info.update({
            "parsed_resource": resource_name,
            "parsed_action": action, 
            "parsed_scope": scope
        })
        
        # Step 3: Handle scope-based validation
        if scope is None:
            # Global permission (no scope restrictions)
            return PermissionResult(
                granted=True,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.GLOBAL,
                reason="Global permission granted",
                resource_id=resource_id,
                debug_info=debug_info
            )
        
        # Step 4: Context-aware validation for scoped permissions
        return self._validate_scoped_permission(
            user, permission, scope, resource_name, resource_id, db, debug_info
        )
    
    def _validate_scoped_permission(self,
                                   user: User,
                                   permission: str,
                                   scope: str,
                                   resource_name: str,
                                   resource_id: Optional[int],
                                   db: Session,
                                   debug_info: Dict[str, Any]) -> PermissionResult:
        """Validate scoped permissions with context awareness"""
        
        if scope == "all":
            # User has access to all resources of this type
            return PermissionResult(
                granted=True,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.GLOBAL,
                reason="Global access permission granted",
                resource_id=resource_id,
                debug_info=debug_info
            )
        
        if resource_id is None:
            # Scoped permission requires resource_id for validation
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.RESOURCE_OWNERSHIP,
                reason=f"Scoped permission {permission} requires resource_id for validation",
                resource_id=resource_id,
                debug_info=debug_info
            )
        
        if scope == "own":
            return self._validate_ownership(user, permission, resource_name, resource_id, db, debug_info)
        elif scope == "supervised":
            return self._validate_supervision(user, permission, resource_name, resource_id, db, debug_info)
        else:
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.GLOBAL,
                reason=f"Unknown permission scope: {scope}",
                resource_id=resource_id,
                debug_info=debug_info
            )
    
    def _validate_ownership(self,
                           user: User,
                           permission: str,
                           resource_name: str,
                           resource_id: int,
                           db: Session,
                           debug_info: Dict[str, Any]) -> PermissionResult:
        """Validate ownership-based permissions"""
        
        try:
            if resource_name == "employee":
                owns_resource = check_employee_ownership(user, resource_id, db)
                debug_info["ownership_check"] = "employee"
            elif resource_name == "assignment":
                owns_resource = check_assignment_ownership(user, resource_id, db)
                debug_info["ownership_check"] = "assignment"
            else:
                # For other resource types, implement as needed
                owns_resource = False
                debug_info["ownership_check"] = f"unsupported_resource_{resource_name}"
            
            debug_info["owns_resource"] = owns_resource
            
            if owns_resource:
                return PermissionResult(
                    granted=True,
                    permission=permission,
                    user_role=",".join(user.role_names),
                    context=PermissionContext.RESOURCE_OWNERSHIP,
                    reason=f"User owns {resource_name} {resource_id}",
                    resource_id=resource_id,
                    debug_info=debug_info
                )
            else:
                return PermissionResult(
                    granted=False,
                    permission=permission,
                    user_role=",".join(user.role_names),
                    context=PermissionContext.RESOURCE_OWNERSHIP,
                    reason=f"User does not own {resource_name} {resource_id}",
                    resource_id=resource_id,
                    debug_info=debug_info
                )
        
        except Exception as e:
            logger.error(f"Error validating ownership for {permission}: {e}")
            debug_info["ownership_error"] = str(e)
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.RESOURCE_OWNERSHIP,
                reason=f"Ownership validation error: {e}",
                resource_id=resource_id,
                debug_info=debug_info
            )
    
    def _validate_supervision(self,
                             user: User,
                             permission: str,
                             resource_name: str,
                             resource_id: int,
                             db: Session,
                             debug_info: Dict[str, Any]) -> PermissionResult:
        """Validate supervision-based permissions"""
        
        try:
            if resource_name == "employee":
                supervises_resource = check_supervisor_relationship(user, resource_id, db)
                debug_info["supervision_check"] = "employee"
            elif resource_name == "assignment":
                supervises_resource = check_assignment_supervisor_relationship(user, resource_id, db)
                debug_info["supervision_check"] = "assignment"
            elif resource_name == "leave_request":
                # For leave requests, need to check if user supervises the associated assignment
                # This would require additional logic to get assignment_id from leave_request_id
                supervises_resource = self._check_leave_request_supervision(user, resource_id, db)
                debug_info["supervision_check"] = "leave_request"
            else:
                supervises_resource = False
                debug_info["supervision_check"] = f"unsupported_resource_{resource_name}"
            
            debug_info["supervises_resource"] = supervises_resource
            
            if supervises_resource:
                return PermissionResult(
                    granted=True,
                    permission=permission,
                    user_role=",".join(user.role_names),
                    context=PermissionContext.SUPERVISION,
                    reason=f"User supervises {resource_name} {resource_id}",
                    resource_id=resource_id,
                    debug_info=debug_info
                )
            else:
                return PermissionResult(
                    granted=False,
                    permission=permission,
                    user_role=",".join(user.role_names),
                    context=PermissionContext.SUPERVISION,
                    reason=f"User does not supervise {resource_name} {resource_id}",
                    resource_id=resource_id,
                    debug_info=debug_info
                )
        
        except Exception as e:
            logger.error(f"Error validating supervision for {permission}: {e}")
            debug_info["supervision_error"] = str(e)
            return PermissionResult(
                granted=False,
                permission=permission,
                user_role=",".join(user.role_names),
                context=PermissionContext.SUPERVISION,
                reason=f"Supervision validation error: {e}",
                resource_id=resource_id,
                debug_info=debug_info
            )
    
    def _check_leave_request_supervision(self, user: User, leave_request_id: int, db: Session) -> bool:
        """Check if user supervises the assignment associated with a leave request"""
        # This would need to be implemented based on your leave request model
        # For now, return False as placeholder
        # TODO: Implement leave request supervision logic
        return False
    
    def validate_any_permission(self,
                              user: User,
                              permissions: List[str],
                              db: Session,
                              resource_id: Optional[int] = None,
                              **context_data) -> PermissionResult:
        """
        Validate that user has ANY of the specified permissions
        
        Returns the result of the first permission that grants access
        """
        debug_info = {
            "permissions_checked": permissions,
            "validation_results": []
        }
        
        for permission in permissions:
            result = self.validate_permission(
                user, permission, db, resource_id, **context_data
            )
            debug_info["validation_results"].append({
                "permission": permission,
                "granted": result.granted,
                "reason": result.reason
            })
            
            if result.granted:
                result.debug_info.update(debug_info)
                return result
        
        # No permissions granted
        return PermissionResult(
            granted=False,
            permission=f"any_of_{permissions}",
            user_role=",".join(user.role_names),
            context=PermissionContext.GLOBAL,
            reason=f"User does not have any of the required permissions: {permissions}",
            resource_id=resource_id,
            debug_info=debug_info
        )
    
    def validate_all_permissions(self,
                               user: User,
                               permissions: List[str],
                               db: Session,
                               resource_id: Optional[int] = None,
                               **context_data) -> PermissionResult:
        """
        Validate that user has ALL of the specified permissions
        
        Returns success only if all permissions are granted
        """
        debug_info = {
            "permissions_checked": permissions,
            "validation_results": []
        }
        
        for permission in permissions:
            result = self.validate_permission(
                user, permission, db, resource_id, **context_data
            )
            debug_info["validation_results"].append({
                "permission": permission,
                "granted": result.granted,
                "reason": result.reason
            })
            
            if not result.granted:
                result.debug_info.update(debug_info)
                return result
        
        # All permissions granted
        return PermissionResult(
            granted=True,
            permission=f"all_of_{permissions}",
            user_role=",".join(user.role_names),
            context=PermissionContext.GLOBAL,
            reason=f"User has all required permissions: {permissions}",
            resource_id=resource_id,
            debug_info=debug_info
        )

# Global validator instance
permission_validator = PermissionValidator()

# Convenience functions for common use cases
def validate_permission(user: User, 
                       permission: str, 
                       db: Session,
                       resource_id: Optional[int] = None,
                       **context_data) -> PermissionResult:
    """Convenience function for single permission validation"""
    return permission_validator.validate_permission(
        user, permission, db, resource_id, **context_data
    )

def validate_any_permission(user: User,
                          permissions: List[str],
                          db: Session, 
                          resource_id: Optional[int] = None,
                          **context_data) -> PermissionResult:
    """Convenience function for any permission validation"""
    return permission_validator.validate_any_permission(
        user, permissions, db, resource_id, **context_data
    )

def validate_all_permissions(user: User,
                           permissions: List[str],
                           db: Session,
                           resource_id: Optional[int] = None,
                           **context_data) -> PermissionResult:
    """Convenience function for all permissions validation"""
    return permission_validator.validate_all_permissions(
        user, permissions, db, resource_id, **context_data
    )

def create_permission_error_response(result: PermissionResult) -> HTTPException:
    """Create standardized HTTP error response for permission denial"""
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "Permission denied",
            "permission": result.permission,
            "reason": result.reason,
            "required_role": "Contact administrator for access",
            "user_role": result.user_role,
            "context": result.context.value if result.context else None,
            "debug_info": result.debug_info if permission_validator.enable_debug else None
        }
    )

# Enhanced User model methods (to be integrated into models.py)
def enhance_user_with_context_validation(user_class):
    """Add context-aware validation methods to User model"""
    
    def has_permission_with_context(self, 
                                   permission: str, 
                                   db: Session,
                                   resource_id: Optional[int] = None,
                                   **context_data) -> bool:
        """Enhanced permission checking with context awareness"""
        result = validate_permission(self, permission, db, resource_id, **context_data)
        return result.granted
    
    def has_any_permission_with_context(self,
                                       permissions: List[str],
                                       db: Session,
                                       resource_id: Optional[int] = None,
                                       **context_data) -> bool:
        """Enhanced any permission checking with context awareness"""
        result = validate_any_permission(self, permissions, db, resource_id, **context_data)
        return result.granted
    
    def has_all_permissions_with_context(self,
                                        permissions: List[str],
                                        db: Session,
                                        resource_id: Optional[int] = None,
                                        **context_data) -> bool:
        """Enhanced all permissions checking with context awareness"""
        result = validate_all_permissions(self, permissions, db, resource_id, **context_data)
        return result.granted
    
    # Add methods to User class
    user_class.has_permission_with_context = has_permission_with_context
    user_class.has_any_permission_with_context = has_any_permission_with_context
    user_class.has_all_permissions_with_context = has_all_permissions_with_context
    
    return user_class