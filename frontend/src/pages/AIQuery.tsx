import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import toast from 'react-hot-toast';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Dataset {
  name: string;
  record_count: number;
  layer: string;
  last_updated: string;
}

interface AuditLog {
  log_id: string;
  timestamp: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  records_accessed: number;
}

interface QueryResult {
  data: Record<string, unknown>[];
  record_count: number;
  query_id: string;
}

interface SearchResult {
  results: Array<{
    content: string;
    similarity: number;
    metadata: Record<string, unknown>;
  }>;
  query_id: string;
}

export default function AIQuery() {
  const [activeTab, setActiveTab] = useState<'query' | 'search' | 'audit'>('query');
  const [apiKey, setApiKey] = useState('');
  const [selectedDataset, setSelectedDataset] = useState('');
  const [queryFilters, setQueryFilters] = useState('{}');
  const [queryLimit, setQueryLimit] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);

  // Fetch datasets
  const { data: datasetsData, isLoading: datasetsLoading } = useQuery({
    queryKey: ['ai-datasets', apiKey],
    queryFn: async () => {
      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      const res = await fetch(`${API_BASE}/ai/datasets`, { headers });
      if (!res.ok) throw new Error('Failed to fetch datasets');
      return res.json();
    },
    enabled: true,
  });

  // Fetch audit logs
  const { data: auditData, isLoading: auditLoading, refetch: refetchAudit } = useQuery({
    queryKey: ['ai-audit', apiKey],
    queryFn: async () => {
      const headers: Record<string, string> = {};
      if (apiKey) headers['X-API-Key'] = apiKey;

      const res = await fetch(`${API_BASE}/ai/audit?limit=50`, { headers });
      if (!res.ok) throw new Error('Failed to fetch audit logs');
      return res.json();
    },
    enabled: activeTab === 'audit',
  });

  // Query mutation
  const queryMutation = useMutation({
    mutationFn: async () => {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (apiKey) headers['X-API-Key'] = apiKey;

      let filters = {};
      try {
        filters = JSON.parse(queryFilters);
      } catch {
        throw new Error('Invalid JSON in filters');
      }

      const res = await fetch(`${API_BASE}/ai/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          dataset_name: selectedDataset,
          query_type: 'select',
          filters,
          limit: queryLimit,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Query failed');
      }
      return res.json();
    },
    onSuccess: (data) => {
      setQueryResult(data);
      toast.success(`Retrieved ${data.record_count} records`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  // Search mutation
  const searchMutation = useMutation({
    mutationFn: async () => {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };
      if (apiKey) headers['X-API-Key'] = apiKey;

      const res = await fetch(`${API_BASE}/ai/search`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          query: searchQuery,
          dataset_name: selectedDataset || undefined,
          limit: queryLimit,
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Search failed');
      }
      return res.json();
    },
    onSuccess: (data) => {
      setSearchResult(data);
      toast.success(`Found ${data.results?.length || 0} results`);
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  const datasets: Dataset[] = datasetsData?.datasets || [];
  const auditLogs: AuditLog[] = auditData?.logs || [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">AI Query & Audit</h1>
        <p className="mt-1 text-[hsl(var(--muted-foreground))]">
          Query data for AI agents and view audit logs
        </p>
      </div>

      {/* API Key Input */}
      <div className="mb-6 p-4 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--secondary))]">
        <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
          API Key (optional for public endpoints)
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="atlas_xxxxxxxxxx..."
          className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))]"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-[hsl(var(--border))]">
        {(['query', 'search', 'audit'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-t-md transition-colors ${
              activeTab === tab
                ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
            }`}
          >
            {tab === 'query' && 'Structured Query'}
            {tab === 'search' && 'Semantic Search'}
            {tab === 'audit' && 'Audit Logs'}
          </button>
        ))}
      </div>

      {/* Query Tab */}
      {activeTab === 'query' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Dataset Selection */}
            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Dataset
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              >
                <option value="">Select a dataset...</option>
                {datasets.map((ds) => (
                  <option key={ds.name} value={ds.name}>
                    {ds.name} ({ds.record_count} records)
                  </option>
                ))}
              </select>
            </div>

            {/* Filters */}
            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Filters (JSON)
              </label>
              <input
                type="text"
                value={queryFilters}
                onChange={(e) => setQueryFilters(e.target.value)}
                placeholder='{"column": "value"}'
                className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            </div>

            {/* Limit */}
            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Limit
              </label>
              <input
                type="number"
                value={queryLimit}
                onChange={(e) => setQueryLimit(parseInt(e.target.value) || 10)}
                min={1}
                max={1000}
                className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            </div>
          </div>

          <button
            onClick={() => queryMutation.mutate()}
            disabled={!selectedDataset || queryMutation.isPending}
            className="px-4 py-2 bg-[hsl(var(--foreground))] text-[hsl(var(--background))] rounded-md font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {queryMutation.isPending ? 'Querying...' : 'Execute Query'}
          </button>

          {/* Query Results */}
          {queryResult && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-3">
                Results ({queryResult.record_count} records)
              </h3>
              <div className="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
                <table className="w-full text-sm">
                  <thead className="bg-[hsl(var(--secondary))]">
                    <tr>
                      {queryResult.data[0] && Object.keys(queryResult.data[0]).map((key) => (
                        <th key={key} className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">
                          {key}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {queryResult.data.map((row, i) => (
                      <tr key={i} className="border-t border-[hsl(var(--border))]">
                        {Object.values(row).map((value, j) => (
                          <td key={j} className="px-4 py-3 text-[hsl(var(--muted-foreground))]">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search Query */}
            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Natural Language Query
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Find customers with high revenue..."
                className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              />
            </div>

            {/* Dataset Filter (Optional) */}
            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Dataset Filter (optional)
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
              >
                <option value="">All datasets</option>
                {datasets.map((ds) => (
                  <option key={ds.name} value={ds.name}>
                    {ds.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button
            onClick={() => searchMutation.mutate()}
            disabled={!searchQuery || searchMutation.isPending}
            className="px-4 py-2 bg-[hsl(var(--foreground))] text-[hsl(var(--background))] rounded-md font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {searchMutation.isPending ? 'Searching...' : 'Semantic Search'}
          </button>

          {/* Search Results */}
          {searchResult && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-3">
                Search Results ({searchResult.results?.length || 0} matches)
              </h3>
              <div className="space-y-3">
                {searchResult.results?.map((result, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--secondary))]"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-[hsl(var(--foreground))]">
                        Result #{i + 1}
                      </span>
                      <span className="px-2 py-1 text-xs rounded bg-green-500/10 text-green-600">
                        {(result.similarity * 100).toFixed(1)}% match
                      </span>
                    </div>
                    <p className="text-sm text-[hsl(var(--muted-foreground))]">{result.content}</p>
                    {result.metadata && Object.keys(result.metadata).length > 0 && (
                      <div className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                        Metadata: {JSON.stringify(result.metadata)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Audit Tab */}
      {activeTab === 'audit' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-[hsl(var(--foreground))]">
              Data Access Audit Log
            </h3>
            <button
              onClick={() => refetchAudit()}
              className="px-3 py-1.5 text-sm border border-[hsl(var(--border))] rounded-md hover:bg-[hsl(var(--secondary))]"
            >
              Refresh
            </button>
          </div>

          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            EU AI Act Article 12 compliant audit trail. All data access is logged for 5+ years.
          </p>

          {auditLoading ? (
            <div className="text-center py-8 text-[hsl(var(--muted-foreground))]">Loading audit logs...</div>
          ) : auditLogs.length === 0 ? (
            <div className="text-center py-8 text-[hsl(var(--muted-foreground))]">
              No audit logs found. Upload data to generate logs.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border border-[hsl(var(--border))]">
              <table className="w-full text-sm">
                <thead className="bg-[hsl(var(--secondary))]">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">Timestamp</th>
                    <th className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">User</th>
                    <th className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">Action</th>
                    <th className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">Resource</th>
                    <th className="px-4 py-3 text-left font-medium text-[hsl(var(--foreground))]">Records</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.log_id} className="border-t border-[hsl(var(--border))]">
                      <td className="px-4 py-3 text-[hsl(var(--muted-foreground))] font-mono text-xs">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-4 py-3 text-[hsl(var(--foreground))]">{log.user_id}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 text-xs rounded ${
                          log.action === 'query' ? 'bg-blue-500/10 text-blue-600' :
                          log.action === 'export' ? 'bg-purple-500/10 text-purple-600' :
                          log.action === 'pipeline_run' ? 'bg-green-500/10 text-green-600' :
                          'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]'
                        }`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[hsl(var(--muted-foreground))]">
                        {log.resource_type}: {log.resource_id}
                      </td>
                      <td className="px-4 py-3 text-[hsl(var(--foreground))]">{log.records_accessed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Dataset List */}
      <div className="mt-8 p-4 rounded-lg border border-[hsl(var(--border))]">
        <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-4">Available Datasets</h3>
        {datasetsLoading ? (
          <div className="text-center py-4 text-[hsl(var(--muted-foreground))]">Loading...</div>
        ) : datasets.length === 0 ? (
          <div className="text-center py-4 text-[hsl(var(--muted-foreground))]">
            No datasets found. Upload data via the Upload page.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map((ds) => (
              <div
                key={ds.name}
                className="p-4 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--secondary))]"
              >
                <h4 className="font-medium text-[hsl(var(--foreground))]">{ds.name}</h4>
                <div className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                  <p>{ds.record_count} records</p>
                  <p className="capitalize">{ds.layer} layer</p>
                  {ds.last_updated && (
                    <p className="text-xs mt-1">
                      Updated: {new Date(ds.last_updated).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
