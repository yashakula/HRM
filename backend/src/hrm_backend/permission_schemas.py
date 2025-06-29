"""
Permission-Aware Response Schemas

This module provides enhanced response schemas that support permission-based
field filtering and dynamic data serialization based on user permissions.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List, Union
from datetime import date, datetime

from .models import EmployeeStatus, UserRole, LeaveStatus


class PermissionAwareBaseModel(BaseModel):
    """
    Base model that supports permission-based field filtering
    """
    
    class Config:
        from_attributes = True
        # Allow extra fields for dynamic filtering
        extra = "allow"
    
    def filter_by_permissions(
        self, 
        user_permissions: List[str], 
        field_permission_map: Dict[str, str]
    ) -> "PermissionAwareBaseModel":
        """
        Filter fields based on user permissions
        
        Args:
            user_permissions: List of permissions the user has
            field_permission_map: Mapping of field names to required permissions
            
        Returns:
            New instance with filtered fields
        """
        # Get current data as dict
        data = self.model_dump()
        
        # Filter fields based on permissions
        for field_name, required_permission in field_permission_map.items():
            if required_permission not in user_permissions:
                # Remove or null the field if user doesn't have permission
                if "." in field_name:
                    # Handle nested fields
                    self._remove_nested_field(data, field_name)
                else:
                    # Remove top-level field
                    data.pop(field_name, None)
        
        # Return new instance with filtered data
        return self.__class__(**data)
    
    def _remove_nested_field(self, data: Dict[str, Any], field_path: str) -> None:
        """Remove nested field using dot notation"""
        parts = field_path.split(".")
        current = data
        
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                return
        
        target_field = parts[-1]
        current.pop(target_field, None)


class PermissionAwarePersonalInformation(PermissionAwareBaseModel):
    """Personal information with permission-aware field filtering"""
    personal_email: Optional[str] = None
    ssn: Optional[str] = None
    bank_account: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Permission requirements for sensitive fields
    _field_permissions = {
        "ssn": "employee.read.sensitive",
        "bank_account": "employee.read.sensitive",
        "personal_email": "employee.read.personal"
    }


class PermissionAwarePerson(PermissionAwareBaseModel):
    """Person information with permission-aware filtering"""
    people_id: int
    full_name: str
    date_of_birth: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    personal_information: Optional[PermissionAwarePersonalInformation] = None
    
    # Permission requirements
    _field_permissions = {
        "date_of_birth": "employee.read.personal",
        "personal_information": "employee.read.personal"
    }


class PermissionAwareEmployeeResponse(PermissionAwareBaseModel):
    """Employee response with permission-aware field filtering"""
    employee_id: int
    people_id: int
    status: EmployeeStatus
    work_email: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    person: PermissionAwarePerson
    
    # Permission requirements for sensitive fields
    _field_permissions = {
        "work_email": "employee.read.contact",
        "effective_start_date": "employee.read.employment",
        "effective_end_date": "employee.read.employment"
    }
    
    def apply_permission_filtering(
        self, 
        user_permissions: List[str]
    ) -> "PermissionAwareEmployeeResponse":
        """
        Apply comprehensive permission filtering to employee data
        
        Args:
            user_permissions: List of permissions the user has
            
        Returns:
            Filtered employee response
        """
        # Get current data
        data = self.model_dump()
        
        # Filter top-level employee fields
        for field_name, required_permission in self._field_permissions.items():
            if required_permission not in user_permissions:
                data.pop(field_name, None)
        
        # Filter person data if present
        if "person" in data and data["person"]:
            person_data = data["person"]
            
            # Filter person fields
            for field_name, required_permission in PermissionAwarePerson._field_permissions.items():
                if required_permission not in user_permissions:
                    person_data.pop(field_name, None)
            
            # Filter personal information if present
            if "personal_information" in person_data and person_data["personal_information"]:
                personal_info = person_data["personal_information"]
                
                for field_name, required_permission in PermissionAwarePersonalInformation._field_permissions.items():
                    if required_permission not in user_permissions:
                        personal_info.pop(field_name, None)
                
                # If no personal info fields remain, remove the entire section
                if not any(personal_info.get(field) for field in ["personal_email", "ssn", "bank_account"]):
                    person_data.pop("personal_information", None)
        
        # Return new filtered instance
        return PermissionAwareEmployeeResponse(**data)


class PermissionAwareAssignmentResponse(PermissionAwareBaseModel):
    """Assignment response with permission-aware filtering"""
    assignment_id: int
    employee_id: int
    assignment_type_id: int
    description: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    
    # Note: Related objects (employee, assignment_type, supervisors) would be 
    # filtered separately based on their own permission requirements
    
    _field_permissions = {
        "description": "assignment.read.details",
        "effective_start_date": "assignment.read.dates",
        "effective_end_date": "assignment.read.dates"
    }


class PermissionAwareLeaveRequestResponse(PermissionAwareBaseModel):
    """Leave request response with permission-aware filtering"""
    leave_id: int
    assignment_id: int
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: LeaveStatus
    submitted_at: datetime
    decision_at: Optional[datetime] = None
    decided_by: Optional[int] = None
    
    _field_permissions = {
        "reason": "leave_request.read.details",
        "decided_by": "leave_request.read.approval_details"
    }


class DynamicSchemaGenerator:
    """
    Generates schemas dynamically based on user permissions
    """
    
    def __init__(self):
        self.permission_schema_mapping = {
            "employee": {
                "full": PermissionAwareEmployeeResponse,
                "personal": PermissionAwareEmployeeResponse,
                "basic": PermissionAwareEmployeeResponse
            },
            "assignment": {
                "full": PermissionAwareAssignmentResponse,
                "basic": PermissionAwareAssignmentResponse
            },
            "leave_request": {
                "full": PermissionAwareLeaveRequestResponse,
                "own": PermissionAwareLeaveRequestResponse,
                "basic": PermissionAwareLeaveRequestResponse
            }
        }
    
    def get_schema_for_permissions(
        self, 
        resource_type: str, 
        user_permissions: List[str]
    ) -> type:
        """
        Get appropriate schema class based on user permissions
        
        Args:
            resource_type: Type of resource (employee, assignment, etc.)
            user_permissions: List of user's permissions
            
        Returns:
            Appropriate schema class
        """
        # Determine access level based on permissions
        access_level = self._determine_access_level(resource_type, user_permissions)
        
        # Get schema mapping for resource type
        schema_mapping = self.permission_schema_mapping.get(resource_type, {})
        
        # Return appropriate schema
        return schema_mapping.get(access_level, PermissionAwareBaseModel)
    
    def _determine_access_level(self, resource_type: str, user_permissions: List[str]) -> str:
        """
        Determine access level based on permissions
        
        Args:
            resource_type: Type of resource
            user_permissions: List of user's permissions
            
        Returns:
            Access level string
        """
        # Check for full access permissions
        full_permissions = [
            f"{resource_type}.read.all",
            f"{resource_type}.manage"
        ]
        if any(perm in user_permissions for perm in full_permissions):
            return "full"
        
        # Check for personal/own access
        personal_permissions = [
            f"{resource_type}.read.own",
            f"{resource_type}.read.personal"
        ]
        if any(perm in user_permissions for perm in personal_permissions):
            return "personal" if resource_type == "employee" else "own"
        
        # Default to basic access
        return "basic"
    
    def create_filtered_response(
        self,
        data: Any,
        resource_type: str,
        user_permissions: List[str]
    ) -> PermissionAwareBaseModel:
        """
        Create a filtered response based on user permissions
        
        Args:
            data: Source data (model instance or dict)
            resource_type: Type of resource
            user_permissions: List of user's permissions
            
        Returns:
            Filtered response object
        """
        # Get appropriate schema
        schema_class = self.get_schema_for_permissions(resource_type, user_permissions)
        
        # Create instance from data
        if hasattr(data, 'model_validate'):
            # Data is already a Pydantic model
            instance = schema_class.model_validate(data)
        else:
            # Data is a dict or SQLAlchemy model
            instance = schema_class.model_validate(data)
        
        # Apply permission filtering if the schema supports it
        if hasattr(instance, 'apply_permission_filtering'):
            return instance.apply_permission_filtering(user_permissions)
        
        return instance


# Global schema generator instance
schema_generator = DynamicSchemaGenerator()


# Utility functions for integration
def get_filtered_employee_response(
    employee_data: Any,
    user_permissions: List[str]
) -> PermissionAwareEmployeeResponse:
    """
    Get permission-filtered employee response
    
    Args:
        employee_data: Employee data
        user_permissions: User's permissions
        
    Returns:
        Filtered employee response
    """
    return schema_generator.create_filtered_response(
        employee_data, "employee", user_permissions
    )


def get_filtered_assignment_response(
    assignment_data: Any,
    user_permissions: List[str]
) -> PermissionAwareAssignmentResponse:
    """
    Get permission-filtered assignment response
    
    Args:
        assignment_data: Assignment data
        user_permissions: User's permissions
        
    Returns:
        Filtered assignment response
    """
    return schema_generator.create_filtered_response(
        assignment_data, "assignment", user_permissions
    )