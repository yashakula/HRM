'use client';

import React from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/authStore';

interface NavigationItem {
  href: string;
  label: string;
  permissions?: string[];
  requireAll?: boolean;
  exact?: boolean;
}

interface PermissionBasedNavProps {
  items: NavigationItem[];
  className?: string;
  linkClassName?: string;
  activeLinkClassName?: string;
  inactiveLinkClassName?: string;
  currentPath?: string;
}

/**
 * Permission-based navigation component that filters menu items based on user permissions.
 */
export default function PermissionBasedNav({
  items,
  className = "flex space-x-6",
  linkClassName = "px-3 py-2 rounded-md text-sm font-medium transition-colors",
  activeLinkClassName = "text-blue-600 bg-blue-50",
  inactiveLinkClassName = "text-gray-700 hover:text-gray-900 hover:bg-gray-50",
  currentPath
}: PermissionBasedNavProps) {
  const { isAuthenticated, hasPermission, hasAnyPermission, hasAllPermissions } = useAuthStore();

  if (!isAuthenticated) return null;

  // Filter items based on permissions
  const visibleItems = items.filter(item => {
    if (!item.permissions || item.permissions.length === 0) {
      return true; // No permissions required - show to all authenticated users
    }

    if (item.permissions.length === 1) {
      return hasPermission(item.permissions[0]);
    }

    return item.requireAll 
      ? hasAllPermissions(item.permissions)
      : hasAnyPermission(item.permissions);
  });

  const isActiveLink = (href: string, exact = false) => {
    if (!currentPath) return false;
    return exact ? currentPath === href : currentPath.startsWith(href);
  };

  return (
    <nav className={className}>
      {visibleItems.map((item) => {
        const isActive = isActiveLink(item.href, item.exact);
        const finalClassName = `${linkClassName} ${isActive ? activeLinkClassName : inactiveLinkClassName}`;

        return (
          <Link 
            key={item.href}
            href={item.href}
            className={finalClassName}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}

/**
 * Predefined navigation configurations for common use cases
 */
export const MAIN_NAVIGATION_ITEMS: NavigationItem[] = [
  {
    href: '/profile',
    label: 'My Profile',
    // No permissions - available to all authenticated users
  },
  {
    href: '/leave-request',
    label: 'Leave Request',
    // No permissions - available to all authenticated users
  },
  {
    href: '/',
    label: 'Dashboard',
    permissions: ['employee.read.all', 'employee.read.supervised', 'department.create', 'department.update'],
    requireAll: false,
    exact: true
  },
  {
    href: '/search',
    label: 'Search Employees',
    permissions: ['employee.read.all', 'employee.read.supervised'],
    requireAll: false
  },
  {
    href: '/employees/create',
    label: 'Create Employee',
    permissions: ['employee.create']
  },
  {
    href: '/departments',
    label: 'Departments',
    permissions: ['department.read']
  }
];

export const ADMIN_NAVIGATION_ITEMS: NavigationItem[] = [
  {
    href: '/admin/users',
    label: 'User Management',
    permissions: ['user.manage']
  },
  {
    href: '/admin/reports',
    label: 'Reports',
    permissions: ['system.access_reports']
  },
  {
    href: '/admin/settings',
    label: 'System Settings',
    permissions: ['system.manage_users']
  }
];

export const EMPLOYEE_SELF_SERVICE_ITEMS: NavigationItem[] = [
  {
    href: '/profile',
    label: 'My Profile'
  },
  {
    href: '/leave-request',
    label: 'Leave Requests'
  },
  {
    href: '/my-assignments',
    label: 'My Assignments',
    permissions: ['assignment.read.own']
  }
];

/**
 * Hook to get filtered navigation items based on current user permissions
 */
export function usePermissionFilteredNavigation(items: NavigationItem[]) {
  const { isAuthenticated, hasPermission, hasAnyPermission, hasAllPermissions } = useAuthStore();

  if (!isAuthenticated) return [];

  return items.filter(item => {
    if (!item.permissions || item.permissions.length === 0) {
      return true;
    }

    if (item.permissions.length === 1) {
      return hasPermission(item.permissions[0]);
    }

    return item.requireAll 
      ? hasAllPermissions(item.permissions)
      : hasAnyPermission(item.permissions);
  });
}

/**
 * Breadcrumb component that respects permissions
 */
interface BreadcrumbItem {
  href?: string;
  label: string;
  permissions?: string[];
}

interface PermissionBasedBreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function PermissionBasedBreadcrumb({
  items,
  className = "flex items-center space-x-2 text-sm text-gray-600"
}: PermissionBasedBreadcrumbProps) {
  const { hasAnyPermission } = useAuthStore();

  const visibleItems = items.filter(item => {
    if (!item.permissions || item.permissions.length === 0) return true;
    return hasAnyPermission(item.permissions);
  });

  return (
    <nav className={className}>
      {visibleItems.map((item, index) => (
        <React.Fragment key={item.label}>
          {index > 0 && (
            <span className="text-gray-400">/</span>
          )}
          {item.href ? (
            <Link href={item.href} className="hover:text-gray-800">
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-800 font-medium">{item.label}</span>
          )}
        </React.Fragment>
      ))}
    </nav>
  );
}