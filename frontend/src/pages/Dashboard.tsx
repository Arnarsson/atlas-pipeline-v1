import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Database,
  Shield,
  TrendingUp,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  Zap,
  Clock,
  BarChart3,
  Cable,
  Upload,
  Eye,
  Play,
} from 'lucide-react';
import { getDashboardStats } from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// ============================================================================
// TYPES
// ============================================================================

interface SyncActivity {
  id: string;
  name: string;
  source: string;
  status: 'running' | 'completed' | 'failed' | 'pending';
  progress?: number;
  records_synced: number;
  eta?: string;
  completed_at?: string;
  error?: string;
}

interface ConnectionHealth {
  id: string;
  name: string;
  icon: string;
  status: 'healthy' | 'warning' | 'error';
  latency?: string;
}

// ============================================================================
// DEMO DATA
// ============================================================================

const DEMO_SYNC_ACTIVITY: SyncActivity[] = [
  { id: '1', name: 'Salesforce', source: 'salesforce', status: 'running', progress: 78, records_synced: 142847, eta: '3 min' },
  { id: '2', name: 'Stripe', source: 'stripe', status: 'completed', records_synced: 23412, completed_at: '2 min ago' },
  { id: '3', name: 'HubSpot', source: 'hubspot', status: 'completed', records_synced: 8291, completed_at: '15 min ago' },
  { id: '4', name: 'PostgreSQL', source: 'postgresql', status: 'failed', records_synced: 0, error: 'Connection timeout', completed_at: '32 min ago' },
];

const DEMO_CONNECTIONS: ConnectionHealth[] = [
  { id: '1', name: 'Salesforce', icon: '☁️', status: 'healthy' },
  { id: '2', name: 'Stripe', icon: '💳', status: 'healthy' },
  { id: '3', name: 'HubSpot', icon: '🧡', status: 'healthy' },
  { id: '4', name: 'PostgreSQL', icon: '🐘', status: 'warning', latency: '2.3s' },
  { id: '5', name: 'MySQL', icon: '🐬', status: 'healthy' },
];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'running':
      return <RefreshCw className="w-4 h-4 animate-spin text-blue-600" />;
    case 'completed':
    case 'healthy':
      return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    case 'failed':
    case 'error':
      return <XCircle className="w-4 h-4 text-red-600" />;
    case 'warning':
      return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
    default:
      return <Clock className="w-4 h-4 text-gray-400" />;
  }
}

// ============================================================================
// COMPONENTS
// ============================================================================

