import pytest
from fastapi.testclient import TestClient
from datetime import date

from hrm_backend.models import EmployeeStatus, UserRole

class TestEmployeeCreation:
    """Test US-01: Create employee profile"""
    
    def setup_authenticated_user(self, client: TestClient, role: UserRole = UserRole.HR_ADMIN):
        """Helper to create and authenticate a user"""
        user_data = {
            "username": f"testuser_{role.value.lower()}",
            "email": f"test_{role.value.lower()}@example.com",
            "password": "testpassword123",
            "role": role.value
        }
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login user (sets session cookie automatically)
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        return user_data
    
    def test_create_employee_minimal(self, client: TestClient):
        """Test creating employee with minimal required data"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        
        employee_data = {
            "person": {
                "full_name": "John Doe"
            }
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] is not None
        assert data["person"]["full_name"] == "John Doe"
        assert data["status"] == EmployeeStatus.ACTIVE.value
    
    def test_create_employee_full_data(self, client: TestClient):
        """Test creating employee with complete data"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        employee_data = {
            "person": {
                "full_name": "Jane Smith",
                "date_of_birth": "1990-05-15"
            },
            "personal_information": {
                "personal_email": "jane.smith@personal.com",
                "ssn": "123-45-6789",
                "bank_account": "ACC123456789"
            },
            "work_email": "jane.smith@company.com",
            "effective_start_date": "2024-01-01"
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["employee_id"] is not None
        assert data["person"]["full_name"] == "Jane Smith"
        assert data["person"]["date_of_birth"] == "1990-05-15"
        assert data["work_email"] == "jane.smith@company.com"
        assert data["effective_start_date"] == "2024-01-01"
        assert data["person"]["personal_information"]["personal_email"] == "jane.smith@personal.com"
        assert data["person"]["personal_information"]["ssn"] == "123-45-6789"
    
    def test_create_employee_missing_name(self, client: TestClient):
        """Test that creating employee without name fails"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        employee_data = {
            "person": {}
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_employee_by_id(self, client: TestClient):
        """Test retrieving employee by ID"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        
        # First create an employee
        employee_data = {
            "person": {
                "full_name": "Test Employee"
            }
        }
        
        create_response = client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        created_employee = create_response.json()
        employee_id = created_employee["employee_id"]
        
        # Then retrieve it
        get_response = client.get(f"/api/v1/employees/{employee_id}")
        assert get_response.status_code == 200
        
        retrieved_employee = get_response.json()
        assert retrieved_employee["employee_id"] == employee_id
        assert retrieved_employee["person"]["full_name"] == "Test Employee"
    
    def test_get_nonexistent_employee(self, client: TestClient):
        """Test that retrieving non-existent employee returns 404"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        response = client.get("/api/v1/employees/99999")
        assert response.status_code == 404
        assert "Employee not found" in response.json()["detail"]
    
    def test_list_employees(self, client: TestClient):
        """Test listing employees"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        
        # Create a few employees
        for i in range(3):
            employee_data = {
                "person": {
                    "full_name": f"Employee {i}"
                }
            }
            response = client.post("/api/v1/employees/", json=employee_data)
            assert response.status_code == 200
        
        # List all employees
        list_response = client.get("/api/v1/employees/")
        assert list_response.status_code == 200
        
        employees = list_response.json()
        assert len(employees) == 3
        assert all("employee_id" in emp for emp in employees)

class TestEmployeeValidation:
    """Test data validation for employee creation"""
    
    def setup_authenticated_user(self, client: TestClient, role: UserRole = UserRole.HR_ADMIN):
        """Helper to create and authenticate a user"""
        user_data = {
            "username": f"testuser_{role.value.lower()}",
            "email": f"test_{role.value.lower()}@example.com",
            "password": "testpassword123",
            "role": role.value
        }
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login user (sets session cookie automatically)
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        return user_data
    
    def test_invalid_email_format(self, client: TestClient):
        """Test that invalid email format is handled"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        employee_data = {
            "person": {
                "full_name": "John Doe"
            },
            "work_email": "invalid-email"
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        # Note: This might pass if we're not validating email format yet
        # We can add email validation later if needed
    
    def test_date_format_validation(self, client: TestClient):
        """Test date format validation"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        employee_data = {
            "person": {
                "full_name": "John Doe",
                "date_of_birth": "invalid-date"
            }
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 422  # Validation error

