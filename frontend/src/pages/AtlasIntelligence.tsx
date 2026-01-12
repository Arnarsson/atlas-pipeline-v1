import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Database,
  Cloud,
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  ChevronRight,
  Zap,
  Server,
  Key,
  Settings,
  Eye,
  EyeOff,
  Save,
  X
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/api/client';

// Types for Airbyte connectors
interface AirbyteConnector {
  id: string;
  description: string;
  type: string;
  path: string | null;
  connector_name: string | null;
}

interface AirbyteEntity {
  name: string;
  actions: string[];
  description?: string;
}

interface ExecuteRequest {
  connector_id: string;
  entity: string;
  action: string;
  params?: Record<string, any>;
}

interface N8NWorkflow {
  id: string;
  name: string;
  active: boolean;
}

interface CredentialStatus {
  configured: boolean;
  env_var: string;
  masked: string;
}

// API functions
const getAirbyteConnectors = async (): Promise<AirbyteConnector[]> => {
  const response = await api.get('/atlas-intelligence/connectors');
  return response.data;
};

const getAirbyteHealth = async () => {
  const response = await api.get('/atlas-intelligence/health');
  return response.data;
};

const getConnectorEntities = async (connectorId: string): Promise<AirbyteEntity[]> => {
  const response = await api.get(`/atlas-intelligence/connectors/${connectorId}/entities`);
  return response.data;
};

const executeAirbyteOperation = async (request: ExecuteRequest) => {
  const response = await api.post('/atlas-intelligence/execute', request);
  return response.data;
};

const getN8NHealth = async () => {
  const response = await api.get('/n8n/health');
  return response.data;
};

const getN8NWorkflows = async (): Promise<N8NWorkflow[]> => {
  const response = await api.get('/n8n/workflows');
  return response.data;
};

const getCredentials = async (): Promise<Record<string, CredentialStatus>> => {
  const response = await api.get('/atlas-intelligence/credentials');
  return response.data;
};

const updateCredentials = async (data: { connector_id: string; api_key: string }) => {
  const response = await api.post('/atlas-intelligence/credentials', data);
  return response.data;
};

