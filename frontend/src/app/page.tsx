'use client';

import { useAuthStore } from '@/store/authStore';
import { usePageRedirect, useAccessibleNavigation } from '@/hooks/useNavigationAccess';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"

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
      <div>
        <Card>
          <CardHeader><CardTitle>Welcome back, {user.username}!</CardTitle></CardHeader>
          <CardFooter className="text-sm">Roles: {user.roles?.join(', ').replace(/_/g, ' ')}</CardFooter>
        </Card>
      </div>

      {/* Quick Access Dashboard */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
         {accessibleNavigation
          .filter(item => item.path !== '/' && item.path !== '/profile') // Exclude dashboard and profile
          .slice(0, 6) // Show max 6 items
          .map((item) =>(
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{item.icon} {item.title}</CardTitle>
              </CardHeader>
              <CardContent className="pb-3">
                <CardDescription>{item.config.description}</CardDescription>
              </CardContent>
              <CardFooter className="pt-0">
                <Button className="w-full"><Link href={item.path}>Open {item.title}</Link></Button>
              </CardFooter>
            </Card>
          )) }
      </div>
    
      {/* Available Features Summary */}
      <div>
        <h3 className="text-lg font-medium mb-4">
          Available Features
        </h3>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {accessibleNavigation.map((item) => (
            <Card key={item.path}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">{item.icon || '📋'} {item.title}</CardTitle>
              </CardHeader>
              <CardContent className="pb-3">
                <CardDescription>{item.config.description}</CardDescription>
              </CardContent>
              <CardFooter className="pt-0">
                <Button className="w-full">
                  <Link href={item.path}>Open {item.title}</Link>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}