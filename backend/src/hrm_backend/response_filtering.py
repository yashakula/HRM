"""
Permission-Based Response Filtering

This module provides permission-based response filtering and schema selection
to replace the role-based filtering system. It implements granular access control
for sensitive data fields based on user permissions.
"""

from typing import Union, Type, Dict, Any, Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from . import schemas
from .models import User, Employee
from .permission_validation import validate_permission


class PermissionBasedResponseFilter:
    """
    Central class for permission-based response filtering and schema selection
    """
    
    def __init__(self):
        # Permission to schema mapping for employee responses
        self.employee_schema_permissions = {
            "employee.read.all": schemas.EmployeeResponseHR,
            "employee.read.own": schemas.EmployeeResponseOwner,
            "employee.read.supervised": schemas.EmployeeResponseBasic,
        }
        
        # Field-level permission mappings
        self.sensitive_field_permissions = {
            "personal_information.ssn": "employee.read.sensitive",
            "personal_information.bank_account": "employee.read.sensitive", 
            "personal_information.personal_email": "employee.read.personal",
            "person.date_of_birth": "employee.read.personal",
        }
    
    def filter_employee_response(
        self,
        employee_data: Employee,
        current_user: User,
        db: Session
    ) -> Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]:
        """
        Filter employee response based on user permissions instead of roles
        
        Args:
            employee_data: The employee record to filter
            current_user: The user requesting the data
            db: Database session for permission validation
            
        Returns:
            Appropriately filtered employee response schema
        """
        resource_id = employee_data.employee_id
        
        # Check permissions in order of access level (most to least permissive)
        
        # 1. Full access - all employee data
        all_result = validate_permission(
            current_user, "employee.read.all", db, resource_id=resource_id
        )
        if all_result.granted:
            return schemas.EmployeeResponseHR.model_validate(employee_data)
        
        # 2. Own access - sensitive data for own record
        own_result = validate_permission(
            current_user, "employee.read.own", db, resource_id=resource_id
        )
        if own_result.granted:
            return schemas.EmployeeResponseOwner.model_validate(employee_data)
        
        # 3. Supervised access - basic data for supervised employees
        supervised_result = validate_permission(
            current_user, "employee.read.supervised", db, resource_id=resource_id
        )
        if supervised_result.granted:
            return schemas.EmployeeResponseBasic.model_validate(employee_data)
        
        # 4. Fallback - very basic access (public employee directory level)
        # This should rarely be reached due to endpoint-level permission checks
        return schemas.EmployeeResponseBasic.model_validate(employee_data)
    
    def determine_employee_response_schema(
        self,
        current_user: User,
        employee_id: int,
        db: Session
    ) -> Type[BaseModel]:
        """
        Determine which schema class to use based on user permissions
        
        Args:
            current_user: The user requesting the data
            employee_id: ID of the employee being accessed
            db: Database session for permission validation
            
        Returns:
            Appropriate schema class for the user's permission level
        """
        # Check permissions in order of access level
        
        # 1. Full access
        all_result = validate_permission(
            current_user, "employee.read.all", db, resource_id=employee_id
        )
        if all_result.granted:
            return schemas.EmployeeResponseHR
        
        # 2. Own access
        own_result = validate_permission(
            current_user, "employee.read.own", db, resource_id=employee_id
        )
        if own_result.granted:
            return schemas.EmployeeResponseOwner
        
        # 3. Supervised access
        supervised_result = validate_permission(
            current_user, "employee.read.supervised", db, resource_id=employee_id
        )
        if supervised_result.granted:
            return schemas.EmployeeResponseBasic
        
        # 4. Fallback
        return schemas.EmployeeResponseBasic
    
    def filter_field_access(
        self,
        data_dict: Dict[str, Any],
        current_user: User,
        db: Session,
        resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Filter individual fields based on field-level permissions
        
        Args:
            data_dict: Dictionary representation of the data
            current_user: The user requesting the data
            db: Database session for permission validation
            resource_id: ID of the resource being accessed
            
        Returns:
            Filtered dictionary with unauthorized fields removed
        """
        filtered_data = data_dict.copy()
        
        for field_path, required_permission in self.sensitive_field_permissions.items():
            # Check if user has permission for this sensitive field
            result = validate_permission(
                current_user, required_permission, db, resource_id=resource_id
            )
            
            if not result.granted:
                # Remove the sensitive field from response
                self._remove_nested_field(filtered_data, field_path)
        
        return filtered_data
    
    def _remove_nested_field(self, data_dict: Dict[str, Any], field_path: str) -> None:
        """
        Remove a nested field from a dictionary using dot notation
        
        Args:
            data_dict: Dictionary to modify
            field_path: Dot-separated path to the field (e.g., "person.date_of_birth")
        """
        parts = field_path.split(".")
        current = data_dict
        
        # Navigate to the parent of the target field
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                # Path doesn't exist, nothing to remove
                return
        
        # Remove the target field if it exists
        target_field = parts[-1]
        if target_field in current:
            current[target_field] = None  # Set to None instead of deleting key


class PermissionBasedSchemaSelector:
    """
    Schema selection based on user permissions
    """
    
    def __init__(self):
        # Define permission hierarchy for different access levels
        self.access_level_permissions = {
            "full": ["employee.read.all", "assignment.read.all", "leave_request.read.all"],
            "supervised": ["employee.read.supervised", "assignment.read.supervised", "leave_request.read.supervised"],
            "own": ["employee.read.own", "assignment.read.own", "leave_request.read.own"],
            "basic": ["employee.read", "assignment.read", "leave_request.read"]
        }
    
    def get_user_access_level(
        self,
        current_user: User,
        resource_type: str,
        db: Session,
        resource_id: Optional[int] = None
    ) -> str:
        """
        Determine the user's access level for a resource type
        
        Args:
            current_user: The user requesting access
            resource_type: Type of resource (employee, assignment, etc.)
            db: Database session
            resource_id: Optional resource ID for context-aware checking
            
        Returns:
            Access level string: "full", "supervised", "own", or "basic"
        """
        # Check access levels in order of privilege
        for level, permissions in self.access_level_permissions.items():
            for permission in permissions:
                if permission.startswith(resource_type):
                    result = validate_permission(
                        current_user, permission, db, resource_id=resource_id
                    )
                    if result.granted:
                        return level
        
        return "basic"
    
    def select_schema(
        self,
        resource_type: str,
        access_level: str,
        current_user: User,
        db: Session,
        resource_id: Optional[int] = None
    ) -> Type[BaseModel]:
        """
        Select appropriate schema based on resource type and access level
        
        Args:
            resource_type: Type of resource
            access_level: User's access level
            current_user: The user requesting access
            db: Database session
            resource_id: Optional resource ID
            
        Returns:
            Appropriate Pydantic schema class
        """
        if resource_type == "employee":
            return self._select_employee_schema(access_level)
        elif resource_type == "assignment":
            return self._select_assignment_schema(access_level)
        # Add more resource types as needed
        
        # Fallback to basic schema
        return self._get_basic_schema(resource_type)
    
    def _select_employee_schema(self, access_level: str) -> Type[BaseModel]:
        """Select employee schema based on access level"""
        if access_level == "full":
            return schemas.EmployeeResponseHR
        elif access_level in ["supervised", "own"]:
            return schemas.EmployeeResponseOwner if access_level == "own" else schemas.EmployeeResponseBasic
        else:
            return schemas.EmployeeResponseBasic
    
    def _select_assignment_schema(self, access_level: str) -> Type[BaseModel]:
        """Select assignment schema based on access level"""
        # For now, assignments use the same schema regardless of access level
        # This can be extended if needed
        return schemas.AssignmentResponse
    
    def _get_basic_schema(self, resource_type: str) -> Type[BaseModel]:
        """Get basic schema for unknown resource types"""
        # Return a basic schema based on resource type
        schema_mapping = {
            "employee": schemas.EmployeeResponseBasic,
            "assignment": schemas.AssignmentResponse,
            "department": schemas.DepartmentResponse,
        }
        return schema_mapping.get(resource_type, BaseModel)


# Global instances
response_filter = PermissionBasedResponseFilter()
schema_selector = PermissionBasedSchemaSelector()


# Convenience functions for backward compatibility
def filter_employee_response_by_permissions(
    employee_data: Employee,
    current_user: User,
    db: Session
) -> Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]:
    """
    Permission-based employee response filtering (replaces filter_employee_response)
    """
    return response_filter.filter_employee_response(employee_data, current_user, db)


def determine_employee_response_schema_by_permissions(
    current_user: User,
    employee_id: int,
    db: Session
) -> Type[BaseModel]:
    """
    Permission-based schema determination (replaces determine_employee_response_schema)
    """
    return response_filter.determine_employee_response_schema(current_user, employee_id, db)


def filter_response_data_by_permissions(
    data_dict: Dict[str, Any],
    current_user: User,
    db: Session,
    resource_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Field-level permission filtering for response data
    """
    return response_filter.filter_field_access(data_dict, current_user, db, resource_id)