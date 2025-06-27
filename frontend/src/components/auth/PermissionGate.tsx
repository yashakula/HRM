'use client';

import { usePagePermissions } from './ProtectedRoute';

interface PermissionGateProps {
  children: React.ReactNode;
  pageIdentifier: string;
  resourceId?: number;
  requiredPermission: 'view' | 'edit' | 'create' | 'delete';
  fallback?: React.ReactNode;
}

/**
 * Component that conditionally renders children based on user permissions.
 * Use this for hiding/showing UI elements like buttons, forms, etc.
 */
export default function PermissionGate({
  children,
  pageIdentifier,
  resourceId,
  requiredPermission,
  fallback = null
}: PermissionGateProps) {
  const { permissions, isLoading } = usePagePermissions(pageIdentifier, resourceId);

  // Don't render anything while loading
  if (isLoading) {
    return null;
  }

  // Check if user has required permission
  const hasPermission = permissions?.permissions && (() => {
    switch (requiredPermission) {
      case 'view': return permissions.permissions.can_view;
      case 'edit': return permissions.permissions.can_edit;
      case 'create': return permissions.permissions.can_create;
      case 'delete': return permissions.permissions.can_delete;
      default: return false;
    }
  })();

  // Render children if permission granted, fallback otherwise
  return hasPermission ? <>{children}</> : <>{fallback}</>;
}

// Additional hooks for common permission checks
export function useCanView(pageIdentifier: string, resourceId?: number): boolean {
  const { permissions } = usePagePermissions(pageIdentifier, resourceId);
  return permissions?.permissions.can_view ?? false;
}

export function useCanEdit(pageIdentifier: string, resourceId?: number): boolean {
  const { permissions } = usePagePermissions(pageIdentifier, resourceId);
  return permissions?.permissions.can_edit ?? false;
}

export function useCanCreate(pageIdentifier: string, resourceId?: number): boolean {
  const { permissions } = usePagePermissions(pageIdentifier, resourceId);
  return permissions?.permissions.can_create ?? false;
}

export function useCanDelete(pageIdentifier: string, resourceId?: number): boolean {
  const { permissions } = usePagePermissions(pageIdentifier, resourceId);
  return permissions?.permissions.can_delete ?? false;
}