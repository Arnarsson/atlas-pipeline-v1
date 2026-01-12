import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  RefreshCw,
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  Clock,
  Calendar,
  Trash2,
  ChevronDown,
  ChevronUp,
  Activity,
  BarChart3,
  Timer,
  AlertCircle,
  Eye
} from 'lucide-react';
import toast from 'react-hot-toast';
import { api } from '@/api/client';
import SyncResultModal from './SyncResultModal';

// Types
interface SyncJob {
  job_id: string;
  source_id: string;
  source_name: string;
  streams: string[];
  sync_mode: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  records_synced: number;
  error_message: string | null;
}

interface ScheduledSync {
  schedule_id: string;
  source_id: string;
  source_name: string;
  streams: string[];
  sync_mode: string;
  cron_expression: string;
  enabled: boolean;
  created_at: string;
  last_run_at: string | null;
  next_run_at: string | null;
  run_count: number;
}

interface SyncStats {
  total_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_records_synced: number;
  active_schedules: number;
  total_schedules: number;
  max_concurrent_jobs: number;
}

interface SyncStatusPanelProps {
  onClose?: () => void;
}

// API functions
const getSyncStats = async (): Promise<SyncStats> => {
  const response = await api.get('/atlas-intelligence/sync/stats');
  return response.data;
};

const getRunningJobs = async (): Promise<SyncJob[]> => {
  const response = await api.get('/atlas-intelligence/sync/running');
  return response.data;
};

const getJobHistory = async (limit: number = 20): Promise<SyncJob[]> => {
  const response = await api.get(`/atlas-intelligence/sync/jobs?limit=${limit}`);
  return response.data;
};

const getSchedules = async (): Promise<ScheduledSync[]> => {
  const response = await api.get('/atlas-intelligence/sync/schedules');
  return response.data;
};

const cancelJob = async (jobId: string) => {
  const response = await api.post(`/atlas-intelligence/sync/jobs/${jobId}/cancel`);
  return response.data;
};

const runSchedule = async (scheduleId: string) => {
  const response = await api.post(`/atlas-intelligence/sync/schedules/${scheduleId}/run`);
  return response.data;
};

const updateSchedule = async ({ scheduleId, enabled }: { scheduleId: string; enabled: boolean }) => {
  const response = await api.put(`/atlas-intelligence/sync/schedules/${scheduleId}`, { enabled });
  return response.data;
};

const deleteSchedule = async (scheduleId: string) => {
  const response = await api.delete(`/atlas-intelligence/sync/schedules/${scheduleId}`);
  return response.data;
};

const getSyncJobResult = async (jobId: string) => {
  const response = await api.get(`/atlas-intelligence/sync/jobs/${jobId}/result`);
  return response.data;
};

