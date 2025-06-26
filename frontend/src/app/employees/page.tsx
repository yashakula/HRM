'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api';
import { Employee, EmployeeSearchParams } from '@/lib/types';

export default function EmployeesPage() {
  const router = useRouter();
  const [searchParams, setSearchParams] = useState<EmployeeSearchParams>({
    name: '',
    employee_id: undefined,
    status: undefined,
    skip: 0,
    limit: 10
  });

  const { data: employees, isLoading, error, refetch } = useQuery({
    queryKey: ['employees', searchParams],
    queryFn: () => {
      // Only search if we have search criteria, otherwise get all employees
      const hasSearchCriteria = searchParams.name || searchParams.employee_id || searchParams.status;
      
      if (hasSearchCriteria) {
        return apiClient.searchEmployees(searchParams);
      } else {
        return apiClient.getAllEmployees(searchParams.skip, searchParams.limit);
      }
    },
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  const handleInputChange = (field: keyof EmployeeSearchParams, value: string | number | undefined) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h1 className="text-2xl font-bold text-gray-900">Employee Directory</h1>
          <p className="mt-1 text-sm text-gray-700">
            Search and view employee records
          </p>
        </div>
      </div>

      {/* Search Form */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Name
                </label>
                <input
                  type="text"
                  id="name"
                  value={searchParams.name || ''}
                  onChange={(e) => handleInputChange('name', e.target.value)}
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
                  value={searchParams.employee_id || ''}
                  onChange={(e) => handleInputChange('employee_id', e.target.value ? parseInt(e.target.value) : undefined)}
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
                  value={searchParams.status || ''}
                  onChange={(e) => handleInputChange('status', e.target.value as 'Active' | 'Inactive' | undefined)}
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
                Search
              </button>

              <button
                type="button"
                onClick={() => {
                  setSearchParams({ name: '', employee_id: undefined, status: undefined, skip: 0, limit: 10 });
                  setTimeout(() => refetch(), 0);
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Clear
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Employee Records
            </h3>
            {employees && (
              <span className="text-sm text-gray-700">
                {employees.length} employee{employees.length !== 1 ? 's' : ''} found
              </span>
            )}
          </div>

          {isLoading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-800">Loading employees...</p>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-600">
                Error loading employees: {error instanceof Error ? error.message : 'Unknown error'}
              </p>
            </div>
          )}

          {employees && employees.length === 0 && !isLoading && (
            <div className="text-center py-8">
              <p className="text-gray-700">No employees found matching your search criteria.</p>
            </div>
          )}

          {employees && employees.length > 0 && (
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
                        <button
                          onClick={() => router.push(`/employees/${employee.employee_id}/edit`)}
                          className="text-blue-600 hover:text-blue-900 focus:outline-none focus:underline"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}