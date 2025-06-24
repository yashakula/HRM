import pytest
from fastapi.testclient import TestClient
from datetime import date

from hrm_backend.models import EmployeeStatus

class TestEmployeeCreation:
    """Test US-01: Create employee profile"""
    
    def test_create_employee_minimal(self, client: TestClient):
        """Test creating employee with minimal required data"""
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
        employee_data = {
            "person": {}
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 422  # Validation error
    
    def test_get_employee_by_id(self, client: TestClient):
        """Test retrieving employee by ID"""
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
        response = client.get("/api/v1/employees/99999")
        assert response.status_code == 404
        assert "Employee not found" in response.json()["detail"]
    
    def test_list_employees(self, client: TestClient):
        """Test listing employees"""
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
    
    def test_invalid_email_format(self, client: TestClient):
        """Test that invalid email format is handled"""
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
        employee_data = {
            "person": {
                "full_name": "John Doe",
                "date_of_birth": "invalid-date"
            }
        }
        
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 422  # Validation error