

'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';
import { GalleryVerticalEnd } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const DEMO_ACCOUNTS = [
  {
    username: 'super_user',
    password: 'superuser123',
    role: 'Super User',
    description: 'System administrator - full access + user management'
  },
  {
    username: 'hr_admin',
    password: 'admin123',
    role: 'HR Admin',
    description: 'Full access - create employees, manage all records'
  },
  {
    username: 'supervisor1', 
    password: 'super123',
    role: 'Supervisor',
    description: 'Manage team - view employees, approve leave requests'
  },
  {
    username: 'employee1',
    password: 'emp123', 
    role: 'Employee',
    description: 'Self-service - view directory, manage personal info'
  }
];

function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login, error, clearError } = useAuthStore();
  const router = useRouter();
  const searchParams = useSearchParams();
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    clearError();
    
    try {
      await login(username, password);
      
      // Redirect to intended page or dashboard
      const redirectTo = searchParams.get('redirect') || '/';
      router.push(redirectTo);
    } catch {
      // Error is handled in the store
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (demoAccount: typeof DEMO_ACCOUNTS[0]) => {
    setUsername(demoAccount.username);
    setPassword(demoAccount.password);
    setIsLoading(true);
    clearError();
    
    try {
      await login(demoAccount.username, demoAccount.password);
      const redirectTo = searchParams.get('redirect') || '/';
      router.push(redirectTo);
    } catch {
      // Error is handled in the store
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Welcome back!</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
            <div className="grid gap-6">
              <div className="grid gap-6">
                <div className="grid gap-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter username"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <div className="flex items-center">
                    <Label htmlFor="password">Password</Label>
                  </div>
                  <Input
                    id="password"
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                  />
                </div>
                {error && (
                  <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
                    <p className="text-sm text-destructive">{error}</p>
                  </div>
                )}
                <Button type="submit" className="w-full" disabled={isLoading}>
                  {isLoading ? 'Signing in...' : 'Login'}
                </Button>
              </div>
              <div className="text-center text-sm">
                Or choose a test account below
              </div>
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.username}
                  onClick={() => handleDemoLogin(account)}
                  disabled={isLoading}
                  className="w-full text-left p-3 border rounded-md hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-50 transition-colors"
                >
                  <div className="font-medium">{account.role}</div>
                  <div className="text-sm text-muted-foreground">{account.description}</div>
                </button>
              ))}
              <div className="mt-6 space-y-3">
            </div>
            </div>
          </form>
      </CardContent>
    </Card>
           
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 md:p-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <a href="#" className="flex items-center gap-2 self-center font-medium">
          <div className="bg-primary text-primary-foreground flex size-6 items-center justify-center rounded-md">
            <GalleryVerticalEnd className="size-4" />
          </div>
          HRM System Inc.
        </a>
        <LoginForm />
      </div>
    </div>
    </Suspense>
  )
}