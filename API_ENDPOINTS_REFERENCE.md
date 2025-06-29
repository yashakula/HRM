# HRM API Endpoints Reference Guide

## Overview
This document provides comprehensive documentation for all API endpoints in the HRM (Human Resource Management) system, including required permissions, authentication requirements, and endpoint organization.

- **Base URL**: `http://localhost:8000` (development)
- **API Version**: v1
- **Authentication**: Session-based with HTTP-only cookies
- **Authorization**: Permission-based access control (RBAC)

## API Router Organization

The HRM backend API is organized into 7 main router modules:

| Router | Base Path | Description | Endpoints |
|--------|-----------|-------------|-----------|
| **auth.py** | `/api/v1/auth` | Authentication and authorization | 5 endpoints |
| **employees.py** | `/api/v1/employees` | Employee management | 6 endpoints |
| **assignments.py** | `/api/v1/assignments` | Assignment management | 12 endpoints |
| **assignment_types.py** | `/api/v1/assignment-types` | Assignment type definitions | 5 endpoints |
| **departments.py** | `/api/v1/departments` | Department management | 5 endpoints |
| **leave_requests.py** | `/api/v1/leave-requests` | Leave request workflows | 7 endpoints |
| **admin.py** | `/api/v1/admin` | System administration | 8 endpoints |

**Total**: 48 API endpoints

## Authentication Router
**Base Path**: `/api/v1/auth`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/register` | None (public) | Register new user account |
| POST | `/login` | None (public) | User login with session creation |
| GET | `/me` | Authenticated | Get current user profile and permissions |
| POST | `/logout` | Authenticated | User logout and session cleanup |
| POST | `/validate-page-access` | Authenticated | Validate page access permissions |

### Usage Notes:
- Registration endpoint creates user accounts (production may restrict this)
- Login sets HTTP-only session cookies for authentication
- `/me` endpoint returns user profile with role-based permissions array
- Page access validation supports frontend route protection

## Employee Management Router
**Base Path**: `/api/v1/employees`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/` | `employee.create` | Create new employee profile (US-01) |
| GET | `/search` | Permission-filtered | Search employees with role-based filtering |
| GET | `/supervisees` | `employee.read.supervised` | Get supervised employees |
| GET | `/{employee_id}` | Context-aware† | Get employee by ID |
| GET | `/` | Permission-filtered | List employees with access control |
| PUT | `/{employee_id}` | Context-aware† | Update employee information |

**†Context-aware permissions**:
- `employee.read.all` - HR Admin access to all employees
- `employee.read.supervised` - Supervisor access to supervised employees  
- `employee.read.own` - Employee access to own profile
- `employee.update.all` - HR Admin can update any employee
- `employee.update.own` - Employees/Supervisors can update own profile

### Business Logic:
- Employee creation includes personal information and assignment setup
- Search functionality respects permission boundaries for data visibility
- Profile updates include ownership validation and supervisor relationship checks

## Assignment Management Router
**Base Path**: `/api/v1/assignments`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/` | `assignment.create` | Create new assignment |
| GET | `/` | Permission-filtered | List assignments with access control |
| GET | `/{assignment_id}` | Context-aware† | Get assignment details |
| PUT | `/{assignment_id}` | `assignment.update.all` | Update assignment information |
| DELETE | `/{assignment_id}` | `assignment.delete` | Remove assignment |
| PUT | `/{assignment_id}/primary` | `assignment.update.all` | Set as primary assignment |
| PUT | `/{assignment_id}/supervisors` | `assignment.manage_supervisors` | Update assignment supervisors |
| GET | `/{assignment_id}/supervisors` | Context-aware† | Get assignment supervisors |
| POST | `/{assignment_id}/supervisors` | `assignment.manage_supervisors` | Add supervisor to assignment |
| DELETE | `/{assignment_id}/supervisors/{supervisor_id}` | `assignment.manage_supervisors` | Remove supervisor from assignment |
| GET | `/employee/{employee_id}` | Context-aware† | Get employee's assignments |
| GET | `/supervisor/{supervisor_id}` | Context-aware† | Get assignments supervised by user |

**†Context-aware permissions**:
- `assignment.read.all` - HR Admin access to all assignments
- `assignment.read.supervised` - Supervisor access to supervised assignments
- `assignment.read.own` - Employee access to own assignments

### Business Logic:
- Assignment creation establishes employee-supervisor relationships
- Primary assignment designation affects compensation and reporting
- Supervisor management supports multi-supervisor approval workflows

## Assignment Types Router
**Base Path**: `/api/v1/assignment-types`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/` | `assignment_type.create` | Create assignment type |
| GET | `/` | Authenticated | List assignment types |
| GET | `/{assignment_type_id}` | Authenticated | Get assignment type details |
| PUT | `/{assignment_type_id}` | `assignment_type.update` | Update assignment type |
| DELETE | `/{assignment_type_id}` | `assignment_type.delete` | Delete assignment type |