export default function SyncStatusPanel(_props: SyncStatusPanelProps) {
  const [activeSection, setActiveSection] = useState<'overview' | 'jobs' | 'schedules'>('overview');
  const [expandedJob, setExpandedJob] = useState<string | null>(null);
  const [selectedJobResult, setSelectedJobResult] = useState<any | null>(null);
  const queryClient = useQueryClient();

  // Queries
  const { data: stats, isLoading: loadingStats } = useQuery({
    queryKey: ['sync-stats'],
    queryFn: getSyncStats,
    refetchInterval: 5000,
  });

  const { data: runningJobs = [] } = useQuery({
    queryKey: ['sync-running'],
    queryFn: getRunningJobs,
    refetchInterval: 3000,
  });

  const { data: jobHistory = [], isLoading: loadingHistory } = useQuery({
    queryKey: ['sync-history'],
    queryFn: () => getJobHistory(20),
    refetchInterval: 10000,
  });

  const { data: schedules = [], isLoading: loadingSchedules } = useQuery({
    queryKey: ['sync-schedules'],
    queryFn: getSchedules,
    refetchInterval: 30000,
  });

  // Mutations
  const cancelMutation = useMutation({
    mutationFn: cancelJob,
    onSuccess: () => {
      toast.success('Job cancelled');
      queryClient.invalidateQueries({ queryKey: ['sync-running'] });
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
    },
    onError: () => {
      toast.error('Failed to cancel job');
    },
  });

  const runScheduleMutation = useMutation({
    mutationFn: runSchedule,
    onSuccess: () => {
      toast.success('Schedule triggered');
      queryClient.invalidateQueries({ queryKey: ['sync-running'] });
      queryClient.invalidateQueries({ queryKey: ['sync-schedules'] });
    },
    onError: () => {
      toast.error('Failed to trigger schedule');
    },
  });

  const toggleScheduleMutation = useMutation({
    mutationFn: updateSchedule,
    onSuccess: (_, variables) => {
      toast.success(variables.enabled ? 'Schedule enabled' : 'Schedule disabled');
      queryClient.invalidateQueries({ queryKey: ['sync-schedules'] });
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
    },
    onError: () => {
      toast.error('Failed to update schedule');
    },
  });

  const deleteScheduleMutation = useMutation({
    mutationFn: deleteSchedule,
    onSuccess: () => {
      toast.success('Schedule deleted');
      queryClient.invalidateQueries({ queryKey: ['sync-schedules'] });
      queryClient.invalidateQueries({ queryKey: ['sync-stats'] });
    },
    onError: () => {
      toast.error('Failed to delete schedule');
    },
  });

  const fetchJobResultMutation = useMutation({
    mutationFn: getSyncJobResult,
    onSuccess: (data) => {
      setSelectedJobResult(data);
    },
    onError: () => {
      toast.error('Failed to fetch job results');
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'cancelled':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />;
      default:
        return <Clock className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      running: 'bg-blue-500/10 text-blue-600',
      completed: 'bg-green-500/10 text-green-600',
      failed: 'bg-red-500/10 text-red-600',
      cancelled: 'bg-yellow-500/10 text-yellow-600',
      pending: 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]',
    };
    return styles[status] || styles.pending;
  };

  const formatDuration = (seconds: number | null) => {
    if (seconds === null) return '-';
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
    return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const formatCron = (cron: string) => {
    // Simple cron description
    const parts = cron.split(' ');
    if (parts.length < 5) return cron;
    const [min, hour] = parts;
    if (min === '*' && hour === '*') return 'Every minute';
    if (min === '0' && hour === '*') return 'Every hour';
    if (min === '0' && hour === '0') return 'Daily at midnight';
    if (min.match(/^\d+$/) && hour === '*') return `Every hour at :${min.padStart(2, '0')}`;
    return cron;
  };

  return (
    <div className="space-y-4">
      {/* Section Navigation */}
      <div className="flex gap-2 border-b border-[hsl(var(--border))] pb-2">
        <Button
          size="sm"
          variant={activeSection === 'overview' ? 'default' : 'ghost'}
          onClick={() => setActiveSection('overview')}
        >
          <BarChart3 className="w-4 h-4 mr-1" />
          Overview
        </Button>
        <Button
          size="sm"
          variant={activeSection === 'jobs' ? 'default' : 'ghost'}
          onClick={() => setActiveSection('jobs')}
        >
          <Activity className="w-4 h-4 mr-1" />
          Jobs
          {runningJobs.length > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs rounded-full bg-blue-500 text-white">
              {runningJobs.length}
            </span>
          )}
        </Button>
        <Button
          size="sm"
          variant={activeSection === 'schedules' ? 'default' : 'ghost'}
          onClick={() => setActiveSection('schedules')}
        >
          <Calendar className="w-4 h-4 mr-1" />
          Schedules
          <span className="ml-1 px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--secondary))]">
            {schedules.length}
          </span>
        </Button>
      </div>

      {/* Overview Section */}
      {activeSection === 'overview' && (
        <div className="space-y-4">
          {/* Stats Grid */}
          {loadingStats ? (
            <div className="text-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[hsl(var(--muted-foreground))]" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Running Jobs</p>
                      <p className="text-2xl font-semibold text-blue-600">
                        {stats?.running_jobs || 0}
                      </p>
                    </div>
                    <RefreshCw className={`w-6 h-6 text-blue-500 ${(stats?.running_jobs || 0) > 0 ? 'animate-spin' : ''}`} />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Completed</p>
                      <p className="text-2xl font-semibold text-green-600">
                        {stats?.completed_jobs || 0}
                      </p>
                    </div>
                    <CheckCircle2 className="w-6 h-6 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Failed</p>
                      <p className="text-2xl font-semibold text-red-600">
                        {stats?.failed_jobs || 0}
                      </p>
                    </div>
                    <XCircle className="w-6 h-6 text-red-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Records Synced</p>
                      <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                        {(stats?.total_records_synced || 0).toLocaleString()}
                      </p>
                    </div>
                    <BarChart3 className="w-6 h-6 text-[hsl(var(--muted-foreground))]" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Running Jobs Quick View */}
          {runningJobs.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h4 className="text-sm font-medium text-[hsl(var(--foreground))] mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Running Now
                </h4>
                <div className="space-y-2">
                  {runningJobs.map((job) => (
                    <div
                      key={job.job_id}
                      className="flex items-center justify-between p-2 bg-blue-500/5 rounded-lg border border-blue-500/10"
                    >
                      <div className="flex items-center gap-3">
                        <RefreshCw className="w-4 h-4 animate-spin text-blue-500" />
                        <div>
                          <p className="text-sm font-medium text-[hsl(var(--foreground))]">
                            {job.source_name}
                          </p>
                          <p className="text-xs text-[hsl(var(--muted-foreground))]">
                            {job.streams.length} stream(s) - {job.records_synced.toLocaleString()} records
                          </p>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => cancelMutation.mutate(job.job_id)}
                        disabled={cancelMutation.isPending}
                      >
                        Cancel
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Active Schedules Quick View */}
          {schedules.filter(s => s.enabled).length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h4 className="text-sm font-medium text-[hsl(var(--foreground))] mb-3 flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  Active Schedules ({schedules.filter(s => s.enabled).length})
                </h4>
                <div className="space-y-2">
                  {schedules.filter(s => s.enabled).slice(0, 5).map((schedule) => (
                    <div
                      key={schedule.schedule_id}
                      className="flex items-center justify-between p-2 bg-[hsl(var(--secondary))] rounded-lg"
                    >
                      <div>
                        <p className="text-sm font-medium text-[hsl(var(--foreground))]">
                          {schedule.source_name}
                        </p>
                        <p className="text-xs text-[hsl(var(--muted-foreground))]">
                          {formatCron(schedule.cron_expression)} - Next: {formatDate(schedule.next_run_at)}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => runScheduleMutation.mutate(schedule.schedule_id)}
                        disabled={runScheduleMutation.isPending}
                      >
                        <Play className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Jobs Section */}
      {activeSection === 'jobs' && (
        <div className="space-y-4">
          {/* Running Jobs */}
          {runningJobs.length > 0 && (
            <Card>
              <CardContent className="p-4">
                <h4 className="text-sm font-medium text-[hsl(var(--foreground))] mb-3">
                  Running Jobs ({runningJobs.length})
                </h4>
                <div className="space-y-2">
                  {runningJobs.map((job) => (
                    <div
                      key={job.job_id}
                      className="p-3 border border-blue-500/20 bg-blue-500/5 rounded-lg"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(job.status)}
                          <span className="font-medium text-[hsl(var(--foreground))]">
                            {job.source_name}
                          </span>
                          <span className={`px-2 py-0.5 text-xs rounded ${getStatusBadge(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => cancelMutation.mutate(job.job_id)}
                          disabled={cancelMutation.isPending}
                        >
                          <Pause className="w-3 h-3 mr-1" />
                          Cancel
                        </Button>
                      </div>
                      <div className="mt-2 grid grid-cols-3 gap-4 text-xs text-[hsl(var(--muted-foreground))]">
                        <div>
                          <span className="block font-medium">Started</span>
                          {formatDate(job.started_at)}
                        </div>
                        <div>
                          <span className="block font-medium">Streams</span>
                          {job.streams.join(', ')}
                        </div>
                        <div>
                          <span className="block font-medium">Records</span>
                          {job.records_synced.toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Job History */}
          <Card>
            <CardContent className="p-4">
              <h4 className="text-sm font-medium text-[hsl(var(--foreground))] mb-3">
                Job History
              </h4>
              {loadingHistory ? (
                <div className="text-center py-8">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[hsl(var(--muted-foreground))]" />
                </div>
              ) : jobHistory.length > 0 ? (
                <div className="space-y-2">
                  {jobHistory.map((job) => (
                    <div
                      key={job.job_id}
                      className="border border-[hsl(var(--border))] rounded-lg overflow-hidden"
                    >
                      <button
                        onClick={() => setExpandedJob(expandedJob === job.job_id ? null : job.job_id)}
                        className="w-full p-3 flex items-center justify-between hover:bg-[hsl(var(--secondary))] transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          {getStatusIcon(job.status)}
                          <span className="font-medium text-[hsl(var(--foreground))]">
                            {job.source_name}
                          </span>
                          <span className={`px-2 py-0.5 text-xs rounded ${getStatusBadge(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-xs text-[hsl(var(--muted-foreground))]">
                            {job.records_synced.toLocaleString()} records
                          </span>
                          <span className="text-xs text-[hsl(var(--muted-foreground))]">
                            <Timer className="w-3 h-3 inline mr-1" />
                            {formatDuration(job.duration_seconds)}
                          </span>
                          {job.status === 'completed' && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={(e) => {
                                e.stopPropagation();
                                fetchJobResultMutation.mutate(job.job_id);
                              }}
                              disabled={fetchJobResultMutation.isPending}
                              title="View detailed results"
                            >
                              <Eye className="w-3 h-3" />
                            </Button>
                          )}
                          {expandedJob === job.job_id ? (
                            <ChevronUp className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                          )}
                        </div>
                      </button>
                      {expandedJob === job.job_id && (
                        <div className="px-3 pb-3 border-t border-[hsl(var(--border))] bg-[hsl(var(--secondary))]">
                          <div className="pt-3 grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                            <div>
                              <span className="block font-medium text-[hsl(var(--muted-foreground))]">Job ID</span>
                              <span className="text-[hsl(var(--foreground))] font-mono">{job.job_id}</span>
                            </div>
                            <div>
                              <span className="block font-medium text-[hsl(var(--muted-foreground))]">Sync Mode</span>
                              <span className="text-[hsl(var(--foreground))]">{job.sync_mode}</span>
                            </div>
                            <div>
                              <span className="block font-medium text-[hsl(var(--muted-foreground))]">Created</span>
                              <span className="text-[hsl(var(--foreground))]">{formatDate(job.created_at)}</span>
                            </div>
                            <div>
                              <span className="block font-medium text-[hsl(var(--muted-foreground))]">Completed</span>
                              <span className="text-[hsl(var(--foreground))]">{formatDate(job.completed_at)}</span>
                            </div>
                          </div>
                          <div className="mt-3">
                            <span className="block font-medium text-xs text-[hsl(var(--muted-foreground))]">Streams</span>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {job.streams.map((stream) => (
                                <span
                                  key={stream}
                                  className="px-2 py-0.5 text-xs bg-[hsl(var(--background))] rounded"
                                >
                                  {stream}
                                </span>
                              ))}
                            </div>
                          </div>
                          {job.error_message && (
                            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded text-xs text-red-600">
                              <span className="font-medium">Error:</span> {job.error_message}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-[hsl(var(--muted-foreground))]">
                  <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>No job history yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Schedules Section */}
      {activeSection === 'schedules' && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-medium text-[hsl(var(--foreground))]">
                Scheduled Syncs ({schedules.length})
              </h4>
            </div>
            {loadingSchedules ? (
              <div className="text-center py-8">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[hsl(var(--muted-foreground))]" />
              </div>
            ) : schedules.length > 0 ? (
              <div className="space-y-3">
                {schedules.map((schedule) => (
                  <div
                    key={schedule.schedule_id}
                    className={`p-4 border rounded-lg ${
                      schedule.enabled
                        ? 'border-[hsl(var(--border))]'
                        : 'border-[hsl(var(--border))] opacity-60'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Calendar className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        <span className="font-medium text-[hsl(var(--foreground))]">
                          {schedule.source_name}
                        </span>
                        {schedule.enabled ? (
                          <span className="px-2 py-0.5 text-xs rounded bg-green-500/10 text-green-600">
                            Active
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
                            Disabled
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => runScheduleMutation.mutate(schedule.schedule_id)}
                          disabled={runScheduleMutation.isPending}
                          title="Run now"
                        >
                          <Play className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => toggleScheduleMutation.mutate({
                            scheduleId: schedule.schedule_id,
                            enabled: !schedule.enabled
                          })}
                          disabled={toggleScheduleMutation.isPending}
                          title={schedule.enabled ? 'Disable' : 'Enable'}
                        >
                          {schedule.enabled ? (
                            <Pause className="w-3 h-3" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => {
                            if (confirm('Delete this schedule?')) {
                              deleteScheduleMutation.mutate(schedule.schedule_id);
                            }
                          }}
                          disabled={deleteScheduleMutation.isPending}
                          className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                          title="Delete"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div>
                        <span className="block font-medium text-[hsl(var(--muted-foreground))]">Schedule</span>
                        <span className="text-[hsl(var(--foreground))]">{formatCron(schedule.cron_expression)}</span>
                      </div>
                      <div>
                        <span className="block font-medium text-[hsl(var(--muted-foreground))]">Sync Mode</span>
                        <span className="text-[hsl(var(--foreground))]">{schedule.sync_mode}</span>
                      </div>
                      <div>
                        <span className="block font-medium text-[hsl(var(--muted-foreground))]">Last Run</span>
                        <span className="text-[hsl(var(--foreground))]">{formatDate(schedule.last_run_at)}</span>
                      </div>
                      <div>
                        <span className="block font-medium text-[hsl(var(--muted-foreground))]">Next Run</span>
                        <span className="text-[hsl(var(--foreground))]">{formatDate(schedule.next_run_at)}</span>
                      </div>
                    </div>
                    <div className="mt-3">
                      <span className="block font-medium text-xs text-[hsl(var(--muted-foreground))]">
                        Streams ({schedule.streams.length})
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {schedule.streams.slice(0, 5).map((stream) => (
                          <span
                            key={stream}
                            className="px-2 py-0.5 text-xs bg-[hsl(var(--secondary))] rounded"
                          >
                            {stream}
                          </span>
                        ))}
                        {schedule.streams.length > 5 && (
                          <span className="px-2 py-0.5 text-xs bg-[hsl(var(--secondary))] rounded">
                            +{schedule.streams.length - 5} more
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                      Run count: {schedule.run_count}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[hsl(var(--muted-foreground))]">
                <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>No scheduled syncs</p>
                <p className="text-xs mt-1">Configure a connector to set up automatic syncs</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sync Result Modal */}
      {selectedJobResult && (
        <SyncResultModal
          result={selectedJobResult}
          onClose={() => setSelectedJobResult(null)}
        />
      )}
    </div>
  );
}
