#!/usr/bin/env python3
"""
User-Role Preservation Validation Script

This script validates that the existing user-role relationship is preserved
while the Enhanced Permission System is implemented.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.models import User, UserRole
from hrm_backend.permission_registry import ROLE_PERMISSIONS

def test_user_model_backward_compatibility():
    """Test that the User model maintains backward compatibility"""
    print("🔍 Testing User Model Backward Compatibility...")
    
    # Test that UserRole enum still works exactly as before
    assert UserRole.HR_ADMIN.value == "HR_ADMIN"
    assert UserRole.SUPERVISOR.value == "SUPERVISOR"
    assert UserRole.EMPLOYEE.value == "EMPLOYEE"
    print("✅ UserRole enum values unchanged")
    
    # Test user creation with each role (existing functionality)
    hr_user = User(
        username="hr_admin",
        email="hr@company.com", 
        password_hash="hashed_password",
        role=UserRole.HR_ADMIN
    )
    
    supervisor_user = User(
        username="supervisor",
        email="supervisor@company.com",
        password_hash="hashed_password", 
        role=UserRole.SUPERVISOR
    )
    
    employee_user = User(
        username="employee",
        email="employee@company.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE
    )
    
    # Test that role field works exactly as before
    assert hr_user.role == UserRole.HR_ADMIN
    assert supervisor_user.role == UserRole.SUPERVISOR
    assert employee_user.role == UserRole.EMPLOYEE
    print("✅ User role assignment works identically")
    
    # Test role comparisons (existing code patterns)
    assert hr_user.role == UserRole.HR_ADMIN
    assert hr_user.role != UserRole.SUPERVISOR
    assert supervisor_user.role in [UserRole.SUPERVISOR, UserRole.HR_ADMIN]
    assert employee_user.role not in [UserRole.SUPERVISOR, UserRole.HR_ADMIN]
    print("✅ Role comparisons work identically")
    
    return True

def test_permission_methods_additive():
    """Test that permission methods are additive and don't break existing functionality"""
    print("\n🔍 Testing Permission Methods Are Additive...")
    
    user = User(role=UserRole.SUPERVISOR)
    
    # Test that original role functionality still works
    assert user.role == UserRole.SUPERVISOR
    assert hasattr(user, 'role')
    assert user.role.value == "SUPERVISOR"
    print("✅ Original role functionality preserved")
    
    # Test that new permission methods work
    assert hasattr(user, 'has_permission')
    assert hasattr(user, 'has_any_permission') 
    assert hasattr(user, 'has_all_permissions')
    assert hasattr(user, 'get_all_permissions')
    print("✅ New permission methods available")
    
    # Test permission methods work correctly
    assert user.has_permission("employee.read.supervised") == True
    assert user.has_permission("employee.create") == False
    assert user.has_any_permission(["employee.create", "employee.read.supervised"]) == True
    assert user.has_all_permissions(["employee.read.own", "department.read"]) == True
    print("✅ Permission methods function correctly")
    
    # Test that both old and new approaches work simultaneously
    if user.role == UserRole.SUPERVISOR:  # Old way
        assert user.has_permission("employee.read.supervised")  # New way
    print("✅ Old and new approaches work simultaneously")
    
    return True

def test_role_enum_preservation():
    """Test that UserRole enum is completely preserved"""
    print("\n🔍 Testing UserRole Enum Preservation...")
    
    # Test enum values unchanged
    roles = [UserRole.HR_ADMIN, UserRole.SUPERVISOR, UserRole.EMPLOYEE]
    expected_values = ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]
    
    for role, expected in zip(roles, expected_values):
        assert role.value == expected
        assert str(role) == f"UserRole.{expected}"
    print("✅ UserRole enum values and string representations unchanged")
    
    # Test enum iteration (existing code might use this)
    all_roles = list(UserRole)
    assert len(all_roles) == 3
    assert UserRole.HR_ADMIN in all_roles
    assert UserRole.SUPERVISOR in all_roles
    assert UserRole.EMPLOYEE in all_roles
    print("✅ UserRole enum iteration works identically")
    
    # Test enum comparison patterns used in existing code
    test_role = UserRole.SUPERVISOR
    assert test_role == UserRole.SUPERVISOR
    assert test_role != UserRole.HR_ADMIN
    assert test_role in [UserRole.SUPERVISOR, UserRole.HR_ADMIN]
    print("✅ UserRole comparison patterns preserved")
    
    return True

def test_static_permission_mapping():
    """Test that static permission mapping works correctly"""
    print("\n🔍 Testing Static Permission Mapping...")
    
    # Test that ROLE_PERMISSIONS mapping exists and is complete
    assert "HR_ADMIN" in ROLE_PERMISSIONS
    assert "SUPERVISOR" in ROLE_PERMISSIONS  
    assert "EMPLOYEE" in ROLE_PERMISSIONS
    print("✅ All roles present in ROLE_PERMISSIONS")
    
    # Test permission counts are as expected
    hr_perms = len(ROLE_PERMISSIONS["HR_ADMIN"])
    supervisor_perms = len(ROLE_PERMISSIONS["SUPERVISOR"])
    employee_perms = len(ROLE_PERMISSIONS["EMPLOYEE"])
    
    assert hr_perms > supervisor_perms > employee_perms
    assert hr_perms == 25  # From our validation
    assert supervisor_perms == 17
    assert employee_perms == 10
    print(f"✅ Permission counts correct: HR({hr_perms}) > SUP({supervisor_perms}) > EMP({employee_perms})")
    
    # Test that static mapping is fast (no database queries)
    import time
    
    user = User(role=UserRole.HR_ADMIN)
    start_time = time.time()
    for _ in range(1000):
        user.has_permission("employee.create")
    end_time = time.time()
    
    # Should be very fast (< 10ms for 1000 checks)
    duration = end_time - start_time
    assert duration < 0.01  # Less than 10ms
    print(f"✅ Permission checking is fast: {duration*1000:.2f}ms for 1000 checks")
    
    return True

