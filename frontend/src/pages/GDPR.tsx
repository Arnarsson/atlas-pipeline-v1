import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Shield,
  FileText,
  Trash2,
  Download,
  Clock,
  CheckCircle,
  AlertCircle,
  X,
} from 'lucide-react';
import { exportSubjectData, deleteSubjectData, getGDPRRequests } from '@/api/client';
import type { GDPRRequest } from '@/types';
import { toast } from 'react-hot-toast';

export default function GDPR() {
  const [requestType, setRequestType] = useState<'export' | 'delete'>('export');
  const [identifierType, setIdentifierType] = useState<'email' | 'phone' | 'ssn' | 'customer_id'>(
    'email'
  );
  const [identifier, setIdentifier] = useState('');
  const [reason, setReason] = useState('');
  const [selectedRequest, setSelectedRequest] = useState<GDPRRequest | null>(null);

  const queryClient = useQueryClient();

  const { data: requests, isLoading } = useQuery({
    queryKey: ['gdpr-requests'],
    queryFn: () => getGDPRRequests(),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const { data: stats } = useQuery({
    queryKey: ['gdpr-stats'],
    queryFn: async () => {
      const allRequests = await getGDPRRequests();
      return {
        total: allRequests.length,
        exports: allRequests.filter((r: GDPRRequest) => r.request_type === 'export').length,
        deletions: allRequests.filter((r: GDPRRequest) => r.request_type === 'delete').length,
        pending: allRequests.filter((r: GDPRRequest) => r.status === 'pending').length,
        avgResponseTime: '2.5 hours', // Mock data
      };
    },
  });

  const exportMutation = useMutation({
    mutationFn: () => exportSubjectData(identifier, identifierType),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gdpr-requests'] });
      toast.success('Data export request submitted successfully');
      setIdentifier('');
    },
    onError: () => {
      toast.error('Failed to submit export request');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: () => deleteSubjectData(identifier, identifierType, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['gdpr-requests'] });
      toast.success('Data deletion request submitted successfully');
      setIdentifier('');
      setReason('');
    },
    onError: () => {
      toast.error('Failed to submit deletion request');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (requestType === 'export') {
      exportMutation.mutate();
    } else {
      if (!reason.trim()) {
        toast.error('Please provide a reason for deletion');
        return;
      }
      deleteMutation.mutate();
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />;
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-600 animate-spin" />;
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <Clock className="h-5 w-5 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">GDPR Compliance</h1>
        <p className="mt-2 text-sm text-gray-600">
          Manage data subject access and deletion requests
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="bg-white overflow-hidden shadow-md rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 rounded-lg bg-blue-500">
                  <FileText className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Total Requests</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stats?.total || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-md rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 rounded-lg bg-green-500">
                  <Download className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Data Exports</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stats?.exports || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-md rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 rounded-lg bg-red-500">
                  <Trash2 className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Data Deletions</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stats?.deletions || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow-md rounded-lg">
          <div className="p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="p-3 rounded-lg bg-orange-500">
                  <Clock className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">Pending</dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stats?.pending || 0}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Request Form */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Submit New Request</h2>
        <form onSubmit={handleSubmit} className="space-y-4" data-testid="gdpr-request-form">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Request Type
              </label>
              <select
                data-testid="request-type-select"
                value={requestType}
                onChange={(e) => setRequestType(e.target.value as 'export' | 'delete')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="export">Data Export (Access Request)</option>
                <option value="delete">Data Deletion (Right to be Forgotten)</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Identifier Type
              </label>
              <select
                data-testid="identifier-type-select"
                value={identifierType}
                onChange={(e) =>
                  setIdentifierType(
                    e.target.value as 'email' | 'phone' | 'ssn' | 'customer_id'
                  )
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              >
                <option value="email">Email Address</option>
                <option value="phone">Phone Number</option>
                <option value="ssn">Social Security Number</option>
                <option value="customer_id">Customer ID</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject Identifier
            </label>
            <input
              type="text"
              data-testid="subject-identifier-input"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              placeholder={
                identifierType === 'email'
                  ? 'user@example.com'
                  : identifierType === 'phone'
                  ? '+1234567890'
                  : identifierType === 'ssn'
                  ? '123-45-6789'
                  : 'CUST-12345'
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            />
          </div>

          {requestType === 'delete' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason for Deletion <span className="text-red-500">*</span>
              </label>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
                rows={3}
                placeholder="Provide a detailed reason for this deletion request..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>
          )}

          <div className="flex justify-end">
            <button
              type="submit"
              data-testid="submit-gdpr-request-btn"
              disabled={exportMutation.isPending || deleteMutation.isPending}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 transition-colors"
            >
              {exportMutation.isPending || deleteMutation.isPending
                ? 'Submitting...'
                : `Submit ${requestType === 'export' ? 'Export' : 'Deletion'} Request`}
            </button>
          </div>
        </form>
      </div>

      {/* Requests Table */}
      <div className="bg-white shadow-md rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Requests</h2>
        </div>
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-8 text-center" data-testid="requests-loading">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto" data-testid="loading-spinner" />
            </div>
          ) : requests && requests.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200" data-testid="requests-table">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Subject
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Submitted
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {requests.map((request: GDPRRequest) => (
                  <tr key={request.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Shield className="h-5 w-5 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {request.subject_identifier}
                          </div>
                          <div className="text-sm text-gray-500">{request.identifier_type}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded ${
                          request.request_type === 'export'
                            ? 'bg-green-100 text-green-800'
                            : request.request_type === 'delete'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {request.request_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(request.status)}
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(
                            request.status
                          )}`}
                        >
                          {request.status}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(request.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      {request.status === 'completed' && (
                        <button
                          onClick={() => setSelectedRequest(request)}
                          className="text-primary-600 hover:text-primary-700 font-medium"
                        >
                          View Results
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="p-12 text-center">
              <Shield className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No requests yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Submit your first GDPR request using the form above
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Results Modal */}
      {selectedRequest && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Request Results</h2>
              <button
                onClick={() => setSelectedRequest(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-sm text-gray-500">Subject:</span>
                  <p className="font-medium text-gray-900">
                    {selectedRequest.subject_identifier}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Request Type:</span>
                  <p className="font-medium text-gray-900">{selectedRequest.request_type}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Status:</span>
                  <p className="font-medium text-gray-900">{selectedRequest.status}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Completed:</span>
                  <p className="font-medium text-gray-900">
                    {selectedRequest.completed_at
                      ? new Date(selectedRequest.completed_at).toLocaleString()
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {selectedRequest.result && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Results</h3>
                  <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                    {selectedRequest.result.records_found !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Records Found:</span>
                        <span className="font-medium text-gray-900">
                          {selectedRequest.result.records_found}
                        </span>
                      </div>
                    )}
                    {selectedRequest.result.records_deleted !== undefined && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Records Deleted:</span>
                        <span className="font-medium text-gray-900">
                          {selectedRequest.result.records_deleted}
                        </span>
                      </div>
                    )}
                    {selectedRequest.result.layers_processed && (
                      <div>
                        <span className="text-gray-600">Layers Processed:</span>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {selectedRequest.result.layers_processed.map((layer, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 text-sm bg-primary-100 text-primary-800 rounded"
                            >
                              {layer}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {selectedRequest.request_type === 'export' &&
                    selectedRequest.result.data_export && (
                      <div className="mt-4">
                        <button
                          onClick={() => {
                            const dataStr = JSON.stringify(
                              selectedRequest.result!.data_export,
                              null,
                              2
                            );
                            const blob = new Blob([dataStr], { type: 'application/json' });
                            const url = URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = `gdpr_export_${selectedRequest.id}.json`;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            URL.revokeObjectURL(url);
                          }}
                          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
                        >
                          <Download className="h-4 w-4" />
                          Download Exported Data
                        </button>
                      </div>
                    )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