export default function AtlasIntelligence() {
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null);
  const [showN8N, setShowN8N] = useState(false);
  const [showCredentials, setShowCredentials] = useState(false);
  const [editingCredential, setEditingCredential] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const queryClient = useQueryClient();

  // Queries
  const { data: connectors = [], isLoading: loadingConnectors } = useQuery({
    queryKey: ['airbyte-connectors'],
    queryFn: getAirbyteConnectors,
    refetchInterval: 60000,
  });

  const { data: health } = useQuery({
    queryKey: ['airbyte-health'],
    queryFn: getAirbyteHealth,
    refetchInterval: 30000,
  });

  const { data: n8nHealth } = useQuery({
    queryKey: ['n8n-health'],
    queryFn: getN8NHealth,
    refetchInterval: 30000,
  });

  const { data: n8nWorkflows = [] } = useQuery({
    queryKey: ['n8n-workflows'],
    queryFn: getN8NWorkflows,
    enabled: showN8N,
  });

  const { data: entities = [], isLoading: loadingEntities } = useQuery({
    queryKey: ['connector-entities', selectedConnector],
    queryFn: () => selectedConnector ? getConnectorEntities(selectedConnector) : Promise.resolve([]),
    enabled: !!selectedConnector,
  });

  const { data: credentials = {} } = useQuery({
    queryKey: ['credentials'],
    queryFn: getCredentials,
    enabled: showCredentials,
  });

  // Mutations
  const executeMutation = useMutation({
    mutationFn: executeAirbyteOperation,
    onSuccess: (data) => {
      toast.success('Operation executed successfully');
      console.log('Execution result:', data);
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.error || 'Operation failed');
    },
  });

  const credentialMutation = useMutation({
    mutationFn: updateCredentials,
    onSuccess: () => {
      toast.success('API key saved successfully');
      queryClient.invalidateQueries({ queryKey: ['credentials'] });
      setEditingCredential(null);
      setApiKeyInput('');
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.detail || 'Failed to save API key');
    },
  });

  const handleExecute = (entity: string, action: string) => {
    if (!selectedConnector) return;
    executeMutation.mutate({
      connector_id: selectedConnector,
      entity,
      action,
      params: {},
    });
  };

  const handleSaveCredential = (connectorId: string) => {
    if (!apiKeyInput.trim()) {
      toast.error('Please enter an API key');
      return;
    }
    credentialMutation.mutate({
      connector_id: connectorId,
      api_key: apiKeyInput,
    });
  };

  const getConnectorIcon = (id: string) => {
    const iconMap: Record<string, JSX.Element> = {
      'n8n': <Zap className="w-5 h-5 text-orange-500" />,
      'github': <Cloud className="w-5 h-5 text-gray-700" />,
      'stripe': <Database className="w-5 h-5 text-purple-500" />,
      'hubspot': <Database className="w-5 h-5 text-orange-600" />,
      'salesforce': <Cloud className="w-5 h-5 text-blue-500" />,
      'jira': <Database className="w-5 h-5 text-blue-600" />,
      'linear': <Database className="w-5 h-5 text-indigo-500" />,
      'intercom': <Database className="w-5 h-5 text-blue-400" />,
      'google-drive': <Cloud className="w-5 h-5 text-yellow-500" />,
      'asana': <Database className="w-5 h-5 text-pink-500" />,
      'zendesk': <Database className="w-5 h-5 text-green-600" />,
      'greenhouse': <Database className="w-5 h-5 text-green-500" />,
      'gong': <Database className="w-5 h-5 text-purple-600" />,
    };
    return iconMap[id] || <Database className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Atlas Connectors</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Access 13+ data sources via MCP integration
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showCredentials ? "default" : "outline"}
            onClick={() => setShowCredentials(!showCredentials)}
          >
            <Key className="w-4 h-4 mr-2" />
            API Keys
          </Button>
          <Button
            variant={showN8N ? "default" : "outline"}
            onClick={() => setShowN8N(!showN8N)}
          >
            <Zap className="w-4 h-4 mr-2" />
            N8N Workflows
          </Button>
        </div>
      </div>

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">MCP Status</p>
                <div className="flex items-center gap-2 mt-1">
                  {health?.status === 'healthy' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="text-lg font-semibold text-[hsl(var(--foreground))]">
                    {health?.status || 'Unknown'}
                  </span>
                </div>
              </div>
              <Database className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Connectors Available</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {health?.connectors_count || connectors.length}
                </p>
              </div>
              <Cloud className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">N8N Status</p>
                <div className="flex items-center gap-2 mt-1">
                  {n8nHealth?.n8n_connectivity === 'connected' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="text-lg font-semibold text-[hsl(var(--foreground))]">
                    {n8nHealth?.workflow_count || 0} workflows
                  </span>
                </div>
              </div>
              <Server className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* API Keys Configuration Section */}
      {showCredentials && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">
                <Key className="w-5 h-5 inline mr-2" />
                API Keys Configuration
              </h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                Configure credentials for each connector
              </p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {connectors.map((connector) => {
                const status = credentials[connector.id];
                const isEditing = editingCredential === connector.id;

                return (
                  <div
                    key={connector.id}
                    className="p-3 border border-[hsl(var(--border))] rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getConnectorIcon(connector.id)}
                        <span className="font-medium text-[hsl(var(--foreground))] capitalize">
                          {connector.id.replace(/-/g, ' ')}
                        </span>
                      </div>
                      {status?.configured ? (
                        <span className="px-2 py-0.5 text-xs rounded bg-green-500/10 text-green-600">
                          Configured
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 text-xs rounded bg-red-500/10 text-red-600">
                          Not Set
                        </span>
                      )}
                    </div>

                    {isEditing ? (
                      <div className="mt-2 space-y-2">
                        <div className="relative">
                          <input
                            type={showApiKey ? 'text' : 'password'}
                            placeholder={`Enter ${connector.id} API key`}
                            value={apiKeyInput}
                            onChange={(e) => setApiKeyInput(e.target.value)}
                            className="w-full px-3 py-2 pr-10 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-sm"
                          />
                          <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-[hsl(var(--muted-foreground))]"
                          >
                            {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleSaveCredential(connector.id)}
                            disabled={credentialMutation.isPending}
                          >
                            <Save className="w-3 h-3 mr-1" />
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setEditingCredential(null);
                              setApiKeyInput('');
                            }}
                          >
                            <X className="w-3 h-3 mr-1" />
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-2 flex items-center justify-between">
                        <span className="text-xs text-[hsl(var(--muted-foreground))] font-mono">
                          {status?.masked || 'not_set'}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingCredential(connector.id);
                            setApiKeyInput('');
                            setShowApiKey(false);
                          }}
                        >
                          <Settings className="w-3 h-3 mr-1" />
                          Configure
                        </Button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* N8N Workflows Section (collapsible) */}
      {showN8N && (
        <Card>
          <CardContent className="p-4">
            <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-4">N8N Workflows</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {n8nWorkflows.slice(0, 12).map((workflow) => (
                <div
                  key={workflow.id}
                  className="p-3 border border-[hsl(var(--border))] rounded-lg hover:bg-[hsl(var(--secondary))] transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                      {workflow.name}
                    </span>
                    <span className={`px-2 py-0.5 text-xs rounded ${
                      workflow.active
                        ? 'bg-green-500/10 text-green-600'
                        : 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]'
                    }`}>
                      {workflow.active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
            {n8nWorkflows.length > 12 && (
              <p className="text-sm text-[hsl(var(--muted-foreground))] mt-3">
                +{n8nWorkflows.length - 12} more workflows
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Main Content - Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Connector List */}
        <div className="lg:col-span-1">
          <Card>
            <CardContent className="p-0">
              <div className="p-4 border-b border-[hsl(var(--border))]">
                <h3 className="font-medium text-[hsl(var(--foreground))]">Data Sources</h3>
              </div>
              {loadingConnectors ? (
                <div className="p-4 text-center text-[hsl(var(--muted-foreground))]">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                  Loading connectors...
                </div>
              ) : (
                <div className="divide-y divide-[hsl(var(--border))]">
                  {connectors.map((connector) => (
                    <button
                      key={connector.id}
                      onClick={() => {
                        setSelectedConnector(connector.id);
                      }}
                      className={`w-full p-3 flex items-center justify-between text-left hover:bg-[hsl(var(--secondary))] transition-colors ${
                        selectedConnector === connector.id ? 'bg-[hsl(var(--secondary))]' : ''
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {getConnectorIcon(connector.id)}
                        <div>
                          <p className="font-medium text-[hsl(var(--foreground))] capitalize">
                            {connector.id.replace(/-/g, ' ')}
                          </p>
                          <p className="text-xs text-[hsl(var(--muted-foreground))] line-clamp-1">
                            {connector.description}
                          </p>
                        </div>
                      </div>
                      <ChevronRight className={`w-4 h-4 text-[hsl(var(--muted-foreground))] transition-transform ${
                        selectedConnector === connector.id ? 'rotate-90' : ''
                      }`} />
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Connector Details & Actions */}
        <div className="lg:col-span-2">
          {selectedConnector ? (
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    {getConnectorIcon(selectedConnector)}
                    <div>
                      <h3 className="text-lg font-medium text-[hsl(var(--foreground))] capitalize">
                        {selectedConnector.replace(/-/g, ' ')}
                      </h3>
                      <p className="text-sm text-[hsl(var(--muted-foreground))]">
                        {connectors.find(c => c.id === selectedConnector)?.description}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Entities & Actions */}
                <div className="border-t border-[hsl(var(--border))] pt-4">
                  <h4 className="text-sm font-medium text-[hsl(var(--foreground))] mb-3">
                    Available Operations
                  </h4>
                  {loadingEntities ? (
                    <div className="text-center py-4">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto text-[hsl(var(--muted-foreground))]" />
                    </div>
                  ) : entities.length > 0 ? (
                    <div className="space-y-3">
                      {entities.map((entity) => (
                        <div
                          key={entity.name}
                          className="p-3 border border-[hsl(var(--border))] rounded-lg"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-[hsl(var(--foreground))] capitalize">
                              {entity.name.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {entity.actions.map((action) => (
                              <Button
                                key={action}
                                size="sm"
                                variant="outline"
                                onClick={() => handleExecute(entity.name, action)}
                                disabled={executeMutation.isPending}
                              >
                                <Play className="w-3 h-3 mr-1" />
                                {action}
                              </Button>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Database className="w-8 h-8 mx-auto text-[hsl(var(--muted-foreground))] mb-2" />
                      <p className="text-[hsl(var(--muted-foreground))]">
                        Configure this connector to see available operations
                      </p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))] mt-2">
                        Click "API Keys" above to add credentials
                      </p>
                    </div>
                  )}
                </div>

                {/* Execution Result */}
                {executeMutation.data && (
                  <div className="mt-4 p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                    <p className="text-sm font-medium text-green-600 mb-1">Execution Result</p>
                    <pre className="text-xs text-[hsl(var(--foreground))] overflow-auto max-h-40">
                      {JSON.stringify(executeMutation.data, null, 2)}
                    </pre>
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="p-8 text-center">
                <Database className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
                <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-2">
                  Select a Connector
                </h3>
                <p className="text-[hsl(var(--muted-foreground))]">
                  Choose a data source from the list to view available operations and execute queries
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
