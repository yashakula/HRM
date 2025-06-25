import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

from hrm_backend.main import app
from hrm_backend.database import get_db
from hrm_backend.models import Base, User, UserRole, Department, AssignmentType
from hrm_backend.auth import get_current_active_user

# Create test database
SQLITE_DATABASE_URL = "sqlite:///./test_departments.db"
engine = create_engine(SQLITE_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def hr_admin_user():
    """Mock HR admin user for authentication"""
    user = Mock()
    user.user_id = 1
    user.username = "hradmin"
    user.email = "hr@company.com"
    user.role = UserRole.HR_ADMIN
    user.is_active = True
    return user

@pytest.fixture
def authenticated_client(client, hr_admin_user):
    """Client with HR admin authentication"""
    app.dependency_overrides[get_current_active_user] = lambda: hr_admin_user
    yield client
    # Clean up override
    if get_current_active_user in app.dependency_overrides:
        del app.dependency_overrides[get_current_active_user]

class TestDepartmentCRUD:
    """Test department CRUD operations with assignment types"""
    
    def test_create_department_without_assignment_types(self, db, authenticated_client):
        """Test creating a department without assignment types"""
        response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Engineering",
                "description": "Software development team"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Engineering"
        assert data["description"] == "Software development team"
        assert data["assignment_types"] == []
    
    def test_create_department_with_assignment_types(self, db, authenticated_client):
        """Test creating a department with assignment types"""
        response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Engineering",
                "description": "Software development team",
                "assignment_types": ["Software Engineer", "Senior Engineer", "Tech Lead"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Engineering"
        assert len(data["assignment_types"]) == 3
        assignment_type_descriptions = [at["description"] for at in data["assignment_types"]]
        assert "Software Engineer" in assignment_type_descriptions
        assert "Senior Engineer" in assignment_type_descriptions
        assert "Tech Lead" in assignment_type_descriptions
    
    def test_get_department_with_assignment_types(self, db, authenticated_client):
        """Test retrieving a department with its assignment types"""
        # First create a department
        create_response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Marketing",
                "description": "Marketing and sales team",
                "assignment_types": ["Marketing Manager", "Sales Rep"]
            }
        )
        department_id = create_response.json()["department_id"]
        
        # Then retrieve it
        response = authenticated_client.get(f"/api/v1/departments/{department_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Marketing"
        assert len(data["assignment_types"]) == 2
    
    def test_list_departments_with_assignment_types(self, db, authenticated_client):
        """Test listing all departments with their assignment types"""
        # Create multiple departments
        authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Engineering",
                "assignment_types": ["Software Engineer"]
            }
        )
        authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "HR",
                "assignment_types": ["HR Manager", "Recruiter"]
            }
        )
        
        response = authenticated_client.get("/api/v1/departments/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Check that assignment types are included
        for dept in data:
            assert "assignment_types" in dept
            assert isinstance(dept["assignment_types"], list)
    
    def test_update_department_add_assignment_types(self, db, authenticated_client):
        """Test updating a department to add assignment types"""
        # Create a department without assignment types
        create_response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Finance",
                "description": "Financial operations"
            }
        )
        department_id = create_response.json()["department_id"]
        
        # Update to add assignment types
        response = authenticated_client.put(
            f"/api/v1/departments/{department_id}",
            json={
                "name": "Finance",
                "description": "Financial operations and accounting",
                "assignment_types_to_add": ["Accountant", "Financial Analyst"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["assignment_types"]) == 2
        assignment_type_descriptions = [at["description"] for at in data["assignment_types"]]
        assert "Accountant" in assignment_type_descriptions
        assert "Financial Analyst" in assignment_type_descriptions
    
    def test_update_department_remove_assignment_types(self, db, authenticated_client):
        """Test updating a department to remove assignment types"""
        # Create a department with assignment types
        create_response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Operations",
                "assignment_types": ["Operations Manager", "Coordinator", "Analyst"]
            }
        )
        data = create_response.json()
        department_id = data["department_id"]
        
        # Get the assignment type ID to remove
        assignment_type_to_remove = data["assignment_types"][0]["assignment_type_id"]
        
        # Update to remove one assignment type
        response = authenticated_client.put(
            f"/api/v1/departments/{department_id}",
            json={
                "assignment_types_to_remove": [assignment_type_to_remove]
            }
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert len(updated_data["assignment_types"]) == 2
        
        # Verify the specific assignment type was removed
        remaining_descriptions = [at["description"] for at in updated_data["assignment_types"]]
        assert "Operations Manager" not in remaining_descriptions
    
    def test_update_department_add_and_remove_assignment_types(self, db, authenticated_client):
        """Test updating a department to both add and remove assignment types"""
        # Create a department with assignment types
        create_response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Product",
                "assignment_types": ["Product Manager", "Designer"]
            }
        )
        data = create_response.json()
        department_id = data["department_id"]
        assignment_type_to_remove = data["assignment_types"][0]["assignment_type_id"]
        
        # Update to add and remove assignment types
        response = authenticated_client.put(
            f"/api/v1/departments/{department_id}",
            json={
                "assignment_types_to_add": ["Senior Product Manager", "UX Researcher"],
                "assignment_types_to_remove": [assignment_type_to_remove]
            }
        )
        assert response.status_code == 200
        updated_data = response.json()
        assert len(updated_data["assignment_types"]) == 3  # Started with 2, removed 1, added 2
        
        descriptions = [at["description"] for at in updated_data["assignment_types"]]
        assert "Product Manager" not in descriptions  # Removed
        assert "Designer" in descriptions  # Kept
        assert "Senior Product Manager" in descriptions  # Added
        assert "UX Researcher" in descriptions  # Added
    
    def test_delete_department_with_assignment_types(self, db, authenticated_client):
        """Test deleting a department that has assignment types"""
        # Create a department with assignment types
        create_response = authenticated_client.post(
            "/api/v1/departments/",
            json={
                "name": "Legal",
                "assignment_types": ["Lawyer", "Paralegal"]
            }
        )
        department_id = create_response.json()["department_id"]
        
        # Delete the department
        response = authenticated_client.delete(f"/api/v1/departments/{department_id}")
        assert response.status_code == 200
        
        # Verify department is deleted
        get_response = authenticated_client.get(f"/api/v1/departments/{department_id}")
        assert get_response.status_code == 404