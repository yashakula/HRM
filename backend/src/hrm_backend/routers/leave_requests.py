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
def create_leave_request(
    leave_request: schemas.LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Submit a new leave request (US-05) - User/Person-based leave requests"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Check if user has permission to create leave requests
    from ..permission_validation import validate_permission
    own_result = validate_permission(current_user, "leave_request.create.own", db, resource_id=employee.employee_id)
    all_result = validate_permission(current_user, "leave_request.create.all", db, resource_id=employee.employee_id)
    
    if not (own_result.granted or all_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to create leave request",
                "user_role": current_user.role_names,
                "required_permissions": ["leave_request.create.own", "leave_request.create.all"]
            }
        )
    
    # Validate date range
    if leave_request.start_date > leave_request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
    
    # Create the leave request for the employee
    try:
        return crud.create_leave_request(db=db, leave_request=leave_request, employee_id=employee.employee_id)
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
                "user_role": current_user.role_names,
                "required_permissions": ["leave_request.read.all", "leave_request.read.supervised", "leave_request.read.own"]
            }
        )

@router.get("/my-requests", response_model=List[schemas.LeaveRequestResponse])
def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get leave requests for the current employee - Permission-based access control"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Check permission with the employee's ID as the resource
    from ..permission_validation import validate_permission
    permission_result = validate_permission(
        current_user, 
        "leave_request.read.own", 
        db, 
        resource_id=employee.employee_id
    )
    
    if not permission_result.granted:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to read leave requests",
                "user_role": current_user.role_names,
                "required_permissions": ["leave_request.read.own"]
            }
        )
    
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
                "user_role": current_user.role_names,
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
        # User can see pending requests for employees whose PRIMARY assignment they supervise
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
                "user_role": current_user.role_names,
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
        if leave_request.employee_id != employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view your own leave requests"
            )
    elif supervised_result.granted and not all_result.granted:
        # Check if this supervisor supervises the employee who made the request
        supervisees = crud.get_supervisees_for_supervisor(db, employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if leave_request.employee_id not in supervisee_ids:
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
                "user_role": current_user.role_names,
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
        
        if leave_request.employee_id not in supervisee_ids:
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

@router.put("/{leave_id}/approve", response_model=schemas.LeaveRequestResponse)
def approve_leave_request(
    leave_id: int,
    approval_data: schemas.LeaveRequestApprove,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Approve a leave request (US-06) - Primary assignment supervisor approval"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Get the leave request
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    from ..permission_validation import validate_permission
    all_result = validate_permission(current_user, "leave_request.approve.all", db, resource_id=leave_id)
    supervised_result = validate_permission(current_user, "leave_request.approve.supervised", db, resource_id=leave_id)
    
    if not (all_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to approve leave requests",
                "user_role": current_user.role_names,
                "required_permissions": ["leave_request.approve.all", "leave_request.approve.supervised"]
            }
        )
    
    # For supervised approval, ensure primary assignment supervision
    if not all_result.granted and supervised_result.granted:
        can_approve = crud.can_supervisor_approve_leave_request(db, leave_id, employee.employee_id)
        if not can_approve:
            raise HTTPException(
                status_code=403,
                detail="You can only approve leave requests from employees whose primary assignment you supervise"
            )
    
    # HR Admin can approve their own requests, supervisors cannot
    if not all_result.granted and leave_request.employee_id == employee.employee_id:
        raise HTTPException(
            status_code=403,
            detail="Supervisors cannot approve their own leave requests. Contact HR for approval."
        )
    
    # Approve the leave request
    try:
        return crud.approve_leave_request(
            db=db,
            leave_id=leave_id,
            approved_by_employee_id=employee.employee_id,
            reason=approval_data.reason,
            allow_self_approval=all_result.granted  # HR_ADMIN can approve their own requests
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving leave request: {str(e)}")

@router.put("/{leave_id}/reject", response_model=schemas.LeaveRequestResponse)
def reject_leave_request(
    leave_id: int,
    rejection_data: schemas.LeaveRequestReject,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Reject a leave request (US-06) - Primary assignment supervisor rejection"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Get the leave request
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    from ..permission_validation import validate_permission
    all_result = validate_permission(current_user, "leave_request.approve.all", db, resource_id=leave_id)
    supervised_result = validate_permission(current_user, "leave_request.approve.supervised", db, resource_id=leave_id)
    
    if not (all_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": "Insufficient permissions to reject leave requests",
                "user_role": current_user.role_names,
                "required_permissions": ["leave_request.approve.all", "leave_request.approve.supervised"]
            }
        )
    
    # For supervised approval, ensure primary assignment supervision
    if not all_result.granted and supervised_result.granted:
        can_approve = crud.can_supervisor_approve_leave_request(db, leave_id, employee.employee_id)
        if not can_approve:
            raise HTTPException(
                status_code=403,
                detail="You can only reject leave requests from employees whose primary assignment you supervise"
            )
    
    # HR Admin can reject their own requests, supervisors cannot
    if not all_result.granted and leave_request.employee_id == employee.employee_id:
        raise HTTPException(
            status_code=403,
            detail="Supervisors cannot reject their own leave requests. Contact HR for decision."
        )
    
    # Reject the leave request
    try:
        return crud.reject_leave_request(
            db=db,
            leave_id=leave_id,
            rejected_by_employee_id=employee.employee_id,
            reason=rejection_data.reason
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rejecting leave request: {str(e)}")

