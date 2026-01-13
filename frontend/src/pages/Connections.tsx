import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  MoreVertical,
  Play,
  Pause,
  Trash2,
  Settings,
  CheckCircle,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Database,
  Zap,
  Calendar,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import toast from 'react-hot-toast';

interface Connection {
  id: string;
  source_name: string;
  source_type: string;
  destination?: string;
  status: 'active' | 'paused' | 'error' | 'syncing';
  last_sync?: string;
  next_sync?: string;
  streams_count: number;
  records_synced: number;
  sync_mode: 'full_refresh' | 'incremental' | 'cdc';
  schedule?: string;
}

export default function Connections() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  // Fetch connections from state
  const { data: connections, isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/state/sources');
        return response.data?.map((source: any) => ({
          id: source.source_id,
          source_name: source.source_name,
          source_type: source.source_type || 'pyairbyte',
          status: source.is_active ? 'active' : 'paused',
          last_sync: source.last_sync_at,
          streams_count: source.streams?.length || 0,
          records_synced: source.total_records || 0,
          sync_mode: source.sync_mode || 'incremental',
        })) as Connection[];
      } catch {
        return getMockConnections();
      }
    },
  });

  // Trigger sync mutation
  const syncMutation = useMutation({
    mutationFn: async (connectionId: string) => {
      const response = await api.post(`/atlas-intelligence/sync/jobs`, {
        source_id: connectionId,
      });
      return response.data;
    },
    onSuccess: () => {
      toast.success('Sync started');
      queryClient.invalidateQueries({ queryKey: ['connections'] });
    },
    onError: () => {
      toast.error('Failed to start sync');
    },
  });

  // Delete connection mutation
  const deleteMutation = useMutation({
    mutationFn: async (connectionId: string) => {
      await api.delete(`/atlas-intelligence/state/sources/${connectionId}`);
    },
    onSuccess: () => {
      toast.success('Connection deleted');
      queryClient.invalidateQueries({ queryKey: ['connections'] });
    },
    onError: () => {
      toast.error('Failed to delete connection');
    },
  });

  const filteredConnections = connections?.filter((conn) => {
    const matchesSearch =
      searchQuery === '' ||
      conn.source_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      conn.source_type.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' || conn.status === statusFilter;

    return matchesSearch && matchesStatus;
  }) || [];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-green-500/10 text-green-600">
            <CheckCircle className="h-3 w-3" />
            Active
          </span>
        );
      case 'syncing':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-blue-500/10 text-blue-600">
            <RefreshCw className="h-3 w-3 animate-spin" />
            Syncing
          </span>
        );
      case 'paused':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
            <Pause className="h-3 w-3" />
            Paused
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center gap-1.5 px-2 py-1 text-xs font-medium rounded-full bg-red-500/10 text-red-600">
            <XCircle className="h-3 w-3" />
            Error
          </span>
        );
      default:
        return null;
    }
  };

  const getSyncModeBadge = (mode: string) => {
    const labels: Record<string, string> = {
      full_refresh: 'Full Refresh',
      incremental: 'Incremental',
      cdc: 'CDC',
    };
    return (
      <span className="px-2 py-0.5 text-[10px] font-medium rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
        {labels[mode] || mode}
      </span>
    );
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTimeAgo = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const activeCount = connections?.filter((c) => c.status === 'active').length || 0;
  const errorCount = connections?.filter((c) => c.status === 'error').length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Connections</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage your active data connections
          </p>
        </div>
        <Link to="/sources">
          <Button size="sm">
            <Plus className="h-4 w-4 mr-2" />
            New Connection
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">{connections?.length || 0}</p>
              </div>
              <Database className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Active</p>
                <p className="text-2xl font-bold text-green-600">{activeCount}</p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Errors</p>
                <p className="text-2xl font-bold text-red-600">{errorCount}</p>
              </div>
              <AlertTriangle className="h-5 w-5 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total Rows</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">
                  {formatNumber(connections?.reduce((sum, c) => sum + c.records_synced, 0) || 0)}
                </p>
              </div>
              <Zap className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--muted-foreground))]" />
          <input
            type="text"
            placeholder="Search connections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[hsl(var(--input))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          />
        </div>

        <div className="flex gap-2">
          {['all', 'active', 'paused', 'error'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors capitalize ${
                statusFilter === status
                  ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                  : 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Connections List */}
      <Card>
        <CardContent className="p-0">
          <div className="divide-y divide-[hsl(var(--border))]">
            {filteredConnections.length > 0 ? (
              filteredConnections.map((conn) => (
                <div
                  key={conn.id}
                  className="flex items-center justify-between p-4 hover:bg-[hsl(var(--secondary)/0.3)] transition-colors"
                >
                  <div className="flex items-center gap-4 min-w-0 flex-1">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[hsl(var(--secondary))]">
                      <Database className="h-5 w-5 text-[hsl(var(--foreground))]" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                          {conn.source_name}
                        </h3>
                        {getSyncModeBadge(conn.sync_mode)}
                      </div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">
                        {conn.streams_count} streams • {formatNumber(conn.records_synced)} rows
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="hidden sm:block text-right">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Last sync</p>
                      <p className="text-sm text-[hsl(var(--foreground))]">{formatTimeAgo(conn.last_sync)}</p>
                    </div>

                    {getStatusBadge(conn.status)}

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => syncMutation.mutate(conn.id)}
                        disabled={conn.status === 'syncing'}
                      >
                        <Play className="h-4 w-4" />
                      </Button>

                      <div className="relative">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setActiveMenu(activeMenu === conn.id ? null : conn.id)}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>

                        {activeMenu === conn.id && (
                          <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-lg z-10">
                            <button className="flex w-full items-center gap-2 px-4 py-2 text-sm text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))]">
                              <Settings className="h-4 w-4" />
                              Configure
                            </button>
                            <button className="flex w-full items-center gap-2 px-4 py-2 text-sm text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))]">
                              <Calendar className="h-4 w-4" />
                              Schedule
                            </button>
                            <button
                              onClick={() => deleteMutation.mutate(conn.id)}
                              className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-500/10"
                            >
                              <Trash2 className="h-4 w-4" />
                              Delete
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-12 text-center">
                <Database className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
                <h3 className="mt-4 text-lg font-medium text-[hsl(var(--foreground))]">No connections</h3>
                <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                  Get started by creating a new connection
                </p>
                <Link to="/sources">
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    New Connection
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getMockConnections(): Connection[] {
  return [
    {
      id: '1',
      source_name: 'PostgreSQL Production',
      source_type: 'postgresql',
      status: 'active',
      last_sync: new Date(Date.now() - 300000).toISOString(),
      streams_count: 12,
      records_synced: 1250000,
      sync_mode: 'incremental',
      schedule: '0 * * * *',
    },
    {
      id: '2',
      source_name: 'Salesforce CRM',
      source_type: 'salesforce',
      status: 'syncing',
      last_sync: new Date(Date.now() - 3600000).toISOString(),
      streams_count: 8,
      records_synced: 45000,
      sync_mode: 'incremental',
    },
    {
      id: '3',
      source_name: 'Stripe Payments',
      source_type: 'stripe',
      status: 'error',
      last_sync: new Date(Date.now() - 7200000).toISOString(),
      streams_count: 5,
      records_synced: 89000,
      sync_mode: 'full_refresh',
    },
    {
      id: '4',
      source_name: 'HubSpot Marketing',
      source_type: 'hubspot',
      status: 'active',
      last_sync: new Date(Date.now() - 1800000).toISOString(),
      streams_count: 15,
      records_synced: 32000,
      sync_mode: 'cdc',
    },
  ];
}
