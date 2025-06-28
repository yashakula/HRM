#!/usr/bin/env python3
"""
Permission System Migration Guide Generator

This script generates a comprehensive migration guide showing how to replace
existing role-based decorators with permission-based decorators.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.permission_registry import ROLE_PERMISSIONS
from hrm_backend.role_permission_mapping import generate_role_comparison_matrix

# Mapping of current decorators to new permission-based decorators
DECORATOR_MIGRATION_MAP = {
    "@require_hr_admin": {
        "description": "Requires HR Admin role",
        "current_usage": "Full administrative access",
        "new_decorator": "@require_permission",
        "common_permissions": [
            "employee.create",
            "assignment.create", 
            "department.create",
            "assignment_type.create",
            "user.manage"
        ],
        "usage_pattern": "Replace with specific permission based on endpoint function"
    },
    
    "@require_supervisor_or_admin": {
        "description": "Requires Supervisor or HR Admin role",
        "current_usage": "Management access to supervised resources",
        "new_decorator": "@require_any_permission",
        "common_permissions": [
            "employee.read.supervised",
            "assignment.read.supervised",
            "leave_request.approve.supervised"
        ],
        "usage_pattern": "Use @require_any_permission with supervised and admin equivalents"
    },
    
    "@require_employee_or_admin": {
        "description": "Requires Employee or HR Admin role", 
        "current_usage": "Self-service access with admin override",
        "new_decorator": "@require_any_permission",
        "common_permissions": [
            "employee.read.own",
            "employee.update.own",
            "leave_request.create.own"
        ],
        "usage_pattern": "Use @require_any_permission with own and admin equivalents"
    },
    
    "@validate_employee_access(allow_supervisor_access=True)": {
        "description": "Complex validation: owner, supervisor, or admin",
        "current_usage": "Employee data access with supervisor visibility",
        "new_decorator": "@require_any_permission + context validation",
        "common_permissions": [
            "employee.read.own",
            "employee.read.supervised", 
            "employee.read.all"
        ],
        "usage_pattern": "Use @require_any_permission with context-aware validation"
    },
    
    "@validate_employee_access(allow_supervisor_access=False)": {
        "description": "Complex validation: owner or admin only",
        "current_usage": "Employee data modification (no supervisor access)",
        "new_decorator": "@require_any_permission + context validation",
        "common_permissions": [
            "employee.update.own",
            "employee.update.all"
        ],
        "usage_pattern": "Use @require_any_permission with ownership validation"
    }
}

# Common API endpoint patterns and their permission mappings
ENDPOINT_MIGRATION_EXAMPLES = {
    "Employee Management": {
        "POST /employees": {
            "current": "@require_hr_admin",
            "new": "@require_permission('employee.create')",
            "rationale": "Only HR admins can create employee records"
        },
        "GET /employees/{id}": {
            "current": "@validate_employee_access(allow_supervisor_access=True)",
            "new": "@require_any_permission(['employee.read.own', 'employee.read.supervised', 'employee.read.all'])",
            "rationale": "Employees see own data, supervisors see supervisees, HR sees all"
        },
        "PUT /employees/{id}": {
            "current": "@validate_employee_access(allow_supervisor_access=False)",
            "new": "@require_any_permission(['employee.update.own', 'employee.update.all'])",
            "rationale": "Only employee themselves or HR can update employee data"
        },
        "GET /employees/search": {
            "current": "Custom role check: SUPERVISOR or HR_ADMIN",
            "new": "@require_permission('employee.search')",
            "rationale": "Only supervisors and HR can search employee records"
        }
    },
    
    "Assignment Management": {
        "POST /assignments": {
            "current": "@require_hr_admin",
            "new": "@require_permission('assignment.create')",
            "rationale": "Only HR admins can create assignments"
        },
        "GET /assignments/{id}": {
            "current": "@validate_assignment_access(allow_supervisor_access=True)",
            "new": "@require_any_permission(['assignment.read.own', 'assignment.read.supervised', 'assignment.read.all'])",
            "rationale": "Employees see own assignments, supervisors see supervised assignments"
        },
        "PUT /assignments/{id}": {
            "current": "@require_hr_admin",
            "new": "@require_permission('assignment.update.all')",
            "rationale": "Only HR admins can modify assignments"
        }
    },
    
    "Department Management": {
        "POST /departments": {
            "current": "@require_hr_admin",
            "new": "@require_permission('department.create')",
            "rationale": "Only HR admins can create departments"
        },
        "GET /departments": {
            "current": "get_current_active_user (all authenticated)",
            "new": "@require_permission('department.read')",
            "rationale": "All users can read department reference data"
        },
        "PUT /departments/{id}": {
            "current": "@require_hr_admin", 
            "new": "@require_permission('department.update')",
            "rationale": "Only HR admins can update departments"
        }
    },
    
    "Leave Request Management": {
        "POST /leave-requests": {
            "current": "Custom validation: user owns assignment",
            "new": "@require_permission('leave_request.create.own') + assignment ownership validation",
            "rationale": "Employees can only create leave requests for their own assignments"
        },
        "PUT /leave-requests/{id}": {
            "current": "Custom validation: supervisor of assignment or HR admin",
            "new": "@require_any_permission(['leave_request.approve.supervised', 'leave_request.approve.all']) + context validation",
            "rationale": "Supervisors approve supervised requests, HR approves any"
        },
        "GET /leave-requests": {
            "current": "Custom role-based filtering",
            "new": "@require_any_permission(['leave_request.read.own', 'leave_request.read.supervised', 'leave_request.read.all']) + role-based filtering",
            "rationale": "Different roles see different subsets of leave requests"
        }
    }
}

def generate_decorator_migration_guide():
    """Generate migration guide for decorators"""
    print("=" * 80)
    print("DECORATOR MIGRATION GUIDE")
    print("=" * 80)
    
    for old_decorator, migration_info in DECORATOR_MIGRATION_MAP.items():
        print(f"\n🔄 {old_decorator}")
        print(f"   Description: {migration_info['description']}")
        print(f"   Current Usage: {migration_info['current_usage']}")
        print(f"   New Decorator: {migration_info['new_decorator']}")
        print(f"   Common Permissions:")
        for perm in migration_info['common_permissions']:
            print(f"     • {perm}")
        print(f"   Migration Pattern: {migration_info['usage_pattern']}")

def generate_endpoint_migration_examples():
    """Generate endpoint-specific migration examples"""
    print(f"\n{'=' * 80}")
    print("ENDPOINT MIGRATION EXAMPLES")
    print("=" * 80)
    
    for category, endpoints in ENDPOINT_MIGRATION_EXAMPLES.items():
        print(f"\n📂 {category}")
        
        for endpoint, migration in endpoints.items():
            print(f"\n  🔗 {endpoint}")
            print(f"      Before: {migration['current']}")
            print(f"      After:  {migration['new']}")
            print(f"      Why:    {migration['rationale']}")

def generate_permission_quick_reference():
    """Generate quick reference for common permission patterns"""
    print(f"\n{'=' * 80}")
    print("PERMISSION QUICK REFERENCE")
    print("=" * 80)
    
    patterns = {
        "Full Admin Access": {
            "description": "Complete access to a resource type",
            "permissions": ["resource.create", "resource.read.all", "resource.update.all", "resource.delete"],
            "typical_role": "HR_ADMIN",
            "decorator": "@require_permission('resource.create') # for create endpoints"
        },
        
        "Supervised Access": {
            "description": "Access to supervised resources",
            "permissions": ["resource.read.supervised", "resource.update.supervised"],
            "typical_role": "SUPERVISOR",
            "decorator": "@require_permission('resource.read.supervised')"
        },
        
        "Self-Service Access": {
            "description": "Access to own resources only",
            "permissions": ["resource.read.own", "resource.update.own", "resource.create.own"],
            "typical_role": "EMPLOYEE",
            "decorator": "@require_permission('resource.read.own')"
        },
        
        "Multi-Level Access": {
            "description": "Different access levels for different roles",
            "permissions": ["resource.read.own", "resource.read.supervised", "resource.read.all"],
            "typical_role": "All roles (different permissions)",
            "decorator": "@require_any_permission(['resource.read.own', 'resource.read.supervised', 'resource.read.all'])"
        },
        
        "Reference Data": {
            "description": "Read-only reference data for all users",
            "permissions": ["resource.read"],
            "typical_role": "All authenticated users",
            "decorator": "@require_permission('resource.read')"
        }
    }
    
    for pattern_name, pattern_info in patterns.items():
        print(f"\n📋 {pattern_name}")
        print(f"   Description: {pattern_info['description']}")
        print(f"   Permissions: {', '.join(pattern_info['permissions'])}")
        print(f"   Typical Role: {pattern_info['typical_role']}")
        print(f"   Decorator: {pattern_info['decorator']}")

def generate_role_permission_matrix():
    """Generate a matrix showing which roles have which permissions"""
    print(f"\n{'=' * 80}")
    print("ROLE-PERMISSION MATRIX")
    print("=" * 80)
    
    matrix = generate_role_comparison_matrix()
    
    # Group permissions by resource type for better readability
    resources = {}
    for permission in matrix.keys():
        resource = permission.split('.')[0]
        if resource not in resources:
            resources[resource] = []
        resources[resource].append(permission)
    
    for resource, permissions in sorted(resources.items()):
        print(f"\n📦 {resource.upper()} PERMISSIONS")
        print(f"{'Permission':<40} {'HR_ADMIN':<10} {'SUPERVISOR':<12} {'EMPLOYEE':<10}")
        print("-" * 75)
        
        for permission in sorted(permissions):
            hr_check = "✅" if matrix[permission]["HR_ADMIN"] else "❌"
            sup_check = "✅" if matrix[permission]["SUPERVISOR"] else "❌"
            emp_check = "✅" if matrix[permission]["EMPLOYEE"] else "❌"
            
            perm_display = permission.replace(f"{resource}.", "")
            print(f"{perm_display:<40} {hr_check:<10} {sup_check:<12} {emp_check:<10}")

def generate_migration_checklist():
    """Generate implementation checklist"""
    print(f"\n{'=' * 80}")
    print("MIGRATION IMPLEMENTATION CHECKLIST")
    print("=" * 80)
    
    checklist = [
        "☐ Create new permission-based decorators in auth.py",
        "☐ Implement @require_permission(permission_name) decorator",
        "☐ Implement @require_any_permission(permission_list) decorator", 
        "☐ Implement @require_all_permissions(permission_list) decorator",
        "☐ Update context-aware validation functions",
        "☐ Integrate ownership validation with permission checking",
        "☐ Update response filtering to use permissions",
        "☐ Migrate employee management endpoints",
        "☐ Migrate assignment management endpoints",
        "☐ Migrate department management endpoints", 
        "☐ Migrate assignment type endpoints",
        "☐ Migrate leave request endpoints",
        "☐ Update error handling for permission denials",
        "☐ Test all endpoints with different user roles",
        "☐ Verify backward compatibility",
        "☐ Update API documentation with new permission requirements",
        "☐ Remove deprecated role-based decorators (after migration)",
    ]
    
    for item in checklist:
        print(f"  {item}")

def main():
    """Generate complete migration guide"""
    print("📋 ENHANCED PERMISSION SYSTEM - MIGRATION GUIDE")
    print("=" * 80)
    print("This guide shows how to migrate from role-based decorators")
    print("to the new permission-based authorization system.")
    print("=" * 80)
    
    generate_decorator_migration_guide()
    generate_endpoint_migration_examples()
    generate_permission_quick_reference()
    generate_role_permission_matrix()
    generate_migration_checklist()
    
    print(f"\n{'=' * 80}")
    print("🎯 NEXT STEPS")
    print("=" * 80)
    print("1. Review this migration guide thoroughly")
    print("2. Implement permission-based decorators in auth.py") 
    print("3. Start with a few simple endpoints as proof of concept")
    print("4. Gradually migrate all endpoints using this guide")
    print("5. Test thoroughly with different user roles")
    print("6. Remove deprecated decorators after full migration")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()