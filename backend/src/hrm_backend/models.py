from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

Base = declarative_base()

class EmployeeStatus(PyEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"

class LeaveStatus(PyEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class PayType(PyEnum):
    HOURLY = "HOURLY"
    SALARY = "SALARY"
    CONTRACT = "CONTRACT"

class People(Base):
    __tablename__ = "people"
    
    people_id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    date_of_birth = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    personal_information = relationship("PersonalInformation", back_populates="person", uselist=False)
    employees = relationship("Employee", back_populates="person")

class PersonalInformation(Base):
    __tablename__ = "personal_information"
    
    people_id = Column(Integer, ForeignKey("people.people_id"), primary_key=True)
    personal_email = Column(String)
    ssn = Column(String)
    bank_account = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = relationship("People", back_populates="personal_information")

class Employee(Base):
    __tablename__ = "employee"
    
    employee_id = Column(Integer, primary_key=True, index=True)
    people_id = Column(Integer, ForeignKey("people.people_id"), nullable=False)
    status = Column(Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    work_email = Column(String)
    effective_start_date = Column(Date)
    effective_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = relationship("People", back_populates="employees")
    assignments = relationship("Assignment", back_populates="employee")
    leave_decisions = relationship("LeaveRequest", foreign_keys="LeaveRequest.decided_by", back_populates="decision_maker")

class Department(Base):
    __tablename__ = "department"
    
    department_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationships
    assignment_types = relationship("AssignmentType", back_populates="department")

class AssignmentType(Base):
    __tablename__ = "assignment_type"
    
    assignment_type_id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("department.department_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    department = relationship("Department", back_populates="assignment_types")
    assignments = relationship("Assignment", back_populates="assignment_type")

class Assignment(Base):
    __tablename__ = "assignment"
    
    assignment_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee.employee_id"), nullable=False)
    assignment_type_id = Column(Integer, ForeignKey("assignment_type.assignment_type_id"), nullable=False)
    description = Column(String)
    effective_start_date = Column(Date)
    effective_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="assignments")
    assignment_type = relationship("AssignmentType", back_populates="assignments")
    leave_requests = relationship("LeaveRequest", back_populates="assignment")
    attendance_records = relationship("Attendance", back_populates="assignment")
    compensation_history = relationship("Compensation", back_populates="assignment")

class LeaveRequest(Base):
    __tablename__ = "leave_request"
    
    leave_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignment.assignment_id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    submitted_at = Column(DateTime, default=datetime.utcnow)
    decision_at = Column(DateTime)
    decided_by = Column(Integer, ForeignKey("employee.employee_id"))
    
    # Relationships
    assignment = relationship("Assignment", back_populates="leave_requests")
    decision_maker = relationship("Employee", foreign_keys=[decided_by], back_populates="leave_decisions")

class Attendance(Base):
    __tablename__ = "attendance"
    
    attendance_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignment.assignment_id"), nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    total_hours = Column(Numeric(precision=5, scale=2))
    
    # Relationships
    assignment = relationship("Assignment", back_populates="attendance_records")

class PayTypeModel(Base):
    __tablename__ = "pay_type"
    
    pay_type_id = Column(Integer, primary_key=True, index=True)
    code = Column(Enum(PayType), nullable=False)
    description = Column(String)
    
    # Relationships
    compensation_records = relationship("Compensation", back_populates="pay_type")

class Compensation(Base):
    __tablename__ = "compensation"
    
    compensation_id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignment.assignment_id"), nullable=False)
    pay_type_id = Column(Integer, ForeignKey("pay_type.pay_type_id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2))
    effective_start_date = Column(Date)
    effective_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="compensation_history")
    pay_type = relationship("PayTypeModel", back_populates="compensation_records")