#!/usr/bin/env python3
"""
Test Permission System

This script tests the permission system implementation to ensure it's working correctly.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.models import User, UserRole
from hrm_backend.permission_registry import ROLE_PERMISSIONS

def test_user_permissions():
    """Test the User model permission methods"""
    print("Testing User Permission Methods...")
    
    # Create test users for each role
    hr_admin = User(role=UserRole.HR_ADMIN)
    supervisor = User(role=UserRole.SUPERVISOR)
    employee = User(role=UserRole.EMPLOYEE)
    
    # Test individual permission checking
    print("\n1. Testing individual permission checking:")
    
    # HR Admin should have employee.create permission
    assert hr_admin.has_permission("employee.create") == True
    print("✅ HR Admin has employee.create permission")
    
    # Supervisor should NOT have employee.create permission
    assert supervisor.has_permission("employee.create") == False
    print("✅ Supervisor does NOT have employee.create permission")
    
    # Employee should have employee.read.own permission
    assert employee.has_permission("employee.read.own") == True
    print("✅ Employee has employee.read.own permission")
    
    # Employee should NOT have employee.read.all permission
    assert employee.has_permission("employee.read.all") == False
    print("✅ Employee does NOT have employee.read.all permission")
    
    # Test multiple permission checking
    print("\n2. Testing multiple permission checking:")
    
    # HR Admin should have ANY of these permissions
    assert hr_admin.has_any_permission(["employee.create", "fake.permission"]) == True
    print("✅ HR Admin has any of [employee.create, fake.permission]")
    
    # Employee should NOT have ANY of these permissions
    assert employee.has_any_permission(["employee.create", "employee.delete"]) == False
    print("✅ Employee does NOT have any of [employee.create, employee.delete]")
    
    # Supervisor should have ALL of these permissions
    assert supervisor.has_all_permissions(["employee.read.own", "department.read"]) == True
    print("✅ Supervisor has all of [employee.read.own, department.read]")
    
    # Employee should NOT have ALL of these permissions
    assert employee.has_all_permissions(["employee.read.own", "employee.create"]) == False
    print("✅ Employee does NOT have all of [employee.read.own, employee.create]")
    
    # Test getting all permissions
    print("\n3. Testing get_all_permissions:")
    
    hr_permissions = hr_admin.get_all_permissions()
    supervisor_permissions = supervisor.get_all_permissions()
    employee_permissions = employee.get_all_permissions()
    
    print(f"HR Admin has {len(hr_permissions)} permissions")
    print(f"Supervisor has {len(supervisor_permissions)} permissions")
    print(f"Employee has {len(employee_permissions)} permissions")
    
    # Verify counts match our expectations
    expected_hr = len(ROLE_PERMISSIONS["HR_ADMIN"])
    expected_supervisor = len(ROLE_PERMISSIONS["SUPERVISOR"])
    expected_employee = len(ROLE_PERMISSIONS["EMPLOYEE"])
    
    assert len(hr_permissions) == expected_hr
    assert len(supervisor_permissions) == expected_supervisor
    assert len(employee_permissions) == expected_employee
    
    print(f"✅ Permission counts match expectations:")
    print(f"   HR Admin: {len(hr_permissions)}/{expected_hr}")
    print(f"   Supervisor: {len(supervisor_permissions)}/{expected_supervisor}")
    print(f"   Employee: {len(employee_permissions)}/{expected_employee}")
    
    print("\n4. Sample permissions by role:")
    print(f"HR Admin sample: {hr_permissions[:3]}")
    print(f"Supervisor sample: {supervisor_permissions[:3]}")
    print(f"Employee sample: {employee_permissions[:3]}")
    
    print("\n✅ All permission tests passed!")

def test_permission_registry():
    """Test the permission registry validation"""
    print("\nTesting Permission Registry...")
    
    from hrm_backend.permission_registry import (
        validate_role_permissions,
        get_all_permission_names,
        get_permissions_for_role,
        validate_permission_name
    )
    
    # Test registry validation
    assert validate_role_permissions() == True
    print("✅ Role-permission mappings are valid")
    
    # Test permission name validation
    assert validate_permission_name("employee.create") == True
    assert validate_permission_name("employee.read.own") == True
    assert validate_permission_name("invalid-name") == False
    assert validate_permission_name("too.many.parts.here") == False
    print("✅ Permission name validation works correctly")
    
    # Test getting permissions for roles
    hr_perms = get_permissions_for_role("HR_ADMIN")
    supervisor_perms = get_permissions_for_role("SUPERVISOR")
    employee_perms = get_permissions_for_role("EMPLOYEE")
    fake_perms = get_permissions_for_role("FAKE_ROLE")
    
    assert len(hr_perms) > len(supervisor_perms) > len(employee_perms)
    assert len(fake_perms) == 0
    print("✅ Role permission retrieval works correctly")
    
    # Test getting all permission names
    all_perms = get_all_permission_names()
    assert len(all_perms) == 39  # Should match our seeded count
    print(f"✅ Retrieved {len(all_perms)} total permissions")
    
    print("\n✅ All permission registry tests passed!")

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Permission System")
    print("=" * 50)
    
    try:
        test_user_permissions()
        test_permission_registry()
        
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Permission system is working correctly.")
        print("\nNext steps:")
        print("1. Implement permission-based decorators in auth.py")
        print("2. Start migrating API endpoints to use new decorators")
        print("3. Test with real API calls")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()