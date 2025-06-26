import { apiClient } from '../api';
import { 
  Assignment, 
  AssignmentCreateRequest, 
  AssignmentUpdateRequest, 
  SupervisorAssignmentCreate
} from '../types';

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
  create: (assignment: AssignmentCreateRequest): Promise<Assignment> => {
    return apiClient.post<Assignment>('/api/v1/assignments/', assignment);
  },

  // Update assignment
  update: (id: number, assignment: AssignmentUpdateRequest): Promise<Assignment> => {
    return apiClient.put<Assignment>(`/api/v1/assignments/${id}`, assignment);
  },

  // Delete assignment
  delete: (id: number): Promise<{ detail: string }> => {
    return apiClient.delete<{ detail: string }>(`/api/v1/assignments/${id}`);
  },

  // Set assignment as primary
  setPrimary: (id: number): Promise<Assignment> => {
    return apiClient.put<Assignment>(`/api/v1/assignments/${id}/primary`, {});
  },

  // Get assignment supervisors
  getSupervisors: (id: number): Promise<{ supervisor_id: number; assignment_id: number; effective_start_date: string; effective_end_date?: string }[]> => {
    return apiClient.get<{ supervisor_id: number; assignment_id: number; effective_start_date: string; effective_end_date?: string }[]>(`/api/v1/assignments/${id}/supervisors`);
  },

  // Add supervisor to assignment
  addSupervisor: (id: number, supervisor: SupervisorAssignmentCreate): Promise<Assignment> => {
    return apiClient.post<Assignment>(`/api/v1/assignments/${id}/supervisors`, supervisor);
  },

  // Remove supervisor from assignment
  removeSupervisor: (id: number, supervisorId: number): Promise<{ detail: string }> => {
    return apiClient.delete<{ detail: string }>(`/api/v1/assignments/${id}/supervisors/${supervisorId}`);
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