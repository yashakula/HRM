'use client';

import { useAuthStore } from '@/store/authStore';
import { usePageRedirect, useAccessibleNavigation } from '@/hooks/useNavigationAccess';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function Home() {
  const { user } = useAuthStore();
  const router = useRouter();
  const redirectTo = usePageRedirect('/');
  const accessibleNavigation = useAccessibleNavigation();

  // Handle automatic redirects based on user permissions
  useEffect(() => {
    if (redirectTo) {
      router.replace(redirectTo);
    }
  }, [redirectTo, router]);

  if (!user) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Welcome to HRM System</h1>
        <p className="mt-2 text-gray-800">Please log in to continue.</p>
      </div>
    );
  }

  // Show loading state while redirect is happening
  if (redirectTo) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Redirecting...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user.username}!
          </h1>
          <p className="mt-1 text-sm text-gray-800">
            Roles: {user.roles?.join(', ').replace(/_/g, ' ')}
          </p>
        </div>
      </div>

      {/* Quick Access Dashboard */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {accessibleNavigation
          .filter(item => item.path !== '/' && item.path !== '/profile') // Exclude dashboard and profile
          .slice(0, 6) // Show max 6 items
          .map((item) => (
          <div key={item.path} className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">{item.icon || '📋'}</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-700 truncate">
                      {item.title}
                    </dt>
                    <dd className="text-sm text-gray-500">
                      {item.config.description || 'Manage and view data'}
                    </dd>
                  </dl>
                </div>
              </div>
              <div className="mt-4">
                <Link
                  href={item.path}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Open {item.title}
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Available Features Summary */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Available Features
          </h3>
          <p className="mt-1 text-sm text-gray-600">
            Based on your permissions, you have access to the following features:
          </p>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {accessibleNavigation.map((item) => (
              <Link
                key={item.path}
                href={item.path}
                className="relative rounded-lg border border-gray-300 bg-white px-4 py-3 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
              >
                <div className="flex-shrink-0">
                  <span className="text-lg">{item.icon || '📋'}</span>
                </div>
                <div className="flex-1 min-w-0">
                  <span className="absolute inset-0" aria-hidden="true" />
                  <p className="text-sm font-medium text-gray-900">{item.title}</p>
                  {item.config.description && (
                    <p className="text-xs text-gray-500 truncate">{item.config.description}</p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}