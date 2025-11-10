'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { departmentApi, Department, DepartmentCreate, DepartmentUpdate } from '@/lib/api/departments';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { ActionButton, useUIPermissions } from '@/components/auth/ConditionalRender';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Edit, Trash2 } from "lucide-react";

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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p className="mt-2 text-muted-foreground">Loading departments...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg text-destructive">Failed to load departments</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle>Departments</CardTitle>
            <CardDescription>
              Manage organizational departments and their information
            </CardDescription>
          </div>
          <ActionButton
            action="create"
            pageIdentifier="departments"
          >
            <Button onClick={() => setIsCreateDialogOpen(true)}>
              Add Department
            </Button>
          </ActionButton>
        </CardHeader>
      </Card>

      {!showIf('create') && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <p className="text-sm text-blue-800">
              You have read-only access to departments. Contact HR Admin to make changes.
            </p>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {departments?.map((department) => (
          <Card key={department.department_id}>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle>{department.name}</CardTitle>
                  <Badge variant="secondary" className="text-xs">
                    ID: {department.department_id}
                  </Badge>
                </div>
                <div className="flex gap-1">
                  <ActionButton
                    action="edit"
                    pageIdentifier="departments"
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEdit(department)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                  </ActionButton>

                  <ActionButton
                    action="delete"
                    pageIdentifier="departments"
                  >
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(department)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </ActionButton>
                </div>
              </div>
              <CardDescription>
                {department.description || 'No description provided'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Assignment Types</h4>
                {department.assignment_types && department.assignment_types.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {department.assignment_types.map((type) => (
                      <Badge
                        key={type.assignment_type_id}
                        variant="outline"
                      >
                        {type.description}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No assignment types defined</p>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {departments?.length === 0 && (
        <Card>
          <CardContent className="text-center py-12">
            <div className="text-6xl mb-4">🏢</div>
            <h3 className="text-lg font-medium mb-2">No departments found</h3>
            <p className="text-muted-foreground mb-4">Get started by creating your first department</p>
            {showIf('create') && (
              <Button onClick={() => setIsCreateDialogOpen(true)}>
                Add Department
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {/* Create Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create New Department</DialogTitle>
            <DialogDescription>
              Add a new department to your organization
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Department Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Engineering, Marketing"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of the department"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label>Assignment Types (Optional)</Label>
                <div className="flex gap-2">
                  <Input
                    value={newAssignmentType}
                    onChange={(e) => setNewAssignmentType(e.target.value)}
                    placeholder="e.g., Software Engineer, Manager"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAssignmentType())}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addAssignmentType}
                  >
                    Add
                  </Button>
                </div>
                {formData.assignment_types && formData.assignment_types.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.assignment_types.map((type, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="gap-1"
                      >
                        {type}
                        <button
                          type="button"
                          onClick={() => removeAssignmentType(index)}
                          className="hover:text-destructive"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setIsCreateDialogOpen(false);
                  setNewAssignmentType('');
                }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Department'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Department</DialogTitle>
            <DialogDescription>
              Update department information and assignment types
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleUpdate}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-name">Department Name *</Label>
                <Input
                  id="edit-name"
                  value={editFormData.name || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
                  placeholder="e.g., Engineering, Marketing"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="edit-description">Description</Label>
                <Textarea
                  id="edit-description"
                  value={editFormData.description || ''}
                  onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
                  placeholder="Brief description of the department"
                  rows={3}
                />
              </div>

              {/* Current Assignment Types */}
              <div className="space-y-2">
                <Label>Current Assignment Types</Label>
                {editingDepartment && editingDepartment.assignment_types && editingDepartment.assignment_types.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {editingDepartment.assignment_types.map((type) => {
                      const isMarkedForRemoval = editFormData.assignment_types_to_remove?.includes(type.assignment_type_id);
                      return (
                        <Badge
                          key={type.assignment_type_id}
                          variant={isMarkedForRemoval ? "destructive" : "secondary"}
                          className={`gap-1 ${isMarkedForRemoval ? 'line-through' : ''}`}
                        >
                          {type.description}
                          <button
                            type="button"
                            onClick={() => isMarkedForRemoval
                              ? unmarkAssignmentTypeForRemoval(type.assignment_type_id)
                              : markAssignmentTypeForRemoval(type.assignment_type_id)
                            }
                            className="hover:opacity-70"
                          >
                            {isMarkedForRemoval ? '↶' : '×'}
                          </button>
                        </Badge>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No assignment types defined</p>
                )}
              </div>

              {/* Add New Assignment Types */}
              <div className="space-y-2">
                <Label>Add New Assignment Types</Label>
                <div className="flex gap-2">
                  <Input
                    value={newAssignmentType}
                    onChange={(e) => setNewAssignmentType(e.target.value)}
                    placeholder="e.g., Software Engineer, Manager"
                    onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addAssignmentTypeToEdit())}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={addAssignmentTypeToEdit}
                  >
                    Add
                  </Button>
                </div>
                {editFormData.assignment_types_to_add && editFormData.assignment_types_to_add.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {editFormData.assignment_types_to_add.map((type, index) => (
                      <Badge
                        key={index}
                        variant="default"
                        className="gap-1 bg-green-600"
                      >
                        {type}
                        <button
                          type="button"
                          onClick={() => removeAssignmentTypeFromEdit(index)}
                          className="hover:opacity-70"
                        >
                          ×
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
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
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? 'Updating...' : 'Update Department'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}