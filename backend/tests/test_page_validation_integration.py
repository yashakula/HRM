"""
Integration test suite for page validation API endpoint
Tests Task 2.1: Server-Side Route Protection implementation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from src.hrm_backend.main import app
from src.hrm_backend.models import Base, User, Employee, People, UserRole, EmployeeStatus
from src.hrm_backend.database import get_db
from src.hrm_backend.auth import create_session_token

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_page_validation_integration.db"
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
def hr_admin_user(db_session):
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
    
    # Create session token
    token = create_session_token(user.user_id)
    return {"user": user, "token": token}

@pytest.fixture
def employee_user(db_session):
    """Create Employee user with session token and employee record"""
    user = User(
        username="employee",
        email="employee@example.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Create person and employee record
    person = People(
        full_name="John Developer",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="john.developer@company.com",
        effective_start_date=date(2023, 1, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(employee)
    
    # Create session token
    token = create_session_token(user.user_id)
    return {"user": user, "employee": employee, "token": token}

class TestPageValidationEndpoint:
    """Test the page validation API endpoint"""
    
    def test_hr_admin_can_create_employees(self, client, hr_admin_user, db_session):
        """Test that HR Admin can access employee creation page"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"},
            cookies={"session_token": hr_admin_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_identifier"] == "employees/create"
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is True
        assert data["permissions"]["user_role"] == "HR_ADMIN"
        assert "HR_ADMIN" in data["permissions"]["required_permissions"]
    
    def test_employee_cannot_create_employees(self, client, employee_user, db_session):
        """Test that Employee cannot access employee creation page"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"},
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["page_identifier"] == "employees/create"
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert data["permissions"]["can_create"] is False
        assert data["permissions"]["user_role"] == "EMPLOYEE"
        assert "Only HR Admin can create employees" in data["permissions"]["message"]
    
    def test_hr_admin_can_manage_departments(self, client, hr_admin_user, db_session):
        """Test that HR Admin can access departments page"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "departments"},
            cookies={"session_token": hr_admin_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is True
        assert data["permissions"]["can_edit"] is True
        assert data["permissions"]["can_delete"] is True
        assert "HR Admin has full department management access" in data["permissions"]["message"]
    
    def test_employee_cannot_access_departments(self, client, employee_user, db_session):
        """Test that Employee cannot access departments page"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "departments"},
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert "Only HR Admin can manage departments" in data["permissions"]["message"]
    
    def test_employee_can_view_own_profile(self, client, employee_user, db_session):
        """Test that employee can view their own profile"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/view",
                "resource_id": employee_user["employee"].employee_id
            },
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_edit"] is True
        assert data["resource_id"] == employee_user["employee"].employee_id
        assert "Employee can view and edit their own profile" in data["permissions"]["message"]
    
    def test_employee_cannot_edit_other_profile(self, client, employee_user, db_session):
        """Test that employee cannot edit other employee profiles"""
        # Use a different employee ID
        other_employee_id = 999
        
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={
                "page_identifier": "employees/edit",
                "resource_id": other_employee_id
            },
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is False
        assert data["permissions"]["can_view"] is False
        assert data["permissions"]["can_edit"] is False
        assert "Only HR Admin or employee themselves can edit employee profiles" in data["permissions"]["message"]
    
    def test_all_users_can_search_employees(self, client, employee_user, db_session):
        """Test that all authenticated users can search employees"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees"},
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is False
        assert data["permissions"]["can_edit"] is False
        assert "All authenticated users can search employees" in data["permissions"]["message"]
    
    def test_unauthenticated_user_gets_401(self, client, db_session):
        """Test that unauthenticated users get 401 error"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"}
            # No session token
        )
        
        assert response.status_code == 401
    
    def test_invalid_page_identifier_gets_default_permissions(self, client, employee_user, db_session):
        """Test that unknown page identifiers get default permissions"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "unknown/page"},
            cookies={"session_token": employee_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["access_granted"] is True
        assert data["permissions"]["can_view"] is True
        assert data["permissions"]["can_create"] is False
        assert data["permissions"]["can_edit"] is False
        assert "Basic page access for authenticated users" in data["permissions"]["message"]

class TestPageValidationResponseFormat:
    """Test the response format of page validation endpoint"""
    
    def test_response_has_required_fields(self, client, hr_admin_user, db_session):
        """Test that response has all required fields"""
        response = client.post(
            "/api/v1/auth/validate-page-access",
            json={"page_identifier": "employees/create"},
            cookies={"session_token": hr_admin_user["token"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check top-level fields
        assert "page_identifier" in data
        assert "resource_id" in data
        assert "permissions" in data
        assert "access_granted" in data
        
        # Check permissions object
        permissions = data["permissions"]
        assert "can_view" in permissions
        assert "can_edit" in permissions
        assert "can_create" in permissions
        assert "can_delete" in permissions
        assert "message" in permissions
        assert "user_role" in permissions
        assert "required_permissions" in permissions
        
        # Check types
        assert isinstance(permissions["can_view"], bool)
        assert isinstance(permissions["can_edit"], bool)
        assert isinstance(permissions["can_create"], bool)
        assert isinstance(permissions["can_delete"], bool)
        assert isinstance(permissions["message"], str)
        assert isinstance(permissions["user_role"], str)
        assert isinstance(permissions["required_permissions"], list)