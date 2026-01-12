import { Link } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Database,
  BarChart3,
  Shield,
  Eye,
  FileText,
  ExternalLink,
  X,
  Layers
} from 'lucide-react';

interface SyncResult {
  run_id: string;
  status: string;
  records_synced: number;
  explore_records?: number;
  chart_records?: number;
  navigate_records?: number;
  pii_detections?: number;
  quality_score?: number;
  sync_mode?: string;
  source_id: string;
  stream_name: string;
  layers_written?: string[];
  checks_performed?: {
    pii_detection: boolean;
    quality_validation: boolean;
    state_updated: boolean;
    lineage_tracked: boolean;
  };
  error?: string;
}

interface SyncResultModalProps {
  result: SyncResult;
  onClose: () => void;
}

export default function SyncResultModal({ result, onClose }: SyncResultModalProps) {
  const isSuccess = result.status === 'completed';
  const qualityScore = result.quality_score ?? 0;
  const piiDetections = result.pii_detections ?? 0;

  // Determine quality status
  const getQualityStatus = (score: number) => {
    if (score >= 90) return { label: 'Excellent', color: 'text-green-600', bg: 'bg-green-500/10' };
    if (score >= 75) return { label: 'Good', color: 'text-blue-600', bg: 'bg-blue-500/10' };
    if (score >= 60) return { label: 'Fair', color: 'text-yellow-600', bg: 'bg-yellow-500/10' };
    return { label: 'Poor', color: 'text-red-600', bg: 'bg-red-500/10' };
  };

  const qualityStatus = getQualityStatus(qualityScore);

  // Determine PII status
  const getPiiStatus = (detections: number) => {
    if (detections === 0) return { label: 'None Detected', color: 'text-green-600', bg: 'bg-green-500/10', icon: CheckCircle2 };
    if (detections <= 5) return { label: 'Low Risk', color: 'text-yellow-600', bg: 'bg-yellow-500/10', icon: AlertTriangle };
    return { label: 'High Risk', color: 'text-red-600', bg: 'bg-red-500/10', icon: AlertTriangle };
  };

  const piiStatus = getPiiStatus(piiDetections);
  const PiiIcon = piiStatus.icon;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-[hsl(var(--card))] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-[hsl(var(--border))]">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[hsl(var(--border))]">
          <div className="flex items-center gap-3">
            {isSuccess ? (
              <CheckCircle2 className="w-8 h-8 text-green-500" />
            ) : (
              <XCircle className="w-8 h-8 text-red-500" />
            )}
            <div>
              <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">
                {isSuccess ? 'Sync Completed Successfully!' : 'Sync Failed'}
              </h2>
              <p className="text-sm text-[hsl(var(--muted-foreground))]">
                {result.source_id} / {result.stream_name}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Error Message */}
          {result.error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
              <div className="flex items-start gap-2">
                <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-600 mb-1">Error Details</p>
                  <p className="text-sm text-[hsl(var(--foreground))]">{result.error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Success Content */}
          {isSuccess && (
            <>
              {/* Key Metrics Grid */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[hsl(var(--muted-foreground))]">Records Synced</p>
                        <p className="text-3xl font-bold text-[hsl(var(--foreground))] mt-1">
                          {result.records_synced.toLocaleString()}
                        </p>
                      </div>
                      <Database className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[hsl(var(--muted-foreground))]">Quality Score</p>
                        <p className={`text-3xl font-bold ${qualityStatus.color} mt-1`}>
                          {qualityScore.toFixed(0)}
                          <span className="text-lg">/100</span>
                        </p>
                      </div>
                      <BarChart3 className={`w-8 h-8 ${qualityStatus.color}`} />
                    </div>
                    <div className="mt-2">
                      <span className={`px-2 py-1 text-xs rounded ${qualityStatus.bg} ${qualityStatus.color}`}>
                        {qualityStatus.label}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[hsl(var(--muted-foreground))]">PII Detections</p>
                        <p className={`text-3xl font-bold ${piiStatus.color} mt-1`}>
                          {piiDetections}
                        </p>
                      </div>
                      <PiiIcon className={`w-8 h-8 ${piiStatus.color}`} />
                    </div>
                    <div className="mt-2">
                      <span className={`px-2 py-1 text-xs rounded ${piiStatus.bg} ${piiStatus.color}`}>
                        {piiStatus.label}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-[hsl(var(--muted-foreground))]">Sync Mode</p>
                        <p className="text-xl font-semibold text-[hsl(var(--foreground))] mt-1 capitalize">
                          {result.sync_mode || 'Full Refresh'}
                        </p>
                      </div>
                      <Layers className="w-8 h-8 text-[hsl(var(--muted-foreground))]" />
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Data Layers Summary */}
              {result.layers_written && result.layers_written.length > 0 && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Layers className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                      <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">
                        Data Layers Written
                      </h3>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-[hsl(var(--secondary))] rounded-lg">
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-1">Explore (Raw)</p>
                        <p className="text-lg font-semibold text-[hsl(var(--foreground))]">
                          {result.explore_records?.toLocaleString() || result.records_synced.toLocaleString()}
                        </p>
                      </div>
                      <div className="text-center p-3 bg-[hsl(var(--secondary))] rounded-lg">
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-1">Chart (Validated)</p>
                        <p className="text-lg font-semibold text-[hsl(var(--foreground))]">
                          {result.chart_records?.toLocaleString() || result.records_synced.toLocaleString()}
                        </p>
                      </div>
                      <div className="text-center p-3 bg-[hsl(var(--secondary))] rounded-lg">
                        <p className="text-xs text-[hsl(var(--muted-foreground))] mb-1">Navigate (Business)</p>
                        <p className="text-lg font-semibold text-[hsl(var(--foreground))]">
                          {result.navigate_records?.toLocaleString() || result.records_synced.toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Checks Performed */}
              {result.checks_performed && (
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 mb-3">
                      <Shield className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                      <h3 className="text-sm font-medium text-[hsl(var(--foreground))]">
                        Pipeline Checks
                      </h3>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="flex items-center gap-2">
                        {result.checks_performed.pii_detection ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        )}
                        <span className="text-sm text-[hsl(var(--foreground))]">PII Detection</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {result.checks_performed.quality_validation ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        )}
                        <span className="text-sm text-[hsl(var(--foreground))]">Quality Validation</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {result.checks_performed.state_updated ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        )}
                        <span className="text-sm text-[hsl(var(--foreground))]">State Persisted</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {result.checks_performed.lineage_tracked ? (
                          <CheckCircle2 className="w-4 h-4 text-green-500" />
                        ) : (
                          <XCircle className="w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                        )}
                        <span className="text-sm text-[hsl(var(--foreground))]">Lineage Tracked</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Run ID */}
              <div className="p-3 bg-[hsl(var(--secondary))] rounded-lg">
                <p className="text-xs text-[hsl(var(--muted-foreground))] mb-1">Run ID</p>
                <p className="text-sm font-mono text-[hsl(var(--foreground))]">{result.run_id}</p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-3 pt-4 border-t border-[hsl(var(--border))]">
                <Link
                  to={`/catalog?run_id=${result.run_id}`}
                  className="flex-1 min-w-[200px]"
                >
                  <Button variant="default" className="w-full">
                    <Database className="w-4 h-4 mr-2" />
                    View in Catalog
                    <ExternalLink className="w-3 h-3 ml-2" />
                  </Button>
                </Link>

                <Link
                  to={`/reports?run_id=${result.run_id}`}
                  className="flex-1 min-w-[200px]"
                >
                  <Button variant="outline" className="w-full">
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Quality Report
                    <ExternalLink className="w-3 h-3 ml-2" />
                  </Button>
                </Link>

                {piiDetections > 0 && (
                  <Link
                    to={`/pii?run_id=${result.run_id}`}
                    className="flex-1 min-w-[200px]"
                  >
                    <Button variant="outline" className="w-full">
                      <Shield className="w-4 h-4 mr-2" />
                      PII Analysis
                      <ExternalLink className="w-3 h-3 ml-2" />
                    </Button>
                  </Link>
                )}

                <Link
                  to={`/lineage?dataset=${result.source_id}_${result.stream_name}`}
                  className="flex-1 min-w-[200px]"
                >
                  <Button variant="outline" className="w-full">
                    <FileText className="w-4 h-4 mr-2" />
                    Data Lineage
                    <ExternalLink className="w-3 h-3 ml-2" />
                  </Button>
                </Link>
              </div>
            </>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between pt-4 border-t border-[hsl(var(--border))]">
            <Button variant="ghost" onClick={onClose}>
              <Eye className="w-4 h-4 mr-2" />
              Continue Monitoring
            </Button>
            <Button onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
