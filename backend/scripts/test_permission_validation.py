#!/usr/bin/env python3
"""
Permission Validation Logic Test Suite

This script tests the enhanced permission validation system including
context-aware validation, ownership checks, and supervision relationships.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from hrm_backend.models import User, UserRole
from hrm_backend.permission_validation import (
    PermissionValidator,
    PermissionResult,
    PermissionContext,
    validate_permission,
    validate_any_permission,
    validate_all_permissions
)

def create_mock_db():
    """Create a mock database session"""
    return Mock()

def create_test_user(role: UserRole) -> User:
    """Create a test user with specified role"""
    user = User(
        user_id=1,
        username=f"test_{role.value.lower()}",
        email=f"test_{role.value.lower()}@company.com",
        password_hash="hashed_password",
        role=role
    )
    return user

def test_basic_permission_validation():
    """Test basic permission validation without context"""
    print("🔍 Testing Basic Permission Validation...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Test HR Admin with global permission
    hr_user = create_test_user(UserRole.HR_ADMIN)
    result = validator.validate_permission(hr_user, "employee.create", db)
    
    assert result.granted == True
    assert result.permission == "employee.create"
    assert result.user_role == "HR_ADMIN"
    assert result.context == PermissionContext.GLOBAL
    print("✅ HR Admin can create employees")
    
    # Test Employee without permission
    employee_user = create_test_user(UserRole.EMPLOYEE)
    result = validator.validate_permission(employee_user, "employee.create", db)
    
    assert result.granted == False
    assert "does not have permission" in result.reason
    print("✅ Employee cannot create employees")
    
    # Test Supervisor with supervised permission (no context)
    supervisor_user = create_test_user(UserRole.SUPERVISOR)
    result = validator.validate_permission(supervisor_user, "employee.search", db)
    
    assert result.granted == True
    assert result.context == PermissionContext.GLOBAL
    print("✅ Supervisor can search employees (global permission)")
    
    return True

def test_ownership_validation():
    """Test ownership-based permission validation"""
    print("\n🔍 Testing Ownership Validation...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Mock the ownership check functions
    import hrm_backend.permission_validation
    original_check_employee_ownership = hrm_backend.permission_validation.check_employee_ownership
    
    def mock_check_employee_ownership(user, employee_id, db):
        # User 1 owns employee 1, User 2 owns employee 2, etc.
        return user.user_id == employee_id
    
    hrm_backend.permission_validation.check_employee_ownership = mock_check_employee_ownership
    
    try:
        # Test employee reading own record
        employee_user = create_test_user(UserRole.EMPLOYEE)
        employee_user.user_id = 1
        
        result = validator.validate_permission(
            employee_user, "employee.read.own", db, resource_id=1
        )
        
        assert result.granted == True
        assert result.context == PermissionContext.RESOURCE_OWNERSHIP
        assert "User owns employee 1" in result.reason
        print("✅ Employee can read own record")
        
        # Test employee reading someone else's record
        result = validator.validate_permission(
            employee_user, "employee.read.own", db, resource_id=2
        )
        
        assert result.granted == False
        assert result.context == PermissionContext.RESOURCE_OWNERSHIP
        assert "does not own employee 2" in result.reason
        print("✅ Employee cannot read other's record")
        
        # Test scoped permission without resource_id
        result = validator.validate_permission(
            employee_user, "employee.read.own", db
        )
        
        assert result.granted == False
        assert "requires resource_id" in result.reason
        print("✅ Scoped permission requires resource_id")
        
    finally:
        # Restore original function
        hrm_backend.permission_validation.check_employee_ownership = original_check_employee_ownership
    
    return True

def test_supervision_validation():
    """Test supervision-based permission validation"""
    print("\n🔍 Testing Supervision Validation...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Mock the supervision check functions
    import hrm_backend.permission_validation
    original_check_supervisor_relationship = hrm_backend.permission_validation.check_supervisor_relationship
    
    def mock_check_supervisor_relationship(user, employee_id, db):
        # Supervisor 1 supervises employees 10-19, Supervisor 2 supervises 20-29, etc.
        supervisor_base = user.user_id * 10
        return supervisor_base <= employee_id < supervisor_base + 10
    
    hrm_backend.permission_validation.check_supervisor_relationship = mock_check_supervisor_relationship
    
    try:
        # Test supervisor reading supervised employee
        supervisor_user = create_test_user(UserRole.SUPERVISOR)
        supervisor_user.user_id = 1
        
        result = validator.validate_permission(
            supervisor_user, "employee.read.supervised", db, resource_id=15
        )
        
        assert result.granted == True
        assert result.context == PermissionContext.SUPERVISION
        assert "supervises employee 15" in result.reason
        print("✅ Supervisor can read supervised employee")
        
        # Test supervisor reading non-supervised employee
        result = validator.validate_permission(
            supervisor_user, "employee.read.supervised", db, resource_id=25
        )
        
        assert result.granted == False
        assert "does not supervise employee 25" in result.reason
        print("✅ Supervisor cannot read non-supervised employee")
        
    finally:
        # Restore original function
        hrm_backend.permission_validation.check_supervisor_relationship = original_check_supervisor_relationship
    
    return True

def test_global_permissions():
    """Test global permissions (all scope)"""
    print("\n🔍 Testing Global Permissions...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Test HR Admin with global permission
    hr_user = create_test_user(UserRole.HR_ADMIN)
    result = validator.validate_permission(
        hr_user, "employee.read.all", db, resource_id=999
    )
    
    assert result.granted == True
    assert result.context == PermissionContext.GLOBAL
    assert "Global access permission granted" in result.reason
    print("✅ HR Admin has global access regardless of resource_id")
    
    # Test Employee without global permission
    employee_user = create_test_user(UserRole.EMPLOYEE)
    result = validator.validate_permission(
        employee_user, "employee.read.all", db, resource_id=1
    )
    
    assert result.granted == False
    assert "does not have permission" in result.reason
    print("✅ Employee doesn't have global permission")
    
    return True

def test_any_permission_validation():
    """Test any permission validation"""
    print("\n🔍 Testing Any Permission Validation...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Mock ownership check
    import hrm_backend.permission_validation
    original_check_employee_ownership = hrm_backend.permission_validation.check_employee_ownership
    hrm_backend.permission_validation.check_employee_ownership = lambda u, e, d: u.user_id == e
    
    try:
        # Test employee with any permission (should match own)
        employee_user = create_test_user(UserRole.EMPLOYEE)
        employee_user.user_id = 1
        
        result = validator.validate_any_permission(
            employee_user,
            ["employee.read.all", "employee.read.supervised", "employee.read.own"],
            db,
            resource_id=1
        )
        
        assert result.granted == True
        assert "employee.read.own" in result.permission
        print("✅ Employee granted access via 'own' permission")
        
        # Test employee without any permission
        result = validator.validate_any_permission(
            employee_user,
            ["employee.create", "employee.delete"],
            db,
            resource_id=1
        )
        
        assert result.granted == False
        assert "does not have any of the required permissions" in result.reason
        print("✅ Employee denied when no permissions match")
        
    finally:
        hrm_backend.permission_validation.check_employee_ownership = original_check_employee_ownership
    
    return True

def test_all_permissions_validation():
    """Test all permissions validation"""
    print("\n🔍 Testing All Permissions Validation...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    
    # Test employee with partial permissions - employee.create is not in employee's permissions
    employee_user = create_test_user(UserRole.EMPLOYEE)
    
    result = validator.validate_all_permissions(
        employee_user,
        ["employee.create", "department.create"],  # Employee has neither of these
        db
    )
    
    assert result.granted == False
    # Debug the result to see what we get
    print(f"    Debug: result.permission = {result.permission}")
    print(f"    Debug: result.reason = {result.reason}")
    # The result should be the failed permission validation result for employee.create
    assert result.permission == "employee.create" or "employee.create" in result.reason
    print("✅ Employee denied when missing one of required permissions")
    
    # Test employee with all required permissions
    result = validator.validate_all_permissions(
        employee_user,
        ["department.read", "assignment_type.read"],  # Employee has both
        db
    )
    
    assert result.granted == True
    assert "has all required permissions" in result.reason
    print("✅ Employee granted when has all required permissions")
    
    return True

def test_permission_result_object():
    """Test PermissionResult object functionality"""
    print("\n🔍 Testing PermissionResult Object...")
    
    # Test successful result
    success_result = PermissionResult(
        granted=True,
        permission="test.permission",
        user_role="EMPLOYEE",
        context=PermissionContext.GLOBAL,
        reason="Test successful",
        resource_id=123,
        debug_info={"test": "data"}
    )
    
    assert bool(success_result) == True
    assert "GRANTED" in str(success_result)
    assert success_result.resource_id == 123
    print("✅ Successful PermissionResult works correctly")
    
    # Test failed result
    failed_result = PermissionResult(
        granted=False,
        permission="test.permission",
        user_role="EMPLOYEE",
        context=PermissionContext.RESOURCE_OWNERSHIP,
        reason="Test failed",
        resource_id=456
    )
    
    assert bool(failed_result) == False
    assert "DENIED" in str(failed_result)
    assert failed_result.debug_info == {}  # Default empty dict
    print("✅ Failed PermissionResult works correctly")
    
    return True

def test_convenience_functions():
    """Test convenience functions"""
    print("\n🔍 Testing Convenience Functions...")
    
    db = create_mock_db()
    hr_user = create_test_user(UserRole.HR_ADMIN)
    
    # Test validate_permission convenience function
    result = validate_permission(hr_user, "employee.create", db)
    assert result.granted == True
    print("✅ validate_permission convenience function works")
    
    # Test validate_any_permission convenience function
    result = validate_any_permission(
        hr_user, ["employee.create", "employee.delete"], db
    )
    assert result.granted == True
    print("✅ validate_any_permission convenience function works")
    
    # Test validate_all_permissions convenience function
    result = validate_all_permissions(
        hr_user, ["employee.create", "department.create"], db
    )
    assert result.granted == True
    print("✅ validate_all_permissions convenience function works")
    
    return True

def test_error_handling():
    """Test error handling in permission validation"""
    print("\n🔍 Testing Error Handling...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    employee_user = create_test_user(UserRole.EMPLOYEE)
    
    # Test invalid permission format
    result = validator.validate_permission(employee_user, "invalid", db)
    assert result.granted == False
    assert "Invalid permission format" in result.reason
    print("✅ Invalid permission format handled correctly")
    
    # Test exception in ownership validation
    import hrm_backend.permission_validation
    original_func = hrm_backend.permission_validation.check_employee_ownership
    
    def failing_ownership_check(*args):
        raise Exception("Database error")
    
    hrm_backend.permission_validation.check_employee_ownership = failing_ownership_check
    
    try:
        result = validator.validate_permission(
            employee_user, "employee.read.own", db, resource_id=1
        )
        assert result.granted == False
        assert "Ownership validation error" in result.reason
        print("✅ Exception in ownership validation handled correctly")
    finally:
        hrm_backend.permission_validation.check_employee_ownership = original_func
    
    return True

def test_debug_information():
    """Test debug information collection"""
    print("\n🔍 Testing Debug Information...")
    
    validator = PermissionValidator(enable_debug=True)
    db = create_mock_db()
    hr_user = create_test_user(UserRole.HR_ADMIN)
    
    result = validator.validate_permission(
        hr_user, "employee.create", db, resource_id=123, resource_type="employee"
    )
    
    # Check debug info
    debug_info = result.debug_info
    assert debug_info["user_id"] == hr_user.user_id
    assert debug_info["username"] == hr_user.username
    assert debug_info["permission_requested"] == "employee.create"
    assert debug_info["resource_id"] == 123
    assert debug_info["resource_type"] == "employee"
    assert debug_info["parsed_resource"] == "employee"
    assert debug_info["parsed_action"] == "create"
    print("✅ Debug information collected correctly")
    
    return True

def main():
    """Run all permission validation tests"""
    print("🧪 PERMISSION VALIDATION LOGIC TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_basic_permission_validation,
        test_ownership_validation,
        test_supervision_validation,
        test_global_permissions,
        test_any_permission_validation,
        test_all_permissions_validation,
        test_permission_result_object,
        test_convenience_functions,
        test_error_handling,
        test_debug_information,
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
    
    print(f"\n{'=' * 70}")
    print(f"VALIDATION RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL PERMISSION VALIDATION TESTS PASSED!")
        print("\nPermission validation system:")
        print("✅ Basic permission checking works")
        print("✅ Context-aware validation functional")
        print("✅ Ownership validation integrated")
        print("✅ Supervision validation integrated") 
        print("✅ Any/All permission logic works")
        print("✅ Error handling robust")
        print("✅ Debug information comprehensive")
        print("✅ Ready for integration with decorators")
        
        return 0
    else:
        print(f"❌ {total - passed} tests failed")
        print("Please fix the issues above before proceeding")
        return 1

if __name__ == "__main__":
    sys.exit(main())