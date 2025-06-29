'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuthStore, useUserRoles } from '@/store/authStore';
import { useAccessibleNavigation, useUserHomePage } from '@/hooks/useNavigationAccess';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface NavigationGroup {
  key: string;
  title: string;
  icon: string;
  items: Array<{
    path: string;
    title: string;
    icon?: string;
  }>;
}

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const userRoles = useUserRoles();
  const router = useRouter();
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  
  // Get navigation items based on user permissions
  const navigationItems = useAccessibleNavigation();
  const userHomePage = useUserHomePage();

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  // Close dropdowns when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setActiveDropdown(null);
        setUserDropdownOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!user) return null;

  // Group navigation items into logical categories
  const navigationGroups: NavigationGroup[] = [
    {
      key: 'dashboard',
      title: 'Dashboard',
      icon: '🏠',
      items: navigationItems.filter(item => item.path === '/').map(item => ({
        path: item.path,
        title: item.title,
        icon: item.icon
      }))
    },
    {
      key: 'employees',
      title: 'Employees',
      icon: '👥',
      items: navigationItems.filter(item => 
        item.path === '/employees' || 
        item.path === '/employees/create' || 
        item.path === '/search'
      ).map(item => ({
        path: item.path,
        title: item.title,
        icon: item.icon
      }))
    },
    {
      key: 'organization',
      title: 'Organization',
      icon: '🏢',
      items: navigationItems.filter(item => 
        item.path === '/departments' || 
        item.path === '/assignments'
      ).map(item => ({
        path: item.path,
        title: item.title,
        icon: item.icon
      }))
    },
    {
      key: 'requests',
      title: 'Leave Requests',
      icon: '📅',
      items: navigationItems.filter(item => 
        item.path === '/leave-request'
      ).map(item => ({
        path: item.path,
        title: item.title,
        icon: item.icon
      }))
    },
    {
      key: 'system',
      title: 'System',
      icon: '⚙️',
      items: navigationItems.filter(item => 
        item.path === '/admin'
      ).map(item => ({
        path: item.path,
        title: item.title,
        icon: item.icon
      }))
    }
  ].filter(group => group.items.length > 0); // Only show groups that have accessible items

  // Get user initials for avatar
  const getUserInitials = (username: string) => {
    return username.split('_').map(part => part[0]?.toUpperCase()).join('').slice(0, 2);
  };

  return (
    <nav className="bg-white shadow border-b border-gray-200" ref={dropdownRef}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Left side - Logo and Navigation */}
          <div className="flex items-center space-x-8">
            <Link 
              href={userHomePage}
              className="text-xl font-bold text-gray-900"
            >
              HRM System
            </Link>
            
            {/* Main Navigation */}
            <div className="hidden md:flex space-x-1">
              {navigationGroups.map((group) => {
                // For single-item groups, render as direct link
                if (group.items.length === 1) {
                  const item = group.items[0];
                  return (
                    <Link
                      key={group.key}
                      href={item.path}
                      className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors"
                    >
                      <span>{group.icon}</span>
                      <span>{group.title}</span>
                    </Link>
                  );
                }

                // For multi-item groups, render as dropdown
                return (
                  <div key={group.key} className="relative">
                    <button
                      onClick={() => setActiveDropdown(activeDropdown === group.key ? null : group.key)}
                      className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors"
                    >
                      <span>{group.icon}</span>
                      <span>{group.title}</span>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>

                    {/* Dropdown Menu */}
                    {activeDropdown === group.key && (
                      <div className="absolute left-0 mt-1 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                        <div className="py-1">
                          {group.items.map((item) => (
                            <Link
                              key={item.path}
                              href={item.path}
                              onClick={() => setActiveDropdown(null)}
                              className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                            >
                              {item.icon && <span>{item.icon}</span>}
                              <span>{item.title}</span>
                            </Link>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right side - User Profile Dropdown */}
          <div className="flex items-center">
            <div className="relative">
              <button
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 transition-colors"
              >
                {/* User Avatar */}
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                  {getUserInitials(user.username)}
                </div>
                <span className="hidden sm:block">{user.username}</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* User Dropdown Menu */}
              {userDropdownOpen && (
                <div className="absolute right-0 mt-1 w-64 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-50">
                  <div className="py-1">
                    {/* User Info Section */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
                          {getUserInitials(user.username)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{user.username}</p>
                          <p className="text-xs text-gray-500">{user.email}</p>
                        </div>
                      </div>
                      
                      {/* Role Badges */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userRoles.map(role => (
                          <span key={role} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {role.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Menu Items */}
                    <Link
                      href="/profile"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    >
                      <span>👤</span>
                      <span>My Profile</span>
                    </Link>
                    
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                    >
                      <span>🚪</span>
                      <span>Logout</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile navigation menu */}
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
            {navigationGroups.map((group) => (
              <div key={group.key}>
                {group.items.length === 1 ? (
                  <Link
                    href={group.items[0].path}
                    className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 block px-3 py-2 rounded-md text-base font-medium"
                  >
                    <span>{group.icon}</span>
                    <span>{group.title}</span>
                  </Link>
                ) : (
                  <>
                    <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                      {group.title}
                    </div>
                    {group.items.map((item) => (
                      <Link
                        key={item.path}
                        href={item.path}
                        className="flex items-center space-x-2 text-gray-700 hover:text-gray-900 block px-6 py-2 rounded-md text-base font-medium"
                      >
                        {item.icon && <span>{item.icon}</span>}
                        <span>{item.title}</span>
                      </Link>
                    ))}
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}