from sqlalchemy.orm import Session, joinedload
from datetime import date, datetime
from . import models, schemas

def create_employee(db: Session, employee: schemas.EmployeeCreate):
    """Create a new employee with person and personal information"""
    
    # Create person record
    db_person = models.People(
        full_name=employee.person.full_name,
        date_of_birth=employee.person.date_of_birth
    )
    db.add(db_person)
    db.flush()  # Get the person ID
    
    # Create personal information if provided
    if employee.personal_information:
        db_personal_info = models.PersonalInformation(
            people_id=db_person.people_id,
            personal_email=employee.personal_information.personal_email,
            ssn=employee.personal_information.ssn,
            bank_account=employee.personal_information.bank_account
        )
        db.add(db_personal_info)
    
    # Create employee record
    db_employee = models.Employee(
        people_id=db_person.people_id,
        work_email=employee.work_email,
        effective_start_date=employee.effective_start_date,
        effective_end_date=employee.effective_end_date
    )
    db.add(db_employee)
    db.commit()
    
    # Query with eager loading of relationships
    return db.query(models.Employee)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )\
        .filter(models.Employee.employee_id == db_employee.employee_id)\
        .first()

def get_employee(db: Session, employee_id: int):
    """Get employee by ID"""
    return db.query(models.Employee)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )\
        .filter(models.Employee.employee_id == employee_id)\
        .first()

def get_employees(db: Session, skip: int = 0, limit: int = 100):
    """Get list of employees"""
    return db.query(models.Employee)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )\
        .offset(skip).limit(limit).all()

def search_employees(db: Session, search_params: schemas.EmployeeSearchParams):
    """Search employees by name, employee ID, or status"""
    query = db.query(models.Employee)\
        .join(models.People)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )
    
    # Filter by name (search in full_name)
    if search_params.name:
        query = query.filter(
            models.People.full_name.ilike(f"%{search_params.name}%")
        )
    
    # Filter by employee ID
    if search_params.employee_id:
        query = query.filter(models.Employee.employee_id == search_params.employee_id)
    
    # Filter by status
    if search_params.status:
        query = query.filter(models.Employee.status == search_params.status)
    
    # Apply pagination
    return query.offset(search_params.skip).limit(search_params.limit).all()

def update_employee(db: Session, employee_id: int, employee_update: schemas.EmployeeUpdate):
    """Update employee information"""
    # Get existing employee
    db_employee = get_employee(db, employee_id)
    if not db_employee:
        return None
    
    # Update employee fields
    if employee_update.work_email is not None:
        db_employee.work_email = employee_update.work_email
    if employee_update.effective_start_date is not None:
        db_employee.effective_start_date = employee_update.effective_start_date
    if employee_update.effective_end_date is not None:
        db_employee.effective_end_date = employee_update.effective_end_date
    if employee_update.status is not None:
        db_employee.status = employee_update.status
    
    # Update person information if provided
    if employee_update.person:
        db_person = db_employee.person
        if employee_update.person.full_name is not None:
            db_person.full_name = employee_update.person.full_name
        if employee_update.person.date_of_birth is not None:
            db_person.date_of_birth = employee_update.person.date_of_birth
    
    # Update personal information if provided
    if employee_update.personal_information:
        # Get or create personal information record
        db_personal_info = db_employee.person.personal_information
        if not db_personal_info:
            # Create new personal information record if it doesn't exist
            db_personal_info = models.PersonalInformation(
                people_id=db_employee.person.people_id
            )
            db.add(db_personal_info)
        
        # Update fields
        if employee_update.personal_information.personal_email is not None:
            db_personal_info.personal_email = employee_update.personal_information.personal_email
        if employee_update.personal_information.ssn is not None:
            db_personal_info.ssn = employee_update.personal_information.ssn
        if employee_update.personal_information.bank_account is not None:
            db_personal_info.bank_account = employee_update.personal_information.bank_account
    
    db.commit()
    
    # Return updated employee with all relationships
    return db.query(models.Employee)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )\
        .filter(models.Employee.employee_id == employee_id)\
        .first()

