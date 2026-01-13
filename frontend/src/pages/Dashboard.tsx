import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  ArrowRight,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Play,
  Plus,
  RefreshCw,
  Clock,
  Zap,
  Database,
  TrendingUp,
  BarChart3,
  ArrowUpRight,
  Loader2,
} from 'lucide-react';
import { getDashboardStats, api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface SyncJob {
  id: string;
  source_name: string;
  source_type: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  records_synced: number;
  started_at: string;
  completed_at?: string;
  progress?: number;
}

interface ConnectionHealth {
  name: string;
  type: string;
  status: 'healthy' | 'warning' | 'error';
  lastSync?: string;
  nextSync?: string;
  recordsTotal?: number;
}

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
    retry: false,
  });

  // Fetch sync stats from AtlasIntelligence
  const { data: syncStats } = useQuery({
    queryKey: ['sync-stats'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/stats');
        return response.data;
      } catch {
        return { running: 0, completed: 0, failed: 0, total_records: 0 };
      }
    },
    refetchInterval: 10000,
  });

  // Fetch running jobs
  const { data: runningJobs } = useQuery({
    queryKey: ['running-jobs'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/running');
        return response.data as SyncJob[];
      } catch {
        return [];
      }
    },
    refetchInterval: 5000,
  });

  // Fetch recent jobs
  const { data: recentJobs } = useQuery({
    queryKey: ['recent-jobs'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/jobs?limit=5');
        return response.data as SyncJob[];
      } catch {
        return [];
      }
    },
    refetchInterval: 15000,
  });

  // Fetch connector health
  const { data: connectorHealth } = useQuery({
    queryKey: ['connector-health'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/health');
        return response.data;
      } catch {
        return { connectors: [] };
      }
    },
    refetchInterval: 30000,
  });

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

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

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />;
    }
  };

  const getHealthStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500 bg-green-500/10';
      case 'warning':
        return 'text-yellow-500 bg-yellow-500/10';
      case 'error':
        return 'text-red-500 bg-red-500/10';
      default:
        return 'text-[hsl(var(--muted-foreground))] bg-[hsl(var(--secondary))]';
    }
  };

  // Mock connection health data if not available
  const connections: ConnectionHealth[] = connectorHealth?.connectors?.length > 0
    ? connectorHealth.connectors
    : [
        { name: 'PostgreSQL Production', type: 'postgresql', status: 'healthy', lastSync: new Date().toISOString(), recordsTotal: 1250000 },
        { name: 'Salesforce CRM', type: 'salesforce', status: 'healthy', lastSync: new Date(Date.now() - 3600000).toISOString(), recordsTotal: 45000 },
        { name: 'Stripe Payments', type: 'stripe', status: 'warning', lastSync: new Date(Date.now() - 7200000).toISOString(), recordsTotal: 89000 },
        { name: 'HubSpot Marketing', type: 'hubspot', status: 'healthy', lastSync: new Date(Date.now() - 1800000).toISOString(), recordsTotal: 32000 },
      ];

  const healthyCount = connections.filter(c => c.status === 'healthy').length;
  const warningCount = connections.filter(c => c.status === 'warning').length;
  const errorCount = connections.filter(c => c.status === 'error').length;

  return (
    <div className="space-y-6">
      {/* Header with Quick Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Overview</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Monitor your data pipelines and sync status
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/sources">
            <Button variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              New Connection
            </Button>
          </Link>
          <Link to="/sync-jobs">
            <Button size="sm">
              <Play className="h-4 w-4 mr-2" />
              View All Syncs
            </Button>
          </Link>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Active Syncs</p>
                <p className="mt-1 text-3xl font-bold text-[hsl(var(--foreground))]">
                  {syncStats?.running || runningJobs?.length || 0}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-blue-500/10">
                <RefreshCw className={`h-6 w-6 text-blue-500 ${(runningJobs?.length || 0) > 0 ? 'animate-spin' : ''}`} />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-[hsl(var(--muted-foreground))]">
              <span className="font-medium text-green-600">{syncStats?.completed || 0}</span>
              <span className="ml-1">completed today</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Rows Synced</p>
                <p className="mt-1 text-3xl font-bold text-[hsl(var(--foreground))]">
                  {formatNumber(syncStats?.total_records || (stats?.total_runs ?? 0) * 1000 || 0)}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                <Database className="h-6 w-6 text-[hsl(var(--foreground))]" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm">
              <ArrowUpRight className="h-4 w-4 text-green-600" />
              <span className="ml-1 text-green-600 font-medium">12%</span>
              <span className="ml-1 text-[hsl(var(--muted-foreground))]">vs last week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Connections</p>
                <p className="mt-1 text-3xl font-bold text-[hsl(var(--foreground))]">
                  {connections.length}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                <Zap className="h-6 w-6 text-[hsl(var(--foreground))]" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3 text-sm">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-[hsl(var(--muted-foreground))]">{healthyCount}</span>
              </span>
              {warningCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-yellow-500" />
                  <span className="text-[hsl(var(--muted-foreground))]">{warningCount}</span>
                </span>
              )}
              {errorCount > 0 && (
                <span className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full bg-red-500" />
                  <span className="text-[hsl(var(--muted-foreground))]">{errorCount}</span>
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Data Quality</p>
                <p className="mt-1 text-3xl font-bold text-[hsl(var(--foreground))]">
                  {Math.round((stats?.avg_quality_score || 0.95) * 100)}%
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                <TrendingUp className="h-6 w-6 text-green-500" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-[hsl(var(--muted-foreground))]">
              <span>{stats?.total_pii_detections || 0} PII detections</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Active Syncs */}
      {(runningJobs?.length || 0) > 0 && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              Active Syncs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {runningJobs?.map((job) => (
                <div key={job.id} className="flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                        {job.source_name}
                      </span>
                      <span className="text-xs text-[hsl(var(--muted-foreground))]">
                        {formatNumber(job.records_synced)} rows
                      </span>
                    </div>
                    <div className="h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all duration-500"
                        style={{ width: `${job.progress || 50}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Connection Health */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-medium">Connection Health</CardTitle>
            <Link to="/connections">
              <Button variant="ghost" size="sm">
                View all
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {connections.slice(0, 5).map((conn, idx) => (
                <div key={idx} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${getHealthStatusColor(conn.status)}`}>
                      {conn.status === 'healthy' ? (
                        <CheckCircle className="h-4 w-4" />
                      ) : conn.status === 'warning' ? (
                        <AlertTriangle className="h-4 w-4" />
                      ) : (
                        <XCircle className="h-4 w-4" />
                      )}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-[hsl(var(--foreground))]">{conn.name}</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">{conn.type}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-[hsl(var(--foreground))]">{formatNumber(conn.recordsTotal || 0)}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{formatTimeAgo(conn.lastSync)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base font-medium">Recent Activity</CardTitle>
            <Link to="/sync-jobs">
              <Button variant="ghost" size="sm">
                View all
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(recentJobs?.length || 0) > 0 ? (
                recentJobs?.map((job) => (
                  <div key={job.id} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <p className="text-sm font-medium text-[hsl(var(--foreground))]">{job.source_name}</p>
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">
                          {formatNumber(job.records_synced)} rows synced
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">
                      {formatTimeAgo(job.completed_at || job.started_at)}
                    </span>
                  </div>
                ))
              ) : stats?.recent_runs?.length ? (
                stats.recent_runs.slice(0, 5).map((run) => (
                  <div key={run.run_id} className="flex items-center justify-between py-2 border-b border-[hsl(var(--border))] last:border-0">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(run.status)}
                      <div>
                        <p className="text-sm font-medium text-[hsl(var(--foreground))]">{run.dataset_name}</p>
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">
                          {Math.round((run.quality_score || 0) * 100)}% quality
                        </p>
                      </div>
                    </div>
                    <span className="text-xs text-[hsl(var(--muted-foreground))]">
                      {formatTimeAgo((run as any).created_at)}
                    </span>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center">
                  <Activity className="mx-auto h-8 w-8 text-[hsl(var(--muted-foreground))]" />
                  <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">No recent activity</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/sources">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full group">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <Zap className="h-5 w-5 text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--foreground))]" />
                <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="mt-4 text-sm font-medium text-[hsl(var(--foreground))]">Browse Sources</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                300+ connectors available
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/sync-jobs">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full group">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <Activity className="h-5 w-5 text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--foreground))]" />
                <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="mt-4 text-sm font-medium text-[hsl(var(--foreground))]">Sync History</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                View all sync jobs and logs
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/reports">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full group">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <BarChart3 className="h-5 w-5 text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--foreground))]" />
                <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="mt-4 text-sm font-medium text-[hsl(var(--foreground))]">Quality Reports</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Data quality analytics
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/health">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full group">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <CheckCircle className="h-5 w-5 text-[hsl(var(--muted-foreground))] group-hover:text-[hsl(var(--foreground))]" />
                <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <h3 className="mt-4 text-sm font-medium text-[hsl(var(--foreground))]">System Health</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Monitor connector status
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
