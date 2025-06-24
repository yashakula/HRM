import pytest
import os
from tests.integration.conftest import IntegrationTestClient

# Allow disabling the redundant search tests
ENABLE_OLD_SEARCH_TESTS = os.getenv("ENABLE_OLD_SEARCH_INTEGRATION_TESTS", "false").lower() == "true"


class TestEmployeeIntegration:
    """Integration tests for employee endpoints against localhost server"""
    
    def test_create_employee_minimal_data(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test creating employee with minimal data via real server"""
        employee_data = {
            "person": {
                "full_name": "Integration Test User"
            }
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] is not None
        assert data["person"]["full_name"] == "Integration Test User"
        assert data["status"] in ["ACTIVE", "Active"]  # Handle enum formatting differences
        assert data["person"]["personal_information"] is None  # No personal info provided
    
    def test_create_employee_complete_data(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test creating employee with complete data via real server"""
        employee_data = {
            "person": {
                "full_name": "Complete Data Employee",
                "date_of_birth": "1985-03-20"
            },
            "personal_information": {
                "personal_email": "complete@personal.com",
                "ssn": "987-65-4321",
                "bank_account": "BANK987654321"
            },
            "work_email": "complete@company.com",
            "effective_start_date": "2024-06-01"
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] is not None
        assert data["person"]["full_name"] == "Complete Data Employee"
        assert data["person"]["date_of_birth"] == "1985-03-20"
        assert data["work_email"] == "complete@company.com"
        assert data["effective_start_date"] == "2024-06-01"
        assert data["person"]["personal_information"]["personal_email"] == "complete@personal.com"
        assert data["person"]["personal_information"]["ssn"] == "987-65-4321"
        assert data["person"]["personal_information"]["bank_account"] == "BANK987654321"
    
    def test_get_employee_by_id(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test retrieving employee by ID via real server"""
        # First create an employee
        employee_data = {
            "person": {
                "full_name": "Retrievable Employee"
            }
        }
        
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        created_employee = create_response.json()
        employee_id = created_employee["employee_id"]
        
        # Then retrieve it
        get_response = integration_client.get(f"/api/v1/employees/{employee_id}")
        assert get_response.status_code == 200
        
        retrieved_employee = get_response.json()
        assert retrieved_employee["employee_id"] == employee_id
        assert retrieved_employee["person"]["full_name"] == "Retrievable Employee"
    
    def test_get_nonexistent_employee(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test that retrieving non-existent employee returns 404"""
        response = integration_client.get("/api/v1/employees/99999")
        assert response.status_code == 404
        assert "Employee not found" in response.json()["detail"]
    
    def test_list_employees(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test listing employees via real server"""
        # Create multiple employees
        employees_to_create = [
            {"person": {"full_name": "List Employee 1"}},
            {"person": {"full_name": "List Employee 2"}},
            {"person": {"full_name": "List Employee 3"}}
        ]
        
        created_ids = []
        for emp_data in employees_to_create:
            response = integration_client.post("/api/v1/employees/", json=emp_data)
            assert response.status_code == 200
            created_ids.append(response.json()["employee_id"])
        
        # List all employees
        list_response = integration_client.get("/api/v1/employees/")
        assert list_response.status_code == 200
        
        employees = list_response.json()
        assert len(employees) >= 3  # At least the ones we created
        
        # Verify our created employees are in the list
        employee_ids_in_response = [emp["employee_id"] for emp in employees]
        for created_id in created_ids:
            assert created_id in employee_ids_in_response
    
    def test_create_employee_validation_errors(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test validation errors when creating employees"""
        # Test missing required field
        invalid_data = {
            "person": {}  # Missing full_name
        }
        
        response = integration_client.post("/api/v1/employees/", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_employee_invalid_date(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test creating employee with invalid date format"""
        employee_data = {
            "person": {
                "full_name": "Invalid Date Employee",
                "date_of_birth": "not-a-date"
            }
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 422  # Validation error


class TestEmployeeIntegrationPermissions:
    """Test employee permissions across different roles via real server"""
    
    def test_supervisor_can_view_but_not_create(self, integration_client: IntegrationTestClient, authenticated_supervisor):
        """Test that supervisors can view but not create employees"""
        # Try to create - should fail
        employee_data = {
            "person": {
                "full_name": "Supervisor Cannot Create"
            }
        }
        
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 403
        assert "HR_ADMIN" in create_response.json()["detail"]
        
        # But can view employee list
        list_response = integration_client.get("/api/v1/employees/")
        assert list_response.status_code == 200
    
    def test_employee_can_view_but_not_create(self, integration_client: IntegrationTestClient, authenticated_employee):
        """Test that employees can view but not create employees"""
        # Try to create - should fail
        employee_data = {
            "person": {
                "full_name": "Employee Cannot Create"
            }
        }
        
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 403
        assert "HR_ADMIN" in create_response.json()["detail"]
        
        # But can view employee list
        list_response = integration_client.get("/api/v1/employees/")
        assert list_response.status_code == 200
    
    def test_cross_role_employee_access(self, integration_client: IntegrationTestClient):
        """Test that employees created by one role can be viewed by others"""
        import uuid
        
        # Step 1: Create and authenticate HR Admin
        hr_unique_id = str(uuid.uuid4())[:8]
        hr_admin_data = {
            "username": f"hr_admin_cross_{hr_unique_id}",
            "email": f"hr_admin_cross_{hr_unique_id}@example.com",
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        
        # Register and login HR Admin
        register_response = integration_client.post("/api/v1/auth/register", json=hr_admin_data)
        assert register_response.status_code == 200
        
        login_data = {"username": hr_admin_data["username"], "password": hr_admin_data["password"]}
        login_response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Step 2: HR Admin creates an employee
        employee_data = {
            "person": {
                "full_name": "Cross Role Test Employee"
            }
        }
        
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        employee_id = create_response.json()["employee_id"]
        
        # Step 3: Logout HR Admin
        logout_response = integration_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # Step 4: Create and authenticate Supervisor
        supervisor_unique_id = str(uuid.uuid4())[:8]
        supervisor_data = {
            "username": f"supervisor_cross_{supervisor_unique_id}",
            "email": f"supervisor_cross_{supervisor_unique_id}@example.com",
            "password": "testpassword123",
            "role": "SUPERVISOR"
        }
        
        # Register and login supervisor
        register_response = integration_client.post("/api/v1/auth/register", json=supervisor_data)
        assert register_response.status_code == 200
        
        login_data = {"username": supervisor_data["username"], "password": supervisor_data["password"]}
        login_response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Step 5: Supervisor should be able to view the employee created by HR Admin
        view_response = integration_client.get(f"/api/v1/employees/{employee_id}")
        assert view_response.status_code == 200
        assert view_response.json()["person"]["full_name"] == "Cross Role Test Employee"


@pytest.mark.skipif(
    not ENABLE_OLD_SEARCH_TESTS,
    reason="Old search integration tests disabled (set ENABLE_OLD_SEARCH_INTEGRATION_TESTS=true to enable)"
)
class TestEmployeeSearchIntegration:
    """Integration tests for US-02: Search and view employee records"""
    
    def setup_test_employees(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Create test employees for search testing"""
        test_employees = [
            {"person": {"full_name": "Alice Johnson"}},
            {"person": {"full_name": "Bob Smith"}},
            {"person": {"full_name": "Charlie Brown"}},
            {"person": {"full_name": "Diana Wilson"}},
            {"person": {"full_name": "Edward Davis"}}
        ]
        
        created_employees = []
        for emp_data in test_employees:
            response = integration_client.post("/api/v1/employees/", json=emp_data)
            assert response.status_code == 200
            created_employees.append(response.json())
        
        return created_employees
    
    def test_search_by_name_exact_match(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test searching by exact name match"""
        employees = self.setup_test_employees(integration_client, authenticated_hr_admin)
        
        response = integration_client.get("/api/v1/employees/search?name=Alice Johnson")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 1
        assert results[0]["person"]["full_name"] == "Alice Johnson"
    
    def test_search_by_name_partial_match(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test searching by partial name match"""
        employees = self.setup_test_employees(integration_client, authenticated_hr_admin)
        
        response = integration_client.get("/api/v1/employees/search?name=Johnson")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("Johnson" in emp["person"]["full_name"] for emp in results)
    
    def test_search_by_employee_id(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test searching by employee ID"""
        employees = self.setup_test_employees(integration_client, authenticated_hr_admin)
        target_employee = employees[0]
        employee_id = target_employee["employee_id"]
        
        response = integration_client.get(f"/api/v1/employees/search?employee_id={employee_id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 1
        assert results[0]["employee_id"] == employee_id
        assert results[0]["person"]["full_name"] == target_employee["person"]["full_name"]
    
    def test_search_by_status_active(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test searching by employee status (Active)"""
        employees = self.setup_test_employees(integration_client, authenticated_hr_admin)
        
        response = integration_client.get("/api/v1/employees/search?status=Active")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 5  # All created employees should be active
        assert all(emp["status"] in ["ACTIVE", "Active"] for emp in results)
    
    def test_search_no_results(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test search that returns no results"""
        self.setup_test_employees(integration_client, authenticated_hr_admin)
        
        response = integration_client.get("/api/v1/employees/search?name=NonExistentEmployee")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 0
    
    def test_search_with_pagination(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test search with pagination parameters"""
        self.setup_test_employees(integration_client, authenticated_hr_admin)
        
        # Test with limit
        response = integration_client.get("/api/v1/employees/search?limit=3")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 3
        
        # Test with skip and limit
        response = integration_client.get("/api/v1/employees/search?skip=2&limit=2")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 2
    
    def test_search_invalid_parameters(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test search with invalid parameters"""
        # Test invalid employee_id (non-integer)
        response = integration_client.get("/api/v1/employees/search?employee_id=invalid")
        assert response.status_code == 422  # Validation error
        
        # Test invalid status
        response = integration_client.get("/api/v1/employees/search?status=InvalidStatus")
        assert response.status_code == 422  # Validation error
        
        # Test negative skip
        response = integration_client.get("/api/v1/employees/search?skip=-1")
        assert response.status_code == 422  # Validation error
        
        # Test limit too high
        response = integration_client.get("/api/v1/employees/search?limit=2000")
        assert response.status_code == 422  # Validation error
    
    def test_search_unauthenticated(self, integration_client: IntegrationTestClient):
        """Test that unauthenticated users cannot search"""
        response = integration_client.get("/api/v1/employees/search?name=John")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_search_as_supervisor(self, integration_client: IntegrationTestClient, authenticated_supervisor):
        """Test search functionality as supervisor role"""
        # Create test data first as HR Admin
        import uuid
        hr_unique_id = str(uuid.uuid4())[:8]
        hr_admin_data = {
            "username": f"hr_admin_search_{hr_unique_id}",
            "email": f"hr_admin_search_{hr_unique_id}@example.com", 
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        
        # Register and login HR Admin temporarily to create test data
        register_response = integration_client.post("/api/v1/auth/register", json=hr_admin_data)
        assert register_response.status_code == 200
        
        login_data = {"username": hr_admin_data["username"], "password": hr_admin_data["password"]}
        login_response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Create test employee
        employee_data = {"person": {"full_name": "Supervisor Search Test"}}
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        
        # Logout HR Admin
        logout_response = integration_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # Login as supervisor (provided by authenticated_supervisor fixture)
        # Test search functionality
        response = integration_client.get("/api/v1/employees/search?name=Supervisor Search Test")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("Supervisor Search Test" in emp["person"]["full_name"] for emp in results)
    
    def test_search_as_employee(self, integration_client: IntegrationTestClient, authenticated_employee):
        """Test search functionality as employee role"""
        # Similar to supervisor test but using employee role
        import uuid
        hr_unique_id = str(uuid.uuid4())[:8]
        hr_admin_data = {
            "username": f"hr_admin_emp_search_{hr_unique_id}",
            "email": f"hr_admin_emp_search_{hr_unique_id}@example.com",
            "password": "testpassword123", 
            "role": "HR_ADMIN"
        }
        
        # Register and login HR Admin temporarily to create test data
        register_response = integration_client.post("/api/v1/auth/register", json=hr_admin_data)
        assert register_response.status_code == 200
        
        login_data = {"username": hr_admin_data["username"], "password": hr_admin_data["password"]}
        login_response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        # Create test employee
        employee_data = {"person": {"full_name": "Employee Search Test"}}
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        
        # Logout HR Admin
        logout_response = integration_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        
        # Login as employee (provided by authenticated_employee fixture)
        # Test search functionality
        response = integration_client.get("/api/v1/employees/search?name=Employee Search Test")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("Employee Search Test" in emp["person"]["full_name"] for emp in results)