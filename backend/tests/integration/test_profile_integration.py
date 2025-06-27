"""
Integration tests for profile page functionality.
Tests the complete profile workflow including API endpoints and authentication.
"""
import pytest
from tests.integration.conftest import IntegrationTestClient


def test_profile_page_validation_all_roles(integration_client: IntegrationTestClient):
    """Test profile page access validation for all user roles"""
    # Test data for seed users
    seed_users = [
        {"username": "hr_admin", "password": "admin123"},
        {"username": "supervisor1", "password": "super123"},
        {"username": "employee1", "password": "emp123"}
    ]
    
    for user_data in seed_users:
        # Login as each user
        login_response = integration_client.post("/api/v1/auth/login", json={
            "username": user_data["username"], 
            "password": user_data["password"]
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
        assert data["permissions"]["can_create"] is False
        assert data["permissions"]["can_delete"] is False
        assert "All authenticated users can view and edit their own profile" in data["permissions"]["message"]
        
        # Logout
        integration_client.post("/api/v1/auth/logout")


def test_employee_directory_access_restrictions(integration_client: IntegrationTestClient):
    """Test that employee directory is properly restricted"""
    # Test each role's access to employee directory
    test_cases = [
        ("hr_admin", "admin123", True, "HR Admin can search all employees"),
        ("supervisor1", "super123", True, "Supervisors can view team members"),
        ("employee1", "emp123", False, "Only HR Admin and Supervisors can access employee directory")
    ]
    
    for username, password, should_have_access, expected_message in test_cases:
        # Login
        login_response = integration_client.post("/api/v1/auth/login", json={
            "username": username, 
            "password": password
        })
        assert login_response.status_code == 200
        
        # Test employees page access
        response = integration_client.post("/api/v1/auth/validate-page-access", json={
            "page_identifier": "employees"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["access_granted"] == should_have_access
        assert data["permissions"]["can_view"] == should_have_access
        assert expected_message in data["permissions"]["message"]
        
        # Logout
        integration_client.post("/api/v1/auth/logout")


def test_departments_access_restrictions(client: Client, test_db, seed_data):
    """Test that departments page is properly restricted"""
    users = seed_data["users"]
    
    # Test each role's access to departments
    test_cases = [
        ("hr_admin", True, True, "HR Admin has full department management access"),
        ("supervisor1", True, False, "Supervisors can view departments"),
        ("employee1", False, False, "Only HR Admin and Supervisors can access departments")
    ]
    
    for username, should_view, should_edit, expected_message in test_cases:
        # Find user data
        user_data = next(u for u in users if u["username"] == username)
        
        # Login
        login_response = client.post("/api/v1/auth/login", json={
            "username": user_data["username"], 
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        # Test departments page access
        response = client.post("/api/v1/auth/validate-page-access", json={
            "page_identifier": "departments"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["access_granted"] == should_view
        assert data["permissions"]["can_view"] == should_view
        assert data["permissions"]["can_edit"] == should_edit
        assert expected_message in data["permissions"]["message"]
        
        # Logout
        client.post("/api/v1/auth/logout")


def test_employee_own_profile_access(client: Client, test_db, seed_data):
    """Test that employees can access and update their own profiles"""
    # Login as employee1 (linked to Alice Johnson employee record)
    login_response = client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    # Get current user info to find employee ID
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    user_data = me_response.json()
    employee_id = user_data["employee"]["employee_id"]
    
    # Fetch employee profile data
    employee_response = client.get(f"/api/v1/employees/{employee_id}")
    assert employee_response.status_code == 200
    employee_data = employee_response.json()
    
    # Verify it's Alice Johnson
    assert employee_data["person"]["full_name"] == "Alice Johnson"
    
    # Test updating personal information
    update_data = {
        "personal_information": {
            "personal_email": "alice.updated@personal.com",
            "ssn": "123-45-6789",  # Keep existing
            "bank_account": "NEWACCOUNT123"
        }
    }
    
    update_response = client.put(f"/api/v1/employees/{employee_id}", json=update_data)
    assert update_response.status_code == 200
    
    # Verify the update
    updated_employee = client.get(f"/api/v1/employees/{employee_id}")
    assert updated_employee.status_code == 200
    updated_data = updated_employee.json()
    
    assert updated_data["person"]["personal_information"]["personal_email"] == "alice.updated@personal.com"
    assert updated_data["person"]["personal_information"]["bank_account"] == "NEWACCOUNT123"


def test_employee_cannot_access_others_profiles(client: Client, test_db, seed_data):
    """Test that employees cannot access other employees' detailed profiles"""
    # Login as employee1 
    login_response = client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    # Try to access another employee's profile (Bob Smith - employee_id 2)
    other_employee_response = client.get("/api/v1/employees/2")
    
    # Should get filtered response (no sensitive data) or 403 depending on implementation
    # Based on our security model, employees should get filtered data
    if other_employee_response.status_code == 200:
        other_data = other_employee_response.json()
        # Sensitive fields should be filtered out
        personal_info = other_data["person"].get("personal_information")
        if personal_info:
            # SSN and bank account should not be present or be None
            assert personal_info.get("ssn") is None
            assert personal_info.get("bank_account") is None


def test_supervisor_team_access(client: Client, test_db, seed_data):
    """Test that supervisors can access their team members' profiles"""
    # Login as supervisor1 (Bob Smith)
    login_response = client.post("/api/v1/auth/login", json={
        "username": "supervisor1", 
        "password": "super123"
    })
    assert login_response.status_code == 200
    
    # Get current user info
    me_response = client.get("/api/v1/auth/me")
    assert me_response.status_code == 200
    user_data = me_response.json()
    
    # Bob Smith should be able to access Alice Johnson's profile (his supervisee)
    # Based on seed data, Alice has Bob as supervisor
    alice_response = client.get("/api/v1/employees/1")  # Alice is employee_id 1
    assert alice_response.status_code == 200
    
    alice_data = alice_response.json()
    assert alice_data["person"]["full_name"] == "Alice Johnson"
    
    # Supervisor should see basic info but not sensitive personal details
    personal_info = alice_data["person"].get("personal_information")
    if personal_info:
        # Should not see SSN or bank account
        assert personal_info.get("ssn") is None
        assert personal_info.get("bank_account") is None


def test_hr_admin_full_access(client: Client, test_db, seed_data):
    """Test that HR Admin has full access to all employee profiles"""
    # Login as HR Admin
    login_response = client.post("/api/v1/auth/login", json={
        "username": "hr_admin", 
        "password": "admin123"
    })
    assert login_response.status_code == 200
    
    # HR Admin should be able to access any employee profile with full details
    alice_response = client.get("/api/v1/employees/1")
    assert alice_response.status_code == 200
    
    alice_data = alice_response.json()
    assert alice_data["person"]["full_name"] == "Alice Johnson"
    
    # HR Admin should see all information including sensitive data
    personal_info = alice_data["person"]["personal_information"]
    assert personal_info is not None
    assert personal_info["ssn"] == "123-45-6789"
    assert personal_info["bank_account"] == "ACC123456789"
    
    # HR Admin should be able to update any employee
    update_data = {
        "person": {
            "full_name": "Alice Johnson Updated"
        }
    }
    
    update_response = client.put("/api/v1/employees/1", json=update_data)
    assert update_response.status_code == 200
    
    # Verify the update
    updated_response = client.get("/api/v1/employees/1")
    assert updated_response.status_code == 200
    updated_data = updated_response.json()
    assert updated_data["person"]["full_name"] == "Alice Johnson Updated"


def test_profile_redirect_behavior(client: Client, test_db, seed_data):
    """Test that the system properly handles profile-based access patterns"""
    # This test validates the expected behavior for profile-centric access
    
    # Login as employee
    login_response = client.post("/api/v1/auth/login", json={
        "username": "employee1", 
        "password": "emp123"
    })
    assert login_response.status_code == 200
    
    # Verify employee can access profile page
    profile_access = client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "profile"
    })
    assert profile_access.status_code == 200
    assert profile_access.json()["access_granted"] is True
    
    # Verify employee cannot access employee directory
    employees_access = client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "employees"
    })
    assert employees_access.status_code == 200
    assert employees_access.json()["access_granted"] is False
    
    # Verify employee cannot access departments
    departments_access = client.post("/api/v1/auth/validate-page-access", json={
        "page_identifier": "departments"
    })
    assert departments_access.status_code == 200
    assert departments_access.json()["access_granted"] is False