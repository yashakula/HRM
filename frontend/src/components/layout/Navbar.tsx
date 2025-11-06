"use client";

import * as React from "react"
import { useState, useRef, useEffect } from 'react';
import { useAuthStore, useUserRoles } from '@/store/authStore';
import { useAccessibleNavigation, useUserHomePage } from '@/hooks/useNavigationAccess';
import Link from "next/link"
import { useRouter } from 'next/navigation';

import { useIsMobile } from "@/hooks/use-mobile"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu"
import { cn } from "@/lib/utils"

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
  const isMobile = useIsMobile();
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
  ].filter(group => group.items.length > 0);

  // Get user initials for avatar
  const getUserInitials = (username: string) => {
    return username.split('_').map(part => part[0]?.toUpperCase()).join('').slice(0, 2);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60" ref={dropdownRef}>
      <div className="container mx-auto flex h-14 max-w-screen-2xl items-center px-4">
        <div className="mr-4 flex">
          <Link
            href={userHomePage}
            className="mr-6 flex items-center space-x-2 font-bold text-foreground"
          >
            HRM System
          </Link>

          {/* Main Navigation - Desktop */}
          {!isMobile && (
            <NavigationMenu>
              <NavigationMenuList>
                  {navigationGroups.map((group) => {
                    // For single-item groups, render as direct link
                    if (group.items.length === 1) {
                      const item = group.items[0];
                      return (
                        <NavigationMenuItem key={group.key}>
                          <Link href={item.path} legacyBehavior passHref>
                            <NavigationMenuLink className={navigationMenuTriggerStyle()}>
                              {group.title}
                            </NavigationMenuLink>
                          </Link>
                        </NavigationMenuItem>
                      );
                    }

                    // For multi-item groups, render as dropdown
                    return (
                      <NavigationMenuItem key={group.key}>
                        <NavigationMenuTrigger>
                          {group.title}
                        </NavigationMenuTrigger>
                        <NavigationMenuContent>
                          <ul className="grid w-[300px] gap-2 p-2">
                            {group.items.map((item) => (
                              <li key={item.path}>
                                <NavigationMenuLink asChild>
                                  <Link
                                    href={item.path}
                                    className={cn(
                                      "block select-none rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground"
                                    )}
                                  >
                                    <div className="font-medium text-sm">
                                      {item.title}
                                    </div>
                                  </Link>
                                </NavigationMenuLink>
                              </li>
                            ))}
                          </ul>
                        </NavigationMenuContent>
                      </NavigationMenuItem>
                    );
                  })}
              </NavigationMenuList>
            </NavigationMenu>
          )}
        </div>

        {/* Right side - User Profile Dropdown */}
        <div className="flex flex-1 items-center justify-end space-x-2">
          <nav className="flex items-center">
            <div className="relative">
              <button
                onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-foreground hover:bg-accent transition-colors"
              >
                {/* User Avatar */}
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium">
                  {getUserInitials(user.username)}
                </div>
                <span className="hidden sm:block">{user.username}</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* User Dropdown Menu */}
              {userDropdownOpen && (
                <div className="absolute right-0 mt-1 w-64 rounded-md shadow-lg bg-card border border-border ring-1 ring-black ring-opacity-5 z-50">
                  <div className="py-1">
                    {/* User Info Section */}
                    <div className="px-4 py-3 border-b border-border">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-medium">
                          {getUserInitials(user.username)}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-foreground">{user.username}</p>
                          <p className="text-xs text-muted-foreground">{user.email}</p>
                        </div>
                      </div>

                      {/* Role Badges */}
                      <div className="mt-2 flex flex-wrap gap-1">
                        {userRoles.map(role => (
                          <span key={role} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary/10 text-primary">
                            {role.replace('_', ' ')}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Menu Items */}
                    <Link
                      href="/profile"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center space-x-2 px-4 py-2 text-sm text-foreground hover:bg-accent"
                    >
                      <span>👤</span>
                      <span>My Profile</span>
                    </Link>

                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-foreground hover:bg-accent"
                    >
                      <span>🚪</span>
                      <span>Logout</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </nav>
        </div>
      </div>

      {/* Mobile navigation menu */}
      {isMobile && (
        <div className="container pb-3 space-y-1 border-t border-border/40">
            {navigationGroups.map((group) => (
              <div key={group.key}>
                {group.items.length === 1 ? (
                  <Link
                    href={group.items[0].path}
                    className="flex items-center space-x-2 text-foreground hover:bg-accent block px-3 py-2 rounded-md text-base font-medium"
                  >
                    <span>{group.icon}</span>
                    <span>{group.title}</span>
                  </Link>
                ) : (
                  <>
                    <div className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                      {group.title}
                    </div>
                    {group.items.map((item) => (
                      <Link
                        key={item.path}
                        href={item.path}
                        className="flex items-center space-x-2 text-foreground hover:bg-accent block px-6 py-2 rounded-md text-base font-medium"
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
      )}
    </header>
  );
}