'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, AdminUser, UserRoleDistribution, SystemHealth } from '@/lib/api/admin';
import { useHasPermission } from '@/store/authStore';

export default function AdminPage() {
  const canManageUsers = useHasPermission('user.manage');

  if (!canManageUsers) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-600">You don&apos;t have permission to access the admin panel.</p>
        </div>
      </div>
    );
  }

  return <AdminDashboard />;
}

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'permissions'>('overview');
  
  // System health data
  const { data: systemHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['admin', 'health'],
    queryFn: adminApi.getSystemHealth,
  });

  // User role distribution
  const { data: roleDistribution, isLoading: distributionLoading } = useQuery({
    queryKey: ['admin', 'user-roles'],
    queryFn: adminApi.getUserRoleDistribution,
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-2xl font-bold text-gray-900">System Administration</h1>
          <p className="mt-1 text-sm text-gray-700">
            Manage users, roles, and permissions across the HRM system
          </p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white shadow rounded-lg">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { key: 'overview', label: 'System Overview' },
              { key: 'users', label: 'User Management' },
              { key: 'permissions', label: 'Permission Overview' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key as 'overview' | 'users' | 'permissions')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="p-6">
          {activeTab === 'overview' && (
            <SystemOverview 
              systemHealth={systemHealth} 
              roleDistribution={roleDistribution}
              loading={healthLoading || distributionLoading}
            />
          )}
          {activeTab === 'users' && <UserManagement />}
          {activeTab === 'permissions' && <PermissionOverview />}
        </div>
      </div>
    </div>
  );
}

