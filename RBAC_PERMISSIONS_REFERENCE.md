# RBAC Permissions Reference Guide

## Overview
This document provides a comprehensive reference for the Multi-Role Based Access Control (RBAC) system implemented in the HRM application. The system supports both single-role and multi-role assignments with fine-grained permission-based access control across all system resources.

- **Total Permissions**: 39 permissions across 8 resource types
- **Total Roles**: 3 user roles (HR_ADMIN, SUPERVISOR, EMPLOYEE)
- **Permission Structure**: `resource.action.scope` format (e.g., `employee.read.all`)
- **Architecture**: Multi-role RBAC with backward compatibility for single-role users
- **Multi-Role Support**: Users can be assigned multiple roles simultaneously with aggregated permissions

## Complete Role-Permission Matrix

| Permission | Description | SUPER_USER | HR_ADMIN | SUPERVISOR | EMPLOYEE |
|------------|-------------|------------|----------|------------|----------|
| **EMPLOYEE MANAGEMENT** |
| `employee.create` | Create new employees | ✅ | ✅ | ❌ | ❌ |
| `employee.read.all` | Read all employee records | ✅ | ✅ | ❌ | ❌ |
| `employee.read.supervised` | Read supervised employee records | ✅ | ❌ | ✅ | ❌ |
| `employee.read.own` | Read own employee record | ✅ | ❌ | ✅ | ✅ |
| `employee.update.all` | Update all employee records | ✅ | ✅ | ❌ | ❌ |
| `employee.update.own` | Update own employee record | ✅ | ❌ | ✅ | ✅ |
| `employee.search` | Search employee records | ✅ | ✅ | ✅ | ❌ |
| `employee.deactivate` | Deactivate employee accounts | ✅ | ✅ | ❌ | ❌ |
| **ASSIGNMENT MANAGEMENT** |
| `assignment.create` | Create new assignments | ✅ | ❌ | ❌ |
| `assignment.read.all` | Read all assignments | ✅ | ❌ | ❌ |
| `assignment.read.supervised` | Read supervised assignments | ❌ | ✅ | ❌ |
| `assignment.read.own` | Read own assignments | ❌ | ✅ | ✅ |
| `assignment.update.all` | Update all assignments | ✅ | ❌ | ❌ |
| `assignment.delete` | Delete assignments | ✅ | ❌ | ❌ |
| `assignment.manage_supervisors` | Manage assignment supervisors | ✅ | ❌ | ❌ |
| **LEAVE REQUEST MANAGEMENT** |
| `leave_request.create.own` | Create own leave requests | ❌ | ✅ | ✅ |
| `leave_request.read.all` | Read all leave requests | ✅ | ❌ | ❌ |
| `leave_request.read.supervised` | Read supervised leave requests | ❌ | ✅ | ❌ |
| `leave_request.read.own` | Read own leave requests | ❌ | ✅ | ✅ |
| `leave_request.approve.all` | Approve all leave requests | ✅ | ❌ | ❌ |
| `leave_request.approve.supervised` | Approve supervised leave requests | ❌ | ✅ | ❌ |
| `leave_request.reject.all` | Reject all leave requests | ✅ | ❌ | ❌ |
| `leave_request.reject.supervised` | Reject supervised leave requests | ❌ | ✅ | ❌ |
| **DEPARTMENT MANAGEMENT** |
| `department.create` | Create departments | ✅ | ❌ | ❌ |
| `department.read` | Read department information | ✅ | ✅ | ✅ |
| `department.update` | Update departments | ✅ | ❌ | ❌ |
| `department.delete` | Delete departments | ✅ | ❌ | ❌ |
| **ASSIGNMENT TYPE MANAGEMENT** |
| `assignment_type.create` | Create assignment types | ✅ | ❌ | ❌ |
| `assignment_type.read` | Read assignment types | ✅ | ✅ | ✅ |
| `assignment_type.update` | Update assignment types | ✅ | ❌ | ❌ |
| `assignment_type.delete` | Delete assignment types | ✅ | ❌ | ❌ |
| **USER MANAGEMENT** |
| `user.manage` | Manage user accounts and roles | ✅ | ❌ | ❌ |
| **ATTENDANCE MANAGEMENT** |
| `attendance.log.own` | Log own attendance | ❌ | ✅ | ✅ |
| `attendance.read.own` | Read own attendance records | ❌ | ✅ | ✅ |
| `attendance.read.supervised` | Read supervised attendance | ❌ | ✅ | ❌ |
| `attendance.read.all` | Read all attendance records | ✅ | ❌ | ❌ |
| **COMPENSATION MANAGEMENT** |
| `compensation.read.own` | Read own compensation | ❌ | ✅ | ✅ |
| `compensation.read.all` | Read all compensation records | ✅ | ❌ | ❌ |
| `compensation.update` | Update compensation records | ✅ | ❌ | ❌ |

## Role Permission Summary

