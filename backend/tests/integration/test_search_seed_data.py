"""
Integration tests for employee search using seed data.
These tests can be disabled by setting ENABLE_SEARCH_INTEGRATION_TESTS=false
"""

import pytest
import os
from tests.integration.conftest import IntegrationTestClient

# Allow disabling these tests via environment variable
ENABLE_TESTS = os.getenv("ENABLE_SEARCH_INTEGRATION_TESTS", "true").lower() == "true"

pytestmark = pytest.mark.skipif(
    not ENABLE_TESTS, 
    reason="Search integration tests disabled (set ENABLE_SEARCH_INTEGRATION_TESTS=true to enable)"
)


class TestEmployeeSearchWithSeedData:
    """Test employee search functionality using pre-created seed data"""
    
    def test_search_seed_employee_by_name(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Test searching for seed employees by name"""
        # Search for Alice Johnson (from seed data)
        response = integration_client.get("/api/v1/employees/search?name=Alice Johnson")
        assert response.status_code == 200
        
        results = response.json()
        # Should find at least 1 Alice Johnson (from seed data)
        assert len(results) >= 1
        
        # Verify we found Alice Johnson (may be multiple due to previous tests)
        alice_found = False
        for employee in results:
            if employee["person"]["full_name"] == "Alice Johnson":
                alice_found = True
                # Check if this is the seed data version (has personal info)
                if (employee["person"]["personal_information"] and 
                    employee["person"]["personal_information"]["personal_email"] == "alice.johnson@personal.com"):
                    # This is our seed data Alice Johnson
                    assert employee["person"]["date_of_birth"] == "1985-03-15"
                    break
        
        assert alice_found, "Alice Johnson from seed data not found"
    
    def test_search_seed_employees_partial_name(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Test partial name search with seed data"""
        # Search for "Johnson" should find Alice Johnson
        response = integration_client.get("/api/v1/employees/search?name=Johnson")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) >= 1
        
        # Should contain Alice Johnson
        alice_found = any(
            emp["person"]["full_name"] == "Alice Johnson" 
            for emp in results
        )
        assert alice_found, "Alice Johnson not found in partial search"
    
    def test_search_by_status_active(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Test searching by status using seed data"""
        response = integration_client.get("/api/v1/employees/search?status=Active")
        assert response.status_code == 200
        
        results = response.json()
        # Should find multiple active employees from seed data
        assert len(results) >= 4  # At least 4 active seed employees
        
        # All results should have Active status
        for employee in results:
            assert employee["status"] in ["Active", "ACTIVE"]
    
    def test_search_with_pagination(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Test search pagination"""
        # Get first 2 results
        response = integration_client.get("/api/v1/employees/search?limit=2")
        assert response.status_code == 200
        
        results = response.json()
        assert len(results) <= 2
    
    def test_search_as_different_roles(self, integration_client: IntegrationTestClient, seed_supervisor, seed_employee):
        """Test that different roles can search using seed users"""
        # Test as supervisor
        response = integration_client.get("/api/v1/employees/search?name=Alice")
        assert response.status_code == 200
        
        # Logout supervisor, login as employee  
        integration_client.post("/api/v1/auth/logout")
        
        # Login as employee and test search
        from hrm_backend.seed_data import get_seed_user_credentials
        employee_creds = get_seed_user_credentials("employee1")
        login_response = integration_client.post("/api/v1/auth/login", json=employee_creds)
        assert login_response.status_code == 200
        
        response = integration_client.get("/api/v1/employees/search?name=Bob")
        assert response.status_code == 200
        
        results = response.json()
        assert isinstance(results, list)


class TestSearchValidationWithSeedData:
    """Test search validation using seed data"""
    
    def test_search_invalid_parameters(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Test validation errors with seed data environment"""
        # Test invalid employee_id (non-integer)
        response = integration_client.get("/api/v1/employees/search?employee_id=invalid")
        assert response.status_code == 422
        
        # Test invalid status
        response = integration_client.get("/api/v1/employees/search?status=InvalidStatus")
        assert response.status_code == 422
    
    def test_search_unauthenticated(self, integration_client: IntegrationTestClient):
        """Test that unauthenticated users cannot search"""
        response = integration_client.get("/api/v1/employees/search?name=Alice")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]


class TestSeedDataConsistency:
    """Test that seed data is properly created and accessible"""
    
    def test_seed_employees_exist(self, integration_client: IntegrationTestClient, seed_hr_admin):
        """Verify that seed employees were created properly"""
        expected_names = ["Alice Johnson", "Bob Smith", "Charlie Brown", "Diana Wilson", "Edward Davis"]
        
        # Get all employees
        response = integration_client.get("/api/v1/employees/")
        assert response.status_code == 200
        
        all_employees = response.json()
        found_names = [emp["person"]["full_name"] for emp in all_employees]
        
        # Check that all seed employees exist
        for name in expected_names:
            assert name in found_names, f"Seed employee {name} not found"
    
    def test_seed_users_can_login(self, integration_client: IntegrationTestClient):
        """Test that all seed users can login successfully"""
        from hrm_backend.seed_data import get_seed_user_credentials
        
        seed_usernames = ["hr_admin", "supervisor1", "employee1"]
        
        for username in seed_usernames:
            credentials = get_seed_user_credentials(username)
            assert credentials is not None, f"Credentials not found for {username}"
            
            response = integration_client.post("/api/v1/auth/login", json=credentials)
            assert response.status_code == 200, f"Login failed for {username}: {response.text}"
            
            # Logout for next user
            integration_client.post("/api/v1/auth/logout")