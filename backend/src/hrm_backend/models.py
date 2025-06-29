from sqlalchemy import Column, Integer, String, Date, DateTime, Enum, Text, ForeignKey, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import List, Optional

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

class UserRole(PyEnum):
    SUPER_USER = "SUPER_USER"
    HR_ADMIN = "HR_ADMIN"
    SUPERVISOR = "SUPERVISOR" 
    EMPLOYEE = "EMPLOYEE"

class User(Base):
    __tablename__ = "user"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employees = relationship("Employee", back_populates="user")
    user_roles = relationship("UserRoleAssignment", back_populates="user", cascade="all, delete-orphan", foreign_keys="[UserRoleAssignment.user_id]")
    
    @property
    def active_roles(self) -> List['Role']:
        """Get all active roles for the user"""
        return [ur.role for ur in self.user_roles 
                if ur.is_active and ur.is_effective()]
    
    @property
    def role_names(self) -> List[str]:
        """Get list of active role names"""
        return [role.name for role in self.active_roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return role_name in self.role_names
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(self.has_role(role) for role in role_names)
    
    def has_permission(self, permission_name: str) -> bool:
        """
        Multi-role permission checking.
        Returns True if user has permission through any of their active roles.
        """
        # Check through all active roles
        for role in self.active_roles:
            if permission_name in role.permissions:
                return True
        
        return False
    
    def has_any_permission(self, permission_names: list) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(perm) for perm in permission_names)
    
    def has_all_permissions(self, permission_names: list) -> bool:
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(perm) for perm in permission_names)
    
    def get_all_permissions(self) -> list:
        """Get aggregated permissions from all user's active roles"""
        all_permissions = set()
        
        # Collect permissions from all active roles
        for role in self.active_roles:
            all_permissions.update(role.permissions)
        
        return list(all_permissions)

class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = relationship("UserRoleAssignment", back_populates="role", cascade="all, delete-orphan")
    
    @property
    def permissions(self) -> List[str]:
        """Get permissions for this role from registry"""
        from .permission_registry import ROLE_PERMISSIONS
        return ROLE_PERMISSIONS.get(self.name, [])

class UserRoleAssignment(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("user.user_id"), nullable=True)
    is_active = Column(Boolean, default=True)
    effective_start_date = Column(Date, default=date.today)
    effective_end_date = Column(Date, nullable=True)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by], post_update=True)
    
    def is_effective(self, check_date: Optional[date] = None) -> bool:
        """Check if role assignment is currently effective"""
        if check_date is None:
            check_date = date.today()
        
        if not self.is_active:
            return False
        
        if self.effective_start_date and check_date < self.effective_start_date:
            return False
        
        if self.effective_end_date and check_date > self.effective_end_date:
            return False
        
        return True

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
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=True)  # Nullable for non-system users
    status = Column(Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE)
    work_email = Column(String)
    effective_start_date = Column(Date)
    effective_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    person = relationship("People", back_populates="employees")
    user = relationship("User", back_populates="employees")
    assignments = relationship("Assignment", back_populates="employee")
    leave_decisions = relationship("LeaveRequest", foreign_keys="LeaveRequest.decided_by", back_populates="decision_maker")
    supervised_assignments = relationship("Assignment", secondary="assignment_supervisor", back_populates="supervisors")

class Department(Base):
    __tablename__ = "department"
    
    department_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Relationships
    assignment_types = relationship("AssignmentType", back_populates="department", cascade="all, delete-orphan")

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
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("Employee", back_populates="assignments")
    assignment_type = relationship("AssignmentType", back_populates="assignments")
    leave_requests = relationship("LeaveRequest", back_populates="assignment")
    attendance_records = relationship("Attendance", back_populates="assignment")
    compensation_history = relationship("Compensation", back_populates="assignment")
    supervisors = relationship("Employee", secondary="assignment_supervisor", back_populates="supervised_assignments")
    assignment_supervisors = relationship("AssignmentSupervisor", back_populates="assignment")

class AssignmentSupervisor(Base):
    __tablename__ = "assignment_supervisor"
    
    assignment_id = Column(Integer, ForeignKey("assignment.assignment_id"), primary_key=True)
    supervisor_id = Column(Integer, ForeignKey("employee.employee_id"), primary_key=True)
    effective_start_date = Column(Date, nullable=False)
    effective_end_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    assignment = relationship("Assignment", back_populates="assignment_supervisors")
    supervisor = relationship("Employee", foreign_keys=[supervisor_id])

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

class Permission(Base):
    __tablename__ = "permissions"
    
    permission_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    resource_type = Column(String(50), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)
    scope = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_enum = Column(String(20), nullable=False, primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.permission_id"), nullable=False, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    permission = relationship("Permission", back_populates="role_permissions")