# Department CRUD operations
def create_department(db: Session, department: schemas.DepartmentCreate):
    """Create a new department with optional assignment types"""
    db_department = models.Department(
        name=department.name,
        description=department.description
    )
    db.add(db_department)
    db.flush()  # Get the department ID
    
    # Create assignment types if provided
    if department.assignment_types:
        for assignment_type_desc in department.assignment_types:
            db_assignment_type = models.AssignmentType(
                description=assignment_type_desc,
                department_id=db_department.department_id
            )
            db.add(db_assignment_type)
    
    db.commit()
    
    # Return with assignment types loaded
    return db.query(models.Department)\
        .options(joinedload(models.Department.assignment_types))\
        .filter(models.Department.department_id == db_department.department_id)\
        .first()

def get_department(db: Session, department_id: int):
    """Get department by ID with assignment types"""
    return db.query(models.Department)\
        .options(joinedload(models.Department.assignment_types))\
        .filter(models.Department.department_id == department_id)\
        .first()

def get_departments(db: Session, skip: int = 0, limit: int = 100):
    """Get list of departments with assignment types"""
    return db.query(models.Department)\
        .options(joinedload(models.Department.assignment_types))\
        .offset(skip).limit(limit).all()

def update_department(db: Session, department_id: int, department: schemas.DepartmentUpdate):
    """Update department with assignment type management"""
    db_department = get_department(db, department_id)
    if not db_department:
        return None
    
    # Update basic department info
    if department.name is not None:
        db_department.name = department.name
    if department.description is not None:
        db_department.description = department.description
    
    # Add new assignment types
    if department.assignment_types_to_add:
        for assignment_type_desc in department.assignment_types_to_add:
            db_assignment_type = models.AssignmentType(
                description=assignment_type_desc,
                department_id=db_department.department_id
            )
            db.add(db_assignment_type)
    
    # Remove assignment types
    if department.assignment_types_to_remove:
        for assignment_type_id in department.assignment_types_to_remove:
            db.query(models.AssignmentType)\
                .filter(
                    models.AssignmentType.assignment_type_id == assignment_type_id,
                    models.AssignmentType.department_id == db_department.department_id
                )\
                .delete()
    
    db.commit()
    
    # Return with updated assignment types
    return db.query(models.Department)\
        .options(joinedload(models.Department.assignment_types))\
        .filter(models.Department.department_id == db_department.department_id)\
        .first()

def delete_department(db: Session, department_id: int):
    """Delete department"""
    db_department = get_department(db, department_id)
    if db_department:
        db.delete(db_department)
        db.commit()
    return db_department

# Assignment Type CRUD operations
def create_assignment_type(db: Session, assignment_type: schemas.AssignmentTypeCreate):
    """Create a new assignment type"""
    db_assignment_type = models.AssignmentType(
        description=assignment_type.description,
        department_id=assignment_type.department_id
    )
    db.add(db_assignment_type)
    db.commit()
    
    # Return with department relationship loaded
    return db.query(models.AssignmentType)\
        .options(joinedload(models.AssignmentType.department))\
        .filter(models.AssignmentType.assignment_type_id == db_assignment_type.assignment_type_id)\
        .first()

def get_assignment_type(db: Session, assignment_type_id: int):
    """Get assignment type by ID"""
    return db.query(models.AssignmentType)\
        .options(joinedload(models.AssignmentType.department))\
        .filter(models.AssignmentType.assignment_type_id == assignment_type_id)\
        .first()

def get_assignment_types(db: Session, department_id: int = None, skip: int = 0, limit: int = 100):
    """Get list of assignment types, optionally filtered by department"""
    query = db.query(models.AssignmentType)\
        .options(joinedload(models.AssignmentType.department))
    
    if department_id:
        query = query.filter(models.AssignmentType.department_id == department_id)
    
    return query.offset(skip).limit(limit).all()

def update_assignment_type(db: Session, assignment_type_id: int, assignment_type: schemas.AssignmentTypeCreate):
    """Update assignment type"""
    db_assignment_type = get_assignment_type(db, assignment_type_id)
    if db_assignment_type:
        db_assignment_type.description = assignment_type.description
        db_assignment_type.department_id = assignment_type.department_id
        db.commit()
        db.refresh(db_assignment_type)
    return db_assignment_type

def delete_assignment_type(db: Session, assignment_type_id: int):
    """Delete assignment type"""
    db_assignment_type = get_assignment_type(db, assignment_type_id)
    if db_assignment_type:
        db.delete(db_assignment_type)
        db.commit()
    return db_assignment_type

