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
    return db.query(models.Employee).offset(skip).limit(limit).all()