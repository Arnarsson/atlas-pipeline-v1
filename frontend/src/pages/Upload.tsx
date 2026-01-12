import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Upload as UploadIcon, Activity, Shield } from 'lucide-react';
import CSVDropzone from '@/components/Upload/CSVDropzone';
import QualityDashboard from '@/components/Quality/QualityDashboard';
import PIITable from '@/components/PII/PIITable';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { getQualityMetrics, getPIIReport, downloadReport } from '@/api/client';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Upload CSV</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Upload a CSV file for quality validation and PII detection
          </p>
        </div>
        {runId && (
          <Button
            data-testid="download-report-btn"
            onClick={handleDownloadReport}
            variant="outline"
          >
            <Download className="h-4 w-4 mr-2" />
            Download Report
          </Button>
        )}
      </div>

      {/* Upload Section */}
      <Card data-testid="upload-section">
        <CardContent className="p-6">
          <CSVDropzone onUploadSuccess={handleUploadSuccess} />
        </CardContent>
      </Card>

      {/* Results Section */}
      {runId && (
        <div className="space-y-6" data-testid="results-section">
          {/* Quality Metrics */}
          {qualityLoading ? (
            <Card data-testid="quality-loading">
              <CardContent className="p-8">
                <div className="flex flex-col items-center justify-center gap-3">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" data-testid="loading-spinner" />
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">Analyzing quality metrics...</p>
                </div>
              </CardContent>
            </Card>
          ) : qualityMetrics ? (
            <div data-testid="quality-metrics-section">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                <h2 className="text-lg font-medium text-[hsl(var(--foreground))]">Quality Metrics</h2>
              </div>
              <ErrorBoundary fallback={
                <Card>
                  <CardContent className="p-6">
                    <p className="text-sm text-red-600">Error loading quality metrics. Please try refreshing.</p>
                  </CardContent>
                </Card>
              }>
                <QualityDashboard metrics={qualityMetrics} />
              </ErrorBoundary>
            </div>
          ) : null}

          {/* PII Detection Results */}
          {piiLoading ? (
            <Card data-testid="pii-loading">
              <CardContent className="p-8">
                <div className="flex flex-col items-center justify-center gap-3">
                  <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" data-testid="loading-spinner" />
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">Scanning for PII...</p>
                </div>
              </CardContent>
            </Card>
          ) : piiReport ? (
            <div data-testid="pii-results-section">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                <h2 className="text-lg font-medium text-[hsl(var(--foreground))]">PII Detection Results</h2>
              </div>
              <ErrorBoundary fallback={
                <Card>
                  <CardContent className="p-6">
                    <p className="text-sm text-red-600">Error loading PII report. Please try refreshing.</p>
                  </CardContent>
                </Card>
              }>
                <PIITable report={piiReport} />
              </ErrorBoundary>
            </div>
          ) : null}

          {/* Run Information */}
          <Card data-testid="run-info">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-[hsl(var(--muted-foreground))]">Run ID:</span>
                  <code className="text-sm font-mono bg-[hsl(var(--secondary))] px-2 py-0.5 rounded text-[hsl(var(--foreground))]">
                    {runId}
                  </code>
                </div>
                <span className="text-xs text-[hsl(var(--muted-foreground))]">
                  Results available for 30 days
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
