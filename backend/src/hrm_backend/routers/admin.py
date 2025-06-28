"""
Admin API endpoints for RBAC management.
Provides interfaces for user management, permission oversight, and system administration.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..database import get_db
from ..auth import get_current_active_user
from ..permission_decorators import require_permission
from ..models import User, Employee, People, UserRole
from ..schemas import UserResponse
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
        query = query.filter(User.role == role_filter)
    
    # Order by creation date (newest first) and apply pagination
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    # Add permissions to each user response
    result = []
    for user in users:
        permissions = ROLE_PERMISSIONS.get(user.role.value, [])
        # Get the user's employee record (if any)
        employee = user.employees[0] if user.employees else None
        
        user_dict = {
            "user_id": user.user_id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "permissions": permissions,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "employee": employee
        }
        result.append(UserResponse(**user_dict))
    
    return result


@router.put("/users/{user_id}/role")
@require_permission("user.manage")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a user's role assignment.
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
    
    # Update the role
    old_role = target_user.role
    target_user.role = new_role
    db.commit()
    db.refresh(target_user)
    
    return {
        "message": f"User role updated from {old_role} to {new_role}",
        "user_id": user_id,
        "old_role": old_role,
        "new_role": new_role,
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
    # Count users by role
    role_counts = db.query(
        User.role,
        func.count(User.user_id).label('count')
    ).filter(
        User.is_active == True
    ).group_by(User.role).all()
    
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