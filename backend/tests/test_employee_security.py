"""
Comprehensive test suite for role-based response filtering
Tests Task 1.1: Role-Based Response Filtering implementation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from src.hrm_backend.models import Base, User, Employee, People, PersonalInformation, UserRole, EmployeeStatus
from src.hrm_backend.auth import (
    filter_employee_response, 
    check_employee_ownership, 
    check_supervisor_relationship,
    get_employee_by_user_id
)
from src.hrm_backend import schemas
from src.hrm_backend.database import get_db

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_employee_security.db"
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
    """Create HR Admin user for testing"""
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
def supervisor_user(db_session):
    """Create Supervisor user for testing"""
    user = User(
        username="supervisor",
        email="supervisor@example.com",
        password_hash="hashed_password",
        role=UserRole.SUPERVISOR,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def employee_user(db_session):
    """Create Employee user for testing"""
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
def test_person_with_sensitive_data(db_session):
    """Create a person with sensitive personal information"""
    person = People(
        full_name="John Doe",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    # Add sensitive personal information
    personal_info = PersonalInformation(
        people_id=person.people_id,
        personal_email="john.doe@personal.com",
        ssn="123-45-6789",
        bank_account="9876543210"
    )
    db_session.add(personal_info)
    db_session.commit()
    db_session.refresh(person)
    return person

@pytest.fixture
def test_employee_with_user(db_session, employee_user, test_person_with_sensitive_data):
    """Create an employee record linked to a user"""
    employee = Employee(
        people_id=test_person_with_sensitive_data.people_id,
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
def other_employee_with_sensitive_data(db_session):
    """Create another employee record with sensitive data (no user link)"""
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

class TestHRAdminAccess:
    """Test HR Admin users can access all employee data including sensitive fields"""
    
    def test_hr_admin_sees_all_sensitive_fields(self, db_session, hr_admin_user, test_employee_with_user):
        """HR Admin should see SSN and bank account fields in response"""
        result = filter_employee_response(test_employee_with_user, hr_admin_user, db_session)
        
        # Should be EmployeeResponseHR type
        assert isinstance(result, schemas.EmployeeResponseHR)
        
        # Verify all sensitive fields are present
        assert result.person.personal_information is not None
        assert result.person.personal_information.ssn == "123-45-6789"
        assert result.person.personal_information.bank_account == "9876543210"
        assert result.person.personal_information.personal_email == "john.doe@personal.com"
    
    def test_hr_admin_access_to_any_employee(self, db_session, hr_admin_user, other_employee_with_sensitive_data):
        """HR Admin should access any employee record with full data"""
        result = filter_employee_response(other_employee_with_sensitive_data, hr_admin_user, db_session)
        
        assert isinstance(result, schemas.EmployeeResponseHR)
        assert result.person.personal_information.ssn == "987-65-4321"
        assert result.person.personal_information.bank_account == "1234567890"

class TestEmployeeOwnerAccess:
    """Test employees can see their own complete data including sensitive fields"""
    
    def test_employee_sees_own_sensitive_data(self, db_session, employee_user, test_employee_with_user):
        """Employee should see their own SSN and bank account data"""
        result = filter_employee_response(test_employee_with_user, employee_user, db_session)
        
        # Should be EmployeeResponseOwner type
        assert isinstance(result, schemas.EmployeeResponseOwner)
        
        # Verify sensitive fields are present for own record
        assert result.person.personal_information is not None
        assert result.person.personal_information.ssn == "123-45-6789"
        assert result.person.personal_information.bank_account == "9876543210"
        assert result.person.personal_information.personal_email == "john.doe@personal.com"

class TestEmployeeRestrictedAccess:
    """Test employees cannot see other employees' sensitive data"""
    
    def test_employee_cannot_see_other_sensitive_data(self, db_session, employee_user, other_employee_with_sensitive_data):
        """Employee should not see SSN or bank account for other employees"""
        result = filter_employee_response(other_employee_with_sensitive_data, employee_user, db_session)
        
        # Should be EmployeeResponseBasic type
        assert isinstance(result, schemas.EmployeeResponseBasic)
        
        # Verify sensitive fields are completely absent (no personal_information relationship)
        # In Basic response, there should be no personal_information field
        assert not hasattr(result.person, 'personal_information')

