'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { LeaveRequestCreateRequest, LeaveStatus, UserRole } from '@/lib/types';
import { useAuthStore } from '@/store/authStore';

interface LeaveRequestFormData {
  assignment_id: string;
  start_date: string;
  end_date: string;
  reason: string;
}

export default function LeaveRequestPage() {
  const { user } = useAuthStore();
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState<LeaveRequestFormData>({
    assignment_id: '',
    start_date: '',
    end_date: '',
    reason: ''
  });
  
  const [confirmationMessage, setConfirmationMessage] = useState<string>('');

  // Get employee's active assignments for the dropdown
  const { data: assignments = [], isLoading: assignmentsLoading } = useQuery({
    queryKey: ['employee-active-assignments', user?.employee?.employee_id],
    queryFn: () => {
      if (!user?.employee?.employee_id) throw new Error('Employee ID not found');
      return apiClient.getEmployeeActiveAssignments(user.employee.employee_id);
    },
    enabled: !!user?.employee?.employee_id,
  });

  // Get employee's leave requests for display
  const { data: leaveRequests = [], isLoading: requestsLoading } = useQuery({
    queryKey: ['my-leave-requests'],
    queryFn: () => apiClient.getMyLeaveRequests(),
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
        assignment_id: '',
        start_date: '',
        end_date: '',
        reason: ''
      });
      
      // Show confirmation message
      const assignment = assignments.find(a => a.assignment_id === newRequest.assignment_id);
      const assignmentName = assignment ? 
        `${assignment.assignment_type.description} in ${assignment.assignment_type.department.name}` :
        'Selected assignment';
      
      setConfirmationMessage(
        `Leave request submitted successfully for ${assignmentName} from ${newRequest.start_date} to ${newRequest.end_date}.`
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
    
    if (!formData.assignment_id || !formData.start_date || !formData.end_date) {
      alert('Please fill in all required fields');
      return;
    }
    
    // Validate date range
    if (new Date(formData.start_date) > new Date(formData.end_date)) {
      alert('Start date must be before or equal to end date');
      return;
    }
    
    const requestData: LeaveRequestCreateRequest = {
      assignment_id: parseInt(formData.assignment_id),
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

  if (!user || user.role !== UserRole.EMPLOYEE) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h1 className="text-2xl font-bold text-red-600 mb-4">Access Denied</h1>
          <p className="text-gray-600">Only employees can submit leave requests.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Submit Leave Request</h1>
          <p className="mt-2 text-gray-600">Request time off for your assignments</p>
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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Leave Request Form */}
          <div className="bg-white shadow-sm rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">New Leave Request</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Assignment Selection */}
              <div>
                <label htmlFor="assignment_id" className="block text-sm font-medium text-gray-700 mb-2">
                  Assignment *
                </label>
                <select
                  id="assignment_id"
                  name="assignment_id"
                  value={formData.assignment_id}
                  onChange={handleInputChange}
                  required
                  disabled={assignmentsLoading}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                >
                  <option value="">
                    {assignmentsLoading ? 'Loading assignments...' : 'Select an assignment'}
                  </option>
                  {assignments.map((assignment) => (
                    <option key={assignment.assignment_id} value={assignment.assignment_id}>
                      {assignment.assignment_type.description} - {assignment.assignment_type.department.name}
                      {assignment.is_primary && ' (Primary)'}
                    </option>
                  ))}
                </select>
                {assignments.length === 0 && !assignmentsLoading && (
                  <p className="mt-1 text-sm text-red-600">No active assignments found. Please contact HR.</p>
                )}
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
                  disabled={createMutation.isPending || assignments.length === 0}
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

          {/* Leave Request History */}
          <div className="bg-white shadow-sm rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Your Leave Requests</h2>
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
                              {request.assignment.assignment_type.description}
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
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}