### Business Logic:
- Assignment types define job roles and responsibilities
- All authenticated users can read assignment types for reference
- Only HR Admins can create, update, or delete assignment types

## Departments Router
**Base Path**: `/api/v1/departments`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/` | `department.create` | Create new department |
| GET | `/` | Authenticated | List departments |
| GET | `/{department_id}` | Authenticated | Get department details |
| PUT | `/{department_id}` | `department.update` | Update department information |
| DELETE | `/{department_id}` | `department.delete` | Delete department |

### Business Logic:
- Departments organize assignments and reporting structures
- All authenticated users can read department information
- Only HR Admins can modify department structure

## Leave Request Management Router
**Base Path**: `/api/v1/leave-requests`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| POST | `/` | `leave_request.create` | Submit new leave request |
| GET | `/` | Permission-filtered | List leave requests with access control |
| GET | `/my-requests` | `leave_request.read.own` | Get user's leave requests |
| GET | `/pending-approvals` | Approval permissions† | Get pending approval requests |
| GET | `/{leave_id}` | Context-aware† | Get leave request details |
| PUT | `/{leave_id}` | Approval permissions† | Approve/reject leave request |
| GET | `/assignments/{employee_id}/active` | Context-aware† | Get active assignments for leave form |

**†Permission variants**:
- **Approval permissions**: `leave_request.approve.all` OR `leave_request.approve.supervised`
- **Context-aware**: `leave_request.read.all` OR `leave_request.read.supervised` OR `leave_request.read.own`

### Business Logic:
- Leave requests require approval from all assignment supervisors
- Multi-supervisor approval workflow with automatic routing
- Pending approvals filtered by supervisor relationships
- Leave creation validates against active assignments

## System Administration Router
**Base Path**: `/api/v1/admin`

| Method | Endpoint | Permission | Description |
|--------|----------|------------|-------------|
| GET | `/users` | `user.manage` | List all users with roles and permissions |
| PUT | `/users/{user_id}/role` | `user.manage` | Update user role assignment |
| GET | `/users/{user_id}/permissions` | `user.manage` | Get user's effective permissions |
| GET | `/permissions` | `user.manage` | List all system permissions |
| GET | `/roles/{role}/permissions` | `user.manage` | Get role's permission assignments |
| GET | `/audit/user-roles` | `user.manage` | Get user role distribution analytics |
| GET | `/audit/permission-usage` | `user.manage` | Get permission usage analytics |
| GET | `/system/health` | `user.manage` | Get system health metrics |

### Admin Interface Features:
- **User Management**: View all users, change roles, analyze permissions
- **Permission Oversight**: View all permissions and role mappings
- **System Analytics**: Role distribution, permission usage statistics
- **Health Monitoring**: System metrics and user activity dashboards

## Permission System Architecture

### Permission Naming Convention
Format: `{resource}.{action}[.{scope}]`

**Examples**:
- `employee.create` - Create employees
- `employee.read.all` - Read all employee records
- `employee.read.own` - Read own employee record
- `leave_request.approve.supervised` - Approve supervised leave requests

### Permission Scopes

| Scope | Description | Access Level | Example |
|-------|-------------|--------------|---------|
| **all** | System-wide access | Unrestricted | `employee.read.all` |
| **supervised** | Team-based access | Supervision relationships | `leave_request.approve.supervised` |
| **own** | Self-only access | Personal resources | `employee.update.own` |
| **none** | General access | Public/reference data | `department.read` |

### Authorization Decorators

The API uses several authorization decorators for endpoint protection:

```python
@require_permission("permission.name")          # Single permission required
@require_any_permission(["perm1", "perm2"])     # Any permission required (OR)
@require_all_permissions(["perm1", "perm2"])    # All permissions required (AND)
```

### Context-Aware Validation

Many endpoints implement context-aware permission checking:
- **Ownership Validation**: Ensures users can only access their own resources
- **Supervision Validation**: Verifies supervisor-employee relationships
- **Resource-Specific Checks**: Additional business rules and access controls

## Role-Permission Matrix

For complete role-permission mappings, see [RBAC_PERMISSIONS_REFERENCE.md](./RBAC_PERMISSIONS_REFERENCE.md).

### Role Summary

| Role | Permissions | Key Capabilities |
|------|-------------|------------------|
| **HR_ADMIN** | 25 permissions | Full system administration, all CRUD operations |
| **SUPERVISOR** | 17 permissions | Team management, supervised access, approvals |
| **EMPLOYEE** | 10 permissions | Self-service, personal data management |

## Error Responses

### Authentication Errors
- **401 Unauthorized**: Missing or invalid session
- **403 Forbidden**: Insufficient permissions for requested resource

### Permission Errors
```json
{
  "detail": "Permission denied. Required permission: employee.read.all",
  "required_permission": "employee.read.all",
  "user_permissions": ["employee.read.own", "employee.update.own"]
}
```

### Validation Errors
- **422 Unprocessable Entity**: Invalid request data or business rule violations
- **404 Not Found**: Resource does not exist or user lacks access

## API Usage Examples

### Authentication Flow
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "hr_admin", "password": "admin123"}' \
  -c cookies.txt

# Use session for subsequent requests
curl -X GET http://localhost:8000/api/v1/employees/ \
  -b cookies.txt
```

