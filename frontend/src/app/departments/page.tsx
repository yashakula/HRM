'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { departmentApi, Department, DepartmentCreate, DepartmentUpdate } from '@/lib/api/departments';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { ActionButton, useUIPermissions } from '@/components/auth/ConditionalRender';

export default function DepartmentsPage() {
  return (
    <ProtectedRoute 
      pageIdentifier="departments" 
      requiredPermissions={['view']}
    >
      <DepartmentsContent />
    </ProtectedRoute>
  );
}

function DepartmentsContent() {
  const queryClient = useQueryClient();
  const { showIf } = useUIPermissions('departments');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState<Department | null>(null);
  const [formData, setFormData] = useState<DepartmentCreate>({
    name: '',
    description: '',
    assignment_types: []
  });
  const [editFormData, setEditFormData] = useState<DepartmentUpdate>({
    name: '',
    description: '',
    assignment_types_to_add: [],
    assignment_types_to_remove: []
  });
  const [newAssignmentType, setNewAssignmentType] = useState('');

  // Fetch departments
  const { data: departments, isLoading, error } = useQuery({
    queryKey: ['departments'],
    queryFn: departmentApi.getAll,
  });

  // Create department mutation
  const createMutation = useMutation({
    mutationFn: departmentApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setIsCreateDialogOpen(false);
      setFormData({ name: '', description: '', assignment_types: [] });
      alert('Department created successfully');
    },
    onError: (error: Error) => {
      alert('Failed to create department: ' + error.message);
    },
  });

  // Update department mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: DepartmentUpdate }) => 
      departmentApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      setIsEditDialogOpen(false);
      setEditingDepartment(null);
      setEditFormData({ 
        name: '', 
        description: '', 
        assignment_types_to_add: [], 
        assignment_types_to_remove: [] 
      });
      alert('Department updated successfully');
    },
    onError: (error: Error) => {
      alert('Failed to update department: ' + error.message);
    },
  });

  // Delete department mutation
  const deleteMutation = useMutation({
    mutationFn: departmentApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['departments'] });
      alert('Department deleted successfully');
    },
    onError: (error: Error) => {
      alert('Failed to delete department: ' + error.message);
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      alert('Department name is required');
      return;
    }
    createMutation.mutate(formData);
  };

  const handleEdit = (department: Department) => {
    setEditingDepartment(department);
    setEditFormData({
      name: department.name,
      description: department.description || '',
      assignment_types_to_add: [],
      assignment_types_to_remove: []
    });
    setIsEditDialogOpen(true);
  };

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingDepartment || !editFormData.name?.trim()) {
      alert('Department name is required');
      return;
    }
    updateMutation.mutate({
      id: editingDepartment.department_id,
      data: editFormData
    });
  };

  const addAssignmentType = () => {
    if (newAssignmentType.trim()) {
      setFormData({
        ...formData,
        assignment_types: [...(formData.assignment_types || []), newAssignmentType.trim()]
      });
      setNewAssignmentType('');
    }
  };

  const removeAssignmentType = (index: number) => {
    const updated = [...(formData.assignment_types || [])];
    updated.splice(index, 1);
    setFormData({ ...formData, assignment_types: updated });
  };

  const addAssignmentTypeToEdit = () => {
    if (newAssignmentType.trim()) {
      setEditFormData({
        ...editFormData,
        assignment_types_to_add: [...(editFormData.assignment_types_to_add || []), newAssignmentType.trim()]
      });
      setNewAssignmentType('');
    }
  };

  const removeAssignmentTypeFromEdit = (index: number) => {
    const updated = [...(editFormData.assignment_types_to_add || [])];
    updated.splice(index, 1);
    setEditFormData({ ...editFormData, assignment_types_to_add: updated });
  };

  const markAssignmentTypeForRemoval = (assignmentTypeId: number) => {
    setEditFormData({
      ...editFormData,
      assignment_types_to_remove: [...(editFormData.assignment_types_to_remove || []), assignmentTypeId]
    });
  };

  const unmarkAssignmentTypeForRemoval = (assignmentTypeId: number) => {
    setEditFormData({
      ...editFormData,
      assignment_types_to_remove: (editFormData.assignment_types_to_remove || []).filter(id => id !== assignmentTypeId)
    });
  };

  const handleDelete = (department: Department) => {
    if (confirm(`Are you sure you want to delete "${department.name}"? This action cannot be undone.`)) {
      deleteMutation.mutate(department.department_id);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Loading departments...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-red-600">Failed to load departments</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-2">
            🏢 Departments
          </h1>
          <p className="text-gray-800 mt-2">
            Manage organizational departments and their information
          </p>
        </div>
        
        <ActionButton
          action="create"
          pageIdentifier="departments"
        >
          <button
            onClick={() => setIsCreateDialogOpen(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            ➕ Add Department
          </button>
        </ActionButton>
      </div>

      {!showIf('create') && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800">
            You have read-only access to departments. Contact HR Admin to make changes.
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments?.map((department) => (
          <div key={department.department_id} className="bg-white p-6 rounded-lg shadow-md border">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-xl font-semibold text-gray-900">{department.name}</h3>
                <span className="text-sm text-gray-700 bg-gray-100 px-2 py-1 rounded">
                  ID: {department.department_id}
                </span>
              </div>
              <div className="flex gap-2">
                <ActionButton
                  action="edit"
                  pageIdentifier="departments"
                >
                  <button
                    onClick={() => handleEdit(department)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded"
                    title="Edit"
                  >
                    ✏️
                  </button>
                </ActionButton>
                
                <ActionButton
                  action="delete"
                  pageIdentifier="departments"
                >
                  <button
                    onClick={() => handleDelete(department)}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-red-600 hover:bg-red-50 rounded"
                    title="Delete"
                  >
                    🗑️
                  </button>
                </ActionButton>
              </div>
            </div>
            <p className="text-gray-800 mb-3">
              {department.description || 'No description provided'}
            </p>
            
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Assignment Types:</h4>
              {department.assignment_types && department.assignment_types.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {department.assignment_types.map((type) => (
                    <span 
                      key={type.assignment_type_id}
                      className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
                    >
                      {type.description}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 text-sm">No assignment types defined</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {departments?.length === 0 && (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🏢</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No departments found</h3>
          <p className="text-gray-700 mb-4">Get started by creating your first department</p>
          {showIf('create') && (
            <button
              onClick={() => setIsCreateDialogOpen(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              ➕ Add Department
            </button>
          )}
        </div>
      )}

      {/* Create Dialog */}
      {isCreateDialogOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create New Department</h2>
            <form onSubmit={handleCreate}>
              <div className="mb-4">
                <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                  Department Name *
                </label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Engineering, Marketing"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of the department"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Assignment Types (Optional)
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newAssignmentType}
                    onChange={(e) => setNewAssignmentType(e.target.value)}
                    placeholder="e.g., Software Engineer, Manager"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAssignmentType())}
                  />
                  <button
                    type="button"
                    onClick={addAssignmentType}
                    className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    Add
                  </button>
                </div>
                {formData.assignment_types && formData.assignment_types.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.assignment_types.map((type, index) => (
                      <span 
                        key={index}
                        className="px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full flex items-center gap-1"
                      >
                        {type}
                        <button
                          type="button"
                          onClick={() => removeAssignmentType(index)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateDialogOpen(false);
                    setNewAssignmentType('');
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
                  {createMutation.isPending ? 'Creating...' : 'Create Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Dialog */}
      {isEditDialogOpen && editingDepartment && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Edit Department</h2>
            <form onSubmit={handleUpdate}>
              <div className="mb-4">
                <label htmlFor="edit-name" className="block text-sm font-medium text-gray-700 mb-1">
                  Department Name *
                </label>
                <input
                  id="edit-name"
                  type="text"
                  value={editFormData.name || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  placeholder="e.g., Engineering, Marketing"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="mb-4">
                <label htmlFor="edit-description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="edit-description"
                  value={editFormData.description || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  placeholder="Brief description of the department"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              {/* Current Assignment Types */}
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Assignment Types
                </label>
                {editingDepartment.assignment_types && editingDepartment.assignment_types.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {editingDepartment.assignment_types.map((type) => {
                      const isMarkedForRemoval = editFormData.assignment_types_to_remove?.includes(type.assignment_type_id);
                      return (
                        <span 
                          key={type.assignment_type_id}
                          className={`px-2 py-1 text-sm rounded-full flex items-center gap-1 ${
                            isMarkedForRemoval 
                              ? 'bg-red-100 text-red-800 line-through' 
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {type.description}
                          <button
                            type="button"
                            onClick={() => isMarkedForRemoval 
                              ? unmarkAssignmentTypeForRemoval(type.assignment_type_id)
                              : markAssignmentTypeForRemoval(type.assignment_type_id)
                            }
                            className={`text-sm hover:opacity-70 ${
                              isMarkedForRemoval ? 'text-red-600' : 'text-gray-800'
                            }`}
                          >
                            {isMarkedForRemoval ? '↶' : '×'}
                          </button>
                        </span>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-600 text-sm">No assignment types defined</p>
                )}
              </div>
              
              {/* Add New Assignment Types */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Add New Assignment Types
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="text"
                    value={newAssignmentType}
                    onChange={(e) => setNewAssignmentType(e.target.value)}
                    placeholder="e.g., Software Engineer, Manager"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAssignmentTypeToEdit())}
                  />
                  <button
                    type="button"
                    onClick={addAssignmentTypeToEdit}
                    className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200"
                  >
                    Add
                  </button>
                </div>
                {editFormData.assignment_types_to_add && editFormData.assignment_types_to_add.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {editFormData.assignment_types_to_add.map((type, index) => (
                      <span 
                        key={index}
                        className="px-2 py-1 bg-green-100 text-green-800 text-sm rounded-full flex items-center gap-1"
                      >
                        {type}
                        <button
                          type="button"
                          onClick={() => removeAssignmentTypeFromEdit(index)}
                          className="text-green-600 hover:text-green-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setIsEditDialogOpen(false);
                    setEditingDepartment(null);
                    setEditFormData({ 
                      name: '', 
                      description: '', 
                      assignment_types_to_add: [], 
                      assignment_types_to_remove: [] 
                    });
                    setNewAssignmentType('');
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {updateMutation.isPending ? 'Updating...' : 'Update Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}