# Assignment CRUD operations
def create_assignment(db: Session, assignment: schemas.AssignmentCreate):
    """Create a new assignment with supervisor relationships"""
    # If this is set as primary, unset other primary assignments for this employee
    if assignment.is_primary:
        db.query(models.Assignment)\
            .filter(models.Assignment.employee_id == assignment.employee_id)\
            .update({"is_primary": False})
    
    # Create the assignment
    db_assignment = models.Assignment(
        employee_id=assignment.employee_id,
        assignment_type_id=assignment.assignment_type_id,
        description=assignment.description,
        effective_start_date=assignment.effective_start_date,
        effective_end_date=assignment.effective_end_date,
        is_primary=assignment.is_primary
    )
    db.add(db_assignment)
    db.flush()  # Get the assignment ID
    
    # Add supervisor relationships if provided
    if assignment.supervisor_ids:
        for supervisor_id in assignment.supervisor_ids:
            supervisor_rel = models.AssignmentSupervisor(
                assignment_id=db_assignment.assignment_id,
                supervisor_id=supervisor_id,
                effective_start_date=assignment.effective_start_date or db_assignment.effective_start_date
            )
            db.add(supervisor_rel)
    
    db.commit()
    
    # Return with all relationships loaded
    return db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.employee)\
            .joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information),
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department),
            joinedload(models.Assignment.supervisors)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.Assignment.assignment_id == db_assignment.assignment_id)\
        .first()

def get_assignment(db: Session, assignment_id: int):
    """Get assignment by ID with all relationships"""
    return db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.employee)\
            .joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information),
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department),
            joinedload(models.Assignment.supervisors)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.Assignment.assignment_id == assignment_id)\
        .first()

def get_assignments(db: Session, employee_id: int = None, supervisor_id: int = None, 
                   department_id: int = None, assignment_type_id: int = None, 
                   employee_name: str = None, skip: int = 0, limit: int = 100):
    """Get list of assignments with comprehensive filtering options"""
    query = db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department),
            joinedload(models.Assignment.supervisors)
        )
    
    # Existing filters
    if employee_id:
        query = query.filter(models.Assignment.employee_id == employee_id)
    
    if supervisor_id:
        query = query.join(models.AssignmentSupervisor)\
            .filter(models.AssignmentSupervisor.supervisor_id == supervisor_id)
    
    # New department filter
    if department_id:
        query = query.join(models.AssignmentType)\
            .filter(models.AssignmentType.department_id == department_id)
    
    # New assignment type filter
    if assignment_type_id:
        query = query.filter(models.Assignment.assignment_type_id == assignment_type_id)
    
    # New employee name search filter
    if employee_name:
        query = query.join(models.Employee)\
            .join(models.People)\
            .filter(models.People.full_name.ilike(f"%{employee_name}%"))
    
    return query.offset(skip).limit(limit).all()

def update_assignment(db: Session, assignment_id: int, assignment_update: schemas.AssignmentUpdate):
    """Update assignment information"""
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        return None
    
    # If setting as primary, unset other primary assignments for this employee
    if assignment_update.is_primary is True:
        db.query(models.Assignment)\
            .filter(
                models.Assignment.employee_id == db_assignment.employee_id,
                models.Assignment.assignment_id != assignment_id
            )\
            .update({"is_primary": False})
    
    # Update assignment fields
    if assignment_update.assignment_type_id is not None:
        db_assignment.assignment_type_id = assignment_update.assignment_type_id
    if assignment_update.description is not None:
        db_assignment.description = assignment_update.description
    if assignment_update.effective_start_date is not None:
        db_assignment.effective_start_date = assignment_update.effective_start_date
    if assignment_update.effective_end_date is not None:
        db_assignment.effective_end_date = assignment_update.effective_end_date
    if assignment_update.is_primary is not None:
        db_assignment.is_primary = assignment_update.is_primary
    
    db.commit()
    return get_assignment(db, assignment_id)

def delete_assignment(db: Session, assignment_id: int):
    """Delete assignment and its supervisor relationships"""
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        return None
    
    # Delete supervisor relationships first (foreign key constraint)
    db.query(models.AssignmentSupervisor)\
        .filter(models.AssignmentSupervisor.assignment_id == assignment_id)\
        .delete()
    
    # Delete the assignment
    db.delete(db_assignment)
    db.commit()
    return db_assignment

