import { Shield, AlertTriangle } from 'lucide-react';
import type { PIIReport } from '@/types';

interface PIITableProps {
  report: PIIReport;
}

const getConfidenceBadge = (confidence: number) => {
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
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-purple-100 rounded-lg">
              <Shield className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Detections</p>
              <p className="text-2xl font-bold text-gray-900" data-testid="pii-total-count">{report.total_detections}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-100 rounded-lg">
              <AlertTriangle className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-600">PII Types Found</p>
              <p className="text-2xl font-bold text-gray-900">
                {Object.keys(report.detections_by_type).length}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-3">
            <div className={`p-3 rounded-lg ${getComplianceColor(report.compliance_status)}`}>
              <Shield className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm text-gray-600">Compliance Status</p>
              <p className="text-lg font-bold capitalize">{report.compliance_status}</p>
            </div>
          </div>
        </div>
      </div>

      {/* PII by Type */}
      {Object.keys(report.detections_by_type).length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Detections by Type
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(report.detections_by_type).map(([type, count]) => (
              <div key={type} className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 capitalize mb-1">
                  {type.replace(/_/g, ' ')}
                </p>
                <p className="text-2xl font-bold text-gray-900">{count}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detections Table */}
      {report.detections.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6" data-testid="pii-detections">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
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
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                        {detection.entity_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      Row {detection.location.row}, Col: {detection.location.column}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 font-mono">
                      {detection.matched_text}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceBadge(
                          detection.confidence
                        )}`}
                      >
                        {Math.round(detection.confidence * 100)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {report.recommendations.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3">
            Recommendations
          </h3>
          <ul className="space-y-2">
            {report.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5 flex-shrink-0" />
                <span className="text-sm text-yellow-800">{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
