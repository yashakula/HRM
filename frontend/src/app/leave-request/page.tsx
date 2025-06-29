'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { LeaveRequestCreateRequest, LeaveStatus } from '@/lib/types';
import { 
  useAuthStore, 
  useHasPermission, 
  useHasAnyPermission 
} from '@/store/authStore';

interface LeaveRequestFormData {
  start_date: string;
  end_date: string;
  reason: string;
}

export default function LeaveRequestPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  
  // Permission checks
  const canCreateLeaveRequest = useHasAnyPermission(['leave_request.create.all', 'leave_request.create.own']);
  const canViewOwnLeaveRequests = useHasPermission('leave_request.read.own');
  const canViewAllLeaveRequests = useHasPermission('leave_request.read.all');
  
  const [formData, setFormData] = useState<LeaveRequestFormData>({
    start_date: '',
    end_date: '',
    reason: ''
  });
  
  const [confirmationMessage, setConfirmationMessage] = useState<string>('');

  // No longer need to fetch assignments for leave requests

  // Get employee's leave requests for display
  const { data: leaveRequests = [], isLoading: requestsLoading } = useQuery({
    queryKey: ['my-leave-requests'],
    queryFn: () => apiClient.getMyLeaveRequests(),
    enabled: !!user,
  });

  // Get primary assignment supervisors
  const { data: primarySupervisors = [], isLoading: supervisorsLoading } = useQuery({
    queryKey: ['my-primary-supervisors'],
    queryFn: () => apiClient.getPrimaryAssignmentSupervisors(),
    enabled: !!user,
  });

  // Create leave request mutation
  const createMutation = useMutation({
    mutationFn: (data: LeaveRequestCreateRequest) => apiClient.createLeaveRequest(data),
    onSuccess: (newRequest) => {
      // Refresh the leave requests list
      queryClient.invalidateQueries({ queryKey: ['my-leave-requests'] });
      
      // Reset form
      setFormData({
        start_date: '',
        end_date: '',
        reason: ''
      });
      
      // Show confirmation message with approver info
      const approverNames = primarySupervisors.length > 0 
        ? primarySupervisors.map(s => s.person.full_name).join(', ')
        : 'your supervisor';
      
      setConfirmationMessage(
        `Leave request submitted successfully from ${newRequest.start_date} to ${newRequest.end_date}. Sent to ${approverNames} for approval.`
      );
      
      // Clear confirmation message after 5 seconds
      setTimeout(() => setConfirmationMessage(''), 5000);
    },
    onError: (error) => {
      console.error('Error creating leave request:', error);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.start_date || !formData.end_date) {
      alert('Please fill in all required fields');
      return;
    }
    
    // Validate date range
    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      alert('Start date must be before or equal to end date');
      return;
    }
    
    const requestData: LeaveRequestCreateRequest = {
      start_date: formData.start_date,
      end_date: formData.end_date,
      reason: formData.reason || undefined,
    };
    
    createMutation.mutate(requestData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const renderSupervisorInfo = () => {
    if (supervisorsLoading) {
      return <span className="text-sm text-gray-500">Loading supervisors...</span>;
    }

    if (primarySupervisors.length === 0) {
      return <span className="text-sm text-red-500">No supervisor assigned to primary assignment</span>;
    }

    if (primarySupervisors.length === 1) {
      return (
        <span className="text-sm text-gray-600">
          Approval required from: <span className="font-medium">{primarySupervisors[0].person.full_name}</span>
        </span>
      );
    }

    return (
      <div className="text-sm text-gray-600">
        <span>Approval required from: </span>
        <span className="font-medium">
          {primarySupervisors.map(supervisor => supervisor.person.full_name).join(', ')}
        </span>
      </div>
    );
  };

  if (!user || (!canCreateLeaveRequest && !canViewOwnLeaveRequests)) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">You don&apos;t have permission to view or create leave requests.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Submit Leave Request</h1>
          <p className="mt-2 text-gray-600">Request time off from work</p>
        </div>

        {/* Confirmation Message */}
        {confirmationMessage && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">{confirmationMessage}</p>
              </div>
            </div>
          </div>
        )}

        <div className={`grid gap-8 ${
          canCreateLeaveRequest && (canViewOwnLeaveRequests || canViewAllLeaveRequests) 
            ? 'grid-cols-1 lg:grid-cols-2' 
            : 'grid-cols-1 max-w-2xl mx-auto'
        }`}>
          {/* Leave Request Form */}
          {canCreateLeaveRequest && (
            <div className="bg-white shadow-sm rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">New Leave Request</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">

              {/* Approver Information */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-blue-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-blue-800">Request Approval Process</h3>
                    <div className="mt-1 text-sm text-blue-700">
                      {supervisorsLoading ? (
                        <span>Loading approval information...</span>
                      ) : primarySupervisors.length === 0 ? (
                        <span className="text-red-600">⚠️ No supervisor assigned - request may not be approved</span>
                      ) : (
                        <span>
                          Your request will be sent to <span className="font-semibold">
                            {primarySupervisors.map(supervisor => supervisor.person.full_name).join(', ')}
                          </span> for approval.
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Date Range */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="start_date" className="block text-sm font-medium text-gray-700 mb-2">
                    Start Date *
                  </label>
                  <input
                    type="date"
                    id="start_date"
                    name="start_date"
                    value={formData.start_date}
                    onChange={handleInputChange}
                    required
                    min={new Date().toISOString().split('T')[0]} // Prevent past dates
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label htmlFor="end_date" className="block text-sm font-medium text-gray-700 mb-2">
                    End Date *
                  </label>
                  <input
                    type="date"
                    id="end_date"
                    name="end_date"
                    value={formData.end_date}
                    onChange={handleInputChange}
                    required
                    min={formData.start_date || new Date().toISOString().split('T')[0]}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Reason */}
              <div>
                <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                  Reason (Optional)
                </label>
                <textarea
                  id="reason"
                  name="reason"
                  rows={3}
                  value={formData.reason}
                  onChange={handleInputChange}
                  placeholder="Provide details about your leave request..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              {/* Submit Button */}
              <div>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending ? 'Submitting...' : 'Submit Leave Request'}
                </button>
              </div>
              
              {createMutation.error && (
                <div className="text-red-600 text-sm mt-2">
                  Error: {createMutation.error.message}
                </div>
              )}
            </form>
          </div>
          )}

          {/* Leave Request History */}
          {(canViewOwnLeaveRequests || canViewAllLeaveRequests) && (
            <div className="bg-white shadow-sm rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Your Leave Requests</h2>
              <div className="mt-2">
                {renderSupervisorInfo()}
              </div>
            </div>
            
            <div className="p-6">
              {requestsLoading ? (
                <div className="text-gray-500">Loading...</div>
              ) : leaveRequests.length === 0 ? (
                <div className="text-gray-500 text-center py-8">
                  No leave requests yet. Submit your first request using the form.
                </div>
              ) : (
                <div className="space-y-4">
                  {leaveRequests.map((request) => (
                    <div key={request.leave_id} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(request.status)}`}>
                              {request.status}
                            </span>
                            <span className="text-sm text-gray-500">
                              Employee: {request.employee.person.full_name}
                            </span>
                          </div>
                          
                          <p className="text-sm font-medium text-gray-900 mb-1">
                            {formatDate(request.start_date)} - {formatDate(request.end_date)}
                          </p>
                          
                          {request.reason && (
                            <p className="text-sm text-gray-600 mb-2">{request.reason}</p>
                          )}
                          
                          <p className="text-xs text-gray-500">
                            Submitted: {formatDate(request.submitted_at)}
                            {request.decision_at && ` • Decided: ${formatDate(request.decision_at)}`}
                          </p>
                          
                          {request.status === LeaveStatus.PENDING && (
                            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                              {primarySupervisors.length > 0 ? (
                                <p className="text-xs text-yellow-800">
                                  <span className="font-medium">⏳ Pending Approval:</span> Waiting for approval from{' '}
                                  <span className="font-semibold">{primarySupervisors.map(s => s.person.full_name).join(', ')}</span>
                                </p>
                              ) : (
                                <p className="text-xs text-red-600">
                                  <span className="font-medium">⚠️ No Approver:</span> No supervisor assigned to approve this request
                                </p>
                              )}
                            </div>
                          )}

                          {request.status === LeaveStatus.APPROVED && request.decision_maker && (
                            <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                              <p className="text-xs text-green-800">
                                <span className="font-medium">✅ Approved by:</span> {request.decision_maker.person.full_name}
                              </p>
                            </div>
                          )}

                          {request.status === LeaveStatus.REJECTED && request.decision_maker && (
                            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                              <p className="text-xs text-red-800">
                                <span className="font-medium">❌ Rejected by:</span> {request.decision_maker.person.full_name}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          )}
          
          {/* No access message */}
          {!canCreateLeaveRequest && !canViewOwnLeaveRequests && !canViewAllLeaveRequests && (
            <div className="bg-white shadow-sm rounded-lg">
              <div className="p-8 text-center">
                <div className="text-6xl mb-4">🔒</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Leave Request Access</h3>
                <p className="text-gray-600">You don&apos;t have permission to view or create leave requests.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}