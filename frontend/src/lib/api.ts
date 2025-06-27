// API client for HRM backend

import { 
  LoginCredentials, 
  LoginResponse, 
  User, 
  Employee, 
  EmployeeCreateRequest,
  EmployeeUpdateRequest,
  EmployeeSearchParams,
  PageAccessRequest,
  PageAccessResponse,
  LeaveRequest,
  LeaveRequestCreateRequest,
  LeaveRequestUpdateRequest,
  Assignment,
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

  async validatePageAccess(request: PageAccessRequest): Promise<PageAccessResponse> {
    return this.request<PageAccessResponse>('/api/v1/auth/validate-page-access', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Generic HTTP methods
  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint);
  }

  async post<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async put<T>(endpoint: string, data?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'DELETE',
    });
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

  async updateEmployee(id: number, employee: EmployeeUpdateRequest): Promise<Employee> {
    return this.request<Employee>(`/api/v1/employees/${id}`, {
      method: 'PUT',
      body: JSON.stringify(employee),
    });
  }

  async getSupervisees(): Promise<Employee[]> {
    return this.request<Employee[]>('/api/v1/employees/supervisees');
  }

  // Leave Request endpoints
  async createLeaveRequest(leaveRequest: LeaveRequestCreateRequest): Promise<LeaveRequest> {
    return this.request<LeaveRequest>('/api/v1/leave-requests/', {
      method: 'POST',
      body: JSON.stringify(leaveRequest),
    });
  }

  async getLeaveRequests(status?: string): Promise<LeaveRequest[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    
    const endpoint = `/api/v1/leave-requests/${params.toString() ? `?${params.toString()}` : ''}`;
    return this.request<LeaveRequest[]>(endpoint);
  }

  async getMyLeaveRequests(): Promise<LeaveRequest[]> {
    return this.request<LeaveRequest[]>('/api/v1/leave-requests/my-requests');
  }

  async getPendingApprovals(): Promise<LeaveRequest[]> {
    return this.request<LeaveRequest[]>('/api/v1/leave-requests/pending-approvals');
  }

  async getLeaveRequest(id: number): Promise<LeaveRequest> {
    return this.request<LeaveRequest>(`/api/v1/leave-requests/${id}`);
  }

  async updateLeaveRequest(id: number, update: LeaveRequestUpdateRequest): Promise<LeaveRequest> {
    return this.request<LeaveRequest>(`/api/v1/leave-requests/${id}`, {
      method: 'PUT',
      body: JSON.stringify(update),
    });
  }

  async getEmployeeActiveAssignments(employeeId: number): Promise<Assignment[]> {
    return this.request<Assignment[]>(`/api/v1/leave-requests/assignments/${employeeId}/active`);
  }
}

export const apiClient = new ApiClient(API_BASE_URL);