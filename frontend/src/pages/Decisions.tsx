import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  FileText,
  History,
  RefreshCw,
  Filter,
  ChevronRight,
  Bot,
  ThumbsUp,
  ThumbsDown,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

// Types
interface AIRecommendation {
  action: string;
  confidence: number;
  reasoning: string;
  model_id: string;
  model_version: string;
  generated_at: string;
}

interface Decision {
  id: string;
  decision_type: string;
  severity: string;
  status: string;
  created_at: string;
  updated_at: string;
  expires_at?: string;
  title: string;
  description: string;
  source_document?: string;
  source_document_hash?: string;
  context: Record<string, unknown>;
  extracted_data: Record<string, unknown>;
  ai_recommendation?: AIRecommendation;
  assigned_to?: string;
  assigned_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_comment?: string;
  audit_id: string;
}

interface DecisionListResponse {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  decisions: Decision[];
}

interface AuditEvent {
  id: string;
  decision_id: string;
  audit_id: string;
  event_type: string;
  timestamp: string;
  user?: string;
  details: Record<string, unknown>;
}

// API functions
const API_BASE = '/api/v1';

async function fetchPendingDecisions(filters: {
  severity?: string;
  decision_type?: string;
}): Promise<DecisionListResponse> {
  const params = new URLSearchParams();
  if (filters.severity) params.append('severity', filters.severity);
  if (filters.decision_type) params.append('decision_type', filters.decision_type);

  const response = await fetch(`${API_BASE}/decisions/pending?${params}`);
  if (!response.ok) throw new Error('Failed to fetch decisions');
  return response.json();
}

async function fetchAuditTrail(id: string): Promise<AuditEvent[]> {
  const response = await fetch(`${API_BASE}/decisions/${id}/audit`);
  if (!response.ok) throw new Error('Failed to fetch audit trail');
  return response.json();
}

