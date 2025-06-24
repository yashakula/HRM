import pytest
import uuid
from tests.integration.conftest import IntegrationTestClient


class TestAuthenticationIntegration:
    """Integration tests for authentication against localhost server"""
    
    def test_user_registration_flow(self, integration_client: IntegrationTestClient):
        """Test complete user registration flow"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"integration_user_{unique_id}",
            "email": f"integration_{unique_id}@example.com",
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        
        response = integration_client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["role"] == "HR_ADMIN"
        assert data["is_active"] is True
        assert "password" not in data
    
    def test_login_logout_flow(self, integration_client: IntegrationTestClient):
        """Test complete login/logout flow"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"login_test_{unique_id}",
            "email": f"login_{unique_id}@example.com",
            "password": "testpassword123",
            "role": "SUPERVISOR"
        }
        
        # Register user
        register_response = integration_client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Login
        login_data = {"username": user_data["username"], "password": user_data["password"]}
        login_response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        login_data = login_response.json()
        assert login_data["message"] == "Login successful"
        assert login_data["user"]["username"] == user_data["username"]
        assert login_data["user"]["role"] == "SUPERVISOR"
        
        # Check that session cookie is set
        assert "session_token" in integration_client.session.cookies
        
        # Test authenticated endpoint
        profile_response = integration_client.get("/api/v1/auth/me")
        assert profile_response.status_code == 200
        profile_data = profile_response.json()
        assert profile_data["username"] == user_data["username"]
        
        # Logout
        logout_response = integration_client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        logout_data = logout_response.json()
        assert logout_data["message"] == "Successfully logged out"
        
        # Verify session is cleared - profile should fail
        profile_response_after_logout = integration_client.get("/api/v1/auth/me")
        assert profile_response_after_logout.status_code == 401
    
    def test_invalid_credentials(self, integration_client: IntegrationTestClient):
        """Test login with invalid credentials"""
        login_data = {"username": "nonexistent", "password": "wrongpassword"}
        response = integration_client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_duplicate_username_registration(self, integration_client: IntegrationTestClient):
        """Test that duplicate username registration fails"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "username": f"duplicate_test_{unique_id}",
            "email": f"test1_{unique_id}@example.com",
            "password": "testpassword123",
            "role": "EMPLOYEE"
        }
        
        # Register first user
        response1 = integration_client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register with same username, different email
        user_data["email"] = f"test2_{unique_id}@example.com"
        response2 = integration_client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Username already registered" in response2.json()["detail"]


class TestRoleBasedAccessIntegration:
    """Integration tests for role-based access control"""
    
    def test_hr_admin_can_create_employee(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test that HR Admin can create employees via real server"""
        employee_data = {
            "person": {
                "full_name": "Integration Test Employee"
            }
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["person"]["full_name"] == "Integration Test Employee"
        assert data["employee_id"] is not None
    
    def test_supervisor_cannot_create_employee(self, integration_client: IntegrationTestClient, authenticated_supervisor):
        """Test that Supervisor cannot create employees"""
        employee_data = {
            "person": {
                "full_name": "Should Not Be Created"
            }
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 403
        assert "HR_ADMIN" in response.json()["detail"]
    
    def test_employee_cannot_create_employee(self, integration_client: IntegrationTestClient, authenticated_employee):
        """Test that Employee cannot create employees"""
        employee_data = {
            "person": {
                "full_name": "Should Not Be Created"
            }
        }
        
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 403
        assert "HR_ADMIN" in response.json()["detail"]
    
    def test_all_roles_can_view_employees(self, integration_client: IntegrationTestClient, authenticated_hr_admin):
        """Test that all authenticated users can view employees"""
        # First create an employee as HR Admin
        employee_data = {
            "person": {
                "full_name": "Viewable Employee"
            }
        }
        create_response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert create_response.status_code == 200
        employee_id = create_response.json()["employee_id"]
        
        # HR Admin can view
        view_response = integration_client.get(f"/api/v1/employees/{employee_id}")
        assert view_response.status_code == 200
        assert view_response.json()["person"]["full_name"] == "Viewable Employee"
        
        # Test listing employees
        list_response = integration_client.get("/api/v1/employees/")
        assert list_response.status_code == 200
        employees = list_response.json()
        assert len(employees) >= 1
        assert any(emp["employee_id"] == employee_id for emp in employees)
    
    def test_unauthenticated_access_denied(self, integration_client: IntegrationTestClient):
        """Test that unauthenticated users cannot access protected endpoints"""
        # Ensure no authentication
        integration_client.post("/api/v1/auth/logout")
        
        # Try to create employee without authentication
        employee_data = {
            "person": {
                "full_name": "Unauthorized Employee"
            }
        }
        response = integration_client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
        
        # Try to view employees without authentication  
        response = integration_client.get("/api/v1/employees/")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]