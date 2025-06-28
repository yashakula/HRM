'use client';

import React from 'react';
import { useAuthStore } from '@/store/authStore';

interface PermissionGuardProps {
  /** Single permission to check */
  permission?: string;
  /** Multiple permissions to check */
  permissions?: string[];
  /** Whether to require ALL permissions (default) or ANY permission */
  requireAll?: boolean;
  /** Content to render when user has permission */
  children: React.ReactNode;
  /** Content to render when user lacks permission */
  fallback?: React.ReactNode;
  /** Show loading state while checking permissions */
  showLoading?: boolean;
}

/**
 * Component that conditionally renders children based on user permissions.
 * Uses the permission-based system from the auth store.
 * 
 * Examples:
 * - Single permission: <PermissionGuard permission="employee.create">...</PermissionGuard>
 * - Multiple permissions (ALL): <PermissionGuard permissions={["employee.read", "employee.update"]}>...</PermissionGuard>
 * - Multiple permissions (ANY): <PermissionGuard permissions={["employee.read.all", "employee.read.own"]} requireAll={false}>...</PermissionGuard>
 */
export default function PermissionGuard({
  permission,
  permissions,
  requireAll = true,
  children,
  fallback = null,
  showLoading = false
}: PermissionGuardProps) {
  const { 
    isAuthenticated, 
    isLoading, 
    hasPermission, 
    hasAnyPermission, 
    hasAllPermissions 
  } = useAuthStore();

  // Show loading state if requested and auth is loading
  if (showLoading && isLoading) {
    return (
      <div className="inline-flex items-center">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
        <span className="ml-2 text-sm text-gray-500">Loading...</span>
      </div>
    );
  }

  // Must be authenticated to have any permissions
  if (!isAuthenticated) {
    return <>{fallback}</>;
  }

  // Determine if user has required permission(s)
  let hasRequiredPermissions = false;

  if (permission) {
    // Single permission check
    hasRequiredPermissions = hasPermission(permission);
  } else if (permissions && permissions.length > 0) {
    // Multiple permission check
    hasRequiredPermissions = requireAll 
      ? hasAllPermissions(permissions)
      : hasAnyPermission(permissions);
  } else {
    // No permissions specified - default to showing content for authenticated users
    hasRequiredPermissions = true;
  }

  // Render children if permission granted, fallback otherwise
  return hasRequiredPermissions ? <>{children}</> : <>{fallback}</>;
}

// Higher-order component version for wrapping entire components
export function withPermissionGuard<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  guardProps: Pick<PermissionGuardProps, 'permission' | 'permissions' | 'requireAll' | 'fallback'>
) {
  const ComponentWithPermission = (props: P) => (
    <PermissionGuard {...guardProps}>
      <WrappedComponent {...props} />
    </PermissionGuard>
  );

  ComponentWithPermission.displayName = `withPermissionGuard(${WrappedComponent.displayName || WrappedComponent.name})`;
  return ComponentWithPermission;
}

// Convenience components for common permission patterns
export function CreateGuard({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGuard permission="employee.create" fallback={fallback}>
      {children}
    </PermissionGuard>
  );
}

export function AdminGuard({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGuard 
      permissions={["employee.read.all", "employee.update.all", "employee.create"]} 
      requireAll={false}
      fallback={fallback}
    >
      {children}
    </PermissionGuard>
  );
}

export function SupervisorGuard({ children, fallback }: { children: React.ReactNode; fallback?: React.ReactNode }) {
  return (
    <PermissionGuard 
      permissions={["employee.read.supervised", "leave_request.approve.supervised"]} 
      requireAll={false}
      fallback={fallback}
    >
      {children}
    </PermissionGuard>
  );
}

// Hook versions for functional components that need conditional logic
export function useHasPermissionGuard(permission: string): boolean {
  const { isAuthenticated, hasPermission } = useAuthStore();
  return isAuthenticated && hasPermission(permission);
}

export function useHasAnyPermissionGuard(permissions: string[]): boolean {
  const { isAuthenticated, hasAnyPermission } = useAuthStore();
  return isAuthenticated && hasAnyPermission(permissions);
}

export function useHasAllPermissionsGuard(permissions: string[]): boolean {
  const { isAuthenticated, hasAllPermissions } = useAuthStore();
  return isAuthenticated && hasAllPermissions(permissions);
}