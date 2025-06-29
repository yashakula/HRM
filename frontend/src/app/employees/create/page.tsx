'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiClient } from '@/lib/api';
import { EmployeeCreateRequest } from '@/lib/types';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import PermissionGuard from '@/components/auth/PermissionGuard';
import { SensitiveField, PermissionBasedSection } from '@/components/auth/ConditionalRender';

// Form validation schema
const employeeSchema = z.object({
  // Person information
  full_name: z.string().min(1, 'Full name is required'),
  date_of_birth: z.string().optional(),
  
  // Personal information (optional)
  personal_email: z.string().email('Invalid email format').optional().or(z.literal('')),
  ssn: z.string().optional(),
  bank_account: z.string().optional(),
  
  // Employee information
  work_email: z.string().email('Invalid email format').optional().or(z.literal('')),
  effective_start_date: z.string().optional(),
  effective_end_date: z.string().optional(),
});

type EmployeeFormData = z.infer<typeof employeeSchema>;

export default function CreateEmployeePage() {
  return (
    <ProtectedRoute 
      pageIdentifier="employees/create" 
      requiredPermissions={['view', 'create']}
    >
      <PermissionGuard 
        permission="employee.create"
        fallback={
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔒</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Access Denied</h3>
            <p className="text-gray-700">You don&apos;t have permission to create employees.</p>
          </div>
        }
      >
        <CreateEmployeeForm />
      </PermissionGuard>
    </ProtectedRoute>
  );
}

function CreateEmployeeForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeSchema),
  });

  const createEmployeeMutation = useMutation({
    mutationFn: (data: EmployeeCreateRequest) => apiClient.createEmployee(data),
    onSuccess: () => {
      reset();
      setIsSubmitting(false);
      // Redirect to employees page with success message
      router.push('/employees');
    },
    onError: (error) => {
      setIsSubmitting(false);
      console.error('Failed to create employee:', error);
    },
  });


  const onSubmit = (data: EmployeeFormData) => {
    setIsSubmitting(true);

    // Transform form data to API format
    const employeeData: EmployeeCreateRequest = {
      person: {
        full_name: data.full_name,
        date_of_birth: data.date_of_birth || undefined,
      },
      work_email: data.work_email || undefined,
      effective_start_date: data.effective_start_date || undefined,
      effective_end_date: data.effective_end_date || undefined,
    };

    // Add personal information if any field is filled
    const hasPersonalInfo = data.personal_email || data.ssn || data.bank_account;
    if (hasPersonalInfo) {
      employeeData.personal_information = {
        personal_email: data.personal_email || undefined,
        ssn: data.ssn || undefined,
        bank_account: data.bank_account || undefined,
      };
    }

    createEmployeeMutation.mutate(employeeData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-2xl font-bold text-gray-900">Create New Employee Profile</h1>
          <p className="mt-1 text-sm text-gray-700">
            Add a new employee to the system
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg">
        <form onSubmit={handleSubmit(onSubmit)} className="px-4 py-5 sm:p-6">
          <div className="space-y-8">
            {/* Personal Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                    Full Name *
                  </label>
                  <input
                    type="text"
                    id="full_name"
                    {...register('full_name')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter full name"
                  />
                  {errors.full_name && (
                    <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    id="date_of_birth"
                    {...register('date_of_birth')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.date_of_birth && (
                    <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="personal_email" className="block text-sm font-medium text-gray-700">
                    Personal Email
                  </label>
                  <input
                    type="email"
                    id="personal_email"
                    {...register('personal_email')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="personal@example.com"
                  />
                  {errors.personal_email && (
                    <p className="mt-1 text-sm text-red-600">{errors.personal_email.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Sensitive Information Section */}
            <PermissionBasedSection
              sectionType="hr_admin"
              title="Sensitive Information"
              description="Financial and identity information (HR Admin only)"
              fallback={
                <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                  <p className="text-sm text-gray-600">
                    Sensitive information fields are only visible to HR Administrators.
                  </p>
                </div>
              }
            >
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <SensitiveField fieldType="ssn">
                  <div>
                    <label htmlFor="ssn" className="block text-sm font-medium text-gray-700">
                      Social Security Number
                    </label>
                    <input
                      type="text"
                      id="ssn"
                      {...register('ssn')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="XXX-XX-XXXX"
                    />
                    {errors.ssn && (
                      <p className="mt-1 text-sm text-red-600">{errors.ssn.message}</p>
                    )}
                  </div>
                </SensitiveField>

                <SensitiveField fieldType="bank_account">
                  <div>
                    <label htmlFor="bank_account" className="block text-sm font-medium text-gray-700">
                      Bank Account
                    </label>
                    <input
                      type="text"
                      id="bank_account"
                      {...register('bank_account')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Account number"
                    />
                    {errors.bank_account && (
                      <p className="mt-1 text-sm text-red-600">{errors.bank_account.message}</p>
                    )}
                  </div>
                </SensitiveField>
              </div>
            </PermissionBasedSection>

            {/* Employment Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Employment Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="work_email" className="block text-sm font-medium text-gray-700">
                    Work Email
                  </label>
                  <input
                    type="email"
                    id="work_email"
                    {...register('work_email')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="employee@company.com"
                  />
                  {errors.work_email && (
                    <p className="mt-1 text-sm text-red-600">{errors.work_email.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="effective_start_date" className="block text-sm font-medium text-gray-700">
                    Start Date
                  </label>
                  <input
                    type="date"
                    id="effective_start_date"
                    {...register('effective_start_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.effective_start_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.effective_start_date.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="effective_end_date" className="block text-sm font-medium text-gray-700">
                    End Date (Optional)
                  </label>
                  <input
                    type="date"
                    id="effective_end_date"
                    {...register('effective_end_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.effective_end_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.effective_end_date.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Error Display */}
            {createEmployeeMutation.error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-600">
                  Error creating employee: {createEmployeeMutation.error instanceof Error 
                    ? createEmployeeMutation.error.message 
                    : 'Unknown error'}
                </p>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-end space-x-4">
              <button
                type="button"
                onClick={() => router.push('/employees')}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creating...' : 'Create Employee'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}