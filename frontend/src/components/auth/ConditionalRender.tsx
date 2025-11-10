'use client';

import { ReactNode } from 'react';
import { useConditionalRender, usePageActions } from '@/hooks/useEnhancedRoleChecking';

interface ConditionalRenderProps {
  children: ReactNode;
  pageIdentifier: string;
  requiredPermission: 'view' | 'edit' | 'create' | 'delete';
  resourceId?: number;
  fallback?: ReactNode;
  showLoadingState?: boolean;
  loadingComponent?: ReactNode;
}

/**
 * Component for conditionally rendering UI elements based on server-validated permissions.
 * Ensures sensitive elements are not present in DOM for unauthorized users.
 */
export function ConditionalRender({
  children,
  pageIdentifier,
  requiredPermission,
  resourceId,
  fallback = null,
  showLoadingState = false,
  loadingComponent
}: ConditionalRenderProps) {
  const { shouldRender, isLoading, error } = useConditionalRender(
    pageIdentifier,
    requiredPermission,
    resourceId
  );

  // Show loading state if requested
  if (isLoading && showLoadingState) {
    return loadingComponent ? (
      <>{loadingComponent}</>
    ) : (
      <div className="animate-pulse bg-gray-200 h-4 w-20 rounded"></div>
    );
  }

  // Don't render anything if there's an error or no permission
  if (error || !shouldRender) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}

interface SensitiveFieldProps {
  children: ReactNode;
  fieldType: 'ssn' | 'bank_account' | 'personal_info' | 'salary' | 'admin_only';
  employeeId?: number;
  fallback?: ReactNode;
}

/**
 * Component that hides sensitive form fields based on user permissions.
 * Ensures sensitive data fields are not even present in DOM for unauthorized users.
 */
export function SensitiveField({
  children,
  fieldType,
  employeeId,
  fallback = null
}: SensitiveFieldProps) {
  // Map field types to permission requirements
  const getPermissionRequirement = () => {
    switch (fieldType) {
      case 'ssn':
      case 'bank_account':
        // Only HR_ADMIN or resource owner can see sensitive financial/identity data
        return {
          pageIdentifier: employeeId ? 'employees/view' : 'employees/create',
          resourceId: employeeId,
          requiredPermission: 'view' as const
        };
      case 'personal_info':
        // Personal information accessible to owner and HR_ADMIN
        return {
          pageIdentifier: employeeId ? 'employees/view' : 'employees/create',
          resourceId: employeeId,
          requiredPermission: 'view' as const
        };
      case 'salary':
        // Salary information - HR_ADMIN only
        return {
          pageIdentifier: 'employees/create', // This will restrict to HR_ADMIN
          requiredPermission: 'create' as const
        };
      case 'admin_only':
        // Admin-only fields
        return {
          pageIdentifier: 'employees/create',
          requiredPermission: 'create' as const
        };
      default:
        return {
          pageIdentifier: 'employees',
          requiredPermission: 'view' as const
        };
    }
  };

  const permissionConfig = getPermissionRequirement();

  return (
    <ConditionalRender
      pageIdentifier={permissionConfig.pageIdentifier}
      requiredPermission={permissionConfig.requiredPermission}
      resourceId={permissionConfig.resourceId}
      fallback={fallback}
    >
      {children}
    </ConditionalRender>
  );
}

interface ActionButtonProps {
  children: ReactNode;
  action: 'edit' | 'delete' | 'create' | 'view';
  pageIdentifier: string;
  resourceId?: number;
  fallback?: ReactNode;
  showLoadingState?: boolean;
}

/**
 * Component that shows/hides action buttons based on user permissions.
 * Prevents users from seeing actions they cannot perform.
 */
