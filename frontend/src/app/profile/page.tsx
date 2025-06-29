'use client';

import { useState, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { apiClient } from '@/lib/api';
import { EmployeeUpdateRequest } from '@/lib/types';
import { useAuthStore } from '@/store/authStore';
import ProtectedRoute from '@/components/auth/ProtectedRoute';

// Form validation schema for personal information
const personalInfoSchema = z.object({
  // Person information
  full_name: z.string().min(1, 'Full name is required'),
  date_of_birth: z.string().optional(),
  
  // Personal information
  personal_email: z.string().email('Invalid email format').optional().or(z.literal('')),
  ssn: z.string().optional(),
  bank_account: z.string().optional(),
  
  // Work email (may be editable by user)
  work_email: z.string().email('Invalid email format').optional().or(z.literal('')),
});

type PersonalInfoFormData = z.infer<typeof personalInfoSchema>;

export default function ProfilePage() {
  return (
    <ProtectedRoute 
      pageIdentifier="profile" 
      requiredPermissions={['view']}
    >
      <ProfileContent />
    </ProtectedRoute>
  );
}

function ProfileContent() {
  const { user } = useAuthStore();
  const [isEditing, setIsEditing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Use employee data directly from auth store (already loaded from /auth/me)
  const employee = user?.employee;
  const isLoading = false;
  const error = null;

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<PersonalInfoFormData>({
    resolver: zodResolver(personalInfoSchema),
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
      });
    }
  }, [employee, reset]);

  const updateProfileMutation = useMutation({
    mutationFn: (data: EmployeeUpdateRequest) => {
      if (!employee?.employee_id) {
        throw new Error('No employee profile found');
      }
      return apiClient.updateEmployee(employee.employee_id, data);
    },
    onSuccess: async () => {
      setIsSubmitting(false);
      setIsEditing(false);
      // Refresh user data from auth store
      await useAuthStore.getState().checkAuth();
    },
    onError: (error) => {
      setIsSubmitting(false);
      console.error('Failed to update profile:', error);
    },
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-600">Loading your profile...</div>
      </div>
    );
  }

  // Error state - user might not have employee profile
  if (error || !employee) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                No Employee Profile Found
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>Your user account is not linked to an employee profile. Please contact HR to set up your employee profile.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const onSubmit = (data: PersonalInfoFormData) => {
    setIsSubmitting(true);

    // Build update request with only changed fields
    const employeeData: EmployeeUpdateRequest = {};
    
    // Personal information updates
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

    // Person information updates (name, DOB)
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

    // Work email update
    if (data.work_email !== (employee.work_email || '')) {
      employeeData.work_email = data.work_email || undefined;
    }

    updateProfileMutation.mutate(employeeData);
  };

  const cancelEdit = () => {
    setIsEditing(false);
    reset({
      full_name: employee.person.full_name,
      date_of_birth: employee.person.date_of_birth || '',
      personal_email: employee.person.personal_information?.personal_email || '',
      ssn: employee.person.personal_information?.ssn || '',
      bank_account: employee.person.personal_information?.bank_account || '',
      work_email: employee.work_email || '',
    });
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                My Profile
              </h1>
              <p className="mt-1 text-sm text-gray-700">
                Manage your personal information and contact details
              </p>
            </div>
            <div className="flex space-x-2">
              {isEditing ? (
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Edit Profile
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Profile Form */}
      <div className="bg-white shadow rounded-lg">
        <form onSubmit={isEditing ? handleSubmit(onSubmit) : undefined} className="px-4 py-5 sm:p-6">
          <div className="space-y-8">
            {/* Basic Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="full_name" className="block text-sm font-medium text-gray-700">
                    Full Name {isEditing && '*'}
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      id="full_name"
                      {...register('full_name')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Enter your full name"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.person.full_name}
                    </div>
                  )}
                  {errors.full_name && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.full_name.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="date_of_birth" className="block text-sm font-medium text-gray-700">
                    Date of Birth
                  </label>
                  {isEditing ? (
                    <input
                      type="date"
                      id="date_of_birth"
                      {...register('date_of_birth')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.person.date_of_birth 
                        ? new Date(employee.person.date_of_birth).toLocaleDateString()
                        : '-'
                      }
                    </div>
                  )}
                  {errors.date_of_birth && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.date_of_birth.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="work_email" className="block text-sm font-medium text-gray-700">
                    Work Email
                  </label>
                  {isEditing ? (
                    <input
                      type="email"
                      id="work_email"
                      {...register('work_email')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="you@company.com"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.work_email || '-'}
                    </div>
                  )}
                  {errors.work_email && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.work_email.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Personal Contact Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Personal Contact Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="personal_email" className="block text-sm font-medium text-gray-700">
                    Personal Email
                  </label>
                  {isEditing ? (
                    <input
                      type="email"
                      id="personal_email"
                      {...register('personal_email')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="personal@example.com"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.person.personal_information?.personal_email || '-'}
                    </div>
                  )}
                  {errors.personal_email && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.personal_email.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Sensitive Information Section */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Sensitive Information</h3>
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-800">
                      This information is private and only visible to you. Keep it secure and up to date.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label htmlFor="ssn" className="block text-sm font-medium text-gray-700">
                    Social Security Number
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      id="ssn"
                      {...register('ssn')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="XXX-XX-XXXX"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.person.personal_information?.ssn ? 
                        `***-**-${employee.person.personal_information.ssn.slice(-4)}` : 
                        '-'
                      }
                    </div>
                  )}
                  {errors.ssn && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.ssn.message}</p>
                  )}
                </div>

                <div>
                  <label htmlFor="bank_account" className="block text-sm font-medium text-gray-700">
                    Bank Account
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      id="bank_account"
                      {...register('bank_account')}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Account number"
                    />
                  ) : (
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {employee.person.personal_information?.bank_account ? 
                        `****${employee.person.personal_information.bank_account.slice(-4)}` : 
                        '-'
                      }
                    </div>
                  )}
                  {errors.bank_account && isEditing && (
                    <p className="mt-1 text-sm text-red-600">{errors.bank_account.message}</p>
                  )}
                </div>
              </div>
            </div>

            {/* Employee Information (Read-only) */}
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">Employment Information</h3>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Employee ID
                  </label>
                  <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                    {employee.employee_id}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Status
                  </label>
                  <div className="mt-1 py-2 px-3">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      employee.status === 'Active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {employee.status}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    Start Date
                  </label>
                  <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                    {employee.effective_start_date 
                      ? new Date(employee.effective_start_date).toLocaleDateString()
                      : '-'
                    }
                  </div>
                </div>

                {employee.effective_end_date && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      End Date
                    </label>
                    <div className="mt-1 py-2 px-3 text-gray-900 bg-gray-50 rounded-md">
                      {new Date(employee.effective_end_date).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Error Display */}
            {updateProfileMutation.error && (
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-600">
                  Error updating profile: {updateProfileMutation.error instanceof Error 
                    ? updateProfileMutation.error.message 
                    : 'Unknown error'}
                </p>
              </div>
            )}

            {/* Form Actions */}
            {isEditing && (
              <div className="flex justify-end space-x-4">
                <button
                  type="button"
                  onClick={cancelEdit}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Updating...' : 'Save Changes'}
                </button>
              </div>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}