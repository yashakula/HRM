```mermaid

erDiagram
    USER {
        int         user_id PK
        string      username
        string      email
        string      password_hash
        boolean     is_active
        datetime    created_at
        datetime    updated_at
    }
    ROLES {
        int         role_id PK
        string      name             "SUPER_USER, HR_ADMIN, SUPERVISOR, EMPLOYEE"
        text        description
        boolean     is_active
        datetime    created_at
        datetime    updated_at
    }
    USER_ROLES {
        int         user_id PK,FK
        int         role_id PK,FK
        datetime    assigned_at
        int         assigned_by FK   "nullable, User who assigned"
        boolean     is_active
        date        effective_start_date
        date        effective_end_date "nullable"
        text        notes
    }
    PERMISSIONS {
        int         permission_id PK
        string      name             "e.g., employee.read.all"
        text        description
        string      resource_type    "employee, assignment, etc."
        string      action           "create, read, update, delete"
        string      scope            "all, own, supervised"
        datetime    created_at
    }
    ROLE_PERMISSIONS {
        string      role_enum PK     "Role name enum value"
        int         permission_id PK,FK
        datetime    created_at
    }
    PEOPLE {
        int         people_id PK
        string      full_name
        date        date_of_birth
        datetime    created_at
        datetime    updated_at
    }
    PERSONAL_INFORMATION {
        int         people_id PK,FK
        string      personal_email
        string      ssn
        string      bank_account
        datetime    created_at
        datetime    updated_at
    }
    EMPLOYEE {
        int         employee_id PK
        int         people_id FK
        int         user_id FK       "nullable"
        enum        status           "Active, Inactive"
        string      work_email
        date        effective_start_date
        date        effective_end_date
        datetime    created_at
        datetime    updated_at
    }
    DEPARTMENT {
        int         department_id PK
        string      name
        string      description
    }
    ASSIGNMENT_TYPE {
        int         assignment_type_id PK
        string      description
        int         department_id FK
        datetime    created_at
        datetime    updated_at
    }
    ASSIGNMENT {
        int         assignment_id PK
        int         employee_id FK
        int         assignment_type_id FK
        string      description
        date        effective_start_date
        date        effective_end_date
        boolean     is_primary
        datetime    created_at
        datetime    updated_at
    }
    ASSIGNMENT_SUPERVISOR {
        int         assignment_id PK,FK
        int         supervisor_id PK,FK
        date        effective_start_date
        date        effective_end_date
        datetime    created_at
        datetime    updated_at
    }
    LEAVE_REQUEST {
        int         leave_id PK
        int         employee_id FK   "Changed from assignment_id"
        date        start_date       "leave begins"
        date        end_date         "leave ends"
        text        reason
        enum        status           "Pending, Approved, Rejected"
        datetime    submitted_at
        datetime    decision_at
        int         decided_by FK    "Employee who approved/rejected"
    }
    ATTENDANCE {
        int         attendance_id PK
        int         assignment_id FK
        datetime    check_in
        datetime    check_out
        decimal     total_hours
    }
    PAY_TYPE {
        int         pay_type_id PK
        enum        code             "HOURLY, SALARY, CONTRACT"
        string      description
    }
    COMPENSATION {
        int         compensation_id PK
        int         assignment_id FK
        int         pay_type_id FK
        decimal     amount           "Hourly rate or annual salary"
        date        effective_start_date
        date        effective_end_date
        datetime    created_at
        datetime    updated_at
    }

    %% RBAC Relationships
    USER ||--o{ USER_ROLES              : "assigned"
    ROLES ||--o{ USER_ROLES             : "grants"
    USER ||--o{ USER_ROLES              : "assigns roles"
    PERMISSIONS ||--o{ ROLE_PERMISSIONS : "granted to"
    
    %% Core Entity Relationships  
    USER ||--o{ EMPLOYEE                : "system account"
    PEOPLE ||--|| PERSONAL_INFORMATION  : "has"
    PEOPLE ||--o{ EMPLOYEE              : "is"
    EMPLOYEE ||--o{ ASSIGNMENT          : "holds"
    DEPARTMENT ||--o{ ASSIGNMENT_TYPE   : "defines"
    ASSIGNMENT_TYPE ||--o{ ASSIGNMENT   : "categorizes"
    ASSIGNMENT ||--o{ ASSIGNMENT_SUPERVISOR : "supervised by"
    EMPLOYEE ||--o{ ASSIGNMENT_SUPERVISOR : "supervises"
    
    %% Leave Request Relationships (Updated)
    EMPLOYEE ||--o{ LEAVE_REQUEST       : "submits"
    EMPLOYEE ||--o{ LEAVE_REQUEST       : "decides"
    
    %% Other Relationships
    ASSIGNMENT ||--o{ ATTENDANCE        : "logs"
    ASSIGNMENT ||--o{ COMPENSATION      : "has pay history"
    PAY_TYPE  ||--o{ COMPENSATION       : "defines"
    ```

## Schema Summary

### Current Database Schema (Updated 2025-06-29)

#### **Key Changes Made:**

1. **🔐 RBAC Implementation**
   - **ROLES**: Centralized role definitions (SUPER_USER, HR_ADMIN, SUPERVISOR, EMPLOYEE)
   - **USER_ROLES**: Many-to-many user-role assignments with temporal validity
   - **PERMISSIONS**: Granular permission definitions with resource.action.scope format
   - **ROLE_PERMISSIONS**: Static mapping of permissions to role enums

2. **📋 Leave Request Model Migration**
   - **Changed**: `LEAVE_REQUEST.assignment_id` → `LEAVE_REQUEST.employee_id`
   - **Benefit**: Simplified employee-based leave requests instead of assignment-based
   - **Impact**: Leave requests now directly associated with employees, approved by primary assignment supervisors

3. **👥 Enhanced Supervisor Relationships**
   - **ASSIGNMENT_SUPERVISOR**: Junction table for assignment-supervisor relationships
   - **Primary Assignment Logic**: Only supervisors of primary assignments can approve leave requests
   - **Temporal Supervision**: Effective start/end dates for supervisor assignments

#### **Core Business Logic:**

- **Multi-Role Users**: Users can have multiple active roles simultaneously
- **Primary Assignment**: Each employee has one primary assignment for leave approval routing
- **Supervisor Hierarchy**: Supervisors approve leave requests for employees whose primary assignment they supervise
- **Permission-Based Access**: All operations governed by granular RBAC permissions
- **Temporal Validity**: Roles and supervisor relationships have effective date ranges

#### **Permission Examples:**
- `employee.read.all` - HR can read all employee records
- `employee.read.own` - Employees can read their own records
- `leave_request.approve.supervised` - Supervisors can approve requests from supervisees
- `assignment.create` - HR can create new assignments

#### **Table Count**: 16 tables
- **Core Entities**: 8 tables (USER, PEOPLE, EMPLOYEE, etc.)
- **RBAC System**: 4 tables (ROLES, USER_ROLES, PERMISSIONS, ROLE_PERMISSIONS)  
- **Business Logic**: 4 tables (ASSIGNMENT, LEAVE_REQUEST, ATTENDANCE, COMPENSATION)