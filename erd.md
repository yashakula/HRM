```mermaid

erDiagram
    USER {
        int         user_id PK
        string      username
        string      email
        string      password_hash
        boolean     is_active
        enum        role             "HR_ADMIN, SUPERVISOR, EMPLOYEE"
        datetime    created_at
        datetime    updated_at
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
        int         assignment_id FK
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

    USER ||--o{ EMPLOYEE                : "system account"
    PEOPLE ||--|| PERSONAL_INFORMATION  : "has"
    PEOPLE ||--o{ EMPLOYEE              : "is"
    EMPLOYEE ||--o{ ASSIGNMENT          : "holds"
    DEPARTMENT ||--o{ ASSIGNMENT_TYPE   : "defines"
    ASSIGNMENT_TYPE ||--o{ ASSIGNMENT   : "categorizes"
    ASSIGNMENT ||--o{ ASSIGNMENT_SUPERVISOR : "supervised by"
    EMPLOYEE ||--o{ ASSIGNMENT_SUPERVISOR : "supervises"
    ASSIGNMENT ||--o{ LEAVE_REQUEST     : "initiates"
    EMPLOYEE ||--o{ LEAVE_REQUEST       : "decides"
    ASSIGNMENT ||--o{ ATTENDANCE        : "logs"
    ASSIGNMENT ||--o{ COMPENSATION      : "has pay history"
    PAY_TYPE  ||--o{ COMPENSATION       : "defines"
    ```