'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';
import { UserRole } from '@/lib/types';
import { apiClient } from '@/lib/api';
import { PageAccessRequest, PageAccessResponse } from '@/lib/types';

// Cache for page permissions to avoid redundant API calls
const permissionsCache = new Map<string, { data: PageAccessResponse; timestamp: number }>();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

interface EmployeeAccessResult {
  canAccess: boolean;
  canEdit: boolean;
  canView: boolean;
  isLoading: boolean;
  error?: string;
  permissions?: PageAccessResponse;
}

interface PagePermissionsResult {
  permissions: PageAccessResponse | null;
  isLoading: boolean;
  error?: string;
  refetch: () => void;
}

/**
 * Enhanced hook to check if current user can access a specific employee record.
 * Includes server-side validation to ensure permissions cannot be bypassed.
 */
export function useCanAccessEmployee(employeeId: number): EmployeeAccessResult {
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();
  const [result, setResult] = useState<EmployeeAccessResult>({
    canAccess: false,
    canEdit: false,
    canView: false,
    isLoading: true
  });

  useEffect(() => {
    const checkAccess = async () => {
      if (authLoading || !isAuthenticated || !user) {
        setResult({
          canAccess: false,
          canEdit: false,
          canView: false,
          isLoading: authLoading
        });
        return;
      }

      try {
        setResult(prev => ({ ...prev, isLoading: true, error: undefined }));

        // Check view permission for employee profile
        const viewRequest: PageAccessRequest = {
          page_identifier: "employees/view",
          resource_id: employeeId
        };

        const viewResponse = await apiClient.validatePageAccess(viewRequest);

        // Check edit permission for employee profile
        const editRequest: PageAccessRequest = {
          page_identifier: "employees/edit",
          resource_id: employeeId
        };

        const editResponse = await apiClient.validatePageAccess(editRequest);

        setResult({
          canAccess: viewResponse.access_granted,
          canView: viewResponse.permissions.can_view,
          canEdit: editResponse.permissions.can_edit,
          isLoading: false,
          permissions: viewResponse
        });

      } catch (error) {
        console.error('Failed to check employee access:', error);
        setResult({
          canAccess: false,
          canEdit: false,
          canView: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Access check failed'
        });
      }
    };

    checkAccess();
  }, [authLoading, isAuthenticated, user, employeeId]);

  return result;
}

/**
 * Enhanced hook to check if current user can edit a specific employee record.
 * Provides real-time permission checking with server-side validation.
 */
export function useCanEditEmployee(employeeId: number): {
  canEdit: boolean;
  isLoading: boolean;
  error?: string;
  permissions?: PageAccessResponse;
} {
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();
  const [state, setState] = useState({
    canEdit: false,
    isLoading: true,
    error: undefined as string | undefined,
    permissions: undefined as PageAccessResponse | undefined
  });

  useEffect(() => {
    const checkEditPermission = async () => {
      if (authLoading || !isAuthenticated || !user) {
        setState({
          canEdit: false,
          isLoading: authLoading,
          error: undefined,
          permissions: undefined
        });
        return;
      }

      try {
        setState(prev => ({ ...prev, isLoading: true, error: undefined }));

        const request: PageAccessRequest = {
          page_identifier: "employees/edit",
          resource_id: employeeId
        };

        const response = await apiClient.validatePageAccess(request);

        setState({
          canEdit: response.permissions.can_edit,
          isLoading: false,
          error: undefined,
          permissions: response
        });

      } catch (error) {
        console.error('Failed to check edit permission:', error);
        setState({
          canEdit: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Permission check failed',
          permissions: undefined
        });
      }
    };

    checkEditPermission();
  }, [authLoading, isAuthenticated, user, employeeId]);

  return state;
}

/**
 * Enhanced hook for checking page permissions with caching and server-side validation.
 * Updates when user roles or relationships change.
 */
