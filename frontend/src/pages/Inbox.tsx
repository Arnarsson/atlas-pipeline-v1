import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Loader2,
  Eye,
  RefreshCw,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface DemoClaim {
  claim_id: string;
  claim_type: string;
  status: string;
  submitted_at: string;
  submitted_by: string;
  amount: number;
  currency: string;
  description: string;
  category: string;
  document_filename?: string;
  document_extracted: boolean;
  extracted_vendor?: string;
  extracted_amount?: number;
  pii_detected: boolean;
  pii_types: string[];
  quality_score?: number;
  quality_issues: string[];
  decision_id?: string;
  reviewed_by?: string;
  reviewed_at?: string;
  rejection_reason?: string;
}

interface UploadingFile {
  id: string;
  file: File;
  progress: number;
  status: 'uploading' | 'processing' | 'completed' | 'error';
  claimId?: string;
  error?: string;
}

const API_BASE = 'http://localhost:8000/api/v1';

export default function Inbox() {
  const queryClient = useQueryClient();
  const [isDragging, setIsDragging] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const [selectedClaim, setSelectedClaim] = useState<DemoClaim | null>(null);

  // Fetch claims
  const { data: claims = [], isLoading: claimsLoading, refetch } = useQuery<DemoClaim[]>({
    queryKey: ['demo-claims'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/demo/claims`);
      if (!res.ok) throw new Error('Failed to fetch claims');
      return res.json();
    },
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  // Submit claim mutation
  const submitClaim = useMutation({
    mutationFn: async (file: File) => {
      // Create a demo claim (in real app, would upload file)
      const claimData = {
        claim_type: 'expense',
        submitted_by: 'demo_user@atlas-intelligence.com',
        amount: Math.floor(Math.random() * 5000) + 100,
        description: `Document: ${file.name}`,
        category: 'Document Upload',
      };

      const res = await fetch(`${API_BASE}/demo/claims`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(claimData),
      });

      if (!res.ok) throw new Error('Failed to submit claim');
      return res.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['demo-claims'] });
      toast.success(`Claim ${data.claim_id} submitted`);
    },
  });

  // Process claim mutation
  const processClaim = useMutation({
    mutationFn: async (claimId: string) => {
      const res = await fetch(`${API_BASE}/demo/claims/${claimId}/process`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to process claim');
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['demo-claims'] });
      toast.success('Claim processed successfully');
    },
  });

  // Handle file drop
  const handleDrop = useCallback(
    async (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length === 0) return;

      for (const file of files) {
        const uploadId = `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // Add to uploading list
        setUploadingFiles((prev) => [
          ...prev,
          { id: uploadId, file, progress: 0, status: 'uploading' },
        ]);

        try {
          // Simulate upload progress
          for (let progress = 0; progress <= 100; progress += 20) {
            await new Promise((r) => setTimeout(r, 200));
            setUploadingFiles((prev) =>
              prev.map((f) => (f.id === uploadId ? { ...f, progress } : f))
            );
          }

          // Submit claim
          setUploadingFiles((prev) =>
            prev.map((f) => (f.id === uploadId ? { ...f, status: 'processing' } : f))
          );

          const claim = await submitClaim.mutateAsync(file);

          // Auto-process the claim
          await processClaim.mutateAsync(claim.claim_id);

          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.id === uploadId
                ? { ...f, status: 'completed', claimId: claim.claim_id }
                : f
            )
          );
        } catch (error) {
          setUploadingFiles((prev) =>
            prev.map((f) =>
              f.id === uploadId
                ? { ...f, status: 'error', error: (error as Error).message }
                : f
            )
          );
        }
      }
    },
    [submitClaim, processClaim]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const clearCompleted = () => {
    setUploadingFiles((prev) => prev.filter((f) => f.status !== 'completed'));
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'submitted':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'document_processing':
        return <Loader2 className="h-4 w-4 text-yellow-500 animate-spin" />;
      case 'pending_review':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      case 'approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      submitted: 'bg-blue-500/10 text-blue-600',
      document_processing: 'bg-yellow-500/10 text-yellow-600',
      pending_review: 'bg-orange-500/10 text-orange-600',
      approved: 'bg-green-500/10 text-green-600',
      rejected: 'bg-red-500/10 text-red-600',
    };
    return styles[status] || 'bg-gray-500/10 text-gray-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">
            Inbox
          </h1>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">
            Drop documents to start processing
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 text-sm bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.8)] rounded-md transition-colors"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`relative border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-500/5'
            : 'border-[hsl(var(--border))] hover:border-[hsl(var(--muted-foreground))]'
        }`}
      >
        <Upload
          className={`h-12 w-12 mx-auto mb-4 ${
            isDragging ? 'text-blue-500' : 'text-[hsl(var(--muted-foreground))]'
          }`}
        />
        <h3 className="text-lg font-medium text-[hsl(var(--foreground))] mb-2">
          {isDragging ? 'Drop files here' : 'Drag & drop documents'}
        </h3>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">
          PDF, images, or Office documents
        </p>
        <p className="text-xs text-[hsl(var(--muted-foreground))] mt-2">
          Documents will be automatically processed with OCR, PII detection, and quality validation
        </p>
      </div>

      {/* Uploading Files */}
      {uploadingFiles.length > 0 && (
        <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-[hsl(var(--secondary))]">
            <h3 className="font-medium text-[hsl(var(--foreground))]">
              Upload Queue ({uploadingFiles.length})
            </h3>
            <button
              onClick={clearCompleted}
              className="text-sm text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            >
              Clear completed
            </button>
          </div>
          <div className="divide-y divide-[hsl(var(--border))]">
            {uploadingFiles.map((upload) => (
              <div
                key={upload.id}
                className="flex items-center gap-4 px-4 py-3"
              >
                <FileText className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                    {upload.file.name}
                  </p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    {(upload.file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {upload.status === 'uploading' && (
                    <div className="w-24 h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 transition-all"
                        style={{ width: `${upload.progress}%` }}
                      />
                    </div>
                  )}
                  {upload.status === 'processing' && (
                    <span className="flex items-center gap-1 text-sm text-yellow-600">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Processing...
                    </span>
                  )}
                  {upload.status === 'completed' && (
                    <span className="flex items-center gap-1 text-sm text-green-600">
                      <CheckCircle className="h-4 w-4" />
                      Done
                    </span>
                  )}
                  {upload.status === 'error' && (
                    <span className="flex items-center gap-1 text-sm text-red-600">
                      <XCircle className="h-4 w-4" />
                      Error
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Claims List */}
      <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
        <div className="px-4 py-3 bg-[hsl(var(--secondary))]">
          <h3 className="font-medium text-[hsl(var(--foreground))]">
            Recent Documents ({claims.length})
          </h3>
        </div>
        {claimsLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-[hsl(var(--muted-foreground))]" />
          </div>
        ) : claims.length === 0 ? (
          <div className="text-center py-12 text-[hsl(var(--muted-foreground))]">
            <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No documents yet. Drop files above to get started.</p>
          </div>
        ) : (
          <div className="divide-y divide-[hsl(var(--border))]">
            {claims.map((claim) => (
              <div
                key={claim.claim_id}
                className="flex items-center gap-4 px-4 py-3 hover:bg-[hsl(var(--secondary)/0.5)] transition-colors cursor-pointer"
                onClick={() => setSelectedClaim(claim)}
              >
                <div className="flex-shrink-0">
                  {getStatusIcon(claim.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-medium text-[hsl(var(--foreground))] truncate">
                      {claim.claim_id}
                    </p>
                    <span
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusBadge(
                        claim.status
                      )}`}
                    >
                      {claim.status.replace('_', ' ')}
                    </span>
                  </div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))] truncate">
                    {claim.description}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-[hsl(var(--foreground))]">
                    {claim.amount.toLocaleString()} {claim.currency}
                  </p>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">
                    {new Date(claim.submitted_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {claim.pii_detected && (
                    <span className="px-2 py-0.5 rounded bg-yellow-500/10 text-yellow-600 text-xs">
                      PII
                    </span>
                  )}
                  {claim.quality_score && (
                    <span className="px-2 py-0.5 rounded bg-green-500/10 text-green-600 text-xs">
                      {Math.round(claim.quality_score * 100)}%
                    </span>
                  )}
                </div>
                <Eye className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setSelectedClaim(null)}
        >
          <div
            className="bg-[hsl(var(--background))] rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b border-[hsl(var(--border))]">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">
                  {selectedClaim.claim_id}
                </h2>
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
                >
                  <XCircle className="h-5 w-5" />
                </button>
              </div>
            </div>
            <div className="px-6 py-4 space-y-4">
              {/* Status */}
              <div className="flex items-center gap-2">
                {getStatusIcon(selectedClaim.status)}
                <span
                  className={`px-2 py-0.5 rounded-full text-sm font-medium ${getStatusBadge(
                    selectedClaim.status
                  )}`}
                >
                  {selectedClaim.status.replace('_', ' ')}
                </span>
              </div>

              {/* Details */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Amount</p>
                  <p className="font-medium text-[hsl(var(--foreground))]">
                    {selectedClaim.amount.toLocaleString()} {selectedClaim.currency}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Category</p>
                  <p className="font-medium text-[hsl(var(--foreground))]">
                    {selectedClaim.category}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Submitted</p>
                  <p className="font-medium text-[hsl(var(--foreground))]">
                    {new Date(selectedClaim.submitted_at).toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Submitted By</p>
                  <p className="font-medium text-[hsl(var(--foreground))]">
                    {selectedClaim.submitted_by}
                  </p>
                </div>
              </div>

              {/* Extracted Data */}
              {selectedClaim.document_extracted && (
                <div className="border border-[hsl(var(--border))] rounded-lg p-4">
                  <h3 className="font-medium text-[hsl(var(--foreground))] mb-2">
                    Extracted Data
                  </h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {selectedClaim.extracted_vendor && (
                      <div>
                        <span className="text-[hsl(var(--muted-foreground))]">Vendor:</span>{' '}
                        {selectedClaim.extracted_vendor}
                      </div>
                    )}
                    {selectedClaim.extracted_amount && (
                      <div>
                        <span className="text-[hsl(var(--muted-foreground))]">Amount:</span>{' '}
                        {selectedClaim.extracted_amount.toLocaleString()} {selectedClaim.currency}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* PII Detection */}
              {selectedClaim.pii_detected && (
                <div className="border border-yellow-500/30 bg-yellow-500/5 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-600 mb-2">PII Detected</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedClaim.pii_types.map((type) => (
                      <span
                        key={type}
                        className="px-2 py-1 bg-yellow-500/10 text-yellow-600 text-xs rounded"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Quality Score */}
              {selectedClaim.quality_score !== null && selectedClaim.quality_score !== undefined && (
                <div className="border border-[hsl(var(--border))] rounded-lg p-4">
                  <h3 className="font-medium text-[hsl(var(--foreground))] mb-2">
                    Quality Score
                  </h3>
                  <div className="flex items-center gap-4">
                    <div className="w-full h-2 bg-[hsl(var(--secondary))] rounded-full overflow-hidden">
                      <div
                        className={`h-full ${
                          selectedClaim.quality_score >= 0.9
                            ? 'bg-green-500'
                            : selectedClaim.quality_score >= 0.7
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                        }`}
                        style={{ width: `${selectedClaim.quality_score * 100}%` }}
                      />
                    </div>
                    <span className="font-medium text-[hsl(var(--foreground))]">
                      {Math.round(selectedClaim.quality_score * 100)}%
                    </span>
                  </div>
                  {selectedClaim.quality_issues.length > 0 && (
                    <ul className="mt-2 text-sm text-[hsl(var(--muted-foreground))]">
                      {selectedClaim.quality_issues.map((issue, i) => (
                        <li key={i}>- {issue}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}

              {/* Rejection Reason */}
              {selectedClaim.rejection_reason && (
                <div className="border border-red-500/30 bg-red-500/5 rounded-lg p-4">
                  <h3 className="font-medium text-red-600 mb-2">Rejection Reason</h3>
                  <p className="text-sm text-[hsl(var(--foreground))]">
                    {selectedClaim.rejection_reason}
                  </p>
                </div>
              )}

              {/* Review Info */}
              {selectedClaim.reviewed_by && (
                <div className="border border-[hsl(var(--border))] rounded-lg p-4">
                  <h3 className="font-medium text-[hsl(var(--foreground))] mb-2">
                    Review
                  </h3>
                  <div className="text-sm">
                    <p>
                      <span className="text-[hsl(var(--muted-foreground))]">Reviewed by:</span>{' '}
                      {selectedClaim.reviewed_by}
                    </p>
                    {selectedClaim.reviewed_at && (
                      <p>
                        <span className="text-[hsl(var(--muted-foreground))]">Reviewed at:</span>{' '}
                        {new Date(selectedClaim.reviewed_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
            <div className="px-6 py-4 border-t border-[hsl(var(--border))] flex justify-end gap-2">
              <button
                onClick={() => setSelectedClaim(null)}
                className="px-4 py-2 text-sm bg-[hsl(var(--secondary))] hover:bg-[hsl(var(--secondary)/0.8)] rounded-md transition-colors"
              >
                Close
              </button>
              {selectedClaim.status === 'pending_review' && (
                <a
                  href="/decisions"
                  className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
                >
                  Review Decision
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
