'use client';

import { useAuthStore, useUserRole } from '@/store/authStore';
import { UserRole } from '@/lib/types';
import Link from 'next/link';

export default function Home() {
  const { user } = useAuthStore();
  const userRole = useUserRole();

  if (!user) {
    return (
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900">Welcome to HRM System</h1>
        <p className="mt-2 text-gray-800">Please log in to continue.</p>
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
            Role: {userRole?.replace('_', ' ')}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {/* Employee Search - All roles */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">👥</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-700 truncate">
                    Employee Directory
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    Search & View
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4">
              <Link
                href="/employees"
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                View Employees
              </Link>
            </div>
          </div>
        </div>

        {/* Departments - All roles */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">🏢</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-700 truncate">
                    Organization
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    Departments
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4">
              <Link
                href="/departments"
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                View Departments
              </Link>
            </div>
          </div>
        </div>

        {/* Assignments - All roles */}
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-orange-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">👥</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-700 truncate">
                    Role Management
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    Assignments
                  </dd>
                </dl>
              </div>
            </div>
            <div className="mt-4">
              <Link
                href="/assignments"
                className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-orange-700 bg-orange-100 hover:bg-orange-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-orange-500"
              >
                View Assignments
              </Link>
            </div>
          </div>
        </div>

        {/* Create Employee - HR Admin only */}
        {userRole === UserRole.HR_ADMIN && (
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">➕</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-700 truncate">
                      HR Management
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      Create Employee
                    </dd>
                  </dl>
                </div>
              </div>
              <div className="mt-4">
                <Link
                  href="/employees/create"
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-green-700 bg-green-100 hover:bg-green-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                >
                  Add New Employee
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Role-specific cards */}
        {userRole === UserRole.SUPERVISOR && (
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">👨‍💼</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-700 truncate">
                      Team Management
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      Coming Soon
                    </dd>
                  </dl>
                </div>
              </div>
              <div className="mt-4">
                <span className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100">
                  Future Feature
                </span>
              </div>
            </div>
          </div>
        )}

        {userRole === UserRole.EMPLOYEE && (
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">👤</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-700 truncate">
                      Self Service
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      Coming Soon
                    </dd>
                  </dl>
                </div>
              </div>
              <div className="mt-4">
                <span className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-gray-100">
                  Future Feature
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Stats */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900">
            Quick Access
          </h3>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link
              href="/employees"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
            >
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Search Employees</p>
                <p className="text-sm text-gray-700">Find employee records quickly</p>
              </div>
            </Link>
            
            <Link
              href="/departments"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
            >
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Departments</p>
                <p className="text-sm text-gray-700">Browse organization structure</p>
              </div>
            </Link>
            
            <Link
              href="/assignments"
              className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
            >
              <div className="flex-1 min-w-0">
                <span className="absolute inset-0" aria-hidden="true" />
                <p className="text-sm font-medium text-gray-900">Assignments</p>
                <p className="text-sm text-gray-700">View employee role assignments</p>
              </div>
            </Link>
            
            {userRole === UserRole.HR_ADMIN && (
              <Link
                href="/employees/create"
                className="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm flex items-center space-x-3 hover:border-gray-400 focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-blue-500"
              >
                <div className="flex-1 min-w-0">
                  <span className="absolute inset-0" aria-hidden="true" />
                  <p className="text-sm font-medium text-gray-900">Add Employee</p>
                  <p className="text-sm text-gray-700">Create new employee profile</p>
                </div>
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}