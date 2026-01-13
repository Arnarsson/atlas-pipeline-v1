import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Calendar,
  Plus,
  Play,
  Pause,
  Trash2,
  Clock,
  CheckCircle,
  Database,
  MoreVertical,
} from 'lucide-react';
import { api } from '@/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import toast from 'react-hot-toast';

interface Schedule {
  id: string;
  name: string;
  source_name: string;
  source_type: string;
  cron_expression: string;
  timezone: string;
  is_enabled: boolean;
  last_run?: string;
  next_run?: string;
  created_at: string;
}

const CRON_PRESETS = [
  { label: 'Every hour', value: '0 * * * *' },
  { label: 'Every 6 hours', value: '0 */6 * * *' },
  { label: 'Daily at midnight', value: '0 0 * * *' },
  { label: 'Daily at 6am', value: '0 6 * * *' },
  { label: 'Weekly on Sunday', value: '0 0 * * 0' },
  { label: 'Monthly on 1st', value: '0 0 1 * *' },
];

export default function Schedules() {
  const queryClient = useQueryClient();
  const [activeMenu, setActiveMenu] = useState<string | null>(null);

  const { data: schedules, isLoading } = useQuery({
    queryKey: ['schedules'],
    queryFn: async () => {
      try {
        const response = await api.get('/atlas-intelligence/sync/schedules');
        return response.data as Schedule[];
      } catch {
        return getMockSchedules();
      }
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, enabled }: { id: string; enabled: boolean }) => {
      await api.put(`/atlas-intelligence/sync/schedules/${id}`, { is_enabled: enabled });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
      toast.success('Schedule updated');
    },
    onError: () => {
      toast.error('Failed to update schedule');
    },
  });

  const runNowMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/atlas-intelligence/sync/schedules/${id}/run`);
    },
    onSuccess: () => {
      toast.success('Sync triggered');
      queryClient.invalidateQueries({ queryKey: ['sync-jobs'] });
    },
    onError: () => {
      toast.error('Failed to trigger sync');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/atlas-intelligence/sync/schedules/${id}`);
    },
    onSuccess: () => {
      toast.success('Schedule deleted');
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
    onError: () => {
      toast.error('Failed to delete schedule');
    },
  });

  const formatCron = (cron: string) => {
    const preset = CRON_PRESETS.find((p) => p.value === cron);
    return preset?.label || cron;
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
    return `${Math.floor(hours / 24)}d ago`;
  };

  const formatNextRun = (dateStr?: string) => {
    if (!dateStr) return 'Not scheduled';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = date.getTime() - now.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Soon';
    if (mins < 60) return `In ${mins}m`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `In ${hours}h`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  const enabledCount = schedules?.filter((s) => s.is_enabled).length || 0;
  const disabledCount = schedules?.filter((s) => !s.is_enabled).length || 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Schedules</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Configure automated sync schedules for your connections
          </p>
        </div>
        <Link to="/connections">
          <Button variant="outline" size="sm">
            <Plus className="h-4 w-4 mr-2" />
            Create Schedule
          </Button>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total</p>
                <p className="text-2xl font-bold text-[hsl(var(--foreground))]">{schedules?.length || 0}</p>
              </div>
              <Calendar className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Enabled</p>
                <p className="text-2xl font-bold text-green-600">{enabledCount}</p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Paused</p>
                <p className="text-2xl font-bold text-[hsl(var(--muted-foreground))]">{disabledCount}</p>
              </div>
              <Pause className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Schedules List */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-medium">Active Schedules</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="divide-y divide-[hsl(var(--border))]">
            {schedules && schedules.length > 0 ? (
              schedules.map((schedule) => (
                <div
                  key={schedule.id}
                  className="flex items-center justify-between p-4 hover:bg-[hsl(var(--secondary)/0.3)] transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${schedule.is_enabled ? 'bg-green-500/10' : 'bg-[hsl(var(--secondary))]'}`}>
                      <Database className={`h-5 w-5 ${schedule.is_enabled ? 'text-green-500' : 'text-[hsl(var(--muted-foreground))]'}`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">{schedule.source_name}</h3>
                      <div className="flex items-center gap-2 text-xs text-[hsl(var(--muted-foreground))]">
                        <Clock className="h-3 w-3" />
                        {formatCron(schedule.cron_expression)}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    <div className="hidden sm:block text-right">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Next run</p>
                      <p className="text-sm text-[hsl(var(--foreground))]">{formatNextRun(schedule.next_run)}</p>
                    </div>

                    <div className="hidden md:block text-right">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Last run</p>
                      <p className="text-sm text-[hsl(var(--foreground))]">{formatTimeAgo(schedule.last_run)}</p>
                    </div>

                    {/* Toggle Switch */}
                    <button
                      onClick={() => toggleMutation.mutate({ id: schedule.id, enabled: !schedule.is_enabled })}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        schedule.is_enabled ? 'bg-green-500' : 'bg-[hsl(var(--secondary))]'
                      }`}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          schedule.is_enabled ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>

                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => runNowMutation.mutate(schedule.id)}
                        disabled={!schedule.is_enabled}
                      >
                        <Play className="h-4 w-4" />
                      </Button>

                      <div className="relative">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setActiveMenu(activeMenu === schedule.id ? null : schedule.id)}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>

                        {activeMenu === schedule.id && (
                          <div className="absolute right-0 top-full mt-1 w-40 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--card))] shadow-lg z-10">
                            <button
                              onClick={() => deleteMutation.mutate(schedule.id)}
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
                <Calendar className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
                <h3 className="mt-4 text-lg font-medium text-[hsl(var(--foreground))]">No schedules</h3>
                <p className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                  Create a schedule to automate your data syncs
                </p>
                <Link to="/connections">
                  <Button className="mt-4">
                    <Plus className="h-4 w-4 mr-2" />
                    Create Schedule
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

function getMockSchedules(): Schedule[] {
  const now = Date.now();
  return [
    {
      id: '1',
      name: 'PostgreSQL Hourly',
      source_name: 'PostgreSQL Production',
      source_type: 'postgresql',
      cron_expression: '0 * * * *',
      timezone: 'UTC',
      is_enabled: true,
      last_run: new Date(now - 1800000).toISOString(),
      next_run: new Date(now + 1800000).toISOString(),
      created_at: '2024-01-15T10:00:00Z',
    },
    {
      id: '2',
      name: 'Salesforce Daily',
      source_name: 'Salesforce CRM',
      source_type: 'salesforce',
      cron_expression: '0 6 * * *',
      timezone: 'America/New_York',
      is_enabled: true,
      last_run: new Date(now - 43200000).toISOString(),
      next_run: new Date(now + 43200000).toISOString(),
      created_at: '2024-02-20T14:30:00Z',
    },
    {
      id: '3',
      name: 'Stripe Weekly',
      source_name: 'Stripe Payments',
      source_type: 'stripe',
      cron_expression: '0 0 * * 0',
      timezone: 'UTC',
      is_enabled: false,
      last_run: new Date(now - 604800000).toISOString(),
      next_run: undefined,
      created_at: '2024-01-10T09:00:00Z',
    },
  ];
}
