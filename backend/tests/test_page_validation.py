"""
Test suite for page access validation endpoint
Tests Task 2.1.1: Create role validation API endpoints implementation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from sqlalchemy.orm import Session
from src.hrm_backend.models import (
    Base, User, Employee, People, PersonalInformation, UserRole, EmployeeStatus,
    Assignment, AssignmentType, Department, AssignmentSupervisor
)
from src.hrm_backend.routers.auth import _get_page_permissions
from src.hrm_backend import schemas

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_page_validation.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def hr_admin_user(db_session):
    """Create HR Admin user"""
    user = User(
        username="hr_admin",
        email="hr@example.com",
        password_hash="hashed_password",
        role=UserRole.HR_ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def supervisor_user(db_session):
    """Create Supervisor user"""
    user = User(
        username="supervisor",
        email="supervisor@example.com", 
        password_hash="hashed_password",
        role=UserRole.SUPERVISOR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def employee_user(db_session):
    """Create Employee user"""
    user = User(
        username="employee",
        email="employee@example.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def employee_record(db_session, employee_user):
    """Create employee record linked to employee_user"""
    person = People(
        full_name="John Developer",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=employee_user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="john.developer@company.com",
        effective_start_date=date(2023, 1, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def supervisor_employee_record(db_session, supervisor_user):
    """Create supervisor employee record"""
    person = People(
        full_name="Jane Manager", 
        date_of_birth=date(1980, 3, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=supervisor_user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="jane.manager@company.com",
        effective_start_date=date(2020, 1, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def other_employee_record(db_session):
    """Create another employee record (no user association)"""
    person = People(
        full_name="Bob Tester",
        date_of_birth=date(1985, 5, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=None,  # No user association
        status=EmployeeStatus.ACTIVE,
        work_email="bob.tester@company.com",
        effective_start_date=date(2022, 6, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

class TestEmployeeCreationPageAccess:
    """Test employee creation page access permissions"""
    
    def test_hr_admin_can_create_employees(self, db_session, hr_admin_user):
        """Test that HR Admin can access employee creation page"""
        permissions = _get_page_permissions("employees/create", None, hr_admin_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is True
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "HR_ADMIN"
        assert "HR_ADMIN" in permissions.required_permissions
        assert "HR Admin can create employees" in permissions.message
    
    def test_supervisor_cannot_create_employees(self, db_session, supervisor_user):
        """Test that Supervisor cannot access employee creation page"""
        permissions = _get_page_permissions("employees/create", None, supervisor_user, db_session)
        
        assert permissions.can_view is False
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "SUPERVISOR"
        assert "HR_ADMIN" in permissions.required_permissions
        assert "Only HR Admin can create employees" in permissions.message
    
    def test_employee_cannot_create_employees(self, db_session, employee_user):
        """Test that Employee cannot access employee creation page"""
        permissions = _get_page_permissions("employees/create", None, employee_user, db_session)
        
        assert permissions.can_view is False
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "HR_ADMIN" in permissions.required_permissions

class TestDepartmentPageAccess:
    """Test department management page access permissions"""
    
    def test_hr_admin_can_manage_departments(self, db_session, hr_admin_user):
        """Test that HR Admin has full department access"""
        permissions = _get_page_permissions("departments", None, hr_admin_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is True
        assert permissions.can_edit is True
        assert permissions.can_delete is True
        assert permissions.user_role == "HR_ADMIN"
        assert "HR_ADMIN" in permissions.required_permissions
        assert "HR Admin has full department management access" in permissions.message
    
    def test_non_hr_admin_cannot_access_departments(self, db_session, supervisor_user):
        """Test that non-HR Admin users cannot access departments"""
        permissions = _get_page_permissions("departments", None, supervisor_user, db_session)
        
        assert permissions.can_view is False
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "SUPERVISOR"
        assert "Only HR Admin can manage departments" in permissions.message

class TestEmployeeProfilePageAccess:
    """Test employee profile page access with resource IDs"""
    
    def test_hr_admin_can_view_any_employee(self, db_session, hr_admin_user, other_employee_record):
        """Test that HR Admin can view any employee profile"""
        permissions = _get_page_permissions("employees/view", other_employee_record.employee_id, hr_admin_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_edit is True
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "HR_ADMIN"
        assert "HR Admin can view and edit any employee" in permissions.message
    
    def test_employee_can_view_own_profile(self, db_session, employee_user, employee_record):
        """Test that employee can view their own profile"""
        permissions = _get_page_permissions("employees/view", employee_record.employee_id, employee_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_edit is True
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "resource_owner" in permissions.required_permissions
        assert "Employee can view and edit their own profile" in permissions.message
    
    def test_employee_cannot_view_other_profile(self, db_session, employee_user, other_employee_record):
        """Test that employee cannot view other employee profiles"""
        permissions = _get_page_permissions("employees/view", other_employee_record.employee_id, employee_user, db_session)
        
        assert permissions.can_view is False
        assert permissions.can_edit is False
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "Insufficient permissions to access this employee profile" in permissions.message

class TestEmployeeEditPageAccess:
    """Test employee edit page access permissions"""
    
    def test_hr_admin_can_edit_any_employee(self, db_session, hr_admin_user, other_employee_record):
        """Test that HR Admin can edit any employee"""
        permissions = _get_page_permissions("employees/edit", other_employee_record.employee_id, hr_admin_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_edit is True
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "HR_ADMIN"
        assert "HR Admin can edit any employee" in permissions.message
    
    def test_employee_can_edit_own_profile(self, db_session, employee_user, employee_record):
        """Test that employee can edit their own profile"""
        permissions = _get_page_permissions("employees/edit", employee_record.employee_id, employee_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_edit is True
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "resource_owner" in permissions.required_permissions
    
    def test_supervisor_cannot_edit_employees(self, db_session, supervisor_user, other_employee_record):
        """Test that supervisor cannot edit employee profiles"""
        permissions = _get_page_permissions("employees/edit", other_employee_record.employee_id, supervisor_user, db_session)
        
        assert permissions.can_view is False
        assert permissions.can_edit is False
        assert permissions.can_create is False
        assert permissions.can_delete is False
        assert permissions.user_role == "SUPERVISOR"
        assert "Only HR Admin or employee themselves can edit employee profiles" in permissions.message

class TestAssignmentPageAccess:
    """Test assignment management page access permissions"""
    
    def test_hr_admin_can_manage_assignments(self, db_session, hr_admin_user):
        """Test that HR Admin has full assignment management access"""
        permissions = _get_page_permissions("assignments", None, hr_admin_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is True
        assert permissions.can_edit is True
        assert permissions.can_delete is True
        assert permissions.user_role == "HR_ADMIN"
        assert "HR Admin has full assignment management access" in permissions.message
    
    def test_non_hr_admin_can_view_assignments(self, db_session, employee_user):
        """Test that non-HR Admin users can view but not manage assignments"""
        permissions = _get_page_permissions("assignments", None, employee_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "Users can view assignments but cannot manage them" in permissions.message

class TestEmployeeSearchPageAccess:
    """Test employee search/list page access permissions"""
    
    def test_all_users_can_search_employees(self, db_session, employee_user):
        """Test that all authenticated users can search employees"""
        permissions = _get_page_permissions("employees", None, employee_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "authenticated" in permissions.required_permissions
        assert "All authenticated users can search employees" in permissions.message

class TestDefaultPageAccess:
    """Test default page access for unknown pages"""
    
    def test_default_page_access_for_authenticated_users(self, db_session, employee_user):
        """Test that authenticated users get basic access to unknown pages"""
        permissions = _get_page_permissions("unknown/page", None, employee_user, db_session)
        
        assert permissions.can_view is True
        assert permissions.can_create is False
        assert permissions.can_edit is False
        assert permissions.can_delete is False
        assert permissions.user_role == "EMPLOYEE"
        assert "authenticated" in permissions.required_permissions
        assert "Basic page access for authenticated users" in permissions.message

class TestPermissionAttributes:
    """Test that permission objects have correct attributes"""
    
    def test_permission_object_structure(self, db_session, hr_admin_user):
        """Test that permission object has all required attributes"""
        permissions = _get_page_permissions("employees/create", None, hr_admin_user, db_session)
        
        # Check all required attributes exist
        assert hasattr(permissions, 'can_view')
        assert hasattr(permissions, 'can_edit')
        assert hasattr(permissions, 'can_create')
        assert hasattr(permissions, 'can_delete')
        assert hasattr(permissions, 'message')
        assert hasattr(permissions, 'user_role')
        assert hasattr(permissions, 'required_permissions')
        
        # Check types
        assert isinstance(permissions.can_view, bool)
        assert isinstance(permissions.can_edit, bool)
        assert isinstance(permissions.can_create, bool)
        assert isinstance(permissions.can_delete, bool)
        assert isinstance(permissions.message, str)
        assert isinstance(permissions.user_role, str)
        assert isinstance(permissions.required_permissions, list)