"""
Test suite for enhanced frontend role checking features
Tests Task 2.2: Enhanced Frontend Role Checking implementation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from src.hrm_backend.main import app
from src.hrm_backend.models import (
    Base, User, Employee, People, PersonalInformation, UserRole, EmployeeStatus,
    Assignment, AssignmentType, Department, AssignmentSupervisor
)
from src.hrm_backend.database import get_db
from src.hrm_backend.auth import create_session_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_enhanced_frontend_role.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

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
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def hr_admin_user_with_token(db_session):
    """Create HR Admin user with session token"""
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
    
    token = create_session_token(user.user_id)
    return {"user": user, "token": token}

@pytest.fixture
def supervisor_user_with_token(db_session):
    """Create Supervisor user with employee record and session token"""
    user = User(
        username="supervisor",
        email="supervisor@example.com",
        password_hash="hashed_password",
        role=UserRole.SUPERVISOR,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    person = People(
        full_name="Jane Manager",
        date_of_birth=date(1980, 3, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="jane.manager@company.com"
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(employee)
    
    token = create_session_token(user.user_id)
    return {"user": user, "employee": employee, "token": token}

@pytest.fixture
def employee_user_with_token(db_session):
    """Create Employee user with employee record and session token"""
    user = User(
        username="employee",
        email="employee@example.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    person = People(
        full_name="John Developer",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    personal_info = PersonalInformation(
        people_id=person.people_id,
        personal_email="john.dev@personal.com",
        ssn="123-45-6789",
        bank_account="9876543210"
    )
    db_session.add(personal_info)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="john.developer@company.com"
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(employee)
    
    token = create_session_token(user.user_id)
    return {"user": user, "employee": employee, "token": token}

class TestEnhancedEmployeeAccess:
    """Test enhanced employee access validation with server-side checks"""
    
    def test_hr_admin_can_access_any_employee(self, client, hr_admin_user_with_token, employee_user_with_token, db_session):
        """Test that HR Admin can access any employee record"""
        employee_id = employee_user_with_token["employee"].employee_id
        
        # Test view permission
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": employee_id
            },
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_edit"] is True
        assert "HR Admin can view and edit any employee" in data["permissions"]["message"]
        
        # Test edit permission
        edit_response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/edit",
                "resource_id": employee_id
            },
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        assert edit_response.status_code == 200
        edit_data = edit_response.json()
        assert edit_data["access_granted"] is True
        assert edit_data["permissions"]["can_edit"] is True
    
    def test_employee_can_access_own_record(self, client, employee_user_with_token, db_session):
        """Test that employee can access their own record with enhanced validation"""
        employee_id = employee_user_with_token["employee"].employee_id
        
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": employee_id
            },
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_edit"] is True
        assert "Employee can view and edit their own profile" in data["permissions"]["message"]
    
    def test_employee_cannot_access_other_record(self, client, employee_user_with_token, supervisor_user_with_token, db_session):
        """Test that employee cannot access other employee records"""
        other_employee_id = supervisor_user_with_token["employee"].employee_id
        
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": other_employee_id
            },
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert "Insufficient permissions" in data["permissions"]["message"]

class TestUIElementPermissions:
    """Test UI element hiding based on server-side permissions"""
    
    def test_sensitive_field_access_hr_admin(self, client, hr_admin_user_with_token, db_session):
        """Test that HR Admin can access sensitive fields"""
        # HR Admin should be able to create employees (which includes sensitive fields)
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"},
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is True
        assert "HR Admin can create employees" in data["permissions"]["message"]
    
    def test_sensitive_field_access_employee(self, client, employee_user_with_token, db_session):
        """Test that regular employees cannot access sensitive creation fields"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"},
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert data["permissions"]["can_create"] is False
        assert "Only HR Admin can create employees" in data["permissions"]["message"]
    
    def test_employee_can_view_own_sensitive_data(self, client, employee_user_with_token, db_session):
        """Test that employee can view their own sensitive data"""
        employee_id = employee_user_with_token["employee"].employee_id
        
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": employee_id
            },
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        # Employee should be able to view their own complete data

