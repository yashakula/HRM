/**
 * Navigation Access Hook
 * 
 * Provides hooks for checking page access and getting filtered navigation items
 * based on user permissions and roles.
 */

import { useMemo } from 'react';
import { useAuthStore } from '@/store/authStore';
import { 
  canAccessPage, 
  getAccessibleNavigation, 
  getPageConfig,
  NavigationItem,
  PageConfig 
} from '@/lib/pageConfig';

/**
 * Hook to check if current user can access a specific page
 */
export function useCanAccessPage(path: string): boolean {
  const { user } = useAuthStore();
  
  return useMemo(() => {
    if (!user) return false;
    
    const userPermissions = user.permissions || [];
    const userRoles = user.roles?.map(role => role.toString()) || [];
    
    return canAccessPage(path, userPermissions, userRoles);
  }, [path, user]);
}

/**
 * Hook to get page configuration for the current or specified path
 */
export function usePageConfig(path?: string): PageConfig | null {
  return useMemo(() => {
    if (!path) return null;
    return getPageConfig(path);
  }, [path]);
}

/**
 * Hook to get all navigation items accessible to the current user
 */
export function useAccessibleNavigation(): NavigationItem[] {
  const { user } = useAuthStore();
  
  return useMemo(() => {
    if (!user) return [];
    
    const userPermissions = user.permissions || [];
    const userRoles = user.roles?.map(role => role.toString()) || [];
    
    return getAccessibleNavigation(userPermissions, userRoles);
  }, [user]);
}

/**
 * Hook to get the default/home page for the current user
 * Based on their highest priority accessible page
 */
export function useUserHomePage(): string {
  const { user } = useAuthStore();
  
  return useMemo(() => {
    if (!user) return '/login';
    
    const userPermissions = user.permissions || [];
    const userRoles = user.roles?.map(role => role.toString()) || [];
    
    // Get accessible navigation items in order
    const accessibleItems = getAccessibleNavigation(userPermissions, userRoles);
    
    // Return the first accessible page, or profile as fallback
    if (accessibleItems.length > 0) {
      return accessibleItems[0].path;
    }
    
    // Fallback to profile since it's accessible to all authenticated users
    return '/profile';
  }, [user]);
}

/**
 * Hook to check if user should be redirected from current page
 * Useful for role-based redirects (e.g., employees going to profile instead of dashboard)
 */
export function usePageRedirect(currentPath: string): string | null {
  const { user } = useAuthStore();
  const canAccess = useCanAccessPage(currentPath);
  const homePage = useUserHomePage();
  
  return useMemo(() => {
    if (!user) return '/login';
    
    // If user can't access current page, redirect to their home page
    if (!canAccess && currentPath !== homePage) {
      return homePage;
    }
    
    return null;
  }, [user, canAccess, currentPath, homePage]);
}