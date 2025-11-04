# Multi-Role RBAC Implementation Plan

## Executive Summary

This document outlines the implementation plan for upgrading the current enhanced single-role RBAC system to a comprehensive multi-role RBAC architecture. This enhancement will allow users to be assigned multiple roles simultaneously, enabling more flexible organizational structures and role assignments.

**Current State**: Enhanced single-role RBAC with 39 permissions across 8 resource types
**Target State**: Multi-role RBAC supporting multiple simultaneous role assignments per user
**Estimated Timeline**: 2-3 weeks
**Business Value**: Support for complex organizational structures, temporary role assignments, and overlapping responsibilities

## Current Architecture Analysis

### Current Single-Role System
```
Users → Single Role (enum) → Static Role-Permission Mapping → Permissions
```

**Current Limitations**:
- Each user has exactly one role (HR_ADMIN, SUPERVISOR, EMPLOYEE)
- No support for temporary role assignments or coverage scenarios
- Cannot handle users with overlapping responsibilities
- Limited flexibility for complex organizational structures

**Current Strengths to Preserve**:
- Simple permission evaluation logic
- Efficient static role-permission mappings
- Well-defined permission taxonomy (39 permissions)
- Comprehensive admin interface
- Strong security controls

## Target Multi-Role Architecture

### Enhanced Multi-Role System
```
Users → Multiple Roles → Role-Permission Mappings → Aggregated Permissions
```

**New Capabilities**:
- Users can have multiple roles simultaneously
- Support for temporary role assignments
- Flexible role combinations (e.g., SUPERVISOR + HR_ADMIN)
- Dynamic role assignment through admin interface
- Backward compatibility with current single-role approach

## Implementation Plan

### Phase 6.1: Database Schema Migration

#### Task 6.1.1: Create Roles Table
```sql
CREATE TABLE roles (
    role_id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate with existing roles
INSERT INTO roles (name, description) VALUES 
    ('HR_ADMIN', 'Human Resources Administrator with full system access'),
    ('SUPERVISOR', 'Team supervisor with employee management capabilities'),
    ('EMPLOYEE', 'Standard employee with self-service access');
```

#### Task 6.1.2: Create User-Roles Junction Table
```sql
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by INTEGER REFERENCES users(user_id),
    is_active BOOLEAN DEFAULT TRUE,
    effective_start_date DATE DEFAULT CURRENT_DATE,
    effective_end_date DATE,
    notes TEXT,
    PRIMARY KEY (user_id, role_id)
);

-- Create indexes for performance
CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
CREATE INDEX idx_user_roles_active ON user_roles(is_active);
```

#### Task 6.1.3: Data Migration Script
```sql
-- Migrate existing single-role data to multi-role structure
INSERT INTO user_roles (user_id, role_id, assigned_at, assigned_by)
SELECT 
    u.user_id, 
    r.role_id,
    u.created_at,
    1 -- System user for migration
FROM users u
JOIN roles r ON r.name = u.role::text
WHERE u.role IS NOT NULL;
```

#### Task 6.1.4: Backward Compatibility
- Preserve existing `users.role` column during transition period
- Add database constraints to ensure data consistency
- Create migration rollback procedures

### Phase 6.2: Backend Model and Logic Updates

#### Task 6.2.1: Enhanced User Model
```python
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    
    # Preserve existing role field for backward compatibility
    role = Column(Enum(UserRole), nullable=True)  # Make nullable
    
    # New multi-role relationship
    user_roles = relationship(
        "UserRole", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    @property
    def active_roles(self):
        """Get all active roles for the user"""
        return [ur.role for ur in self.user_roles 
                if ur.is_active and ur.is_effective()]
    
    @property
    def role_names(self):
        """Get list of active role names"""
        return [role.name for role in self.active_roles]
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return role_name in self.role_names
    
    def has_any_role(self, role_names: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(self.has_role(role) for role in role_names)
```

#### Task 6.2.2: New Role Model
```python
class Role(Base):
    __tablename__ = "roles"
    
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user_roles
    user_roles = relationship("UserRole", back_populates="role")
    
    @property
    def permissions(self):
        """Get permissions for this role from registry"""
        from .permission_registry import ROLE_PERMISSIONS
        return ROLE_PERMISSIONS.get(self.name, [])

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("users.user_id"))
    is_active = Column(Boolean, default=True)
    effective_start_date = Column(Date, default=date.today)
    effective_end_date = Column(Date, nullable=True)
    notes = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    def is_effective(self, check_date=None):
        """Check if role assignment is currently effective"""
        if check_date is None:
            check_date = date.today()
        
        if not self.is_active:
            return False
        
        if self.effective_start_date and check_date < self.effective_start_date:
            return False
        
        if self.effective_end_date and check_date > self.effective_end_date:
            return False
        
        return True
```

