from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from .models import EmployeeStatus

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