import { useQuery } from '@tanstack/react-query';
import { getQualityMetrics, getPIIReport, downloadReport } from '@/api/client';
import { X, Download, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface Props {
  runId: string;
  onClose: () => void;
}

export default function QualityDetailModal({ runId, onClose }: Props) {
  const [expandedColumns, setExpandedColumns] = useState<Set<string>>(new Set());

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['qualityMetrics', runId],
    queryFn: () => getQualityMetrics(runId),
  });

  const { data: piiReport, isLoading: piiLoading } = useQuery({
    queryKey: ['piiReport', runId],
    queryFn: () => getPIIReport(runId),
  });

  const toggleColumn = (column: string) => {
    const newExpanded = new Set(expandedColumns);
    if (newExpanded.has(column)) {
      newExpanded.delete(column);
    } else {
      newExpanded.add(column);
    }
    setExpandedColumns(newExpanded);
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.95) return 'bg-green-500';
    if (score >= 0.85) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreTextColor = (score: number) => {
    if (score >= 0.95) return 'text-green-800';
    if (score >= 0.85) return 'text-yellow-800';
    return 'text-red-800';
  };

  const dimensions = metrics ? [
    { key: 'completeness', label: 'Completeness', data: metrics.dimensions.completeness },
    { key: 'uniqueness', label: 'Uniqueness', data: metrics.dimensions.uniqueness },
    { key: 'validity', label: 'Validity', data: metrics.dimensions.validity },
    { key: 'consistency', label: 'Consistency', data: metrics.dimensions.consistency },
    { key: 'accuracy', label: 'Accuracy', data: metrics.dimensions.accuracy },
    { key: 'timeliness', label: 'Timeliness', data: metrics.dimensions.timeliness },
  ] : [];

  if (metricsLoading || piiLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading report...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Quality Report Details</h2>
            <p className="text-sm text-gray-600 mt-1">Run ID: {runId.slice(0, 8)}</p>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => downloadReport(runId, 'json')}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              <Download className="w-4 h-4 inline mr-2" />
              Download JSON
            </button>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Overall Score */}
          {metrics && (
            <div className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg p-6 mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Overall Quality Score</h3>
                  <p className="text-4xl font-bold text-blue-900">
                    {(metrics.overall_score * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600 mb-2">
                    {dimensions.filter(d => d.data.passed).length} of {dimensions.length} dimensions passed
                  </p>
                  <div className="flex space-x-1">
                    {dimensions.map((dim) => (
                      <div
                        key={dim.key}
                        className={`w-8 h-8 rounded ${
                          dim.data.passed ? 'bg-green-500' : 'bg-red-500'
                        }`}
                        title={`${dim.label}: ${(dim.data.score * 100).toFixed(1)}%`}
                      ></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Quality Dimensions */}
          {metrics && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Quality Dimensions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {dimensions.map((dim) => (
                  <div key={dim.key} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium text-gray-900">{dim.label}</h4>
                      <span className={`text-sm font-medium ${getScoreTextColor(dim.data.score)}`}>
                        {(dim.data.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                      <div
                        className={`h-2 rounded-full ${getScoreColor(dim.data.score)}`}
                        style={{ width: `${dim.data.score * 100}%` }}
                      ></div>
                    </div>
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span>Threshold: {(dim.data.threshold * 100).toFixed(0)}%</span>
                      <span className={dim.data.passed ? 'text-green-600' : 'text-red-600'}>
                        {dim.data.passed ? '✓ Passed' : '✗ Failed'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* PII Summary */}
          {piiReport && (
            <div className="mb-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">PII Detection Summary</h3>
              <div className="border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-600">Total Detections</p>
                    <p className="text-2xl font-bold text-gray-900">{piiReport.total_detections}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Unique Types</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {Object.keys(piiReport.detections_by_type).length}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Compliance Status</p>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        piiReport.compliance_status === 'compliant'
                          ? 'bg-green-100 text-green-800'
                          : piiReport.compliance_status === 'warning'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {piiReport.compliance_status}
                    </span>
                  </div>
                </div>

                {Object.keys(piiReport.detections_by_type).length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">PII Types Detected:</p>
                    <div className="flex flex-wrap gap-2">
                      {Object.entries(piiReport.detections_by_type).map(([type, count]) => (
                        <span
                          key={type}
                          className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                        >
                          {type}: {count}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {piiReport.recommendations.length > 0 && (
                  <div className="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3">
                    <p className="text-sm font-medium text-yellow-900 mb-2">Recommendations:</p>
                    <ul className="text-sm text-yellow-800 space-y-1">
                      {piiReport.recommendations.map((rec, idx) => (
                        <li key={idx}>• {rec}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Per-Column Metrics */}
          {metrics && Object.keys(metrics.column_metrics).length > 0 && (
            <div>
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Column-Level Quality ({Object.keys(metrics.column_metrics).length} columns)
              </h3>
              <div className="space-y-2">
                {Object.entries(metrics.column_metrics).map(([column, data]) => (
                  <div key={column} className="border border-gray-200 rounded-lg overflow-hidden">
                    <button
                      onClick={() => toggleColumn(column)}
                      className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between"
                    >
                      <div className="flex items-center space-x-3">
                        {expandedColumns.has(column) ? (
                          <ChevronDown className="w-4 h-4 text-gray-500" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-500" />
                        )}
                        <span className="font-medium text-gray-900">{column}</span>
                        <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
                          {data.data_type}
                        </span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Completeness: {(data.completeness * 100).toFixed(1)}%</span>
                        <span>Validity: {(data.validity * 100).toFixed(1)}%</span>
                      </div>
                    </button>

                    {expandedColumns.has(column) && (
                      <div className="p-4 bg-white border-t border-gray-200">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <p className="text-xs text-gray-600">Completeness</p>
                            <div className="flex items-center mt-1">
                              <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className={`h-2 rounded-full ${getScoreColor(data.completeness)}`}
                                  style={{ width: `${data.completeness * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-gray-900">
                                {(data.completeness * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Uniqueness</p>
                            <div className="flex items-center mt-1">
                              <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className={`h-2 rounded-full ${getScoreColor(data.uniqueness)}`}
                                  style={{ width: `${data.uniqueness * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-gray-900">
                                {(data.uniqueness * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Validity</p>
                            <div className="flex items-center mt-1">
                              <div className="flex-1 bg-gray-200 rounded-full h-2 mr-2">
                                <div
                                  className={`h-2 rounded-full ${getScoreColor(data.validity)}`}
                                  style={{ width: `${data.validity * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm font-medium text-gray-900">
                                {(data.validity * 100).toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Data Type</p>
                            <p className="text-sm font-medium text-gray-900 mt-1">
                              {data.data_type}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Null Count</p>
                            <p className="text-sm font-medium text-gray-900 mt-1">
                              {data.null_count.toLocaleString()}
                            </p>
                          </div>
                          <div>
                            <p className="text-xs text-gray-600">Unique Count</p>
                            <p className="text-sm font-medium text-gray-900 mt-1">
                              {data.unique_count.toLocaleString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
