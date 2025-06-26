from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from .. import crud, models, schemas
from ..database import get_db
from ..auth import require_hr_admin, get_current_active_user, filter_employee_response, validate_employee_access
from ..models import User, EmployeeStatus

router = APIRouter(prefix="/employees", tags=["employees"])

@router.post("/", response_model=schemas.EmployeeResponse)
def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Create a new employee profile (US-01) - HR Admin only"""
    try:
        return crud.create_employee(db=db, employee=employee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search", response_model=List[schemas.EmployeeResponseUnion])
def search_employees(
    name: Optional[str] = Query(None, description="Search by employee name"),
    employee_id: Optional[int] = Query(None, description="Search by employee ID"),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by employee status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]]:
    """Search and view employee records with role-based data filtering"""
    search_params = schemas.EmployeeSearchParams(
        name=name,
        employee_id=employee_id, 
        status=status,
        skip=skip,
        limit=limit
    )
    employees = crud.search_employees(db, search_params)
    
    # Apply role-based filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees

@router.get("/{employee_id}", response_model=schemas.EmployeeResponseUnion)
@validate_employee_access(allow_supervisor_access=True)
async def read_employee(
    employee_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]:
    """Get employee by ID with role-based data filtering and ownership validation"""
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Apply role-based filtering
    return filter_employee_response(db_employee, current_user, db)

@router.get("/", response_model=List[schemas.EmployeeResponseUnion])
def read_employees(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]]:
    """Get list of employees with role-based data filtering"""
    employees = crud.get_employees(db, skip=skip, limit=limit)
    
    # Apply role-based filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees

@router.put("/{employee_id}", response_model=schemas.EmployeeResponse)
@validate_employee_access(allow_supervisor_access=False)
async def update_employee(
    employee_id: int,
    employee_update: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update employee information with ownership validation - HR Admin or employee themselves only"""
    db_employee = crud.update_employee(db=db, employee_id=employee_id, employee_update=employee_update)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee