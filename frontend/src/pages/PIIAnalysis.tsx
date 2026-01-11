import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRecentRuns, getPIIReport } from '@/api/client';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Shield, AlertTriangle, CheckCircle, Download } from 'lucide-react';
import { format } from 'date-fns';

export default function PIIAnalysis() {
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const [selectedDataset, setSelectedDataset] = useState<string>('all');

  const { data: runs = [] } = useQuery({
    queryKey: ['recentRuns', 100],
    queryFn: () => getRecentRuns(100),
    refetchInterval: 30000,
  });

  // Aggregate PII data from all runs
  const [piiData, setPiiData] = useState<any[]>([]);
  const [isLoadingPII, setIsLoadingPII] = useState(true);

  // Load all PII reports
  useEffect(() => {
    const loadPIIData = async () => {
      setIsLoadingPII(true);
      const allDetections: any[] = [];

      for (const run of runs) {
        if (run.status !== 'completed') continue;
        try {
          const report = await getPIIReport(run.run_id);
          report.detections.forEach((detection: any) => {
            allDetections.push({
              ...detection,
              dataset: run.dataset_name,
              run_id: run.run_id,
              created_at: run.created_at,
            });
          });
        } catch (error) {
          console.error('Failed to load PII report:', error);
        }
      }

      setPiiData(allDetections);
      setIsLoadingPII(false);
    };

    loadPIIData();
  }, [runs]);

  // Calculate stats
  const totalPIIFields = piiData.length;
  const piiByType = piiData.reduce((acc: Record<string, number>, detection) => {
    acc[detection.entity_type] = (acc[detection.entity_type] || 0) + 1;
    return acc;
  }, {});

  const mostCommonType = Object.entries(piiByType).sort((a, b) => b[1] - a[1])[0];
  const confidenceValues = piiData
    .map((d) => d.confidence)
    .filter((value) => typeof value === 'number') as number[];
  const avgConfidence = confidenceValues.length > 0
    ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
    : 0;

  // High-risk PII types
  const highRiskTypes = ['CREDIT_CARD', 'US_SSN', 'DK_CPR', 'US_BANK_NUMBER', 'IBAN_CODE'];
  const highRiskCount = piiData.filter(d => highRiskTypes.includes(d.entity_type)).length;

  // Compliance status
  const getComplianceStatus = () => {
    if (highRiskCount > 0) return 'violation';
    if (totalPIIFields > 50) return 'warning';
    return 'compliant';
  };

  // Chart data
  const chartData = Object.entries(piiByType).map(([type, count]) => ({
    name: type,
    value: count,
  }));

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

  // Filter data
  const filteredData = piiData.filter((detection) => {
    if (selectedType && detection.entity_type !== selectedType) return false;
    if (selectedDataset !== 'all' && detection.dataset !== selectedDataset) return false;
    return true;
  });

  // Get unique datasets
  const datasets = ['all', ...new Set(piiData.map(d => d.dataset))];

  const exportToCSV = () => {
    const headers = ['Dataset', 'Column', 'PII Type', 'Confidence', 'Row', 'Detected At'];
    const rows = filteredData.map(d => [
      d.dataset,
      d.location?.column || '',
      d.entity_type,
      d.confidence !== undefined ? d.confidence.toFixed(2) : '',
      d.location?.row ?? '',
      d.created_at ? format(new Date(d.created_at), 'yyyy-MM-dd HH:mm') : '',
    ]);

    const csv = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pii-inventory-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const getComplianceColor = () => {
    const status = getComplianceStatus();
    if (status === 'compliant') return 'bg-green-100 text-green-800';
    if (status === 'warning') return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">PII Analysis</h1>
          <p className="mt-2 text-sm text-gray-600">
            Monitor and manage personally identifiable information
          </p>
        </div>
        <button
          onClick={exportToCSV}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          <Download className="w-5 h-5 mr-2" />
          Export CSV
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total PII Fields</p>
              <p className="text-2xl font-bold text-gray-900">{totalPIIFields}</p>
            </div>
            <Shield className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Most Common Type</p>
              <p className="text-lg font-bold text-gray-900">
                {mostCommonType ? mostCommonType[0] : 'N/A'}
              </p>
              {mostCommonType && (
                <p className="text-sm text-gray-500">{mostCommonType[1]} occurrences</p>
              )}
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-2xl">🔍</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Confidence</p>
              <p className="text-2xl font-bold text-gray-900">{(avgConfidence * 100).toFixed(1)}%</p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Compliance Status</p>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2 ${getComplianceColor()}`}>
                {getComplianceStatus().toUpperCase()}
              </span>
            </div>
            {getComplianceStatus() === 'compliant' ? (
              <CheckCircle className="w-8 h-8 text-green-600" />
            ) : (
              <AlertTriangle className="w-8 h-8 text-yellow-600" />
            )}
          </div>
        </div>
      </div>

      {/* Compliance Alerts */}
      {highRiskCount > 0 && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <AlertTriangle className="w-5 h-5 text-red-400 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">High-Risk PII Detected</h3>
              <p className="text-sm text-red-700 mt-1">
                {highRiskCount} high-risk PII fields detected (credit cards, SSN, CPR numbers).
                Immediate action required for GDPR compliance.
              </p>
              <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                <li>Review data masking policies</li>
                <li>Enable encryption for sensitive fields</li>
                <li>Update data retention policies</li>
                <li>Document legal basis for processing</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Charts and Table Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PII by Type Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">PII Distribution by Type</h3>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }: any) => `${name}: ${((percent || 0) * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  onClick={(data: any) => setSelectedType(data.name)}
                >
                  {chartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-300 flex items-center justify-center text-gray-500">
              No PII data available
            </div>
          )}
        </div>

        {/* PII Types List */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">PII Types Summary</h3>
          <div className="space-y-3 max-h-[300px] overflow-y-auto">
            {Object.entries(piiByType)
              .sort((a, b) => b[1] - a[1])
              .map(([type, count]) => (
                <div
                  key={type}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                  onClick={() => setSelectedType(type === selectedType ? null : type)}
                >
                  <div className="flex items-center">
                    <span
                      className={`w-3 h-3 rounded-full mr-3 ${
                        highRiskTypes.includes(type) ? 'bg-red-500' : 'bg-blue-500'
                      }`}
                    ></span>
                    <span className="font-medium text-gray-900">{type}</span>
                    {highRiskTypes.includes(type) && (
                      <AlertTriangle className="w-4 h-4 text-red-500 ml-2" />
                    )}
                  </div>
                  <span className="text-sm font-medium text-gray-600">{count}</span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="flex items-center space-x-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">Filter by Dataset</label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              {datasets.map((dataset) => (
                <option key={dataset} value={dataset}>
                  {dataset === 'all' ? 'All Datasets' : dataset}
                </option>
              ))}
            </select>
          </div>
          {selectedType && (
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-600">Filtered by type:</span>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                {selectedType}
                <button
                  onClick={() => setSelectedType(null)}
                  className="ml-1 text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            </div>
          )}
        </div>
      </div>

      {/* PII Inventory Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            PII Inventory ({filteredData.length} items)
          </h3>
        </div>
        <div className="overflow-x-auto">
          {isLoadingPII ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading PII data...</p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="p-12 text-center">
              <Shield className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No PII detected</h3>
              <p className="text-gray-600">
                {selectedType || selectedDataset !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Your data appears to be free of personally identifiable information'}
              </p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Column
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    PII Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Matches
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Detected
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredData.map((detection, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {detection.dataset}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {detection.location?.column || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          highRiskTypes.includes(detection.entity_type)
                            ? 'bg-red-100 text-red-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {detection.entity_type}
                        </span>
                        {highRiskTypes.includes(detection.entity_type) && (
                          <AlertTriangle className="w-4 h-4 text-red-500 ml-2" />
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      Row {detection.location.row ?? '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${(detection.confidence || 0) * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">
                          {detection.confidence !== undefined
                            ? `${(detection.confidence * 100).toFixed(0)}%`
                            : 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {detection.created_at ? format(new Date(detection.created_at), 'MMM dd, yyyy') : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
