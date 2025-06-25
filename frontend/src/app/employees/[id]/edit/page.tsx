'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiClient } from '@/lib/api';
import { EmployeeUpdateRequest } from '@/lib/types';
import { useIsHRAdmin } from '@/store/authStore';

// Form validation schema
const employeeUpdateSchema = z.object({
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
  status: z.enum(['Active', 'Inactive']).optional(),
});

type EmployeeFormData = z.infer<typeof employeeUpdateSchema>;

export default function EditEmployeePage() {
  const router = useRouter();
  const params = useParams();
  const queryClient = useQueryClient();
  const isHRAdmin = useIsHRAdmin();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const employeeId = parseInt(params.id as string);

  // Fetch existing employee data
  const { data: employee, isLoading, error } = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => apiClient.getEmployee(employeeId),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EmployeeFormData>({
    resolver: zodResolver(employeeUpdateSchema),
  });

  // Populate form with existing data when employee is loaded
  useEffect(() => {
    if (employee) {
      reset({
        full_name: employee.person.full_name,
        date_of_birth: employee.person.date_of_birth || '',
        personal_email: employee.person.personal_information?.personal_email || '',
        ssn: employee.person.personal_information?.ssn || '',
        bank_account: employee.person.personal_information?.bank_account || '',
        work_email: employee.work_email || '',
        effective_start_date: employee.effective_start_date || '',
        effective_end_date: employee.effective_end_date || '',
        status: employee.status,
      });
    }
  }, [employee, reset]);

  const updateEmployeeMutation = useMutation({
    mutationFn: (data: EmployeeUpdateRequest) => apiClient.updateEmployee(employeeId, data),
    onSuccess: () => {
      setIsSubmitting(false);
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['employee', employeeId] });
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      // Redirect to employees page with success message
      router.push('/employees');
    },
    onError: (error) => {
      setIsSubmitting(false);
      console.error('Failed to update employee:', error);
    },
  });

  // Redirect if not HR Admin
  if (!isHRAdmin) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Access denied. Only HR Administrators can edit employees.</p>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading employee data...</div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Error loading employee: {error instanceof Error ? error.message : 'Unknown error'}</p>
      </div>
    );
  }

  // Employee not found
  if (!employee) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <p className="text-red-600">Employee not found</p>
      </div>
    );
  }

  const onSubmit = (data: EmployeeFormData) => {
    setIsSubmitting(true);

    // Transform form data to API format
    const employeeData: EmployeeUpdateRequest = {};

    // Only include person data if fields have changed
    const personData: {
      full_name?: string;
      date_of_birth?: string;
    } = {};
    if (data.full_name !== employee.person.full_name) {
      personData.full_name = data.full_name;
    }
    if (data.date_of_birth !== (employee.person.date_of_birth || '')) {
      personData.date_of_birth = data.date_of_birth || undefined;
    }
    if (Object.keys(personData).length > 0) {
      employeeData.person = personData;
    }

    // Only include personal information if fields have changed
    const personalInfoData: {
      personal_email?: string;
      ssn?: string;
      bank_account?: string;
    } = {};
    const currentPersonalInfo = employee.person.personal_information;
    if (data.personal_email !== (currentPersonalInfo?.personal_email || '')) {
      personalInfoData.personal_email = data.personal_email || undefined;
    }
    if (data.ssn !== (currentPersonalInfo?.ssn || '')) {
      personalInfoData.ssn = data.ssn || undefined;
    }
    if (data.bank_account !== (currentPersonalInfo?.bank_account || '')) {
      personalInfoData.bank_account = data.bank_account || undefined;
    }
    if (Object.keys(personalInfoData).length > 0) {
      employeeData.personal_information = personalInfoData;
    }

    // Only include employee fields if they have changed
    if (data.work_email !== (employee.work_email || '')) {
      employeeData.work_email = data.work_email || undefined;
    }
    if (data.effective_start_date !== (employee.effective_start_date || '')) {
      employeeData.effective_start_date = data.effective_start_date || undefined;
    }
    if (data.effective_end_date !== (employee.effective_end_date || '')) {
      employeeData.effective_end_date = data.effective_end_date || undefined;
    }
    if (data.status !== employee.status) {
      employeeData.status = data.status;
    }

    updateEmployeeMutation.mutate(employeeData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-2xl font-bold text-gray-900">Edit Employee Profile</h1>
          <p className="mt-1 text-sm text-gray-700">
            Update information for {employee.person.full_name} (ID: {employee.employee_id})
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
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Sensitive Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
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
              </div>
            </div>

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

                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                    Employee Status
                  </label>
                  <select
                    id="status"
                    {...register('status')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="Active">Active</option>
                    <option value="Inactive">Inactive</option>
                  </select>
                  {errors.status && (
                    <p className="mt-1 text-sm text-red-600">{errors.status.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Error Display */}
            {updateEmployeeMutation.error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-600">
                  Error updating employee: {updateEmployeeMutation.error instanceof Error 
                    ? updateEmployeeMutation.error.message 
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
                {isSubmitting ? 'Updating...' : 'Update Employee'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}