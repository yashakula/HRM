"""
Permission Registry for Enhanced Permission System

This module defines all permissions and role-permission mappings for the HRM system.
Permissions follow the naming convention: {resource}.{action}[.{scope}]
"""

from typing import List, Dict, Tuple

# Permission Definitions: (name, description, resource_type, action, scope)
PERMISSION_DEFINITIONS: List[Tuple[str, str, str, str, str]] = [
    # Employee Management Permissions
    ("employee.create", "Create new employee records", "employee", "create", None),
    ("employee.read.all", "Read all employee records", "employee", "read", "all"),
    ("employee.read.own", "Read own employee record", "employee", "read", "own"),
    ("employee.read.supervised", "Read supervised employee records", "employee", "read", "supervised"),
    ("employee.update.all", "Update any employee record", "employee", "update", "all"),
    ("employee.update.own", "Update own employee record", "employee", "update", "own"),
    ("employee.search", "Search employee records", "employee", "search", None),
    ("employee.deactivate", "Deactivate employee records", "employee", "deactivate", None),
    
    # Assignment Management Permissions
    ("assignment.create", "Create assignments", "assignment", "create", None),
    ("assignment.read.all", "Read all assignments", "assignment", "read", "all"),
    ("assignment.read.own", "Read own assignments", "assignment", "read", "own"),
    ("assignment.read.supervised", "Read supervised assignments", "assignment", "read", "supervised"),
    ("assignment.update.all", "Update any assignment", "assignment", "update", "all"),
    ("assignment.delete", "Delete assignments", "assignment", "delete", None),
    ("assignment.manage_supervisors", "Manage assignment supervisors", "assignment", "manage_supervisors", None),
    
    # Leave Request Permissions
    ("leave_request.create.own", "Create own leave requests", "leave_request", "create", "own"),
    ("leave_request.read.all", "Read all leave requests", "leave_request", "read", "all"),
    ("leave_request.read.own", "Read own leave requests", "leave_request", "read", "own"),
    ("leave_request.read.supervised", "Read supervised leave requests", "leave_request", "read", "supervised"),
    ("leave_request.approve.supervised", "Approve supervised leave requests", "leave_request", "approve", "supervised"),
    ("leave_request.approve.all", "Approve any leave request", "leave_request", "approve", "all"),
    ("leave_request.reject.supervised", "Reject supervised leave requests", "leave_request", "reject", "supervised"),
    ("leave_request.reject.all", "Reject any leave request", "leave_request", "reject", "all"),
    
    # Department Management Permissions
    ("department.create", "Create departments", "department", "create", None),
    ("department.read", "Read departments", "department", "read", None),
    ("department.update", "Update departments", "department", "update", None),
    ("department.delete", "Delete departments", "department", "delete", None),
    
    # Assignment Type Management Permissions
    ("assignment_type.create", "Create assignment types", "assignment_type", "create", None),
    ("assignment_type.read", "Read assignment types", "assignment_type", "read", None),
    ("assignment_type.update", "Update assignment types", "assignment_type", "update", None),
    ("assignment_type.delete", "Delete assignment types", "assignment_type", "delete", None),
    
    # User Management Permissions
    ("user.manage", "Manage user accounts", "user", "manage", None),
    
    # Attendance Permissions
    ("attendance.log.own", "Log own attendance", "attendance", "log", "own"),
    ("attendance.read.own", "Read own attendance records", "attendance", "read", "own"),
    ("attendance.read.supervised", "Read supervised attendance records", "attendance", "read", "supervised"),
    ("attendance.read.all", "Read all attendance records", "attendance", "read", "all"),
    
    # Compensation Permissions
    ("compensation.read.own", "Read own compensation", "compensation", "read", "own"),
    ("compensation.read.all", "Read all compensation records", "compensation", "read", "all"),
    ("compensation.update", "Update compensation records", "compensation", "update", None),
]

