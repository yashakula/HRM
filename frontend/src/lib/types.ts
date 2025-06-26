// Core types for the HRM frontend application

export enum UserRole {
  HR_ADMIN = "HR_ADMIN",
  SUPERVISOR = "SUPERVISOR", 
  EMPLOYEE = "EMPLOYEE"
}

export interface User {
  user_id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
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
    role: string;
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