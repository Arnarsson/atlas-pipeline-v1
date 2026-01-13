import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Play,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Database,
  AlertTriangle,
  Loader2,
  Calendar,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface SyncJob {
  id: string;
  source_name: string;
  source_type: string;
  status: 'running' | 'completed' | 'failed' | 'pending' | 'cancelled';
  started_at: string;
  completed_at?: string;
  records_synced: number;
  records_failed: number;
  duration_seconds?: number;
  error_message?: string;
  streams: StreamResult[];
}

interface StreamResult {
  name: string;
  records_synced: number;
  records_failed: number;
  status: 'completed' | 'failed' | 'running';
}

export default function SyncJobs() {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [dateRange, setDateRange] = useState<string>('today');

  // Fetch sync jobs
  const { data: jobs, isLoading } = useQuery({
    queryKey: ['sync-jobs', statusFilter, dateRange],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/jobs', {
          params: { status: statusFilter !== 'all' ? statusFilter : undefined, limit: 50 },
        });
        return response.data as SyncJob[];
      } catch {
        return getMockJobs();
      }
    },
    refetchInterval: 10000,
  });

  // Fetch running jobs specifically
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

  const toggleExpanded = (jobId: string) => {
    const newExpanded = new Set(expandedJobs);
    if (newExpanded.has(jobId)) {
      newExpanded.delete(jobId);
    } else {
      newExpanded.add(jobId);
    }
    setExpandedJobs(newExpanded);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />;
      case 'cancelled':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      default:
        return <Clock className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      running: 'bg-blue-500/10 text-blue-600',
      completed: 'bg-green-500/10 text-green-600',
      failed: 'bg-red-500/10 text-red-600',
      pending: 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]',
      cancelled: 'bg-yellow-500/10 text-yellow-600',
    };
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full capitalize ${styles[status] || styles.pending}`}>
        {status}
      </span>
    );
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    if (mins < 60) return `${mins}m ${secs}s`;
    const hours = Math.floor(mins / 60);
    return `${hours}h ${mins % 60}m`;
  };

  const formatTime = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const completedCount = jobs?.filter((j) => j.status === 'completed').length || 0;
  const failedCount = jobs?.filter((j) => j.status === 'failed').length || 0;
  const totalRecords = jobs?.reduce((sum, j) => sum + j.records_synced, 0) || 0;

  // Group jobs by date
  const jobsByDate = jobs?.reduce((acc, job) => {
    const dateKey = formatDate(job.started_at);
    if (!acc[dateKey]) {
      acc[dateKey] = [];
    }
    acc[dateKey].push(job);
    return acc;
  }, {} as Record<string, SyncJob[]>) || {};

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Sync Jobs</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Monitor and manage your data sync operations
          </p>
        </div>
        <Link to="/schedules">
          <Button variant="outline" size="sm">
            <Calendar className="h-4 w-4 mr-2" />
            Manage Schedules
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Running</p>
                <p className="text-2xl font-bold text-blue-600">{runningJobs?.length || 0}</p>
              </div>
              <RefreshCw className={`h-5 w-5 text-blue-500 ${(runningJobs?.length || 0) > 0 ? 'animate-spin' : ''}`} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Completed</p>
                <p className="text-2xl font-bold text-green-600">{completedCount}</p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Failed</p>
                <p className="text-2xl font-bold text-red-600">{failedCount}</p>
              </div>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Records Synced</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">{formatNumber(totalRecords)}</p>
              </div>
              <Database className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Running Jobs */}
      {(runningJobs?.length || 0) > 0 && (
        <Card className="border-blue-500/20">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-medium flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
              Currently Running
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {runningJobs?.map((job) => (
                <div key={job.id} className="flex items-center gap-4 p-3 rounded-lg bg-blue-500/5">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-[hsl(var(--foreground))]">
                        {job.source_name}
                      </span>
                      <span className="text-xs text-[hsl(var(--muted-foreground))]">
                        {formatNumber(job.records_synced)} rows synced
                      </span>
                    </div>
                    <div className="h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 animate-pulse" style={{ width: '60%' }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex gap-2">
          {['all', 'completed', 'failed', 'pending'].map((status) => (
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

        <div className="flex gap-2">
          {['today', '7days', '30days'].map((range) => (
            <button
              key={range}
              onClick={() => setDateRange(range)}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                dateRange === range
                  ? 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                  : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
              }`}
            >
              {range === 'today' ? 'Today' : range === '7days' ? '7 Days' : '30 Days'}
            </button>
          ))}
        </div>
      </div>

      {/* Jobs List */}
      <div className="space-y-6">
        {Object.entries(jobsByDate).map(([date, dateJobs]) => (
          <div key={date}>
            <h3 className="text-sm font-semibold text-[hsl(var(--muted-foreground))] mb-3">{date}</h3>
            <Card>
              <CardContent className="p-0">
                <div className="divide-y divide-[hsl(var(--border))]">
                  {dateJobs.map((job) => (
                    <div key={job.id}>
                      <button
                        onClick={() => toggleExpanded(job.id)}
                        className="flex items-center justify-between w-full p-4 hover:bg-[hsl(var(--secondary)/0.3)] transition-colors text-left"
                      >
                        <div className="flex items-center gap-4">
                          {getStatusIcon(job.status)}
                          <div>
                            <h4 className="text-sm font-medium text-[hsl(var(--foreground))]">
                              {job.source_name}
                            </h4>
                            <p className="text-xs text-[hsl(var(--muted-foreground))]">
                              Started at {formatTime(job.started_at)}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="hidden sm:block text-right">
                            <p className="text-sm text-[hsl(var(--foreground))]">
                              {formatNumber(job.records_synced)} rows
                            </p>
                            <p className="text-xs text-[hsl(var(--muted-foreground))]">
                              {formatDuration(job.duration_seconds)}
                            </p>
                          </div>
                          {getStatusBadge(job.status)}
                          {expandedJobs.has(job.id) ? (
                            <ChevronDown className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                          )}
                        </div>
                      </button>

                      {/* Expanded Details */}
                      {expandedJobs.has(job.id) && (
                        <div className="px-4 pb-4 bg-[hsl(var(--secondary)/0.2)]">
                          {job.error_message && (
                            <div className="mb-4 p-3 rounded-lg bg-red-500/10 text-red-600 text-sm">
                              <strong>Error:</strong> {job.error_message}
                            </div>
                          )}

                          <h5 className="text-xs font-semibold text-[hsl(var(--muted-foreground))] uppercase mb-2">
                            Streams ({job.streams.length})
                          </h5>
                          <div className="space-y-2">
                            {job.streams.map((stream) => (
                              <div
                                key={stream.name}
                                className="flex items-center justify-between p-2 rounded bg-[hsl(var(--background))]"
                              >
                                <div className="flex items-center gap-2">
                                  {getStatusIcon(stream.status)}
                                  <span className="text-sm text-[hsl(var(--foreground))]">{stream.name}</span>
                                </div>
                                <div className="flex items-center gap-4 text-sm">
                                  <span className="text-green-600">{formatNumber(stream.records_synced)} synced</span>
                                  {stream.records_failed > 0 && (
                                    <span className="text-red-600">{formatNumber(stream.records_failed)} failed</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        ))}

        {Object.keys(jobsByDate).length === 0 && (
          <Card>
            <CardContent className="py-12 text-center">
              <Clock className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
              <h3 className="mt-4 text-lg font-medium text-[hsl(var(--foreground))]">No sync jobs</h3>
              <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                Jobs will appear here when you run syncs
              </p>
              <Link to="/connections">
                <Button className="mt-4">
                  <Play className="h-4 w-4 mr-2" />
                  Go to Connections
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function getMockJobs(): SyncJob[] {
  const now = Date.now();
  return [
    {
      id: '1',
      source_name: 'PostgreSQL Production',
      source_type: 'postgresql',
      status: 'completed',
      started_at: new Date(now - 1800000).toISOString(),
      completed_at: new Date(now - 1200000).toISOString(),
      records_synced: 125000,
      records_failed: 0,
      duration_seconds: 600,
      streams: [
        { name: 'users', records_synced: 45000, records_failed: 0, status: 'completed' },
        { name: 'orders', records_synced: 80000, records_failed: 0, status: 'completed' },
      ],
    },
    {
      id: '2',
      source_name: 'Salesforce CRM',
      source_type: 'salesforce',
      status: 'completed',
      started_at: new Date(now - 3600000).toISOString(),
      completed_at: new Date(now - 3000000).toISOString(),
      records_synced: 8500,
      records_failed: 0,
      duration_seconds: 600,
      streams: [
        { name: 'accounts', records_synced: 3000, records_failed: 0, status: 'completed' },
        { name: 'contacts', records_synced: 5500, records_failed: 0, status: 'completed' },
      ],
    },
    {
      id: '3',
      source_name: 'Stripe Payments',
      source_type: 'stripe',
      status: 'failed',
      started_at: new Date(now - 7200000).toISOString(),
      completed_at: new Date(now - 7000000).toISOString(),
      records_synced: 2300,
      records_failed: 150,
      duration_seconds: 200,
      error_message: 'Authentication failed: Invalid API key',
      streams: [
        { name: 'charges', records_synced: 2300, records_failed: 0, status: 'completed' },
        { name: 'refunds', records_synced: 0, records_failed: 150, status: 'failed' },
      ],
    },
  ];
}
