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
  hasRole: (role: UserRole) => boolean;
  hasAnyRole: (roles: UserRole[]) => boolean;
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
      
      // Extract permissions from user object (now required in multi-role system)
      const permissions = user.permissions || [];
      
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
      
      // Extract permissions from user object (now required in multi-role system)
      const permissions = user.permissions || [];
      
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
      const permissions = updatedUser.permissions || [];
      
      set({ 
        user: updatedUser, 
        permissions 
      });
    } catch (error) {
      console.error('Failed to refresh permissions:', error);
    }
  },

  // Multi-role checking functions
  hasRole: (role: UserRole): boolean => {
    const { user } = get();
    return user?.roles?.includes(role) || false;
  },

  hasAnyRole: (roles: UserRole[]): boolean => {
    const { user } = get();
    if (!user?.roles) return false;
    return roles.some(role => user.roles.includes(role));
  },
}));

// Helper functions for multi-role access
export const useUserRoles = (): UserRole[] => {
  const user = useAuthStore(state => state.user);
  return user?.roles || [];
};

export const useHasRole = (requiredRole: UserRole): boolean => {
  const hasRole = useAuthStore(state => state.hasRole);
  return hasRole(requiredRole);
};

export const useHasAnyRole = (requiredRoles: UserRole[]): boolean => {
  const hasAnyRole = useAuthStore(state => state.hasAnyRole);
  return hasAnyRole(requiredRoles);
};

// Helper functions for specific role checks
export const useIsHRAdmin = (): boolean => {
  return useHasRole(UserRole.HR_ADMIN);
};

export const useIsSupervisor = (): boolean => {
  return useHasRole(UserRole.SUPERVISOR);
};

export const useIsEmployee = (): boolean => {
  return useHasRole(UserRole.EMPLOYEE);
};

export const useIsSuperUser = (): boolean => {
  return useHasRole(UserRole.SUPER_USER);
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