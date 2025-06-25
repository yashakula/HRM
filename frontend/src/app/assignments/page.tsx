'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthStore } from '@/store/authStore';
import { assignmentApi, Assignment, AssignmentCreate } from '@/lib/api/assignments';
import { departmentApi } from '@/lib/api/departments';
import { assignmentTypeApi } from '@/lib/api/assignmentTypes';
import { apiClient } from '@/lib/api';

export default function AssignmentsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');
  const [selectedEmployee, setSelectedEmployee] = useState<string>('');
  const [selectedSupervisor, setSelectedSupervisor] = useState<string>('');
  const [formData, setFormData] = useState<AssignmentCreate>({
    employee_id: 0,
    assignment_type_id: 0,
    description: '',
    effective_start_date: '',
    effective_end_date: '',
    supervisor_ids: []
  });

  // Check if user is HR Admin
  const isHrAdmin = user?.role === 'HR_ADMIN';

  // Fetch assignments
  const { data: assignments, isLoading, error } = useQuery({
    queryKey: ['assignments'],
    queryFn: () => assignmentApi.getAll(),
  });

  // Fetch departments for filtering
  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: departmentApi.getAll,
  });

  // Fetch assignment types based on selected department
  const { data: assignmentTypes } = useQuery({
    queryKey: ['assignmentTypes', selectedDepartment],
    queryFn: () => assignmentTypeApi.getAll(selectedDepartment ? parseInt(selectedDepartment) : undefined),
    enabled: true
  });

  // Fetch employees
  const { data: employees } = useQuery({
    queryKey: ['employees'],
    queryFn: () => apiClient.searchEmployees({}),
  });

  // Create assignment mutation
  const createMutation = useMutation({
    mutationFn: assignmentApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignments'] });
      setIsCreateDialogOpen(false);
      resetForm();
      alert('Assignment created successfully');
    },
    onError: (error: Error) => {
      alert('Failed to create assignment: ' + error.message);
    },
  });

  const resetForm = () => {
    setFormData({
      employee_id: 0,
      assignment_type_id: 0,
      description: '',
      effective_start_date: '',
      effective_end_date: '',
      supervisor_ids: []
    });
    setSelectedDepartment('');
    setSelectedEmployee('');
    setSelectedSupervisor('');
  };

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.employee_id || !formData.assignment_type_id) {
      alert('Employee and assignment type are required');
      return;
    }
    
    const supervisorIds = selectedSupervisor ? [parseInt(selectedSupervisor)] : [];
    createMutation.mutate({
      ...formData,
      supervisor_ids: supervisorIds
    });
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadge = (assignment: Assignment) => {
    const now = new Date();
    const startDate = assignment.effective_start_date ? new Date(assignment.effective_start_date) : null;
    const endDate = assignment.effective_end_date ? new Date(assignment.effective_end_date) : null;

    if (endDate && endDate < now) {
      return <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded">Ended</span>;
    } else if (startDate && startDate > now) {
      return <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">Future</span>;
    } else {
      return <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">Active</span>;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading assignments...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">Failed to load assignments</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            👥 Employee Assignments
          </h1>
          <p className="text-gray-600 mt-2">
            Manage employee role assignments and supervisor relationships
          </p>
        </div>
        
        {isHrAdmin && (
          <button
            onClick={() => setIsCreateDialogOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            ➕ Create Assignment
          </button>
        )}
      </div>

      {!isHrAdmin && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800">
            You have read-only access to assignments. Contact HR Admin to make changes.
          </p>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium">Current Assignments</h2>
          <p className="text-sm text-gray-600">All employee role assignments and their details</p>
        </div>
        <div className="overflow-x-auto">
          {assignments && assignments.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Supervisor(s)</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {assignments.map((assignment) => (
                  <tr key={assignment.assignment_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {assignment.employee.person.full_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          ID: {assignment.employee.employee_id}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {assignment.assignment_type.description}
                        </div>
                        {assignment.description && (
                          <div className="text-sm text-gray-500">
                            {assignment.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-sm text-gray-900">
                          🏢 {assignment.assignment_type.department.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {assignment.supervisors.length > 0 ? (
                        <div className="space-y-1">
                          {assignment.supervisors.map((supervisor) => (
                            <span 
                              key={supervisor.employee_id} 
                              className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded mr-1"
                            >
                              {supervisor.person.full_name}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">No supervisor</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900">
                        📅 {formatDate(assignment.effective_start_date)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center text-sm text-gray-900">
                        📅 {formatDate(assignment.effective_end_date)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(assignment)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">👥</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No assignments found</h3>
              <p className="text-gray-500 mb-4">Get started by creating your first assignment</p>
              {isHrAdmin && (
                <button
                  onClick={() => setIsCreateDialogOpen(true)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  ➕ Create Assignment
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Create Assignment Dialog */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">Create New Assignment</h2>
            <form onSubmit={handleCreate}>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="employee" className="block text-sm font-medium text-gray-700 mb-1">
                    Employee *
                  </label>
                  <select
                    id="employee"
                    value={selectedEmployee}
                    onChange={(e) => {
                      setSelectedEmployee(e.target.value);
                      setFormData({ ...formData, employee_id: parseInt(e.target.value) });
                    }}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select employee</option>
                    {employees?.map((employee) => (
                      <option key={employee.employee_id} value={employee.employee_id.toString()}>
                        {employee.person.full_name} (ID: {employee.employee_id})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="department" className="block text-sm font-medium text-gray-700 mb-1">
                    Department
                  </label>
                  <select
                    id="department"
                    value={selectedDepartment}
                    onChange={(e) => setSelectedDepartment(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">All departments</option>
                    {departments?.map((dept) => (
                      <option key={dept.department_id} value={dept.department_id.toString()}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mb-4">
                <label htmlFor="assignmentType" className="block text-sm font-medium text-gray-700 mb-1">
                  Assignment Type *
                </label>
                <select
                  id="assignmentType"
                  value={formData.assignment_type_id.toString()}
                  onChange={(e) => setFormData({ ...formData, assignment_type_id: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="0">Select assignment type</option>
                  {assignmentTypes?.map((type) => (
                    <option key={type.assignment_type_id} value={type.assignment_type_id.toString()}>
                      {type.description} ({type.department.name})
                    </option>
                  ))}
                </select>
              </div>

              <div className="mb-4">
                <label htmlFor="supervisor" className="block text-sm font-medium text-gray-700 mb-1">
                  Supervisor (Optional)
                </label>
                <select
                  id="supervisor"
                  value={selectedSupervisor}
                  onChange={(e) => setSelectedSupervisor(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No supervisor</option>
                  {employees?.map((employee) => (
                    <option key={employee.employee_id} value={employee.employee_id.toString()}>
                      {employee.person.full_name} (ID: {employee.employee_id})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label htmlFor="startDate" className="block text-sm font-medium text-gray-700 mb-1">
                    Start Date
                  </label>
                  <input
                    id="startDate"
                    type="date"
                    value={formData.effective_start_date}
                    onChange={(e) => setFormData({ ...formData, effective_start_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label htmlFor="endDate" className="block text-sm font-medium text-gray-700 mb-1">
                    End Date (Optional)
                  </label>
                  <input
                    id="endDate"
                    type="date"
                    value={formData.effective_end_date}
                    onChange={(e) => setFormData({ ...formData, effective_end_date: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <div className="mb-6">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Additional details about the assignment"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    resetForm();
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Assignment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}