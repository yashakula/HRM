"""
Admin API endpoints for RBAC management.
Provides interfaces for user management, permission oversight, and system administration.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel

from ..database import get_db
from ..auth import get_current_active_user
from ..permission_decorators import require_permission
from ..models import User, Employee, People, UserRole, Role, UserRoleAssignment
from ..schemas import UserResponse, RoleResponse, UserRoleAssignmentCreate, UserRoleAssignmentResponse, UserWithRolesResponse
from ..permission_registry import ROLE_PERMISSIONS

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/users", response_model=List[UserResponse])
@require_permission("user.manage")
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[UserRole] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all users with their roles and effective permissions.
    Available to users with user.manage permission.
    """
    query = db.query(User)
    
    # Filter by role if specified
    if role_filter:
        # Join with user_roles and roles table to filter by role name
        query = query.join(UserRoleAssignment).join(Role).filter(
            Role.name == role_filter.value,
            UserRoleAssignment.is_active == True
        )
    
    # Order by creation date (newest first) and apply pagination
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    # Add permissions to each user response
    result = []
    for user in users:
        permissions = user.get_all_permissions()
        # Get the user's employee record (if any)
        employee = user.employees[0] if user.employees else None
        
        user_dict = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "roles": user.role_names,
            "permissions": permissions,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "employee": employee
        }
        result.append(UserResponse(**user_dict))
    
    return result


class RoleUpdateRequest(BaseModel):
    new_role: UserRole

