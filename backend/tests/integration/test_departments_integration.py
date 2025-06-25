import pytest
import requests
from typing import Dict, Any

from .conftest import TEST_USER_CREDENTIALS

BASE_URL = "http://localhost:8000/api/v1"

class TestDepartmentAssignmentTypeIntegration:
    """Integration tests for department and assignment type management"""
    
    @pytest.fixture(autouse=True)
    def setup_auth(self):
        """Authenticate before each test"""
        # Login to get session
        login_response = requests.post(
            f"{BASE_URL}/auth/login",
            data=TEST_USER_CREDENTIALS["hr_admin"]
        )
        assert login_response.status_code == 200
        self.session = requests.Session()
        self.session.cookies.update(login_response.cookies)
    
    def test_complete_department_lifecycle_with_assignment_types(self):
        """Test the complete lifecycle of department management with assignment types"""
        
        # 1. Create a department with assignment types
        create_data = {
            "name": "Technology Integration",
            "description": "Technology and integration services",
            "assignment_types": [
                "Software Developer",
                "DevOps Engineer", 
                "QA Engineer"
            ]
        }
        
        create_response = self.session.post(
            f"{BASE_URL}/departments/",
            json=create_data
        )
        assert create_response.status_code == 200
        department = create_response.json()
        
        # Verify department was created with assignment types
        assert department["name"] == "Technology Integration"
        assert len(department["assignment_types"]) == 3
        assignment_type_descriptions = [at["description"] for at in department["assignment_types"]]
        assert "Software Developer" in assignment_type_descriptions
        assert "DevOps Engineer" in assignment_type_descriptions
        assert "QA Engineer" in assignment_type_descriptions
        
        department_id = department["department_id"]
        
        # 2. Retrieve the department and verify assignment types
        get_response = self.session.get(f"{BASE_URL}/departments/{department_id}")
        assert get_response.status_code == 200
        retrieved_department = get_response.json()
        assert len(retrieved_department["assignment_types"]) == 3
        
        # 3. Update department to add and remove assignment types
        assignment_type_to_remove = retrieved_department["assignment_types"][0]["assignment_type_id"]
        
        update_data = {
            "name": "Technology & Innovation",
            "description": "Technology, innovation, and integration services",
            "assignment_types_to_add": [
                "Senior Software Developer",
                "Solutions Architect"
            ],
            "assignment_types_to_remove": [assignment_type_to_remove]
        }
        
        update_response = self.session.put(
            f"{BASE_URL}/departments/{department_id}",
            json=update_data
        )
        assert update_response.status_code == 200
        updated_department = update_response.json()
        
        # Verify updates
        assert updated_department["name"] == "Technology & Innovation"
        assert len(updated_department["assignment_types"]) == 4  # Started 3, removed 1, added 2
        
        updated_descriptions = [at["description"] for at in updated_department["assignment_types"]]
        assert "Senior Software Developer" in updated_descriptions
        assert "Solutions Architect" in updated_descriptions
        
        # 4. Test assignment type API endpoints
        # Get all assignment types for this department
        assignment_types_response = self.session.get(
            f"{BASE_URL}/assignment-types/?department_id={department_id}"
        )
        assert assignment_types_response.status_code == 200
        assignment_types = assignment_types_response.json()
        assert len(assignment_types) == 4
        
        # 5. Create an assignment type directly via assignment-types endpoint
        direct_create_response = self.session.post(
            f"{BASE_URL}/assignment-types/",
            json={
                "description": "Technical Lead",
                "department_id": department_id
            }
        )
        assert direct_create_response.status_code == 200
        
        # Verify department now has 5 assignment types
        final_get_response = self.session.get(f"{BASE_URL}/departments/{department_id}")
        assert final_get_response.status_code == 200
        final_department = final_get_response.json()
        assert len(final_department["assignment_types"]) == 5
        
        # 6. Clean up - delete the department
        delete_response = self.session.delete(f"{BASE_URL}/departments/{department_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        deleted_get_response = self.session.get(f"{BASE_URL}/departments/{department_id}")
        assert deleted_get_response.status_code == 404
    
    def test_assignment_type_validation(self):
        """Test validation when creating assignment types"""
        
        # Try to create assignment type for non-existent department
        invalid_response = self.session.post(
            f"{BASE_URL}/assignment-types/",
            json={
                "description": "Invalid Assignment Type",
                "department_id": 99999
            }
        )
        assert invalid_response.status_code == 400
        assert "Department not found" in invalid_response.json()["detail"]
    
    def test_department_creation_empty_assignment_types(self):
        """Test creating department with empty assignment types list"""
        
        create_data = {
            "name": "Empty Department",
            "description": "Department with no assignment types",
            "assignment_types": []
        }
        
        response = self.session.post(
            f"{BASE_URL}/departments/",
            json=create_data
        )
        assert response.status_code == 200
        department = response.json()
        assert len(department["assignment_types"]) == 0
        
        # Clean up
        self.session.delete(f"{BASE_URL}/departments/{department['department_id']}")
    
    def test_department_update_only_assignment_types(self):
        """Test updating a department to only modify assignment types"""
        
        # Create department
        create_response = self.session.post(
            f"{BASE_URL}/departments/",
            json={
                "name": "Test Department",
                "description": "Test description",
                "assignment_types": ["Initial Type"]
            }
        )
        department = create_response.json()
        department_id = department["department_id"]
        
        # Update only assignment types (no name/description changes)
        assignment_type_to_remove = department["assignment_types"][0]["assignment_type_id"]
        
        update_response = self.session.put(
            f"{BASE_URL}/departments/{department_id}",
            json={
                "assignment_types_to_add": ["New Type 1", "New Type 2"],
                "assignment_types_to_remove": [assignment_type_to_remove]
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        
        # Verify name and description unchanged, assignment types changed
        assert updated["name"] == "Test Department"
        assert updated["description"] == "Test description"
        assert len(updated["assignment_types"]) == 2
        
        descriptions = [at["description"] for at in updated["assignment_types"]]
        assert "Initial Type" not in descriptions
        assert "New Type 1" in descriptions
        assert "New Type 2" in descriptions
        
        # Clean up
        self.session.delete(f"{BASE_URL}/departments/{department_id}")
    
    def test_large_number_of_assignment_types(self):
        """Test creating department with many assignment types"""
        
        assignment_types = [f"Role {i}" for i in range(1, 21)]  # 20 assignment types
        
        create_response = self.session.post(
            f"{BASE_URL}/departments/",
            json={
                "name": "Large Department",
                "assignment_types": assignment_types
            }
        )
        assert create_response.status_code == 200
        department = create_response.json()
        assert len(department["assignment_types"]) == 20
        
        # Clean up
        self.session.delete(f"{BASE_URL}/departments/{department['department_id']}")