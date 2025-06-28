from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..auth import get_current_active_user
from ..permission_decorators import require_permission
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/assignment-types", tags=["assignment-types"])

@router.post("/", response_model=schemas.AssignmentTypeResponse)
@require_permission("assignment_type.create")
def create_assignment_type(
    assignment_type: schemas.AssignmentTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new assignment type (HR Admin only)"""
    # Verify department exists
    department = crud.get_department(db=db, department_id=assignment_type.department_id)
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")
    
    return crud.create_assignment_type(db=db, assignment_type=assignment_type)

@router.get("/", response_model=List[schemas.AssignmentTypeResponse])
def list_assignment_types(
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of assignment types, optionally filtered by department (all authenticated users)"""
    return crud.get_assignment_types(db=db, department_id=department_id, skip=skip, limit=limit)

@router.get("/{assignment_type_id}", response_model=schemas.AssignmentTypeResponse)
def get_assignment_type(
    assignment_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assignment type by ID (all authenticated users)"""
    assignment_type = crud.get_assignment_type(db=db, assignment_type_id=assignment_type_id)
    if not assignment_type:
        raise HTTPException(status_code=404, detail="Assignment type not found")
    return assignment_type

@router.put("/{assignment_type_id}", response_model=schemas.AssignmentTypeResponse)
@require_permission("assignment_type.update")
def update_assignment_type(
    assignment_type_id: int,
    assignment_type: schemas.AssignmentTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update assignment type (HR Admin only)"""
    # Verify department exists
    department = crud.get_department(db=db, department_id=assignment_type.department_id)
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")
    
    updated_assignment_type = crud.update_assignment_type(
        db=db, assignment_type_id=assignment_type_id, assignment_type=assignment_type
    )
    if not updated_assignment_type:
        raise HTTPException(status_code=404, detail="Assignment type not found")
    return updated_assignment_type

@router.delete("/{assignment_type_id}")
@require_permission("assignment_type.delete")
def delete_assignment_type(
    assignment_type_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete assignment type (HR Admin only)"""
    assignment_type = crud.delete_assignment_type(db=db, assignment_type_id=assignment_type_id)
    if not assignment_type:
        raise HTTPException(status_code=404, detail="Assignment type not found")
    return {"message": "Assignment type deleted successfully"}