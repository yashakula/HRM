// Core types for the HRM frontend application

export enum UserRole {
  SUPER_USER = "SUPER_USER",
  HR_ADMIN = "HR_ADMIN",
  SUPERVISOR = "SUPERVISOR", 
  EMPLOYEE = "EMPLOYEE"
}

export enum LeaveStatus {
  PENDING = "Pending",
  APPROVED = "Approved",
  REJECTED = "Rejected"
}

export interface User {
  user_id: number;
  username: string;
  email: string;
  roles: UserRole[]; // User's active roles from multi-role system
  permissions: string[]; // User's aggregated permissions from all roles
  is_active: boolean;
  created_at: string;
  employee?: Employee; // Associated employee if exists
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface LoginResponse {
  message: string;
  user: {
    user_id: number;
    username: string;
    roles: UserRole[];
  };
}

export interface PersonalInformation {
  personal_email?: string;
  ssn?: string;
  bank_account?: string;
  created_at: string;
  updated_at: string;
}

export interface Person {
  people_id: number;
  full_name: string;
  date_of_birth?: string;
  created_at: string;
  updated_at: string;
  personal_information?: PersonalInformation;
}

export interface Employee {
  employee_id: number;
  people_id: number;
  status: "Active" | "Inactive";
  work_email?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  created_at: string;
  updated_at: string;
  person: Person;
}

export interface EmployeeCreateRequest {
  person: {
    full_name: string;
    date_of_birth?: string;
  };
  personal_information?: {
    personal_email?: string;
    ssn?: string;
    bank_account?: string;
  };
  work_email?: string;
  effective_start_date?: string;
  effective_end_date?: string;
}

export interface EmployeeUpdateRequest {
  person?: {
    full_name?: string;
    date_of_birth?: string;
  };
  personal_information?: {
    personal_email?: string;
    ssn?: string;
    bank_account?: string;
  };
  work_email?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  status?: "Active" | "Inactive";
}

export interface EmployeeSearchParams {
  name?: string;
  employee_id?: number;
  status?: "Active" | "Inactive";
  skip?: number;
  limit?: number;
}

export interface ApiError {
  detail: string;
}

// Assignment management types
export interface Department {
  department_id: number;
  name: string;
  description: string;
}

export interface AssignmentType {
  assignment_type_id: number;
  description: string;
  department_id: number;
  department: Department;
  created_at: string;
  updated_at: string;
}

export interface Assignment {
  assignment_id: number;
  employee_id: number;
  assignment_type_id: number;
  description?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
  employee: Employee;
  assignment_type: AssignmentType;
  supervisors: Employee[];
}

export interface AssignmentCreateRequest {
  employee_id: number;
  assignment_type_id: number;
  description?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  is_primary?: boolean;
  supervisor_ids?: number[];
}

export interface AssignmentUpdateRequest {
  assignment_type_id?: number;
  description?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  is_primary?: boolean;
}

export interface SupervisorAssignmentCreate {
  supervisor_id: number;
  effective_start_date: string;
  effective_end_date?: string;
}

// Page access validation types
export interface PageAccessRequest {
  page_identifier: string;
  resource_id?: number; // For resource-specific pages like employee/123
}

export interface PageAccessPermissions {
  can_view: boolean;
  can_edit: boolean;
  can_create: boolean;
  can_delete: boolean;
  message: string;
  user_role: string;
  required_permissions: string[];
}

export interface PageAccessResponse {
  page_identifier: string;
  resource_id?: number;
  permissions: PageAccessPermissions;
  access_granted: boolean;
}

// Leave Request types
export interface LeaveRequest {
  leave_id: number;
  employee_id: number;
  start_date: string;
  end_date: string;
  reason?: string;
  status: LeaveStatus;
  submitted_at: string;
  decision_at?: string;
  decided_by?: number;
  employee: Employee;
  decision_maker?: Employee;
}

export interface LeaveRequestCreateRequest {
  start_date: string;
  end_date: string;
  reason?: string;
}

export interface LeaveRequestUpdateRequest {
  status: LeaveStatus;
  reason?: string;
}

export interface LeaveRequestApproveRequest {
  reason?: string;
}

export interface LeaveRequestRejectRequest {
  reason: string;
}