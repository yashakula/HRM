from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Union

from .. import crud, models, schemas
from ..database import get_db
from ..auth import require_hr_admin, get_current_active_user, filter_employee_response, validate_employee_access, get_employee_by_user_id
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

def _get_role_filtered_employees(
    db: Session, 
    current_user: User, 
    search_params: Optional[schemas.EmployeeSearchParams] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get employees filtered by user role - supervisors only see their supervisees"""
    
    # HR Admin gets all employees (existing behavior)
    if current_user.role == models.UserRole.HR_ADMIN:
        if search_params:
            employees = crud.search_employees(db, search_params)
        else:
            employees = crud.get_employees(db, skip=skip, limit=limit)
    else:
        # For supervisors and employees, get filtered list
        supervisor_employee = get_employee_by_user_id(db, current_user.user_id)
        if not supervisor_employee:
            return []
        
        if current_user.role == models.UserRole.SUPERVISOR:
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
        else:
            # Regular employees can only see themselves
            if supervisor_employee:
                employees = [supervisor_employee]
                
                # Apply search filtering even for single employee result
                if search_params:
                    # Check if their own record matches the search criteria
                    if search_params.name and search_params.name.lower() not in supervisor_employee.person.full_name.lower():
                        employees = []
                    elif search_params.employee_id and supervisor_employee.employee_id != search_params.employee_id:
                        employees = []
                    elif search_params.status and supervisor_employee.status != search_params.status:
                        employees = []
                    # Skip pagination for single result
            else:
                employees = []
    
    return employees

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
    
    # Get role-filtered employees
    employees = _get_role_filtered_employees(db, current_user, search_params)
    
    # Apply role-based data filtering to each employee record
    filtered_employees = []
    for employee in employees:
        filtered_employee = filter_employee_response(employee, current_user, db)
        filtered_employees.append(filtered_employee)
    
    return filtered_employees


@router.get("/supervisees", response_model=List[schemas.EmployeeResponseUnion])
def get_supervisees(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Union[schemas.EmployeeResponseHR, schemas.EmployeeResponseOwner, schemas.EmployeeResponseBasic]]:
    """Get employees that the current supervisor supervises (for assignment creation)"""
    
    # Only supervisors and HR admins can use this endpoint
    if current_user.role not in [models.UserRole.SUPERVISOR, models.UserRole.HR_ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Only supervisors and HR admins can access supervisee lists"
        )
    
    # HR Admin gets all employees (existing behavior)
    if current_user.role == models.UserRole.HR_ADMIN:
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
    """Get list of employees with role-based access control and data filtering"""
    
    # Get role-filtered employees
    employees = _get_role_filtered_employees(db, current_user, skip=skip, limit=limit)
    
    # Apply role-based data filtering to each employee record
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