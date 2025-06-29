/**
 * Admin API client for RBAC management functions
 */

import { UserRole } from '@/lib/types';


export interface AdminUser {
  user_id: number;
  username: string;
  email: string;
  roles: UserRole[];  // Changed from role: string to roles: UserRole[]
  permissions: string[];
  is_active: boolean;
  created_at: string;
  employee?: {
    employee_id: number;
    status: string;
    work_email: string;
    person: {
      full_name: string;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  };
}

export interface RolePermissions {
  role: string;
  permissions: string[];
  permission_count: number;
  permission_groups: Record<string, string[]>;
}

export interface UserRoleDistribution {
  total_active_users: number;
  role_distribution: Array<{
    role: string;
    user_count: number;
    percentage: number;
  }>;
  roles_available: string[];
}

export interface PermissionUsageAnalytics {
  permission_analytics: Array<{
    permission: string;
    total_users: number;
    roles_with_permission: Array<{
      role: string;
      user_count: number;
    }>;
  }>;
  total_unique_permissions: number;
  role_user_counts: Record<string, number>;
}

export interface SystemHealth {
  total_users: number;
  active_users: number;
  inactive_users: number;
  total_employees: number;
  recent_users_30d: number;
  permission_system: {
    total_roles: number;
    total_permissions: number;
    avg_permissions_per_role: number;
  };
  timestamp: string;
}

// API base URL configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function for API requests
async function adminRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  
  return await response.json();
}

export const adminApi = {
  // User Management
  async listUsers(params: {
    skip?: number;
    limit?: number;
    role_filter?: string;
  } = {}): Promise<AdminUser[]> {
    const searchParams = new URLSearchParams();
    if (params.skip !== undefined) searchParams.set('skip', params.skip.toString());
    if (params.limit !== undefined) searchParams.set('limit', params.limit.toString());
    if (params.role_filter) searchParams.set('role_filter', params.role_filter);

    const url = `/api/v1/admin/users${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    return adminRequest<AdminUser[]>(url);
  },

  async updateUserRole(userId: number, newRole: string): Promise<{
    message: string;
    user_id: number;
    old_role: string;
    new_role: string;
    updated_by: string;
  }> {
    return adminRequest(`/api/v1/admin/users/${userId}/role`, {
      method: 'PUT',
      body: JSON.stringify({ new_role: newRole }),
    });
  },

  async getUserPermissions(userId: number): Promise<{
    user_id: number;
    username: string;
    role: string;
    permissions: string[];
    permission_count: number;
  }> {
    return adminRequest(`/api/v1/admin/users/${userId}/permissions`);
  },

  // Permission Management
  async listPermissions(): Promise<{
    total_permissions: number;
    permission_groups: Record<string, string[]>;
    all_permissions: string[];
  }> {
    return adminRequest('/api/v1/admin/permissions');
  },

  async getRolePermissions(role: string): Promise<RolePermissions> {
    return adminRequest(`/api/v1/admin/roles/${role}/permissions`);
  },

  // Audit and Analytics
  async getUserRoleDistribution(): Promise<UserRoleDistribution> {
    return adminRequest('/api/v1/admin/audit/user-roles');
  },

  async getPermissionUsageAnalytics(): Promise<PermissionUsageAnalytics> {
    return adminRequest('/api/v1/admin/audit/permission-usage');
  },

  async getSystemHealth(): Promise<SystemHealth> {
    return adminRequest('/api/v1/admin/system/health');
  },
};