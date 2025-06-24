import pytest
from fastapi.testclient import TestClient
from hrm_backend.models import UserRole, User
from hrm_backend.auth import get_password_hash

class TestAuthentication:
    """Test authentication system"""
    
    def test_register_user(self, client: TestClient):
        """Test user registration"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["role"] == "HR_ADMIN"
        assert data["is_active"] == True
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_username(self, client: TestClient):
        """Test that duplicate username registration fails"""
        user_data = {
            "username": "duplicate",
            "email": "test1@example.com",
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        
        # Register first user
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Try to register with same username
        user_data["email"] = "test2@example.com"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Username already registered" in response2.json()["detail"]
    
    def test_login_success(self, client: TestClient):
        """Test successful login"""
        # First register a user
        user_data = {
            "username": "logintest",
            "email": "login@example.com",
            "password": "testpassword123",
            "role": "HR_ADMIN"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Then login
        login_data = {
            "username": "logintest",
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Login successful"
        assert "user" in data
        assert data["user"]["username"] == "logintest"
        assert data["user"]["role"] == "HR_ADMIN"
        
        # Check that session cookie was set
        assert "session_token" in response.cookies
    
    def test_login_wrong_password(self, client: TestClient):
        """Test login with wrong password"""
        # First register a user
        user_data = {
            "username": "wrongpass",
            "email": "wrongpass@example.com",
            "password": "correctpassword",
            "role": "HR_ADMIN"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        # Try login with wrong password
        login_data = {
            "username": "wrongpass",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_get_current_user(self, client: TestClient):
        """Test getting current user info"""
        # Register and login
        user_data = {
            "username": "currentuser",
            "email": "current@example.com", 
            "password": "testpassword123",
            "role": "SUPERVISOR"
        }
        client.post("/api/v1/auth/register", json=user_data)
        
        login_data = {
            "username": "currentuser",
            "password": "testpassword123"
        }
        # Login sets session cookie automatically for the client
        login_response = client.post("/api/v1/auth/login", json=login_data)
        
        # Get current user (using session cookie)
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == "currentuser"
        assert data["role"] == "SUPERVISOR"

class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def setup_users_and_clients(self, client: TestClient):
        """Helper to create users with different roles and return authenticated clients"""
        from fastapi.testclient import TestClient
        from hrm_backend.main import app
        
        users = [
            {"username": "hradmin", "email": "hr@example.com", "password": "pass123", "role": "HR_ADMIN"},
            {"username": "supervisor", "email": "sup@example.com", "password": "pass123", "role": "SUPERVISOR"},
            {"username": "employee", "email": "emp@example.com", "password": "pass123", "role": "EMPLOYEE"}
        ]
        
        clients = {}
        for user in users:
            # Register user
            client.post("/api/v1/auth/register", json=user)
            
            # Create new client for this user and login
            user_client = TestClient(app)
            login_data = {"username": user["username"], "password": user["password"]}
            user_client.post("/api/v1/auth/login", json=login_data)
            clients[user["role"]] = user_client
        
        return clients
    
    def test_hr_admin_can_create_employee(self, client: TestClient):
        """Test that HR Admin can create employees"""
        clients = self.setup_users_and_clients(client)
        
        employee_data = {
            "person": {
                "full_name": "New Employee"
            }
        }
        
        response = clients['HR_ADMIN'].post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 200
    
    def test_supervisor_cannot_create_employee(self, client: TestClient):
        """Test that Supervisor cannot create employees"""
        clients = self.setup_users_and_clients(client)
        
        employee_data = {
            "person": {
                "full_name": "New Employee"
            }
        }
        
        response = clients['SUPERVISOR'].post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 403
        assert "HR_ADMIN" in response.json()["detail"]
    
    def test_employee_cannot_create_employee(self, client: TestClient):
        """Test that Employee cannot create employees"""
        clients = self.setup_users_and_clients(client)
        
        employee_data = {
            "person": {
                "full_name": "New Employee"
            }
        }
        
        response = clients['EMPLOYEE'].post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 403
        assert "HR_ADMIN" in response.json()["detail"]
    
    def test_all_roles_can_view_employees(self, client: TestClient):
        """Test that all authenticated users can view employees"""
        clients = self.setup_users_and_clients(client)
        
        # First create an employee as HR Admin
        employee_data = {
            "person": {
                "full_name": "View Test Employee"
            }
        }
        create_response = clients['HR_ADMIN'].post("/api/v1/employees/", json=employee_data)
        employee_id = create_response.json()["employee_id"]
        
        # Test that all roles can view
        for role in ["HR_ADMIN", "SUPERVISOR", "EMPLOYEE"]:
            response = clients[role].get(f"/api/v1/employees/{employee_id}")
            assert response.status_code == 200, f"Role {role} should be able to view employees"
    
    def test_unauthenticated_access_denied(self, client: TestClient):
        """Test that unauthenticated users cannot access protected endpoints"""
        employee_data = {
            "person": {
                "full_name": "Unauthorized Employee"
            }
        }
        
        # Try to create employee without token
        response = client.post("/api/v1/employees/", json=employee_data)
        assert response.status_code == 401
        
        # Try to view employees without token
        response = client.get("/api/v1/employees/")
        assert response.status_code == 401