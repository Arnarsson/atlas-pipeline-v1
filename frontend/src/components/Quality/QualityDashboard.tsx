import {
  Activity,
  CheckCircle,
  Database,
  Target,
  Clock,
  TrendingUp,
} from 'lucide-react';
import DimensionCard from './DimensionCard';
import type { QualityMetrics } from '@/types';

interface QualityDashboardProps {
  metrics: QualityMetrics;
}

const dimensionIcons = {
  completeness: Database,
  uniqueness: CheckCircle,
  validity: Target,
  consistency: Activity,
  accuracy: TrendingUp,
  timeliness: Clock,
};

export default function QualityDashboard({ metrics }: QualityDashboardProps) {
  const overallPercentage = Math.round(metrics.overall_score * 100);
  const isHealthy = metrics.overall_score >= 0.9;

  return (
    <div className="space-y-6" data-testid="quality-dashboard">
      {/* Overall Score */}
      <div className="bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl shadow-lg p-8 text-white" data-testid="overall-score">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">Overall Quality Score</h2>
            <p className="text-primary-100">
              Run ID: {metrics.run_id}
            </p>
          </div>
          <div className="text-right">
            <div className="text-6xl font-bold mb-2" data-testid="overall-score-percentage">{overallPercentage}%</div>
            <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${
              isHealthy ? 'bg-green-500' : 'bg-yellow-500'
            }`}>
              {isHealthy ? (
                <>
                  <CheckCircle className="h-5 w-5" />
                  <span className="font-semibold">Healthy</span>
                </>
              ) : (
                <>
                  <Activity className="h-5 w-5" />
                  <span className="font-semibold">Needs Attention</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Radial Progress */}
        <div className="mt-6">
          <div className="relative w-full h-4 bg-white/20 rounded-full overflow-hidden">
            <div
              className="absolute top-0 left-0 h-full bg-white transition-all duration-1000 ease-out"
              style={{ width: `${overallPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Dimension Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="quality-dimensions">
        {Object.entries(metrics.dimensions).map(([dimension, dimMetrics]) => (
          <DimensionCard
            key={dimension}
            title={dimension.charAt(0).toUpperCase() + dimension.slice(1)}
            metrics={dimMetrics}
            icon={dimensionIcons[dimension as keyof typeof dimensionIcons]}
          />
        ))}
      </div>

      {/* Column-Level Metrics */}
      {metrics.column_metrics && Object.keys(metrics.column_metrics).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Column-Level Quality Metrics
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Column
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Data Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Completeness
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Uniqueness
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Validity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Nulls
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {Object.entries(metrics.column_metrics).map(([column, colMetrics]) => (
                  <tr key={column} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {column}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {colMetrics.data_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500"
                            style={{ width: `${colMetrics.completeness * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-700">
                          {Math.round(colMetrics.completeness * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{ width: `${colMetrics.uniqueness * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-700">
                          {Math.round(colMetrics.uniqueness * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-purple-500"
                            style={{ width: `${colMetrics.validity * 100}%` }}
                          />
                        </div>
                        <span className="text-sm text-gray-700">
                          {Math.round(colMetrics.validity * 100)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {colMetrics.null_count}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
