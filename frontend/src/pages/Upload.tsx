import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download } from 'lucide-react';
import CSVDropzone from '@/components/Upload/CSVDropzone';
import QualityDashboard from '@/components/Quality/QualityDashboard';
import PIITable from '@/components/PII/PIITable';
import { getQualityMetrics, getPIIReport, downloadReport } from '@/api/client';

export default function Upload() {
  const [runId, setRunId] = useState<string | null>(null);

  const { data: qualityMetrics, isLoading: qualityLoading } = useQuery({
    queryKey: ['quality-metrics', runId],
    queryFn: () => getQualityMetrics(runId!),
    enabled: !!runId,
  });

  const { data: piiReport, isLoading: piiLoading } = useQuery({
    queryKey: ['pii-report', runId],
    queryFn: () => getPIIReport(runId!),
    enabled: !!runId,
  });

  const handleUploadSuccess = (newRunId: string) => {
    setRunId(newRunId);
  };

  const handleDownloadReport = () => {
    if (runId) {
      downloadReport(runId, 'json');
    }
  };

  return (
    <div className="space-y-8" data-testid="upload-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Upload CSV</h1>
          <p className="mt-2 text-sm text-gray-600">
            Upload a CSV file for quality validation and PII detection
          </p>
        </div>
        {runId && (
          <button
            data-testid="download-report-btn"
            onClick={handleDownloadReport}
            className="inline-flex items-center gap-2 px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700"
          >
            <Download className="h-4 w-4" />
            Download Report
          </button>
        )}
      </div>

      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-md p-8" data-testid="upload-section">
        <CSVDropzone onUploadSuccess={handleUploadSuccess} />
      </div>

      {/* Results Section */}
      {runId && (
        <div className="space-y-8" data-testid="results-section">
          {/* Quality Metrics */}
          {qualityLoading ? (
            <div className="bg-white rounded-lg shadow-md p-12" data-testid="quality-loading">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" data-testid="loading-spinner" />
                <span className="ml-4 text-gray-600">Loading quality metrics...</span>
              </div>
            </div>
          ) : qualityMetrics ? (
            <div data-testid="quality-metrics-section">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Quality Metrics
              </h2>
              <QualityDashboard metrics={qualityMetrics} />
            </div>
          ) : null}

          {/* PII Detection Results */}
          {piiLoading ? (
            <div className="bg-white rounded-lg shadow-md p-12" data-testid="pii-loading">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" data-testid="loading-spinner" />
                <span className="ml-4 text-gray-600">Analyzing PII detections...</span>
              </div>
            </div>
          ) : piiReport ? (
            <div data-testid="pii-results-section">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                PII Detection Results
              </h2>
              <PIITable report={piiReport} />
            </div>
          ) : null}

          {/* Run Information */}
          <div className="bg-gray-50 rounded-lg p-6" data-testid="run-info">
            <h3 className="text-sm font-medium text-gray-500 mb-2">Run Information</h3>
            <p className="text-sm text-gray-700">
              <span className="font-medium">Run ID:</span> {runId}
            </p>
            <p className="text-xs text-gray-500 mt-2">
              Results are available for 30 days. Download the report for long-term storage.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
