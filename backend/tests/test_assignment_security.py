"""
Test suite for assignment security access controls
Tests Task 1.3: Secure Assignment Data Access implementation
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from sqlalchemy.orm import Session
from src.hrm_backend.models import (
    Base, User, Employee, People, PersonalInformation, UserRole, EmployeeStatus,
    Assignment, AssignmentType, Department, AssignmentSupervisor
)
from src.hrm_backend.auth import (
    check_assignment_ownership, check_assignment_supervisor_relationship,
    filter_assignments_by_role, validate_assignment_access
)
from src.hrm_backend.database import get_db
from fastapi import HTTPException
from unittest.mock import Mock

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_assignment_security.db"
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
def supervisor_user(db_session):
    """Create Supervisor user"""
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
def department(db_session):
    """Create a test department"""
    dept = Department(
        name="Engineering",
        description="Software Development Department"
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept

@pytest.fixture
def assignment_type(db_session, department):
    """Create a test assignment type"""
    assignment_type = AssignmentType(
        description="Software Developer",
        department_id=department.department_id
    )
    db_session.add(assignment_type)
    db_session.commit()
    db_session.refresh(assignment_type)
    return assignment_type

@pytest.fixture
def supervisor_employee_record(db_session, supervisor_user):
    """Create supervisor employee record"""
    person = People(
        full_name="Jane Manager", 
        date_of_birth=date(1980, 3, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=supervisor_user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="jane.manager@company.com",
        effective_start_date=date(2020, 1, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def employee_record(db_session, employee_user):
    """Create employee record linked to employee_user"""
    person = People(
        full_name="John Developer",
        date_of_birth=date(1990, 1, 1)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=employee_user.user_id,
        status=EmployeeStatus.ACTIVE,
        work_email="john.developer@company.com",
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
        full_name="Bob Tester",
        date_of_birth=date(1985, 5, 15)
    )
    db_session.add(person)
    db_session.flush()
    
    employee = Employee(
        people_id=person.people_id,
        user_id=None,  # No user association
        status=EmployeeStatus.ACTIVE,
        work_email="bob.tester@company.com",
        effective_start_date=date(2022, 6, 1)
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee

@pytest.fixture
def employee_assignment(db_session, employee_record, assignment_type):
    """Create assignment for employee_record"""
    assignment = Assignment(
        employee_id=employee_record.employee_id,
        assignment_type_id=assignment_type.assignment_type_id,
        description="Frontend Development",
        effective_start_date=date(2023, 1, 1),
        is_primary=True
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

@pytest.fixture
def other_assignment(db_session, other_employee_record, assignment_type):
    """Create assignment for other_employee_record"""
    assignment = Assignment(
        employee_id=other_employee_record.employee_id,
        assignment_type_id=assignment_type.assignment_type_id,
        description="Backend Development",
        effective_start_date=date(2022, 6, 1),
        is_primary=True
    )
    db_session.add(assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

@pytest.fixture
def supervised_assignment(db_session, other_employee_record, assignment_type, supervisor_employee_record):
    """Create assignment supervised by supervisor_employee_record"""
    assignment = Assignment(
        employee_id=other_employee_record.employee_id,
        assignment_type_id=assignment_type.assignment_type_id,
        description="Supervised Backend Development",
        effective_start_date=date(2022, 6, 1),
        is_primary=False
    )
    db_session.add(assignment)
    db_session.flush()
    
    # Add supervisor relationship
    supervisor_assignment = AssignmentSupervisor(
        assignment_id=assignment.assignment_id,
        supervisor_id=supervisor_employee_record.employee_id,
        effective_start_date=date(2022, 6, 1)
    )
    db_session.add(supervisor_assignment)
    db_session.commit()
    db_session.refresh(assignment)
    return assignment

class TestAssignmentOwnership:
    """Test assignment ownership validation logic"""
    
    def test_employee_owns_their_assignment(self, db_session, employee_user, employee_assignment):
        """Test that employee owns their own assignment"""
        is_owner = check_assignment_ownership(employee_user, employee_assignment.assignment_id, db_session)
        assert is_owner is True
    
    def test_employee_does_not_own_other_assignment(self, db_session, employee_user, other_assignment):
        """Test that employee does not own other employee assignments"""
        is_owner = check_assignment_ownership(employee_user, other_assignment.assignment_id, db_session)
        assert is_owner is False
    
    def test_hr_admin_owns_any_assignment(self, db_session, hr_admin_user, other_assignment):
        """Test that HR Admin has ownership access to any assignment"""
        is_owner = check_assignment_ownership(hr_admin_user, other_assignment.assignment_id, db_session)
        assert is_owner is True

class TestAssignmentSupervisorRelationship:
    """Test assignment supervisor relationship logic"""
    
    def test_supervisor_supervises_assignment(self, db_session, supervisor_user, supervised_assignment):
        """Test that supervisor has access to assignments they supervise"""
        has_access = check_assignment_supervisor_relationship(supervisor_user, supervised_assignment.assignment_id, db_session)
        assert has_access is True
    
    def test_supervisor_does_not_supervise_other_assignment(self, db_session, supervisor_user, employee_assignment):
        """Test that supervisor does not have access to assignments they don't supervise"""
        has_access = check_assignment_supervisor_relationship(supervisor_user, employee_assignment.assignment_id, db_session)
        assert has_access is False
    
    def test_employee_role_cannot_supervise(self, db_session, employee_user, supervised_assignment):
        """Test that employee role cannot have supervisor access"""
        has_access = check_assignment_supervisor_relationship(employee_user, supervised_assignment.assignment_id, db_session)
        assert has_access is False