def get_employee_assignments(db: Session, employee_id: int):
    """Get all assignments for a specific employee"""
    return db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department),
            joinedload(models.Assignment.supervisors)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.Assignment.employee_id == employee_id)\
        .order_by(models.Assignment.is_primary.desc(), models.Assignment.effective_start_date.desc())\
        .all()

def set_primary_assignment(db: Session, assignment_id: int):
    """Set an assignment as primary and unset others for the same employee"""
    db_assignment = get_assignment(db, assignment_id)
    if not db_assignment:
        return None
    
    # Unset all primary assignments for this employee
    db.query(models.Assignment)\
        .filter(models.Assignment.employee_id == db_assignment.employee_id)\
        .update({"is_primary": False})
    
    # Set this assignment as primary
    db_assignment.is_primary = True
    db.commit()
    
    return get_assignment(db, assignment_id)

# Supervisor management functions
def add_supervisor_to_assignment(db: Session, assignment_id: int, supervisor_assignment: schemas.SupervisorAssignmentCreate):
    """Add a supervisor to an assignment"""
    # Check if supervisor relationship already exists
    existing = db.query(models.AssignmentSupervisor)\
        .filter(
            models.AssignmentSupervisor.assignment_id == assignment_id,
            models.AssignmentSupervisor.supervisor_id == supervisor_assignment.supervisor_id
        ).first()
    
    if existing:
        return None  # Supervisor already assigned
    
    supervisor_rel = models.AssignmentSupervisor(
        assignment_id=assignment_id,
        supervisor_id=supervisor_assignment.supervisor_id,
        effective_start_date=supervisor_assignment.effective_start_date,
        effective_end_date=supervisor_assignment.effective_end_date
    )
    db.add(supervisor_rel)
    db.commit()
    
    return get_assignment(db, assignment_id)

def remove_supervisor_from_assignment(db: Session, assignment_id: int, supervisor_id: int):
    """Remove a supervisor from an assignment"""
    deleted_count = db.query(models.AssignmentSupervisor)\
        .filter(
            models.AssignmentSupervisor.assignment_id == assignment_id,
            models.AssignmentSupervisor.supervisor_id == supervisor_id
        ).delete()
    
    db.commit()
    return deleted_count > 0

def get_assignment_supervisors(db: Session, assignment_id: int):
    """Get all supervisors for a specific assignment"""
    return db.query(models.AssignmentSupervisor)\
        .options(
            joinedload(models.AssignmentSupervisor.supervisor)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.AssignmentSupervisor.assignment_id == assignment_id)\
        .all()

def update_assignment_supervisors(db: Session, assignment_id: int, supervisor_ids: list[int]):
    """Update assignment supervisors"""
    # Remove existing supervisor relationships
    db.query(models.AssignmentSupervisor)\
        .filter(models.AssignmentSupervisor.assignment_id == assignment_id)\
        .delete()
    
    # Add new supervisor relationships
    for supervisor_id in supervisor_ids:
        supervisor_rel = models.AssignmentSupervisor(
            assignment_id=assignment_id,
            supervisor_id=supervisor_id,
            effective_start_date=date.today()  # Default to today
        )
        db.add(supervisor_rel)
    
    db.commit()
    return get_assignment(db, assignment_id)

def get_supervisees_for_supervisor(db: Session, supervisor_employee_id: int):
    """Get all employees that the specified supervisor supervises
    
    Args:
        supervisor_employee_id: The employee_id of the supervisor
        
    Returns:
        List of Employee objects that this supervisor supervises
    """
    # Query to get distinct employees supervised by this supervisor
    # through active assignment supervisor relationships
    return db.query(models.Employee)\
        .join(models.Assignment, models.Employee.employee_id == models.Assignment.employee_id)\
        .join(models.AssignmentSupervisor, models.Assignment.assignment_id == models.AssignmentSupervisor.assignment_id)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information),
            joinedload(models.Employee.assignments)\
            .joinedload(models.Assignment.assignment_type)
        )\
        .filter(
            models.AssignmentSupervisor.supervisor_id == supervisor_employee_id,
            models.AssignmentSupervisor.effective_start_date <= date.today(),
            (models.AssignmentSupervisor.effective_end_date.is_(None) | 
             (models.AssignmentSupervisor.effective_end_date > date.today()))
        )\
        .distinct()\
        .all()

