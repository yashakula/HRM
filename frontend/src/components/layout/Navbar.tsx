'use client';

import { 
  useAuthStore, 
  useUserRole,
  useHasPermission,
  useHasAnyPermission
} from '@/store/authStore';
// UserRole import removed - using permission-based navigation
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const userRole = useUserRole();
  const router = useRouter();

  // Permission checking hooks
  const canCreateEmployee = useHasPermission('employee.create');
  const canSearchEmployees = useHasAnyPermission(['employee.read.all', 'employee.read.supervised']);
  const canViewDepartments = useHasPermission('department.read');
  const canManageDepartments = useHasAnyPermission(['department.create', 'department.update', 'department.delete']);
  const canManageUsers = useHasPermission('user.manage');

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!user) return null;

  // Define permission-based navigation items
  const getNavigationItems = () => {
    const items = [];

    // Profile is available to all authenticated users
    items.push({
      href: '/profile',
      label: 'My Profile',
      condition: true
    });

    // Leave request is available to all authenticated users
    items.push({
      href: '/leave-request',
      label: 'Leave Request',
      condition: true
    });

    // Dashboard - available to users who can manage others or see broader data
    if (canSearchEmployees || canManageDepartments) {
      items.push({
        href: '/',
        label: 'Dashboard',
        condition: true
      });
    }

    // Search employees - based on read permissions
    if (canSearchEmployees) {
      items.push({
        href: '/search',
        label: 'Search Employees',
        condition: true
      });
    }

    // Create employee - based on create permission
    if (canCreateEmployee) {
      items.push({
        href: '/employees/create',
        label: 'Create Employee',
        condition: true
      });
    }

    // Departments - based on department permissions
    if (canViewDepartments) {
      items.push({
        href: '/departments',
        label: 'Departments',
        condition: true
      });
    }

    // Admin panel - based on user management permission
    if (canManageUsers) {
      items.push({
        href: '/admin',
        label: 'Admin Panel',
        condition: true
      });
    }

    return items.filter(item => item.condition);
  };

  const navigationItems = getNavigationItems();

  return (
    <nav className="bg-white shadow border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link 
              href={canSearchEmployees || canManageDepartments ? '/' : '/profile'} 
              className="text-xl font-bold text-gray-900 mr-8"
            >
              HRM System
            </Link>
            
            <div className="hidden md:flex space-x-6">
              {navigationItems.map((item) => (
                <Link 
                  key={item.href}
                  href={item.href} 
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="text-sm">
              <span className="text-gray-700">Welcome, </span>
              <span className="font-medium text-gray-900">{user.username}</span>
              <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {userRole?.replace('_', ' ')}
              </span>
            </div>
            
            <button
              onClick={handleLogout}
              className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}