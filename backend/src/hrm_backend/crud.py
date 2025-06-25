from sqlalchemy.orm import Session, joinedload
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
    # Create the assignment
    db_assignment = models.Assignment(
        employee_id=assignment.employee_id,
        assignment_type_id=assignment.assignment_type_id,
        description=assignment.description,
        effective_start_date=assignment.effective_start_date,
        effective_end_date=assignment.effective_end_date
    )
    db.add(db_assignment)
    db.flush()  # Get the assignment ID
    
    # Add supervisor relationships if provided
    if assignment.supervisor_ids:
        for supervisor_id in assignment.supervisor_ids:
            supervisor_rel = models.AssignmentSupervisor(
                assignment_id=db_assignment.assignment_id,
                supervisor_id=supervisor_id
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

def get_assignments(db: Session, employee_id: int = None, supervisor_id: int = None, skip: int = 0, limit: int = 100):
    """Get list of assignments, optionally filtered by employee or supervisor"""
    query = db.query(models.Assignment)\
        .options(
            joinedload(models.Assignment.employee)\
            .joinedload(models.Employee.person),
            joinedload(models.Assignment.assignment_type)\
            .joinedload(models.AssignmentType.department),
            joinedload(models.Assignment.supervisors)
        )
    
    if employee_id:
        query = query.filter(models.Assignment.employee_id == employee_id)
    
    if supervisor_id:
        query = query.join(models.AssignmentSupervisor)\
            .filter(models.AssignmentSupervisor.supervisor_id == supervisor_id)
    
    return query.offset(skip).limit(limit).all()

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
            supervisor_id=supervisor_id
        )
        db.add(supervisor_rel)
    
    db.commit()
    return get_assignment(db, assignment_id)