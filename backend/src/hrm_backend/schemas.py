from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, Union, List
from .models import EmployeeStatus, LeaveStatus

class PersonCreate(BaseModel):
    full_name: str
    date_of_birth: Optional[date] = None

class PersonalInformationCreate(BaseModel):
    personal_email: Optional[str] = None
    ssn: Optional[str] = None
    bank_account: Optional[str] = None

class EmployeeCreate(BaseModel):
    person: PersonCreate
    personal_information: Optional[PersonalInformationCreate] = None
    work_email: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None

class PersonUpdate(BaseModel):
    full_name: Optional[str] = None
    date_of_birth: Optional[date] = None

class PersonalInformationUpdate(BaseModel):
    personal_email: Optional[str] = None
    ssn: Optional[str] = None
    bank_account: Optional[str] = None

class EmployeeUpdate(BaseModel):
    person: Optional[PersonUpdate] = None
    personal_information: Optional[PersonalInformationUpdate] = None
    work_email: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    status: Optional[EmployeeStatus] = None

class PersonResponse(BaseModel):
    people_id: int
    full_name: str
    date_of_birth: Optional[date]
    created_at: datetime
    updated_at: datetime
    personal_information: Optional["PersonalInformationResponse"] = None

    class Config:
        from_attributes = True

class PersonalInformationResponse(BaseModel):
    personal_email: Optional[str]
    ssn: Optional[str]
    bank_account: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmployeeResponse(BaseModel):
    employee_id: int
    people_id: int
    status: EmployeeStatus
    work_email: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    person: PersonResponse

    class Config:
        from_attributes = True

# Role-based response schemas for security filtering
class PersonalInformationResponseHR(BaseModel):
    """Full personal information response for HR Admin users"""
    personal_email: Optional[str]
    ssn: Optional[str]
    bank_account: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonalInformationResponseOwner(BaseModel):
    """Personal information response for employee viewing their own record"""
    personal_email: Optional[str]
    ssn: Optional[str]
    bank_account: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PersonResponseHR(BaseModel):
    """Full person response for HR Admin users including all personal information"""
    people_id: int
    full_name: str
    date_of_birth: Optional[date]
    created_at: datetime
    updated_at: datetime
    personal_information: Optional[PersonalInformationResponseHR] = None

    class Config:
        from_attributes = True

class PersonResponseOwner(BaseModel):
    """Person response for employees viewing their own record including sensitive fields"""
    people_id: int
    full_name: str
    date_of_birth: Optional[date]
    created_at: datetime
    updated_at: datetime
    personal_information: Optional[PersonalInformationResponseOwner] = None

    class Config:
        from_attributes = True

class PersonResponseBasic(BaseModel):
    """Basic person response excluding personal_information relationship"""
    people_id: int
    full_name: str
    date_of_birth: Optional[date]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EmployeeResponseHR(BaseModel):
    """Full employee response for HR Admin users with complete personal information"""
    employee_id: int
    people_id: int
    status: EmployeeStatus
    work_email: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    person: PersonResponseHR

    class Config:
        from_attributes = True

class EmployeeResponseOwner(BaseModel):
    """Employee response for employees viewing their own record with sensitive data"""
    employee_id: int
    people_id: int
    status: EmployeeStatus
    work_email: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    person: PersonResponseOwner

    class Config:
        from_attributes = True

class EmployeeResponseBasic(BaseModel):
    """Basic employee response excluding sensitive personal information"""
    employee_id: int
    people_id: int
    status: EmployeeStatus
    work_email: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    person: PersonResponseBasic

    class Config:
        from_attributes = True

# Union type for endpoint return annotations
EmployeeResponseUnion = Union[EmployeeResponseHR, EmployeeResponseOwner, EmployeeResponseBasic]

# Authentication schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    roles: List[str] = []  # Active role names from multi-role system
    permissions: List[str] = []  # Aggregated permissions from all roles
    is_active: bool
    created_at: datetime
    employee: Optional["EmployeeResponse"] = None  # Associated employee if exists

    class Config:
        from_attributes = True

# Multi-role schemas
class RoleResponse(BaseModel):
    role_id: int
    name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserRoleAssignmentResponse(BaseModel):
    user_id: int
    role_id: int
    assigned_at: datetime
    assigned_by: Optional[int]
    is_active: bool
    effective_start_date: date
    effective_end_date: Optional[date]
    notes: Optional[str]
    role: RoleResponse

    class Config:
        from_attributes = True