class TestAssignmentFiltering:
    """Test assignment list filtering by role"""
    
    def test_hr_admin_sees_all_assignments(self, db_session, hr_admin_user, employee_assignment, other_assignment, supervised_assignment):
        """Test that HR Admin sees all assignments"""
        all_assignments = [employee_assignment, other_assignment, supervised_assignment]
        filtered = filter_assignments_by_role(hr_admin_user, db_session, all_assignments)
        assert len(filtered) == 3
        assert employee_assignment in filtered
        assert other_assignment in filtered
        assert supervised_assignment in filtered
    
    def test_employee_sees_only_own_assignments(self, db_session, employee_user, employee_assignment, other_assignment, supervised_assignment):
        """Test that employee only sees their own assignments"""
        all_assignments = [employee_assignment, other_assignment, supervised_assignment]
        filtered = filter_assignments_by_role(employee_user, db_session, all_assignments)
        assert len(filtered) == 1
        assert employee_assignment in filtered
        assert other_assignment not in filtered
        assert supervised_assignment not in filtered
    
    def test_supervisor_sees_own_and_supervised_assignments(self, db_session, supervisor_user, employee_assignment, other_assignment, supervised_assignment):
        """Test that supervisor sees assignments they supervise"""
        all_assignments = [employee_assignment, other_assignment, supervised_assignment]
        filtered = filter_assignments_by_role(supervisor_user, db_session, all_assignments)
        assert len(filtered) == 1
        assert supervised_assignment in filtered
        assert employee_assignment not in filtered
        assert other_assignment not in filtered
    
    def test_user_without_employee_record_sees_nothing(self, db_session, employee_assignment, other_assignment):
        """Test that user without employee record sees no assignments"""
        user_no_employee = User(
            username="no_employee",
            email="no_employee@example.com",
            password_hash="hashed_password",
            role=UserRole.EMPLOYEE,
            is_active=True
        )
        db_session.add(user_no_employee)
        db_session.commit()
        
        all_assignments = [employee_assignment, other_assignment]
        filtered = filter_assignments_by_role(user_no_employee, db_session, all_assignments)
        assert len(filtered) == 0