| Role | Total Permissions | Key Capabilities |
|------|------------------|------------------|
| **HR_ADMIN** | **25 permissions** | • Full system administration<br>• All employee/assignment management<br>• User role management<br>• Complete leave request oversight<br>• Department & assignment type management<br>• Access to admin panel |
| **SUPERVISOR** | **17 permissions** | • Supervised employee management<br>• Leave request approval for team<br>• Own profile management<br>• Team attendance oversight<br>• Read-only system data access |
| **EMPLOYEE** | **10 permissions** | • Own profile management<br>• Own leave request creation<br>• Own attendance logging<br>• Own assignment viewing<br>• Read-only system data access |

## Permission Scope Definitions

| Scope | Description | Example | Access Level |
|-------|-------------|---------|--------------|
| **all** | Access to all records system-wide | `employee.read.all` | Unrestricted |
| **supervised** | Access to records of supervised users | `leave_request.approve.supervised` | Team-based |
| **own** | Access only to user's own records | `employee.update.own` | Self-only |
| **none** | No scope restriction (general access) | `department.read` | Public data |

## Resource Types

| Resource | Description | Total Permissions |
|----------|-------------|------------------|
| **employee** | Employee profiles and personal information | 8 permissions |
| **assignment** | Job assignments and role mappings | 7 permissions |
| **leave_request** | Leave applications and approvals | 8 permissions |
| **department** | Organizational departments | 4 permissions |
| **assignment_type** | Job role definitions | 4 permissions |
| **user** | System user accounts and roles | 1 permission |
| **attendance** | Time tracking and attendance records | 4 permissions |
| **compensation** | Salary and payment information | 3 permissions |

## System Architecture

### Permission-Based Authorization
- **Backend**: Permission decorators (`@require_permission`) validate user access
- **Frontend**: Permission hooks (`useHasPermission`) control UI rendering
- **Database**: Static role-permission mappings for efficient lookup
- **Context-Aware**: Automatic ownership and supervision validation

### Multi-Role Assignment
- **Multiple Roles Per User**: Users can be assigned multiple roles simultaneously (e.g., SUPERVISOR + HR_ADMIN)
- **Permission Aggregation**: Users inherit permissions from ALL assigned roles (union of all role permissions)
- **Dynamic Evaluation**: Permissions evaluated at runtime with context awareness across all roles
- **Admin Management**: Only SUPER_USER can change user roles via admin panel
- **Role Management APIs**: Complete CRUD operations for multi-role assignments with effective dates

## Usage Examples

### Backend API Protection
```python
@require_permission("employee.read.all")
async def list_all_employees():
    # Only HR_ADMIN can access this endpoint
    pass

@require_permission("employee.update.own")
async def update_own_profile():
    # SUPERVISOR and EMPLOYEE can update their own profiles
    pass
```

### Frontend Permission Checks
```typescript
const canCreateEmployee = useHasPermission('employee.create');
const canApproveLeave = useHasAnyPermission([
  'leave_request.approve.all', 
  'leave_request.approve.supervised'
]);
```

### Admin Interface Access
- **URL**: `/admin` 
- **Required Permission**: `user.manage`
- **Available To**: HR_ADMIN only
- **Features**: User role management, permission overview, system analytics

## Security Features

### Principle of Least Privilege
- Users receive only the minimum permissions required for their role
- Scope-based restrictions prevent unauthorized access to other users' data
- Supervisor permissions limited to their direct reports

### Context-Aware Validation
- **Ownership Validation**: Automatic checking of resource ownership
- **Supervision Validation**: Verification of supervisor-employee relationships
- **Resource-Specific Access**: Different permissions for different data types

### Audit and Monitoring
- **Permission Usage Analytics**: Track which permissions are most used
- **Role Distribution Metrics**: Monitor user role distribution
- **System Health Dashboard**: Real-time system metrics and user statistics

## Migration Information

This RBAC system was migrated from a legacy role-based system to provide:
- **Fine-grained Control**: 39 specific permissions vs 3 broad roles
- **Maintainable Code**: Centralized permission management
- **Scalable Architecture**: Easy addition of new permissions and roles
- **Audit Capabilities**: Complete visibility into user access patterns

For detailed migration information, see `RBAC_MIGRATION_PLAN.md`.

## Development Guidelines

### Adding New Permissions
1. Add permission definition to `permission_registry.py`
2. Update role mappings in `ROLE_PERMISSIONS`
3. Apply permission decorators to API endpoints
4. Update frontend permission checks as needed

### Permission Naming Convention
- Format: `resource.action.scope`
- Resource: Lowercase entity name (e.g., `employee`, `assignment`)
- Action: CRUD operation (e.g., `create`, `read`, `update`, `delete`)
- Scope: Access level (e.g., `all`, `supervised`, `own`) - optional

### Testing Permissions
- Unit tests validate permission logic
- Integration tests verify end-to-end permission enforcement
- Admin interface provides real-time permission testing capabilities

---

*This document is automatically maintained as part of the RBAC system. For updates or questions, contact the development team.*