function StatCard({ title, value, subtitle, icon, trend, href }: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  trend?: { value: number; positive: boolean };
  href?: string;
}) {
  const content = (
    <Card className={href ? "hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer" : ""}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">{title}</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))] mt-1">{value}</p>
            {subtitle && (
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{subtitle}</p>
            )}
            {trend && (
              <div className={`flex items-center gap-1 mt-2 text-xs ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
                <TrendingUp className={`w-3 h-3 ${!trend.positive && 'rotate-180'}`} />
                <span>{trend.value}% vs yesterday</span>
              </div>
            )}
          </div>
          <div className="p-2.5 rounded-lg bg-[hsl(var(--secondary))]">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (href) {
    return <Link to={href}>{content}</Link>;
  }
  return content;
}

function SyncProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-full h-1.5 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
      <div
        className="h-full bg-blue-600 rounded-full transition-all duration-500"
        style={{ width: `${progress}%` }}
      />
    </div>
  );
}

function SyncActivityItem({ sync }: { sync: SyncActivity }) {
  return (
    <div className="py-3 border-b border-[hsl(var(--border))] last:border-0">
      {sync.status === 'running' && (
        <>
          <div className="mb-2">
            <SyncProgressBar progress={sync.progress || 0} />
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {getStatusIcon(sync.status)}
              <span className="font-medium text-[hsl(var(--foreground))]">{sync.name}</span>
              <span className="text-xs text-blue-600">→ Atlas</span>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className="text-[hsl(var(--foreground))]">{formatNumber(sync.records_synced)} rows</span>
              <span className="text-[hsl(var(--muted-foreground))]">ETA: {sync.eta}</span>
            </div>
          </div>
        </>
      )}
      {sync.status !== 'running' && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon(sync.status)}
            <span className={`font-medium ${sync.status === 'failed' ? 'text-red-600' : 'text-[hsl(var(--foreground))]'}`}>
              {sync.name}
            </span>
            {sync.error && (
              <span className="text-xs text-red-600">- {sync.error}</span>
            )}
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-[hsl(var(--foreground))]">
              {sync.status === 'failed' ? 'Failed' : `${formatNumber(sync.records_synced)} rows`}
            </span>
            <span className="text-[hsl(var(--muted-foreground))]">{sync.completed_at}</span>
            {sync.status === 'failed' && (
              <Link to="/connections" className="text-xs font-medium text-blue-600 hover:underline">
                View →
              </Link>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ConnectionHealthCard({ connection }: { connection: ConnectionHealth }) {
  const statusColors = {
    healthy: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
  };

  return (
    <div className="flex flex-col items-center p-3 rounded-lg border border-[hsl(var(--border))] hover:bg-[hsl(var(--secondary)/0.5)] transition-colors min-w-[100px]">
      <div className="text-2xl mb-1">{connection.icon}</div>
      <span className="text-xs font-medium text-[hsl(var(--foreground))] text-center truncate w-full">{connection.name}</span>
      <div className={`flex items-center gap-1 mt-1 ${statusColors[connection.status]}`}>
        <div className={`w-1.5 h-1.5 rounded-full ${
          connection.status === 'healthy' ? 'bg-green-500' :
          connection.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
        }`} />
        <span className="text-[10px] uppercase">
          {connection.status === 'healthy' ? 'OK' : connection.status === 'warning' ? 'Warn' : 'Error'}
        </span>
      </div>
    </div>
  );
}

function UsageBar({ label, current, max, color = 'bg-blue-600' }: { label: string; current: number; max: number; color?: string }) {
  const percentage = Math.min((current / max) * 100, 100);

  return (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-[hsl(var(--muted-foreground))]">{label}</span>
        <span className="text-[hsl(var(--foreground))] font-medium">
          {formatNumber(current)} / {formatNumber(max)} ({Math.round(percentage)}%)
        </span>
      </div>
      <div className="w-full h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function Dashboard() {
  const [timeRange] = useState('24h');

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
    retry: false,
  });

  // Calculate metrics
  const activeSources = 12;
  const runningSyncs = DEMO_SYNC_ACTIVITY.filter(s => s.status === 'running').length;
  const totalRowsSynced = 847_392;
  const warnings = DEMO_CONNECTIONS.filter(c => c.status === 'warning').length;
  const avgQualityScore = stats?.avg_quality_score ? Math.round(stats.avg_quality_score * 100) : 94;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Dashboard</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Data pipeline command center
          </p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            className="px-3 py-1.5 text-sm border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
          >
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Sources"
          value={activeSources}
          subtitle="Connections configured"
          icon={<Cable className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />}
          href="/connections"
        />
        <StatCard
          title="Running Syncs"
          value={runningSyncs}
          subtitle={runningSyncs > 0 ? "In progress now" : "All syncs idle"}
          icon={<Zap className="w-5 h-5 text-blue-600" />}
          href="/connections"
        />
        <StatCard
          title="Rows Synced"
          value={formatNumber(totalRowsSynced)}
          subtitle="Today"
          icon={<BarChart3 className="w-5 h-5 text-green-600" />}
          trend={{ value: 12, positive: true }}
        />
        <StatCard
          title="Warnings"
          value={warnings}
          subtitle={warnings > 0 ? "Need attention" : "All systems healthy"}
          icon={warnings > 0
            ? <AlertTriangle className="w-5 h-5 text-yellow-600" />
            : <CheckCircle2 className="w-5 h-5 text-green-600" />
          }
          href="/connections"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sync Activity - Takes 2 columns */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div>
                <CardTitle className="text-base font-semibold">Sync Activity</CardTitle>
                <CardDescription>Real-time data pipeline status</CardDescription>
              </div>
              <Link to="/connections">
                <Button variant="ghost" size="sm">
                  View All
                  <ArrowRight className="ml-1 h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {DEMO_SYNC_ACTIVITY.length > 0 ? (
                <div>
                  {DEMO_SYNC_ACTIVITY.map((sync) => (
                    <SyncActivityItem key={sync.id} sync={sync} />
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Activity className="mx-auto h-8 w-8 text-[hsl(var(--muted-foreground))]" />
                  <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">No recent sync activity</p>
                  <Link to="/connections">
                    <Button variant="outline" size="sm" className="mt-4">
                      <Play className="w-4 h-4 mr-2" />
                      Start a Sync
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Data Quality & Usage - Takes 1 column */}
        <div className="space-y-6">
          {/* Data Quality */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Data Quality</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-center mb-4">
                <div className="relative w-28 h-28">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle
                      cx="56"
                      cy="56"
                      r="48"
                      fill="none"
                      stroke="hsl(var(--secondary))"
                      strokeWidth="8"
                    />
                    <circle
                      cx="56"
                      cy="56"
                      r="48"
                      fill="none"
                      stroke={avgQualityScore >= 90 ? '#22c55e' : avgQualityScore >= 70 ? '#eab308' : '#ef4444'}
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${avgQualityScore * 3.02} 302`}
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-2xl font-bold text-[hsl(var(--foreground))]">{avgQualityScore}%</span>
                  </div>
                </div>
              </div>
              <p className="text-xs text-center text-[hsl(var(--muted-foreground))]">
                Average across all sources
              </p>
              <Link to="/reports" className="block mt-3">
                <Button variant="outline" size="sm" className="w-full">
                  <Eye className="w-4 h-4 mr-2" />
                  View Reports
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Usage This Month */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Usage This Month</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <UsageBar label="Rows Synced" current={847_000} max={1_000_000} color="bg-blue-600" />
              <UsageBar label="Connections" current={12} max={50} color="bg-green-600" />
              <UsageBar label="API Calls" current={45_000} max={100_000} color="bg-purple-600" />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Connection Health */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-base font-semibold">Connection Health</CardTitle>
            <CardDescription>Status of all data sources</CardDescription>
          </div>
          <Link to="/connections">
            <Button variant="outline" size="sm">
              Manage Connections
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {DEMO_CONNECTIONS.map((connection) => (
              <ConnectionHealthCard key={connection.id} connection={connection} />
            ))}
            <Link to="/connections" className="flex-shrink-0">
              <div className="flex flex-col items-center justify-center p-3 rounded-lg border border-dashed border-[hsl(var(--border))] hover:bg-[hsl(var(--secondary)/0.5)] transition-colors min-w-[100px] h-full">
                <div className="w-8 h-8 rounded-full bg-[hsl(var(--secondary))] flex items-center justify-center mb-1">
                  <Database className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                </div>
                <span className="text-xs text-[hsl(var(--muted-foreground))]">Add Source</span>
              </div>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Link to="/upload">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-5">
              <Upload className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Upload CSV</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Process data with quality validation
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/connections">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-5">
              <Cable className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Add Connection</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Connect to 150+ data sources
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/catalog">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-5">
              <Database className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Data Catalog</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Browse and search all datasets
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/gdpr">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-5">
              <Shield className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Compliance</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                GDPR and governance controls
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
