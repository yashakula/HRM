'use client';

import { useAuthStore, useUserRole } from '@/store/authStore';
import { UserRole } from '@/lib/types';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const userRole = useUserRole();
  const router = useRouter();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!user) return null;

  // Define role-based navigation items
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

    // Role-specific navigation
    if (userRole === UserRole.HR_ADMIN) {
      items.push(
        {
          href: '/',
          label: 'Dashboard',
          condition: true
        },
        {
          href: '/search',
          label: 'Search Employees',
          condition: true
        },
        {
          href: '/employees/create',
          label: 'Create Employee',
          condition: true
        },
        {
          href: '/departments',
          label: 'Departments',
          condition: true
        }
      );
    } else if (userRole === UserRole.SUPERVISOR) {
      items.push(
        {
          href: '/',
          label: 'Dashboard',
          condition: true
        },
        {
          href: '/search',
          label: 'Search Employees',
          condition: true
        },
        {
          href: '/departments',
          label: 'Departments',
          condition: true
        }
      );
    }
    // For EMPLOYEE role, only profile is available (already added above)

    return items.filter(item => item.condition);
  };

  const navigationItems = getNavigationItems();

  return (
    <nav className="bg-white shadow border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link 
              href={userRole === UserRole.EMPLOYEE ? '/profile' : '/'} 
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