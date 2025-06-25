import { apiClient } from '../api';
import { Department } from './departments';

export interface AssignmentType {
  assignment_type_id: number;
  description: string;
  department_id: number;
  created_at: string;
  updated_at: string;
  department: Department;
}

export interface AssignmentTypeCreate {
  description: string;
  department_id: number;
}

export const assignmentTypeApi = {
  // Get all assignment types
  getAll: (departmentId?: number): Promise<AssignmentType[]> => {
    const params = departmentId ? `?department_id=${departmentId}` : '';
    return apiClient.get<AssignmentType[]>(`/api/v1/assignment-types${params}`);
  },

  // Get assignment type by ID
  getById: (id: number): Promise<AssignmentType> => {
    return apiClient.get<AssignmentType>(`/api/v1/assignment-types/${id}`);
  },

  // Create new assignment type
  create: (assignmentType: AssignmentTypeCreate): Promise<AssignmentType> => {
    return apiClient.post<AssignmentType>('/api/v1/assignment-types/', assignmentType);
  },

  // Update assignment type
  update: (id: number, assignmentType: AssignmentTypeCreate): Promise<AssignmentType> => {
    return apiClient.put<AssignmentType>(`/api/v1/assignment-types/${id}`, assignmentType);
  },

  // Delete assignment type
  delete: (id: number): Promise<{ message: string }> => {
    return apiClient.delete<{ message: string }>(`/api/v1/assignment-types/${id}`);
  },
};