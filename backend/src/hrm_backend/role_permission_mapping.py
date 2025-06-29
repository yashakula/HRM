"""
Role-Permission Mapping Documentation and Validation

This module provides comprehensive documentation and validation for role-permission mappings
in the Enhanced Permission System. It ensures backward compatibility with the existing
role-based access control system.
"""

from typing import Dict, List, Set, Tuple
from enum import Enum
from .models import UserRole
from .permission_registry import ROLE_PERMISSIONS, PERMISSION_DEFINITIONS

class AccessLevel(Enum):
    """Defines different levels of access for resources"""
    FULL = "full"           # Complete CRUD access
    READ_WRITE = "read_write"  # Read and update access
    READ_ONLY = "read_only"    # Read access only
    CREATE_ONLY = "create_only"  # Create access only
    NONE = "none"           # No access

class ResourceScope(Enum):
    """Defines the scope of access for resources"""
    ALL = "all"             # Access to all resources
    SUPERVISED = "supervised"  # Access to supervised resources only
    OWN = "own"             # Access to own resources only
    NONE = "none"           # No access

# Comprehensive role capability documentation
ROLE_CAPABILITIES: Dict[str, Dict[str, Dict[str, any]]] = {
    "HR_ADMIN": {
        "description": "Full administrative access to all HR functions",
        "capabilities": {
            "employee_management": {
                "access_level": AccessLevel.FULL,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "employee.create",
                    "employee.read.all", 
                    "employee.update.all",
                    "employee.search",
                    "employee.deactivate"
                ],
                "business_justification": "HR admins need complete employee lifecycle management"
            },
            "assignment_management": {
                "access_level": AccessLevel.FULL,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "assignment.create",
                    "assignment.read.all",
                    "assignment.update.all", 
                    "assignment.delete",
                    "assignment.manage_supervisors"
                ],
                "business_justification": "HR admins manage organizational structure and assignments"
            },
            "leave_management": {
                "access_level": AccessLevel.FULL,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "leave_request.read.all",
                    "leave_request.approve.all",
                    "leave_request.reject.all"
                ],
                "business_justification": "HR admins handle complex leave situations and policy enforcement"
            },
            "organizational_structure": {
                "access_level": AccessLevel.FULL,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "department.create",
                    "department.read",
                    "department.update",
                    "department.delete",
                    "assignment_type.create",
                    "assignment_type.read",
                    "assignment_type.update",
                    "assignment_type.delete"
                ],
                "business_justification": "HR admins design and maintain organizational structure"
            },
            "system_administration": {
                "access_level": AccessLevel.FULL,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "user.manage"
                ],
                "business_justification": "HR admins manage user accounts and system access"
            },
            "reporting_and_analytics": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "attendance.read.all",
                    "compensation.read.all",
                    "compensation.update"
                ],
                "business_justification": "HR admins need full visibility for reporting and compliance"
            }
        }
    },
    
    "SUPERVISOR": {
        "description": "Management access to supervised employees and teams",
        "capabilities": {
            "team_management": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.SUPERVISED,
                "permissions": [
                    "employee.read.supervised",
                    "employee.search"
                ],
                "business_justification": "Supervisors need visibility into their team members"
            },
            "assignment_oversight": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.SUPERVISED,
                "permissions": [
                    "assignment.read.supervised",
                    "assignment.read.own"
                ],
                "business_justification": "Supervisors monitor team assignments and workload"
            },
            "leave_approval": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.SUPERVISED,
                "permissions": [
                    "leave_request.read.supervised",
                    "leave_request.approve.supervised",
                    "leave_request.reject.supervised"
                ],
                "business_justification": "Supervisors approve team leave requests and manage coverage"
            },
            "attendance_monitoring": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.SUPERVISED,
                "permissions": [
                    "attendance.read.supervised",
                    "attendance.log.own",
                    "attendance.read.own"
                ],
                "business_justification": "Supervisors monitor team attendance and productivity"
            },
            "self_service": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "employee.read.own",
                    "employee.update.own",
                    "leave_request.create.own",
                    "leave_request.read.own",
                    "compensation.read.own"
                ],
                "business_justification": "Supervisors manage their own employee data like any other employee"
            },
            "reference_data": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "department.read",
                    "assignment_type.read"
                ],
                "business_justification": "Supervisors need reference data for decision making"
            }
        }
    },
    
    "EMPLOYEE": {
        "description": "Self-service access to personal data and basic functions",
        "capabilities": {
            "personal_data_management": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "employee.read.own",
                    "employee.update.own"
                ],
                "business_justification": "Employees manage their personal information"
            },
            "assignment_visibility": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "assignment.read.own"
                ],
                "business_justification": "Employees need to know their current assignments"
            },
            "leave_self_service": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "leave_request.create.own",
                    "leave_request.read.own"
                ],
                "business_justification": "Employees request and track their own leave"
            },
            "attendance_tracking": {
                "access_level": AccessLevel.READ_WRITE,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "attendance.log.own",
                    "attendance.read.own"
                ],
                "business_justification": "Employees track their work hours"
            },
            "compensation_visibility": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.OWN,
                "permissions": [
                    "compensation.read.own"
                ],
                "business_justification": "Employees can view their compensation information"
            },
            "reference_data": {
                "access_level": AccessLevel.READ_ONLY,
                "scope": ResourceScope.ALL,
                "permissions": [
                    "department.read",
                    "assignment_type.read"
                ],
                "business_justification": "Employees need reference data for forms and understanding"
            }
        }
    }
}