#### Task 6.2.3: Multi-Role Permission Logic
```python
def has_permission(user: User, permission_name: str) -> bool:
    """
    Enhanced permission checking for multi-role users
    Returns True if user has permission through any of their active roles
    """
    # Check through all active roles
    for role in user.active_roles:
        if permission_name in role.permissions:
            return True
    
    # Fallback to single role for backward compatibility
    if user.role:
        from .permission_registry import ROLE_PERMISSIONS
        single_role_permissions = ROLE_PERMISSIONS.get(user.role.value, [])
        if permission_name in single_role_permissions:
            return True
    
    return False

def get_user_permissions(user: User) -> List[str]:
    """Get aggregated permissions from all user's active roles"""
    all_permissions = set()
    
    # Collect permissions from all active roles
    for role in user.active_roles:
        all_permissions.update(role.permissions)
    
    # Add permissions from single role (backward compatibility)
    if user.role:
        from .permission_registry import ROLE_PERMISSIONS
        single_role_permissions = ROLE_PERMISSIONS.get(user.role.value, [])
        all_permissions.update(single_role_permissions)
    
    return list(all_permissions)
```

### Phase 6.3: API and Authorization Updates

#### Task 6.3.1: Enhanced Admin APIs
```python
# New endpoints for multi-role management
@router.post("/api/v1/admin/users/{user_id}/roles")
@require_permission("user.manage")
async def assign_user_role(
    user_id: int,
    role_assignment: UserRoleAssignment,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a role to a user"""
    pass

@router.delete("/api/v1/admin/users/{user_id}/roles/{role_id}")
@require_permission("user.manage")
async def remove_user_role(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a role from a user"""
    pass

@router.get("/api/v1/admin/users/{user_id}/roles")
@require_permission("user.manage")
async def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all roles assigned to a user"""
    pass
```

#### Task 6.3.2: Updated Authentication Responses
```python
class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    # Enhanced for multi-role support
    roles: List[str]  # Active role names
    primary_role: Optional[str]  # For backward compatibility
    permissions: List[str]  # Aggregated permissions
    role_details: List[UserRoleDetail]  # Full role information

class UserRoleDetail(BaseModel):
    role_id: int
    role_name: str
    role_description: str
    assigned_at: datetime
    effective_start_date: date
    effective_end_date: Optional[date]
    is_active: bool
```

#### Task 6.3.3: Permission Decorator Updates
```python
def require_permission(permission_name: str):
    """Enhanced decorator supporting multi-role permission checking"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=401, 
                    detail="Authentication required"
                )
            
            # Multi-role permission check
            if not has_permission(current_user, permission_name):
                user_permissions = get_user_permissions(current_user)
                raise HTTPException(
                    status_code=403,
                    detail={
                        "message": "Permission denied",
                        "required_permission": permission_name,
                        "user_roles": current_user.role_names,
                        "user_permissions": user_permissions
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### Phase 6.4: Frontend Integration

#### Task 6.4.1: Enhanced Admin Interface
- **Multi-Role Assignment UI**: Interface for assigning/removing multiple roles per user
- **Role Timeline View**: Visual representation of role assignments with effective dates
- **Bulk Role Operations**: Assign/remove roles for multiple users simultaneously
- **Role Conflict Detection**: Identify and resolve conflicting role assignments

#### Task 6.4.2: User Interface Updates
```typescript
interface User {
  user_id: number;
  username: string;
  email: string;
  roles: string[];  // Active role names
  primary_role?: string;  // Backward compatibility
  permissions: string[];  // Aggregated permissions
  role_details: UserRoleDetail[];
}

interface UserRoleDetail {
  role_id: number;
  role_name: string;
  role_description: string;
  assigned_at: string;
  effective_start_date: string;
  effective_end_date?: string;
  is_active: boolean;
}
```

#### Task 6.4.3: Permission Checking Updates
```typescript
// Enhanced permission hooks for multi-role support
export const useHasPermission = (permission: string): boolean => {
  const { user } = useAuth();
  return user?.permissions?.includes(permission) ?? false;
};

export const useHasAnyRole = (roles: string[]): boolean => {
  const { user } = useAuth();
  return roles.some(role => user?.roles?.includes(role)) ?? false;
};

