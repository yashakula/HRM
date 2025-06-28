// Authentication store using Zustand

import { create } from 'zustand';
import { User, UserRole } from '@/lib/types';
import { apiClient } from '@/lib/api';

interface AuthState {
  user: User | null;
  permissions: string[]; // User's current permissions
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  hasPermission: (permission: string) => boolean;
  hasAnyPermission: (permissions: string[]) => boolean;
  hasAllPermissions: (permissions: string[]) => boolean;
  refreshPermissions: () => Promise<void>;
  getRolePermissions: (role: UserRole) => string[];
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>((set, get) => ({
  // Initial state
  user: null,
  permissions: [],
  isAuthenticated: false,
  isLoading: false,
  error: null,

  // Actions
  login: async (username: string, password: string) => {
    set({ isLoading: true, error: null });
    
    try {
      await apiClient.login({ username, password });
      
      // Get full user details
      const user = await apiClient.getCurrentUser();
      
      // Extract permissions from user object or set defaults based on role
      const permissions = user.permissions || get().getRolePermissions(user.role);
      
      set({ 
        user, 
        permissions,
        isAuthenticated: true, 
        isLoading: false,
        error: null 
      });
    } catch (error) {
      set({ 
        user: null, 
        permissions: [],
        isAuthenticated: false, 
        isLoading: false,
        error: error instanceof Error ? error.message : 'Login failed'
      });
      throw error;
    }
  },

  logout: async () => {
    set({ isLoading: true });
    
    try {
      await apiClient.logout();
    } catch {
      // Ignore logout errors
    } finally {
      set({ 
        user: null, 
        permissions: [],
        isAuthenticated: false, 
        isLoading: false,
        error: null 
      });
    }
  },

  checkAuth: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const user = await apiClient.getCurrentUser();
      
      // Extract permissions from user object or set defaults based on role
      const permissions = user.permissions || get().getRolePermissions(user.role);
      
      set({ 
        user, 
        permissions,
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch {
      set({ 
        user: null, 
        permissions: [],
        isAuthenticated: false, 
        isLoading: false,
        error: null // Don't set error for auth check failure
      });
    }
  },

  clearError: () => {
    set({ error: null });
  },

  // Permission checking functions
  hasPermission: (permission: string): boolean => {
    const { permissions } = get();
    return permissions.includes(permission);
  },

  hasAnyPermission: (requiredPermissions: string[]): boolean => {
    const { permissions } = get();
    return requiredPermissions.some(permission => permissions.includes(permission));
  },

  hasAllPermissions: (requiredPermissions: string[]): boolean => {
    const { permissions } = get();
    return requiredPermissions.every(permission => permissions.includes(permission));
  },

  refreshPermissions: async (): Promise<void> => {
    const { user } = get();
    if (!user) return;

    try {
      // Try to fetch updated user data with permissions
      const updatedUser = await apiClient.getCurrentUser();
      const permissions = updatedUser.permissions || get().getRolePermissions(updatedUser.role);
      
      set({ 
        user: updatedUser, 
        permissions 
      });
    } catch (error) {
      console.error('Failed to refresh permissions:', error);
    }
  },

  // Helper function to get default permissions based on role
  getRolePermissions: (role: UserRole): string[] => {
    switch (role) {
      case UserRole.HR_ADMIN:
        return [
          // Employee permissions
          'employee.create',
          'employee.read.all',
          'employee.update.all',
          'employee.delete',
          // Assignment permissions
          'assignment.create',
          'assignment.read.all', 
          'assignment.update.all',
          'assignment.delete',
          'assignment.manage_supervisors',
          // Department permissions
          'department.create',
          'department.read.all',
          'department.update',
          'department.delete',
          // Assignment type permissions
          'assignment_type.create',
          'assignment_type.read.all',
          'assignment_type.update',
          'assignment_type.delete',
          // Leave request permissions
          'leave_request.create.all',
          'leave_request.read.all',
          'leave_request.approve.all',
          // System permissions
          'system.manage_users',
          'system.access_reports'
        ];
      case UserRole.SUPERVISOR:
        return [
          // Employee permissions (supervised scope)
          'employee.read.supervised',
          'employee.read.own',
          // Assignment permissions (supervised scope)
          'assignment.read.supervised',
          'assignment.read.own',
          // Department permissions (read only)
          'department.read.all',
          // Assignment type permissions (read only)
          'assignment_type.read.all',
          // Leave request permissions
          'leave_request.create.own',
          'leave_request.read.supervised',
          'leave_request.read.own',
          'leave_request.approve.supervised'
        ];
      case UserRole.EMPLOYEE:
        return [
          // Employee permissions (own only)
          'employee.read.own',
          // Assignment permissions (own only)
          'assignment.read.own',
          // Department permissions (read only)
          'department.read.all',
          // Assignment type permissions (read only)
          'assignment_type.read.all',
          // Leave request permissions
          'leave_request.create.own',
          'leave_request.read.own'
        ];
      default:
        return [];
    }
  },
}));

// Helper functions for role-based access (DEPRECATED - use permission-based functions)
export const useUserRole = (): UserRole | null => {
  const user = useAuthStore(state => state.user);
  return user?.role || null;
};

export const useHasRole = (requiredRole: UserRole): boolean => {
  const user = useAuthStore(state => state.user);
  return user?.role === requiredRole;
};

// DEPRECATED: Use permission-based functions instead
export const useIsHRAdmin = (): boolean => {
  return useHasRole(UserRole.HR_ADMIN);
};

// DEPRECATED: Use permission-based functions instead
export const useIsSupervisor = (): boolean => {
  return useHasRole(UserRole.SUPERVISOR);
};

// DEPRECATED: Use permission-based functions instead
export const useIsEmployee = (): boolean => {
  return useHasRole(UserRole.EMPLOYEE);
};

// NEW: Permission-based helper functions
export const usePermissions = (): string[] => {
  return useAuthStore(state => state.permissions);
};

export const useHasPermission = (permission: string): boolean => {
  return useAuthStore(state => state.hasPermission(permission));
};

export const useHasAnyPermission = (permissions: string[]): boolean => {
  return useAuthStore(state => state.hasAnyPermission(permissions));
};

export const useHasAllPermissions = (permissions: string[]): boolean => {
  return useAuthStore(state => state.hasAllPermissions(permissions));
};

// Convenience hooks for common permission checks
export const useCanCreateEmployee = (): boolean => {
  return useHasPermission('employee.create');
};

export const useCanReadAllEmployees = (): boolean => {
  return useHasPermission('employee.read.all');
};

export const useCanUpdateEmployee = (): boolean => {
  return useHasAnyPermission(['employee.update.all', 'employee.update.own']);
};

export const useCanCreateAssignment = (): boolean => {
  return useHasPermission('assignment.create');
};

export const useCanManageDepartments = (): boolean => {
  return useHasAnyPermission(['department.create', 'department.update', 'department.delete']);
};

export const useCanApproveLeaveRequests = (): boolean => {
  return useHasAnyPermission(['leave_request.approve.all', 'leave_request.approve.supervised']);
};