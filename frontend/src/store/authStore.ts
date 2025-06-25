// Authentication store using Zustand

import { create } from 'zustand';
import { User, UserRole } from '@/lib/types';
import { apiClient } from '@/lib/api';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
}

type AuthStore = AuthState & AuthActions;

export const useAuthStore = create<AuthStore>((set) => ({
  // Initial state
  user: null,
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
      
      set({ 
        user, 
        isAuthenticated: true, 
        isLoading: false,
        error: null 
      });
    } catch (error) {
      set({ 
        user: null, 
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
      set({ 
        user, 
        isAuthenticated: true, 
        isLoading: false 
      });
    } catch {
      set({ 
        user: null, 
        isAuthenticated: false, 
        isLoading: false,
        error: null // Don't set error for auth check failure
      });
    }
  },

  clearError: () => {
    set({ error: null });
  },
}));

// Helper functions for role-based access
export const useUserRole = (): UserRole | null => {
  const user = useAuthStore(state => state.user);
  return user?.role || null;
};

export const useHasRole = (requiredRole: UserRole): boolean => {
  const user = useAuthStore(state => state.user);
  return user?.role === requiredRole;
};

export const useIsHRAdmin = (): boolean => {
  return useHasRole(UserRole.HR_ADMIN);
};

export const useIsSupervisor = (): boolean => {
  return useHasRole(UserRole.SUPERVISOR);
};

export const useIsEmployee = (): boolean => {
  return useHasRole(UserRole.EMPLOYEE);
};