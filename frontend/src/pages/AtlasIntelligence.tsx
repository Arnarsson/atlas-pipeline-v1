import { useState, ReactNode } from 'react';
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
  X,
  Search,
  Layers,
  Package,
  FileText,
  Activity
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/api/client';
import ConnectorConfigWizard from '@/components/ConnectorConfigWizard';
import SchemaBrowser from '@/components/SchemaBrowser';
import SyncStatusPanel from '@/components/SyncStatusPanel';

// Types for connectors
interface AtlasConnector {
  id: string;
  description: string;
  type: string;
  path: string | null;
  connector_name: string | null;
  category?: string;
}

interface AtlasEntity {
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

interface SourceConnector {
  id: string;
  name: string;
  category: string;
  status: string;
  pyairbyte_available: boolean;
}

interface SourceCategory {
  category: string;
  count: number;
  label: string;
}

// API functions - MCP
const getAtlasConnectors = async (): Promise<AtlasConnector[]> => {
  const response = await api.get('/atlas-intelligence/connectors');
  return response.data;
};

const getAtlasHealth = async () => {
  const response = await api.get('/atlas-intelligence/health');
  return response.data;
};

const getConnectorEntities = async (connectorId: string): Promise<AtlasEntity[]> => {
  const response = await api.get(`/atlas-intelligence/connectors/${connectorId}/entities`);
  return response.data;
};

const executeAtlasOperation = async (request: ExecuteRequest) => {
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

// API functions - Atlas Sources
const getSourcesHealth = async () => {
  const response = await api.get('/atlas-intelligence/pyairbyte/health');
  return response.data;
};

const getSourceConnectors = async (category?: string, search?: string): Promise<SourceConnector[]> => {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (search) params.append('search', search);
  const response = await api.get(`/atlas-intelligence/pyairbyte/connectors?${params.toString()}`);
  return response.data;
};

const getSourceCategories = async (): Promise<SourceCategory[]> => {
  const response = await api.get('/atlas-intelligence/pyairbyte/categories');
  return response.data;
};

const getPlatformStats = async () => {
  const response = await api.get('/atlas-intelligence/stats');
  return response.data;
};

type TabType = 'mcp' | 'sources' | 'n8n';

export default function AtlasIntelligence() {
  const [activeTab, setActiveTab] = useState<TabType>('mcp');
  const [selectedConnector, setSelectedConnector] = useState<string | null>(null);
  const [showCredentials, setShowCredentials] = useState(false);
  const [editingCredential, setEditingCredential] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [sourceSearch, setSourceSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [configWizardConnector, setConfigWizardConnector] = useState<SourceConnector | null>(null);
  const [schemaBrowserConnector, setSchemaBrowserConnector] = useState<SourceConnector | null>(null);
  const [showSyncStatus, setShowSyncStatus] = useState(false);
  const queryClient = useQueryClient();

  // MCP Queries
  const { data: connectors = [], isLoading: loadingConnectors } = useQuery({
    queryKey: ['atlas-connectors'],
    queryFn: getAtlasConnectors,
    refetchInterval: 60000,
  });

  const { data: health } = useQuery({
    queryKey: ['atlas-health'],
    queryFn: getAtlasHealth,
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
    enabled: activeTab === 'n8n',
  });

  const { data: entities = [], isLoading: loadingEntities } = useQuery({
    queryKey: ['connector-entities', selectedConnector],
    queryFn: () => selectedConnector ? getConnectorEntities(selectedConnector) : Promise.resolve([]),
    enabled: !!selectedConnector && activeTab === 'mcp',
  });

  const { data: credentials = {} } = useQuery({
    queryKey: ['credentials'],
    queryFn: getCredentials,
    enabled: showCredentials,
  });

  // Atlas Sources Queries
  const { data: sourcesHealth } = useQuery({
    queryKey: ['sources-health'],
    queryFn: getSourcesHealth,
    enabled: activeTab === 'sources',
    refetchInterval: 30000,
  });

  const { data: sourceConnectors = [], isLoading: loadingSources } = useQuery({
    queryKey: ['source-connectors', selectedCategory, sourceSearch],
    queryFn: () => getSourceConnectors(selectedCategory || undefined, sourceSearch || undefined),
    enabled: activeTab === 'sources',
  });

  const { data: sourceCategories = [] } = useQuery({
    queryKey: ['source-categories'],
    queryFn: getSourceCategories,
    enabled: activeTab === 'sources',
  });

  const { data: stats } = useQuery({
    queryKey: ['platform-stats'],
    queryFn: getPlatformStats,
    refetchInterval: 60000,
  });

  // Mutations
  const executeMutation = useMutation({
    mutationFn: executeAtlasOperation,
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
    const iconMap: Record<string, ReactNode> = {
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

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, ReactNode> = {
      database: <Database className="w-4 h-4" />,
      crm: <Cloud className="w-4 h-4" />,
      marketing: <Zap className="w-4 h-4" />,
      ecommerce: <Package className="w-4 h-4" />,
      analytics: <Layers className="w-4 h-4" />,
      project: <Server className="w-4 h-4" />,
    };
    return icons[category] || <Database className="w-4 h-4" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">AtlasIntelligence</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Unified connector platform - {stats?.total_available || '300+'}+ data sources
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={showSyncStatus ? "default" : "outline"}
            onClick={() => setShowSyncStatus(!showSyncStatus)}
          >
            <Activity className="w-4 h-4 mr-2" />
            Sync Status
          </Button>
          <Button
            variant={showCredentials ? "default" : "outline"}
            onClick={() => setShowCredentials(!showCredentials)}
          >
            <Key className="w-4 h-4 mr-2" />
            API Keys
          </Button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b border-[hsl(var(--border))] pb-2">
        <Button
          variant={activeTab === 'mcp' ? 'default' : 'ghost'}
          onClick={() => { setActiveTab('mcp'); setSelectedConnector(null); }}
          className="flex items-center gap-2"
        >
          <Zap className="w-4 h-4" />
          MCP Connectors
          <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--secondary))]">
            {connectors.length}
          </span>
        </Button>
        <Button
          variant={activeTab === 'sources' ? 'default' : 'ghost'}
          onClick={() => { setActiveTab('sources'); setSelectedConnector(null); }}
          className="flex items-center gap-2"
        >
          <Package className="w-4 h-4" />
          Atlas Sources
          <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--secondary))]">
            {stats?.pyairbyte_connectors?.total || '70+'}
          </span>
        </Button>
        <Button
          variant={activeTab === 'n8n' ? 'default' : 'ghost'}
          onClick={() => setActiveTab('n8n')}
          className="flex items-center gap-2"
        >
          <Server className="w-4 h-4" />
          N8N Workflows
          <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--secondary))]">
            {n8nHealth?.workflow_count || 0}
          </span>
        </Button>
      </div>

      {/* Health Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Platform Status</p>
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
                <p className="text-sm text-[hsl(var(--muted-foreground))]">MCP Connectors</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {connectors.length}
                </p>
              </div>
              <Zap className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Atlas Sources</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                  {stats?.pyairbyte_connectors?.total || '70+'}
                </p>
              </div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">N8N Workflows</p>
                <div className="flex items-center gap-2 mt-1">
                  {n8nHealth?.n8n_connectivity === 'connected' ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-500" />
                  )}
                  <span className="text-lg font-semibold text-[hsl(var(--foreground))]">
                    {n8nHealth?.workflow_count || 0}
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

      {/* Sync Status Panel */}
      {showSyncStatus && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">
                <Activity className="w-5 h-5 inline mr-2" />
                Sync Status & Job Management
              </h3>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setShowSyncStatus(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
            <SyncStatusPanel />
          </CardContent>
        </Card>
      )}

      {/* MCP Tab Content */}
      {activeTab === 'mcp' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Connector List */}
          <div className="lg:col-span-1">
            <Card>
              <CardContent className="p-0">
                <div className="p-4 border-b border-[hsl(var(--border))]">
                  <h3 className="font-medium text-[hsl(var(--foreground))]">MCP Data Sources</h3>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">Lightweight, fast connectors</p>
                </div>
                {loadingConnectors ? (
                  <div className="p-4 text-center text-[hsl(var(--muted-foreground))]">
                    <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2" />
                    Loading connectors...
                  </div>
                ) : (
                  <div className="divide-y divide-[hsl(var(--border))] max-h-[500px] overflow-y-auto">
                    {connectors.map((connector) => (
                      <button
                        key={connector.id}
                        onClick={() => setSelectedConnector(connector.id)}
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
                  <Zap className="w-12 h-12 mx-auto text-orange-500 mb-4" />
                  <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-2">
                    Select an MCP Connector
                  </h3>
                  <p className="text-[hsl(var(--muted-foreground))]">
                    Choose a data source from the list to view available operations
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Atlas Sources Tab Content */}
      {activeTab === 'sources' && (
        <div className="space-y-6">
          {/* Atlas Sources Status Banner */}
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Package className="w-8 h-8 text-blue-500" />
                  <div>
                    <h3 className="font-medium text-[hsl(var(--foreground))]">AtlasIntelligence Sources</h3>
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">
                      {sourcesHealth?.message || 'Access 300+ data sources through Atlas connector protocol'}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {sourcesHealth?.pyairbyte_installed ? (
                    <span className="px-3 py-1 text-sm rounded-full bg-green-500/10 text-green-600">
                      <CheckCircle2 className="w-4 h-4 inline mr-1" />
                      Ready
                    </span>
                  ) : (
                    <span className="px-3 py-1 text-sm rounded-full bg-yellow-500/10 text-yellow-600">
                      Install: pip install pyairbyte
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Search and Filter */}
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--muted-foreground))]" />
              <input
                type="text"
                placeholder="Search connectors..."
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            </div>
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              className="px-4 py-2 border border-[hsl(var(--border))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
            >
              <option value="">All Categories</option>
              {sourceCategories.map((cat) => (
                <option key={cat.category} value={cat.category}>
                  {cat.label} ({cat.count})
                </option>
              ))}
            </select>
          </div>

          {/* Category Pills */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                !selectedCategory
                  ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                  : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--border))]'
              }`}
            >
              All
            </button>
            {sourceCategories.slice(0, 8).map((cat) => (
              <button
                key={cat.category}
                onClick={() => setSelectedCategory(cat.category)}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors flex items-center gap-1.5 ${
                  selectedCategory === cat.category
                    ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                    : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--border))]'
                }`}
              >
                {getCategoryIcon(cat.category)}
                {cat.label}
                <span className="text-xs opacity-70">({cat.count})</span>
              </button>
            ))}
          </div>

          {/* Connector Grid */}
          {loadingSources ? (
            <div className="text-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
              <p className="text-[hsl(var(--muted-foreground))]">Loading connectors...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {sourceConnectors.map((connector) => (
                <Card key={connector.id} className="hover:border-[hsl(var(--foreground))] transition-colors">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        {getCategoryIcon(connector.category)}
                        <span className="font-medium text-[hsl(var(--foreground))]">
                          {connector.name}
                        </span>
                      </div>
                      <span className={`px-2 py-0.5 text-xs rounded ${
                        connector.status === 'installed'
                          ? 'bg-green-500/10 text-green-600'
                          : 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]'
                      }`}>
                        {connector.status}
                      </span>
                    </div>
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mb-3">
                      {connector.id}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-xs px-2 py-0.5 rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
                        {connector.category}
                      </span>
                      <div className="flex gap-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setSchemaBrowserConnector(connector)}
                          title="View Schema"
                        >
                          <FileText className="w-4 h-4" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setConfigWizardConnector(connector)}
                        >
                          <Settings className="w-3 h-3 mr-1" />
                          Configure
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {sourceConnectors.length === 0 && !loadingSources && (
            <div className="text-center py-12">
              <Package className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-2">
                No connectors found
              </h3>
              <p className="text-[hsl(var(--muted-foreground))]">
                Try a different search or category filter
              </p>
            </div>
          )}
        </div>
      )}

      {/* N8N Tab Content */}
      {activeTab === 'n8n' && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">
                <Server className="w-5 h-5 inline mr-2" />
                N8N Workflow Automation
              </h3>
              <div className="flex items-center gap-2">
                {n8nHealth?.n8n_connectivity === 'connected' ? (
                  <span className="px-2 py-0.5 text-xs rounded bg-green-500/10 text-green-600">
                    Connected
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-xs rounded bg-red-500/10 text-red-600">
                    Disconnected
                  </span>
                )}
              </div>
            </div>
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
            {n8nWorkflows.length === 0 && (
              <div className="text-center py-8">
                <Server className="w-8 h-8 mx-auto text-[hsl(var(--muted-foreground))] mb-2" />
                <p className="text-[hsl(var(--muted-foreground))]">
                  No workflows available. Connect to N8N to see workflows.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Connector Configuration Wizard Modal */}
      {configWizardConnector && (
        <ConnectorConfigWizard
          connector={configWizardConnector}
          onClose={() => setConfigWizardConnector(null)}
          onSuccess={(sourceId) => {
            toast.success(`Connector ${configWizardConnector.name} configured with ID: ${sourceId}`);
            queryClient.invalidateQueries({ queryKey: ['source-connectors'] });
          }}
        />
      )}

      {/* Schema Browser Modal */}
      {schemaBrowserConnector && (
        <SchemaBrowser
          sourceName={schemaBrowserConnector.id}
          sourceDisplayName={schemaBrowserConnector.name}
          onClose={() => setSchemaBrowserConnector(null)}
        />
      )}
    </div>
  );
}
