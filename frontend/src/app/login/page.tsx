

'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/store/authStore';

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
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
          HRM System
        </h2>
        <p className="mt-2 text-center text-sm text-gray-700">
          Sign in to your account
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                Username
              </label>
              <div className="mt-1">
                <input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter username"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter password"
                />
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-3">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-700">Demo Accounts</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.username}
                  onClick={() => handleDemoLogin(account)}
                  disabled={isLoading}
                  className="w-full text-left p-3 border border-gray-200 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  <div className="font-medium text-gray-900">{account.role}</div>
                  <div className="text-sm text-gray-700">{account.description}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}