### Employee Management
```bash
# Create employee (HR Admin only)
curl -X POST http://localhost:8000/api/v1/employees/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "personal_info": {
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@company.com"
    }
  }'

# Search employees (permission-filtered results)
curl -X GET "http://localhost:8000/api/v1/employees/search?query=John" \
  -b cookies.txt
```

### Leave Request Workflow
```bash
# Submit leave request
curl -X POST http://localhost:8000/api/v1/leave-requests/ \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "assignment_id": 1,
    "start_date": "2025-07-01",
    "end_date": "2025-07-05",
    "leave_type": "vacation",
    "reason": "Summer vacation"
  }'

# Approve leave request (supervisor)
curl -X PUT http://localhost:8000/api/v1/leave-requests/1 \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"status": "approved", "approval_notes": "Approved - coverage arranged"}'
```

## Development Guidelines

### Adding New Endpoints
1. Define appropriate permissions in `permission_registry.py`
2. Apply permission decorators to endpoint functions
3. Implement context-aware validation as needed
4. Update API documentation and permission reference
5. Add comprehensive unit and integration tests

### Permission Best Practices
- Use least-privilege principle for role assignments
- Implement resource-specific validation for sensitive operations
- Provide clear error messages for permission violations
- Test permission boundaries thoroughly
- Document any custom permission logic

### Testing Endpoints
- Unit tests for permission decorator behavior
- Integration tests for full request-response cycles
- Test matrix covering all permission combinations
- Validate error responses and edge cases

---

*This API reference is maintained alongside the HRM system codebase. For implementation details, see the source code in `/backend/src/hrm_backend/routers/`.*