'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { assignmentApi } from '@/lib/api/assignments';
import { departmentApi } from '@/lib/api/departments';
import { assignmentTypeApi } from '@/lib/api/assignmentTypes';
import { apiClient } from '@/lib/api';
import { AssignmentCreateRequest, Employee } from '@/lib/types';
import { 
  useHasPermission
} from '@/store/authStore';

// Form validation schema for new assignments
const assignmentCreateSchema = z.object({
  assignment_type_id: z.number().min(1, 'Assignment type is required'),
  description: z.string().optional(),
  effective_start_date: z.string().min(1, 'Start date is required'),
  effective_end_date: z.string().optional(),
  is_primary: z.boolean().optional(),
  supervisor_ids: z.array(z.number()).optional(),
});

type AssignmentFormData = z.infer<typeof assignmentCreateSchema>;

interface AssignmentManagementProps {
  employee: Employee;
}

export default function AssignmentManagement({ employee }: AssignmentManagementProps) {
  const queryClient = useQueryClient();
  // Permission checks
  const canCreateAssignment = useHasPermission('assignment.create');
  const canUpdateAssignments = useHasPermission('assignment.update.all');
  const canDeleteAssignments = useHasPermission('assignment.delete');
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<number | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Fetch employee assignments
  const { data: assignments = [], isLoading: assignmentsLoading } = useQuery({
    queryKey: ['employeeAssignments', employee.employee_id],
    queryFn: () => assignmentApi.getByEmployee(employee.employee_id),
  });

  // Fetch departments for assignment creation
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => departmentApi.getAll(),
    enabled: showAddForm,
  });

  // Fetch assignment types for selected department
  const { data: assignmentTypes = [] } = useQuery({
    queryKey: ['assignmentTypes', selectedDepartment],
    queryFn: () => assignmentTypeApi.getAll(selectedDepartment || undefined),
    enabled: showAddForm && !!selectedDepartment,
  });

  // Fetch employees for supervisor selection (role-aware)
  const { data: employees = [] } = useQuery({
    queryKey: ['employees-for-assignment'],
    queryFn: () => apiClient.getSupervisees(),
    enabled: showAddForm,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<AssignmentFormData>({
    resolver: zodResolver(assignmentCreateSchema),
    defaultValues: {
      effective_start_date: new Date().toISOString().split('T')[0],
      is_primary: false,
    },
  });

  // Watch assignment type selection to get department
  watch('assignment_type_id');

  // Create assignment mutation
  const createAssignmentMutation = useMutation({
    mutationFn: (data: AssignmentCreateRequest) => assignmentApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employeeAssignments', employee.employee_id] });
      setShowAddForm(false);
      reset();
      setSelectedDepartment(null);
    },
  });

  // Delete assignment mutation
  const deleteAssignmentMutation = useMutation({
    mutationFn: (assignmentId: number) => assignmentApi.delete(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employeeAssignments', employee.employee_id] });
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      setDeleteError(null);
      console.log('Assignment deleted successfully');
    },
    onError: (error: unknown) => {
      console.error('Failed to delete assignment:', error);
      const httpError = error as { response?: { status?: number } };
      if (httpError?.response?.status === 403) {
        setDeleteError('Permission denied: Only HR Administrators can delete assignments');
        console.error('Permission denied: User may not have HR Admin privileges');
      } else if (httpError?.response?.status === 404) {
        setDeleteError('Assignment not found');
        console.error('Assignment not found');
      } else {
        setDeleteError('Failed to delete assignment. Please try again.');
      }
    },
  });

  // Set primary assignment mutation
  const setPrimaryMutation = useMutation({
    mutationFn: (assignmentId: number) => assignmentApi.setPrimary(assignmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employeeAssignments', employee.employee_id] });
    },
  });

  const onSubmit = (data: AssignmentFormData) => {
    const assignmentData: AssignmentCreateRequest = {
      employee_id: employee.employee_id,
      assignment_type_id: data.assignment_type_id,
      description: data.description || undefined,
      effective_start_date: data.effective_start_date,
      effective_end_date: data.effective_end_date || undefined,
      is_primary: data.is_primary || false,
      supervisor_ids: data.supervisor_ids?.length ? data.supervisor_ids : undefined,
    };

    createAssignmentMutation.mutate(assignmentData);
  };

  const handleDeleteAssignment = (assignmentId: number, assignmentName: string) => {
    if (confirm(`Are you sure you want to remove the ${assignmentName} assignment?`)) {
      console.log('Attempting to delete assignment:', assignmentId);
      setDeleteError(null); // Clear any previous errors
      deleteAssignmentMutation.mutate(assignmentId);
    }
  };

  const handleSetPrimary = (assignmentId: number) => {
    setPrimaryMutation.mutate(assignmentId);
  };

  // Show read-only view if user can't manage assignments
  if (!canCreateAssignment && !canDeleteAssignments) {
    return (
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Assignments</h3>
          {assignmentsLoading ? (
            <div className="text-gray-600">Loading assignments...</div>
          ) : (
            <div className="space-y-3">
              {assignments.length === 0 ? (
                <p className="text-gray-500">No assignments found.</p>
              ) : (
                assignments.map((assignment) => (
                  <div key={assignment.assignment_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900 flex items-center">
                          {assignment.assignment_type.description}
                          {assignment.is_primary && (
                            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              Primary
                            </span>
                          )}
                        </h4>
                        <p className="text-sm text-gray-600">{assignment.assignment_type.department.name}</p>
                        {assignment.description && (
                          <p className="text-sm text-gray-600">{assignment.description}</p>
                        )}
                        {assignment.effective_start_date && (
                          <p className="text-xs text-gray-500">
                            Started: {new Date(assignment.effective_start_date).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg">
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Assignments</h3>
          {canCreateAssignment && (
            <button
              onClick={() => setShowAddForm(true)}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Add Assignment
            </button>
          )}
        </div>

        {/* Error Display */}
        {deleteError && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-600 text-sm">{deleteError}</p>
            <button 
              onClick={() => setDeleteError(null)}
              className="mt-2 text-red-500 hover:text-red-700 text-xs underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Assignment List */}
        {assignmentsLoading ? (
          <div className="text-gray-600">Loading assignments...</div>
        ) : (
          <div className="space-y-3 mb-6">
            {assignments.length === 0 ? (
              <p className="text-gray-500">No assignments found.</p>
            ) : (
              assignments.map((assignment) => (
                <div key={assignment.assignment_id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <h4 className="font-medium text-gray-900 flex items-center">
                          {assignment.assignment_type.description}
                          {assignment.is_primary && (
                            <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              Primary
                            </span>
                          )}
                        </h4>
                      </div>
                      <p className="text-sm text-gray-600">{assignment.assignment_type.department.name}</p>
                      {assignment.description && (
                        <p className="text-sm text-gray-600">{assignment.description}</p>
                      )}
                      <div className="flex items-center space-x-4 text-xs text-gray-500 mt-1">
                        {assignment.effective_start_date && (
                          <span>Started: {new Date(assignment.effective_start_date).toLocaleDateString()}</span>
                        )}
                        {assignment.supervisors.length > 0 && (
                          <span>
                            Supervisors: {assignment.supervisors.map(s => s.person.full_name).join(', ')}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-2 ml-4">
                      {!assignment.is_primary && canUpdateAssignments && (
                        <button
                          onClick={() => handleSetPrimary(assignment.assignment_id)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          disabled={setPrimaryMutation.isPending}
                        >
                          Set Primary
                        </button>
                      )}
                      {canDeleteAssignments && (
                        <button
                          onClick={() => handleDeleteAssignment(assignment.assignment_id, assignment.assignment_type.description)}
                          className="text-red-600 hover:text-red-800 text-sm font-medium"
                          disabled={deleteAssignmentMutation.isPending}
                        >
                          {deleteAssignmentMutation.isPending ? 'Removing...' : 'Remove'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Add Assignment Form */}
        {showAddForm && (
          <div className="border border-blue-200 rounded-xl p-6 bg-gradient-to-br from-blue-50 to-indigo-50 shadow-lg">
            <div className="flex items-center mb-6">
              <div className="bg-blue-100 rounded-lg p-2 mr-3">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-gray-900">Add New Assignment</h4>
            </div>
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              {/* Position Details Section */}
              <div className="bg-white rounded-lg p-5 shadow-sm">
                <h5 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  Position Details
                </h5>
                
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {/* Department Selection */}
                  <div className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Department <span className="text-red-500">*</span>
                    </label>
                    <select
                      onChange={(e) => setSelectedDepartment(Number(e.target.value) || null)}
                      className="mt-1 block w-full border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                    >
                      <option value="">Choose a department...</option>
                      {departments.map((dept) => (
                        <option key={dept.department_id} value={dept.department_id}>
                          {dept.name}
                        </option>
                      ))}
                    </select>
                    {!selectedDepartment && (
                      <p className="text-xs text-gray-500">Select a department first</p>
                    )}
                  </div>

                  {/* Assignment Type Selection */}
                  <div className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Role/Position <span className="text-red-500">*</span>
                    </label>
                    <select
                      {...register('assignment_type_id', { valueAsNumber: true })}
                      className="mt-1 block w-full border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
                      disabled={!selectedDepartment}
                    >
                      <option value="">
                        {selectedDepartment ? 'Choose a role...' : 'Select department first'}
                      </option>
                      {assignmentTypes.map((type) => (
                        <option key={type.assignment_type_id} value={type.assignment_type_id}>
                          {type.description}
                        </option>
                      ))}
                    </select>
                    {errors.assignment_type_id && (
                      <p className="mt-1 text-sm text-red-600 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {errors.assignment_type_id.message}
                      </p>
                    )}
                  </div>

                  {/* Description */}
                  <div className="sm:col-span-2 space-y-1">
                    <label className="block text-sm font-medium text-gray-700">Assignment Description</label>
                    <textarea
                      {...register('description')}
                      rows={3}
                      className="mt-1 block w-full border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                      placeholder="Optional: Describe specific responsibilities, projects, or notes for this assignment..."
                    />
                  </div>
                </div>
              </div>

              {/* Timeline Section */}
              <div className="bg-white rounded-lg p-5 shadow-sm">
                <h5 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  Assignment Timeline
                </h5>
                
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  {/* Start Date */}
                  <div className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">
                      Start Date <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      {...register('effective_start_date')}
                      className="mt-1 block w-full border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                    />
                    {errors.effective_start_date && (
                      <p className="mt-1 text-sm text-red-600 flex items-center">
                        <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        {errors.effective_start_date.message}
                      </p>
                    )}
                  </div>

                  {/* End Date */}
                  <div className="space-y-1">
                    <label className="block text-sm font-medium text-gray-700">End Date (Optional)</label>
                    <input
                      type="date"
                      {...register('effective_end_date')}
                      className="mt-1 block w-full border border-gray-300 rounded-lg shadow-sm py-2.5 px-3 text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors duration-200"
                    />
                    <p className="text-xs text-gray-500">Leave blank for ongoing assignment</p>
                  </div>
                </div>
              </div>

              {/* Assignment Settings Section */}
              <div className="bg-white rounded-lg p-5 shadow-sm">
                <h5 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <svg className="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  Assignment Settings
                </h5>
                
                <div className="space-y-4">
                  {/* Primary Assignment Toggle */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <div className="flex items-center h-5">
                        <input
                          type="checkbox"
                          {...register('is_primary')}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                      </div>
                      <div className="ml-3">
                        <label className="font-medium text-blue-900">Primary Assignment</label>
                        <p className="text-sm text-blue-700">Mark this as the employee&apos;s main role and responsibility</p>
                      </div>
                    </div>
                  </div>

                  {/* Supervisors Selection */}
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-700">
                      Assign Supervisors (Optional)
                    </label>
                    <div className="border border-gray-300 rounded-lg max-h-40 overflow-y-auto bg-gray-50">
                      {employees
                        .filter(emp => emp.employee_id !== employee.employee_id)
                        .map((emp) => (
                          <label key={emp.employee_id} className="flex items-center px-3 py-2 hover:bg-gray-100 cursor-pointer border-b border-gray-200 last:border-b-0">
                            <input
                              type="checkbox"
                              value={emp.employee_id}
                              {...register('supervisor_ids', { 
                                setValueAs: (value) => {
                                  if (Array.isArray(value)) {
                                    return value.map(Number).filter(Boolean);
                                  }
                                  return [];
                                }
                              })}
                              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                            />
                            <div className="ml-3 flex-1">
                              <div className="text-sm font-medium text-gray-900">{emp.person.full_name}</div>
                              <div className="text-xs text-gray-500">
                                Employee
                              </div>
                            </div>
                          </label>
                        ))}
                    </div>
                    <p className="text-xs text-gray-500">Select one or more supervisors for this assignment</p>
                  </div>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    reset();
                    setSelectedDepartment(null);
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors duration-200"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAssignmentMutation.isPending}
                  className="inline-flex items-center px-6 py-2 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {createAssignmentMutation.isPending ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Creating...
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      Create Assignment
                    </>
                  )}
                </button>
              </div>

              {/* Error Display */}
              {createAssignmentMutation.error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start">
                    <svg className="w-5 h-5 text-red-400 mt-0.5 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                    <div>
                      <h3 className="text-sm font-medium text-red-800">Assignment Creation Failed</h3>
                      <p className="mt-1 text-sm text-red-700">
                        {createAssignmentMutation.error instanceof Error 
                          ? createAssignmentMutation.error.message 
                          : 'An unexpected error occurred. Please try again.'}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </form>
          </div>
        )}
      </div>
    </div>
  );
}