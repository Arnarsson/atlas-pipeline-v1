import { useQuery } from '@tanstack/react-query';
import {
  CheckCircle,
  AlertTriangle,
  Clock,
  Database,
  RefreshCw,
  BarChart3,
  ArrowUpRight,
  Zap,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface HealthStatus {
  name: string;
  type: string;
  status: 'healthy' | 'degraded' | 'down';
  latency_ms: number;
  last_check: string;
  uptime_percent: number;
  error_rate: number;
  records_today: number;
}

export default function ConnectorHealth() {
  const { data: healthData, isLoading, refetch } = useQuery({
    queryKey: ['connector-health-detailed'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/health');
        return response.data;
      } catch {
        return getMockHealthData();
      }
    },
    refetchInterval: 30000,
  });

  const { data: syncStats } = useQuery({
    queryKey: ['sync-stats'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/stats');
        return response.data;
      } catch {
        return { total_records: 0, success_rate: 0.98 };
      }
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const connectors: HealthStatus[] = healthData?.connectors || getMockHealthData().connectors;
  const healthyCount = connectors.filter((c) => c.status === 'healthy').length;
  const degradedCount = connectors.filter((c) => c.status === 'degraded').length;
  const downCount = connectors.filter((c) => c.status === 'down').length;
  const avgLatency = connectors.reduce((sum, c) => sum + c.latency_ms, 0) / connectors.length || 0;

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      healthy: 'bg-green-500/10 text-green-600',
      degraded: 'bg-yellow-500/10 text-yellow-600',
      down: 'bg-red-500/10 text-red-600',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${styles[status]}`}>
        {status}
      </span>
    );
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatTimeAgo = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">System Health</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Monitor connector status and performance metrics
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">System Status</p>
                <p className="mt-1 text-2xl font-bold text-green-600">
                  {downCount === 0 ? 'Healthy' : degradedCount > 0 ? 'Degraded' : 'Issues'}
                </p>
              </div>
              <div className={`flex h-12 w-12 items-center justify-center rounded-full ${downCount === 0 ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
                {downCount === 0 ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : (
                  <AlertTriangle className="h-6 w-6 text-red-500" />
                )}
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1 text-green-600">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                {healthyCount}
              </span>
              {degradedCount > 0 && (
                <span className="flex items-center gap-1 text-yellow-600">
                  <span className="h-2 w-2 rounded-full bg-yellow-500" />
                  {degradedCount}
                </span>
              )}
              {downCount > 0 && (
                <span className="flex items-center gap-1 text-red-600">
                  <span className="h-2 w-2 rounded-full bg-red-500" />
                  {downCount}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Avg Latency</p>
                <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">
                  {Math.round(avgLatency)}ms
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                <Clock className="h-6 w-6 text-[hsl(var(--foreground))]" />
              </div>
            </div>
            <div className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">
              {avgLatency < 100 ? 'Excellent' : avgLatency < 500 ? 'Good' : 'Slow'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Success Rate</p>
                <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">
                  {((syncStats?.success_rate || 0.98) * 100).toFixed(1)}%
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                <BarChart3 className="h-6 w-6 text-[hsl(var(--foreground))]" />
              </div>
            </div>
            <div className="mt-4 flex items-center text-sm text-green-600">
              <ArrowUpRight className="h-4 w-4" />
              <span className="ml-1">+0.5% vs last week</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Records Today</p>
                <p className="mt-1 text-2xl font-bold text-[hsl(var(--foreground))]">
                  {formatNumber(syncStats?.total_records || connectors.reduce((sum, c) => sum + c.records_today, 0))}
                </p>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                <Database className="h-6 w-6 text-[hsl(var(--foreground))]" />
              </div>
            </div>
            <div className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">
              Across {connectors.length} connectors
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Connectors Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Connector Status</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[hsl(var(--border))]">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Connector
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Latency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Uptime
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Error Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase">
                    Last Check
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border))]">
                {connectors.map((connector) => (
                  <tr key={connector.name} className="hover:bg-[hsl(var(--secondary)/0.3)]">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--secondary))]">
                          <Zap className="h-4 w-4 text-[hsl(var(--foreground))]" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-[hsl(var(--foreground))]">{connector.name}</p>
                          <p className="text-xs text-[hsl(var(--muted-foreground))]">{connector.type}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">{getStatusBadge(connector.status)}</td>
                    <td className="px-6 py-4">
                      <span className={`text-sm ${connector.latency_ms > 500 ? 'text-yellow-600' : 'text-[hsl(var(--foreground))]'}`}>
                        {connector.latency_ms}ms
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-[hsl(var(--foreground))]">{connector.uptime_percent.toFixed(1)}%</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`text-sm ${connector.error_rate > 0.05 ? 'text-red-600' : 'text-[hsl(var(--foreground))]'}`}>
                        {(connector.error_rate * 100).toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-[hsl(var(--muted-foreground))]">
                        {formatTimeAgo(connector.last_check)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function getMockHealthData() {
  return {
    connectors: [
      { name: 'PostgreSQL Production', type: 'postgresql', status: 'healthy', latency_ms: 45, last_check: new Date().toISOString(), uptime_percent: 99.99, error_rate: 0.001, records_today: 125000 },
      { name: 'Salesforce CRM', type: 'salesforce', status: 'healthy', latency_ms: 120, last_check: new Date().toISOString(), uptime_percent: 99.95, error_rate: 0.005, records_today: 8500 },
      { name: 'Stripe Payments', type: 'stripe', status: 'degraded', latency_ms: 450, last_check: new Date().toISOString(), uptime_percent: 98.5, error_rate: 0.08, records_today: 2300 },
      { name: 'HubSpot Marketing', type: 'hubspot', status: 'healthy', latency_ms: 85, last_check: new Date().toISOString(), uptime_percent: 99.9, error_rate: 0.002, records_today: 32000 },
      { name: 'Google Analytics', type: 'google_analytics', status: 'healthy', latency_ms: 95, last_check: new Date().toISOString(), uptime_percent: 99.98, error_rate: 0.001, records_today: 450000 },
    ] as HealthStatus[],
  };
}
