'use client';

import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Employee, EmployeeSearchParams, Assignment, AssignmentCreateRequest } from '@/lib/types';
import { 
  useHasPermission, 
  useHasAnyPermission 
} from '@/store/authStore';
import { assignmentApi } from '@/lib/api/assignments';
import { departmentApi } from '@/lib/api/departments';
import { assignmentTypeApi } from '@/lib/api/assignmentTypes';

export default function SearchPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  
  // Tab state
  const [activeTab, setActiveTab] = useState<'employees' | 'assignments'>('employees');
  
  // Employee search states
  const [employeeSearchParams, setEmployeeSearchParams] = useState<EmployeeSearchParams>({
    name: '',
    employee_id: undefined,
    status: undefined,
    skip: 0,
    limit: 10
  });

  // Assignment search states  
  const [assignmentFilterDepartmentId, setAssignmentFilterDepartmentId] = useState<string>('');
  const [assignmentFilterAssignmentTypeId, setAssignmentFilterAssignmentTypeId] = useState<string>('');
  const [assignmentFilterEmployeeName, setAssignmentFilterEmployeeName] = useState<string>('');
  
  // Assignment creation dialog state
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');
  const [selectedEmployee, setSelectedEmployee] = useState<string>('');
  const [selectedSupervisor, setSelectedSupervisor] = useState<string>('');
  const [formData, setFormData] = useState<AssignmentCreateRequest>({
    employee_id: 0,
    assignment_type_id: 0,
    description: '',
    effective_start_date: '',
    effective_end_date: '',
    supervisor_ids: []
  });
  
  // Permission checks
  const canCreateAssignment = useHasPermission('assignment.create');
  const canSearchEmployees = useHasAnyPermission(['employee.read.all', 'employee.read.supervised']);
  const canViewEmployeeDetails = useHasAnyPermission(['employee.read.all', 'employee.read.supervised', 'employee.read.own']);
  const canViewAssignments = useHasAnyPermission(['assignment.read.all', 'assignment.read.supervised', 'assignment.read.own']);

  // Set default tab based on permissions
  useEffect(() => {
    if (!canSearchEmployees && canViewAssignments) {
      setActiveTab('assignments');
    } else if (canSearchEmployees && !canViewAssignments) {
      setActiveTab('employees');
    }
  }, [canSearchEmployees, canViewAssignments]);

  // Employee queries
  const { data: employees, isLoading: employeesLoading, error: employeesError, refetch: refetchEmployees } = useQuery({
    queryKey: ['employees', employeeSearchParams],
    queryFn: () => {
      const hasSearchCriteria = employeeSearchParams.name || employeeSearchParams.employee_id || employeeSearchParams.status;
      
      if (hasSearchCriteria) {
        return apiClient.searchEmployees(employeeSearchParams);
      } else {
        return apiClient.getAllEmployees(employeeSearchParams.skip, employeeSearchParams.limit);
      }
    },
    enabled: activeTab === 'employees' && canSearchEmployees,
  });

  // Assignment queries
  const { data: assignments, isLoading: assignmentsLoading, error: assignmentsError } = useQuery({
    queryKey: ['assignments', assignmentFilterDepartmentId, assignmentFilterAssignmentTypeId, assignmentFilterEmployeeName],
    queryFn: () => assignmentApi.getAll({
      department_id: assignmentFilterDepartmentId ? parseInt(assignmentFilterDepartmentId) : undefined,
      assignment_type_id: assignmentFilterAssignmentTypeId ? parseInt(assignmentFilterAssignmentTypeId) : undefined,
      employee_name: assignmentFilterEmployeeName || undefined,
    }),
    enabled: activeTab === 'assignments',
  });
  
  // Fetch departments for filtering
  const { data: departments } = useQuery({
    queryKey: ['departments'],
    queryFn: departmentApi.getAll,
  });
  
  // Fetch assignment types based on selected department (for create form)
  const { data: assignmentTypes } = useQuery({
    queryKey: ['assignmentTypes', selectedDepartment],
    queryFn: () => assignmentTypeApi.getAll(selectedDepartment ? parseInt(selectedDepartment) : undefined),
    enabled: isCreateDialogOpen && !!selectedDepartment
  });
  
  // Fetch assignment types for filtering (based on filter department)
  const { data: filterAssignmentTypes } = useQuery({
    queryKey: ['assignmentTypes', assignmentFilterDepartmentId],
    queryFn: () => assignmentTypeApi.getAll(assignmentFilterDepartmentId ? parseInt(assignmentFilterDepartmentId) : undefined),
    enabled: !!assignmentFilterDepartmentId
  });

  // Get all employees for assignment creation
  const { data: allEmployees } = useQuery({
    queryKey: ['employees-all'],
    queryFn: () => apiClient.searchEmployees({}),
    enabled: isCreateDialogOpen,
  });

  // Employee search handlers
  const handleEmployeeSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetchEmployees();
  };

  const handleEmployeeInputChange = (field: keyof EmployeeSearchParams, value: string | number | undefined) => {
    setEmployeeSearchParams(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // Assignment creation mutation
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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Search</h1>
            <p className="mt-1 text-sm text-gray-700">
              Search for employees and assignments
            </p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            {canSearchEmployees && (
              <button
                onClick={() => setActiveTab('employees')}
                className={`whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'employees'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Employee Search
              </button>
            )}
            {canViewAssignments && (
              <button
                onClick={() => setActiveTab('assignments')}
                className={`whitespace-nowrap py-4 px-6 border-b-2 font-medium text-sm ${
                  activeTab === 'assignments'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Assignment Search
              </button>
            )}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'employees' && canSearchEmployees && (
            <div className="space-y-6">
              {/* Employee Search Form */}
              <form onSubmit={handleEmployeeSearch} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div>
                    <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                      Name
                    </label>
                    <input
                      type="text"
                      id="name"
                      value={employeeSearchParams.name || ''}
                      onChange={(e) => handleEmployeeInputChange('name', e.target.value)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Search by name..."
                    />
                  </div>

                  <div>
                    <label htmlFor="employee_id" className="block text-sm font-medium text-gray-700">
                      Employee ID
                    </label>
                    <input
                      type="number"
                      id="employee_id"
                      value={employeeSearchParams.employee_id || ''}
                      onChange={(e) => handleEmployeeInputChange('employee_id', e.target.value ? parseInt(e.target.value) : undefined)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Search by ID..."
                    />
                  </div>

                  <div>
                    <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                      Status
                    </label>
                    <select
                      id="status"
                      value={employeeSearchParams.status || ''}
                      onChange={(e) => handleEmployeeInputChange('status', e.target.value as 'Active' | 'Inactive' | undefined)}
                      className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    >
                      <option value="">All Statuses</option>
                      <option value="Active">Active</option>
                      <option value="Inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <button
                    type="submit"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Search Employees
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setEmployeeSearchParams({ name: '', employee_id: undefined, status: undefined, skip: 0, limit: 10 });
                      setTimeout(() => refetchEmployees(), 0);
                    }}
                    className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    Clear
                  </button>
                </div>
              </form>

              {/* Employee Results */}
              {employeesLoading && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-800">Loading employees...</p>
                </div>
              )}

              {employeesError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-600">
                    Error loading employees: {employeesError instanceof Error ? employeesError.message : 'Unknown error'}
                  </p>
                </div>
              )}

              {employees && employees.length === 0 && !employeesLoading && (
                <div className="text-center py-8">
                  <p className="text-gray-700">No employees found matching your search criteria.</p>
                </div>
              )}

              {employees && employees.length > 0 && (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Employee Results
                    </h3>
                    <span className="text-sm text-gray-700">
                      {employees.length} employee{employees.length !== 1 ? 's' : ''} found
                    </span>
                  </div>
                  
                  <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Name
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Employee ID
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Status
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Work Email
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Start Date
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                            Actions
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {employees.map((employee: Employee) => (
                          <tr key={employee.employee_id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">
                                {employee.person.full_name}
                              </div>
                              {employee.person.date_of_birth && (
                                <div className="text-sm text-gray-700">
                                  DOB: {new Date(employee.person.date_of_birth).toLocaleDateString()}
                                </div>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.employee_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                                employee.status === 'Active' 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-red-100 text-red-800'
                              }`}>
                                {employee.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.work_email || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {employee.effective_start_date 
                                ? new Date(employee.effective_start_date).toLocaleDateString()
                                : '-'
                              }
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                              {canViewEmployeeDetails && (
                                <button
                                  onClick={() => router.push(`/employees/${employee.employee_id}/edit`)}
                                  className="text-blue-600 hover:text-blue-900 focus:outline-none focus:underline"
                                >
                                  View
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'assignments' && canViewAssignments && (
            <div className="space-y-6">
              {/* Assignment Filter Controls */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-gray-900">Filter Assignments</h3>
                  {canCreateAssignment && (
                    <button
                      onClick={() => setIsCreateDialogOpen(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      Create Assignment
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label htmlFor="assignmentFilterDepartment" className="block text-sm font-medium text-gray-700 mb-1">
                      Department
                    </label>
                    <select
                      id="assignmentFilterDepartment"
                      value={assignmentFilterDepartmentId}
                      onChange={(e) => {
                        setAssignmentFilterDepartmentId(e.target.value);
                        setAssignmentFilterAssignmentTypeId(''); // Reset assignment type when department changes
                      }}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Departments</option>
                      {departments?.map((dept) => (
                        <option key={dept.department_id} value={dept.department_id.toString()}>
                          {dept.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="assignmentFilterAssignmentType" className="block text-sm font-medium text-gray-700 mb-1">
                      Assignment Type
                    </label>
                    <select
                      id="assignmentFilterAssignmentType"
                      value={assignmentFilterAssignmentTypeId}
                      onChange={(e) => setAssignmentFilterAssignmentTypeId(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Assignment Types</option>
                      {filterAssignmentTypes?.map((type) => (
                        <option key={type.assignment_type_id} value={type.assignment_type_id.toString()}>
                          {type.description}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="assignmentFilterEmployeeName" className="block text-sm font-medium text-gray-700 mb-1">
                      Employee Name
                    </label>
                    <input
                      id="assignmentFilterEmployeeName"
                      type="text"
                      placeholder="Search by employee name..."
                      value={assignmentFilterEmployeeName}
                      onChange={(e) => setAssignmentFilterEmployeeName(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Active Assignment Filters */}
                {(assignmentFilterDepartmentId || assignmentFilterAssignmentTypeId || assignmentFilterEmployeeName) && (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-700">Active filters:</span>
                      {assignmentFilterDepartmentId && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                          Dept: {departments?.find(d => d.department_id.toString() === assignmentFilterDepartmentId)?.name}
                          <button
                            onClick={() => setAssignmentFilterDepartmentId('')}
                            className="ml-1 text-blue-600 hover:text-blue-800"
                            type="button"
                          >
                            ×
                          </button>
                        </span>
                      )}
                      {assignmentFilterAssignmentTypeId && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                          Type: {filterAssignmentTypes?.find(t => t.assignment_type_id.toString() === assignmentFilterAssignmentTypeId)?.description}
                          <button
                            onClick={() => setAssignmentFilterAssignmentTypeId('')}
                            className="ml-1 text-green-600 hover:text-green-800"
                            type="button"
                          >
                            ×
                          </button>
                        </span>
                      )}
                      {assignmentFilterEmployeeName && (
                        <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-100 text-purple-800">
                          Name: {assignmentFilterEmployeeName}
                          <button
                            onClick={() => setAssignmentFilterEmployeeName('')}
                            className="ml-1 text-purple-600 hover:text-purple-800"
                            type="button"
                          >
                            ×
                          </button>
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => {
                        setAssignmentFilterDepartmentId('');
                        setAssignmentFilterAssignmentTypeId('');
                        setAssignmentFilterEmployeeName('');
                      }}
                      className="text-sm text-gray-600 hover:text-gray-800 px-3 py-1 border border-gray-300 rounded-md hover:bg-gray-50"
                      type="button"
                    >
                      Clear All Filters
                    </button>
                  </div>
                )}
              </div>

              {/* Assignment Results */}
              {assignmentsLoading && (
                <div className="text-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                  <p className="mt-2 text-gray-800">Loading assignments...</p>
                </div>
              )}

              {assignmentsError && (
                <div className="bg-red-50 border border-red-200 rounded-md p-4">
                  <p className="text-red-600">
                    Error loading assignments: {assignmentsError instanceof Error ? assignmentsError.message : 'Unknown error'}
                  </p>
                </div>
              )}

              {assignments && assignments.length > 0 ? (
                <div>
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg leading-6 font-medium text-gray-900">
                      Assignment Results
                    </h3>
                    <span className="text-sm text-gray-700 bg-gray-100 px-3 py-1 rounded-full">
                      {assignments.length} assignment{assignments.length !== 1 ? 's' : ''} found
                    </span>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Employee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Role</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Department</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Supervisor(s)</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Start Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">End Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">Status</th>
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
                                <div className="text-sm text-gray-700">
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
                                  <div className="text-sm text-gray-700">
                                    {assignment.description}
                                  </div>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-sm text-gray-900">
                                  {assignment.assignment_type.department.name}
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
                                <span className="text-sm text-gray-700">No supervisor</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                {formatDate(assignment.effective_start_date)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center text-sm text-gray-900">
                                {formatDate(assignment.effective_end_date)}
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {getStatusBadge(assignment)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : assignments && assignments.length === 0 && !assignmentsLoading ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">👥</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No assignments found</h3>
                  <p className="text-gray-700 mb-4">No assignments match your current filters</p>
                  {canCreateAssignment && (
                    <button
                      onClick={() => setIsCreateDialogOpen(true)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Create Assignment
                    </button>
                  )}
                </div>
              ) : null}
            </div>
          )}

          {/* No access message */}
          {!canSearchEmployees && !canViewAssignments && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔒</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Access Restricted</h3>
              <p className="text-gray-700">You don&apos;t have permission to search employees or view assignments.</p>
            </div>
          )}
        </div>
      </div>

      {/* Create Assignment Dialog */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Assignment</h2>
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  >
                    <option value="">Select employee</option>
                    {allEmployees?.map((employee) => (
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">No supervisor</option>
                  {allEmployees?.map((employee) => (
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
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