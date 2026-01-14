import { useState } from 'react';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Search,
  Database,
  ShoppingCart,
  MessageSquare,
  BarChart3,
  Cloud,
  Code,
  Users,
  DollarSign,
  Briefcase,
  FileText,
  Globe,
  Zap,
  CheckCircle,
  ArrowRight,
  Sparkles,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import ConnectorConfigWizard from '@/components/ConnectorConfigWizard';
import toast from 'react-hot-toast';

interface Connector {
  name: string;
  display_name: string;
  category: string;
  description?: string;
  icon?: string;
  is_connected?: boolean;
  is_popular?: boolean;
}

const CATEGORY_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  'Database': Database,
  'CRM': Users,
  'Marketing': BarChart3,
  'E-commerce': ShoppingCart,
  'Analytics': BarChart3,
  'Communication': MessageSquare,
  'Storage': Cloud,
  'Development': Code,
  'Finance': DollarSign,
  'HR': Briefcase,
  'Productivity': FileText,
  'default': Globe,
};

const CATEGORIES = [
  'All',
  'Database',
  'CRM',
  'Marketing',
  'E-commerce',
  'Analytics',
  'Communication',
  'Storage',
  'Development',
  'Finance',
  'HR',
  'Productivity',
];

export default function SourceCatalog() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [configWizardConnector, setConfigWizardConnector] = useState<Connector | null>(null);

  // Check platform health/mock mode status
  const { data: platformHealth } = useQuery({
    queryKey: ['platform-health'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/health');
        return response.data;
      } catch {
        return { pyairbyte_status: 'unknown' };
      }
    },
    refetchInterval: 30000, // Check every 30 seconds
  });

  const isMockMode = platformHealth?.mock_mode ?? platformHealth?.pyairbyte_status === 'degraded';
  const canDisableMock = platformHealth?.can_disable_mock ?? false;
  const isMockForced = platformHealth?.mock_mode_forced ?? false;

  // Mutation to toggle mock mode
  const toggleMockMutation = useMutation({
    mutationFn: async (enabled: boolean) => {
      const response = await api.post(`/atlas-intelligence/pyairbyte/mock-mode?enabled=${enabled}`);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['platform-health'] });
      queryClient.invalidateQueries({ queryKey: ['pyairbyte-connectors'] });
      toast.success(data.message);
    },
    onError: () => {
      toast.error('Failed to toggle demo mode');
    },
  });

  // Fetch PyAirbyte connectors
  const { data: connectors, isLoading } = useQuery({
    queryKey: ['pyairbyte-connectors'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/pyairbyte/connectors');
        // Map API response to frontend interface
        // API returns: { id, name (display), category, status }
        // Frontend expects: { name (id), display_name, category }
        return response.data.map((c: any) => ({
          name: c.id || c.name,
          display_name: c.name || c.display_name || c.id,
          category: capitalizeCategory(c.category),
          description: c.description || `Connect to ${c.name || c.id}`,
          is_popular: c.is_popular || isPopularConnector(c.id || c.name),
        })) as Connector[];
      } catch {
        // Return mock data if API not available
        return getMockConnectors();
      }
    },
  });

  // Helper to capitalize category names
  const capitalizeCategory = (cat: string) => {
    if (!cat) return 'Other';
    const mapping: Record<string, string> = {
      'database': 'Database',
      'crm': 'CRM',
      'marketing': 'Marketing',
      'ecommerce': 'E-commerce',
      'analytics': 'Analytics',
      'project': 'Development',
      'communication': 'Communication',
      'storage': 'Storage',
      'finance': 'Finance',
      'hr': 'HR',
      'productivity': 'Productivity',
    };
    return mapping[cat.toLowerCase()] || cat.charAt(0).toUpperCase() + cat.slice(1);
  };

  // Popular connectors list
  const isPopularConnector = (id: string) => {
    const popular = ['source-postgres', 'source-mysql', 'source-salesforce', 'source-stripe',
                     'source-hubspot', 'source-google-analytics', 'source-shopify', 'source-slack'];
    return popular.includes(id);
  };

  // Fetch connected sources
  const { data: connectedSources } = useQuery({
    queryKey: ['connected-sources'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/state/sources');
        return response.data?.map((s: any) => s.source_name) || [];
      } catch {
        return [];
      }
    },
  });

  const filteredConnectors = connectors?.filter((connector) => {
    const matchesSearch =
      searchQuery === '' ||
      connector.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      connector.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory =
      selectedCategory === 'All' || connector.category === selectedCategory;

    return matchesSearch && matchesCategory;
  }) || [];

  const popularConnectors = filteredConnectors.filter((c) => c.is_popular);
  const regularConnectors = filteredConnectors.filter((c) => !c.is_popular);

  const handleConnect = (connector: Connector) => {
    // Open the configuration wizard modal
    setConfigWizardConnector(connector);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Demo Mode Banner with Toggle */}
      <div className={`flex items-start gap-3 p-4 rounded-lg border ${
        isMockMode
          ? 'bg-amber-500/10 border-amber-500/20'
          : 'bg-green-500/10 border-green-500/20'
      }`}>
        {isMockMode ? (
          <AlertTriangle className="h-5 w-5 text-amber-500 shrink-0 mt-0.5" />
        ) : (
          <CheckCircle className="h-5 w-5 text-green-500 shrink-0 mt-0.5" />
        )}
        <div className="flex-1">
          <h3 className={`text-sm font-medium ${
            isMockMode
              ? 'text-amber-600 dark:text-amber-400'
              : 'text-green-600 dark:text-green-400'
          }`}>
            {isMockMode ? 'Demo Mode' : 'Live Mode'}
          </h3>
          <p className={`mt-1 text-sm ${
            isMockMode
              ? 'text-amber-600/80 dark:text-amber-400/80'
              : 'text-green-600/80 dark:text-green-400/80'
          }`}>
            {isMockMode
              ? (canDisableMock
                  ? 'Using sample data. Toggle off to use real PyAirbyte connectors.'
                  : 'PyAirbyte not installed. Install in Python 3.11/3.12 to enable live mode.')
              : 'Connected to real PyAirbyte connectors.'}
          </p>
        </div>

        {/* Toggle Switch */}
        <div className="flex items-center gap-3 shrink-0">
          <span className="text-xs text-[hsl(var(--muted-foreground))]">
            {isMockMode ? 'Demo' : 'Live'}
          </span>
          <button
            onClick={() => toggleMockMutation.mutate(!isMockMode)}
            disabled={toggleMockMutation.isPending || (!canDisableMock && isMockMode && !isMockForced)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              isMockMode
                ? 'bg-amber-500 focus:ring-amber-500'
                : 'bg-green-500 focus:ring-green-500'
            } ${(!canDisableMock && isMockMode && !isMockForced) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
            title={!canDisableMock && isMockMode ? 'PyAirbyte not installed - cannot enable live mode' : ''}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                isMockMode ? 'translate-x-1' : 'translate-x-6'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Source Catalog</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Browse and connect to 300+ data sources
          </p>
        </div>
        <Link to="/connections">
          <Button variant="outline" size="sm">
            View Connections
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Link>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
          <input
            type="text"
            placeholder="Search connectors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[hsl(var(--input))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          />
        </div>

        {/* Category Filter */}
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.slice(0, 6).map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                selectedCategory === category
                  ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                  : 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
              }`}
            >
              {category}
            </button>
          ))}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-1.5 text-sm font-medium rounded-lg bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] border-none focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          >
            {CATEGORIES.slice(6).map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-6 text-sm text-[hsl(var(--muted-foreground))]">
        <span>{filteredConnectors.length} connectors</span>
        <span>{connectedSources?.length || 0} connected</span>
        {isMockMode && (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Info className="h-3 w-3" />
            Demo Mode
          </span>
        )}
      </div>

      {/* Popular Connectors */}
      {popularConnectors.length > 0 && selectedCategory === 'All' && searchQuery === '' && (
        <div>
          <h2 className="text-sm font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider mb-4 flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Popular
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {popularConnectors.slice(0, 8).map((connector) => (
              <ConnectorCard
                key={connector.name}
                connector={connector}
                isConnected={connectedSources?.includes(connector.name)}
                onConnect={() => handleConnect(connector)}
              />
            ))}
          </div>
        </div>
      )}

      {/* All Connectors */}
      <div>
        {popularConnectors.length > 0 && selectedCategory === 'All' && searchQuery === '' && (
          <h2 className="text-sm font-semibold text-[hsl(var(--muted-foreground))] uppercase tracking-wider mb-4">
            All Connectors
          </h2>
        )}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {(popularConnectors.length > 0 && selectedCategory === 'All' && searchQuery === ''
            ? regularConnectors
            : filteredConnectors
          ).map((connector) => (
            <ConnectorCard
              key={connector.name}
              connector={connector}
              isConnected={connectedSources?.includes(connector.name)}
              onConnect={() => handleConnect(connector)}
            />
          ))}
        </div>
      </div>

      {filteredConnectors.length === 0 && (
        <div className="py-12 text-center">
          <Search className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
          <h3 className="mt-4 text-lg font-medium text-[hsl(var(--foreground))]">No connectors found</h3>
          <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}

      {/* Connector Configuration Wizard Modal */}
      {configWizardConnector && (
        <ConnectorConfigWizard
          connector={{
            id: configWizardConnector.name,  // internal ID like "source-postgres"
            name: configWizardConnector.display_name,  // display name like "PostgreSQL"
            category: configWizardConnector.category,
          }}
          onClose={() => setConfigWizardConnector(null)}
          onSuccess={() => {
            toast.success(`${configWizardConnector.display_name} connected successfully!`);
            setConfigWizardConnector(null);
            queryClient.invalidateQueries({ queryKey: ['pyairbyte-connectors'] });
            queryClient.invalidateQueries({ queryKey: ['connected-sources'] });
          }}
        />
      )}
    </div>
  );
}

interface ConnectorCardProps {
  connector: Connector;
  isConnected?: boolean;
  onConnect: () => void;
}

function ConnectorCard({ connector, isConnected, onConnect }: ConnectorCardProps) {
  const Icon = CATEGORY_ICONS[connector.category] || CATEGORY_ICONS.default;

  return (
    <Card className="group hover:border-[hsl(var(--foreground)/0.2)] transition-all">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[hsl(var(--secondary))]">
              <Icon className="h-5 w-5 text-[hsl(var(--foreground))]" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                {connector.display_name}
              </h3>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">{connector.category}</p>
            </div>
          </div>
          {isConnected && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-green-500/10">
              <CheckCircle className="h-3 w-3 text-green-500" />
            </span>
          )}
        </div>

        {connector.description && (
          <p className="mt-3 text-xs text-[hsl(var(--muted-foreground))] line-clamp-2">
            {connector.description}
          </p>
        )}

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-[hsl(var(--muted-foreground))]">
            {isConnected ? 'Connected' : 'Available'}
          </span>
          <Button
            size="sm"
            variant={isConnected ? 'outline' : 'default'}
            onClick={onConnect}
            className="h-7 text-xs"
          >
            {isConnected ? 'Configure' : 'Connect'}
            <Zap className="ml-1 h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function getMockConnectors(): Connector[] {
  return [
    // Popular
    { name: 'source-postgres', display_name: 'PostgreSQL', category: 'Database', description: 'Open source relational database', is_popular: true },
    { name: 'source-mysql', display_name: 'MySQL', category: 'Database', description: 'Popular open source database', is_popular: true },
    { name: 'source-salesforce', display_name: 'Salesforce', category: 'CRM', description: 'Customer relationship management platform', is_popular: true },
    { name: 'source-stripe', display_name: 'Stripe', category: 'Finance', description: 'Payment processing platform', is_popular: true },
    { name: 'source-hubspot', display_name: 'HubSpot', category: 'Marketing', description: 'Inbound marketing and sales platform', is_popular: true },
    { name: 'source-google-analytics', display_name: 'Google Analytics', category: 'Analytics', description: 'Web analytics service', is_popular: true },
    { name: 'source-shopify', display_name: 'Shopify', category: 'E-commerce', description: 'E-commerce platform', is_popular: true },
    { name: 'source-slack', display_name: 'Slack', category: 'Communication', description: 'Team communication platform', is_popular: true },
    // Database
    { name: 'source-mongodb', display_name: 'MongoDB', category: 'Database', description: 'NoSQL document database' },
    { name: 'source-mssql', display_name: 'Microsoft SQL Server', category: 'Database', description: 'Enterprise relational database' },
    { name: 'source-oracle', display_name: 'Oracle', category: 'Database', description: 'Enterprise database system' },
    { name: 'source-snowflake', display_name: 'Snowflake', category: 'Database', description: 'Cloud data warehouse' },
    { name: 'source-bigquery', display_name: 'BigQuery', category: 'Database', description: 'Google cloud data warehouse' },
    { name: 'source-redshift', display_name: 'Amazon Redshift', category: 'Database', description: 'AWS data warehouse' },
    { name: 'source-clickhouse', display_name: 'ClickHouse', category: 'Database', description: 'Column-oriented OLAP database' },
    // CRM
    { name: 'source-zendesk', display_name: 'Zendesk', category: 'CRM', description: 'Customer service platform' },
    { name: 'source-intercom', display_name: 'Intercom', category: 'CRM', description: 'Customer messaging platform' },
    { name: 'source-pipedrive', display_name: 'Pipedrive', category: 'CRM', description: 'Sales CRM' },
    { name: 'source-freshdesk', display_name: 'Freshdesk', category: 'CRM', description: 'Customer support software' },
    // Marketing
    { name: 'source-facebook-marketing', display_name: 'Facebook Ads', category: 'Marketing', description: 'Facebook advertising platform' },
    { name: 'source-google-ads', display_name: 'Google Ads', category: 'Marketing', description: 'Google advertising platform' },
    { name: 'source-linkedin-ads', display_name: 'LinkedIn Ads', category: 'Marketing', description: 'LinkedIn advertising' },
    { name: 'source-mailchimp', display_name: 'Mailchimp', category: 'Marketing', description: 'Email marketing platform' },
    { name: 'source-sendgrid', display_name: 'SendGrid', category: 'Marketing', description: 'Email delivery platform' },
    // E-commerce
    { name: 'source-woocommerce', display_name: 'WooCommerce', category: 'E-commerce', description: 'WordPress e-commerce' },
    { name: 'source-amazon-seller', display_name: 'Amazon Seller', category: 'E-commerce', description: 'Amazon marketplace' },
    { name: 'source-ebay', display_name: 'eBay', category: 'E-commerce', description: 'Online marketplace' },
    // Analytics
    { name: 'source-mixpanel', display_name: 'Mixpanel', category: 'Analytics', description: 'Product analytics' },
    { name: 'source-amplitude', display_name: 'Amplitude', category: 'Analytics', description: 'Product analytics platform' },
    { name: 'source-segment', display_name: 'Segment', category: 'Analytics', description: 'Customer data platform' },
    // Communication
    { name: 'source-twilio', display_name: 'Twilio', category: 'Communication', description: 'Cloud communications' },
    { name: 'source-discord', display_name: 'Discord', category: 'Communication', description: 'Community platform' },
    // Storage
    { name: 'source-s3', display_name: 'Amazon S3', category: 'Storage', description: 'AWS object storage' },
    { name: 'source-gcs', display_name: 'Google Cloud Storage', category: 'Storage', description: 'Google cloud storage' },
    { name: 'source-azure-blob', display_name: 'Azure Blob Storage', category: 'Storage', description: 'Microsoft cloud storage' },
    // Development
    { name: 'source-github', display_name: 'GitHub', category: 'Development', description: 'Code hosting platform' },
    { name: 'source-gitlab', display_name: 'GitLab', category: 'Development', description: 'DevOps platform' },
    { name: 'source-jira', display_name: 'Jira', category: 'Development', description: 'Project management' },
    { name: 'source-linear', display_name: 'Linear', category: 'Development', description: 'Issue tracking' },
    // Finance
    { name: 'source-quickbooks', display_name: 'QuickBooks', category: 'Finance', description: 'Accounting software' },
    { name: 'source-xero', display_name: 'Xero', category: 'Finance', description: 'Accounting platform' },
    { name: 'source-plaid', display_name: 'Plaid', category: 'Finance', description: 'Financial data platform' },
    // HR
    { name: 'source-workday', display_name: 'Workday', category: 'HR', description: 'HR management' },
    { name: 'source-bamboohr', display_name: 'BambooHR', category: 'HR', description: 'HR software' },
    { name: 'source-greenhouse', display_name: 'Greenhouse', category: 'HR', description: 'Recruiting software' },
    // Productivity
    { name: 'source-notion', display_name: 'Notion', category: 'Productivity', description: 'All-in-one workspace' },
    { name: 'source-airtable', display_name: 'Airtable', category: 'Productivity', description: 'Spreadsheet database' },
    { name: 'source-asana', display_name: 'Asana', category: 'Productivity', description: 'Work management' },
    { name: 'source-google-sheets', display_name: 'Google Sheets', category: 'Productivity', description: 'Spreadsheet application' },
  ];
}