class UserRoleAssignmentCreate(BaseModel):
    role_name: str
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    notes: Optional[str] = None

class UserWithRolesResponse(BaseModel):
    user_id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    role_assignments: List[UserRoleAssignmentResponse]
    aggregated_permissions: List[str]
    employee: Optional["EmployeeResponse"] = None

    class Config:
        from_attributes = True

# Search schemas
class EmployeeSearchParams(BaseModel):
    name: Optional[str] = None
    employee_id: Optional[int] = None
    status: Optional[EmployeeStatus] = None
    skip: int = 0
    limit: int = 100

# Department schemas
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assignment_types: Optional[list[str]] = []  # List of assignment type descriptions to create

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    assignment_types_to_add: Optional[list[str]] = []  # Assignment type descriptions to add
    assignment_types_to_remove: Optional[list[int]] = []  # Assignment type IDs to remove

# Assignment Type schemas
class AssignmentTypeCreate(BaseModel):
    description: str
    department_id: int

class AssignmentTypeResponse(BaseModel):
    assignment_type_id: int
    description: str
    department_id: int
    created_at: datetime
    updated_at: datetime
    department: "DepartmentResponse"

    class Config:
        from_attributes = True

class AssignmentTypeSimple(BaseModel):
    assignment_type_id: int
    description: str
    department_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class DepartmentResponse(BaseModel):
    department_id: int
    name: str
    description: Optional[str]
    assignment_types: list[AssignmentTypeSimple] = []

    class Config:
        from_attributes = True

# Assignment schemas
class AssignmentCreate(BaseModel):
    employee_id: int
    assignment_type_id: int
    description: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_primary: Optional[bool] = False
    supervisor_ids: Optional[list[int]] = []

class AssignmentUpdate(BaseModel):
    assignment_type_id: Optional[int] = None
    description: Optional[str] = None
    effective_start_date: Optional[date] = None
    effective_end_date: Optional[date] = None
    is_primary: Optional[bool] = None

class AssignmentResponse(BaseModel):
    assignment_id: int
    employee_id: int
    assignment_type_id: int
    description: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    employee: EmployeeResponse
    assignment_type: AssignmentTypeResponse
    supervisors: list[EmployeeResponse]

    class Config:
        from_attributes = True

class AssignmentSimple(BaseModel):
    assignment_id: int
    employee_id: int
    assignment_type_id: int
    description: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    assignment_type: AssignmentTypeResponse

    class Config:
        from_attributes = True

# Supervisor management schemas
class SupervisorAssignmentCreate(BaseModel):
    supervisor_id: int
    effective_start_date: date
    effective_end_date: Optional[date] = None

class SupervisorAssignmentResponse(BaseModel):
    assignment_id: int
    supervisor_id: int
    effective_start_date: date
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    supervisor: EmployeeResponse

    class Config:
        from_attributes = True

# Leave Request schemas
class LeaveRequestCreate(BaseModel):
    start_date: date
    end_date: date
    reason: Optional[str] = None

class LeaveRequestUpdate(BaseModel):
    status: LeaveStatus
    reason: Optional[str] = None  # Allow supervisor to add notes

class LeaveRequestApprove(BaseModel):
    reason: Optional[str] = None  # Optional approval comment

class LeaveRequestReject(BaseModel):
    reason: str  # Required rejection reason

class LeaveRequestResponse(BaseModel):
    leave_id: int
    employee_id: int
    start_date: date
    end_date: date
    reason: Optional[str]
    status: LeaveStatus
    submitted_at: datetime
    decision_at: Optional[datetime]
    decided_by: Optional[int]
    employee: "EmployeeResponse"
    decision_maker: Optional["EmployeeResponse"] = None

    class Config:
        from_attributes = True

# Page access validation schemas
class PageAccessRequest(BaseModel):
    page_identifier: str
    resource_id: Optional[int] = None  # For resource-specific pages like employee/123

class PageAccessPermissions(BaseModel):
    can_view: bool
    can_edit: bool
    can_create: bool
    can_delete: bool
    message: str
    user_role: str
    required_permissions: List[str]

class PageAccessResponse(BaseModel):
    page_identifier: str
    resource_id: Optional[int]
    permissions: PageAccessPermissions
    access_granted: bool