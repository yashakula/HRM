from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import require_hr_admin, get_current_active_user
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

@router.get("/search", response_model=List[schemas.EmployeeResponse])
def search_employees(
    name: Optional[str] = Query(None, description="Search by employee name"),
    employee_id: Optional[int] = Query(None, description="Search by employee ID"),
    status: Optional[EmployeeStatus] = Query(None, description="Filter by employee status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Search and view employee records (US-02) - All authenticated users can search"""
    search_params = schemas.EmployeeSearchParams(
        name=name,
        employee_id=employee_id, 
        status=status,
        skip=skip,
        limit=limit
    )
    employees = crud.search_employees(db, search_params)
    return employees

@router.get("/{employee_id}", response_model=schemas.EmployeeResponse)
def read_employee(
    employee_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get employee by ID - All authenticated users can view"""
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee

@router.get("/", response_model=List[schemas.EmployeeResponse])
def read_employees(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of employees - All authenticated users can view"""
    employees = crud.get_employees(db, skip=skip, limit=limit)
    return employees

@router.put("/{employee_id}", response_model=schemas.EmployeeResponse)
def update_employee(
    employee_id: int,
    employee_update: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Update employee information (US-03) - HR Admin only"""
    db_employee = crud.update_employee(db=db, employee_id=employee_id, employee_update=employee_update)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee