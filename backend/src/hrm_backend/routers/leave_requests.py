from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_active_user, get_employee_by_user_id
from ..permission_decorators import require_permission
from ..permission_validation import validate_permission

router = APIRouter(prefix="/leave-requests", tags=["leave-requests"])

@router.post("/", response_model=schemas.LeaveRequestResponse)
@require_permission("leave_request.create")
def create_leave_request(
    leave_request: schemas.LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Submit a new leave request (US-05) - Permission-based access control"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Verify that the assignment belongs to the current employee
    assignment = crud.get_assignment(db, leave_request.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if user has permission to create leave requests for this assignment
    own_result = validate_permission(current_user, "leave_request.create.own", db, resource_id=assignment.employee_id)
    all_result = validate_permission(current_user, "leave_request.create.all", db, resource_id=assignment.employee_id)
    
    if not (own_result.granted or all_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to create leave request for assignment {leave_request.assignment_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["leave_request.create.own", "leave_request.create.all"]
            }
        )
    
    # Additional validation: ensure assignment belongs to user (for non-admin users)
    if not all_result.granted and assignment.employee_id != employee.employee_id:
        raise HTTPException(
            status_code=403, 
            detail="You can only submit leave requests for your own assignments"
        )
    
    # Validate date range
    if leave_request.start_date > leave_request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
    
    # Create the leave request
    try:
        return crud.create_leave_request(db=db, leave_request=leave_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[schemas.LeaveRequestResponse])
def get_leave_requests(
    status: Optional[models.LeaveStatus] = Query(None, description="Filter by leave request status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get leave requests based on user permissions"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Check permissions to determine what leave requests user can see
    all_result = validate_permission(current_user, "leave_request.read.all", db)
    supervised_result = validate_permission(current_user, "leave_request.read.supervised", db)
    own_result = validate_permission(current_user, "leave_request.read.own", db)
    
    if all_result.granted:
        # User can see all leave requests
        return crud.get_leave_requests(db, skip=skip, limit=limit)
    
    elif supervised_result.granted:
        # User can see requests for their supervisees
        return crud.get_leave_requests_for_supervisor(
            db, 
            supervisor_employee_id=employee.employee_id,
            status=status
        )
    
    elif own_result.granted:
        # User can see only their own requests
        return crud.get_leave_requests_by_employee(db, employee.employee_id)
    
    else:
        # No permission to read leave requests
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to read leave requests",
                "user_role": current_user.role.value,
                "required_permissions": ["leave_request.read.all", "leave_request.read.supervised", "leave_request.read.own"]
            }
        )

@router.get("/my-requests", response_model=List[schemas.LeaveRequestResponse])
@require_permission("leave_request.read.own")
def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get leave requests for the current employee - Permission-based access control"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    return crud.get_leave_requests_by_employee(db, employee.employee_id)

@router.get("/pending-approvals", response_model=List[schemas.LeaveRequestResponse])
def get_pending_approvals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get pending leave requests requiring approval - Permission-based access control"""
    
    # Check if user has permission to view pending approvals
    all_result = validate_permission(current_user, "leave_request.approve.all", db)
    supervised_result = validate_permission(current_user, "leave_request.approve.supervised", db)
    
    if not (all_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to view pending approvals",
                "user_role": current_user.role.value,
                "required_permissions": ["leave_request.approve.all", "leave_request.approve.supervised"]
            }
        )
    
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    if all_result.granted:
        # User can see all pending requests
        all_requests = crud.get_leave_requests(db)
        return [req for req in all_requests if req.status == models.LeaveStatus.PENDING]
    else:
        # User can see pending requests for their supervisees
        return crud.get_leave_requests_for_supervisor(
            db, 
            supervisor_employee_id=employee.employee_id,
            status=models.LeaveStatus.PENDING
        )

@router.get("/{leave_id}", response_model=schemas.LeaveRequestResponse)
def get_leave_request(
    leave_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get a specific leave request - Permission-based access control"""
    
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check if user has permission to access this specific leave request
    all_result = validate_permission(current_user, "leave_request.read.all", db, resource_id=leave_id)
    own_result = validate_permission(current_user, "leave_request.read.own", db, resource_id=leave_request.assignment.employee_id)
    supervised_result = validate_permission(current_user, "leave_request.read.supervised", db, resource_id=leave_request.assignment.employee_id)
    
    if not (all_result.granted or own_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to access leave request {leave_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["leave_request.read.all", "leave_request.read.own", "leave_request.read.supervised"]
            }
        )
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Additional validation for scoped permissions
    if own_result.granted and not all_result.granted:
        # Employee can only see their own requests
        if leave_request.assignment.employee_id != employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view your own leave requests"
            )
    elif supervised_result.granted and not all_result.granted:
        # Check if this supervisor supervises the employee who made the request
        supervisees = crud.get_supervisees_for_supervisor(db, employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if leave_request.assignment.employee_id not in supervisee_ids:
            raise HTTPException(
                status_code=403, 
                detail="You can only view leave requests from your supervisees"
            )
    
    return leave_request

@router.put("/{leave_id}", response_model=schemas.LeaveRequestResponse)
def update_leave_request(
    leave_id: int,
    leave_update: schemas.LeaveRequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Approve or reject a leave request - Permission-based access control"""
    
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check if user has permission to approve/reject leave requests
    all_result = validate_permission(current_user, "leave_request.approve.all", db, resource_id=leave_id)
    supervised_result = validate_permission(current_user, "leave_request.approve.supervised", db, resource_id=leave_id)
    
    if not (all_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to approve/reject leave request {leave_id}",
                "user_role": current_user.role.value,
                "required_permissions": ["leave_request.approve.all", "leave_request.approve.supervised"]
            }
        )
    
    # Only allow updating pending requests
    if leave_request.status != models.LeaveStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail="Can only update pending leave requests"
        )
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Additional validation for supervised permission: ensure supervisor relationship
    if not all_result.granted and supervised_result.granted:
        # Check if this supervisor supervises the employee who made the request
        supervisees = crud.get_supervisees_for_supervisor(db, employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if leave_request.assignment.employee_id not in supervisee_ids:
            raise HTTPException(
                status_code=403, 
                detail="You can only approve/reject leave requests from your supervisees"
            )
    
    # Update the leave request
    try:
        return crud.update_leave_request(
            db=db, 
            leave_id=leave_id, 
            leave_update=leave_update,
            updated_by_employee_id=employee.employee_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/assignments/{employee_id}/active", response_model=List[schemas.AssignmentResponse])
def get_employee_active_assignments(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get active assignments for an employee (for leave request form) - Permission-based access control"""
    
    # Check if user has permission to access assignments for this employee
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
    
    # Get the current user's employee record
    current_employee = get_employee_by_user_id(db, current_user.user_id)
    if not current_employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Additional validation for scoped permissions
    if own_result.granted and not all_result.granted:
        if employee_id != current_employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view your own assignments"
            )
    elif supervised_result.granted and not all_result.granted:
        # Supervisors can see assignments for their supervisees
        supervisees = crud.get_supervisees_for_supervisor(db, current_employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if employee_id not in supervisee_ids and employee_id != current_employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view assignments for your supervisees"
            )
    
    return crud.get_employee_active_assignments(db, employee_id)