class TestActionButtonPermissions:
    """Test action button visibility based on permissions"""
    
    def test_department_management_actions_hr_admin(self, client, hr_admin_user_with_token, db_session):
        """Test that HR Admin can see all department management actions"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "departments"},
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is True
        assert data["permissions"]["can_edit"] is True
        assert data["permissions"]["can_delete"] is True
        assert "HR Admin has full department management access" in data["permissions"]["message"]
    
    def test_department_management_actions_employee(self, client, employee_user_with_token, db_session):
        """Test that employees cannot see department management actions"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "departments"},
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert data["permissions"]["can_create"] is False
        assert data["permissions"]["can_edit"] is False
        assert data["permissions"]["can_delete"] is False
        assert "Only HR Admin can manage departments" in data["permissions"]["message"]
    
    def test_employee_edit_button_ownership(self, client, employee_user_with_token, supervisor_user_with_token, db_session):
        """Test that edit button appears only for owned employee records"""
        own_employee_id = employee_user_with_token["employee"].employee_id
        other_employee_id = supervisor_user_with_token["employee"].employee_id
        
        # Can edit own record
        own_response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/edit",
                "resource_id": own_employee_id
            },
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert own_response.status_code == 200
        own_data = own_response.json()
        assert own_data["access_granted"] is True
        assert own_data["permissions"]["can_edit"] is True
        
        # Cannot edit other's record
        other_response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/edit",
                "resource_id": other_employee_id
            },
            cookies={"session_token": employee_user_with_token["token"]}
        )
        
        assert other_response.status_code == 200
        other_data = other_response.json()
        assert other_data["access_granted"] is False
        assert other_data["permissions"]["can_edit"] is False

class TestPermissionCaching:
    """Test permission caching behavior for performance"""
    
    def test_multiple_same_requests_efficient(self, client, hr_admin_user_with_token, db_session):
        """Test that multiple requests for same permissions are handled efficiently"""
        # Make multiple identical requests
        page_config = {"page_identifier": "employees/create"}
        token = hr_admin_user_with_token["token"]
        
        responses = []
        for _ in range(3):
            response = client.post(
                "/api/v1/auth/validate-page-access",
                json=page_config,
                cookies={"session_token": token}
            )
            responses.append(response)
        
        # All should succeed with consistent results
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["access_granted"] is True
            assert data["permissions"]["can_create"] is True
    
    def test_different_resources_different_permissions(self, client, employee_user_with_token, supervisor_user_with_token, db_session):
        """Test that different resource IDs return different permissions correctly"""
        own_employee_id = employee_user_with_token["employee"].employee_id
        other_employee_id = supervisor_user_with_token["employee"].employee_id
        token = employee_user_with_token["token"]
        
        # Check own resource
        own_response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": own_employee_id
            },
            cookies={"session_token": token}
        )
        
        # Check other resource
        other_response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": other_employee_id
            },
            cookies={"session_token": token}
        )
        
        assert own_response.status_code == 200
        assert other_response.status_code == 200
        
        own_data = own_response.json()
        other_data = other_response.json()
        
        # Should have different permissions
        assert own_data["access_granted"] is True
        assert other_data["access_granted"] is False
        assert own_data["permissions"]["can_view"] is True
        assert other_data["permissions"]["can_view"] is False

class TestErrorHandling:
    """Test error handling in permission validation"""
    
    def test_invalid_resource_id(self, client, hr_admin_user_with_token, db_session):
        """Test handling of invalid resource IDs"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": 99999  # Non-existent employee
            },
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        # Should still return valid response (HR Admin can attempt to access any resource)
        assert response.status_code == 200
        data = response.json()
        assert data["permissions"]["user_role"] == "HR_ADMIN"
    
    def test_missing_page_identifier(self, client, hr_admin_user_with_token, db_session):
        """Test handling of missing page identifier"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={},  # Missing page_identifier
            cookies={"session_token": hr_admin_user_with_token["token"]}
        )
        
        # Should return validation error
        assert response.status_code == 422  # Validation error