import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getRecentRuns, downloadReport } from '@/api/client';
import { Search, Download, Filter, Calendar } from 'lucide-react';
import { format } from 'date-fns';
import QualityDetailModal from '@/components/Quality/QualityDetailModal';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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

  const getQualityBadge = (score?: number) => {
    if (!score) return null;
    const styles = score >= 95
      ? 'bg-green-500/10 text-green-600'
      : score >= 85
        ? 'bg-yellow-500/10 text-yellow-600'
        : 'bg-red-500/10 text-red-600';
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles}`}>
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
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Quality Reports</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            View and analyze data quality assessments
          </p>
        </div>
        <Button
          onClick={() => setShowFilters(!showFilters)}
          variant="outline"
        >
          <Filter className="w-4 h-4 mr-2" />
          Filters
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">Total Reports</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">{filteredRuns.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">Avg Quality Score</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
              {filteredRuns.length > 0
                ? (
                    filteredRuns.reduce((sum, r) => sum + (r.quality_score || 0), 0) /
                    filteredRuns.filter(r => r.quality_score).length
                  ).toFixed(1)
                : '0'}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">High Quality (≥95%)</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
              {filteredRuns.filter(r => (r.quality_score || 0) >= 95).length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-[hsl(var(--muted-foreground))]">With PII Detections</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
              {filteredRuns.filter(r => (r.pii_detections || 0) > 0).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <Card>
          <CardContent className="p-6 space-y-4">
            <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Date Range */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[hsl(var(--foreground))]">Date From</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                />
              </div>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[hsl(var(--foreground))]">Date To</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                />
              </div>

              {/* PII Filter */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-[hsl(var(--foreground))]">PII Found</label>
                <select
                  value={piiFilter}
                  onChange={(e) => setPiiFilter(e.target.value as 'all' | 'yes' | 'no')}
                  className="w-full px-3 py-2 text-sm border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                >
                  <option value="all">All</option>
                  <option value="yes">Yes</option>
                  <option value="no">No</option>
                </select>
              </div>

              {/* Quality Range */}
              <div className="col-span-3 space-y-2">
                <label className="block text-sm font-medium text-[hsl(var(--foreground))]">
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
              <Button
                variant="ghost"
                onClick={() => {
                  setDateFrom('');
                  setDateTo('');
                  setMinQuality(0);
                  setMaxQuality(100);
                  setPiiFilter('all');
                  setSearchTerm('');
                }}
              >
                Reset Filters
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[hsl(var(--muted-foreground))] w-4 h-4" />
            <input
              type="search"
              data-testid="search-input"
              placeholder="Search by dataset name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            />
          </div>
        </CardContent>
      </Card>

      {/* Reports Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-12 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent mx-auto" />
              <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">Loading reports...</p>
            </div>
          ) : filteredRuns.length === 0 ? (
            <div className="p-12 text-center">
              <Calendar className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
              <h3 className="text-sm font-medium text-[hsl(var(--foreground))] mb-1">No reports found</h3>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                {searchTerm || dateFrom || dateTo || piiFilter !== 'all'
                  ? 'Try adjusting your filters'
                  : 'Upload a CSV to generate your first quality report'}
              </p>
            </div>
          ) : (
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-[hsl(var(--border))]">
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Run ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Quality Score
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    PII Found
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--border))]">
                {filteredRuns.map((run) => (
                  <tr
                    key={run.run_id}
                    className="hover:bg-[hsl(var(--secondary)/0.5)] cursor-pointer"
                    onClick={() => setSelectedRunId(run.run_id)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-[hsl(var(--foreground))]">
                      {run.run_id.slice(0, 8)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--foreground))]">
                      {run.dataset_name}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-[hsl(var(--muted-foreground))]">
                      {format(new Date(run.created_at), 'MMM dd, yyyy HH:mm')}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getQualityBadge(run.quality_score)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {run.pii_detections ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-500/10 text-yellow-600">
                          {run.pii_detections} found
                        </span>
                      ) : (
                        <span className="text-sm text-[hsl(var(--muted-foreground))]">None</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDownload(run.run_id, 'json');
                          }}
                          title="Download JSON"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRunId(run.run_id);
                          }}
                        >
                          View Details
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

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
