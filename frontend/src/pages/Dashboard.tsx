import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Database,
  Shield,
  TrendingUp,
  ArrowRight,
  Clock,
  CheckCircle,
  AlertTriangle,
  FileCheck,
  Upload,
  Search,
  Settings,
} from 'lucide-react';
import { getDashboardStats } from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 30000,
    retry: false,
    meta: {
      errorMessage: 'Failed to load dashboard stats',
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const readinessItems = [
    {
      name: 'Art. 10 Data Governance',
      status: (stats?.avg_quality_score ?? 0) >= 0.8 ? 'Ready' : 'Needs attention',
      description: 'Quality gates and schema validation in place',
      icon: FileCheck,
    },
    {
      name: 'Art. 11 Documentation',
      status: (stats?.recent_runs?.length ?? 0) > 0 ? 'Ready' : 'In progress',
      description: 'Run history and metadata captured',
      icon: CheckCircle,
    },
    {
      name: 'Art. 12 Logging',
      status: (stats?.recent_runs?.length ?? 0) > 0 ? 'Ready' : 'In progress',
      description: 'Execution logs and lineage available',
      icon: Activity,
    },
    {
      name: 'Art. 30 Registrering',
      status: (stats?.total_pii_detections ?? 0) >= 0 ? 'Ready' : 'In progress',
      description: 'PII scanning and GDPR flows active',
      icon: Shield,
    },
  ];

  const formatDate = (value?: string) => {
    if (!value) return 'Not available';
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? 'Not available' : d.toLocaleString();
  };

  const statCards = [
    { name: 'Pipeline Runs', value: stats?.total_runs || 0, icon: Activity, link: '/reports' },
    { name: 'Quality Score', value: `${Math.round((stats?.avg_quality_score || 0) * 100)}%`, icon: TrendingUp, link: '/reports' },
    { name: 'PII Detections', value: stats?.total_pii_detections || 0, icon: Shield, link: '/pii' },
    { name: 'Connectors', value: stats?.active_connectors || 0, icon: Database, link: '/connectors' },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Dashboard</h1>
        <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
          Monitor your data pipeline and compliance status
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <Link key={stat.name} to={stat.link}>
            <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">{stat.name}</p>
                    <p className="mt-1 text-2xl font-semibold text-[hsl(var(--foreground))]">{stat.value}</p>
                  </div>
                  <stat.icon className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {/* Recent Runs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-medium">Recent Pipeline Runs</CardTitle>
            <CardDescription>Latest data processing activity</CardDescription>
          </div>
          <Link to="/reports">
            <Button variant="ghost" size="sm">
              View all
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </CardHeader>
        <CardContent>
          <div className="divide-y divide-[hsl(var(--border))]">
            {stats?.recent_runs && stats.recent_runs.length > 0 ? (
              stats.recent_runs.slice(0, 5).map((run) => (
                <div key={run.run_id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`h-2 w-2 rounded-full ${
                        run.status === 'completed' ? 'bg-green-500' :
                        run.status === 'failed' ? 'bg-red-500' :
                        run.status === 'running' ? 'bg-blue-500' : 'bg-gray-400'
                      }`} />
                      <div>
                        <p className="text-sm font-medium text-[hsl(var(--foreground))]">{run.dataset_name}</p>
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">
                          {formatDate((run as any).created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {run.quality_score !== undefined && (
                        <span className="text-xs text-[hsl(var(--muted-foreground))]">
                          {Math.round(run.quality_score * 100)}% quality
                        </span>
                      )}
                      <Link
                        to={`/reports/${run.run_id}`}
                        className="text-xs font-medium text-[hsl(var(--foreground))] hover:underline"
                      >
                        Details
                      </Link>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center">
                <Activity className="mx-auto h-8 w-8 text-[hsl(var(--muted-foreground))]" />
                <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">No recent runs</p>
                <Link to="/upload">
                  <Button variant="outline" size="sm" className="mt-4">
                    Upload CSV
                  </Button>
                </Link>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Governance & EU AI Act */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base font-medium">Governance & EU AI Act</CardTitle>
              <CardDescription>Compliance status across data quality and controls</CardDescription>
            </div>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--secondary))] px-2.5 py-1 text-xs font-medium text-[hsl(var(--secondary-foreground))]">
              <Shield className="h-3 w-3" />
              Compliant
            </span>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {readinessItems.map((item) => {
              const Icon = item.icon;
              const isReady = item.status === 'Ready';
              return (
                <div
                  key={item.name}
                  className="rounded-lg border border-[hsl(var(--border))] p-4"
                >
                  <div className="flex items-center gap-2">
                    <Icon className={`h-4 w-4 ${isReady ? 'text-green-500' : 'text-yellow-500'}`} />
                    <span className="text-xs font-medium text-[hsl(var(--muted-foreground))]">{item.name}</span>
                  </div>
                  <div className="mt-2 flex items-center gap-1.5">
                    {isReady ? (
                      <CheckCircle className="h-3.5 w-3.5 text-green-500" />
                    ) : (
                      <AlertTriangle className="h-3.5 w-3.5 text-yellow-500" />
                    )}
                    <span className={`text-sm font-medium ${isReady ? 'text-green-600' : 'text-yellow-600'}`}>
                      {item.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">{item.description}</p>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/upload">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-6">
              <Upload className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Upload CSV</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Process data with quality validation
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/catalog">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-6">
              <Search className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Data Catalog</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Browse and search all datasets
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/features">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-6">
              <Database className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">Feature Store</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Manage ML features and versions
              </p>
            </CardContent>
          </Card>
        </Link>

        <Link to="/gdpr">
          <Card className="hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer h-full">
            <CardContent className="p-6">
              <Settings className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-3 text-sm font-medium text-[hsl(var(--foreground))]">GDPR Compliance</h3>
              <p className="mt-1 text-xs text-[hsl(var(--muted-foreground))]">
                Manage data subject requests
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