export function usePagePermissionsWithCache(
  pageIdentifier: string, 
  resourceId?: number
): PagePermissionsResult {
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();
  const [state, setState] = useState<PagePermissionsResult>({
    permissions: null,
    isLoading: true,
    error: undefined,
    refetch: () => {}
  });

  const fetchPermissions = useCallback(async () => {
    if (authLoading || !isAuthenticated || !user) {
      setState(prev => ({
        ...prev,
        permissions: null,
        isLoading: authLoading,
        error: undefined
      }));
      return;
    }

    // Create cache key
    const cacheKey = `${pageIdentifier}:${resourceId || 'none'}:${user.user_id}`;
    
    // Check cache first
    const cached = permissionsCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setState(prev => ({
        ...prev,
        permissions: cached.data,
        isLoading: false,
        error: undefined
      }));
      return;
    }

    try {
      setState(prev => ({ ...prev, isLoading: true, error: undefined }));

      const request: PageAccessRequest = {
        page_identifier: pageIdentifier,
        resource_id: resourceId
      };

      const response = await apiClient.validatePageAccess(request);

      // Cache the response
      permissionsCache.set(cacheKey, {
        data: response,
        timestamp: Date.now()
      });

      setState(prev => ({
        ...prev,
        permissions: response,
        isLoading: false,
        error: undefined
      }));

    } catch (error) {
      console.error('Failed to fetch page permissions:', error);
      setState(prev => ({
        ...prev,
        permissions: null,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Permission fetch failed'
      }));
    }
  }, [authLoading, isAuthenticated, user, pageIdentifier, resourceId]);

  // Set up refetch function
  useEffect(() => {
    setState(prev => ({
      ...prev,
      refetch: fetchPermissions
    }));
  }, [fetchPermissions]);

  // Fetch permissions on mount and when dependencies change
  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  return state;
}

/**
 * Hook to check if current user can perform specific actions on a page.
 * Provides granular permission checking for UI elements.
 */
export function usePageActions(pageIdentifier: string, resourceId?: number) {
  const { permissions, isLoading, error, refetch } = usePagePermissionsWithCache(pageIdentifier, resourceId);

  return {
    canView: permissions?.permissions.can_view ?? false,
    canEdit: permissions?.permissions.can_edit ?? false,
    canCreate: permissions?.permissions.can_create ?? false,
    canDelete: permissions?.permissions.can_delete ?? false,
    isLoading,
    error,
    refetch,
    permissions
  };
}

/**
 * Hook to clear permissions cache (useful when user role changes)
 */
export function useClearPermissionsCache() {
  return useCallback(() => {
    permissionsCache.clear();
  }, []);
}

/**
 * Enhanced role checking hooks that include server-side validation
 */
export function useEnhancedRoleCheck() {
  const { user, isAuthenticated, isLoading } = useAuthStore();
  const clearCache = useClearPermissionsCache();

  return {
    // Basic role checks (client-side for UI performance)
    isHRAdmin: user?.roles?.includes(UserRole.HR_ADMIN) || false,
    isSupervisor: user?.roles?.includes(UserRole.SUPERVISOR) || false, 
    isEmployee: user?.roles?.includes(UserRole.EMPLOYEE) || false,
    userRoles: user?.roles || [],
    isAuthenticated,
    isLoading,

    // Server-validated permission checks
    useCanAccessEmployee,
    useCanEditEmployee,
    usePagePermissions: usePagePermissionsWithCache,
    usePageActions,

    // Cache management
    clearPermissionsCache: clearCache
  };
}

/**
 * Hook for conditional rendering based on user role and server-side validation.
 * Provides loading states and proper error handling.
 */
export function useConditionalRender(
  pageIdentifier: string,
  requiredPermission: 'view' | 'edit' | 'create' | 'delete',
  resourceId?: number
) {
  const { permissions, isLoading, error } = usePagePermissionsWithCache(pageIdentifier, resourceId);

  const hasPermission = permissions?.permissions && (() => {
    switch (requiredPermission) {
      case 'view': return permissions.permissions.can_view;
      case 'edit': return permissions.permissions.can_edit;
      case 'create': return permissions.permissions.can_create;
      case 'delete': return permissions.permissions.can_delete;
      default: return false;
    }
  })();

  return {
    shouldRender: hasPermission ?? false,
    isLoading,
    error,
    permissions
  };
}