@router.put("/users/{user_id}/role")
@require_permission("user.manage")
async def update_user_role(
    user_id: int,
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a user's primary role assignment (for backward compatibility).
    This replaces all current roles with a single new role.
    Available to users with user.manage permission.
    """
    # Get the target user
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent users from modifying their own role
    if target_user.user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role"
        )
    
    # Get current roles for logging
    current_roles = [assignment.role.name for assignment in target_user.user_roles if assignment.is_active]
    
    # Deactivate all current role assignments
    for assignment in target_user.user_roles:
        assignment.is_active = False
    
    # Get the new role
    role = db.query(Role).filter(Role.name == request.new_role.value).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{request.new_role.value}' not found"
        )
    
    # Check if user already has this role assignment (reactivate if exists)
    existing_assignment = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role.role_id
    ).first()
    
    if existing_assignment:
        existing_assignment.is_active = True
    else:
        # Create new role assignment
        new_assignment = UserRoleAssignment(
            user_id=user_id,
            role_id=role.role_id,
            assigned_by=current_user.user_id,
            is_active=True
        )
        db.add(new_assignment)
    
    db.commit()
    db.refresh(target_user)
    
    return {
        "message": f"User role updated from {current_roles} to [{request.new_role.value}]",
        "user_id": user_id,
        "old_roles": current_roles,
        "new_role": request.new_role.value,
        "updated_by": current_user.username
    }


@router.get("/users/{user_id}/permissions")
@require_permission("user.manage")
async def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get effective permissions for a specific user.
    Available to users with user.manage permission.
    """
    target_user = db.query(User).filter(User.user_id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permissions = ROLE_PERMISSIONS.get(target_user.role.value, [])
    
    return {
        "user_id": user_id,
        "username": target_user.username,
        "role": target_user.role,
        "permissions": permissions,
        "permission_count": len(permissions)
    }


@router.get("/permissions")
@require_permission("user.manage")
async def list_all_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all available permissions in the system.
    Available to users with user.manage permission.
    """
    # Collect all unique permissions from role mappings
    all_permissions = set()
    for role_permissions in ROLE_PERMISSIONS.values():
        all_permissions.update(role_permissions)
    
    # Group permissions by resource type
    permission_groups = {}
    for permission in sorted(all_permissions):
        parts = permission.split('.')
        resource = parts[0] if parts else 'unknown'
        
        if resource not in permission_groups:
            permission_groups[resource] = []
        permission_groups[resource].append(permission)
    
    return {
        "total_permissions": len(all_permissions),
        "permission_groups": permission_groups,
        "all_permissions": sorted(all_permissions)
    }


@router.get("/roles/{role}/permissions")
@require_permission("user.manage")
async def get_role_permissions(
    role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all permissions assigned to a specific role.
    Available to users with user.manage permission.
    """
    permissions = ROLE_PERMISSIONS.get(role.value, [])
    
    # Group permissions by resource type for better organization
    permission_groups = {}
    for permission in permissions:
        parts = permission.split('.')
        resource = parts[0] if parts else 'unknown'
        
        if resource not in permission_groups:
            permission_groups[resource] = []
        permission_groups[resource].append(permission)
    
    return {
        "role": role,
        "permissions": permissions,
        "permission_count": len(permissions),
        "permission_groups": permission_groups
    }


@router.get("/audit/user-roles")
@require_permission("user.manage")
async def get_user_role_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics on user role distribution.
    Available to users with user.manage permission.
    """
    # Count users by role (using the multi-role system)
    role_counts = db.query(
        Role.name,
        func.count(func.distinct(User.user_id)).label('count')
    ).select_from(Role).join(
        UserRoleAssignment, Role.role_id == UserRoleAssignment.role_id
    ).join(
        User, UserRoleAssignment.user_id == User.user_id
    ).filter(
        User.is_active == True,
        UserRoleAssignment.is_active == True
    ).group_by(Role.name).all()
    
    # Total active users
    total_users = db.query(func.count(User.user_id)).filter(User.is_active == True).scalar()
    
    # Format the results
    role_distribution = []
    for role, count in role_counts:
        percentage = (count / total_users * 100) if total_users > 0 else 0
        role_distribution.append({
            "role": role,
            "user_count": count,
            "percentage": round(percentage, 1)
        })
    
    return {
        "total_active_users": total_users,
        "role_distribution": role_distribution,
        "roles_available": list(UserRole)
    }


@router.get("/audit/permission-usage")
@require_permission("user.manage")
async def get_permission_usage_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get analytics on permission usage across roles.
    Available to users with user.manage permission.
    """
    # Get user counts by role
    role_counts = dict(db.query(
        User.role,
        func.count(User.user_id).label('count')
    ).filter(User.is_active == True).group_by(User.role).all())
    
    # Calculate permission usage
    permission_usage = {}
    
    for role, permissions in ROLE_PERMISSIONS.items():
        user_count = role_counts.get(role, 0)
        
        for permission in permissions:
            if permission not in permission_usage:
                permission_usage[permission] = {
                    "permission": permission,
                    "total_users": 0,
                    "roles_with_permission": []
                }
            
            permission_usage[permission]["total_users"] += user_count
            permission_usage[permission]["roles_with_permission"].append({
                "role": role,
                "user_count": user_count
            })
    
    # Sort by usage (most used permissions first)
    sorted_permissions = sorted(
        permission_usage.values(),
        key=lambda x: x["total_users"],
        reverse=True
    )
    
    return {
        "permission_analytics": sorted_permissions,
        "total_unique_permissions": len(permission_usage),
        "role_user_counts": role_counts
    }


@router.get("/system/health")
@require_permission("user.manage")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get system health metrics for admin dashboard.
    Available to users with user.manage permission.
    """
    # Count various entities
    total_users = db.query(func.count(User.user_id)).scalar()
    active_users = db.query(func.count(User.user_id)).filter(User.is_active == True).scalar()
    total_employees = db.query(func.count(Employee.employee_id)).scalar()
    
    # Recent activity (users created in last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = db.query(func.count(User.user_id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "total_employees": total_employees,
        "recent_users_30d": recent_users,
        "permission_system": {
            "total_roles": len(UserRole),
            "total_permissions": len(set().union(*ROLE_PERMISSIONS.values())),
            "avg_permissions_per_role": sum(len(perms) for perms in ROLE_PERMISSIONS.values()) / len(ROLE_PERMISSIONS)
        },
        "timestamp": datetime.utcnow()
    }


# Multi-Role RBAC Management Endpoints

@router.get("/roles", response_model=List[RoleResponse])
@require_permission("user.manage")
async def list_all_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all available roles in the system"""
    roles = db.query(Role).filter(Role.is_active == True).all()
    return roles


@router.get("/users/{user_id}/roles", response_model=UserWithRolesResponse)
@require_permission("user.manage")
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all role assignments for a specific user"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get role assignments with role details
    role_assignments = []
    for user_role in user.user_roles:
        role_assignments.append(user_role)
    
    return {
        "user_id": user.user_id,
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "role_assignments": role_assignments,
        "permissions": user.get_all_permissions(),
        "employee": user.employees[0] if user.employees else None
    }


@router.post("/users/{user_id}/roles")
@require_permission("user.manage")
async def assign_user_role(
    user_id: int,
    role_assignment: UserRoleAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assign a role to a user"""
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if role exists
    role = db.query(Role).filter(Role.name == role_assignment.role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_assignment.role_name}' not found")
    
    # Check if user already has this role
    existing_assignment = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role.role_id
    ).first()
    
    if existing_assignment:
        raise HTTPException(
            status_code=400, 
            detail=f"User already has role '{role_assignment.role_name}'"
        )
    
    # Create new role assignment
    from datetime import date
    new_assignment = UserRoleAssignment(
        user_id=user_id,
        role_id=role.role_id,
        assigned_by=current_user.user_id,
        effective_start_date=role_assignment.effective_start_date or date.today(),
        effective_end_date=role_assignment.effective_end_date,
        notes=role_assignment.notes
    )
    
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)
    
    return {
        "message": "Role assigned successfully",
        "user_id": user_id,
        "role_name": role_assignment.role_name,
        "assigned_by": current_user.username,
        "effective_start_date": new_assignment.effective_start_date,
        "effective_end_date": new_assignment.effective_end_date
    }


@router.delete("/users/{user_id}/roles/{role_id}")
@require_permission("user.manage")
async def remove_user_role(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Remove a role from a user"""
    # Find the role assignment
    assignment = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    # Get role name for response
    role = db.query(Role).filter(Role.role_id == role_id).first()
    role_name = role.name if role else "Unknown"
    
    # Remove the assignment
    db.delete(assignment)
    db.commit()
    
    return {
        "message": "Role removed successfully",
        "user_id": user_id,
        "role_name": role_name,
        "removed_by": current_user.username
    }


@router.put("/users/{user_id}/roles/{role_id}/toggle")
@require_permission("user.manage")
async def toggle_user_role_status(
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle the active status of a user's role assignment"""
    assignment = db.query(UserRoleAssignment).filter(
        UserRoleAssignment.user_id == user_id,
        UserRoleAssignment.role_id == role_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    
    # Toggle the status
    assignment.is_active = not assignment.is_active
    db.commit()
    
    # Get role name for response
    role = db.query(Role).filter(Role.role_id == role_id).first()
    role_name = role.name if role else "Unknown"
    
    return {
        "message": f"Role {'activated' if assignment.is_active else 'deactivated'} successfully",
        "user_id": user_id,
        "role_name": role_name,
        "is_active": assignment.is_active,
        "modified_by": current_user.username
    }


@router.get("/roles/{role_name}/users")
@require_permission("user.manage")
async def get_users_with_role(
    role_name: str,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all users who have a specific role"""
    # Check if role exists
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        raise HTTPException(status_code=404, detail=f"Role '{role_name}' not found")
    
    # Build query
    query = db.query(User).join(UserRoleAssignment).filter(
        UserRoleAssignment.role_id == role.role_id
    )
    
    if not include_inactive:
        query = query.filter(UserRoleAssignment.is_active == True)
    
    users = query.all()
    
    return {
        "role_name": role_name,
        "total_users": len(users),
        "users": [
            {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "employee_name": user.employees[0].person.full_name if user.employees else None
            }
            for user in users
        ]
    }