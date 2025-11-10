'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi, AdminUser, UserRoleDistribution, SystemHealth } from '@/lib/api/admin';
import { useHasPermission } from '@/store/authStore';
import { UserRole } from '@/lib/types';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Users, UserCheck, Building2, Shield } from "lucide-react";

export default function AdminPage() {
  const canManageUsers = useHasPermission('user.manage');

  if (!canManageUsers) {
    return (
      <div className="space-y-6">
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">You don&apos;t have permission to access the admin panel.</p>
          </CardContent>
        </Card>
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
      <Card>
        <CardHeader>
          <CardTitle>System Administration</CardTitle>
          <CardDescription>
            Manage users, roles, and permissions across the HRM system
          </CardDescription>
        </CardHeader>
      </Card>

      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as 'overview' | 'users' | 'permissions')}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="permissions">Permissions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <SystemOverview
            systemHealth={systemHealth}
            roleDistribution={roleDistribution}
            loading={healthLoading || distributionLoading}
          />
        </TabsContent>

        <TabsContent value="users" className="space-y-4">
          <UserManagement />
        </TabsContent>

        <TabsContent value="permissions" className="space-y-4">
          <PermissionOverview />
        </TabsContent>
      </Tabs>
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
      <div className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="pt-6">
                <div className="h-20 bg-muted rounded"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* System Metrics */}
      {systemHealth && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Total Users</p>
                  <p className="text-2xl font-bold">{systemHealth.total_users}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-green-100 rounded-lg">
                  <UserCheck className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Active Users</p>
                  <p className="text-2xl font-bold">{systemHealth.active_users}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-purple-100 rounded-lg">
                  <Building2 className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Employees</p>
                  <p className="text-2xl font-bold">{systemHealth.total_employees}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center space-x-4">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <Shield className="h-6 w-6 text-yellow-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Permissions</p>
                  <p className="text-2xl font-bold">{systemHealth.permission_system.total_permissions}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Role Distribution */}
      {roleDistribution && (
        <Card>
          <CardHeader>
            <CardTitle>User Role Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {roleDistribution.role_distribution.map((roleData) => (
                <div key={roleData.role} className="flex items-center justify-between gap-4">
                  <div className="flex items-center space-x-3 flex-1">
                    <Badge
                      variant={
                        roleData.role === UserRole.HR_ADMIN ? 'destructive' :
                        roleData.role === UserRole.SUPERVISOR ? 'default' :
                        roleData.role === UserRole.SUPER_USER ? 'secondary' :
                        'outline'
                      }
                    >
                      {roleData.role.replace('_', ' ')}
                    </Badge>
                    <p className="text-sm font-medium">
                      {roleData.user_count} users ({roleData.percentage}%)
                    </p>
                  </div>
                  <div className="w-32">
                    <div className="w-full bg-secondary rounded-full h-2">
                      <div
                        className={`h-2 rounded-full ${
                          roleData.role === UserRole.HR_ADMIN ? 'bg-destructive' :
                          roleData.role === UserRole.SUPERVISOR ? 'bg-primary' :
                          roleData.role === UserRole.SUPER_USER ? 'bg-purple-600' :
                          'bg-green-600'
                        }`}
                        style={{ width: `${roleData.percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
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
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="ml-2 text-muted-foreground">Loading users...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <p className="text-destructive">Error loading users: {error.message}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Filter by role:</label>
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="All Roles" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value=" ">All Roles</SelectItem>
                <SelectItem value={UserRole.SUPER_USER}>Super User</SelectItem>
                <SelectItem value={UserRole.HR_ADMIN}>HR Admin</SelectItem>
                <SelectItem value={UserRole.SUPERVISOR}>Supervisor</SelectItem>
                <SelectItem value={UserRole.EMPLOYEE}>Employee</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>User</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users?.map((user) => (
                <TableRow key={user.user_id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{user.username}</div>
                      <div className="text-sm text-muted-foreground">{user.email}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {user.roles.map(role => (
                        <Badge
                          key={role}
                          variant={
                            role === UserRole.HR_ADMIN ? 'destructive' :
                            role === UserRole.SUPERVISOR ? 'default' :
                            role === UserRole.SUPER_USER ? 'secondary' :
                            'outline'
                          }
                        >
                          {role.replace('_', ' ')}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant={user.is_active ? 'default' : 'destructive'}>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {user.permissions.length} permissions
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRoleChange(user)}
                    >
                      Change Role
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Role Change Modal */}
      <Dialog open={showRoleModal} onOpenChange={setShowRoleModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Change Role</DialogTitle>
            <DialogDescription>
              Change role for {selectedUser?.username}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 py-4">
            {Object.values(UserRole).map((role) => (
              <Button
                key={role}
                onClick={() => confirmRoleChange(role)}
                disabled={selectedUser?.roles.includes(role) || updateRoleMutation.isPending}
                variant={selectedUser?.roles.includes(role) ? "secondary" : "outline"}
                className="w-full justify-start"
              >
                {role.replace('_', ' ')} {selectedUser?.roles.includes(role) && '(Current)'}
              </Button>
            ))}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRoleModal(false)}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PermissionOverview() {
  const { data: permissions, isLoading } = useQuery({
    queryKey: ['admin', 'permissions'],
    queryFn: adminApi.listPermissions,
  });

  const { data: superUserPermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', UserRole.SUPER_USER],
    queryFn: () => adminApi.getRolePermissions(UserRole.SUPER_USER),
  });

  const { data: hrPermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', UserRole.HR_ADMIN],
    queryFn: () => adminApi.getRolePermissions(UserRole.HR_ADMIN),
  });

  const { data: supervisorPermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', UserRole.SUPERVISOR],
    queryFn: () => adminApi.getRolePermissions(UserRole.SUPERVISOR),
  });

  const { data: employeePermissions } = useQuery({
    queryKey: ['admin', 'role-permissions', UserRole.EMPLOYEE],
    queryFn: () => adminApi.getRolePermissions(UserRole.EMPLOYEE),
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="ml-2 text-muted-foreground">Loading permissions...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Permission Summary */}
      {permissions && (
        <Card>
          <CardHeader>
            <CardTitle>Permission Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">{permissions.total_permissions}</div>
                <div className="text-sm text-muted-foreground">Total Permissions</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">{Object.keys(permissions.permission_groups).length}</div>
                <div className="text-sm text-muted-foreground">Resource Types</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">4</div>
                <div className="text-sm text-muted-foreground">User Roles</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Role Permission Matrix */}
      <Card>
        <CardHeader>
          <CardTitle>Role Permission Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {[
              { role: UserRole.SUPER_USER, data: superUserPermissions, variant: 'secondary' as const },
              { role: UserRole.HR_ADMIN, data: hrPermissions, variant: 'destructive' as const },
              { role: UserRole.SUPERVISOR, data: supervisorPermissions, variant: 'default' as const },
              { role: UserRole.EMPLOYEE, data: employeePermissions, variant: 'outline' as const }
            ].map(({ role, data, variant }) => (
              <Card key={role}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{role.replace('_', ' ')}</CardTitle>
                    <Badge variant={variant}>
                      {data?.permission_count || 0}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  {data?.permission_groups && Object.entries(data.permission_groups).map(([resource, perms]) => (
                    <div key={resource} className="mb-3">
                      <div className="text-sm font-medium capitalize">{resource}</div>
                      <div className="text-xs text-muted-foreground">{perms.length} permissions</div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}