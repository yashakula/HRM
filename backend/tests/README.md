# HRM Backend Test Suite

This project has two types of tests:

## Unit Tests (`tests/unit/`)

Fast, isolated tests that run against TestClient with SQLite database. These test business logic with mocking/stubbing where appropriate.

**To run unit tests:**
```bash
# Run all unit tests
uv run pytest tests/unit/ -v

# Run specific unit test file
uv run pytest tests/unit/test_auth.py -v
uv run pytest tests/unit/test_employees.py -v
```

**Features:**
- Uses TestClient (no actual HTTP server)
- SQLite in-memory database
- Fast execution (~3-5 seconds)
- Isolated test environment
- Authentication helper methods included

## Integration Tests (`tests/integration/`)

End-to-end tests that run against the actual localhost Docker server with real PostgreSQL database.

**Prerequisites:**
1. Docker server must be running:
```bash
cd /Users/yashakula/Documents/projects/HRM
docker-compose up -d
```

2. Backend server should be accessible at `http://localhost:8000`

**To run integration tests:**
```bash
# Run all integration tests
uv run pytest tests/integration/ -v

# Run specific integration test file
uv run pytest tests/integration/test_auth_integration.py -v
uv run pytest tests/integration/test_employees_integration.py -v
```

**Features:**
- Real HTTP requests to localhost:8000
- Real PostgreSQL database via Docker
- Tests complete request/response cycle
- Session-based authentication with real cookies
- Server readiness checking (waits up to 30 seconds)

## Running All Tests

```bash
# Run all tests (unit + integration)
uv run pytest -v

# Run only unit tests (fast)
uv run pytest tests/unit/ -v

# Run only integration tests (requires server)
uv run pytest tests/integration/ -v
```

## Test Configuration

- **Unit Tests**: `tests/conftest.py` - SQLite database, TestClient
- **Integration Tests**: `tests/integration/conftest.py` - HTTP client, server checking

## Troubleshooting Integration Tests

If integration tests fail:

1. **Check if Docker is running:**
```bash
docker-compose ps
```

2. **Check if backend is accessible:**
```bash
curl http://localhost:8000/docs
```

3. **View backend logs:**
```bash
docker-compose logs backend
```

4. **Restart services:**
```bash
docker-compose down
docker-compose up -d
```

The integration test suite will automatically wait up to 30 seconds for the server to be ready before running tests.