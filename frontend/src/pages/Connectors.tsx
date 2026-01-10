import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getConnectors, deleteConnector, triggerSync } from '@/api/client';
import { Connector } from '@/types';
import { PlusCircle, Database, Trash2, Play, Edit } from 'lucide-react';
import ConnectorWizard from '@/components/Connectors/ConnectorWizard';
import SyncHistoryModal from '@/components/Connectors/SyncHistoryModal';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';

export default function Connectors() {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);
  const [syncHistoryConnectorId, setSyncHistoryConnectorId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: connectors = [], isLoading } = useQuery({
    queryKey: ['connectors'],
    queryFn: getConnectors,
    refetchInterval: 30000,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConnector,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] });
      toast.success('Connector deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete connector');
    },
  });

  const syncMutation = useMutation({
    mutationFn: triggerSync,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connectors'] });
      toast.success('Sync started successfully');
    },
    onError: () => {
      toast.error('Failed to start sync');
    },
  });

  const handleDelete = async (id: string, name: string) => {
    if (window.confirm(`Are you sure you want to delete connector "${name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const handleSync = (connectorId: string) => {
    syncMutation.mutate(connectorId);
  };

  const getStatusBadge = (status: Connector['status']) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      inactive: 'bg-gray-100 text-gray-800',
      error: 'bg-red-100 text-red-800',
    };
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getTypeIcon = (type: Connector['type']) => {
    const icons = {
      postgresql: '🐘',
      mysql: '🐬',
      rest_api: '🌐',
      csv: '📄',
      json: '📋',
    };
    return icons[type] || '📦';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Connectors</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage data sources and sync schedules
          </p>
        </div>
        <button
          data-testid="create-connector-btn"
          onClick={() => setIsWizardOpen(true)}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          <PlusCircle className="w-5 h-5 mr-2" />
          New Connector
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Connectors</p>
              <p className="text-2xl font-bold text-gray-900">{connectors.length}</p>
            </div>
            <Database className="w-8 h-8 text-blue-600" />
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Active</p>
              <p className="text-2xl font-bold text-green-600">
                {connectors.filter(c => c.status === 'active').length}
              </p>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-green-600 text-xl">✓</span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Inactive</p>
              <p className="text-2xl font-bold text-gray-600">
                {connectors.filter(c => c.status === 'inactive').length}
              </p>
            </div>
            <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center">
              <span className="text-gray-600 text-xl">⏸</span>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Errors</p>
              <p className="text-2xl font-bold text-red-600">
                {connectors.filter(c => c.status === 'error').length}
              </p>
            </div>
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <span className="text-red-600 text-xl">✕</span>
            </div>
          </div>
        </div>
      </div>

      {/* Connectors Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading connectors...</p>
            </div>
          ) : connectors.length === 0 ? (
            <div className="p-12 text-center" data-testid="empty-state">
              <Database className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No connectors yet</h3>
              <p className="text-gray-600 mb-6">
                Get started by creating your first data connector
              </p>
              <button
                data-testid="create-first-connector-btn"
                onClick={() => setIsWizardOpen(true)}
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                <PlusCircle className="w-5 h-5 mr-2" />
                Create Connector
              </button>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Schedule
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Sync
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {connectors.map((connector) => (
                  <tr key={connector.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="text-2xl mr-3">{getTypeIcon(connector.type)}</span>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{connector.name}</div>
                          <div className="text-sm text-gray-500">{connector.id.slice(0, 8)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 capitalize">
                        {connector.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(connector.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {connector.schedule || 'Manual'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {connector.last_sync
                        ? formatDistanceToNow(new Date(connector.last_sync), { addSuffix: true })
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleSync(connector.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="Sync Now"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => setSyncHistoryConnectorId(connector.id)}
                          className="text-gray-600 hover:text-gray-900"
                          title="View History"
                        >
                          📊
                        </button>
                        <button
                          onClick={() => setSelectedConnector(connector)}
                          className="text-gray-600 hover:text-gray-900"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(connector.id, connector.name)}
                          className="text-red-600 hover:text-red-900"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Modals */}
      {isWizardOpen && (
        <ConnectorWizard
          onClose={() => setIsWizardOpen(false)}
          connector={selectedConnector}
          onSuccess={() => {
            setIsWizardOpen(false);
            setSelectedConnector(null);
            queryClient.invalidateQueries({ queryKey: ['connectors'] });
          }}
        />
      )}

      {syncHistoryConnectorId && (
        <SyncHistoryModal
          connectorId={syncHistoryConnectorId}
          onClose={() => setSyncHistoryConnectorId(null)}
        />
      )}
    </div>
  );
}
