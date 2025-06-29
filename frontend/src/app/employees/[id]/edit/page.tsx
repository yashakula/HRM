'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiClient } from '@/lib/api';
import { EmployeeUpdateRequest } from '@/lib/types';
import { 
  useAuthStore, 
  useHasPermission
} from '@/store/authStore';
import AssignmentManagement from '@/components/employees/AssignmentManagement';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

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
  const params = useParams();
  const employeeId = parseInt(params.id as string);

  return (
    <ProtectedRoute 
      pageIdentifier="employees/edit" 
      resourceId={employeeId}
      requiredPermissions={['view', 'edit']}
    >
      <EditEmployeeForm employeeId={employeeId} />
    </ProtectedRoute>
  );
}

function EditEmployeeForm({ employeeId }: { employeeId: number }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);

  // Permission checking
  const canUpdateAllEmployees = useHasPermission('employee.update.all');
  const canUpdateOwnProfile = useHasPermission('employee.update.own');
  const canViewAllEmployees = useHasPermission('employee.read.all');

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

  // Check if this is the user's own employee record
  const isOwnRecord = user?.employee?.employee_id === employeeId;
  
  // Permission-based editing logic
  const canEditThisEmployee = (canUpdateAllEmployees || (canUpdateOwnProfile && isOwnRecord)) && isEditMode;
  
  // View permissions for sensitive information
  const canViewSensitiveInfo = isOwnRecord || canViewAllEmployees;
  
  // Allow editing sensitive info if it's their own record and they're in edit mode
  const canEditSensitiveInfo = isOwnRecord && isEditMode;

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

    // Only users with update permissions can update basic employee data
    if (canEditThisEmployee) {
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

      // Include personal email for HR admins
      const currentPersonalInfo = employee.person.personal_information;
      if (data.personal_email !== (currentPersonalInfo?.personal_email || '')) {
        if (!employeeData.personal_information) {
          employeeData.personal_information = {};
        }
        employeeData.personal_information.personal_email = data.personal_email || undefined;
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
    }

    // Employees can only update their own sensitive information
    if (canEditSensitiveInfo) {
      const personalInfoData: {
        personal_email?: string;
        ssn?: string;
        bank_account?: string;
      } = {};
      const currentPersonalInfo = employee.person.personal_information;
      
      // Only include sensitive fields for employees editing their own record
      if (data.ssn !== (currentPersonalInfo?.ssn || '')) {
        personalInfoData.ssn = data.ssn || undefined;
      }
      if (data.bank_account !== (currentPersonalInfo?.bank_account || '')) {
        personalInfoData.bank_account = data.bank_account || undefined;
      }
      
      if (Object.keys(personalInfoData).length > 0) {
        if (!employeeData.personal_information) {
          employeeData.personal_information = {};
        }
        Object.assign(employeeData.personal_information, personalInfoData);
      }
    }

    updateEmployeeMutation.mutate(employeeData);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditMode ? 'Edit Employee Profile' : employee.person.full_name}
              </h1>
              <p className="mt-1 text-sm text-gray-700">
                {isEditMode 
                  ? `Update information for ${employee.person.full_name} (ID: ${employee.employee_id})`
                  : `Employee ID: ${employee.employee_id} • Status: `
                }
                {!isEditMode && (
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    employee.status === 'Active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {employee.status}
                  </span>
                )}
              </p>
            </div>
            {(canUpdateAllEmployees || (canUpdateOwnProfile && isOwnRecord)) && (
              <div className="flex space-x-2">
                {isEditMode ? (
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditMode(false);
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
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Cancel Edit
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsEditMode(true)}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    {canUpdateAllEmployees ? 'Edit Employee' : 'Edit My Information'}
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Form */}
      <div className="bg-white shadow rounded-lg">
        <form onSubmit={canEditThisEmployee ? handleSubmit(onSubmit) : undefined} className="px-4 py-5 sm:p-6">
          <div className="space-y-8">
            {/* Personal Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                    Full Name {canEditThisEmployee && '*'}
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="text"
                      id="full_name"
                      {...register('full_name')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter full name"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">{employee.person.full_name}</div>
                  )}
                  {errors.full_name && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700">
                    Date of Birth
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="date"
                      id="date_of_birth"
                      {...register('date_of_birth')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.person.date_of_birth 
                        ? new Date(employee.person.date_of_birth).toLocaleDateString()
                        : '-'
                      }
                    </div>
                  )}
                  {errors.date_of_birth && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="personal_email" className="block text-sm font-medium text-gray-700">
                    Personal Email
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="email"
                      id="personal_email"
                      {...register('personal_email')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="personal@example.com"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.person.personal_information?.personal_email || '-'}
                    </div>
                  )}
                  {errors.personal_email && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.personal_email.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Sensitive Information Section - Only show for employee themselves */}
            {canViewSensitiveInfo && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Sensitive Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="ssn" className="block text-sm font-medium text-gray-700">
                    Social Security Number
                  </label>
                  {canEditSensitiveInfo ? (
                    <input
                      type="text"
                      id="ssn"
                      {...register('ssn')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="XXX-XX-XXXX"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.person.personal_information?.ssn || '-'}
                    </div>
                  )}
                  {errors.ssn && canEditSensitiveInfo && (
                    <p className="mt-1 text-sm text-red-600">{errors.ssn.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="bank_account" className="block text-sm font-medium text-gray-700">
                    Bank Account
                  </label>
                  {canEditSensitiveInfo ? (
                    <input
                      type="text"
                      id="bank_account"
                      {...register('bank_account')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Account number"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.person.personal_information?.bank_account || '-'}
                    </div>
                  )}
                  {errors.bank_account && canEditSensitiveInfo && (
                    <p className="mt-1 text-sm text-red-600">{errors.bank_account.message}</p>
                  )}
                </div>
              </div>
            </div>
            )}

            {/* Employment Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Employment Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="work_email" className="block text-sm font-medium text-gray-700">
                    Work Email
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="email"
                      id="work_email"
                      {...register('work_email')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="employee@company.com"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">{employee.work_email || '-'}</div>
                  )}
                  {errors.work_email && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.work_email.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="effective_start_date" className="block text-sm font-medium text-gray-700">
                    Start Date
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="date"
                      id="effective_start_date"
                      {...register('effective_start_date')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.effective_start_date 
                        ? new Date(employee.effective_start_date).toLocaleDateString()
                        : '-'
                      }
                    </div>
                  )}
                  {errors.effective_start_date && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.effective_start_date.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="effective_end_date" className="block text-sm font-medium text-gray-700">
                    End Date (Optional)
                  </label>
                  {canEditThisEmployee ? (
                    <input
                      type="date"
                      id="effective_end_date"
                      {...register('effective_end_date')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      {employee.effective_end_date 
                        ? new Date(employee.effective_end_date).toLocaleDateString()
                        : '-'
                      }
                    </div>
                  )}
                  {errors.effective_end_date && canEditThisEmployee && (
                    <p className="mt-1 text-sm text-red-600">{errors.effective_end_date.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                    Employee Status
                  </label>
                  {canEditThisEmployee ? (
                    <select
                      id="status"
                      {...register('status')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="Active">Active</option>
                      <option value="Inactive">Inactive</option>
                    </select>
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        employee.status === 'Active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {employee.status}
                      </span>
                    </div>
                  )}
                  {errors.status && canEditThisEmployee && (
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

            {/* Form Actions - Show in edit mode for HR admins or employees editing their own info */}
            {(canEditThisEmployee || canEditSensitiveInfo) && (
              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditMode(false);
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
                  }}
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
            )}

            {/* Back to Directory Button - Only show in view mode */}
            {!canEditThisEmployee && (
              <div className="flex justify-center">
                <button
                  type="button"
                  onClick={() => router.push('/employees')}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Back to Employee Directory
                </button>
              </div>
            )}
          </div>
        </form>
      </div>

      {/* Assignment Management Section */}
      <AssignmentManagement employee={employee} />
    </div>
  );
}