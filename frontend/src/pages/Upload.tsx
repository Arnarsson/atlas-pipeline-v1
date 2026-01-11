import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Download, Sparkles, Activity } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CSVDropzone from '@/components/Upload/CSVDropzone';
import QualityDashboard from '@/components/Quality/QualityDashboard';
import PIITable from '@/components/PII/PIITable';
import { ErrorBoundary } from '@/components/ErrorBoundary';
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
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-gradient-to-r from-purple-600 via-indigo-600 to-blue-600 rounded-2xl p-8 shadow-2xl border-4 border-white"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-extrabold text-white drop-shadow-lg flex items-center gap-3">
              <Sparkles className="h-10 w-10" />
              Upload CSV
            </h1>
            <p className="mt-3 text-lg text-indigo-100 font-semibold">
              Upload a CSV file for quality validation and PII detection
            </p>
          </div>
          <AnimatePresence>
            {runId && (
              <motion.button
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                data-testid="download-report-btn"
                onClick={handleDownloadReport}
                className="inline-flex items-center gap-2 px-6 py-3 border-2 border-white text-base font-bold rounded-xl shadow-lg text-white bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 transition-all duration-300"
              >
                <Download className="h-5 w-5" />
                Download Report
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Upload Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="bg-white rounded-2xl shadow-xl p-8 border-2 border-gray-200"
        data-testid="upload-section"
      >
        <CSVDropzone onUploadSuccess={handleUploadSuccess} />
      </motion.div>

      {/* Results Section */}
      <AnimatePresence>
        {runId && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-8"
            data-testid="results-section"
          >
            {/* Quality Metrics */}
            {qualityLoading ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gradient-to-br from-white to-blue-50 rounded-2xl shadow-xl p-12 border-2 border-blue-200"
                data-testid="quality-loading"
              >
                <div className="flex flex-col items-center justify-center gap-4">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="relative"
                  >
                    <div className="rounded-full h-16 w-16 border-4 border-primary-200" />
                    <div className="absolute inset-0 rounded-full h-16 w-16 border-4 border-t-primary-600 border-r-primary-600" data-testid="loading-spinner" />
                  </motion.div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">Analyzing Quality Metrics</p>
                    <p className="text-sm text-gray-600 mt-1">Running validation checks across 6 dimensions...</p>
                  </div>
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="flex gap-2 mt-4"
                  >
                    {['Completeness', 'Uniqueness', 'Validity'].map((dim, idx) => (
                      <motion.div
                        key={dim}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.2 }}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold"
                      >
                        {dim}
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              </motion.div>
            ) : qualityMetrics ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                data-testid="quality-metrics-section"
              >
                <div className="flex items-center gap-3 mb-6">
                  <Activity className="h-8 w-8 text-primary-600" />
                  <h2 className="text-3xl font-extrabold bg-gradient-to-r from-primary-600 to-blue-600 bg-clip-text text-transparent">
                    Quality Metrics
                  </h2>
                </div>
                <ErrorBoundary fallback={
                  <div className="p-6 bg-red-50 rounded-xl border-2 border-red-200">
                    <p className="text-red-800">Error loading quality metrics. Please try refreshing the page.</p>
                  </div>
                }>
                  <QualityDashboard metrics={qualityMetrics} />
                </ErrorBoundary>
              </motion.div>
            ) : null}

            {/* PII Detection Results */}
            {piiLoading ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-gradient-to-br from-white to-purple-50 rounded-2xl shadow-xl p-12 border-2 border-purple-200"
                data-testid="pii-loading"
              >
                <div className="flex flex-col items-center justify-center gap-4">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                    className="relative"
                  >
                    <div className="rounded-full h-16 w-16 border-4 border-purple-200" />
                    <div className="absolute inset-0 rounded-full h-16 w-16 border-4 border-t-purple-600 border-r-purple-600" data-testid="loading-spinner" />
                  </motion.div>
                  <div className="text-center">
                    <p className="text-lg font-bold text-gray-900">Analyzing PII Detections</p>
                    <p className="text-sm text-gray-600 mt-1">Scanning for sensitive data with Microsoft Presidio...</p>
                  </div>
                  <motion.div
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="flex gap-2 mt-4"
                  >
                    {['EMAIL', 'PERSON', 'PHONE', 'SSN'].map((type, idx) => (
                      <motion.div
                        key={type}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.2 }}
                        className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold"
                      >
                        {type}
                      </motion.div>
                    ))}
                  </motion.div>
                </div>
              </motion.div>
            ) : piiReport ? (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                data-testid="pii-results-section"
              >
                <div className="flex items-center gap-3 mb-6">
                  <Sparkles className="h-8 w-8 text-purple-600" />
                  <h2 className="text-3xl font-extrabold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                    PII Detection Results
                  </h2>
                </div>
                <ErrorBoundary fallback={
                  <div className="p-6 bg-red-50 rounded-xl border-2 border-red-200">
                    <p className="text-red-800">Error loading PII report. Please try refreshing the page.</p>
                  </div>
                }>
                  <PIITable report={piiReport} />
                </ErrorBoundary>
              </motion.div>
            ) : null}

            {/* Run Information */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="bg-gradient-to-br from-gray-50 to-blue-50 rounded-xl p-6 border-2 border-gray-200 shadow-md"
              data-testid="run-info"
            >
              <h3 className="text-sm font-bold text-gray-700 mb-3 uppercase tracking-wide">Run Information</h3>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-600">Run ID:</span>
                <code className="text-sm font-mono bg-white px-3 py-1 rounded-lg border border-gray-300 text-gray-900">
                  {runId}
                </code>
              </div>
              <p className="text-xs text-gray-500 mt-3 flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Results are available for 30 days. Download the report for long-term storage.
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
