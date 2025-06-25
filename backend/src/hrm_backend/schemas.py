from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .models import EmployeeStatus, UserRole

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

# Authentication schemas
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

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
    supervisor_ids: Optional[list[int]] = []

class AssignmentResponse(BaseModel):
    assignment_id: int
    employee_id: int
    assignment_type_id: int
    description: Optional[str]
    effective_start_date: Optional[date]
    effective_end_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    employee: EmployeeResponse
    assignment_type: AssignmentTypeResponse
    supervisors: list[EmployeeResponse]

    class Config:
        from_attributes = True