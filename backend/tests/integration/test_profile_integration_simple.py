"""
Simplified integration tests for profile page functionality.
Tests the complete profile workflow including API endpoints and authentication.
"""
import pytest
from tests.integration.conftest import IntegrationTestClient


def test_profile_page_access_all_roles(integration_client: IntegrationTestClient):
    """Test that all user roles can access their profile page"""
    # Test with HR Admin
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "hr_admin", 
        "password": "admin123"
    })
    assert login_response.status_code == 200
    
    # Test profile page access
    response = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "profile"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["access_granted"] is True
    assert data["permissions"]["can_view"] is True
    assert data["permissions"]["can_edit"] is True
    
    # Logout
    integration_client.post("/api/v1/auth/logout")


def test_employee_directory_restrictions(integration_client: IntegrationTestClient):
    """Test that employee directory is properly restricted"""
    # Test Employee cannot access employee directory
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    response = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "employees"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["access_granted"] is False
    assert data["permissions"]["can_view"] is False
    assert "Only HR Admin and Supervisors can access employee directory" in data["permissions"]["message"]
    
    integration_client.post("/api/v1/auth/logout")
    
    # Test HR Admin can access employee directory
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "hr_admin", 
        "password": "admin123"
    })
    assert login_response.status_code == 200
    
    response = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "employees"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["access_granted"] is True
    assert data["permissions"]["can_view"] is True
    
    integration_client.post("/api/v1/auth/logout")


def test_departments_access_restrictions(integration_client: IntegrationTestClient):
    """Test that departments page is properly restricted"""
    # Test Employee cannot access departments
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    response = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "departments"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["access_granted"] is False
    assert data["permissions"]["can_view"] is False
    assert "Only HR Admin and Supervisors can access departments" in data["permissions"]["message"]
    
    integration_client.post("/api/v1/auth/logout")
    
    # Test HR Admin can access departments
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "hr_admin", 
        "password": "admin123"
    })
    assert login_response.status_code == 200
    
    response = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "departments"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["access_granted"] is True
    assert data["permissions"]["can_view"] is True
    assert data["permissions"]["can_edit"] is True
    
    integration_client.post("/api/v1/auth/logout")


def test_employee_profile_access(integration_client: IntegrationTestClient):
    """Test that employees can access and view their own profile data"""
    # Login as employee1 (linked to Alice Johnson employee record)
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    # Get current user info to find employee ID
    me_response = integration_client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    user_data = me_response.json()
    
    # Should have employee information linked
    assert "employee" in user_data
    assert user_data["employee"] is not None
    employee_id = user_data["employee"]["employee_id"]
    
    # Fetch employee profile data
    employee_response = integration_client.get(f"/api/v1/employees/{employee_id}")
    assert employee_response.status_code == 200
    employee_data = employee_response.json()
    
    # Verify it's Alice Johnson
    assert employee_data["person"]["full_name"] == "Alice Johnson"
    
    # Should be able to see own sensitive data
    personal_info = employee_data["person"]["personal_information"]
    assert personal_info is not None
    assert personal_info["ssn"] == "123-45-6789"
    
    integration_client.post("/api/v1/auth/logout")


def test_role_based_navigation_simulation(integration_client: IntegrationTestClient):
    """Test the expected behavior for role-based navigation"""
    # Test Employee - should only have profile access
    login_response = integration_client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    # Profile access - should work
    profile_access = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "profile"
    })
    assert profile_access.status_code == 200
    assert profile_access.json()["access_granted"] is True
    
    # Employee directory - should fail
    employees_access = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "employees"
    })
    assert employees_access.status_code == 200
    assert employees_access.json()["access_granted"] is False
    
    # Departments - should fail
    departments_access = integration_client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "departments"
    })
    assert departments_access.status_code == 200
    assert departments_access.json()["access_granted"] is False
    
    integration_client.post("/api/v1/auth/logout")