def get_employees_for_supervisor_assignment(db: Session, supervisor_employee_id: int, include_self: bool = True):
    """Get employees that a supervisor can assign as supervisors to assignments
    
    This includes:
    - Employees they currently supervise 
    - Themselves (if include_self=True)
    
    Args:
        supervisor_employee_id: The employee_id of the supervisor
        include_self: Whether to include the supervisor themselves in the list
        
    Returns:
        List of Employee objects that can be assigned as supervisors
    """
    # Get employees supervised by this supervisor
    supervisees = get_supervisees_for_supervisor(db, supervisor_employee_id)
    
    # If requested, also include the supervisor themselves
    available_supervisors = list(supervisees)
    
    if include_self:
        supervisor = get_employee(db, supervisor_employee_id)
        if supervisor and supervisor not in available_supervisors:
            available_supervisors.append(supervisor)
    
    return available_supervisors

# Leave Request CRUD functions
def create_leave_request(db: Session, leave_request: schemas.LeaveRequestCreate, employee_id: int):
    """Create a new leave request for an employee"""
    db_leave_request = models.LeaveRequest(
        employee_id=employee_id,
        start_date=leave_request.start_date,
        end_date=leave_request.end_date,
        reason=leave_request.reason,
        status=models.LeaveStatus.PENDING
    )
    db.add(db_leave_request)
    db.commit()
    db.refresh(db_leave_request)
    
    return get_leave_request(db, db_leave_request.leave_id)

def get_leave_request(db: Session, leave_id: int):
    """Get leave request by ID with all relationships"""
    return db.query(models.LeaveRequest)\
        .options(
            joinedload(models.LeaveRequest.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.LeaveRequest.decision_maker)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.LeaveRequest.leave_id == leave_id)\
        .first()