async function approveDecision(id: string, data: { user: string; comment?: string }) {
  const response = await fetch(`${API_BASE}/decisions/${id}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to approve decision');
  return response.json();
}

async function rejectDecision(id: string, data: { user: string; reason: string }) {
  const response = await fetch(`${API_BASE}/decisions/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error('Failed to reject decision');
  return response.json();
}

async function fetchDecisionStats() {
  const response = await fetch(`${API_BASE}/decisions/stats/summary`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

// Helper functions
function getSeverityColor(severity: string) {
  switch (severity) {
    case 'critical':
      return 'bg-red-500/10 text-red-600 border-red-200';
    case 'high':
      return 'bg-orange-500/10 text-orange-600 border-orange-200';
    case 'medium':
      return 'bg-yellow-500/10 text-yellow-600 border-yellow-200';
    case 'low':
      return 'bg-green-500/10 text-green-600 border-green-200';
    default:
      return 'bg-gray-500/10 text-gray-600 border-gray-200';
  }
}

function getStatusIcon(status: string) {
  switch (status) {
    case 'approved':
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case 'rejected':
      return <XCircle className="h-5 w-5 text-red-500" />;
    case 'pending':
      return <Clock className="h-5 w-5 text-yellow-500" />;
    default:
      return <AlertTriangle className="h-5 w-5 text-gray-500" />;
  }
}

function formatTimeAgo(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  return `${diffDays}d ago`;
}

// Decision Detail Modal Component
function DecisionDetailModal({
  decision,
  onClose,
  onApprove,
  onReject,
}: {
  decision: Decision;
  onClose: () => void;
  onApprove: (comment?: string) => void;
  onReject: (reason: string) => void;
}) {
  const [comment, setComment] = useState('');
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);

  const { data: auditTrail } = useQuery({
    queryKey: ['decision-audit', decision.id],
    queryFn: () => fetchAuditTrail(decision.id),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-[hsl(var(--background))] rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-[hsl(var(--border))]">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {getStatusIcon(decision.status)}
              <div>
                <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">
                  {decision.title}
                </h2>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">
                  Audit ID: {decision.audit_id}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            >
              <XCircle className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[60vh] space-y-6">
          {/* Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Type</p>
              <p className="text-sm text-[hsl(var(--foreground))] capitalize">{decision.decision_type}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Severity</p>
              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getSeverityColor(decision.severity)}`}>
                {decision.severity}
              </span>
            </div>
            <div>
              <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Created</p>
              <p className="text-sm text-[hsl(var(--foreground))]">{formatTimeAgo(decision.created_at)}</p>
            </div>
            {decision.assigned_to && (
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Assigned To</p>
                <p className="text-sm text-[hsl(var(--foreground))]">{decision.assigned_to}</p>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <p className="text-sm font-medium text-[hsl(var(--muted-foreground))] mb-2">Description</p>
            <p className="text-sm text-[hsl(var(--foreground))] bg-[hsl(var(--secondary))] p-3 rounded">
              {decision.description}
            </p>
          </div>

          {/* AI Recommendation */}
          {decision.ai_recommendation && (
            <div className="bg-[hsl(var(--secondary)/0.5)] p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <Bot className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                <p className="text-sm font-medium text-[hsl(var(--foreground))]">AI Recommendation</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  {decision.ai_recommendation.action === 'approve' ? (
                    <ThumbsUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <ThumbsDown className="h-4 w-4 text-red-500" />
                  )}
                  <span className="text-sm font-medium capitalize">{decision.ai_recommendation.action}</span>
                  <span className="text-sm text-[hsl(var(--muted-foreground))]">
                    ({Math.round(decision.ai_recommendation.confidence * 100)}% confidence)
                  </span>
                </div>
                <p className="text-sm text-[hsl(var(--muted-foreground))]">
                  {decision.ai_recommendation.reasoning}
                </p>
              </div>
            </div>
          )}

          {/* Extracted Data */}
          {Object.keys(decision.extracted_data).length > 0 && (
            <div>
              <p className="text-sm font-medium text-[hsl(var(--muted-foreground))] mb-2">Extracted Data</p>
              <div className="bg-[hsl(var(--secondary))] p-3 rounded overflow-x-auto">
                <pre className="text-xs text-[hsl(var(--foreground))]">
                  {JSON.stringify(decision.extracted_data, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Audit Trail */}
          {auditTrail && auditTrail.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <History className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                <p className="text-sm font-medium text-[hsl(var(--foreground))]">Audit Trail</p>
              </div>
              <div className="space-y-2">
                {auditTrail.map((event) => (
                  <div
                    key={event.id}
                    className="flex items-center gap-3 text-sm text-[hsl(var(--muted-foreground))]"
                  >
                    <span className="text-xs bg-[hsl(var(--secondary))] px-2 py-1 rounded">
                      {event.event_type}
                    </span>
                    <span>{event.user || 'system'}</span>
                    <span className="text-xs">{formatTimeAgo(event.timestamp)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        {decision.status === 'pending' && (
          <div className="p-6 border-t border-[hsl(var(--border))] space-y-4">
            {showRejectForm ? (
              <div className="space-y-3">
                <textarea
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  placeholder="Enter rejection reason (required)"
                  className="w-full p-3 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                  rows={3}
                />
                <div className="flex gap-2">
                  <Button
                    onClick={() => {
                      if (rejectReason.trim()) {
                        onReject(rejectReason);
                      }
                    }}
                    className="flex-1 bg-red-500 hover:bg-red-600 text-white"
                    disabled={!rejectReason.trim()}
                  >
                    Confirm Rejection
                  </Button>
                  <Button
                    onClick={() => setShowRejectForm(false)}
                    variant="outline"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <>
                <div>
                  <input
                    type="text"
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    placeholder="Add comment (optional)"
                    className="w-full p-3 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                  />
                </div>
                <div className="flex gap-3">
                  <Button
                    onClick={() => onApprove(comment || undefined)}
                    className="flex-1 bg-green-500 hover:bg-green-600 text-white"
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    onClick={() => setShowRejectForm(true)}
                    className="flex-1 bg-red-500 hover:bg-red-600 text-white"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Main Component
export default function Decisions() {
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [filters, setFilters] = useState<{ severity?: string; decision_type?: string }>({});
  const queryClient = useQueryClient();

  // Current user (in production, get from auth context)
  const currentUser = 'current_user';

  // Queries
  const { data: decisions, isLoading, refetch } = useQuery({
    queryKey: ['pending-decisions', filters],
    queryFn: () => fetchPendingDecisions(filters),
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: stats } = useQuery({
    queryKey: ['decision-stats'],
    queryFn: fetchDecisionStats,
    refetchInterval: 60000,
  });

  // Mutations
  const approveMutation = useMutation({
    mutationFn: ({ id, comment }: { id: string; comment?: string }) =>
      approveDecision(id, { user: currentUser, comment }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-decisions'] });
      queryClient.invalidateQueries({ queryKey: ['decision-stats'] });
      setSelectedDecision(null);
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      rejectDecision(id, { user: currentUser, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pending-decisions'] });
      queryClient.invalidateQueries({ queryKey: ['decision-stats'] });
      setSelectedDecision(null);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-[hsl(var(--foreground))] border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Decisions</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Human-in-the-loop approval queue
          </p>
        </div>
        <Button onClick={() => refetch()} variant="outline" className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Pending</p>
                <p className="mt-1 text-2xl font-semibold text-yellow-600">
                  {decisions?.pending ?? 0}
                </p>
              </div>
              <Clock className="h-5 w-5 text-yellow-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Approved</p>
                <p className="mt-1 text-2xl font-semibold text-green-600">
                  {decisions?.approved ?? 0}
                </p>
              </div>
              <CheckCircle className="h-5 w-5 text-green-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Rejected</p>
                <p className="mt-1 text-2xl font-semibold text-red-600">
                  {decisions?.rejected ?? 0}
                </p>
              </div>
              <XCircle className="h-5 w-5 text-red-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Critical</p>
                <p className="mt-1 text-2xl font-semibold text-red-600">
                  {stats?.pending_critical ?? 0}
                </p>
              </div>
              <AlertTriangle className="h-5 w-5 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <span className="text-sm font-medium text-[hsl(var(--muted-foreground))]">Filter:</span>
            </div>
            <select
              value={filters.severity || ''}
              onChange={(e) => setFilters({ ...filters, severity: e.target.value || undefined })}
              className="px-3 py-2 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-sm"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filters.decision_type || ''}
              onChange={(e) => setFilters({ ...filters, decision_type: e.target.value || undefined })}
              className="px-3 py-2 border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))] text-sm"
            >
              <option value="">All Types</option>
              <option value="classification">Classification</option>
              <option value="approval">Approval</option>
              <option value="validation">Validation</option>
              <option value="review">Review</option>
            </select>
            {(filters.severity || filters.decision_type) && (
              <Button
                onClick={() => setFilters({})}
                variant="outline"
                size="sm"
              >
                Clear Filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Decisions List */}
      <Card>
        <CardHeader>
          <CardTitle>Pending Decisions</CardTitle>
          <CardDescription>
            {decisions?.total ?? 0} decisions awaiting review
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!decisions?.decisions?.length ? (
            <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
              <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No pending decisions</p>
              <p className="text-sm mt-1">All caught up!</p>
            </div>
          ) : (
            <div className="space-y-3">
              {decisions.decisions.map((decision) => (
                <div
                  key={decision.id}
                  className="flex items-center justify-between p-4 border border-[hsl(var(--border))] rounded-lg hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer"
                  onClick={() => setSelectedDecision(decision)}
                >
                  <div className="flex items-center gap-4">
                    {getStatusIcon(decision.status)}
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-[hsl(var(--foreground))]">{decision.title}</p>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getSeverityColor(decision.severity)}`}>
                          {decision.severity}
                        </span>
                      </div>
                      <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
                        {decision.description.substring(0, 100)}
                        {decision.description.length > 100 && '...'}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-[hsl(var(--muted-foreground))]">
                        <span className="flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {decision.decision_type}
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatTimeAgo(decision.created_at)}
                        </span>
                        {decision.assigned_to && (
                          <span className="flex items-center gap-1">
                            <User className="h-3 w-3" />
                            {decision.assigned_to}
                          </span>
                        )}
                        {decision.ai_recommendation && (
                          <span className="flex items-center gap-1">
                            <Bot className="h-3 w-3" />
                            AI: {decision.ai_recommendation.action} ({Math.round(decision.ai_recommendation.confidence * 100)}%)
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Decision Detail Modal */}
      {selectedDecision && (
        <DecisionDetailModal
          decision={selectedDecision}
          onClose={() => setSelectedDecision(null)}
          onApprove={(comment) => approveMutation.mutate({ id: selectedDecision.id, comment })}
          onReject={(reason) => rejectMutation.mutate({ id: selectedDecision.id, reason })}
        />
      )}
    </div>
  );
}
