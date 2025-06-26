"""
Unit tests for assignment system (departments, assignment types, assignments)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from hrm_backend.main import app
from hrm_backend.database import get_db, Base
from hrm_backend.models import User, UserRole
from hrm_backend.auth import get_password_hash

# Test database setup
SQLITE_DATABASE_URL = "sqlite:///./test_assignments.db"
engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_test_db():
    """Create test database and tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(setup_test_db):
    """Create test client"""
    return TestClient(app)

@pytest.fixture(scope="module")
def test_users(setup_test_db):
    """Create test users"""
    db = TestingSessionLocal()
    
    # Create HR Admin user
    hr_admin = User(
        username="test_hr_admin",
        email="hr_admin@test.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.HR_ADMIN
    )
    
    # Create Supervisor user
    supervisor = User(
        username="test_supervisor",
        email="supervisor@test.com", 
        password_hash=get_password_hash("testpass123"),
        role=UserRole.SUPERVISOR
    )
    
    # Create Employee user
    employee = User(
        username="test_employee",
        email="employee@test.com",
        password_hash=get_password_hash("testpass123"),
        role=UserRole.EMPLOYEE
    )
    
    db.add_all([hr_admin, supervisor, employee])
    db.commit()
    
    users = {
        "hr_admin": hr_admin,
        "supervisor": supervisor,
        "employee": employee
    }
    
    db.close()
    return users

def login_user(client: TestClient, username: str, password: str = "testpass123"):
    """Helper to login and get session cookies"""
    response = client.post("/api/v1/auth/login", json={
        "username": username,
        "password": password
    })
    assert response.status_code == 200
    return response.cookies

