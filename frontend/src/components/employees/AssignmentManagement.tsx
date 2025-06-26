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
import { useIsHRAdmin } from '@/store/authStore';

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
  const isHRAdmin = useIsHRAdmin();
  const [showAddForm, setShowAddForm] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<number | null>(null);

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

  // Fetch all employees for supervisor selection
  const { data: employees = [] } = useQuery({
    queryKey: ['employees'],
    queryFn: () => apiClient.searchEmployees({}),
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
      deleteAssignmentMutation.mutate(assignmentId);
    }
  };

  const handleSetPrimary = (assignmentId: number) => {
    setPrimaryMutation.mutate(assignmentId);
  };

  if (!isHRAdmin) {
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
          <button
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Add Assignment
          </button>
        </div>

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
                      {!assignment.is_primary && (
                        <button
                          onClick={() => handleSetPrimary(assignment.assignment_id)}
                          className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          disabled={setPrimaryMutation.isPending}
                        >
                          Set Primary
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteAssignment(assignment.assignment_id, assignment.assignment_type.description)}
                        className="text-red-600 hover:text-red-800 text-sm font-medium"
                        disabled={deleteAssignmentMutation.isPending}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Add Assignment Form */}
        {showAddForm && (
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <h4 className="text-lg font-medium text-gray-900 mb-4">Add New Assignment</h4>
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {/* Department Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Department</label>
                  <select
                    onChange={(e) => setSelectedDepartment(Number(e.target.value) || null)}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select Department</option>
                    {departments.map((dept) => (
                      <option key={dept.department_id} value={dept.department_id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Assignment Type Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Assignment Type *</label>
                  <select
                    {...register('assignment_type_id', { valueAsNumber: true })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    disabled={!selectedDepartment}
                  >
                    <option value="">Select Assignment Type</option>
                    {assignmentTypes.map((type) => (
                      <option key={type.assignment_type_id} value={type.assignment_type_id}>
                        {type.description}
                      </option>
                    ))}
                  </select>
                  {errors.assignment_type_id && (
                    <p className="mt-1 text-sm text-red-600">{errors.assignment_type_id.message}</p>
                  )}
                </div>

                {/* Description */}
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Description</label>
                  <input
                    type="text"
                    {...register('description')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Optional assignment description"
                  />
                </div>

                {/* Start Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">Start Date *</label>
                  <input
                    type="date"
                    {...register('effective_start_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.effective_start_date && (
                    <p className="mt-1 text-sm text-red-600">{errors.effective_start_date.message}</p>
                  )}
                </div>

                {/* End Date */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">End Date (Optional)</label>
                  <input
                    type="date"
                    {...register('effective_end_date')}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* Primary Assignment Checkbox */}
                <div className="sm:col-span-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      {...register('is_primary')}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-900">
                      Set as primary assignment
                    </label>
                  </div>
                </div>

                {/* Supervisors Selection */}
                <div className="sm:col-span-2">
                  <label className="block text-sm font-medium text-gray-700">Supervisors (Optional)</label>
                  <select
                    multiple
                    {...register('supervisor_ids', { 
                      setValueAs: (value) => Array.from(value as HTMLSelectElement, (option: HTMLOptionElement) => Number(option.value)).filter(Boolean)
                    })}
                    className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    size={4}
                  >
                    {employees
                      .filter(emp => emp.employee_id !== employee.employee_id)
                      .map((emp) => (
                        <option key={emp.employee_id} value={emp.employee_id}>
                          {emp.person.full_name}
                        </option>
                      ))}
                  </select>
                  <p className="mt-1 text-xs text-gray-500">Hold Ctrl/Cmd to select multiple supervisors</p>
                </div>
              </div>

              {/* Form Actions */}
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddForm(false);
                    reset();
                    setSelectedDepartment(null);
                  }}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createAssignmentMutation.isPending}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                >
                  {createAssignmentMutation.isPending ? 'Creating...' : 'Create Assignment'}
                </button>
              </div>

              {/* Error Display */}
              {createAssignmentMutation.error && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-600 text-sm">
                    Error creating assignment: {createAssignmentMutation.error instanceof Error 
                      ? createAssignmentMutation.error.message 
                      : 'Unknown error'}
                  </p>
                </div>
              )}
            </form>
          </div>
        )}
      </div>
    </div>
  );
}