class TestSupervisorAccess:
    """Test supervisors receive basic information without sensitive data"""
    
    def test_supervisor_sees_basic_data_only(self, db_session, supervisor_user, test_employee_with_user):
        """Supervisor should see basic employee info without sensitive fields"""
        result = filter_employee_response(test_employee_with_user, supervisor_user, db_session)
        
        # Should be EmployeeResponseBasic type
        assert isinstance(result, schemas.EmployeeResponseBasic)
        
        # Verify basic fields are present
        assert result.person.full_name == "John Doe"
        assert result.work_email == "john.doe@company.com"
        
        # Verify sensitive fields are absent
        assert not hasattr(result.person, 'personal_information')

class TestOwnershipValidation:
    """Test employee ownership checking functions"""
    
    def test_check_employee_ownership_true(self, db_session, employee_user, test_employee_with_user):
        """check_employee_ownership should return True for user's own employee record"""
        is_owner = check_employee_ownership(employee_user, test_employee_with_user.employee_id, db_session)
        assert is_owner is True
    
    def test_check_employee_ownership_false(self, db_session, employee_user, other_employee_with_sensitive_data):
        """check_employee_ownership should return False for other employee records"""
        is_owner = check_employee_ownership(employee_user, other_employee_with_sensitive_data.employee_id, db_session)
        assert is_owner is False
    
    def test_hr_admin_ownership_always_true(self, db_session, hr_admin_user, other_employee_with_sensitive_data):
        """HR Admin should have ownership access to any employee record"""
        is_owner = check_employee_ownership(hr_admin_user, other_employee_with_sensitive_data.employee_id, db_session)
        assert is_owner is True

class TestEndpointSchemaConsistency:
    """Test that filtering works consistently across different endpoints"""
    
    def test_individual_employee_endpoint_filtering(self, db_session, employee_user, test_employee_with_user):
        """Test filtering works for individual employee GET endpoint"""
        # This would be called by the individual employee endpoint
        result = filter_employee_response(test_employee_with_user, employee_user, db_session)
        assert isinstance(result, schemas.EmployeeResponseOwner)
    
    def test_search_endpoint_filtering(self, db_session, employee_user, other_employee_with_sensitive_data):
        """Test filtering works for employee search endpoint"""
        # This would be called for each employee in search results
        result = filter_employee_response(other_employee_with_sensitive_data, employee_user, db_session)
        assert isinstance(result, schemas.EmployeeResponseBasic)

class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_user_without_employee_record(self, db_session, employee_user, other_employee_with_sensitive_data):
        """Test user without associated employee record"""
        # Create a user without an employee record
        user_without_employee = User(
            username="no_employee",
            email="no_employee@example.com",
            password_hash="hashed_password",
            role=UserRole.EMPLOYEE,
            is_active=True
        )
        db_session.add(user_without_employee)
        db_session.commit()
        
        # Should not have ownership of any employee record
        is_owner = check_employee_ownership(user_without_employee, other_employee_with_sensitive_data.employee_id, db_session)
        assert is_owner is False
    
    def test_employee_with_no_personal_information(self, db_session, hr_admin_user):
        """Test employee record without personal_information relationship"""
        person = People(
            full_name="No Personal Info",
            date_of_birth=date(1995, 3, 10)
        )
        db_session.add(person)
        db_session.flush()
        
        employee = Employee(
            people_id=person.people_id,
            user_id=None,
            status=EmployeeStatus.ACTIVE,
            work_email="no.info@company.com"
        )
        db_session.add(employee)
        db_session.commit()
        db_session.refresh(employee)
        
        # HR Admin should still get HR response type, but personal_information will be None
        result = filter_employee_response(employee, hr_admin_user, db_session)
        assert isinstance(result, schemas.EmployeeResponseHR)
        assert result.person.personal_information is None

class TestJSONResponseFields:
    """Test specific JSON field presence and absence in responses"""
    
    def test_hr_response_contains_ssn_field(self, db_session, hr_admin_user, test_employee_with_user):
        """Verify HR response JSON contains SSN field"""
        result = filter_employee_response(test_employee_with_user, hr_admin_user, db_session)
        result_dict = result.model_dump()
        
        assert "person" in result_dict
        assert "personal_information" in result_dict["person"]
        assert result_dict["person"]["personal_information"] is not None
        assert "ssn" in result_dict["person"]["personal_information"]
        assert "bank_account" in result_dict["person"]["personal_information"]
    
    def test_basic_response_excludes_personal_information(self, db_session, employee_user, other_employee_with_sensitive_data):
        """Verify Basic response JSON completely excludes personal_information"""
        result = filter_employee_response(other_employee_with_sensitive_data, employee_user, db_session)
        result_dict = result.model_dump()
        
        assert "person" in result_dict
        # personal_information should not exist in Basic response
        assert "personal_information" not in result_dict["person"]