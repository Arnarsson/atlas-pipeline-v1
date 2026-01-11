import {
  Activity,
  CheckCircle,
  Database,
  Target,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { motion } from 'framer-motion';
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
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="bg-gradient-to-br from-primary-500 via-blue-600 to-primary-700 rounded-2xl shadow-2xl p-8 text-white border-4 border-white"
        data-testid="overall-score"
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-extrabold mb-3 flex items-center gap-2">
              Overall Quality Score
              <TrendingUp className="h-7 w-7" />
            </h2>
            <p className="text-blue-100 font-semibold">
              Run ID: {metrics.run_id}
            </p>
          </div>
          <div className="text-right">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
              className="text-7xl font-extrabold mb-3 drop-shadow-lg"
              data-testid="overall-score-percentage"
            >
              {overallPercentage}%
            </motion.div>
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className={`inline-flex items-center gap-2 px-5 py-2 rounded-full border-2 border-white shadow-lg ${
                isHealthy ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            >
              {isHealthy ? (
                <>
                  <CheckCircle className="h-6 w-6" />
                  <span className="font-bold text-lg">Healthy</span>
                </>
              ) : (
                <>
                  <Activity className="h-6 w-6" />
                  <span className="font-bold text-lg">Needs Attention</span>
                </>
              )}
            </motion.div>
          </div>
        </div>

        {/* Radial Progress */}
        <div className="mt-8">
          <div className="relative w-full h-6 bg-white/20 rounded-full overflow-hidden shadow-inner">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${overallPercentage}%` }}
              transition={{ duration: 1.5, ease: 'easeOut', delay: 0.5 }}
              className="absolute top-0 left-0 h-full bg-gradient-to-r from-white via-green-200 to-white"
            >
              <motion.div
                animate={{
                  x: ['-100%', '200%'],
                }}
                transition={{
                  duration: 2,
                  repeat: Infinity,
                  ease: 'linear',
                }}
                className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent"
                style={{ width: '50%' }}
              />
            </motion.div>
          </div>
        </div>
      </motion.div>

      {/* Dimension Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" data-testid="quality-dimensions">
        {Object.entries(metrics.dimensions).map(([dimension, dimMetrics], idx) => (
          <motion.div
            key={dimension}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.6 + idx * 0.1 }}
          >
            <DimensionCard
              title={dimension.charAt(0).toUpperCase() + dimension.slice(1)}
              metrics={dimMetrics}
              icon={dimensionIcons[dimension as keyof typeof dimensionIcons]}
            />
          </motion.div>
        ))}
      </div>

      {/* Column-Level Metrics */}
      {metrics.column_metrics && Object.keys(metrics.column_metrics).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 1.2 }}
          className="bg-white rounded-2xl shadow-xl p-6 border-2 border-gray-200"
        >
          <h3 className="text-xl font-bold text-gray-900 mb-6 flex items-center gap-2">
            <Database className="h-6 w-6 text-primary-600" />
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
                  <motion.tr
                    key={column}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                    whileHover={{ backgroundColor: '#f9fafb', scale: 1.01 }}
                    className="transition-colors"
                  >
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
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}
