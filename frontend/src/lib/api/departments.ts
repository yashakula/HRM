import { apiClient } from '../api';

export interface Department {
  department_id: number;
  name: string;
  description?: string;
}

export interface DepartmentCreate {
  name: string;
  description?: string;
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
  update: (id: number, department: DepartmentCreate): Promise<Department> => {
    return apiClient.put<Department>(`/api/v1/departments/${id}`, department);
  },

  // Delete department
  delete: (id: number): Promise<{ message: string }> => {
    return apiClient.delete<{ message: string }>(`/api/v1/departments/${id}`);
  },
};