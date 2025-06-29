#!/usr/bin/env python3
"""
Role-Permission Mapping Validation Script

This script validates the role-permission mappings to ensure:
1. Completeness and consistency
2. Backward compatibility with existing access patterns
3. Proper role hierarchy (HR_ADMIN > SUPERVISOR > EMPLOYEE)
4. Documentation accuracy
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.role_permission_mapping import (
    validate_role_permission_completeness,
    validate_backward_compatibility,
    get_role_permission_summary,
    get_permission_usage_analysis,
    generate_role_comparison_matrix,
    print_role_documentation,
    ROLE_CAPABILITIES
)
from hrm_backend.permission_registry import ROLE_PERMISSIONS, PERMISSION_DEFINITIONS

def test_permission_completeness():
    """Test that all permissions are properly documented"""
    print("🔍 Testing Permission Completeness...")
    
    is_complete, errors = validate_role_permission_completeness()
    
    if is_complete:
        print("✅ All permissions are properly documented and consistent")
    else:
        print("❌ Permission documentation issues found:")
        for error in errors:
            print(f"  • {error}")
        return False
    
    return True

def test_backward_compatibility():
    """Test backward compatibility with existing role patterns"""
    print("\n🔍 Testing Backward Compatibility...")
    
    is_compatible, issues = validate_backward_compatibility()
    
    if is_compatible:
        print("✅ Role-permission mappings maintain backward compatibility")
    else:
        print("❌ Backward compatibility issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    
    return True

def test_role_hierarchy():
    """Test that role hierarchy is maintained (HR_ADMIN > SUPERVISOR > EMPLOYEE)"""
    print("\n🔍 Testing Role Hierarchy...")
    
    hr_perms = len(ROLE_PERMISSIONS.get("HR_ADMIN", []))
    supervisor_perms = len(ROLE_PERMISSIONS.get("SUPERVISOR", []))
    employee_perms = len(ROLE_PERMISSIONS.get("EMPLOYEE", []))
    
    print(f"Permission counts: HR_ADMIN({hr_perms}) > SUPERVISOR({supervisor_perms}) > EMPLOYEE({employee_perms})")
    
    if hr_perms > supervisor_perms > employee_perms:
        print("✅ Role hierarchy is properly maintained")
        return True
    else:
        print("❌ Role hierarchy is not maintained")
        return False

def test_permission_coverage():
    """Test that all defined permissions are assigned to at least one role"""
    print("\n🔍 Testing Permission Coverage...")
    
    # Get all defined permissions
    defined_permissions = {perm[0] for perm in PERMISSION_DEFINITIONS}
    
    # Get all assigned permissions
    assigned_permissions = set()
    for permissions in ROLE_PERMISSIONS.values():
        assigned_permissions.update(permissions)
    
    # Check for unassigned permissions
    unassigned = defined_permissions - assigned_permissions
    orphaned = assigned_permissions - defined_permissions
    
    if not unassigned and not orphaned:
        print("✅ All permissions are properly assigned and defined")
        return True
    else:
        if unassigned:
            print(f"❌ Unassigned permissions: {unassigned}")
        if orphaned:
            print(f"❌ Orphaned permissions (assigned but not defined): {orphaned}")
        return False

def test_critical_permissions():
    """Test that critical permissions are assigned to appropriate roles"""
    print("\n🔍 Testing Critical Permission Assignments...")
    
    critical_tests = [
        ("HR_ADMIN", "employee.create", "HR admins must be able to create employees"),
        ("HR_ADMIN", "user.manage", "HR admins must be able to manage user accounts"),
        ("SUPERVISOR", "leave_request.approve.supervised", "Supervisors must approve team leave"),
        ("SUPERVISOR", "employee.read.supervised", "Supervisors must see team member details"),
        ("EMPLOYEE", "employee.read.own", "Employees must see their own profile"),
        ("EMPLOYEE", "leave_request.create.own", "Employees must request their own leave"),
    ]
    
    all_passed = True
    
    for role, permission, description in critical_tests:
        role_perms = ROLE_PERMISSIONS.get(role, [])
        if permission in role_perms:
            print(f"✅ {role} has {permission}")
        else:
            print(f"❌ {role} missing {permission} - {description}")
            all_passed = False
    
    return all_passed

def analyze_permission_distribution():
    """Analyze and display permission distribution"""
    print("\n📊 Permission Distribution Analysis...")
    
    summary = get_role_permission_summary()
    analysis = get_permission_usage_analysis()
    
    print(f"\nRole Summary:")
    for role, data in summary.items():
        print(f"  {role}: {data['total_permissions']} permissions")
        print(f"    Description: {data['description']}")
        print(f"    Categories: {dict(data['categories'])}")
    
    print(f"\nPermission Sharing:")
    print(f"  Total unique permissions: {analysis['total_unique_permissions']}")
    print(f"  Shared permissions: {len(analysis['shared_permissions'])}")
    
    print(f"\nMost shared permissions:")
    shared_by_count = {}
    for shared in analysis["shared_permissions"]:
        count = len(shared['roles'])
        if count not in shared_by_count:
            shared_by_count[count] = []
        shared_by_count[count].append(shared['permission'])
    
    for count in sorted(shared_by_count.keys(), reverse=True):
        permissions = shared_by_count[count]
        print(f"    {count} roles: {len(permissions)} permissions")
        for perm in permissions[:3]:  # Show first 3
            print(f"      • {perm}")
        if len(permissions) > 3:
            print(f"      ... and {len(permissions) - 3} more")

def test_role_documentation_coverage():
    """Test that all roles have proper documentation"""
    print("\n🔍 Testing Role Documentation Coverage...")
    
    all_documented = True
    
    for role in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
        if role not in ROLE_CAPABILITIES:
            print(f"❌ {role} not documented in ROLE_CAPABILITIES")
            all_documented = False
            continue
        
        role_data = ROLE_CAPABILITIES[role]
        
        # Check required fields
        if "description" not in role_data:
            print(f"❌ {role} missing description")
            all_documented = False
        
        if "capabilities" not in role_data:
            print(f"❌ {role} missing capabilities")
            all_documented = False
            continue
        
        # Check capability documentation
        for cap_name, cap_data in role_data["capabilities"].items():
            required_fields = ["access_level", "scope", "permissions", "business_justification"]
            for field in required_fields:
                if field not in cap_data:
                    print(f"❌ {role}.{cap_name} missing {field}")
                    all_documented = False
    
    if all_documented:
        print("✅ All roles have complete documentation")
    
    return all_documented

def main():
    """Run all validation tests"""
    print("🧪 ROLE-PERMISSION MAPPING VALIDATION")
    print("=" * 60)
    
    tests = [
        test_permission_completeness,
        test_backward_compatibility,
        test_role_hierarchy,
        test_permission_coverage,
        test_critical_permissions,
        test_role_documentation_coverage,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with error: {e}")
    
    # Always run analysis (non-test)
    analyze_permission_distribution()
    
    print(f"\n{'=' * 60}")
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL VALIDATION TESTS PASSED!")
        print("\nRole-permission mappings are:")
        print("✅ Complete and consistent")
        print("✅ Backward compatible")
        print("✅ Properly documented")
        print("✅ Ready for implementation")
        
        print(f"\n{'=' * 60}")
        print("DETAILED ROLE DOCUMENTATION")
        print("=" * 60)
        print_role_documentation()
        
        return 0
    else:
        print(f"❌ {total - passed} validation tests failed")
        print("Please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())