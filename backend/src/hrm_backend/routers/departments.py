from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, crud
from ..auth import get_current_active_user, require_hr_admin
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/departments", tags=["departments"])

@router.post("/", response_model=schemas.DepartmentResponse)
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Create a new department (HR Admin only)"""
    return crud.create_department(db=db, department=department)

@router.get("/", response_model=List[schemas.DepartmentResponse])
def list_departments(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get list of departments (all authenticated users)"""
    return crud.get_departments(db=db, skip=skip, limit=limit)

@router.get("/{department_id}", response_model=schemas.DepartmentResponse)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get department by ID (all authenticated users)"""
    department = crud.get_department(db=db, department_id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return department

@router.put("/{department_id}", response_model=schemas.DepartmentResponse)
def update_department(
    department_id: int,
    department: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Update department (HR Admin only)"""
    updated_department = crud.update_department(db=db, department_id=department_id, department=department)
    if not updated_department:
        raise HTTPException(status_code=404, detail="Department not found")
    return updated_department

@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_hr_admin())
):
    """Delete department (HR Admin only)"""
    department = crud.delete_department(db=db, department_id=department_id)
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")
    return {"message": "Department deleted successfully"}