def get_leave_requests(db: Session, skip: int = 0, limit: int = 100):
    """Get all leave requests"""
    return db.query(models.LeaveRequest)\
        .options(
            joinedload(models.LeaveRequest.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.LeaveRequest.decision_maker)\
            .joinedload(models.Employee.person)
        )\
        .order_by(models.LeaveRequest.submitted_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_leave_requests_by_employee(db: Session, employee_id: int):
    """Get all leave requests for a specific employee"""
    return db.query(models.LeaveRequest)\
        .options(
            joinedload(models.LeaveRequest.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.LeaveRequest.decision_maker)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.LeaveRequest.employee_id == employee_id)\
        .order_by(models.LeaveRequest.submitted_at.desc())\
        .all()

def get_leave_requests_for_supervisor(db: Session, supervisor_employee_id: int, status: models.LeaveStatus = None):
    """Get leave requests that require approval from a specific supervisor (PRIMARY ASSIGNMENT ONLY)"""
    # Get employees where this supervisor supervises their PRIMARY assignment
    supervised_employee_ids = db.query(models.Assignment.employee_id)\
        .join(models.AssignmentSupervisor, models.Assignment.assignment_id == models.AssignmentSupervisor.assignment_id)\
        .filter(
            models.AssignmentSupervisor.supervisor_id == supervisor_employee_id,
            models.Assignment.is_primary == True,  # Only primary assignments
            models.AssignmentSupervisor.effective_start_date <= date.today(),
            (models.AssignmentSupervisor.effective_end_date.is_(None) | 
             (models.AssignmentSupervisor.effective_end_date > date.today()))
        )\
        .distinct()\
        .subquery()
    
    # Get leave requests for employees with primary assignment supervision
    query = db.query(models.LeaveRequest)\
        .options(
            joinedload(models.LeaveRequest.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.LeaveRequest.decision_maker)\
            .joinedload(models.Employee.person)
        )\
        .filter(models.LeaveRequest.employee_id.in_(supervised_employee_ids))
    
    if status:
        query = query.filter(models.LeaveRequest.status == status)
    
    return query.order_by(models.LeaveRequest.submitted_at.desc()).all()

def can_supervisor_approve_leave_request(db: Session, leave_id: int, supervisor_employee_id: int) -> bool:
    """Check if a supervisor can approve a specific leave request (primary assignment supervision only)"""
    leave_request = get_leave_request(db, leave_id)
    if not leave_request:
        return False
    
    # Check if supervisor supervises the employee's primary assignment
    primary_assignment = db.query(models.Assignment)\
        .join(models.AssignmentSupervisor)\
        .filter(
            models.Assignment.employee_id == leave_request.employee_id,
            models.Assignment.is_primary == True,
            models.AssignmentSupervisor.supervisor_id == supervisor_employee_id,
            models.AssignmentSupervisor.effective_start_date <= date.today(),
            (models.AssignmentSupervisor.effective_end_date.is_(None) | 
             (models.AssignmentSupervisor.effective_end_date > date.today()))
        ).first()
    
    return primary_assignment is not None

def approve_leave_request(db: Session, leave_id: int, approved_by_employee_id: int, reason: str = None, allow_self_approval: bool = False):
    """Approve a leave request"""
    db_leave_request = get_leave_request(db, leave_id)
    if not db_leave_request:
        raise ValueError("Leave request not found")
    
    if db_leave_request.status != models.LeaveStatus.PENDING:
        raise ValueError("Can only approve pending leave requests")
    
    # Prevent self-approval unless explicitly allowed (for HR admin)
    if not allow_self_approval and db_leave_request.employee_id == approved_by_employee_id:
        raise ValueError("Cannot approve your own leave request")
    
    db_leave_request.status = models.LeaveStatus.APPROVED
    db_leave_request.decision_at = datetime.utcnow()
    db_leave_request.decided_by = approved_by_employee_id
    
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

def reject_leave_request(db: Session, leave_id: int, rejected_by_employee_id: int, reason: str):
    """Reject a leave request"""
    db_leave_request = get_leave_request(db, leave_id)
    if not db_leave_request:
        raise ValueError("Leave request not found")
    
    if db_leave_request.status != models.LeaveStatus.PENDING:
        raise ValueError("Can only reject pending leave requests")
    
    # Prevent self-rejection (unless HR admin, handled in router)
    if db_leave_request.employee_id == rejected_by_employee_id:
        raise ValueError("Cannot reject your own leave request")
    
    if not reason or not reason.strip():
        raise ValueError("Rejection reason is required")
    
    db_leave_request.status = models.LeaveStatus.REJECTED
    db_leave_request.decision_at = datetime.utcnow()
    db_leave_request.decided_by = rejected_by_employee_id
    # Note: We might want to add a reason field to the model in the future
    
    db.commit()
    db.refresh(db_leave_request)
    return db_leave_request

def update_leave_request(db: Session, leave_id: int, leave_update: schemas.LeaveRequestUpdate, updated_by_employee_id: int):
    """Update leave request status and decision information"""
    db_leave_request = get_leave_request(db, leave_id)
    if not db_leave_request:
        return None
    
    db_leave_request.status = leave_update.status
    if leave_update.reason:
        db_leave_request.reason = leave_update.reason
    
    # Set decision information
    db_leave_request.decided_by = updated_by_employee_id
    db_leave_request.decision_at = datetime.utcnow()
    
    db.commit()
    return get_leave_request(db, leave_id)

def get_employee_active_assignments(db: Session, employee_id: int):
    """Get all active assignments for an employee"""
    return db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department)
        )\
        .filter(
            models.Assignment.employee_id == employee_id,
            models.Assignment.effective_start_date <= date.today(),
            (models.Assignment.effective_end_date.is_(None) | 
             (models.Assignment.effective_end_date > date.today()))
        )\
        .order_by(models.Assignment.is_primary.desc())\
        .all()

def get_primary_assignment_supervisors(db: Session, employee_id: int):
    """Get supervisors of an employee's primary assignment"""
    # Find the employee's primary assignment
    primary_assignment = db.query(models.Assignment)\
        .filter(
            models.Assignment.employee_id == employee_id,
            models.Assignment.is_primary == True,
            models.Assignment.effective_start_date <= date.today(),
            (models.Assignment.effective_end_date.is_(None) | 
             (models.Assignment.effective_end_date > date.today()))
        ).first()
    
    if not primary_assignment:
        return []
    
    # Get active supervisors for the primary assignment
    supervisors = db.query(models.Employee)\
        .join(models.AssignmentSupervisor, models.Employee.employee_id == models.AssignmentSupervisor.supervisor_id)\
        .options(
            joinedload(models.Employee.person)\
            .joinedload(models.People.personal_information)
        )\
        .filter(
            models.AssignmentSupervisor.assignment_id == primary_assignment.assignment_id,
            models.AssignmentSupervisor.effective_start_date <= date.today(),
            (models.AssignmentSupervisor.effective_end_date.is_(None) | 
             (models.AssignmentSupervisor.effective_end_date > date.today()))
        ).all()
    
    return supervisors