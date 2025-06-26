import { apiClient } from '../api';
import { Employee } from '../types';
import { AssignmentType } from './assignmentTypes';

export interface Assignment {
  assignment_id: number;
  employee_id: number;
  assignment_type_id: number;
  description?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  created_at: string;
  updated_at: string;
  employee: Employee;
  assignment_type: AssignmentType;
  supervisors: Employee[];
}

export interface AssignmentCreate {
  employee_id: number;
  assignment_type_id: number;
  description?: string;
  effective_start_date?: string;
  effective_end_date?: string;
  supervisor_ids?: number[];
}

export const assignmentApi = {
  // Get all assignments with optional filters
  getAll: (params?: {
    employee_id?: number;
    supervisor_id?: number;
    department_id?: number;
    assignment_type_id?: number;
    employee_name?: string;
    skip?: number;
    limit?: number;
  }): Promise<Assignment[]> => {
    const searchParams = new URLSearchParams();
    if (params?.employee_id) searchParams.append('employee_id', params.employee_id.toString());
    if (params?.supervisor_id) searchParams.append('supervisor_id', params.supervisor_id.toString());
    if (params?.department_id) searchParams.append('department_id', params.department_id.toString());
    if (params?.assignment_type_id) searchParams.append('assignment_type_id', params.assignment_type_id.toString());
    if (params?.employee_name) searchParams.append('employee_name', params.employee_name);
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const queryString = searchParams.toString();
    return apiClient.get<Assignment[]>(`/api/v1/assignments${queryString ? `?${queryString}` : ''}`);
  },

  // Get assignment by ID
  getById: (id: number): Promise<Assignment> => {
    return apiClient.get<Assignment>(`/api/v1/assignments/${id}`);
  },

  // Create new assignment
  create: (assignment: AssignmentCreate): Promise<Assignment> => {
    return apiClient.post<Assignment>('/api/v1/assignments/', assignment);
  },

  // Update assignment supervisors
  updateSupervisors: (id: number, supervisorIds: number[]): Promise<{
    message: string;
    assignment: Assignment;
  }> => {
    return apiClient.put<{
      message: string;
      assignment: Assignment;
    }>(`/api/v1/assignments/${id}/supervisors`, supervisorIds);
  },

  // Get assignments for a specific employee
  getByEmployee: (employeeId: number): Promise<Assignment[]> => {
    return apiClient.get<Assignment[]>(`/api/v1/assignments/employee/${employeeId}`);
  },

  // Get assignments supervised by a specific employee
  getBySupervisor: (supervisorId: number): Promise<Assignment[]> => {
    return apiClient.get<Assignment[]>(`/api/v1/assignments/supervisor/${supervisorId}`);
  },
};