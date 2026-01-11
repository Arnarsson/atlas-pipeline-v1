import { Shield, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import type { PIIReport } from '@/types';

interface PIITableProps {
  report: PIIReport;
}

const getConfidenceBadge = (confidence?: number) => {
  if (confidence === undefined) {
    return 'bg-gray-100 text-gray-800';
  }
  if (confidence >= 0.95) {
    return 'bg-green-100 text-green-800';
  } else if (confidence >= 0.85) {
    return 'bg-yellow-100 text-yellow-800';
  } else {
    return 'bg-orange-100 text-orange-800';
  }
};

const getComplianceColor = (status: string) => {
  switch (status) {
    case 'compliant':
      return 'text-green-600 bg-green-100';
    case 'warning':
      return 'text-yellow-600 bg-yellow-100';
    case 'violation':
      return 'text-red-600 bg-red-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
};

export default function PIITable({ report }: PIITableProps) {
  return (
    <div className="space-y-6" data-testid="pii-table">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6" data-testid="pii-summary">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          whileHover={{ scale: 1.03 }}
          className="bg-gradient-to-br from-white to-purple-50 rounded-xl shadow-lg p-6 border-2 border-purple-200"
        >
          <div className="flex items-center gap-3">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.2 }}
              className="p-3 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-md"
            >
              <Shield className="h-7 w-7 text-white" />
            </motion.div>
            <div>
              <p className="text-sm text-gray-600 font-semibold">Total Detections</p>
              <motion.p
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.3 }}
                className="text-3xl font-extrabold text-gray-900"
                data-testid="pii-total-count"
              >
                {report.total_detections}
              </motion.p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          whileHover={{ scale: 1.03 }}
          className="bg-gradient-to-br from-white to-blue-50 rounded-xl shadow-lg p-6 border-2 border-blue-200"
        >
          <div className="flex items-center gap-3">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.3 }}
              className="p-3 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-md"
            >
              <AlertTriangle className="h-7 w-7 text-white" />
            </motion.div>
            <div>
              <p className="text-sm text-gray-600 font-semibold">PII Types Found</p>
              <motion.p
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.4 }}
                className="text-3xl font-extrabold text-gray-900"
              >
                {Object.keys(report.detections_by_type || {}).length}
              </motion.p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          whileHover={{ scale: 1.03 }}
          className="bg-gradient-to-br from-white to-green-50 rounded-xl shadow-lg p-6 border-2 border-green-200"
        >
          <div className="flex items-center gap-3">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.4 }}
              className={`p-3 rounded-xl shadow-md ${getComplianceColor(report.compliance_status)}`}
            >
              <Shield className="h-7 w-7" />
            </motion.div>
            <div>
              <p className="text-sm text-gray-600 font-semibold">Compliance Status</p>
              <motion.p
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', stiffness: 200, damping: 15, delay: 0.5 }}
                className="text-xl font-extrabold capitalize"
              >
                {report.compliance_status}
              </motion.p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* PII by Type */}
      {Object.keys(report.detections_by_type || {}).length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="bg-white rounded-2xl shadow-xl p-6 border-2 border-gray-200"
        >
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Detections by Type
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(report.detections_by_type || {}).map(([type, count], idx) => (
              <motion.div
                key={type}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.6 + idx * 0.1 }}
                whileHover={{ scale: 1.05 }}
                className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border-2 border-gray-200 shadow-md"
              >
                <p className="text-sm text-gray-600 capitalize mb-2 font-semibold">
                  {type.replace(/_/g, ' ')}
                </p>
                <p className="text-3xl font-extrabold text-purple-600">{count}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Detections Table */}
      {report.detections && report.detections.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
          className="bg-white rounded-2xl shadow-xl p-6 border-2 border-gray-200"
          data-testid="pii-detections"
        >
          <h3 className="text-xl font-bold text-gray-900 mb-6">
            Detection Details
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200" data-testid="pii-detections-table">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Matched Text
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {report.detections.map((detection, idx) => (
                  <motion.tr
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.9 + idx * 0.05 }}
                    whileHover={{ backgroundColor: '#f9fafb', scale: 1.01 }}
                    className="transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {detection.entity_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      Row {detection.location.row ?? '—'}, Col: {detection.location.column || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {detection.matched_text || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceBadge(
                          detection.confidence
                        )}`}
                      >
                        {detection.confidence !== undefined
                          ? `${Math.round(detection.confidence * 100)}%`
                          : 'N/A'}
                      </span>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Recommendations */}
      {report.recommendations && report.recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 1.0 }}
          className="bg-gradient-to-br from-yellow-50 to-orange-50 border-2 border-yellow-300 rounded-2xl p-6 shadow-lg"
        >
          <h3 className="text-xl font-bold text-yellow-900 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-6 w-6" />
            Recommendations
          </h3>
          <ul className="space-y-3">
            {report.recommendations.map((rec, idx) => (
              <motion.li
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: 1.1 + idx * 0.1 }}
                className="flex items-start gap-3 bg-white/50 rounded-lg p-3 border border-yellow-200"
              >
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-yellow-900 font-medium">{rec}</span>
              </motion.li>
            ))}
          </ul>
        </motion.div>
      )}
    </div>
  );
}