class TestAssignmentAccessDecorator:
    """Test the assignment access validation decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_allows_hr_admin_access(self, db_session, hr_admin_user, other_assignment):
        """Test that decorator allows HR Admin to access any assignment"""
        
        @validate_assignment_access(allow_supervisor_access=False)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        result = await test_function(
            assignment_id=other_assignment.assignment_id,
            current_user=hr_admin_user,
            db=db_session
        )
        
        assert result == f"Accessed assignment {other_assignment.assignment_id}"
    
    @pytest.mark.asyncio
    async def test_decorator_allows_owner_access(self, db_session, employee_user, employee_assignment):
        """Test that decorator allows employee to access their own assignment"""
        
        @validate_assignment_access(allow_supervisor_access=False)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        result = await test_function(
            assignment_id=employee_assignment.assignment_id,
            current_user=employee_user,
            db=db_session
        )
        
        assert result == f"Accessed assignment {employee_assignment.assignment_id}"
    
    @pytest.mark.asyncio
    async def test_decorator_allows_supervisor_access(self, db_session, supervisor_user, supervised_assignment):
        """Test that decorator allows supervisor to access assignments they supervise"""
        
        @validate_assignment_access(allow_supervisor_access=True)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        result = await test_function(
            assignment_id=supervised_assignment.assignment_id,
            current_user=supervisor_user,
            db=db_session
        )
        
        assert result == f"Accessed assignment {supervised_assignment.assignment_id}"
    
    @pytest.mark.asyncio
    async def test_decorator_blocks_unauthorized_access(self, db_session, employee_user, other_assignment):
        """Test that decorator blocks employee from accessing other assignments"""
        
        @validate_assignment_access(allow_supervisor_access=False)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                assignment_id=other_assignment.assignment_id,
                current_user=employee_user,
                db=db_session
            )
        
        assert exc_info.value.status_code == 403
        assert "Access Denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_decorator_blocks_supervisor_without_permission(self, db_session, supervisor_user, employee_assignment):
        """Test that decorator blocks supervisor from accessing assignments they don't supervise"""
        
        @validate_assignment_access(allow_supervisor_access=True)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                assignment_id=employee_assignment.assignment_id,
                current_user=supervisor_user,
                db=db_session
            )
        
        assert exc_info.value.status_code == 403
        assert "Access Denied" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_decorator_error_response_format(self, db_session, employee_user, other_assignment):
        """Test that decorator returns properly formatted error response"""
        
        @validate_assignment_access(allow_supervisor_access=False)
        async def test_function(assignment_id: int, current_user: User, db: Session):
            return f"Accessed assignment {assignment_id}"
        
        with pytest.raises(HTTPException) as exc_info:
            await test_function(
                assignment_id=other_assignment.assignment_id,
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

class TestEdgeCases:
    """Test edge cases for assignment access control"""
    
    def test_assignment_ownership_with_no_user_employee(self, db_session, other_assignment):
        """Test ownership check when user has no employee record"""
        user_no_employee = User(
            username="no_employee",
            email="no_employee@example.com",
            password_hash="hashed_password",
            role=UserRole.EMPLOYEE,
            is_active=True
        )
        db_session.add(user_no_employee)
        db_session.commit()
        
        is_owner = check_assignment_ownership(user_no_employee, other_assignment.assignment_id, db_session)
        assert is_owner is False
    
    def test_supervisor_relationship_with_no_supervisor_employee(self, db_session, supervised_assignment):
        """Test supervisor check when supervisor user has no employee record"""
        supervisor_no_employee = User(
            username="supervisor_no_employee",
            email="supervisor_no_employee@example.com",
            password_hash="hashed_password",
            role=UserRole.SUPERVISOR,
            is_active=True
        )
        db_session.add(supervisor_no_employee)
        db_session.commit()
        
        has_access = check_assignment_supervisor_relationship(supervisor_no_employee, supervised_assignment.assignment_id, db_session)
        assert has_access is False