export const useUserRoles = (): string[] => {
  const { user } = useAuth();
  return user?.roles ?? [];
};
```

## Migration Strategy

### Gradual Migration Approach

#### Phase 1: Parallel System Operation
- Both single-role and multi-role systems work simultaneously
- Existing users continue using single role field
- New multi-role assignments stored in user_roles table
- Permission checking tries multi-role first, falls back to single role

#### Phase 2: User Migration
- Migrate existing users from single role to multi-role system
- Preserve all existing access patterns and permissions
- Validate permission consistency after migration
- Provide admin tools for role assignment verification

#### Phase 3: Legacy System Deprecation
- Remove dependency on single role field
- Update all permission checking to use multi-role only
- Remove backward compatibility code
- Update documentation and training materials

### Rollback Strategy

#### Database Rollback
```sql
-- Emergency rollback to single-role system
UPDATE users SET role = (
    SELECT r.name::user_role_enum
    FROM user_roles ur
    JOIN roles r ON ur.role_id = r.role_id
    WHERE ur.user_id = users.user_id
    AND ur.is_active = true
    ORDER BY ur.assigned_at ASC
    LIMIT 1
);
```

#### Code Rollback
- Feature flags to disable multi-role functionality
- Immediate fallback to single-role permission checking
- Admin interface to revert to single-role management

## Testing Strategy

### Unit Testing
- Multi-role permission evaluation logic
- Role assignment and removal functionality
- Edge cases (no roles, multiple roles, expired roles)
- Migration script validation

### Integration Testing
- End-to-end multi-role workflows
- Permission aggregation across multiple roles
- Admin interface role management
- API endpoint protection with multi-role users

### Performance Testing
- Permission checking performance with multiple roles
- Database query optimization for role lookups
- Memory usage with expanded role data
- Concurrent user load testing

## Risk Assessment and Mitigation

### Technical Risks

#### Risk: Permission Escalation
**Mitigation**: 
- Comprehensive permission validation
- Audit logging for all role assignments
- Regular permission review workflows

#### Risk: Performance Degradation
**Mitigation**:
- Database indexing strategy
- Permission caching mechanisms
- Query optimization for role lookups

#### Risk: Data Consistency Issues
**Mitigation**:
- Database constraints and foreign keys
- Transaction-based role assignments
- Data validation at application level

### Business Risks

#### Risk: Complex Role Management
**Mitigation**:
- Intuitive admin interface design
- Role assignment documentation
- Training for HR administrators

#### Risk: Security Gaps During Migration
**Mitigation**:
- Gradual migration approach
- Comprehensive testing at each phase
- Immediate rollback capabilities

## Success Criteria

### Functional Requirements
- ✅ Users can be assigned multiple roles simultaneously
- ✅ Permission evaluation aggregates permissions from all active roles
- ✅ Admin interface supports multi-role management
- ✅ Backward compatibility maintained during transition
- ✅ All existing functionality preserved

### Performance Requirements
- ✅ Permission checking latency < 50ms with multiple roles
- ✅ No performance regression compared to single-role system
- ✅ Database queries optimized for multi-role lookups

### Security Requirements
- ✅ No permission escalation vulnerabilities
- ✅ Audit trail for all role assignments
- ✅ Proper authorization for role management operations

## Timeline and Milestones

### Week 1: Database and Models
- **Day 1-2**: Database schema design and migration scripts
- **Day 3-4**: Backend model implementation and testing
- **Day 5**: Permission logic updates and validation

### Week 2: API and Integration
- **Day 1-2**: Admin API enhancements for multi-role management
- **Day 3-4**: Authentication and authorization updates
- **Day 5**: Backend integration testing

### Week 3: Frontend and Deployment
- **Day 1-3**: Admin interface updates for multi-role support
- **Day 4**: User acceptance testing and bug fixes
- **Day 5**: Production deployment and validation

## Post-Implementation

### Monitoring and Maintenance
- Permission usage analytics
- Role assignment pattern analysis
- Performance monitoring for multi-role operations
- User feedback collection and system optimization

### Future Enhancements
- **Temporal RBAC**: Time-based role assignments and permissions
- **Dynamic Permissions**: Context-aware permission evaluation
- **Role Hierarchy**: Parent-child role relationships
- **External Integration**: SSO and LDAP role synchronization

## Conclusion

This multi-role RBAC implementation provides the foundation for complex organizational structures while maintaining the security and performance characteristics of the current system. The gradual migration approach ensures minimal disruption to existing operations while providing immediate value through enhanced role flexibility.

The estimated 2-3 week timeline allows for comprehensive testing and validation at each phase, ensuring a smooth transition to the enhanced multi-role architecture.