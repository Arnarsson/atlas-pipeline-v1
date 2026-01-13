import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Clock,
  CheckCircle,
  XCircle,
  BarChart3,
  ArrowRight,
  RefreshCw,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface ThroughputMetric {
  period: string;
  cases_submitted: number;
  cases_resolved: number;
  cases_pending: number;
  avg_daily_throughput: number;
  trend_percent: number;
}

interface LeadTimeMetric {
  period: string;
  avg_lead_time_hours: number;
  median_lead_time_hours: number;
  p95_lead_time_hours: number;
  trend_percent: number;
}

interface ApprovalMetric {
  period: string;
  total_resolved: number;
  approved: number;
  rejected: number;
  approval_rate: number;
  trend_percent: number;
}

interface RejectionReason {
  reason: string;
  count: number;
  percentage: number;
}

interface RejectionMetric {
  period: string;
  total_rejections: number;
  reasons: RejectionReason[];
  top_reason: string | null;
}

interface KPISummary {
  period: string;
  throughput: ThroughputMetric;
  lead_time: LeadTimeMetric;
  approval: ApprovalMetric;
  rejections: RejectionMetric;
}

interface BeforeAfterComparison {
  metric_name: string;
  before_value: number;
  after_value: number;
  change_absolute: number;
  change_percent: number;
  improvement: boolean;
}

interface KPIDashboardResponse {
  generated_at: string;
  period: string;
  current: KPISummary;
  previous: KPISummary | null;
  before_after: BeforeAfterComparison[];
}

const API_BASE = 'http://localhost:8000/api/v1';

type TimeRange = 'day' | 'week' | 'month' | 'quarter';

export default function KPIDashboard() {
  const [timeRange, setTimeRange] = useState<TimeRange>('week');

  const { data: dashboard, isLoading, refetch } = useQuery<KPIDashboardResponse>({
    queryKey: ['kpi-dashboard', timeRange],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/kpi/dashboard?period=${timeRange}`);
      if (!res.ok) throw new Error('Failed to fetch KPI data');
      return res.json();
    },
  });

  const formatPercent = (value: number) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value.toFixed(1)}%`;
  };

  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    return `${hours.toFixed(1)}h`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">
            KPI Dashboard
          </h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Before/after automation impact metrics
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Time Range Selector */}
          <div className="flex items-center gap-1 bg-[hsl(var(--secondary))] rounded-lg p-1">
            {(['day', 'week', 'month', 'quarter'] as TimeRange[]).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                  timeRange === range
                    ? 'bg-[hsl(var(--background))] text-[hsl(var(--foreground))] shadow-sm'
                    : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                }`}
              >
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </button>
            ))}
          </div>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <RefreshCw className="h-6 w-6 animate-spin text-[hsl(var(--muted-foreground))]" />
        </div>
      ) : dashboard ? (
        <>
          {/* Before/After Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {dashboard.before_after.map((comparison) => (
              <Card key={comparison.metric_name}>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-[hsl(var(--muted-foreground))]">
                    {comparison.metric_name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center justify-between">
                    <div className="text-center">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Before</p>
                      <p className="text-lg font-semibold text-[hsl(var(--foreground))]">
                        {comparison.before_value.toFixed(1)}
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                    <div className="text-center">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">After</p>
                      <p className="text-lg font-semibold text-[hsl(var(--foreground))]">
                        {comparison.after_value.toFixed(1)}
                      </p>
                    </div>
                  </div>
                  <div className={`mt-2 flex items-center justify-center gap-1 text-sm ${
                    comparison.improvement ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {comparison.improvement ? (
                      <TrendingUp className="h-4 w-4" />
                    ) : (
                      <TrendingDown className="h-4 w-4" />
                    )}
                    {formatPercent(comparison.change_percent)}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Main KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Throughput */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Throughput
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-[hsl(var(--foreground))]">
                      {dashboard.current.throughput.cases_submitted}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Submitted</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-green-600">
                      {dashboard.current.throughput.cases_resolved}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Resolved</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-yellow-600">
                      {dashboard.current.throughput.cases_pending}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Pending</p>
                  </div>
                </div>
                <div className="pt-4 border-t border-[hsl(var(--border))]">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">
                      Avg Daily Throughput
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">
                        {dashboard.current.throughput.avg_daily_throughput.toFixed(1)}
                      </span>
                      <span className={`text-xs ${
                        dashboard.current.throughput.trend_percent >= 0
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}>
                        {formatPercent(dashboard.current.throughput.trend_percent)}
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Lead Time */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Lead Time
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-[hsl(var(--foreground))]">
                      {formatHours(dashboard.current.lead_time.avg_lead_time_hours)}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Average</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-blue-600">
                      {formatHours(dashboard.current.lead_time.median_lead_time_hours)}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Median</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-orange-600">
                      {formatHours(dashboard.current.lead_time.p95_lead_time_hours)}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">P95</p>
                  </div>
                </div>
                <div className="pt-4 border-t border-[hsl(var(--border))]">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">
                      Trend vs Previous
                    </span>
                    <span className={`text-sm font-medium ${
                      dashboard.current.lead_time.trend_percent <= 0
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}>
                      {formatPercent(dashboard.current.lead_time.trend_percent)}
                      {dashboard.current.lead_time.trend_percent <= 0 ? ' faster' : ' slower'}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Approval Rate */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  Approval Rate
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center">
                  <div className="relative w-32 h-32">
                    <svg className="w-full h-full transform -rotate-90">
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        fill="none"
                        stroke="hsl(var(--secondary))"
                        strokeWidth="12"
                      />
                      <circle
                        cx="64"
                        cy="64"
                        r="56"
                        fill="none"
                        stroke="rgb(34, 197, 94)"
                        strokeWidth="12"
                        strokeDasharray={`${dashboard.current.approval.approval_rate * 352} 352`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-2xl font-bold">
                        {Math.round(dashboard.current.approval.approval_rate * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-[hsl(var(--border))]">
                  <div className="text-center">
                    <p className="text-lg font-semibold text-green-600">
                      {dashboard.current.approval.approved}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Approved</p>
                  </div>
                  <div className="text-center">
                    <p className="text-lg font-semibold text-red-600">
                      {dashboard.current.approval.rejected}
                    </p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">Rejected</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Rejection Reasons */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <XCircle className="h-5 w-5" />
                  Rejection Reasons
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {dashboard.current.rejections.reasons.map((reason, index) => (
                    <div key={reason.reason} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[hsl(var(--foreground))]">
                          {index + 1}. {reason.reason}
                        </span>
                        <span className="text-[hsl(var(--muted-foreground))]">
                          {reason.count} ({reason.percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
                        <div
                          className="h-full bg-red-500/70 rounded-full"
                          style={{ width: `${reason.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
                {dashboard.current.rejections.top_reason && (
                  <p className="mt-4 text-xs text-[hsl(var(--muted-foreground))]">
                    Top reason: <span className="font-medium">{dashboard.current.rejections.top_reason}</span>
                  </p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Period Info */}
          <div className="flex items-center justify-center gap-2 text-sm text-[hsl(var(--muted-foreground))]">
            <Calendar className="h-4 w-4" />
            <span>
              Data for: {dashboard.period} • Generated: {new Date(dashboard.generated_at).toLocaleString()}
            </span>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
          <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
          <p>No KPI data available</p>
        </div>
      )}
    </div>
  );
}
