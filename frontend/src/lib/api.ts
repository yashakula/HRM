// API client for HRM backend

import { 
  LoginCredentials, 
  LoginResponse, 
  User, 
  Employee, 
  EmployeeCreateRequest, 
  EmployeeSearchParams,
  ApiError 
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session-based auth
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        let errorMessage = 'An error occurred';
        try {
          const errorData: ApiError = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      // Handle empty responses (like logout)
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      } else {
        return {} as T;
      }
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication endpoints
  async login(credentials: LoginCredentials): Promise<LoginResponse> {
    return this.request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async logout(): Promise<void> {
    await this.request<void>('/api/v1/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/api/v1/auth/me');
  }

  // Employee endpoints
  async searchEmployees(params: EmployeeSearchParams): Promise<Employee[]> {
    const searchParams = new URLSearchParams();
    
    if (params.name) searchParams.append('name', params.name);
    if (params.employee_id) searchParams.append('employee_id', params.employee_id.toString());
    if (params.status) searchParams.append('status', params.status);
    if (params.skip) searchParams.append('skip', params.skip.toString());
    if (params.limit) searchParams.append('limit', params.limit.toString());

    const queryString = searchParams.toString();
    const endpoint = `/api/v1/employees/search${queryString ? `?${queryString}` : ''}`;
    
    return this.request<Employee[]>(endpoint);
  }

  async createEmployee(employee: EmployeeCreateRequest): Promise<Employee> {
    return this.request<Employee>('/api/v1/employees/', {
      method: 'POST',
      body: JSON.stringify(employee),
    });
  }

  async getEmployee(id: number): Promise<Employee> {
    return this.request<Employee>(`/api/v1/employees/${id}`);
  }

  async getAllEmployees(skip = 0, limit = 100): Promise<Employee[]> {
    return this.request<Employee[]>(`/api/v1/employees/?skip=${skip}&limit=${limit}`);
  }
}

export const apiClient = new ApiClient(API_BASE_URL);