export function ActionButton({
  children,
  action,
  pageIdentifier,
  resourceId,
  fallback = null,
  showLoadingState = true
}: ActionButtonProps) {
  return (
    <ConditionalRender
      pageIdentifier={pageIdentifier}
      requiredPermission={action}
      resourceId={resourceId}
      fallback={fallback}
      showLoadingState={showLoadingState}
      loadingComponent={
        <button 
          disabled 
          className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
        >
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
          Loading...
        </button>
      }
    >
      {children}
    </ConditionalRender>
  );
}

interface PermissionBasedSectionProps {
  children: ReactNode;
  sectionType: 'hr_admin' | 'supervisor' | 'employee_owner' | 'general';
  employeeId?: number;
  title?: string;
  description?: string;
  fallback?: ReactNode;
}

/**
 * Component that renders entire sections based on permission levels.
 * Useful for grouping related UI elements that should appear/disappear together.
 */
export function PermissionBasedSection({
  children,
  sectionType,
  employeeId,
  title,
  description,
  fallback = null
}: PermissionBasedSectionProps) {
  const getPageConfig = () => {
    switch (sectionType) {
      case 'hr_admin':
        return {
          pageIdentifier: 'departments', // HR Admin only page
          requiredPermission: 'view' as const
        };
      case 'supervisor':
        return {
          pageIdentifier: 'assignments', // All can view, but checking for supervisor-level access
          requiredPermission: 'edit' as const // Only supervisors and HR can edit
        };
      case 'employee_owner':
        return {
          pageIdentifier: 'employees/edit',
          resourceId: employeeId,
          requiredPermission: 'edit' as const
        };
      case 'general':
        return {
          pageIdentifier: 'employees',
          requiredPermission: 'view' as const
        };
      default:
        return {
          pageIdentifier: 'employees',
          requiredPermission: 'view' as const
        };
    }
  };

  const config = getPageConfig();

  return (
    <ConditionalRender
      pageIdentifier={config.pageIdentifier}
      requiredPermission={config.requiredPermission}
      resourceId={config.resourceId}
      fallback={fallback}
      showLoadingState={true}
      loadingComponent={
        <div className="animate-pulse">
          {title && <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>}
          {description && <div className="h-4 bg-gray-200 rounded w-2/3 mb-4"></div>}
          <div className="space-y-3">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        {title && (
          <div>
            <h3 className="text-lg font-medium ">{title}</h3>
            {description && (
              <p className="mt-1 text-sm text-gray-600">{description}</p>
            )}
          </div>
        )}
        {children}
      </div>
    </ConditionalRender>
  );
}

/**
 * Hook that provides helper functions for common UI permission patterns
 */
export function useUIPermissions(pageIdentifier: string, resourceId?: number) {
  const { canView, canEdit, canCreate, canDelete, isLoading } = usePageActions(pageIdentifier, resourceId);

  return {
    // Permission checks
    canView,
    canEdit,
    canCreate,
    canDelete,
    isLoading,

    // Helper components bound to this page/resource
    ConditionalRender: ({ children, requiredPermission, fallback }: {
      children: ReactNode;
      requiredPermission: 'view' | 'edit' | 'create' | 'delete';
      fallback?: ReactNode;
    }) => (
      <ConditionalRender
        pageIdentifier={pageIdentifier}
        requiredPermission={requiredPermission}
        resourceId={resourceId}
        fallback={fallback}
      >
        {children}
      </ConditionalRender>
    ),

    ActionButton: ({ children, action, fallback }: {
      children: ReactNode;
      action: 'edit' | 'delete' | 'create' | 'view';
      fallback?: ReactNode;
    }) => (
      <ActionButton
        pageIdentifier={pageIdentifier}
        action={action}
        resourceId={resourceId}
        fallback={fallback}
      >
        {children}
      </ActionButton>
    ),

    // Quick permission checks for inline conditionals
    showIf: (permission: 'view' | 'edit' | 'create' | 'delete') => {
      switch (permission) {
        case 'view': return canView;
        case 'edit': return canEdit;
        case 'create': return canCreate;
        case 'delete': return canDelete;
        default: return false;
      }
    }
  };
}