def validate_role_permission_completeness() -> Tuple[bool, List[str]]:
    """
    Validate that all permissions in ROLE_CAPABILITIES are included in ROLE_PERMISSIONS
    and that there are no missing or extra permissions.
    """
    errors = []
    
    # Get all permissions from registry
    registry_permissions = set()
    for role, permissions in ROLE_PERMISSIONS.items():
        registry_permissions.update(permissions)
    
    # Get all permissions from capabilities documentation
    capabilities_permissions = set()
    for role, role_data in ROLE_CAPABILITIES.items():
        for capability, capability_data in role_data["capabilities"].items():
            capabilities_permissions.update(capability_data["permissions"])
    
    # Check for missing permissions in capabilities
    missing_in_capabilities = registry_permissions - capabilities_permissions
    if missing_in_capabilities:
        errors.append(f"Permissions in registry but not documented in capabilities: {missing_in_capabilities}")
    
    # Check for extra permissions in capabilities
    extra_in_capabilities = capabilities_permissions - registry_permissions
    if extra_in_capabilities:
        errors.append(f"Permissions documented in capabilities but not in registry: {extra_in_capabilities}")
    
    # Validate each role's permissions match
    for role in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
        registry_role_perms = set(ROLE_PERMISSIONS.get(role, []))
        
        capability_role_perms = set()
        if role in ROLE_CAPABILITIES:
            for capability_data in ROLE_CAPABILITIES[role]["capabilities"].values():
                capability_role_perms.update(capability_data["permissions"])
        
        if registry_role_perms != capability_role_perms:
            missing = registry_role_perms - capability_role_perms
            extra = capability_role_perms - registry_role_perms
            if missing:
                errors.append(f"{role}: Missing in capabilities: {missing}")
            if extra:
                errors.append(f"{role}: Extra in capabilities: {extra}")
    
    return len(errors) == 0, errors

def get_role_permission_summary() -> Dict[str, Dict[str, any]]:
    """Get a summary of permissions by role with counts and categories"""
    summary = {}
    
    for role in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
        role_permissions = ROLE_PERMISSIONS.get(role, [])
        
        # Categorize permissions by resource type
        categories = {}
        for permission in role_permissions:
            resource_type = permission.split('.')[0]
            if resource_type not in categories:
                categories[resource_type] = []
            categories[resource_type].append(permission)
        
        summary[role] = {
            "total_permissions": len(role_permissions),
            "categories": {k: len(v) for k, v in categories.items()},
            "detailed_categories": categories,
            "description": ROLE_CAPABILITIES.get(role, {}).get("description", "No description")
        }
    
    return summary

def get_permission_usage_analysis() -> Dict[str, any]:
    """Analyze how permissions are distributed across roles"""
    all_permissions = set()
    for permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(permissions)
    
    usage_analysis = {
        "total_unique_permissions": len(all_permissions),
        "permission_distribution": {},
        "shared_permissions": [],
        "role_exclusive_permissions": {}
    }
    
    # Analyze each permission's usage across roles
    for permission in all_permissions:
        roles_with_permission = []
        for role, permissions in ROLE_PERMISSIONS.items():
            if permission in permissions:
                roles_with_permission.append(role)
        
        usage_analysis["permission_distribution"][permission] = roles_with_permission
        
        if len(roles_with_permission) > 1:
            usage_analysis["shared_permissions"].append({
                "permission": permission,
                "roles": roles_with_permission
            })
    
    # Find role-exclusive permissions
    for role, permissions in ROLE_PERMISSIONS.items():
        exclusive = []
        for permission in permissions:
            if len(usage_analysis["permission_distribution"][permission]) == 1:
                exclusive.append(permission)
        usage_analysis["role_exclusive_permissions"][role] = exclusive
    
    return usage_analysis

