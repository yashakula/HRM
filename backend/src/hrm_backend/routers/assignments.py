from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..auth import get_current_active_user, require_hr_admin, require_supervisor_or_admin
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/assignments", tags=["assignments"])

@router.post("/", response_model=schemas.AssignmentResponse)
def create_assignment(
    assignment: schemas.AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Create a new assignment (HR Admin only)"""
    # Verify employee exists
    employee = crud.get_employee(db=db, employee_id=assignment.employee_id)
    if not employee:
        raise HTTPException(status_code=400, detail="Employee not found")
    
    # Verify assignment type exists
    assignment_type = crud.get_assignment_type(db=db, assignment_type_id=assignment.assignment_type_id)
    if not assignment_type:
        raise HTTPException(status_code=400, detail="Assignment type not found")
    
    # Verify all supervisors exist
    if assignment.supervisor_ids:
        for supervisor_id in assignment.supervisor_ids:
            supervisor = crud.get_employee(db=db, employee_id=supervisor_id)
            if not supervisor:
                raise HTTPException(status_code=400, detail=f"Supervisor with ID {supervisor_id} not found")
    
    return crud.create_assignment(db=db, assignment=assignment)

@router.get("/", response_model=List[schemas.AssignmentResponse])
def list_assignments(
    employee_id: Optional[int] = Query(None, description="Filter by employee ID"),
    supervisor_id: Optional[int] = Query(None, description="Filter by supervisor ID"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    assignment_type_id: Optional[int] = Query(None, description="Filter by assignment type ID"),
    employee_name: Optional[str] = Query(None, description="Search by employee name"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of assignments with comprehensive filtering options (all authenticated users)"""
    return crud.get_assignments(
        db=db, 
        employee_id=employee_id, 
        supervisor_id=supervisor_id,
        department_id=department_id,
        assignment_type_id=assignment_type_id,
        employee_name=employee_name,
        skip=skip, 
        limit=limit
    )

@router.get("/{assignment_id}", response_model=schemas.AssignmentResponse)
def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assignment by ID (all authenticated users)"""
    assignment = crud.get_assignment(db=db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment

@router.put("/{assignment_id}/supervisors")
def update_assignment_supervisors(
    assignment_id: int,
    supervisor_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Update assignment supervisors (HR Admin only)"""
    # Verify assignment exists
    assignment = crud.get_assignment(db=db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Verify all supervisors exist
    for supervisor_id in supervisor_ids:
        supervisor = crud.get_employee(db=db, employee_id=supervisor_id)
        if not supervisor:
            raise HTTPException(status_code=400, detail=f"Supervisor with ID {supervisor_id} not found")
    
    updated_assignment = crud.update_assignment_supervisors(
        db=db, assignment_id=assignment_id, supervisor_ids=supervisor_ids
    )
    return {"message": "Assignment supervisors updated successfully", "assignment": updated_assignment}

@router.get("/employee/{employee_id}", response_model=List[schemas.AssignmentResponse])
def get_employee_assignments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all assignments for a specific employee"""
    # Verify employee exists
    employee = crud.get_employee(db=db, employee_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return crud.get_assignments(db=db, employee_id=employee_id)

@router.get("/supervisor/{supervisor_id}", response_model=List[schemas.AssignmentResponse])
def get_supervisor_assignments(
    supervisor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_admin())
):
    """Get all assignments supervised by a specific employee (Supervisor or HR Admin only)"""
    # Verify supervisor exists
    supervisor = crud.get_employee(db=db, employee_id=supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    
    return crud.get_assignments(db=db, supervisor_id=supervisor_id)