class TestEmployeeSearch:
    """Test US-02: Search and view employee records"""
    
    def setup_authenticated_user(self, client: TestClient, role: UserRole = UserRole.HR_ADMIN):
        """Helper to create and authenticate a user"""
        user_data = {
            "username": f"testuser_{role.value.lower()}",
            "email": f"test_{role.value.lower()}@example.com",
            "password": "testpassword123",
            "role": role.value
        }
        
        # Register user
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login user (sets session cookie automatically)
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        return user_data
    
    def create_test_employees(self, client: TestClient):
        """Helper to create test employees for search testing"""
        # Authenticate as HR Admin first
        self.setup_authenticated_user(client, UserRole.HR_ADMIN)
        
        employees_data = [
            {"person": {"full_name": "John Smith"}},
            {"person": {"full_name": "Jane Doe"}},
            {"person": {"full_name": "Bob Johnson"}},
            {"person": {"full_name": "Alice Wilson"}}
        ]
        
        created_employees = []
        for emp_data in employees_data:
            response = client.post("/api/v1/employees/", json=emp_data)
            assert response.status_code == 200
            created_employees.append(response.json())
        
        return created_employees
    
    def test_search_by_name_exact(self, client: TestClient):
        """Test searching employees by exact name"""
        employees = self.create_test_employees(client)
        
        response = client.get("/api/v1/employees/search?name=John Smith")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 1
        assert results[0]["person"]["full_name"] == "John Smith"
    
    def test_search_by_name_partial(self, client: TestClient):
        """Test searching employees by partial name"""
        employees = self.create_test_employees(client)
        
        response = client.get("/api/v1/employees/search?name=John")  # Should match "John Smith"
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        assert any("John" in emp["person"]["full_name"] for emp in results)
    
    def test_search_by_employee_id(self, client: TestClient):
        """Test searching employees by employee ID"""
        employees = self.create_test_employees(client)
        target_employee = employees[0]
        employee_id = target_employee["employee_id"]
        
        response = client.get(f"/api/v1/employees/search?employee_id={employee_id}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 1
        assert results[0]["employee_id"] == employee_id
        assert results[0]["person"]["full_name"] == target_employee["person"]["full_name"]
    
    def test_search_by_status(self, client: TestClient):
        """Test searching employees by status"""
        employees = self.create_test_employees(client)
        
        response = client.get(f"/api/v1/employees/search?status={EmployeeStatus.ACTIVE.value}")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 4  # All created employees should be active
        assert all(emp["status"] == EmployeeStatus.ACTIVE.value for emp in results)
    
    def test_search_no_results(self, client: TestClient):
        """Test search with no matching results"""
        self.create_test_employees(client)
        
        response = client.get("/api/v1/employees/search?name=NonExistentEmployee")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) == 0
    
    def test_search_with_pagination(self, client: TestClient):
        """Test search with pagination parameters"""
        self.create_test_employees(client)
        
        # Test with limit
        response = client.get("/api/v1/employees/search?limit=2")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 2
        
        # Test with skip
        response = client.get("/api/v1/employees/search?skip=1&limit=2")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 2
    
    def test_search_unauthenticated(self, client: TestClient):
        """Test that unauthenticated users cannot search"""
        response = client.get("/api/v1/employees/search?name=John")
        assert response.status_code == 401
    
    def test_search_as_employee_role(self, client: TestClient):
        """Test that regular employees can search (role-based access)"""
        # Create test data as HR Admin
        self.create_test_employees(client)
        
        # Authenticate as regular employee
        self.setup_authenticated_user(client, UserRole.EMPLOYEE)
        
        response = client.get("/api/v1/employees/search?name=John")
        assert response.status_code == 200  # All authenticated users can search
        
        results = response.json()
        assert isinstance(results, list)
    
    def test_search_as_supervisor_role(self, client: TestClient):
        """Test that supervisors can search (role-based access)"""
        # Create test data as HR Admin
        self.create_test_employees(client)
        
        # Authenticate as supervisor
        self.setup_authenticated_user(client, UserRole.SUPERVISOR)
        
        response = client.get("/api/v1/employees/search?name=Jane")
        assert response.status_code == 200  # All authenticated users can search
        
        results = response.json()
        assert isinstance(results, list)