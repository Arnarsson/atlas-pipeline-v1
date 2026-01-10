import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRecentRuns, downloadReport } from '@/api/client';
import { Search, Download, Filter, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import QualityDetailModal from '@/components/Quality/QualityDetailModal';

export default function QualityReports() {
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [minQuality, setMinQuality] = useState(0);
  const [maxQuality, setMaxQuality] = useState(100);
  const [piiFilter, setPiiFilter] = useState<'all' | 'yes' | 'no'>('all');
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data: runs = [], isLoading } = useQuery({
    queryKey: ['recentRuns', 100],
    queryFn: () => getRecentRuns(100),
    refetchInterval: 30000,
  });

  // Filter runs based on search and filters
  const filteredRuns = runs.filter((run) => {
    // Search filter
    if (searchTerm && !run.dataset_name.toLowerCase().includes(searchTerm.toLowerCase())) {
      return false;
    }

    // Date filters
    if (dateFrom && new Date(run.created_at) < new Date(dateFrom)) {
      return false;
    }
    if (dateTo && new Date(run.created_at) > new Date(dateTo)) {
      return false;
    }

    // Quality score filter
    if (run.quality_score !== undefined) {
      if (run.quality_score < minQuality || run.quality_score > maxQuality) {
        return false;
      }
    }

    // PII filter
    if (piiFilter !== 'all') {
      const hasPII = (run.pii_detections || 0) > 0;
      if (piiFilter === 'yes' && !hasPII) return false;
      if (piiFilter === 'no' && hasPII) return false;
    }

    return true;
  });

  const getQualityColor = (score?: number) => {
    if (!score) return 'bg-gray-100 text-gray-800';
    if (score >= 95) return 'bg-green-100 text-green-800';
    if (score >= 85) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getQualityBadge = (score?: number) => {
    if (!score) return null;
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getQualityColor(score)}`}>
        {score.toFixed(1)}%
      </span>
    );
  };

  const handleDownload = async (runId: string, format: 'json' | 'pdf' = 'json') => {
    await downloadReport(runId, format);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Quality Reports</h1>
          <p className="mt-2 text-sm text-gray-600">
            View and analyze data quality assessments
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <Filter className="w-5 h-5 mr-2" />
          Filters
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Total Reports</p>
          <p className="text-2xl font-bold text-gray-900">{filteredRuns.length}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">Avg Quality Score</p>
          <p className="text-2xl font-bold text-green-600">
            {filteredRuns.length > 0
              ? (
                  filteredRuns.reduce((sum, r) => sum + (r.quality_score || 0), 0) /
                  filteredRuns.filter(r => r.quality_score).length
                ).toFixed(1)
              : '0'}%
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">High Quality (≥95%)</p>
          <p className="text-2xl font-bold text-green-600">
            {filteredRuns.filter(r => (r.quality_score || 0) >= 95).length}
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-sm text-gray-600">With PII Detections</p>
          <p className="text-2xl font-bold text-yellow-600">
            {filteredRuns.filter(r => (r.pii_detections || 0) > 0).length}
          </p>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <h3 className="text-lg font-medium text-gray-900">Filters</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Date Range */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Date From</label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Date To</label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {/* PII Filter */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">PII Found</label>
              <select
                value={piiFilter}
                onChange={(e) => setPiiFilter(e.target.value as 'all' | 'yes' | 'no')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All</option>
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>

            {/* Quality Range */}
            <div className="col-span-3 space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Quality Score Range: {minQuality}% - {maxQuality}%
              </label>
              <div className="flex items-center space-x-4">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={minQuality}
                  onChange={(e) => setMinQuality(Number(e.target.value))}
                  className="flex-1"
                />
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={maxQuality}
                  onChange={(e) => setMaxQuality(Number(e.target.value))}
                  className="flex-1"
                />
              </div>
            </div>
          </div>

          {/* Reset Filters */}
          <div className="flex justify-end">
            <button
              onClick={() => {
                setDateFrom('');
                setDateTo('');
                setMinQuality(0);
                setMaxQuality(100);
                setPiiFilter('all');
                setSearchTerm('');
              }}
              className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
            >
              Reset Filters
            </button>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="search"
            data-testid="search-input"
            placeholder="Search by dataset name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Reports Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <p className="mt-4 text-gray-600">Loading reports...</p>
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="p-12 text-center">
              <Calendar className="w-16 h-16 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No reports found</h3>
              <p className="text-gray-600">
                {searchTerm || dateFrom || dateTo || piiFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Upload a CSV to generate your first quality report'}
              </p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Quality Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    PII Found
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRuns.map((run) => (
                  <tr
                    key={run.run_id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setSelectedRunId(run.run_id)}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-gray-900">
                      {run.run_id.slice(0, 8)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {run.dataset_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {format(new Date(run.created_at), 'MMM dd, yyyy HH:mm')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getQualityBadge(run.quality_score)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {run.pii_detections ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          {run.pii_detections} found
                        </span>
                      ) : (
                        <span className="text-sm text-gray-500">None</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownload(run.run_id, 'json');
                        }}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                        title="Download JSON"
                      >
                        <Download className="w-4 h-4 inline" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedRunId(run.run_id);
                        }}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Quality Detail Modal */}
      {selectedRunId && (
        <QualityDetailModal
          runId={selectedRunId}
          onClose={() => setSelectedRunId(null)}
        />
      )}
    </div>
  );
}
