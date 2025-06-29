from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from .. import crud, models, schemas
from ..database import get_db
from ..auth import get_current_active_user, get_employee_by_user_id
from ..permission_decorators import require_permission
from ..permission_validation import validate_permission
from ..response_filtering import filter_employee_response_by_permissions
from ..models import User, EmployeeStatus

router = APIRouter(prefix="/employees", tags=["employees"])

@router.post("/", response_model=schemas.EmployeeResponse)
@require_permission("employee.create")
def create_employee(
    employee: schemas.EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new employee profile (US-01) - HR Admin only"""
    try:
        return crud.create_employee(db=db, employee=employee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def _get_permission_filtered_employees(
    db: Session, 
    current_user: User, 
    search_params: Optional[schemas.EmployeeSearchParams] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get employees filtered by user permissions - replace role-based filtering"""
    
    # Check if user has permission to read all employees
    all_permission = validate_permission(current_user, "employee.read.all", db)
    if all_permission.granted:
        if search_params:
            employees = crud.search_employees(db, search_params)
        else:
            employees = crud.get_employees(db, skip=skip, limit=limit)
        return employees
    
    # Check if user has permission to read supervised employees
    supervised_permission = validate_permission(current_user, "employee.read.supervised", db)
    if supervised_permission.granted:
        supervisor_employee = get_employee_by_user_id(db, current_user.user_id)
        if not supervisor_employee:
            return []
        
        # Get employees that this supervisor can see (supervisees + self)
        employees = crud.get_employees_for_supervisor_assignment(
            db, 
            supervisor_employee.employee_id, 
            include_self=True
        )
        
        # Apply search filtering if provided
        if search_params:
            filtered_employees = []
            for employee in employees:
                # Check name filter
                if search_params.name and search_params.name.lower() not in employee.person.full_name.lower():
                    continue
                # Check employee ID filter
                if search_params.employee_id and employee.employee_id != search_params.employee_id:
                    continue
                # Check status filter
                if search_params.status and employee.status != search_params.status:
                    continue
                filtered_employees.append(employee)
            
            # Apply pagination
            start_idx = search_params.skip if search_params.skip else 0
            end_idx = start_idx + (search_params.limit if search_params.limit else 100)
            employees = filtered_employees[start_idx:end_idx]
        else:
            # Apply pagination for non-search requests
            employees = employees[skip:skip + limit]
        return employees
    
    # Check if user has permission to read own employee record
    own_permission = validate_permission(current_user, "employee.read.own", db)
    if own_permission.granted:
        user_employee = get_employee_by_user_id(db, current_user.user_id)
        if user_employee:
            employees = [user_employee]
            
            # Apply search filtering even for single employee result
            if search_params:
                # Check if their own record matches the search criteria
                if search_params.name and search_params.name.lower() not in user_employee.person.full_name.lower():
                    employees = []
                elif search_params.employee_id and user_employee.employee_id != search_params.employee_id:
                    employees = []
                elif search_params.status and user_employee.status != search_params.status:
                    employees = []
                # Skip pagination for single result
            return employees
        else:
            return []
    
    # No permission to read any employees
    return []

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
    """Search and view employee records with role-based data filtering and access control"""
    search_params = schemas.EmployeeSearchParams(
        name=name,
        employee_id=employee_id, 
        status=status,
        skip=skip,
        limit=limit
    )
    
    # Get permission-filtered employees
    employees = _get_permission_filtered_employees(db, current_user, search_params)
    
    # Apply permission-based data filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response_by_permissions(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees


@router.get("/supervisees", response_model=List[schemas.EmployeeResponseUnion])
@require_permission("employee.read.supervised")
def get_supervisees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]]:
    """Get employees that the current supervisor supervises (for assignment creation)"""
    
    # Check if user has permission to read all employees (HR Admin case)
    all_permission = validate_permission(current_user, "employee.read.all", db)
    if all_permission.granted:
        employees = crud.get_employees(db, skip=0, limit=1000)  # Large limit for HR admin
    else:
        # Get supervisor's employee record
        supervisor_employee = get_employee_by_user_id(db, current_user.user_id)
        if not supervisor_employee:
            raise HTTPException(status_code=404, detail="Supervisor employee record not found")
        
        # Get employees that this supervisor can assign as supervisors
        employees = crud.get_employees_for_supervisor_assignment(
            db, 
            supervisor_employee.employee_id, 
            include_self=True
        )
    
    # Apply permission-based filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response_by_permissions(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees

@router.get("/my-primary-supervisors", response_model=List[schemas.EmployeeResponse])
def get_my_primary_supervisors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get supervisors of current employee's primary assignment"""
    # Get current employee record
    employee = get_employee_by_user_id(db, current_user.user_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee record not found")
    
    # Get primary assignment supervisors
    supervisors = crud.get_primary_assignment_supervisors(db, employee.employee_id)
    return supervisors

@router.get("/{employee_id}", response_model=schemas.EmployeeResponseUnion)
async def read_employee(
    employee_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]:
    """Get employee by ID with permission-based data filtering and access validation"""
    db_employee = crud.get_employee(db, employee_id=employee_id)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Check if user has permission to access this specific employee
    all_result = validate_permission(current_user, "employee.read.all", db, resource_id=employee_id)
    own_result = validate_permission(current_user, "employee.read.own", db, resource_id=employee_id)
    supervised_result = validate_permission(current_user, "employee.read.supervised", db, resource_id=employee_id)
    
    if not (all_result.granted or own_result.granted or supervised_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to access employee {employee_id}",
                "user_role": current_user.role_names,
                "required_permissions": ["employee.read.all", "employee.read.own", "employee.read.supervised"]
            }
        )
    
    # Apply permission-based filtering
    return filter_employee_response_by_permissions(db_employee, current_user, db)

@router.get("/", response_model=List[schemas.EmployeeResponseUnion])
def read_employees(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]]:
    """Get list of employees with role-based access control and data filtering"""
    
    # Get permission-filtered employees
    employees = _get_permission_filtered_employees(db, current_user, skip=skip, limit=limit)
    
    # Apply permission-based data filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response_by_permissions(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees

@router.put("/{employee_id}", response_model=schemas.EmployeeResponse)
async def update_employee(
    employee_id: int,
    employee_update: schemas.EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update employee information with permission-based access control"""
    # Check if user has permission to update this specific employee
    all_result = validate_permission(current_user, "employee.update.all", db, resource_id=employee_id)
    own_result = validate_permission(current_user, "employee.update.own", db, resource_id=employee_id)
    
    if not (all_result.granted or own_result.granted):
        raise HTTPException(
            status_code=403,
            detail={
                "error": "Access Denied",
                "message": f"Insufficient permissions to update employee {employee_id}",
                "user_role": current_user.role_names,
                "required_permissions": ["employee.update.all", "employee.update.own"]
            }
        )
    
    db_employee = crud.update_employee(db=db, employee_id=employee_id, employee_update=employee_update)
    if db_employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return db_employee