# Role-Permission Mappings
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "SUPER_USER": [
        # System administration and user management
        "user.manage",
        
        # Employee management (create, read, search)
        "employee.create",
        "employee.read.all",
        "employee.search",
        
        # Department management (full access)
        "department.create",
        "department.read",
        "department.update",
        "department.delete",
    ],
    
    "HR_ADMIN": [
        # All employee permissions (except user management)
        "employee.create",
        "employee.read.all",
        "employee.update.all",
        "employee.search",
        "employee.deactivate",
        
        # All assignment permissions
        "assignment.create",
        "assignment.read.all",
        "assignment.update.all",
        "assignment.delete",
        "assignment.manage_supervisors",
        
        # All leave request permissions
        "leave_request.read.all",
        "leave_request.approve.all",
        "leave_request.reject.all",
        
        # All department permissions
        "department.create",
        "department.read",
        "department.update",
        "department.delete",
        
        # All assignment type permissions
        "assignment_type.create",
        "assignment_type.read",
        "assignment_type.update",
        "assignment_type.delete",
        
        # All attendance permissions
        "attendance.read.all",
        
        # All compensation permissions
        "compensation.read.all",
        "compensation.update",
    ],
    
    "SUPERVISOR": [
        # Supervised employee access
        "employee.read.supervised",
        "employee.search",
        
        # Own data access
        "employee.read.own",
        "employee.update.own",
        
        # Supervised assignment access
        "assignment.read.supervised",
        "assignment.read.own",
        
        # Supervised leave request access
        "leave_request.read.supervised",
        "leave_request.approve.supervised",
        "leave_request.reject.supervised",
        "leave_request.create.own",
        "leave_request.read.own",
        
        # Read-only admin data
        "department.read",
        "assignment_type.read",
        
        # Attendance access
        "attendance.log.own",
        "attendance.read.own",
        "attendance.read.supervised",
        
        # Own compensation
        "compensation.read.own",
    ],
    
    "EMPLOYEE": [
        # Own data access
        "employee.read.own",
        "employee.update.own",
        "assignment.read.own",
        "leave_request.create.own",
        "leave_request.read.own",
        
        # Read-only admin data
        "department.read",
        "assignment_type.read",
        
        # Attendance access
        "attendance.log.own",
        "attendance.read.own",
        
        # Own compensation
        "compensation.read.own",
    ]
}

# Validation functions
def validate_permission_name(name: str) -> bool:
    """Validate permission name follows the naming convention"""
    import re
    pattern = r'^[a-z_]+\.[a-z_]+(\.[a-z_]+)?$'
    return bool(re.match(pattern, name))

def get_all_permission_names() -> List[str]:
    """Get list of all permission names"""
    return [perm[0] for perm in PERMISSION_DEFINITIONS]

def get_permissions_for_role(role: str) -> List[str]:
    """Get list of permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, [])

def validate_role_permissions() -> bool:
    """Validate that all role permissions exist in permission definitions"""
    all_permissions = set(get_all_permission_names())
    
    for role, permissions in ROLE_PERMISSIONS.items():
        for permission in permissions:
            if permission not in all_permissions:
                print(f"Error: Permission '{permission}' for role '{role}' not found in definitions")
                return False
    
    return True

# Resource and action definitions for validation
VALID_RESOURCES = {
    "employee", "assignment", "leave_request", "department", 
    "assignment_type", "user", "attendance", "compensation"
}

VALID_ACTIONS = {
    "create", "read", "update", "delete", "approve", "reject", 
    "search", "deactivate", "manage", "manage_supervisors", "log"
}

VALID_SCOPES = {"own", "supervised", "all", None}

def validate_permission_definition(name: str, resource_type: str, action: str, scope: str) -> bool:
    """Validate a permission definition"""
    if not validate_permission_name(name):
        return False
    
    if resource_type not in VALID_RESOURCES:
        return False
    
    if action not in VALID_ACTIONS:
        return False
    
    if scope not in VALID_SCOPES:
        return False
    
    return True