class TestDepartments:
    """Test department management"""
    
    def test_create_department_as_hr_admin(self, client, test_users):
        """HR Admin can create departments"""
        cookies = login_user(client, "test_hr_admin")
        
        department_data = {
            "name": "Test Engineering",
            "description": "Test department for engineering"
        }
        
        response = client.post("/api/v1/departments/", json=department_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Engineering"
        assert data["description"] == "Test department for engineering"
        assert "department_id" in data
    
    def test_create_department_as_employee_forbidden(self, client, test_users):
        """Employee cannot create departments"""
        cookies = login_user(client, "test_employee")
        
        department_data = {
            "name": "Unauthorized Department",
            "description": "Should not be created"
        }
        
        response = client.post("/api/v1/departments/", json=department_data, cookies=cookies)
        assert response.status_code == 403
    
    def test_list_departments_authenticated(self, client, test_users):
        """All authenticated users can list departments"""
        # Create a department first
        hr_cookies = login_user(client, "test_hr_admin")
        client.post("/api/v1/departments/", json={
            "name": "Test Marketing",
            "description": "Marketing department"
        }, cookies=hr_cookies)
        
        # Test with employee
        employee_cookies = login_user(client, "test_employee")
        response = client.get("/api/v1/departments/", cookies=employee_cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert any(dept["name"] == "Test Marketing" for dept in data)
    
    def test_get_department_by_id(self, client, test_users):
        """Get specific department by ID"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create department
        create_response = client.post("/api/v1/departments/", json={
            "name": "Test Finance",
            "description": "Finance operations"
        }, cookies=cookies)
        
        department_id = create_response.json()["department_id"]
        
        # Get department
        response = client.get(f"/api/v1/departments/{department_id}", cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["department_id"] == department_id
        assert data["name"] == "Test Finance"
    
    def test_update_department(self, client, test_users):
        """Update department (HR Admin only)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create department
        create_response = client.post("/api/v1/departments/", json={
            "name": "Old Name",
            "description": "Old description"
        }, cookies=cookies)
        
        department_id = create_response.json()["department_id"]
        
        # Update department
        update_data = {
            "name": "New Name", 
            "description": "New description"
        }
        
        response = client.put(f"/api/v1/departments/{department_id}", json=update_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"
    
    def test_delete_department(self, client, test_users):
        """Delete department (HR Admin only)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create department
        create_response = client.post("/api/v1/departments/", json={
            "name": "To Delete",
            "description": "Will be deleted"
        }, cookies=cookies)
        
        department_id = create_response.json()["department_id"]
        
        # Delete department
        response = client.delete(f"/api/v1/departments/{department_id}", cookies=cookies)
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/v1/departments/{department_id}", cookies=cookies)
        assert get_response.status_code == 404

class TestAssignmentTypes:
    """Test assignment type management"""
    
    def test_create_assignment_type(self, client, test_users):
        """Create assignment type linked to department"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create department first
        dept_response = client.post("/api/v1/departments/", json={
            "name": "Test IT",
            "description": "IT Department"
        }, cookies=cookies)
        
        department_id = dept_response.json()["department_id"]
        
        # Create assignment type
        at_data = {
            "description": "Senior Developer",
            "department_id": department_id
        }
        
        response = client.post("/api/v1/assignment-types/", json=at_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "Senior Developer"
        assert data["department_id"] == department_id
        assert data["department"]["name"] == "Test IT"
    
    def test_create_assignment_type_invalid_department(self, client, test_users):
        """Cannot create assignment type with invalid department"""
        cookies = login_user(client, "test_hr_admin")
        
        at_data = {
            "description": "Invalid Role",
            "department_id": 99999  # Non-existent department
        }
        
        response = client.post("/api/v1/assignment-types/", json=at_data, cookies=cookies)
        assert response.status_code == 400
        assert "Department not found" in response.json()["detail"]
    
    def test_list_assignment_types_by_department(self, client, test_users):
        """Filter assignment types by department"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create departments
        dept1 = client.post("/api/v1/departments/", json={
            "name": "Engineering", 
            "description": "Engineering dept"
        }, cookies=cookies).json()
        
        dept2 = client.post("/api/v1/departments/", json={
            "name": "Sales",
            "description": "Sales dept"
        }, cookies=cookies).json()
        
        # Create assignment types
        client.post("/api/v1/assignment-types/", json={
            "description": "Software Engineer",
            "department_id": dept1["department_id"]
        }, cookies=cookies)
        
        client.post("/api/v1/assignment-types/", json={
            "description": "Sales Rep",
            "department_id": dept2["department_id"]
        }, cookies=cookies)
        
        # Filter by department 1
        response = client.get(f"/api/v1/assignment-types/?department_id={dept1['department_id']}", cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert all(at["department_id"] == dept1["department_id"] for at in data)

class TestAssignments:
    """Test assignment management"""
    
    def test_create_assignment_full_workflow(self, client, test_users):
        """Complete assignment creation workflow"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create department
        dept_response = client.post("/api/v1/departments/", json={
            "name": "Product",
            "description": "Product team"
        }, cookies=cookies)
        department_id = dept_response.json()["department_id"]
        
        # Create assignment type
        at_response = client.post("/api/v1/assignment-types/", json={
            "description": "Product Manager",
            "department_id": department_id
        }, cookies=cookies)
        assignment_type_id = at_response.json()["assignment_type_id"]
        
        # Create employees
        employee1 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "John Doe"},
            "work_email": "john.doe@test.com"
        }, cookies=cookies).json()
        
        employee2 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Jane Smith"},
            "work_email": "jane.smith@test.com"
        }, cookies=cookies).json()
        
        # Create assignment
        assignment_data = {
            "employee_id": employee1["employee_id"],
            "assignment_type_id": assignment_type_id,
            "description": "Lead product development initiatives", 
            "effective_start_date": "2025-01-01",
            "supervisor_ids": [employee2["employee_id"]]
        }
        
        response = client.post("/api/v1/assignments/", json=assignment_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] == employee1["employee_id"]
        assert data["assignment_type_id"] == assignment_type_id
        assert data["description"] == "Lead product development initiatives"
        assert data["effective_start_date"] == "2025-01-01"
        assert len(data["supervisors"]) == 1
        assert data["supervisors"][0]["employee_id"] == employee2["employee_id"]
        assert data["employee"]["person"]["full_name"] == "John Doe"
        assert data["assignment_type"]["description"] == "Product Manager"
        assert data["assignment_type"]["department"]["name"] == "Product"
    
    def test_update_assignment_supervisors(self, client, test_users):
        """Update assignment supervisors"""
        cookies = login_user(client, "test_hr_admin")
        
        # Setup: department, assignment type, employees
        dept = client.post("/api/v1/departments/", json={
            "name": "Operations", "description": "Ops team"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "Operations Analyst", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        emp1 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Employee One"}
        }, cookies=cookies).json()
        
        sup1 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Supervisor One"}
        }, cookies=cookies).json()
        
        sup2 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Supervisor Two"}
        }, cookies=cookies).json()
        
        # Create assignment with one supervisor
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": emp1["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "supervisor_ids": [sup1["employee_id"]]
        }, cookies=cookies).json()
        
        assignment_id = assignment["assignment_id"]
        
        # Update to different supervisors
        response = client.put(f"/api/v1/assignments/{assignment_id}/supervisors", 
                            json=[sup2["employee_id"]], cookies=cookies)
        assert response.status_code == 200
        
        # Verify update
        updated = response.json()["assignment"]
        assert len(updated["supervisors"]) == 1
        assert updated["supervisors"][0]["employee_id"] == sup2["employee_id"]
    
    def test_get_assignments_by_supervisor(self, client, test_users):
        """Get assignments filtered by supervisor"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data (simplified)
        dept = client.post("/api/v1/departments/", json={
            "name": "HR", "description": "Human Resources"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "HR Specialist", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "HR Employee"}
        }, cookies=cookies).json()
        
        supervisor = client.post("/api/v1/employees/", json={
            "person": {"full_name": "HR Manager"}
        }, cookies=cookies).json()
        
        # Create assignment with supervisor
        client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "supervisor_ids": [supervisor["employee_id"]]
        }, cookies=cookies)
        
        # Get assignments by supervisor
        response = client.get(f"/api/v1/assignments/supervisor/{supervisor['employee_id']}", 
                            cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 1
        assert any(sup["employee_id"] == supervisor["employee_id"] 
                  for assignment in data for sup in assignment["supervisors"])
    
    def test_assignment_permission_checks(self, client, test_users):
        """Test role-based permissions for assignments"""
        hr_cookies = login_user(client, "test_hr_admin")
        employee_cookies = login_user(client, "test_employee")
        
        # Create basic test data
        dept = client.post("/api/v1/departments/", json={
            "name": "Test Dept", "description": "Test"
        }, cookies=hr_cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "Test Role", "department_id": dept["department_id"]
        }, cookies=hr_cookies).json()
        
        emp = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Test Employee"}
        }, cookies=hr_cookies).json()
        
        # Employee cannot create assignments
        assignment_data = {
            "employee_id": emp["employee_id"],
            "assignment_type_id": at["assignment_type_id"]
        }
        
        response = client.post("/api/v1/assignments/", json=assignment_data, cookies=employee_cookies)
        assert response.status_code == 403
        
        # Employee can view assignments
        response = client.get("/api/v1/assignments/", cookies=employee_cookies)
        assert response.status_code == 200

class TestAssignmentManagement:
    """Test US-14, US-15, US-17: Assignment management functionality"""
    
    def test_create_assignment_with_primary_flag(self, client, test_users):
        """Test creating assignment with primary flag (US-15)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Setup test data
        dept = client.post("/api/v1/departments/", json={
            "name": "QA Department", "description": "Quality Assurance"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "QA Lead", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "QA Employee"}
        }, cookies=cookies).json()
        
        # Create assignment as primary
        assignment_data = {
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "description": "Primary QA role",
            "is_primary": True
        }
        
        response = client.post("/api/v1/assignments/", json=assignment_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_primary"] is True
        assert data["description"] == "Primary QA role"
    
    def test_set_primary_assignment(self, client, test_users):
        """Test setting an assignment as primary (US-15)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Setup test data
        dept = client.post("/api/v1/departments/", json={
            "name": "DevOps", "description": "DevOps Team"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "DevOps Engineer", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "DevOps Employee"}
        }, cookies=cookies).json()
        
        # Create two assignments
        assignment1 = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "description": "First assignment",
            "is_primary": True
        }, cookies=cookies).json()
        
        assignment2 = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "description": "Second assignment",
            "is_primary": False
        }, cookies=cookies).json()
        
        # Set second assignment as primary
        response = client.put(f"/api/v1/assignments/{assignment2['assignment_id']}/primary", 
                            cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_primary"] is True
        assert data["assignment_id"] == assignment2["assignment_id"]
        
        # Verify first assignment is no longer primary
        first_response = client.get(f"/api/v1/assignments/{assignment1['assignment_id']}", 
                                  cookies=cookies)
        assert first_response.json()["is_primary"] is False
    
    def test_update_assignment(self, client, test_users):
        """Test updating assignment information (US-17)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data
        dept = client.post("/api/v1/departments/", json={
            "name": "Security", "description": "Security Team"
        }, cookies=cookies).json()
        
        at1 = client.post("/api/v1/assignment-types/", json={
            "description": "Security Analyst", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        at2 = client.post("/api/v1/assignment-types/", json={
            "description": "Senior Security Analyst", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Security Employee"}
        }, cookies=cookies).json()
        
        # Create assignment
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at1["assignment_type_id"],
            "description": "Junior security role"
        }, cookies=cookies).json()
        
        # Update assignment
        update_data = {
            "assignment_type_id": at2["assignment_type_id"],
            "description": "Promoted to senior role",
            "is_primary": True
        }
        
        response = client.put(f"/api/v1/assignments/{assignment['assignment_id']}", 
                            json=update_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert data["assignment_type_id"] == at2["assignment_type_id"]
        assert data["description"] == "Promoted to senior role"
        assert data["is_primary"] is True
    
    def test_delete_assignment(self, client, test_users):
        """Test removing an assignment (US-17)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data
        dept = client.post("/api/v1/departments/", json={
            "name": "Legal", "description": "Legal Department"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "Legal Counsel", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Legal Employee"}
        }, cookies=cookies).json()
        
        # Create assignment
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"]
        }, cookies=cookies).json()
        
        assignment_id = assignment["assignment_id"]
        
        # Delete assignment
        response = client.delete(f"/api/v1/assignments/{assignment_id}", cookies=cookies)
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["detail"]
        
        # Verify deletion
        get_response = client.get(f"/api/v1/assignments/{assignment_id}", cookies=cookies)
        assert get_response.status_code == 404
    
    def test_add_supervisor_to_assignment(self, client, test_users):
        """Test adding supervisor to assignment (US-14)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data
        dept = client.post("/api/v1/departments/", json={
            "name": "Research", "description": "Research Team"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "Research Scientist", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Research Employee"}
        }, cookies=cookies).json()
        
        supervisor = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Research Supervisor"}
        }, cookies=cookies).json()
        
        # Create assignment without supervisor
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"]
        }, cookies=cookies).json()
        
        assignment_id = assignment["assignment_id"]
        
        # Add supervisor
        supervisor_data = {
            "supervisor_id": supervisor["employee_id"],
            "effective_start_date": "2025-01-01"
        }
        
        response = client.post(f"/api/v1/assignments/{assignment_id}/supervisors", 
                             json=supervisor_data, cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["supervisors"]) == 1
        assert data["supervisors"][0]["employee_id"] == supervisor["employee_id"]
    
    def test_remove_supervisor_from_assignment(self, client, test_users):
        """Test removing supervisor from assignment (US-14)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data with supervisor
        dept = client.post("/api/v1/departments/", json={
            "name": "Design", "description": "Design Team"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "UI Designer", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Design Employee"}
        }, cookies=cookies).json()
        
        supervisor = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Design Manager"}
        }, cookies=cookies).json()
        
        # Create assignment with supervisor
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "supervisor_ids": [supervisor["employee_id"]]
        }, cookies=cookies).json()
        
        assignment_id = assignment["assignment_id"]
        supervisor_id = supervisor["employee_id"]
        
        # Remove supervisor
        response = client.delete(f"/api/v1/assignments/{assignment_id}/supervisors/{supervisor_id}", 
                               cookies=cookies)
        assert response.status_code == 200
        assert "removed" in response.json()["detail"]
        
        # Verify removal
        get_response = client.get(f"/api/v1/assignments/{assignment_id}", cookies=cookies)
        assert len(get_response.json()["supervisors"]) == 0
    
    def test_get_assignment_supervisors(self, client, test_users):
        """Test getting supervisors for an assignment (US-14)"""
        cookies = login_user(client, "test_hr_admin")
        
        # Create test data
        dept = client.post("/api/v1/departments/", json={
            "name": "Customer Support", "description": "Support Team"
        }, cookies=cookies).json()
        
        at = client.post("/api/v1/assignment-types/", json={
            "description": "Support Agent", "department_id": dept["department_id"]
        }, cookies=cookies).json()
        
        employee = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Support Employee"}
        }, cookies=cookies).json()
        
        supervisor1 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Support Manager 1"}
        }, cookies=cookies).json()
        
        supervisor2 = client.post("/api/v1/employees/", json={
            "person": {"full_name": "Support Manager 2"}
        }, cookies=cookies).json()
        
        # Create assignment with multiple supervisors
        assignment = client.post("/api/v1/assignments/", json={
            "employee_id": employee["employee_id"],
            "assignment_type_id": at["assignment_type_id"],
            "supervisor_ids": [supervisor1["employee_id"], supervisor2["employee_id"]]
        }, cookies=cookies).json()
        
        assignment_id = assignment["assignment_id"]
        
        # Get assignment supervisors
        response = client.get(f"/api/v1/assignments/{assignment_id}/supervisors", cookies=cookies)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 2
        supervisor_ids = [sup["supervisor_id"] for sup in data]
        assert supervisor1["employee_id"] in supervisor_ids
        assert supervisor2["employee_id"] in supervisor_ids