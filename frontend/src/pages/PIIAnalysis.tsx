import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRecentRuns, getPIIReport } from '@/api/client';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Shield, AlertTriangle, CheckCircle, Download } from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
  useState(() => {
    const loadPIIData = async () => {
      setIsLoadingPII(true);
      const allDetections: any[] = [];

      for (const run of runs) {
        if (run.pii_detections && run.pii_detections > 0) {
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
      }

      setPiiData(allDetections);
      setIsLoadingPII(false);
    };

    if (runs.length > 0) {
      loadPIIData();
    }
  });

  // Calculate stats
  const totalPIIFields = piiData.length;
  const piiByType = piiData.reduce((acc: Record<string, number>, detection) => {
    acc[detection.entity_type] = (acc[detection.entity_type] || 0) + 1;
    return acc;
  }, {});

  const mostCommonType = Object.entries(piiByType).sort((a, b) => b[1] - a[1])[0];
  const avgConfidence = piiData.length > 0
    ? piiData.reduce((sum, d) => sum + d.confidence, 0) / piiData.length
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

  const COLORS = ['#737373', '#525252', '#404040', '#262626', '#171717', '#a3a3a3', '#d4d4d4'];

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
      d.location.column,
      d.entity_type,
      d.confidence.toFixed(2),
      d.location.row,
      format(new Date(d.created_at), 'yyyy-MM-dd HH:mm'),
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
    if (status === 'compliant') return 'bg-green-500/10 text-green-600';
    if (status === 'warning') return 'bg-yellow-500/10 text-yellow-600';
    return 'bg-red-500/10 text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">PII Analysis</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Monitor and manage personally identifiable information
          </p>
        </div>
        <Button onClick={exportToCSV}>
          <Download className="w-4 h-4 mr-2" />
          Export CSV
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Total PII Fields</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">{totalPIIFields}</p>
              </div>
              <Shield className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Most Common Type</p>
                <p className="text-base font-semibold text-[hsl(var(--foreground))]">
                  {mostCommonType ? mostCommonType[0] : 'N/A'}
                </p>
                {mostCommonType && (
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">{mostCommonType[1]} occurrences</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Avg Confidence</p>
                <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">{avgConfidence.toFixed(1)}%</p>
              </div>
              <CheckCircle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">Compliance Status</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium mt-2 ${getComplianceColor()}`}>
                  {getComplianceStatus().toUpperCase()}
                </span>
              </div>
              {getComplianceStatus() === 'compliant' ? (
                <CheckCircle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Compliance Alerts */}
      {highRiskCount > 0 && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-900">
          <CardContent className="p-4">
            <div className="flex">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-3 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">High-Risk PII Detected</h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {highRiskCount} high-risk PII fields detected (credit cards, SSN, CPR numbers).
                  Immediate action required for GDPR compliance.
                </p>
                <ul className="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                  <li>Review data masking policies</li>
                  <li>Enable encryption for sensitive fields</li>
                  <li>Update data retention policies</li>
                  <li>Document legal basis for processing</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts and Table Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* PII by Type Chart */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-medium text-[hsl(var(--foreground))] mb-4">PII Distribution by Type</h3>
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
              <div className="h-[300px] flex items-center justify-center text-[hsl(var(--muted-foreground))]">
                No PII data available
              </div>
            )}
          </CardContent>
        </Card>

        {/* PII Types List */}
        <Card>
          <CardContent className="p-6">
            <h3 className="text-sm font-medium text-[hsl(var(--foreground))] mb-4">PII Types Summary</h3>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {Object.entries(piiByType)
                .sort((a, b) => b[1] - a[1])
                .map(([type, count]) => (
                  <div
                    key={type}
                    className="flex items-center justify-between p-3 bg-[hsl(var(--secondary))] rounded-lg hover:bg-[hsl(var(--secondary)/0.8)] cursor-pointer"
                    onClick={() => setSelectedType(type === selectedType ? null : type)}
                  >
                    <div className="flex items-center">
                      <span
                        className={`w-2 h-2 rounded-full mr-3 ${
                          highRiskTypes.includes(type) ? 'bg-red-500' : 'bg-[hsl(var(--foreground))]'
                        }`}
                      ></span>
                      <span className="text-sm font-medium text-[hsl(var(--foreground))]">{type}</span>
                      {highRiskTypes.includes(type) && (
                        <AlertTriangle className="w-4 h-4 text-red-500 ml-2" />
                      )}
                    </div>
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">{count}</span>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">Filter by Dataset</label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
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
                <span className="text-sm text-[hsl(var(--muted-foreground))]">Filtered by type:</span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]">
                  {selectedType}
                  <button
                    onClick={() => setSelectedType(null)}
                    className="ml-1 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
                  >
                    ×
                  </button>
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* PII Inventory Table */}
      <Card>
        <CardContent className="p-0">
          <div className="px-4 py-3 border-b border-[hsl(var(--border))]">
            <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">
              PII Inventory ({filteredData.length} items)
            </h3>
          </div>
          {isLoadingPII ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent mx-auto" />
              <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">Loading PII data...</p>
            </div>
          ) : filteredData.length === 0 ? (
            <div className="p-12 text-center">
              <Shield className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
              <h3 className="text-sm font-medium text-[hsl(var(--foreground))] mb-1">No PII detected</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                {selectedType || selectedDataset !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Your data appears to be free of personally identifiable information'}
              </p>
            </div>
          ) : (
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-[hsl(var(--border))]">
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Column
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    PII Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Matches
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Last Detected
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border))]">
                {filteredData.map((detection, idx) => (
                  <tr key={idx} className="hover:bg-[hsl(var(--secondary)/0.5)]">
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--foreground))]">
                      {detection.dataset}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-[hsl(var(--foreground))]">
                      {detection.location.column}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          highRiskTypes.includes(detection.entity_type)
                            ? 'bg-red-500/10 text-red-600'
                            : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]'
                        }`}>
                          {detection.entity_type}
                        </span>
                        {highRiskTypes.includes(detection.entity_type) && (
                          <AlertTriangle className="w-4 h-4 text-red-500 ml-2" />
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--muted-foreground))]">
                      Row {detection.location.row}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-[hsl(var(--secondary))] rounded-full h-1.5 mr-2">
                          <div
                            className="bg-[hsl(var(--foreground))] h-1.5 rounded-full"
                            style={{ width: `${detection.confidence * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-[hsl(var(--muted-foreground))]">
                          {(detection.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--muted-foreground))]">
                      {format(new Date(detection.created_at), 'MMM dd, yyyy')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
