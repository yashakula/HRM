from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import schemas, crud
from ..auth import get_current_active_user
from ..permission_validation import validate_permission
from ..permission_decorators import require_permission, require_any_permission
from ..database import get_db
from ..models import User

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _filter_assignments_by_permissions(current_user: User, db: Session, assignments: list) -> list:
    """
    Filter assignment list based on user permissions and relationships.
    
    Args:
        current_user: The current authenticated user
        db: Database session
        assignments: List of assignment objects to filter
    
    Returns:
        Filtered list of assignments the user is authorized to see
    """
    # Check if user has permission to see all assignments
    all_result = validate_permission(current_user, "assignment.read.all", db)
    if all_result.granted:
        return assignments
    
    # Get user's employee record for ownership/supervision checks
    from ..auth import get_employee_by_user_id
    user_employee = get_employee_by_user_id(db, current_user.user_id)
    if not user_employee:
        return []  # User has no employee record, cannot see any assignments
    
    filtered_assignments = []
    
    for assignment in assignments:
        # Check if user has permission to read this specific assignment
        own_result = validate_permission(current_user, "assignment.read.own", db, resource_id=assignment.assignment_id)
        supervised_result = validate_permission(current_user, "assignment.read.supervised", db, resource_id=assignment.assignment_id)
        
        if own_result.granted or supervised_result.granted:
            filtered_assignments.append(assignment)
    
    return filtered_assignments

@router.post("/", response_model=schemas.AssignmentResponse)
@require_permission("assignment.create")
def create_assignment(
    assignment: schemas.AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new assignment (HR Admin only) - US-14"""
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
    """Get list of assignments with permission-based filtering - users only see assignments based on their permissions"""
    assignments = crud.get_assignments(
        db=db, 
        employee_id=employee_id, 
        supervisor_id=supervisor_id,
        department_id=department_id,
        assignment_type_id=assignment_type_id,
        employee_name=employee_name,
        skip=skip, 
        limit=limit
    )
    
    # Apply permission-based filtering
    return _filter_assignments_by_permissions(current_user, db, assignments)

@router.get("/{assignment_id}", response_model=schemas.AssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get assignment by ID with permission-based access validation"""
    assignment = crud.get_assignment(db=db, assignment_id=assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if user has permission to access this specific assignment
    all_result = validate_permission(current_user, "assignment.read.all", db, resource_id=assignment_id)
    own_result = validate_permission(current_user, "assignment.read.own", db, resource_id=assignment_id)
    supervised_result = validate_permission(current_user, "assignment.read.supervised", db, resource_id=assignment_id)
    
    if not (all_result.granted or own_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to access assignment {assignment_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["assignment.read.all", "assignment.read.own", "assignment.read.supervised"]
            }
        )
    
    return assignment

@router.put("/{assignment_id}/supervisors")
@require_permission("assignment.manage_supervisors")
def update_assignment_supervisors(
    assignment_id: int,
    supervisor_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
    """Get all assignments for a specific employee with permission-based access control"""
    # Verify employee exists
    employee = crud.get_employee(db=db, employee_id=employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if user has permission to access this employee's assignments
    all_result = validate_permission(current_user, "assignment.read.all", db, resource_id=employee_id)
    own_result = validate_permission(current_user, "assignment.read.own", db, resource_id=employee_id)
    supervised_result = validate_permission(current_user, "assignment.read.supervised", db, resource_id=employee_id)
    
    if not (all_result.granted or own_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to access assignments for employee {employee_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["assignment.read.all", "assignment.read.own", "assignment.read.supervised"]
            }
        )
    
    assignments = crud.get_assignments(db=db, employee_id=employee_id)
    
    # Apply permission-based filtering
    return _filter_assignments_by_permissions(current_user, db, assignments)

@router.get("/supervisor/{supervisor_id}", response_model=List[schemas.AssignmentResponse])
@require_any_permission(["assignment.read.supervised", "assignment.read.all"])
def get_supervisor_assignments(
    supervisor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all assignments supervised by a specific employee with role-based filtering"""
    # Verify supervisor exists
    supervisor = crud.get_employee(db=db, employee_id=supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    
    assignments = crud.get_assignments(db=db, supervisor_id=supervisor_id)
    
    # Apply permission-based filtering
    return _filter_assignments_by_permissions(current_user, db, assignments)

# New endpoints for US-15, US-17

@router.put("/{assignment_id}", response_model=schemas.AssignmentResponse)
@require_permission("assignment.update.all")
def update_assignment(
    assignment_id: int,
    assignment_update: schemas.AssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update assignment information - US-15, US-17"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Validate assignment type if being updated
    if assignment_update.assignment_type_id:
        assignment_type = crud.get_assignment_type(db, assignment_update.assignment_type_id)
        if not assignment_type:
            raise HTTPException(status_code=404, detail="Assignment type not found")
    
    updated_assignment = crud.update_assignment(db, assignment_id, assignment_update)
    if not updated_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return updated_assignment

@router.delete("/{assignment_id}")
@require_permission("assignment.delete")
def delete_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove an assignment - US-17"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    deleted_assignment = crud.delete_assignment(db, assignment_id)
    if not deleted_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"detail": "Assignment deleted successfully"}

@router.put("/{assignment_id}/primary", response_model=schemas.AssignmentResponse)
@require_permission("assignment.update.all")
def set_primary_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set assignment as primary for the employee - US-15"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    updated_assignment = crud.set_primary_assignment(db, assignment_id)
    if not updated_assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return updated_assignment

@router.get("/{assignment_id}/supervisors", response_model=List[schemas.SupervisorAssignmentResponse])
async def get_assignment_supervisors(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all supervisors for an assignment with permission-based access validation - US-14"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if user has permission to access this assignment's supervisors
    all_result = validate_permission(current_user, "assignment.read.all", db, resource_id=assignment_id)
    own_result = validate_permission(current_user, "assignment.read.own", db, resource_id=assignment_id)
    supervised_result = validate_permission(current_user, "assignment.read.supervised", db, resource_id=assignment_id)
    
    if not (all_result.granted or own_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to access supervisors for assignment {assignment_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["assignment.read.all", "assignment.read.own", "assignment.read.supervised"]
            }
        )
    
    return crud.get_assignment_supervisors(db, assignment_id)

@router.post("/{assignment_id}/supervisors", response_model=schemas.AssignmentResponse)
@require_permission("assignment.manage_supervisors")
def add_supervisor_to_assignment(
    assignment_id: int,
    supervisor_assignment: schemas.SupervisorAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Add a supervisor to an assignment - US-14"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Validate supervisor exists
    supervisor = crud.get_employee(db, supervisor_assignment.supervisor_id)
    if not supervisor:
        raise HTTPException(status_code=404, detail="Supervisor not found")
    
    updated_assignment = crud.add_supervisor_to_assignment(db, assignment_id, supervisor_assignment)
    if not updated_assignment:
        raise HTTPException(status_code=400, detail="Supervisor already assigned to this assignment")
    
    return updated_assignment

@router.delete("/{assignment_id}/supervisors/{supervisor_id}")
@require_permission("assignment.manage_supervisors")
def remove_supervisor_from_assignment(
    assignment_id: int,
    supervisor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a supervisor from an assignment - US-14"""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    success = crud.remove_supervisor_from_assignment(db, assignment_id, supervisor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Supervisor assignment not found")
    
    return {"detail": "Supervisor removed from assignment successfully"}