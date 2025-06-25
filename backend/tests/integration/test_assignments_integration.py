"""
Integration tests for assignment system against live server
"""

import pytest
import requests
import time
from typing import Dict, Any

# Server configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class TestAssignmentSystemIntegration:
    """Integration tests for complete assignment system workflow"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Login as HR Admin and maintain session"""
        session = requests.Session()
        
        # Login
        login_response = session.post(f"{API_BASE}/auth/login", json={
            "username": "hr_admin",
            "password": "admin123"
        })
        
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        return session
    
    @pytest.fixture(scope="class")
    def employee_session(self):
        """Login as Employee for permission testing"""
        session = requests.Session()
        
        login_response = session.post(f"{API_BASE}/auth/login", json={
            "username": "employee1", 
            "password": "emp123"
        })
        
        assert login_response.status_code == 200
        return session
    
    def test_department_lifecycle(self, auth_session):
        """Test complete department CRUD lifecycle"""
        
        # Create department
        dept_data = {
            "name": "Integration Test Dept",
            "description": "Created during integration testing"
        }
        
        create_response = auth_session.post(f"{API_BASE}/departments/", json=dept_data)
        assert create_response.status_code == 200
        
        dept = create_response.json()
        dept_id = dept["department_id"]
        assert dept["name"] == dept_data["name"]
        assert dept["description"] == dept_data["description"]
        
        # Read department
        get_response = auth_session.get(f"{API_BASE}/departments/{dept_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == dept_data["name"]
        
        # Update department
        update_data = {
            "name": "Updated Test Dept",
            "description": "Updated description"
        }
        
        update_response = auth_session.put(f"{API_BASE}/departments/{dept_id}", json=update_data)
        assert update_response.status_code == 200
        
        updated_dept = update_response.json()
        assert updated_dept["name"] == update_data["name"]
        assert updated_dept["description"] == update_data["description"]
        
        # List departments (verify exists)
        list_response = auth_session.get(f"{API_BASE}/departments/")
        assert list_response.status_code == 200
        
        departments = list_response.json()
        assert any(d["department_id"] == dept_id for d in departments)
        
        # Delete department
        delete_response = auth_session.delete(f"{API_BASE}/departments/{dept_id}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_deleted_response = auth_session.get(f"{API_BASE}/departments/{dept_id}")
        assert get_deleted_response.status_code == 404
    
    def test_assignment_type_with_department_relationship(self, auth_session):
        """Test assignment type creation and department relationships"""
        
        # Create department
        dept_response = auth_session.post(f"{API_BASE}/departments/", json={
            "name": "AT Test Department",
            "description": "For assignment type testing"
        })
        dept_id = dept_response.json()["department_id"]
        
        # Create assignment type
        at_data = {
            "description": "Integration Test Role",
            "department_id": dept_id
        }
        
        at_response = auth_session.post(f"{API_BASE}/assignment-types/", json=at_data)
        assert at_response.status_code == 200
        
        assignment_type = at_response.json()
        at_id = assignment_type["assignment_type_id"]
        
        # Verify relationship data
        assert assignment_type["description"] == at_data["description"]
        assert assignment_type["department_id"] == dept_id
        assert assignment_type["department"]["name"] == "AT Test Department"
        assert "created_at" in assignment_type
        assert "updated_at" in assignment_type
        
        # Filter assignment types by department
        filter_response = auth_session.get(f"{API_BASE}/assignment-types/?department_id={dept_id}")
        assert filter_response.status_code == 200
        
        filtered_types = filter_response.json()
        assert len(filtered_types) >= 1
        assert any(at["assignment_type_id"] == at_id for at in filtered_types)
        
        # Clean up
        auth_session.delete(f"{API_BASE}/departments/{dept_id}")
    
    def test_complete_assignment_workflow(self, auth_session):
        """Test end-to-end assignment creation with all relationships"""
        
        # 1. Create department
        dept_response = auth_session.post(f"{API_BASE}/departments/", json={
            "name": "Complete Workflow Dept",
            "description": "Full assignment workflow test"
        })
        dept_id = dept_response.json()["department_id"]
        
        # 2. Create assignment type
        at_response = auth_session.post(f"{API_BASE}/assignment-types/", json={
            "description": "Workflow Test Role",
            "department_id": dept_id
        })
        at_id = at_response.json()["assignment_type_id"]
        
        # 3. Get existing employees (from seed data)
        employees_response = auth_session.get(f"{API_BASE}/employees/search?name=Alice")
        employees = employees_response.json()
        assert len(employees) > 0
        
        alice = employees[0]
        alice_id = alice["employee_id"]
        
        # Get Bob as supervisor
        bob_response = auth_session.get(f"{API_BASE}/employees/search?name=Bob")
        bob = bob_response.json()[0]
        bob_id = bob["employee_id"]
        
        # 4. Create assignment with supervisor
        assignment_data = {
            "employee_id": alice_id,
            "assignment_type_id": at_id,
            "description": "Integration test assignment with full workflow",
            "effective_start_date": "2025-01-15",
            "effective_end_date": "2025-12-31",
            "supervisor_ids": [bob_id]
        }
        
        assignment_response = auth_session.post(f"{API_BASE}/assignments/", json=assignment_data)
        assert assignment_response.status_code == 200
        
        assignment = assignment_response.json()
        assignment_id = assignment["assignment_id"]
        
        # Verify assignment data
        assert assignment["employee_id"] == alice_id
        assert assignment["assignment_type_id"] == at_id
        assert assignment["description"] == assignment_data["description"]
        assert assignment["effective_start_date"] == "2025-01-15"
        assert assignment["effective_end_date"] == "2025-12-31"
        
        # Verify relationships are populated
        assert assignment["employee"]["person"]["full_name"] == "Alice Johnson"
        assert assignment["assignment_type"]["description"] == "Workflow Test Role"
        assert assignment["assignment_type"]["department"]["name"] == "Complete Workflow Dept"
        assert len(assignment["supervisors"]) == 1
        assert assignment["supervisors"][0]["person"]["full_name"] == "Bob Smith"
        
        # 5. Test supervisor relationship queries
        supervisor_assignments = auth_session.get(f"{API_BASE}/assignments/supervisor/{bob_id}")
        assert supervisor_assignments.status_code == 200
        
        sup_assignments = supervisor_assignments.json()
        assert any(a["assignment_id"] == assignment_id for a in sup_assignments)
        
        # 6. Test employee assignment query
        employee_assignments = auth_session.get(f"{API_BASE}/assignments/employee/{alice_id}")
        assert employee_assignments.status_code == 200
        
        emp_assignments = employee_assignments.json()
        assert any(a["assignment_id"] == assignment_id for a in emp_assignments)
        
        # 7. Update supervisors
        charlie_response = auth_session.get(f"{API_BASE}/employees/search?name=Charlie")
        if charlie_response.json():
            charlie_id = charlie_response.json()[0]["employee_id"]
            
            # Update to multiple supervisors
            update_response = auth_session.put(
                f"{API_BASE}/assignments/{assignment_id}/supervisors",
                json=[bob_id, charlie_id]
            )
            assert update_response.status_code == 200
            
            updated_assignment = update_response.json()["assignment"]
            assert len(updated_assignment["supervisors"]) == 2
            supervisor_ids = [s["employee_id"] for s in updated_assignment["supervisors"]]
            assert bob_id in supervisor_ids
            assert charlie_id in supervisor_ids
        
        # 8. Test filtering and queries
        # Filter assignments by employee
        filtered_response = auth_session.get(f"{API_BASE}/assignments/?employee_id={alice_id}")
        assert filtered_response.status_code == 200
        
        filtered_assignments = filtered_response.json()
        assert any(a["assignment_id"] == assignment_id for a in filtered_assignments)
        
        # Filter assignments by supervisor
        sup_filtered_response = auth_session.get(f"{API_BASE}/assignments/?supervisor_id={bob_id}")
        assert sup_filtered_response.status_code == 200
        
        sup_filtered = sup_filtered_response.json()
        assert any(a["assignment_id"] == assignment_id for a in sup_filtered)
        
        # Clean up (optional - will be cleaned up by test database reset)
        print(f"Created assignment {assignment_id} for testing")
    
    def test_permission_enforcement(self, auth_session, employee_session):
        """Test role-based access control enforcement"""
        
        # Create test department as HR Admin
        dept_response = auth_session.post(f"{API_BASE}/departments/", json={
            "name": "Permission Test Dept",
            "description": "Testing permissions"
        })
        dept_id = dept_response.json()["department_id"]
        
        # Employee cannot create departments
        employee_create_response = employee_session.post(f"{API_BASE}/departments/", json={
            "name": "Unauthorized Dept",
            "description": "Should fail"
        })
        assert employee_create_response.status_code == 403
        
        # Employee can read departments
        employee_read_response = employee_session.get(f"{API_BASE}/departments/")
        assert employee_read_response.status_code == 200
        
        # Employee cannot update departments
        employee_update_response = employee_session.put(f"{API_BASE}/departments/{dept_id}", json={
            "name": "Updated by Employee",
            "description": "Should fail"
        })
        assert employee_update_response.status_code == 403
        
        # Employee cannot delete departments
        employee_delete_response = employee_session.delete(f"{API_BASE}/departments/{dept_id}")
        assert employee_delete_response.status_code == 403
        
        # Test assignment type permissions
        at_response = auth_session.post(f"{API_BASE}/assignment-types/", json={
            "description": "Permission Test Role",
            "department_id": dept_id
        })
        at_id = at_response.json()["assignment_type_id"]
        
        # Employee cannot create assignment types
        employee_at_response = employee_session.post(f"{API_BASE}/assignment-types/", json={
            "description": "Unauthorized Role",
            "department_id": dept_id
        })
        assert employee_at_response.status_code == 403
        
        # Employee can read assignment types
        employee_at_read = employee_session.get(f"{API_BASE}/assignment-types/")
        assert employee_at_read.status_code == 200
        
        # Employee cannot create assignments
        alice_response = auth_session.get(f"{API_BASE}/employees/search?name=Alice")
        alice_id = alice_response.json()[0]["employee_id"]
        
        employee_assignment_response = employee_session.post(f"{API_BASE}/assignments/", json={
            "employee_id": alice_id,
            "assignment_type_id": at_id
        })
        assert employee_assignment_response.status_code == 403
        
        # Employee can read assignments
        employee_assignment_read = employee_session.get(f"{API_BASE}/assignments/")
        assert employee_assignment_read.status_code == 200
    
    def test_data_validation_and_error_handling(self, auth_session):
        """Test validation and error handling"""
        
        # Create assignment type with non-existent department
        invalid_at_response = auth_session.post(f"{API_BASE}/assignment-types/", json={
            "description": "Invalid Role",
            "department_id": 99999
        })
        assert invalid_at_response.status_code == 400
        assert "Department not found" in invalid_at_response.json()["detail"]
        
        # Create assignment with non-existent employee
        dept_response = auth_session.post(f"{API_BASE}/departments/", json={
            "name": "Validation Test Dept",
            "description": "For validation testing"
        })
        dept_id = dept_response.json()["department_id"]
        
        at_response = auth_session.post(f"{API_BASE}/assignment-types/", json={
            "description": "Validation Test Role",
            "department_id": dept_id
        })
        at_id = at_response.json()["assignment_type_id"]
        
        invalid_assignment_response = auth_session.post(f"{API_BASE}/assignments/", json={
            "employee_id": 99999,
            "assignment_type_id": at_id
        })
        assert invalid_assignment_response.status_code == 400
        assert "Employee not found" in invalid_assignment_response.json()["detail"]
        
        # Create assignment with non-existent assignment type
        alice_response = auth_session.get(f"{API_BASE}/employees/search?name=Alice")
        alice_id = alice_response.json()[0]["employee_id"]
        
        invalid_at_assignment = auth_session.post(f"{API_BASE}/assignments/", json={
            "employee_id": alice_id,
            "assignment_type_id": 99999
        })
        assert invalid_at_assignment.status_code == 400
        assert "Assignment type not found" in invalid_at_assignment.json()["detail"]
        
        # Create assignment with non-existent supervisor
        invalid_sup_assignment = auth_session.post(f"{API_BASE}/assignments/", json={
            "employee_id": alice_id,
            "assignment_type_id": at_id,
            "supervisor_ids": [99999]
        })
        assert invalid_sup_assignment.status_code == 400
        assert "Supervisor with ID 99999 not found" in invalid_sup_assignment.json()["detail"]
    
    def test_assignment_system_with_seed_data(self, auth_session):
        """Test assignment system using existing seed data"""
        
        # Verify seed departments exist
        departments_response = auth_session.get(f"{API_BASE}/departments/")
        assert departments_response.status_code == 200
        
        departments = departments_response.json()
        dept_names = [d["name"] for d in departments]
        
        # Check for expected seed departments
        expected_depts = ["Engineering", "Marketing", "Human Resources", "Finance", "Operations"]
        for expected_dept in expected_depts:
            assert expected_dept in dept_names, f"Expected department '{expected_dept}' not found in seed data"
        
        # Verify seed assignment types exist
        assignment_types_response = auth_session.get(f"{API_BASE}/assignment-types/")
        assert assignment_types_response.status_code == 200
        
        assignment_types = assignment_types_response.json()
        assert len(assignment_types) >= 15, "Expected at least 15 assignment types from seed data"
        
        # Test filtering assignment types by department
        engineering_dept = next(d for d in departments if d["name"] == "Engineering")
        eng_types_response = auth_session.get(f"{API_BASE}/assignment-types/?department_id={engineering_dept['department_id']}")
        eng_types = eng_types_response.json()
        
        eng_type_descriptions = [at["description"] for at in eng_types]
        expected_eng_types = ["Software Engineer", "Senior Software Engineer", "Engineering Manager", "DevOps Engineer"]
        
        for expected_type in expected_eng_types:
            assert expected_type in eng_type_descriptions, f"Expected engineering role '{expected_type}' not found"
        
        # Create assignment using seed data
        software_engineer_at = next(at for at in eng_types if at["description"] == "Software Engineer")
        
        # Get seed employees
        alice_response = auth_session.get(f"{API_BASE}/employees/search?name=Alice")
        bob_response = auth_session.get(f"{API_BASE}/employees/search?name=Bob")
        
        alice = alice_response.json()[0]
        bob = bob_response.json()[0]
        
        # Create assignment using all seed data
        assignment_response = auth_session.post(f"{API_BASE}/assignments/", json={
            "employee_id": alice["employee_id"],
            "assignment_type_id": software_engineer_at["assignment_type_id"],
            "description": "Python development using seed data",
            "effective_start_date": "2025-01-01",
            "supervisor_ids": [bob["employee_id"]]
        })
        
        assert assignment_response.status_code == 200
        assignment = assignment_response.json()
        
        # Verify all relationships work with seed data
        assert assignment["employee"]["person"]["full_name"] == "Alice Johnson"
        assert assignment["assignment_type"]["description"] == "Software Engineer"
        assert assignment["assignment_type"]["department"]["name"] == "Engineering"
        assert assignment["supervisors"][0]["person"]["full_name"] == "Bob Smith"
        
        print(f"Successfully created assignment using seed data: Assignment ID {assignment['assignment_id']}")

# Helper function to run integration tests
def run_integration_tests():
    """Run integration tests if server is available"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("Server is available, running integration tests...")
            pytest.main([__file__, "-v"])
        else:
            print(f"Server returned status {response.status_code}, skipping integration tests")
    except requests.RequestException as e:
        print(f"Server not available: {e}")
        print("Skipping integration tests")

if __name__ == "__main__":
    run_integration_tests()