from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_active_user, get_employee_by_user_id

router = APIRouter(prefix="/leave-requests", tags=["leave-requests"])

@router.post("/", response_model=schemas.LeaveRequestResponse)
def create_leave_request(
    leave_request: schemas.LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Submit a new leave request (US-05) - Employee only"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Verify that the assignment belongs to the current employee
    assignment = crud.get_assignment(db, leave_request.assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    if assignment.employee_id != employee.employee_id:
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
    """Get leave requests based on user role"""
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    if current_user.role == models.UserRole.HR_ADMIN:
        # HR Admin can see all leave requests
        return crud.get_leave_requests(db, skip=skip, limit=limit)
    
    elif current_user.role == models.UserRole.SUPERVISOR:
        # Supervisors see requests for their supervisees
        return crud.get_leave_requests_for_supervisor(
            db, 
            supervisor_employee_id=employee.employee_id,
            status=status
        )
    
    else:
        # Employees see only their own requests
        return crud.get_leave_requests_by_employee(db, employee.employee_id)

@router.get("/my-requests", response_model=List[schemas.LeaveRequestResponse])
def get_my_leave_requests(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get leave requests for the current employee"""
    
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
    """Get pending leave requests requiring approval from current supervisor"""
    
    if current_user.role not in [models.UserRole.SUPERVISOR, models.UserRole.HR_ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only supervisors and HR admins can view pending approvals"
        )
    
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    if current_user.role == models.UserRole.HR_ADMIN:
        # HR Admin sees all pending requests
        all_requests = crud.get_leave_requests(db)
        return [req for req in all_requests if req.status == models.LeaveStatus.PENDING]
    else:
        # Supervisors see pending requests for their supervisees
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
    """Get a specific leave request"""
    
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Get the employee record for the current user
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Access control: employees can only see their own requests, 
    # supervisors can see requests from their supervisees,
    # HR admin can see all requests
    if current_user.role == models.UserRole.HR_ADMIN:
        # HR Admin can see any request
        pass
    elif current_user.role == models.UserRole.SUPERVISOR:
        # Check if this supervisor supervises the employee who made the request
        supervisees = crud.get_supervisees_for_supervisor(db, employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if leave_request.assignment.employee_id not in supervisee_ids:
            raise HTTPException(
                status_code=403, 
                detail="You can only view leave requests from your supervisees"
            )
    else:
        # Employee can only see their own requests
        if leave_request.assignment.employee_id != employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view your own leave requests"
            )
    
    return leave_request

@router.put("/{leave_id}", response_model=schemas.LeaveRequestResponse)
def update_leave_request(
    leave_id: int,
    leave_update: schemas.LeaveRequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Approve or reject a leave request - Supervisor/HR Admin only"""
    
    if current_user.role not in [models.UserRole.SUPERVISOR, models.UserRole.HR_ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only supervisors and HR admins can approve/reject leave requests"
        )
    
    leave_request = crud.get_leave_request(db, leave_id)
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
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
    
    # Access control: supervisors can only approve requests from their supervisees
    if current_user.role == models.UserRole.SUPERVISOR:
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
    """Get active assignments for an employee (for leave request form)"""
    
    # Get the current user's employee record
    current_employee = get_employee_by_user_id(db, current_user.user_id)
    if not current_employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Access control: employees can only see their own assignments
    if current_user.role == models.UserRole.EMPLOYEE:
        if employee_id != current_employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view your own assignments"
            )
    elif current_user.role == models.UserRole.SUPERVISOR:
        # Supervisors can see assignments for their supervisees
        supervisees = crud.get_supervisees_for_supervisor(db, current_employee.employee_id)
        supervisee_ids = [s.employee_id for s in supervisees]
        
        if employee_id not in supervisee_ids and employee_id != current_employee.employee_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only view assignments for your supervisees"
            )
    # HR Admin can see any employee's assignments (no additional check needed)
    
    return crud.get_employee_active_assignments(db, employee_id)