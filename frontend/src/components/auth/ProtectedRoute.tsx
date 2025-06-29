'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { apiClient } from '@/lib/api';
import { PageAccessRequest, PageAccessResponse } from '@/lib/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  pageIdentifier: string;
  resourceId?: number;
  requiredPermissions?: ('view' | 'edit' | 'create' | 'delete')[];
  fallbackComponent?: React.ReactNode;
}

interface AccessState {
  isLoading: boolean;
  accessGranted: boolean;
  permissions?: PageAccessResponse;
  error?: string;
}

export default function ProtectedRoute({
  children,
  pageIdentifier,
  resourceId,
  requiredPermissions = ['view'],
  fallbackComponent
}: ProtectedRouteProps) {
  const { isAuthenticated, isLoading: authLoading, user } = useAuthStore();
  const router = useRouter();
  const [accessState, setAccessState] = useState<AccessState>({
    isLoading: true,
    accessGranted: false
  });

  useEffect(() => {
    const validateAccess = async () => {
      // Wait for auth to complete
      if (authLoading) return;

      // Redirect to login if not authenticated
      if (!isAuthenticated) {
        router.push('/login');
        return;
      }

      try {
        setAccessState({ isLoading: true, accessGranted: false });

        const request: PageAccessRequest = {
          page_identifier: pageIdentifier,
          resource_id: resourceId
        };

        const response = await apiClient.validatePageAccess(request);

        // Check if user has required permissions
        const hasRequiredPermissions = requiredPermissions.every(permission => {
          switch (permission) {
            case 'view': return response.permissions.can_view;
            case 'edit': return response.permissions.can_edit;
            case 'create': return response.permissions.can_create;
            case 'delete': return response.permissions.can_delete;
            default: return false;
          }
        });

        setAccessState({
          isLoading: false,
          accessGranted: hasRequiredPermissions,
          permissions: response
        });

      } catch (error) {
        console.error('Page access validation failed:', error);
        setAccessState({
          isLoading: false,
          accessGranted: false,
          error: error instanceof Error ? error.message : 'Access validation failed'
        });
      }
    };

    validateAccess();
  }, [authLoading, isAuthenticated, pageIdentifier, resourceId, requiredPermissions, router]);

  // Show loading spinner while checking auth or permissions
  if (authLoading || accessState.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">Validating access...</p>
        </div>
      </div>
    );
  }

  // Show access denied if user doesn't have permission
  if (!accessState.accessGranted) {
    // Use custom fallback component if provided
    if (fallbackComponent) {
      return <>{fallbackComponent}</>;
    }

    // Default access denied page
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="mb-4">
            <svg className="mx-auto h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.464 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">
            {accessState.permissions?.permissions.message || 'You do not have permission to access this page.'}
          </p>
          <div className="text-sm text-gray-500 mb-4">
            <p>Your roles: {user?.roles?.join(', ')}</p>
            {accessState.permissions?.permissions.required_permissions && (
              <p>Required permissions: {accessState.permissions.permissions.required_permissions.join(', ')}</p>
            )}
          </div>
          <button
            onClick={() => router.back()}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  // Access granted - render children
  return <>{children}</>;
}

// Hook to get page permissions for conditional UI rendering
export function usePagePermissions(pageIdentifier: string, resourceId?: number) {
  const { isAuthenticated, isLoading: authLoading } = useAuthStore();
  const [permissions, setPermissions] = useState<PageAccessResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const getPermissions = async () => {
      if (authLoading || !isAuthenticated) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const request: PageAccessRequest = {
          page_identifier: pageIdentifier,
          resource_id: resourceId
        };

        const response = await apiClient.validatePageAccess(request);
        setPermissions(response);
        setError(null);
      } catch (err) {
        console.error('Failed to get page permissions:', err);
        setError(err instanceof Error ? err.message : 'Failed to get permissions');
      } finally {
        setIsLoading(false);
      }
    };

    getPermissions();
  }, [authLoading, isAuthenticated, pageIdentifier, resourceId]);

  return { permissions, isLoading, error };
}