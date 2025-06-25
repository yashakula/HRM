import { apiClient } from '../api';

export interface AssignmentTypeSimple {
  assignment_type_id: number;
  description: string;
  department_id: number;
  created_at: string;
  updated_at: string;
}

export interface Department {
  department_id: number;
  name: string;
  description?: string;
  assignment_types: AssignmentTypeSimple[];
}

export interface DepartmentCreate {
  name: string;
  description?: string;
  assignment_types?: string[];  // List of assignment type descriptions to create
}

export interface DepartmentUpdate {
  name?: string;
  description?: string;
  assignment_types_to_add?: string[];  // Assignment type descriptions to add
  assignment_types_to_remove?: number[];  // Assignment type IDs to remove
}

export const departmentApi = {
  // Get all departments
  getAll: (): Promise<Department[]> => {
    return apiClient.get<Department[]>('/api/v1/departments/');
  },

  // Get department by ID
  getById: (id: number): Promise<Department> => {
    return apiClient.get<Department>(`/api/v1/departments/${id}`);
  },

  // Create new department
  create: (department: DepartmentCreate): Promise<Department> => {
    return apiClient.post<Department>('/api/v1/departments/', department);
  },

  // Update department
  update: (id: number, department: DepartmentUpdate): Promise<Department> => {
    return apiClient.put<Department>(`/api/v1/departments/${id}`, department);
  },

  // Delete department
  delete: (id: number): Promise<{ message: string }> => {
    return apiClient.delete<{ message: string }>(`/api/v1/departments/${id}`);
  },
};