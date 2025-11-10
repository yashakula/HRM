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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Textarea } from "@/components/ui/textarea"
import { DataTable } from "./data-table"
import { employeeColumns } from "./employee-columns"
import { assignmentColumns } from "./assignment-columns"

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
    limit: 100 // Increase limit for better data table experience
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
  const { data: employees = [], isLoading: employeesLoading, error: employeesError, refetch: refetchEmployees } = useQuery({
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
  const { data: assignments = [], isLoading: assignmentsLoading, error: assignmentsError } = useQuery({
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
    },
    onError: (error: Error) => {
      console.error('Failed to create assignment:', error.message);
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
      return;
    }

    const supervisorIds = selectedSupervisor ? [parseInt(selectedSupervisor)] : [];
    createMutation.mutate({
      ...formData,
      supervisor_ids: supervisorIds
    });
  };

  return (
    <div className="space-y-6">
      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'employees' | 'assignments')}>
        <TabsList className="grid w-full grid-cols-2">
          {canSearchEmployees && (
            <TabsTrigger value="employees">Employees</TabsTrigger>
          )}
          {canViewAssignments && (
            <TabsTrigger value="assignments">Assignments</TabsTrigger>
          )}
        </TabsList>

        {/* Employee Tab */}
        {canSearchEmployees && (
          <TabsContent value="employees" className="space-y-4">
            <Card>
              <CardContent className="pt-6">
                <form onSubmit={handleEmployeeSearch} className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="name">Name</Label>
                      <Input
                        id="name"
                        value={employeeSearchParams.name || ''}
                        onChange={(e) => handleEmployeeInputChange('name', e.target.value)}
                        placeholder="Search by name..."
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="employee_id">Employee ID</Label>
                      <Input
                        id="employee_id"
                        type="text"
                        inputMode="numeric"
                        pattern="[0-9]*"
                        value={employeeSearchParams.employee_id || ''}
                        onChange={(e) => handleEmployeeInputChange('employee_id', e.target.value ? parseInt(e.target.value) : undefined)}
                        placeholder="Search by ID..."
                      />
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="status">Status</Label>
                      <Select
                        value={employeeSearchParams.status || ''}
                        onValueChange={(value) => handleEmployeeInputChange('status', value as 'Active' | 'Inactive' | undefined)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="All Statuses" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value=" ">All Statuses</SelectItem>
                          <SelectItem value="Active">Active</SelectItem>
                          <SelectItem value="Inactive">Inactive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="flex gap-4">
                    <Button type="submit">Search Employees</Button>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => {
                        setEmployeeSearchParams({ name: '', employee_id: undefined, status: undefined, skip: 0, limit: 100 });
                        setTimeout(() => refetchEmployees(), 0);
                      }}
                    >
                      Clear
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                {employeesLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-2 text-muted-foreground">Loading employees...</p>
                  </div>
                ) : employeesError ? (
                  <div className="bg-destructive/10 border border-destructive/50 rounded-md p-4">
                    <p className="text-destructive text-sm">
                      Error loading employees: {employeesError instanceof Error ? employeesError.message : 'Unknown error'}
                    </p>
                  </div>
                ) : (
                  <DataTable
                    columns={employeeColumns}
                    data={employees}
                    searchKey="person.full_name"
                    searchPlaceholder="Filter by name..."
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}

        {/* Assignment Tab */}
        {canViewAssignments && (
          <TabsContent value="assignments" className="space-y-4">
            <Card>
              <CardContent className="pt-6 space-y-4">
                <div className="flex items-center justify-end">
                  {canCreateAssignment && (
                    <Button onClick={() => setIsCreateDialogOpen(true)}>
                      Create Assignment
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="assignmentFilterDepartment">Department</Label>
                    <Select
                      value={assignmentFilterDepartmentId}
                      onValueChange={(value) => {
                        setAssignmentFilterDepartmentId(value);
                        setAssignmentFilterAssignmentTypeId('');
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All Departments" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=" ">All Departments</SelectItem>
                        {departments?.map((dept) => (
                          <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                            {dept.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="assignmentFilterAssignmentType">Assignment Type</Label>
                    <Select
                      value={assignmentFilterAssignmentTypeId}
                      onValueChange={setAssignmentFilterAssignmentTypeId}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="All Assignment Types" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value=" ">All Assignment Types</SelectItem>
                        {filterAssignmentTypes?.map((type) => (
                          <SelectItem key={type.assignment_type_id} value={type.assignment_type_id.toString()}>
                            {type.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="assignmentFilterEmployeeName">Employee Name</Label>
                    <Input
                      id="assignmentFilterEmployeeName"
                      placeholder="Search by employee name..."
                      value={assignmentFilterEmployeeName}
                      onChange={(e) => setAssignmentFilterEmployeeName(e.target.value)}
                    />
                  </div>
                </div>

                {/* Active Filters */}
                {(assignmentFilterDepartmentId || assignmentFilterAssignmentTypeId || assignmentFilterEmployeeName) && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm text-muted-foreground">Active filters:</span>
                    {assignmentFilterDepartmentId && (
                      <Badge variant="secondary">
                        Dept: {departments?.find(d => d.department_id.toString() === assignmentFilterDepartmentId)?.name}
                        <button
                          onClick={() => setAssignmentFilterDepartmentId('')}
                          className="ml-1 hover:text-destructive"
                        >
                          ×
                        </button>
                      </Badge>
                    )}
                    {assignmentFilterAssignmentTypeId && (
                      <Badge variant="secondary">
                        Type: {filterAssignmentTypes?.find(t => t.assignment_type_id.toString() === assignmentFilterAssignmentTypeId)?.description}
                        <button
                          onClick={() => setAssignmentFilterAssignmentTypeId('')}
                          className="ml-1 hover:text-destructive"
                        >
                          ×
                        </button>
                      </Badge>
                    )}
                    {assignmentFilterEmployeeName && (
                      <Badge variant="secondary">
                        Name: {assignmentFilterEmployeeName}
                        <button
                          onClick={() => setAssignmentFilterEmployeeName('')}
                          className="ml-1 hover:text-destructive"
                        >
                          ×
                        </button>
                      </Badge>
                    )}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setAssignmentFilterDepartmentId('');
                        setAssignmentFilterAssignmentTypeId('');
                        setAssignmentFilterEmployeeName('');
                      }}
                    >
                      Clear All
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                {assignmentsLoading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
                    <p className="mt-2 text-muted-foreground">Loading assignments...</p>
                  </div>
                ) : assignmentsError ? (
                  <div className="bg-destructive/10 border border-destructive/50 rounded-md p-4">
                    <p className="text-destructive text-sm">
                      Error loading assignments: {assignmentsError instanceof Error ? assignmentsError.message : 'Unknown error'}
                    </p>
                  </div>
                ) : assignments.length > 0 ? (
                  <DataTable
                    columns={assignmentColumns}
                    data={assignments}
                    searchKey="employee.person.full_name"
                    searchPlaceholder="Filter by employee name..."
                  />
                ) : (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">👥</div>
                    <h3 className="text-lg font-medium mb-2">No assignments found</h3>
                    <p className="text-muted-foreground mb-4">No assignments match your current filters</p>
                    {canCreateAssignment && (
                      <Button onClick={() => setIsCreateDialogOpen(true)}>
                        Create Assignment
                      </Button>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Create Assignment Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Assignment</DialogTitle>
            <DialogDescription>
              Assign an employee to a role in a department
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="employee">Employee *</Label>
                  <Select
                    value={selectedEmployee}
                    onValueChange={(value) => {
                      setSelectedEmployee(value);
                      setFormData({ ...formData, employee_id: parseInt(value) });
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select employee" />
                    </SelectTrigger>
                    <SelectContent>
                      {allEmployees?.map((employee) => (
                        <SelectItem key={employee.employee_id} value={employee.employee_id.toString()}>
                          {employee.person.full_name} (ID: {employee.employee_id})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="department">Department</Label>
                  <Select
                    value={selectedDepartment}
                    onValueChange={setSelectedDepartment}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="All departments" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value=" ">All departments</SelectItem>
                      {departments?.map((dept) => (
                        <SelectItem key={dept.department_id} value={dept.department_id.toString()}>
                          {dept.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="assignmentType">Assignment Type *</Label>
                <Select
                  value={formData.assignment_type_id.toString()}
                  onValueChange={(value) => setFormData({ ...formData, assignment_type_id: parseInt(value) })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select assignment type" />
                  </SelectTrigger>
                  <SelectContent>
                    {assignmentTypes?.map((type) => (
                      <SelectItem key={type.assignment_type_id} value={type.assignment_type_id.toString()}>
                        {type.description} ({type.department.name})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="supervisor">Supervisor (Optional)</Label>
                <Select
                  value={selectedSupervisor}
                  onValueChange={setSelectedSupervisor}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="No supervisor" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=" ">No supervisor</SelectItem>
                    {allEmployees?.map((employee) => (
                      <SelectItem key={employee.employee_id} value={employee.employee_id.toString()}>
                        {employee.person.full_name} (ID: {employee.employee_id})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="startDate">Start Date</Label>
                  <Input
                    id="startDate"
                    type="date"
                    value={formData.effective_start_date}
                    onChange={(e) => setFormData({ ...formData, effective_start_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="endDate">End Date (Optional)</Label>
                  <Input
                    id="endDate"
                    type="date"
                    value={formData.effective_end_date}
                    onChange={(e) => setFormData({ ...formData, effective_end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Additional details about the assignment"
                  rows={3}
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateDialogOpen(false);
                  resetForm();
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Assignment'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* No access message */}
      {!canSearchEmployees && !canViewAssignments && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-6xl mb-4">🔒</div>
            <h3 className="text-lg font-medium mb-2">Access Restricted</h3>
            <p className="text-muted-foreground">You don&apos;t have permission to search employees or view assignments.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
