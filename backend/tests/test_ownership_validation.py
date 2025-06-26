"""
Test suite for data ownership validation
Tests Task 1.2: Data Ownership Controls implementation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from sqlalchemy.orm import Session
from src.hrm_backend.models import Base, User, Employee, People, PersonalInformation, UserRole, EmployeeStatus
from src.hrm_backend.auth import validate_employee_access, check_employee_ownership
from src.hrm_backend.database import get_db
from fastapi import HTTPException
from unittest.mock import Mock

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ownership_validation.db"
test_engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def hr_admin_user(db_session):
    """Create HR Admin user"""
    user = User(
        username="hr_admin",
        email="hr@example.com",
        password_hash="hashed_password",
        role=UserRole.HR_ADMIN,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def employee_user(db_session):
    """Create Employee user"""
    user = User(
        username="employee",
        email="employee@example.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def other_employee_user(db_session):
    """Create another Employee user"""
    user = User(
        username="other_employee",
        email="other_employee@example.com",
        password_hash="hashed_password",
        role=UserRole.EMPLOYEE,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_employee_record(db_session, employee_user):
    """Create an employee record linked to employee_user"""
    person = People(
        full_name="John Doe",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    personal_info = PersonalInformation(
        people_id=person.people_id,
        personal_email="john.doe@personal.com",
        ssn="123-45-6789",
        bank_account="9876543210"
    )
    db_session.add(personal_info)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=employee_user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="john.doe@company.com",
        effective_start_date=date(2023, 1, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def other_employee_record(db_session):
    """Create another employee record (no user association)"""
    person = People(
        full_name="Jane Smith",
        date_of_birth=date(1985, 5, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    personal_info = PersonalInformation(
        people_id=person.people_id,
        personal_email="jane.smith@personal.com",
        ssn="987-65-4321",
        bank_account="1234567890"
    )
    db_session.add(personal_info)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=None,  # No user association
        status=EmployeeStatus.ACTIVE,
        work_email="jane.smith@company.com",
        effective_start_date=date(2022, 6, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

class TestOwnershipValidation:
    """Test ownership validation logic"""
    
    def test_employee_owns_their_record(self, db_session, employee_user, test_employee_record):
        """Test that employee owns their own record"""
        is_owner = check_employee_ownership(employee_user, test_employee_record.employee_id, db_session)
        assert is_owner is True
    
    def test_employee_does_not_own_other_record(self, db_session, employee_user, other_employee_record):
        """Test that employee does not own other employee records"""
        is_owner = check_employee_ownership(employee_user, other_employee_record.employee_id, db_session)
        assert is_owner is False
    
    def test_hr_admin_owns_any_record(self, db_session, hr_admin_user, other_employee_record):
        """Test that HR Admin has ownership access to any record"""
        is_owner = check_employee_ownership(hr_admin_user, other_employee_record.employee_id, db_session)
        assert is_owner is True

class TestOwnershipDecorator:
    """Test the ownership validation decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_allows_hr_admin_access(self, db_session, hr_admin_user, other_employee_record):
        """Test that decorator allows HR Admin to access any record"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(employee_id: int, current_user: User, db: Session):
            return f"Accessed employee {employee_id}"
        
        result = await test_function(
            employee_id=other_employee_record.employee_id,
            current_user=hr_admin_user,
            db=db_session
        )
        
        assert result == f"Accessed employee {other_employee_record.employee_id}"
    
    @pytest.mark.asyncio
    async def test_decorator_allows_owner_access(self, db_session, employee_user, test_employee_record):
        """Test that decorator allows employee to access their own record"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(employee_id: int, current_user: User, db: Session):
            return f"Accessed employee {employee_id}"
        
        result = await test_function(
            employee_id=test_employee_record.employee_id,
            current_user=employee_user,
            db=db_session
        )
        
        assert result == f"Accessed employee {test_employee_record.employee_id}"
    
    @pytest.mark.asyncio
    async def test_decorator_blocks_unauthorized_access(self, db_session, employee_user, other_employee_record):
        """Test that decorator blocks employee from accessing other employee records"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(employee_id: int, current_user: User, db: Session):
            return f"Accessed employee {employee_id}"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                employee_id=other_employee_record.employee_id,
                current_user=employee_user,
                db=db_session
            )
        
        assert exc_info.value.status_code == 403
        assert "Access Denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_decorator_error_response_format(self, db_session, employee_user, other_employee_record):
        """Test that decorator returns properly formatted error response"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(employee_id: int, current_user: User, db: Session):
            return f"Accessed employee {employee_id}"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                employee_id=other_employee_record.employee_id,
                current_user=employee_user,
                db=db_session
            )
        
        error_detail = exc_info.value.detail
        assert isinstance(error_detail, dict)
        assert error_detail["error"] == "Access Denied"
        assert "Insufficient permissions" in error_detail["message"]
        assert error_detail["user_role"] == "EMPLOYEE"
        assert "HR_ADMIN" in error_detail["required_permissions"]
        assert "resource_owner" in error_detail["required_permissions"]

class TestArgumentExtraction:
    """Test that the decorator properly extracts arguments"""
    
    @pytest.mark.asyncio
    async def test_decorator_extracts_positional_employee_id(self, db_session, hr_admin_user):
        """Test that decorator can extract employee_id from positional arguments"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(employee_id, db, current_user):
            return f"Accessed employee {employee_id}"
        
        result = await test_function(
            123,  # positional employee_id
            db_session,
            hr_admin_user
        )
        
        assert result == "Accessed employee 123"
    
    @pytest.mark.asyncio
    async def test_decorator_missing_employee_id_error(self, db_session, hr_admin_user):
        """Test that decorator raises error when employee_id is missing"""
        
        @validate_employee_access(allow_supervisor_access=False)
        async def test_function(db: Session, current_user: User):
            return "Should not reach here"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                db=db_session,
                current_user=hr_admin_user
            )
        
        assert exc_info.value.status_code == 400
        assert "Employee ID not found" in exc_info.value.detail