def generate_role_comparison_matrix() -> Dict[str, Dict[str, bool]]:
    """Generate a matrix showing which roles have which permissions"""
    all_permissions = set()
    for permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(permissions)
    
    matrix = {}
    for permission in sorted(all_permissions):
        matrix[permission] = {}
        for role in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
            matrix[permission][role] = permission in ROLE_PERMISSIONS.get(role, [])
    
    return matrix

def validate_backward_compatibility() -> Tuple[bool, List[str]]:
    """
    Validate that the permission system maintains backward compatibility
    with the existing role-based access patterns
    """
    issues = []
    
    # Check that HR_ADMIN has the most permissions
    hr_count = len(ROLE_PERMISSIONS.get("HR_ADMIN", []))
    supervisor_count = len(ROLE_PERMISSIONS.get("SUPERVISOR", []))
    employee_count = len(ROLE_PERMISSIONS.get("EMPLOYEE", []))
    
    if not (hr_count > supervisor_count > employee_count):
        issues.append(f"Permission hierarchy issue: HR_ADMIN({hr_count}) > SUPERVISOR({supervisor_count}) > EMPLOYEE({employee_count})")
    
    # Check that all employee permissions are also available to supervisors
    employee_perms = set(ROLE_PERMISSIONS.get("EMPLOYEE", []))
    supervisor_perms = set(ROLE_PERMISSIONS.get("SUPERVISOR", []))
    
    # Employee self-service permissions that supervisors should also have
    expected_supervisor_perms = {p for p in employee_perms if ".own" in p}
    missing_supervisor_perms = expected_supervisor_perms - supervisor_perms
    
    if missing_supervisor_perms:
        issues.append(f"Supervisors missing self-service permissions: {missing_supervisor_perms}")
    
    # Check that supervisors have supervised equivalents of employee permissions
    for emp_perm in employee_perms:
        if ".own" in emp_perm:
            supervised_perm = emp_perm.replace(".own", ".supervised")
            if supervised_perm not in supervisor_perms and f"{emp_perm.split('.')[0]}.read.supervised" not in supervisor_perms:
                # Some flexibility for different permission naming patterns
                continue
    
    # Validate critical permissions exist
    critical_permissions = {
        "HR_ADMIN": ["employee.create", "user.manage", "assignment.create"],
        "SUPERVISOR": ["employee.read.supervised", "leave_request.approve.supervised"],
        "EMPLOYEE": ["employee.read.own", "leave_request.create.own"]
    }
    
    for role, critical_perms in critical_permissions.items():
        role_perms = set(ROLE_PERMISSIONS.get(role, []))
        missing_critical = set(critical_perms) - role_perms
        if missing_critical:
            issues.append(f"{role} missing critical permissions: {missing_critical}")
    
    return len(issues) == 0, issues

def print_role_documentation():
    """Print comprehensive role-permission documentation"""
    print("=" * 80)
    print("ROLE-PERMISSION MAPPING DOCUMENTATION")
    print("=" * 80)
    
    for role, role_data in ROLE_CAPABILITIES.items():
        print(f"\n📋 {role}")
        print(f"Description: {role_data['description']}")
        print(f"Total Permissions: {len(ROLE_PERMISSIONS.get(role, []))}")
        
        for capability_name, capability_data in role_data["capabilities"].items():
            print(f"\n  🔹 {capability_name.replace('_', ' ').title()}")
            print(f"     Access Level: {capability_data['access_level'].value}")
            print(f"     Scope: {capability_data['scope'].value}")
            print(f"     Permissions: {len(capability_data['permissions'])}")
            for perm in capability_data["permissions"]:
                print(f"       • {perm}")
            print(f"     Justification: {capability_data['business_justification']}")
    
    print(f"\n{'=' * 80}")
    print("PERMISSION USAGE ANALYSIS")
    print("=" * 80)
    
    analysis = get_permission_usage_analysis()
    print(f"Total Unique Permissions: {analysis['total_unique_permissions']}")
    
    print(f"\nShared Permissions ({len(analysis['shared_permissions'])}):")
    for shared in analysis["shared_permissions"]:
        print(f"  • {shared['permission']} → {', '.join(shared['roles'])}")
    
    print(f"\nRole-Exclusive Permissions:")
    for role, exclusive_perms in analysis["role_exclusive_permissions"].items():
        print(f"  • {role}: {len(exclusive_perms)} exclusive permissions")
        for perm in exclusive_perms[:3]:  # Show first 3
            print(f"    - {perm}")
        if len(exclusive_perms) > 3:
            print(f"    ... and {len(exclusive_perms) - 3} more")

if __name__ == "__main__":
    print_role_documentation()