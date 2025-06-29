'use client';

import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { apiClient } from '@/lib/api';
import { PageAccessRequest, PageAccessResponse } from '@/lib/types';

interface PageAccessState {
  isLoading: boolean;
  accessGranted: boolean;
  canView: boolean;
  canEdit: boolean;
  canCreate: boolean;
  canDelete: boolean;
  permissions?: PageAccessResponse;
  error?: string;
}

/**
 * Hook that combines granular permission checking with page-based access validation.
 * Provides both local permission checks and server-side validation.
 */
export function usePageAccess(
  pageIdentifier: string, 
  resourceId?: number,
  localPermissions?: string[]
): PageAccessState {
  const { 
    isAuthenticated, 
    isLoading: authLoading, 
    hasAnyPermission 
  } = useAuthStore();
  
  const [pageAccessState, setPageAccessState] = useState<PageAccessState>({
    isLoading: true,
    accessGranted: false,
    canView: false,
    canEdit: false,
    canCreate: false,
    canDelete: false
  });

  useEffect(() => {
    const validatePageAccess = async () => {
      // Wait for auth to complete
      if (authLoading) return;

      // No access if not authenticated
      if (!isAuthenticated) {
        setPageAccessState({
          isLoading: false,
          accessGranted: false,
          canView: false,
          canEdit: false,
          canCreate: false,
          canDelete: false
        });
        return;
      }

      try {
        setPageAccessState(prev => ({ ...prev, isLoading: true }));

        // First, check local permissions if provided
        let hasLocalPermissions = true;
        if (localPermissions && localPermissions.length > 0) {
          hasLocalPermissions = hasAnyPermission(localPermissions);
        }

        // If local permissions fail, short-circuit
        if (!hasLocalPermissions) {
          setPageAccessState({
            isLoading: false,
            accessGranted: false,
            canView: false,
            canEdit: false,
            canCreate: false,
            canDelete: false,
            error: 'Insufficient local permissions'
          });
          return;
        }

        // Validate with server for resource-specific access
        const request: PageAccessRequest = {
          page_identifier: pageIdentifier,
          resource_id: resourceId
        };

        const response = await apiClient.validatePageAccess(request);

        setPageAccessState({
          isLoading: false,
          accessGranted: response.access_granted,
          canView: response.permissions.can_view,
          canEdit: response.permissions.can_edit,
          canCreate: response.permissions.can_create,
          canDelete: response.permissions.can_delete,
          permissions: response
        });

      } catch (error) {
        console.error('Page access validation failed:', error);
        setPageAccessState({
          isLoading: false,
          accessGranted: false,
          canView: false,
          canEdit: false,
          canCreate: false,
          canDelete: false,
          error: error instanceof Error ? error.message : 'Access validation failed'
        });
      }
    };

    validatePageAccess();
  }, [authLoading, isAuthenticated, pageIdentifier, resourceId, localPermissions, hasAnyPermission]);

  return pageAccessState;
}

/**
 * Hook for simple permission checking without server validation.
 * Uses only the granular permissions from the auth store.
 */
export function useLocalPermissionCheck(permissions: string[], requireAll = false): boolean {
  const { isAuthenticated, hasPermission, hasAnyPermission, hasAllPermissions } = useAuthStore();

  if (!isAuthenticated) return false;

  if (permissions.length === 1) {
    return hasPermission(permissions[0]);
  }

  return requireAll ? hasAllPermissions(permissions) : hasAnyPermission(permissions);
}

/**
 * Hook that checks if user can perform specific actions based on permissions.
 * Maps action types to permission patterns.
 */
export function useActionPermissions(resource: string) {
  const { hasPermission, hasAnyPermission } = useAuthStore();

  const canCreate = () => hasPermission(`${resource}.create`);
  
  const canRead = () => hasAnyPermission([
    `${resource}.read.all`,
    `${resource}.read.supervised`, 
    `${resource}.read.own`
  ]);
  
  const canUpdate = () => hasAnyPermission([
    `${resource}.update.all`,
    `${resource}.update.supervised`,
    `${resource}.update.own`
  ]);
  
  const canDelete = () => hasPermission(`${resource}.delete`);

  const canReadAll = () => hasPermission(`${resource}.read.all`);
  
  const canUpdateAll = () => hasPermission(`${resource}.update.all`);

  return {
    canCreate,
    canRead,
    canUpdate,
    canDelete,
    canReadAll,
    canUpdateAll
  };
}

/**
 * Hook for common employee-related permission checks.
 */
export function useEmployeePermissions() {
  return useActionPermissions('employee');
}

/**
 * Hook for common assignment-related permission checks.
 */
export function useAssignmentPermissions() {
  return useActionPermissions('assignment');
}

/**
 * Hook for common leave request permission checks.
 */
export function useLeaveRequestPermissions() {
  const { hasPermission, hasAnyPermission } = useAuthStore();

  return {
    canCreate: () => hasAnyPermission(['leave_request.create.all', 'leave_request.create.own']),
    canRead: () => hasAnyPermission(['leave_request.read.all', 'leave_request.read.supervised', 'leave_request.read.own']),
    canApprove: () => hasAnyPermission(['leave_request.approve.all', 'leave_request.approve.supervised']),
    canReadAll: () => hasPermission('leave_request.read.all'),
    canApproveAll: () => hasPermission('leave_request.approve.all')
  };
}

/**
 * Hook for department and assignment type permission checks.
 */
export function useDepartmentPermissions() {
  const { hasPermission, hasAnyPermission } = useAuthStore();

  return {
    canCreate: () => hasPermission('department.create'),
    canRead: () => hasPermission('department.read'),
    canUpdate: () => hasPermission('department.update'),
    canDelete: () => hasPermission('department.delete'),
    canManage: () => hasAnyPermission(['department.create', 'department.update', 'department.delete'])
  };
}