function SystemOverview({ 
  systemHealth, 
  roleDistribution, 
  loading 
}: { 
  systemHealth?: SystemHealth; 
  roleDistribution?: UserRoleDistribution;
  loading: boolean;
}) {
  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-32 bg-gray-200 rounded"></div>
        <div className="h-64 bg-gray-200 rounded"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Metrics */}
      {systemHealth && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="bg-blue-50 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">U</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Users</dt>
                    <dd className="text-lg font-medium text-gray-900">{systemHealth.total_users}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-green-50 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">A</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Active Users</dt>
                    <dd className="text-lg font-medium text-gray-900">{systemHealth.active_users}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-purple-50 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">E</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Employees</dt>
                    <dd className="text-lg font-medium text-gray-900">{systemHealth.total_employees}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center">
                    <span className="text-white text-sm font-medium">P</span>
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Permissions</dt>
                    <dd className="text-lg font-medium text-gray-900">{systemHealth.permission_system.total_permissions}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Role Distribution */}
      {roleDistribution && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">User Role Distribution</h3>
            <div className="space-y-4">
              {roleDistribution.role_distribution.map((roleData) => (
                <div key={roleData.role} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        roleData.role === 'HR_ADMIN' ? 'bg-red-100 text-red-800' :
                        roleData.role === 'SUPERVISOR' ? 'bg-blue-100 text-blue-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {roleData.role.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {roleData.user_count} users ({roleData.percentage}%)
                      </p>
                    </div>
                  </div>
                  <div className="flex-shrink-0">
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          roleData.role === 'HR_ADMIN' ? 'bg-red-600' :
                          roleData.role === 'SUPERVISOR' ? 'bg-blue-600' :
                          'bg-green-600'
                        }`}
                        style={{ width: `${roleData.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function UserManagement() {
  const [selectedRole, setSelectedRole] = useState<string>('');
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const queryClient = useQueryClient();

  // Fetch users
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['admin', 'users', selectedRole],
    queryFn: () => adminApi.listUsers({ 
      limit: 50,
      role_filter: selectedRole || undefined 
    }),
  });

  // Role update mutation
  const updateRoleMutation = useMutation({
    mutationFn: ({ userId, newRole }: { userId: number; newRole: string }) =>
      adminApi.updateUserRole(userId, newRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      queryClient.invalidateQueries({ queryKey: ['admin', 'user-roles'] });
      setShowRoleModal(false);
      setSelectedUser(null);
    },
  });

  const handleRoleChange = (user: AdminUser) => {
    setSelectedUser(user);
    setShowRoleModal(true);
  };

  const confirmRoleChange = (newRole: string) => {
    if (selectedUser) {
      updateRoleMutation.mutate({ userId: selectedUser.user_id, newRole });
    }
  };

  if (isLoading) {
    return <div className="text-center py-4">Loading users...</div>;
  }

  if (error) {
    return <div className="text-red-600 py-4">Error loading users: {error.message}</div>;
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex space-x-4">
        <select
          value={selectedRole}
          onChange={(e) => setSelectedRole(e.target.value)}
          className="rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="">All Roles</option>
          <option value="HR_ADMIN">HR Admin</option>
          <option value="SUPERVISOR">Supervisor</option>
          <option value="EMPLOYEE">Employee</option>
        </select>
      </div>

      {/* Users Table */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Permissions
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users?.map((user) => (
              <tr key={user.user_id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{user.username}</div>
                    <div className="text-sm text-gray-500">{user.email}</div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.role === 'HR_ADMIN' ? 'bg-red-100 text-red-800' :
                    user.role === 'SUPERVISOR' ? 'bg-blue-100 text-blue-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {user.role.replace('_', ' ')}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                    user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {user.permissions.length} permissions
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <button
                    onClick={() => handleRoleChange(user)}
                    className="text-blue-600 hover:text-blue-900"
                  >
                    Change Role
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Role Change Modal */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Change Role for {selectedUser.username}
            </h3>
            <div className="space-y-4">
              {['HR_ADMIN', 'SUPERVISOR', 'EMPLOYEE'].map((role) => (
                <button
                  key={role}
                  onClick={() => confirmRoleChange(role)}
                  disabled={role === selectedUser.role || updateRoleMutation.isPending}
                  className={`w-full text-left px-4 py-2 rounded border ${
                    role === selectedUser.role 
                      ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      : 'bg-white hover:bg-gray-50 border-gray-300'
                  }`}
                >
                  {role.replace('_', ' ')} {role === selectedUser.role && '(Current)'}
                </button>
              ))}
            </div>
            <div className="flex justify-end space-x-2 mt-6">
              <button
                onClick={() => setShowRoleModal(false)}
                className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PermissionOverview() {
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['admin', 'permissions'],
    queryFn: adminApi.listPermissions,
  });

  const { data: hrPermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', 'HR_ADMIN'],
    queryFn: () => adminApi.getRolePermissions('HR_ADMIN'),
  });

  const { data: supervisorPermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', 'SUPERVISOR'],
    queryFn: () => adminApi.getRolePermissions('SUPERVISOR'),
  });

  const { data: employeePermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', 'EMPLOYEE'],
    queryFn: () => adminApi.getRolePermissions('EMPLOYEE'),
  });

  if (isLoading) {
    return <div className="text-center py-4">Loading permissions...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Permission Summary */}
      {permissions && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Permission Summary</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{permissions.total_permissions}</div>
              <div className="text-sm text-gray-500">Total Permissions</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{Object.keys(permissions.permission_groups).length}</div>
              <div className="text-sm text-gray-500">Resource Types</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">3</div>
              <div className="text-sm text-gray-500">User Roles</div>
            </div>
          </div>
        </div>
      )}

      {/* Role Permission Matrix */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Role Permission Comparison</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {[
            { role: 'HR_ADMIN', data: hrPermissions, color: 'red' },
            { role: 'SUPERVISOR', data: supervisorPermissions, color: 'blue' },
            { role: 'EMPLOYEE', data: employeePermissions, color: 'green' }
          ].map(({ role, data, color }) => (
            <div key={role} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-gray-900">{role.replace('_', ' ')}</h4>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-${color}-100 text-${color}-800`}>
                  {data?.permission_count || 0} permissions
                </span>
              </div>
              {data?.permission_groups && Object.entries(data.permission_groups).map(([resource, perms]) => (
                <div key={resource} className="mb-2">
                  <div className="text-sm font-medium text-gray-700 capitalize">{resource}</div>
                  <div className="text-xs text-gray-500">{perms.length} permissions</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}