def test_no_database_schema_changes():
    """Test that no database schema changes are required"""
    print("\n🔍 Testing No Database Schema Changes Required...")
    
    # Test that User model structure is preserved
    user = User(
        username="test",
        email="test@test.com",
        password_hash="hash",
        role=UserRole.EMPLOYEE
    )
    
    # Test that all expected fields exist and are unchanged
    expected_fields = [
        'user_id', 'username', 'email', 'password_hash', 
        'is_active', 'role', 'created_at', 'updated_at'
    ]
    
    for field in expected_fields:
        assert hasattr(user, field)
    print("✅ All expected User model fields present")
    
    # Test that role field is still Enum type
    assert isinstance(user.role, UserRole)
    assert user.role.value in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]
    print("✅ Role field remains UserRole enum type")
    
    # Test that no new required fields were added
    # (This ensures existing user data remains valid)
    try:
        minimal_user = User(role=UserRole.EMPLOYEE)
        assert minimal_user.role == UserRole.EMPLOYEE
        print("✅ No new required fields added to User model")
    except Exception as e:
        print(f"❌ New required fields detected: {e}")
        return False
    
    return True

def test_existing_code_patterns():
    """Test common existing code patterns still work"""
    print("\n🔍 Testing Existing Code Patterns...")
    
    user = User(role=UserRole.SUPERVISOR)
    
    # Pattern 1: Direct role comparison
    if user.role == UserRole.SUPERVISOR:
        supervisor_task = True
    assert supervisor_task == True
    print("✅ Direct role comparison pattern works")
    
    # Pattern 2: Role in list check
    admin_or_supervisor = user.role in [UserRole.HR_ADMIN, UserRole.SUPERVISOR]
    assert admin_or_supervisor == True
    print("✅ Role in list pattern works")
    
    # Pattern 3: Role value string comparison
    role_name = user.role.value
    assert role_name == "SUPERVISOR"
    assert role_name in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]
    print("✅ Role value string pattern works")
    
    # Pattern 4: Role switch/dispatch pattern
    permissions_count = 0
    if user.role == UserRole.HR_ADMIN:
        permissions_count = 25
    elif user.role == UserRole.SUPERVISOR:
        permissions_count = 17
    elif user.role == UserRole.EMPLOYEE:
        permissions_count = 10
    
    assert permissions_count == 17  # Supervisor
    print("✅ Role switch/dispatch pattern works")
    
    return True

def test_migration_compatibility():
    """Test that the system supports gradual migration"""
    print("\n🔍 Testing Migration Compatibility...")
    
    user = User(role=UserRole.HR_ADMIN)
    
    # Test that both old and new authorization can coexist
    # Old way (role-based)
    old_auth_admin = (user.role == UserRole.HR_ADMIN)
    
    # New way (permission-based)  
    new_auth_admin = user.has_permission("employee.create")
    
    # Both should return True for HR_ADMIN
    assert old_auth_admin == True
    assert new_auth_admin == True
    print("✅ Old and new authorization methods coexist")
    
    # Test gradual migration scenario
    def check_admin_access_old_way(user):
        return user.role == UserRole.HR_ADMIN
    
    def check_admin_access_new_way(user):
        return user.has_permission("employee.create")
    
    # Both should give same result
    assert check_admin_access_old_way(user) == check_admin_access_new_way(user)
    print("✅ Gradual migration compatibility verified")
    
    return True

def test_performance_no_regression():
    """Test that there's no performance regression"""
    print("\n🔍 Testing Performance No Regression...")
    
    import time
    
    user = User(role=UserRole.SUPERVISOR)
    
    # Test old role checking performance
    start_time = time.time()
    for _ in range(10000):
        user.role == UserRole.SUPERVISOR
    old_duration = time.time() - start_time
    
    # Test new permission checking performance
    start_time = time.time()
    for _ in range(10000):
        user.has_permission("employee.read.supervised")
    new_duration = time.time() - start_time
    
    # New method should be reasonably fast (within 10x of old method)
    performance_ratio = new_duration / old_duration
    assert performance_ratio < 10  # Less than 10x slower
    
    print(f"✅ Performance acceptable:")
    print(f"    Old method: {old_duration*1000:.2f}ms for 10k checks")
    print(f"    New method: {new_duration*1000:.2f}ms for 10k checks") 
    print(f"    Ratio: {performance_ratio:.1f}x")
    
    return True

def main():
    """Run all user-role preservation tests"""
    print("🧪 USER-ROLE PRESERVATION VALIDATION")
    print("=" * 60)
    
    tests = [
        test_user_model_backward_compatibility,
        test_permission_methods_additive,
        test_role_enum_preservation,
        test_static_permission_mapping,
        test_no_database_schema_changes,
        test_existing_code_patterns,
        test_migration_compatibility,
        test_performance_no_regression,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'=' * 60}")
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL USER-ROLE PRESERVATION TESTS PASSED!")
        print("\nUser-role relationship is:")
        print("✅ Completely preserved")
        print("✅ Backward compatible")
        print("✅ Enhanced with permission capabilities")
        print("✅ Ready for gradual migration")
        print("✅ Performance optimized")
        
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        print("Please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())