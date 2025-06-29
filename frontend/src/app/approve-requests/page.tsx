'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { LeaveRequest, LeaveStatus } from '@/lib/types';
import { 
  useAuthStore, 
  useHasPermission, 
  useHasAnyPermission 
} from '@/store/authStore';

interface RejectModalProps {
  leaveRequest: LeaveRequest | null;
  isOpen: boolean;
  onClose: () => void;
  onReject: (reason: string) => void;
  isLoading: boolean;
}

function RejectModal({ leaveRequest, isOpen, onClose, onReject, isLoading }: RejectModalProps) {
  const [reason, setReason] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (reason.trim()) {
      onReject(reason.trim());
      setReason('');
    }
  };

  if (!isOpen || !leaveRequest) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Reject Leave Request
        </h3>
        <div className="mb-4 p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">
            <strong>Employee:</strong> {leaveRequest.employee.person.full_name}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Dates:</strong> {new Date(leaveRequest.start_date).toLocaleDateString()} - {new Date(leaveRequest.end_date).toLocaleDateString()}
          </p>
          {leaveRequest.reason && (
            <p className="text-sm text-gray-600">
              <strong>Reason:</strong> {leaveRequest.reason}
            </p>
          )}
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
              Rejection Reason *
            </label>
            <textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              placeholder="Please provide a reason for rejecting this request..."
            />
          </div>
          
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !reason.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Rejecting...' : 'Reject Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ApproveRequestsPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  
  // Permission checks
  const canApproveAll = useHasPermission('leave_request.approve.all');
  const canApprove = useHasAnyPermission(['leave_request.approve.supervised', 'leave_request.approve.all']);
  
  const [rejectModalOpen, setRejectModalOpen] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState<LeaveRequest | null>(null);

  // Get pending approval requests
  const { data: pendingRequests = [], isLoading: requestsLoading, error } = useQuery({
    queryKey: ['pending-approvals'],
    queryFn: () => apiClient.getPendingApprovals(),
    enabled: !!user && canApprove,
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) => 
      apiClient.approveLeaveRequest(id, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
      queryClient.invalidateQueries({ queryKey: ['my-leave-requests'] });
    },
    onError: (error) => {
      console.error('Error approving leave request:', error);
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => 
      apiClient.rejectLeaveRequest(id, { reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-approvals'] });
      queryClient.invalidateQueries({ queryKey: ['my-leave-requests'] });
      setRejectModalOpen(false);
      setSelectedRequest(null);
    },
    onError: (error) => {
      console.error('Error rejecting leave request:', error);
    },
  });

  const handleApprove = (request: LeaveRequest) => {
    approveMutation.mutate({ 
      id: request.leave_id,
      reason: 'Approved by supervisor'
    });
  };

  const handleRejectClick = (request: LeaveRequest) => {
    setSelectedRequest(request);
    setRejectModalOpen(true);
  };

  const handleReject = (reason: string) => {
    if (selectedRequest) {
      rejectMutation.mutate({ 
        id: selectedRequest.leave_id, 
        reason 
      });
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusBadgeColor = (status: LeaveStatus) => {
    switch (status) {
      case LeaveStatus.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case LeaveStatus.APPROVED:
        return 'bg-green-100 text-green-800';
      case LeaveStatus.REJECTED:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (!user || !canApprove) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">You don&apos;t have permission to approve leave requests.</p>
        </div>
      </div>
    );
  }

  if (requestsLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading pending requests...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Error</h1>
          <p className="text-gray-600">Failed to load pending requests. Please try again.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Approve Leave Requests</h1>
          <p className="mt-2 text-gray-600">
            Review and approve leave requests from your team members
            {canApproveAll && ' (or all employees)'}
          </p>
        </div>

        {pendingRequests.length === 0 ? (
          <div className="bg-white shadow-sm rounded-lg">
            <div className="p-8 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Pending Requests</h3>
              <p className="text-gray-600">All leave requests have been processed.</p>
            </div>
          </div>
        ) : (
          <div className="bg-white shadow-sm rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">
                Pending Requests ({pendingRequests.length})
              </h2>
            </div>
            
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Employee
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Dates
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Reason
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Submitted
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {pendingRequests.map((request) => (
                    <tr key={request.leave_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {request.employee.person.full_name}
                        </div>
                        <div className="text-sm text-gray-500">
                          {request.employee.work_email}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {formatDate(request.start_date)} - {formatDate(request.end_date)}
                        </div>
                        <div className="text-sm text-gray-500">
                          {Math.ceil((new Date(request.end_date).getTime() - new Date(request.start_date).getTime()) / (1000 * 60 * 60 * 24)) + 1} day(s)
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900 max-w-xs truncate">
                          {request.reason || 'No reason provided'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatDate(request.submitted_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(request.status)}`}>
                          {request.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleApprove(request)}
                            disabled={approveMutation.isPending}
                            className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {approveMutation.isPending ? '...' : 'Approve'}
                          </button>
                          <button
                            onClick={() => handleRejectClick(request)}
                            disabled={rejectMutation.isPending}
                            className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {rejectMutation.isPending ? '...' : 'Reject'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <RejectModal
        leaveRequest={selectedRequest}
        isOpen={rejectModalOpen}
        onClose={() => setRejectModalOpen(false)}
        onReject={handleReject}
        isLoading={rejectMutation.isPending}
      />
    </div>
  );
}