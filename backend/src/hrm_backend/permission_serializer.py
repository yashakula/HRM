"""
Permission-Aware Serialization System

This module provides comprehensive permission-aware serialization that dynamically
filters response data based on user permissions, including nested resources and
field-level access control.
"""

from typing import Any, Dict, List, Optional, Union, Type
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .models import User, Employee, Assignment, Department
from .permission_validation import validate_permission
from .permission_registry import ROLE_PERMISSIONS
from . import schemas


class PermissionAwareSerializer:
    """
    Core serialization class that applies permission-based filtering to response data
    """
    
    def __init__(self):
        # Define field-level permission requirements
        self.field_permission_map = {
            # Employee sensitive fields
            "employee": {
                "personal_information.ssn": "employee.read.sensitive",
                "personal_information.bank_account": "employee.read.sensitive", 
                "personal_information.personal_email": "employee.read.personal",
                "person.date_of_birth": "employee.read.personal",
                "work_email": "employee.read.contact",
                "effective_start_date": "employee.read.employment",
                "effective_end_date": "employee.read.employment"
            },
            # Assignment sensitive fields
            "assignment": {
                "description": "assignment.read.details",
                "effective_start_date": "assignment.read.dates",
                "effective_end_date": "assignment.read.dates",
                "compensation": "assignment.read.compensation"
            },
            # Leave request sensitive fields
            "leave_request": {
                "reason": "leave_request.read.details",
                "decided_by": "leave_request.read.approval_details",
                "supervisor_notes": "leave_request.read.approval_details"
            }
        }
        
        # Define schema hierarchy based on access levels
        self.schema_hierarchy = {
            "employee": {
                "full": schemas.EmployeeResponseHR,
                "owner": schemas.EmployeeResponseOwner,
                "basic": schemas.EmployeeResponseBasic
            }
        }
    
    def serialize_employee(
        self,
        employee_data: Employee,
        current_user: User,
        db: Session,
        include_nested: bool = True
    ) -> Dict[str, Any]:
        """
        Serialize employee data with permission-based filtering
        
        Args:
            employee_data: Employee model instance
            current_user: User requesting the data
            db: Database session
            include_nested: Whether to include nested resources
            
        Returns:
            Permission-filtered employee data dictionary
        """
        resource_id = employee_data.employee_id
        
        # Determine appropriate schema based on permissions
        schema_class = self._get_employee_schema(current_user, resource_id, db)
        
        # Convert to base schema first
        base_data = schema_class.model_validate(employee_data).model_dump()
        
        # Apply field-level filtering
        filtered_data = self._apply_field_filtering(
            base_data, "employee", current_user, db, resource_id
        )
        
        # Handle nested resources if requested
        if include_nested:
            filtered_data = self._include_nested_resources(
                filtered_data, "employee", current_user, db
            )
        
        return filtered_data
    
    def serialize_assignment(
        self,
        assignment_data: Assignment,
        current_user: User,
        db: Session,
        include_nested: bool = True
    ) -> Dict[str, Any]:
        """
        Serialize assignment data with permission-based filtering
        
        Args:
            assignment_data: Assignment model instance
            current_user: User requesting the data
            db: Database session
            include_nested: Whether to include nested resources
            
        Returns:
            Permission-filtered assignment data dictionary
        """
        resource_id = assignment_data.assignment_id
        
        # Convert to schema
        base_data = schemas.AssignmentResponse.model_validate(assignment_data).model_dump()
        
        # Apply field-level filtering
        filtered_data = self._apply_field_filtering(
            base_data, "assignment", current_user, db, resource_id
        )
        
        # Handle nested employee data with appropriate filtering
        if include_nested and "employee" in filtered_data:
            employee_data = filtered_data["employee"]
            if employee_data:
                # Re-serialize employee with permission filtering
                filtered_data["employee"] = self._filter_nested_employee(
                    employee_data, current_user, db
                )
        
        return filtered_data
    
    def serialize_list(
        self,
        data_list: List[Any],
        resource_type: str,
        current_user: User,
        db: Session,
        include_nested: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Serialize a list of resources with permission filtering
        
        Args:
            data_list: List of model instances
            resource_type: Type of resource (employee, assignment, etc.)
            current_user: User requesting the data
            db: Database session
            include_nested: Whether to include nested resources
            
        Returns:
            List of permission-filtered data dictionaries
        """
        filtered_list = []
        
        for item in data_list:
            try:
                if resource_type == "employee":
                    filtered_item = self.serialize_employee(item, current_user, db, include_nested)
                elif resource_type == "assignment":
                    filtered_item = self.serialize_assignment(item, current_user, db, include_nested)
                else:
                    # Generic serialization for other types
                    filtered_item = self._generic_serialize(item, resource_type, current_user, db)
                
                filtered_list.append(filtered_item)
            except Exception as e:
                # Log error and skip item rather than failing entire request
                print(f"Warning: Failed to serialize {resource_type} item: {e}")
                continue
        
        return filtered_list
    
    def _get_employee_schema(self, current_user: User, employee_id: int, db: Session) -> Type[BaseModel]:
        """Determine appropriate employee schema based on permissions"""
        
        # Check full access
        full_result = validate_permission(
            current_user, "employee.read.all", db, resource_id=employee_id
        )
        if full_result.granted:
            return schemas.EmployeeResponseHR
        
        # Check own access
        own_result = validate_permission(
            current_user, "employee.read.own", db, resource_id=employee_id
        )
        if own_result.granted:
            return schemas.EmployeeResponseOwner
        
        # Default to basic
        return schemas.EmployeeResponseBasic
    
    def _apply_field_filtering(
        self,
        data: Dict[str, Any],
        resource_type: str,
        current_user: User,
        db: Session,
        resource_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Apply field-level permission filtering
        
        Args:
            data: Data dictionary to filter
            resource_type: Type of resource
            current_user: User requesting the data
            db: Database session
            resource_id: ID of the resource
            
        Returns:
            Filtered data dictionary
        """
        if resource_type not in self.field_permission_map:
            return data
        
        filtered_data = data.copy()
        field_permissions = self.field_permission_map[resource_type]
        
        for field_path, required_permission in field_permissions.items():
            # Check if user has the required permission
            result = validate_permission(
                current_user, required_permission, db, resource_id=resource_id
            )
            
            if not result.granted:
                # Remove the field from response
                self._remove_nested_field(filtered_data, field_path)
        
        return filtered_data
    
    def _remove_nested_field(self, data: Dict[str, Any], field_path: str) -> None:
        """
        Remove a nested field using dot notation
        
        Args:
            data: Data dictionary to modify
            field_path: Dot-separated path to field (e.g., "person.date_of_birth")
        """
        parts = field_path.split(".")
        current = data
        
        # Navigate to parent of target field
        for part in parts[:-1]:
            if part in current and isinstance(current[part], dict):
                current = current[part]
            else:
                # Path doesn't exist
                return
        
        # Remove target field
        target_field = parts[-1]
        if target_field in current:
            current[target_field] = None
    
    def _include_nested_resources(
        self,
        data: Dict[str, Any],
        resource_type: str,
        current_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Include nested resources with appropriate permission filtering
        
        Args:
            data: Main resource data
            resource_type: Type of main resource
            current_user: User requesting the data
            db: Database session
            
        Returns:
            Data with filtered nested resources
        """
        # This would be extended based on specific nested resource requirements
        # For now, we handle basic cases
        
        if resource_type == "employee" and "assignments" in data:
            # Filter assignment data if present
            assignments = data.get("assignments", [])
            if assignments:
                filtered_assignments = []
                for assignment in assignments:
                    # Check if user can read this assignment
                    assignment_id = assignment.get("assignment_id")
                    if assignment_id:
                        result = validate_permission(
                            current_user, "assignment.read.own", db, resource_id=assignment_id
                        )
                        if result.granted:
                            filtered_assignment = self._apply_field_filtering(
                                assignment, "assignment", current_user, db, assignment_id
                            )
                            filtered_assignments.append(filtered_assignment)
                
                data["assignments"] = filtered_assignments
        
        return data
    
    def _filter_nested_employee(
        self,
        employee_data: Dict[str, Any],
        current_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Filter nested employee data based on permissions
        
        Args:
            employee_data: Employee data dictionary
            current_user: User requesting the data
            db: Database session
            
        Returns:
            Filtered employee data
        """
        employee_id = employee_data.get("employee_id")
        if not employee_id:
            return employee_data
        
        # Apply same filtering logic as main employee serialization
        return self._apply_field_filtering(
            employee_data, "employee", current_user, db, employee_id
        )
    
    def _generic_serialize(
        self,
        data: Any,
        resource_type: str,
        current_user: User,
        db: Session
    ) -> Dict[str, Any]:
        """
        Generic serialization for resource types without specific handlers
        
        Args:
            data: Resource data
            resource_type: Type of resource
            current_user: User requesting the data
            db: Database session
            
        Returns:
            Serialized data dictionary
        """
        # Convert to dict if it's a model
        if hasattr(data, 'model_validate'):
            data_dict = data.model_dump() if hasattr(data, 'model_dump') else data.__dict__
        else:
            data_dict = data if isinstance(data, dict) else data.__dict__
        
        # Apply any field filtering if configured
        return self._apply_field_filtering(data_dict, resource_type, current_user, db)
    
    def get_user_permissions(self, user: User) -> List[str]:
        """
        Get list of permissions for a user
        
        Args:
            user: User instance
            
        Returns:
            List of permission strings
        """
        role_name = user.role.value if hasattr(user.role, 'value') else str(user.role)
        return ROLE_PERMISSIONS.get(role_name, [])


class PermissionAwarePaginator:
    """
    Pagination with permission-aware filtering
    """
    
    def __init__(self, serializer: PermissionAwareSerializer):
        self.serializer = serializer
    
    def paginate_and_serialize(
        self,
        query_result: List[Any],
        resource_type: str,
        current_user: User,
        db: Session,
        page: int = 1,
        per_page: int = 20,
        include_nested: bool = False
    ) -> Dict[str, Any]:
        """
        Paginate and serialize results with permission filtering
        
        Args:
            query_result: List of model instances
            resource_type: Type of resource
            current_user: User requesting the data
            db: Database session
            page: Page number (1-based)
            per_page: Items per page
            include_nested: Whether to include nested resources
            
        Returns:
            Paginated and filtered response
        """
        # Calculate pagination
        total_items = len(query_result)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = query_result[start_idx:end_idx]
        
        # Serialize page items
        serialized_items = self.serializer.serialize_list(
            page_items, resource_type, current_user, db, include_nested
        )
        
        return {
            "items": serialized_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total_items": total_items,
                "total_pages": (total_items + per_page - 1) // per_page,
                "has_next": end_idx < total_items,
                "has_prev": page > 1
            }
        }


# Global instances
permission_serializer = PermissionAwareSerializer()
permission_paginator = PermissionAwarePaginator(permission_serializer)


# Convenience functions for easy integration
def serialize_employee_with_permissions(
    employee_data: Employee,
    current_user: User,
    db: Session,
    include_nested: bool = True
) -> Dict[str, Any]:
    """
    Serialize employee data with permission filtering
    """
    return permission_serializer.serialize_employee(
        employee_data, current_user, db, include_nested
    )


def serialize_assignment_with_permissions(
    assignment_data: Assignment,
    current_user: User,
    db: Session,
    include_nested: bool = True
) -> Dict[str, Any]:
    """
    Serialize assignment data with permission filtering
    """
    return permission_serializer.serialize_assignment(
        assignment_data, current_user, db, include_nested
    )


def serialize_list_with_permissions(
    data_list: List[Any],
    resource_type: str,
    current_user: User,
    db: Session,
    include_nested: bool = False
) -> List[Dict[str, Any]]:
    """
    Serialize list of resources with permission filtering
    """
    return permission_serializer.serialize_list(
        data_list, resource_type, current_user, db, include_nested
    )