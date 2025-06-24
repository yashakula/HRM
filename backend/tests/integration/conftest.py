import pytest
import requests
import time
from typing import Generator

# Integration test configuration
INTEGRATION_BASE_URL = "http://localhost:8000"
MAX_RETRIES = 30
RETRY_DELAY = 1


class IntegrationTestClient:
    """HTTP client for integration tests against localhost server"""
    
    def __init__(self, base_url: str = INTEGRATION_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def post(self, endpoint: str, **kwargs):
        return self.session.post(f"{self.base_url}{endpoint}", **kwargs)
    
    def get(self, endpoint: str, **kwargs):
        return self.session.get(f"{self.base_url}{endpoint}", **kwargs)
    
    def put(self, endpoint: str, **kwargs):
        return self.session.put(f"{self.base_url}{endpoint}", **kwargs)
    
    def delete(self, endpoint: str, **kwargs):
        return self.session.delete(f"{self.base_url}{endpoint}", **kwargs)


def wait_for_server(base_url: str = INTEGRATION_BASE_URL, max_retries: int = MAX_RETRIES):
    """Wait for the server to be ready"""
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            if response.status_code == 200:
                print(f"Server is ready after {i+1} attempts")
                return True
        except requests.exceptions.RequestException:
            pass
        
        if i < max_retries - 1:
            print(f"Waiting for server... attempt {i+1}/{max_retries}")
            time.sleep(RETRY_DELAY)
    
    raise Exception(f"Server not ready after {max_retries} attempts")


@pytest.fixture(scope="session", autouse=True)
def ensure_server_running():
    """Ensure the Docker server is running before integration tests"""
    print("Checking if server is running for integration tests...")
    wait_for_server()
    yield
    print("Integration tests completed")


@pytest.fixture(scope="function")
def integration_client() -> Generator[IntegrationTestClient, None, None]:
    """Provide an HTTP client for integration tests"""
    client = IntegrationTestClient()
    yield client
    # Cleanup: logout if session exists
    try:
        client.post("/api/v1/auth/logout")
    except:
        pass


@pytest.fixture(scope="function")
def authenticated_hr_admin(integration_client: IntegrationTestClient):
    """Create and authenticate an HR Admin user for tests"""
    import uuid
    
    # Create unique user data
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"hr_admin_{unique_id}",
        "email": f"hr_admin_{unique_id}@example.com",
        "password": "testpassword123",
        "role": "HR_ADMIN"
    }
    
    # Register user
    register_response = integration_client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
    
    # Login user
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = integration_client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    return user_data


@pytest.fixture(scope="function")
def authenticated_supervisor(integration_client: IntegrationTestClient):
    """Create and authenticate a Supervisor user for tests"""
    import uuid
    
    # Create unique user data
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"supervisor_{unique_id}",
        "email": f"supervisor_{unique_id}@example.com",
        "password": "testpassword123",
        "role": "SUPERVISOR"
    }
    
    # Register user
    register_response = integration_client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
    
    # Login user
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = integration_client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    return user_data


@pytest.fixture(scope="function")
def authenticated_employee(integration_client: IntegrationTestClient):
    """Create and authenticate an Employee user for tests"""
    import uuid
    
    # Create unique user data
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "username": f"employee_{unique_id}",
        "email": f"employee_{unique_id}@example.com",
        "password": "testpassword123",
        "role": "EMPLOYEE"
    }
    
    # Register user
    register_response = integration_client.post("/api/v1/auth/register", json=user_data)
    assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
    
    # Login user
    login_data = {"username": user_data["username"], "password": user_data["password"]}
    login_response = integration_client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    
    return user_data