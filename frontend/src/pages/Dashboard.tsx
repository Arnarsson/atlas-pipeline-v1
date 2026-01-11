import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Activity,
  Database,
  Shield,
  TrendingUp,
  ArrowRight,
  Clock,
} from 'lucide-react';
import { getDashboardStats } from '@/api/client';

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: getDashboardStats,
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: false, // Don't retry if endpoint doesn't exist
    onError: () => {
      // Silently handle errors - dashboard will show zeros
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Pipeline Runs',
      value: stats?.total_runs || 0,
      icon: Activity,
      color: 'bg-blue-500',
      subtitle: 'All time',
      link: '/reports',
    },
    {
      name: 'Avg Quality Score',
      value: `${Math.round((stats?.avg_quality_score || 0) * 100)}%`,
      icon: TrendingUp,
      color: 'bg-green-500',
      subtitle: 'Last 30 days',
      link: '/reports',
    },
    {
      name: 'PII Detections',
      value: stats?.total_pii_detections || 0,
      icon: Shield,
      color: 'bg-purple-500',
      subtitle: 'Total fields',
      link: '/pii',
    },
    {
      name: 'Active Connectors',
      value: stats?.active_connectors || 0,
      icon: Database,
      color: 'bg-orange-500',
      subtitle: 'Enabled',
      link: '/connectors',
    },
    {
      name: 'Feature Groups',
      value: stats?.total_feature_groups || 0,
      icon: Database,
      color: 'bg-indigo-500',
      subtitle: 'Registered',
      link: '/features',
    },
    {
      name: 'GDPR Requests',
      value: stats?.pending_gdpr_requests || 0,
      icon: Shield,
      color: 'bg-red-500',
      subtitle: 'Pending',
      link: '/gdpr',
    },
    {
      name: 'Catalog Datasets',
      value: stats?.catalog_datasets || 0,
      icon: Database,
      color: 'bg-teal-500',
      subtitle: 'In catalog',
      link: '/catalog',
    },
    {
      name: 'Avg Lineage Depth',
      value: `${stats?.avg_lineage_depth || 0} levels`,
      icon: Activity,
      color: 'bg-cyan-500',
      subtitle: 'Transformations',
      link: '/lineage',
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-8 shadow-2xl border-4 border-white">
        <h1 className="text-4xl font-extrabold text-white drop-shadow-lg">Dashboard</h1>
        <p className="mt-3 text-lg text-indigo-100 font-semibold">
          Welcome to Atlas Data Pipeline Platform - Your Data Command Center
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div
            key={stat.name}
            className="bg-white overflow-hidden shadow-2xl rounded-2xl hover:shadow-3xl transition-all hover:scale-105 border-4 border-gray-200 hover:border-indigo-400"
          >
            <div className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`p-4 rounded-xl ${stat.color} shadow-lg`}>
                    <stat.icon className="h-8 w-8 text-white" />
                  </div>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-bold text-gray-700 truncate uppercase tracking-wide">
                      {stat.name}
                    </dt>
                    <dd>
                      <div className="text-3xl font-extrabold bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                        {stat.value}
                      </div>
                      <div className="mt-1 text-xs font-semibold text-gray-600 uppercase">
                        {stat.subtitle}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Runs */}
      <div className="bg-white shadow-md rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Recent Pipeline Runs</h2>
          <Link
            to="/reports"
            className="text-sm font-medium text-primary-600 hover:text-primary-500 flex items-center gap-1"
          >
            View all
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="divide-y divide-gray-200">
          {stats?.recent_runs && stats.recent_runs.length > 0 ? (
            stats.recent_runs.map((run) => (
              <div
                key={run.run_id}
                className="px-6 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-sm font-medium text-gray-900">
                        {run.dataset_name}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          run.status === 'completed'
                            ? 'bg-green-100 text-green-800'
                            : run.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : run.status === 'running'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {run.status}
                      </span>
                    </div>
                    <div className="mt-1 flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {run.created_at ? new Date(run.created_at).toLocaleString() : 'N/A'}
                      </span>
                      {run.quality_score !== undefined && (
                        <span className="font-medium">
                          Quality: {Math.round(run.quality_score * 100)}%
                        </span>
                      )}
                      {run.pii_detections !== undefined && run.pii_detections > 0 && (
                        <span className="text-purple-600 font-medium">
                          {run.pii_detections} PII detections
                        </span>
                      )}
                    </div>
                  </div>
                  <Link
                    to={`/reports/${run.run_id}`}
                    className="ml-4 text-sm font-medium text-primary-600 hover:text-primary-500"
                  >
                    View Details
                  </Link>
                </div>
              </div>
            ))
          ) : (
            <div className="px-6 py-12 text-center">
              <Activity className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No recent runs</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by uploading a CSV file.
              </p>
              <div className="mt-6">
                <Link
                  to="/upload"
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                >
                  Upload CSV
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          to="/upload"
          className="block p-6 bg-gradient-to-br from-primary-500 to-primary-600 rounded-lg shadow-md hover:shadow-lg transition-all hover:-translate-y-1"
        >
          <div className="text-white">
            <h3 className="text-lg font-semibold mb-2">Upload CSV</h3>
            <p className="text-sm text-primary-100">
              Process new data with quality validation and PII detection
            </p>
          </div>
        </Link>

        <Link
          to="/catalog"
          className="block p-6 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg shadow-md hover:shadow-lg transition-all hover:-translate-y-1"
        >
          <div className="text-white">
            <h3 className="text-lg font-semibold mb-2">Data Catalog</h3>
            <p className="text-sm text-teal-100">
              Browse and search all datasets in the pipeline
            </p>
          </div>
        </Link>

        <Link
          to="/features"
          className="block p-6 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-lg shadow-md hover:shadow-lg transition-all hover:-translate-y-1"
        >
          <div className="text-white">
            <h3 className="text-lg font-semibold mb-2">Feature Store</h3>
            <p className="text-sm text-indigo-100">
              Manage ML features with versioning and exports
            </p>
          </div>
        </Link>

        <Link
          to="/gdpr"
          className="block p-6 bg-gradient-to-br from-red-500 to-red-600 rounded-lg shadow-md hover:shadow-lg transition-all hover:-translate-y-1"
        >
          <div className="text-white">
            <h3 className="text-lg font-semibold mb-2">GDPR Compliance</h3>
            <p className="text-sm text-red-100">
              Manage data subject access and deletion requests
            </p>
          </div>
        </Link>
      </div>
    </div>
  );
}
