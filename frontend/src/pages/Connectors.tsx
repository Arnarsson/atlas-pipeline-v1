import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getConnectors, deleteConnector, triggerSync } from '@/api/client';
import { Connector } from '@/types';
import { PlusCircle, Database, Trash2, Play, Edit, Pause, AlertCircle } from 'lucide-react';
import ConnectorWizard from '@/components/Connectors/ConnectorWizard';
import SyncHistoryModal from '@/components/Connectors/SyncHistoryModal';
import toast from 'react-hot-toast';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
      active: 'bg-green-500/10 text-green-600',
      inactive: 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]',
      error: 'bg-red-500/10 text-red-600',
    };
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const getTypeIcon = (_type: Connector['type']) => {
    return <Database className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Connectors</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage data sources and sync schedules
          </p>
        </div>
        <Button
          data-testid="create-connector-btn"
          onClick={() => setIsWizardOpen(true)}
        >
          <PlusCircle className="w-4 h-4 mr-2" />
          New Connector
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total Connectors</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">{connectors.length}</p>
              </div>
              <Database className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Active</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {connectors.filter(c => c.status === 'active').length}
                </p>
              </div>
              <div className="h-2 w-2 bg-green-500 rounded-full" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Inactive</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {connectors.filter(c => c.status === 'inactive').length}
                </p>
              </div>
              <Pause className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Errors</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {connectors.filter(c => c.status === 'error').length}
                </p>
              </div>
              <AlertCircle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Connectors Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent mx-auto" />
              <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">Loading connectors...</p>
            </div>
          ) : connectors.length === 0 ? (
            <div className="p-12 text-center" data-testid="empty-state">
              <Database className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
              <h3 className="text-sm font-medium text-[hsl(var(--foreground))] mb-1">No connectors yet</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                Get started by creating your first data connector
              </p>
              <Button
                data-testid="create-first-connector-btn"
                onClick={() => setIsWizardOpen(true)}
                variant="outline"
              >
                <PlusCircle className="w-4 h-4 mr-2" />
                Create Connector
              </Button>
            </div>
          ) : (
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-[hsl(var(--border))]">
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Schedule
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Last Sync
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border))]">
                {connectors.map((connector) => (
                  <tr key={connector.id} className="hover:bg-[hsl(var(--secondary)/0.5)]">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        {getTypeIcon(connector.type)}
                        <div>
                          <div className="text-sm font-medium text-[hsl(var(--foreground))]">{connector.name}</div>
                          <div className="text-xs text-[hsl(var(--muted-foreground))]">{connector.id.slice(0, 8)}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="text-sm text-[hsl(var(--foreground))] capitalize">
                        {connector.type.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getStatusBadge(connector.status)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--muted-foreground))]">
                      {connector.schedule || 'Manual'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--muted-foreground))]">
                      {connector.last_sync
                        ? formatDistanceToNow(new Date(connector.last_sync), { addSuffix: true })
                        : 'Never'}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => handleSync(connector.id)}
                          title="Sync Now"
                        >
                          <Play className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setSyncHistoryConnectorId(connector.id)}
                          title="View History"
                        >
                          <Database className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => setSelectedConnector(connector)}
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-500/10"
                          onClick={() => handleDelete(connector.id, connector.name)}
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

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
