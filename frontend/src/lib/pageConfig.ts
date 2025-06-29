/**
 * Page Configuration System
 * 
 * Defines metadata for each page including required permissions,
 * navigation visibility, and display information.
 */

export interface PageConfig {
  /** Permissions required to access this page (user needs ANY of these) */
  requiredPermissions: string[];
  /** Display title for navigation */
  title: string;
  /** Whether to show this page in navigation */
  showInNav: boolean;
  /** Optional icon for navigation */
  icon?: string;
  /** Optional description */
  description?: string;
  /** Navigation order (lower numbers appear first) */
  navOrder?: number;
  /** Whether this page requires specific role(s) in addition to permissions */
  requiredRoles?: string[];
}

export interface NavigationItem {
  path: string;
  title: string;
  icon?: string;
  order: number;
  config: PageConfig;
}

/**
 * Central registry of all page configurations
 * Key: route path, Value: page configuration
 */
export const PAGE_CONFIGS: Record<string, PageConfig> = {
  '/': {
    requiredPermissions: [], // Dashboard accessible to all authenticated users
    title: 'Dashboard',
    showInNav: true,
    icon: '🏠',
    navOrder: 1,
    description: 'Main dashboard and overview'
  },

  '/profile': {
    requiredPermissions: [], // Profile accessible to all authenticated users
    title: 'My Profile',
    showInNav: true,
    icon: '👤',
    navOrder: 2,
    description: 'View and edit personal information'
  },

  '/employees': {
    requiredPermissions: ['employee.read.all', 'employee.read.supervised'],
    title: 'Employees',
    showInNav: true,
    icon: '👥',
    navOrder: 3,
    description: 'View and manage employee records'
  },

  '/employees/create': {
    requiredPermissions: ['employee.create'],
    title: 'Create Employee',
    showInNav: true,
    icon: '➕',
    navOrder: 4,
    description: 'Add new employee to the system'
  },

  '/search': {
    requiredPermissions: ['employee.search'],
    title: 'Search Employees',
    showInNav: true,
    icon: '🔍',
    navOrder: 5,
    description: 'Search and filter employee records'
  },

  '/departments': {
    requiredPermissions: ['department.read'],
    title: 'Departments',
    showInNav: true,
    icon: '🏢',
    navOrder: 6,
    description: 'View and manage departments'
  },

  '/assignments': {
    requiredPermissions: ['assignment.read.all', 'assignment.read.own', 'assignment.read.supervised'],
    title: 'Assignments',
    showInNav: true,
    icon: '📋',
    navOrder: 7,
    description: 'View and manage role assignments'
  },

  '/leave-request': {
    requiredPermissions: ['leave_request.create.own', 'leave_request.read.own'],
    title: 'My Leave Requests',
    showInNav: true,
    icon: '📅',
    navOrder: 8,
    description: 'Submit and view my leave requests',
    requiredRoles: ['EMPLOYEE', 'SUPERVISOR', 'HR_ADMIN'] // Exclude SUPER_USER
  },

  '/approve-requests': {
    requiredPermissions: ['leave_request.approve.supervised', 'leave_request.approve.all'],
    title: 'Approve Requests',
    showInNav: true,
    icon: '✅',
    navOrder: 9,
    description: 'Review and approve leave requests from team members',
    requiredRoles: ['SUPERVISOR', 'HR_ADMIN'] // Only supervisors and HR can approve
  },

  '/admin': {
    requiredPermissions: ['user.manage'],
    title: 'Admin Panel',
    showInNav: true,
    icon: '⚙️',
    navOrder: 10,
    description: 'System administration and user management'
  },

  // Employee detail pages (dynamic routes)
  '/employees/[id]/edit': {
    requiredPermissions: ['employee.update.all', 'employee.update.own'],
    title: 'Edit Employee',
    showInNav: false, // Don't show dynamic routes in nav
    description: 'Edit employee information'
  }
};

/**
 * Get page configuration for a given route path
 */
export function getPageConfig(path: string): PageConfig | null {
  // Handle dynamic routes by checking for exact match first, then patterns
  if (PAGE_CONFIGS[path]) {
    return PAGE_CONFIGS[path];
  }

  // Handle dynamic routes like /employees/123/edit
  for (const [configPath, config] of Object.entries(PAGE_CONFIGS)) {
    if (configPath.includes('[id]')) {
      const pattern = configPath.replace('[id]', '\\d+');
      const regex = new RegExp(`^${pattern}$`);
      if (regex.test(path)) {
        return config;
      }
    }
  }

  return null;
}

/**
 * Check if user has access to a specific page
 */
export function canAccessPage(
  path: string, 
  userPermissions: string[], 
  userRoles: string[] = []
): boolean {
  const config = getPageConfig(path);
  
  if (!config) {
    // If no config defined, deny access by default
    return false;
  }

  // If no permissions required, allow access (e.g., dashboard, profile)
  if (config.requiredPermissions.length === 0) {
    return true;
  }

  // Check if user has any of the required permissions
  const hasPermission = config.requiredPermissions.some(permission => 
    userPermissions.includes(permission)
  );

  // Check role requirements if specified
  let hasRole = true;
  if (config.requiredRoles && config.requiredRoles.length > 0) {
    hasRole = config.requiredRoles.some(role => userRoles.includes(role));
  }

  return hasPermission && hasRole;
}

/**
 * Get all navigation items that the user can access
 */
export function getAccessibleNavigation(
  userPermissions: string[],
  userRoles: string[] = []
): NavigationItem[] {
  const navItems: NavigationItem[] = [];

  for (const [path, config] of Object.entries(PAGE_CONFIGS)) {
    // Only include pages that should show in navigation
    if (!config.showInNav) continue;

    // Check if user can access this page
    if (canAccessPage(path, userPermissions, userRoles)) {
      navItems.push({
        path,
        title: config.title,
        icon: config.icon,
        order: config.navOrder || 999,
        config
      });
    }
  }

  // Sort by navigation order
  return navItems.sort((a, b) => a.order - b.order);
}