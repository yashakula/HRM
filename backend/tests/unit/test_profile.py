"""
Unit tests for profile page functionality.
Tests the profile page access validation logic.
"""
import pytest
from unittest.mock import Mock, MagicMock
from hrm_backend.models import User, UserRole, Employee, People, PersonalInformation
from hrm_backend.routers.auth import _get_page_permissions


def test_profile_page_access_hr_admin():
    """Test that HR Admin can access profile page"""
    # Mock user
    user = Mock(spec=User)
    user.user_id = 1
    user.role = UserRole.HR_ADMIN
    
    # Mock database
    db = Mock()
    
    # Test profile page access
    permissions = _get_page_permissions("profile", None, user, db)
    
    assert permissions.can_view is True
    assert permissions.can_edit is True
    assert permissions.can_create is False
    assert permissions.can_delete is False
    assert permissions.user_role == "HR_ADMIN"
    assert "All authenticated users can view and edit their own profile" in permissions.message


def test_profile_page_access_supervisor():
    """Test that Supervisor can access profile page"""
    # Mock user
    user = Mock(spec=User)
    user.user_id = 2
    user.role = UserRole.SUPERVISOR
    
    # Mock database
    db = Mock()
    
    # Test profile page access
    permissions = _get_page_permissions("profile", None, user, db)
    
    assert permissions.can_view is True
    assert permissions.can_edit is True
    assert permissions.can_create is False
    assert permissions.can_delete is False
    assert permissions.user_role == "SUPERVISOR"
    assert "All authenticated users can view and edit their own profile" in permissions.message


def test_profile_page_access_employee():
    """Test that Employee can access profile page"""
    # Mock user
    user = Mock(spec=User)
    user.user_id = 3
    user.role = UserRole.EMPLOYEE
    
    # Mock database
    db = Mock()
    
    # Test profile page access
    permissions = _get_page_permissions("profile", None, user, db)
    
    assert permissions.can_view is True
    assert permissions.can_edit is True
    assert permissions.can_create is False
    assert permissions.can_delete is False
    assert permissions.user_role == "EMPLOYEE"
    assert "All authenticated users can view and edit their own profile" in permissions.message


def test_employees_page_access_restrictions():
    """Test that employees page is restricted to HR Admin and Supervisors only"""
    # Test HR Admin access
    hr_user = Mock(spec=User)
    hr_user.user_id = 1
    hr_user.role = UserRole.HR_ADMIN
    
    db = Mock()
    
    permissions = _get_page_permissions("employees", None, hr_user, db)
    assert permissions.can_view is True
    assert permissions.user_role == "HR_ADMIN"
    assert "HR Admin can search all employees" in permissions.message
    
    # Test Supervisor access
    supervisor_user = Mock(spec=User)
    supervisor_user.user_id = 2
    supervisor_user.role = UserRole.SUPERVISOR
    
    permissions = _get_page_permissions("employees", None, supervisor_user, db)
    assert permissions.can_view is True
    assert permissions.user_role == "SUPERVISOR"
    assert "Supervisors can view team members" in permissions.message
    
    # Test Employee denied access
    employee_user = Mock(spec=User)
    employee_user.user_id = 3
    employee_user.role = UserRole.EMPLOYEE
    
    permissions = _get_page_permissions("employees", None, employee_user, db)
    assert permissions.can_view is False
    assert permissions.user_role == "EMPLOYEE"
    assert "Only HR Admin and Supervisors can access employee directory" in permissions.message


def test_departments_page_access_restrictions():
    """Test that departments page is restricted to HR Admin and Supervisors only"""
    # Test HR Admin access (full permissions)
    hr_user = Mock(spec=User)
    hr_user.user_id = 1
    hr_user.role = UserRole.HR_ADMIN
    
    db = Mock()
    
    permissions = _get_page_permissions("departments", None, hr_user, db)
    assert permissions.can_view is True
    assert permissions.can_edit is True
    assert permissions.can_create is True
    assert permissions.can_delete is True
    assert permissions.user_role == "HR_ADMIN"
    assert "HR Admin has full department management access" in permissions.message
    
    # Test Supervisor access (read-only)
    supervisor_user = Mock(spec=User)
    supervisor_user.user_id = 2
    supervisor_user.role = UserRole.SUPERVISOR
    
    permissions = _get_page_permissions("departments", None, supervisor_user, db)
    assert permissions.can_view is True
    assert permissions.can_edit is False
    assert permissions.can_create is False
    assert permissions.can_delete is False
    assert permissions.user_role == "SUPERVISOR"
    assert "Supervisors can view departments" in permissions.message
    
    # Test Employee denied access
    employee_user = Mock(spec=User)
    employee_user.user_id = 3
    employee_user.role = UserRole.EMPLOYEE
    
    permissions = _get_page_permissions("departments", None, employee_user, db)
    assert permissions.can_view is False
    assert permissions.can_edit is False
    assert permissions.can_create is False
    assert permissions.can_delete is False
    assert permissions.user_role == "EMPLOYEE"
    assert "Only HR Admin and Supervisors can access departments" in permissions.message


def test_role_based_navigation_access():
    """Test that navigation properly reflects role-based access"""
    # This test validates the logic that would be used in frontend navigation
    
    def get_navigation_items(user_role):
        """Simulate the navigation logic from frontend"""
        items = [{"href": "/profile", "label": "My Profile"}]  # Always available
        
        if user_role == UserRole.HR_ADMIN:
            items.extend([
                {"href": "/", "label": "Dashboard"},
                {"href": "/employees", "label": "Employees"},
                {"href": "/employees/create", "label": "Create Employee"},
                {"href": "/departments", "label": "Departments"},
                {"href": "/search", "label": "Search"}
            ])
        elif user_role == UserRole.SUPERVISOR:
            items.extend([
                {"href": "/", "label": "Dashboard"},
                {"href": "/employees", "label": "My Team"},
                {"href": "/departments", "label": "Departments"}
            ])
        # Employee role only gets profile (already added above)
        
        return items
    
    # Test HR Admin navigation
    hr_nav = get_navigation_items(UserRole.HR_ADMIN)
    assert len(hr_nav) == 6
    assert any(item["href"] == "/profile" for item in hr_nav)
    assert any(item["href"] == "/employees/create" for item in hr_nav)
    assert any(item["href"] == "/departments" for item in hr_nav)
    
    # Test Supervisor navigation
    supervisor_nav = get_navigation_items(UserRole.SUPERVISOR)
    assert len(supervisor_nav) == 4
    assert any(item["href"] == "/profile" for item in supervisor_nav)
    assert any(item["href"] == "/employees" for item in supervisor_nav)
    assert any(item["href"] == "/departments" for item in supervisor_nav)
    assert not any(item["href"] == "/employees/create" for item in supervisor_nav)
    
    # Test Employee navigation (only profile)
    employee_nav = get_navigation_items(UserRole.EMPLOYEE)
    assert len(employee_nav) == 1
    assert employee_nav[0]["href"] == "/profile"
    assert employee_nav[0]["label"] == "My Profile"