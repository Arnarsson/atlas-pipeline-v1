import axios from 'axios';
import type {
  PipelineRun,
  QualityMetrics,
  PIIReport,
  Connector,
  ConnectorFormData,
  SyncHistory,
  DashboardStats,
  Dataset,
  FeatureGroup,
  FeatureVersion,
  GDPRRequest,
  LineageGraph,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const QUALITY_THRESHOLDS = {
  completeness: 0.95,
  uniqueness: 0.99,
  validity: 0.9,
  consistency: 0.85,
  accuracy: 0.9,
  timeliness: 0.95,
};

const normalizeRunStatus = (status?: string): PipelineRun['status'] => {
  switch (status) {
    case 'queued':
    case 'pending':
    case 'running':
    case 'completed':
    case 'failed':
    case 'error':
      return status;
    default:
      return 'unknown';
  }
};

const normalizePipelineRun = (raw: any): PipelineRun => ({
  run_id: raw.run_id,
  dataset_name: raw.dataset_name || raw.name || raw.filename || 'Unknown Dataset',
  status: normalizeRunStatus(raw.status),
  created_at: raw.created_at || raw.started_at || undefined,
  completed_at: raw.completed_at || undefined,
  current_step: raw.current_step ?? null,
  filename: raw.filename,
  quality_score: typeof raw.quality_score === 'number' ? raw.quality_score : undefined,
  pii_detections: typeof raw.pii_detections === 'number' ? raw.pii_detections : undefined,
});

const normalizeQualityMetrics = (raw: any): QualityMetrics => {
  const details = raw?.details || {};
  const allDimensions = details.all_dimensions || details.dimensions || raw?.dimensions;

  const baseDimensions = {
    completeness: {
      score: raw?.completeness_score ?? 0,
      threshold: QUALITY_THRESHOLDS.completeness,
      passed: (raw?.completeness_score ?? 0) >= QUALITY_THRESHOLDS.completeness,
      details: {},
    },
    uniqueness: {
      score: 0,
      threshold: QUALITY_THRESHOLDS.uniqueness,
      passed: false,
      details: {},
    },
    validity: {
      score: raw?.validity_score ?? 0,
      threshold: QUALITY_THRESHOLDS.validity,
      passed: (raw?.validity_score ?? 0) >= QUALITY_THRESHOLDS.validity,
      details: {},
    },
    consistency: {
      score: raw?.consistency_score ?? 0,
      threshold: QUALITY_THRESHOLDS.consistency,
      passed: (raw?.consistency_score ?? 0) >= QUALITY_THRESHOLDS.consistency,
      details: {},
    },
    accuracy: {
      score: 0,
      threshold: QUALITY_THRESHOLDS.accuracy,
      passed: false,
      details: {},
    },
    timeliness: {
      score: 0,
      threshold: QUALITY_THRESHOLDS.timeliness,
      passed: false,
      details: {},
    },
  };

  const mergedDimensions = allDimensions
    ? Object.fromEntries(
        Object.entries(baseDimensions).map(([key, fallback]) => {
          const rawDim = allDimensions[key] || {};
          const score = typeof rawDim.score === 'number' ? rawDim.score : fallback.score;
          const threshold =
            typeof rawDim.threshold === 'number' ? rawDim.threshold : fallback.threshold;
          return [
            key,
            {
              score,
              threshold,
              passed: typeof rawDim.passed === 'boolean' ? rawDim.passed : score >= threshold,
              details: rawDim.details || fallback.details,
            },
          ];
        })
      )
    : baseDimensions;

  return {
    run_id: raw.run_id,
    overall_score: raw.overall_score ?? 0,
    dimensions: mergedDimensions as QualityMetrics['dimensions'],
    column_metrics: details.column_metrics || {},
    details,
  };
};

const normalizePIIReport = (raw: any): PIIReport => {
  const findings = raw?.pii_details || raw?.detections || [];
  const detectionsByType: Record<string, number> = {};
  const detections = findings.flatMap((finding: any) => {
    const type = finding.type || finding.entity_type || 'unknown';
    const count = typeof finding.match_count === 'number' ? finding.match_count : 1;
    detectionsByType[type] = (detectionsByType[type] || 0) + count;

    if (Array.isArray(finding.sample_values) && finding.sample_values.length > 0) {
      return finding.sample_values.map((sample: string) => ({
        entity_type: type,
        location: {
          row: undefined,
          column: finding.column,
        },
        confidence: finding.confidence ?? undefined,
        matched_text: sample,
        start: finding.start ?? undefined,
        end: finding.end ?? undefined,
      }));
    }

    return [
      {
        entity_type: type,
        location: {
          row: undefined,
          column: finding.column,
        },
        confidence: finding.confidence ?? undefined,
        matched_text: finding.matched_text ?? undefined,
        start: finding.start ?? undefined,
        end: finding.end ?? undefined,
      },
    ];
  });

  const totalDetections =
    typeof raw?.total_detections === 'number'
      ? raw.total_detections
      : typeof raw?.pii_count === 'number'
      ? raw.pii_count
      : detections.length;

  const complianceStatus =
    raw?.compliance_status ||
    (totalDetections > 0 ? 'warning' : 'compliant');

  return {
    run_id: raw.run_id,
    dataset_name: raw.dataset_name,
    total_detections: totalDetections,
    detections_by_type: raw?.detections_by_type || detectionsByType,
    detections,
    compliance_status: complianceStatus === 'non_compliant' ? 'violation' : complianceStatus,
    recommendations: raw?.recommendations || [],
  };
};

const normalizeConnector = (raw: any): Connector => {
  const enabled = raw.enabled !== undefined ? raw.enabled : true;
  const lastStatus = raw.last_sync_status;

  let status: Connector['status'] = 'active';
  if (!enabled) {
    status = 'inactive';
  } else if (lastStatus === 'failed' || lastStatus === 'error') {
    status = 'error';
  }

  return {
    id: raw.connector_id || raw.id,
    name: raw.source_name || raw.name || 'Unnamed Connector',
    type: (raw.source_type || raw.type || 'rest_api') as Connector['type'],
    config: raw.config,
    schedule: raw.schedule_cron ?? raw.schedule ?? null,
    status,
    last_sync: raw.last_sync_at ?? raw.last_sync ?? null,
    created_at: raw.created_at,
  };
};

const normalizeDataset = (raw: any): Dataset => ({
  id: raw.dataset_id || raw.id,
  name: raw.name,
  description: raw.description,
  layer: raw.namespace || raw.layer || 'unknown',
  schema: raw.columns || raw.schema || [],
  row_count_estimate: raw.row_count ?? raw.row_count_estimate,
  quality_score: raw.quality_score,
  tags: raw.tags || [],
  created_at: raw.created_at || raw.last_updated || new Date().toISOString(),
  updated_at: raw.last_updated || raw.updated_at || new Date().toISOString(),
});

const normalizeFeatureGroup = (raw: any): FeatureGroup => ({
  id: raw.feature_group_id || raw.id,
  name: raw.name,
  description: raw.description,
  version: raw.version,
  created_at: raw.created_at,
  updated_at: raw.updated_at || raw.created_at,
  feature_count: raw.feature_count ?? 0,
  features: raw.features || [],
});

const normalizeFeatureVersion = (raw: any): FeatureVersion => ({
  version: raw.version,
  created_at: raw.created_at,
  feature_count: raw.feature_count ?? 0,
  row_count: raw.row_count ?? 0,
});

const normalizeGDPRRequest = (raw: any): GDPRRequest => ({
  id: raw.request_id || raw.id,
  subject_identifier: raw.subject_id || raw.subject_identifier || 'Unknown',
  identifier_type: raw.identifier_type || 'unknown',
  request_type: raw.request_type,
  status: raw.status,
  created_at: raw.requested_at || raw.created_at || new Date().toISOString(),
  completed_at: raw.completed_at || undefined,
  reason: raw.reason,
  result: raw.result,
});

const normalizeLineageGraph = (raw: any): LineageGraph => {
  if (raw?.graph) {
    return raw.graph;
  }
  return raw || { nodes: [], edges: [] };
};

const normalizeSyncHistory = (raw: any): SyncHistory => ({
  id: raw.run_id || raw.id,
  connector_id: raw.connector_id,
  started_at: raw.started_at,
  completed_at: raw.completed_at,
  status: raw.status,
  records_processed: raw.rows_processed ?? raw.records_processed ?? 0,
  error_message: raw.error_message,
});

// Pipeline endpoints
export const uploadCSV = async (file: File, datasetName: string): Promise<{ run_id: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dataset_name', datasetName);

  const response = await api.post('/pipeline/run', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getPipelineStatus = async (runId: string): Promise<PipelineRun> => {
  const response = await api.get(`/pipeline/status/${runId}`);
  return normalizePipelineRun(response.data);
};

export const getRecentRuns = async (limit: number = 10): Promise<PipelineRun[]> => {
  const response = await api.get('/pipeline/runs', { params: { limit } });
  return (response.data || []).map(normalizePipelineRun);
};

// Quality endpoints
export const getQualityMetrics = async (runId: string): Promise<QualityMetrics> => {
  const response = await api.get(`/quality/metrics/${runId}`);
  return normalizeQualityMetrics(response.data);
};

export const getPIIReport = async (runId: string): Promise<PIIReport> => {
  const response = await api.get(`/quality/pii-report/${runId}`);
  return normalizePIIReport(response.data);
};

export const getComplianceReport = async (runId: string) => {
  const response = await api.get(`/compliance/report/${runId}`);
  return response.data;
};

// Connector endpoints
export const getConnectors = async (): Promise<Connector[]> => {
  const response = await api.get('/connectors/');
  return (response.data || []).map(normalizeConnector);
};

export const getConnector = async (id: string): Promise<Connector> => {
  const response = await api.get(`/connectors/${id}`);
  return normalizeConnector(response.data);
};

export const createConnector = async (data: ConnectorFormData): Promise<Connector> => {
  const payload = {
    source_type: data.type,
    source_name: data.name,
    config: data.config,
    schedule_cron: data.schedule || null,
  };
  const response = await api.post('/connectors/', payload);
  return normalizeConnector(response.data);
};

export const updateConnector = async (id: string, data: Partial<ConnectorFormData>): Promise<Connector> => {
  const payload: Record<string, any> = {};
  if (data.type) payload.source_type = data.type;
  if (data.name) payload.source_name = data.name;
  if (data.config) payload.config = data.config;
  if (data.schedule !== undefined) payload.schedule_cron = data.schedule;
  const response = await api.put(`/connectors/${id}`, payload);
  return normalizeConnector(response.data);
};

export const deleteConnector = async (id: string): Promise<void> => {
  await api.delete(`/connectors/${id}`);
};

export const testConnection = async (
  connectorId: string
): Promise<{ success: boolean; message: string }> => {
  const response = await api.post(`/connectors/${connectorId}/test`);
  const status = response.data?.connection_status;
  return {
    success: status === 'success',
    message: response.data?.message || 'Connection test completed',
  };
};

export const triggerSync = async (connectorId: string): Promise<{ sync_id: string }> => {
  const response = await api.post(`/connectors/${connectorId}/sync`);
  return response.data;
};

export const getSyncHistory = async (connectorId: string): Promise<SyncHistory[]> => {
  const response = await api.get(`/connectors/${connectorId}/history`);
  return (response.data?.runs || []).map(normalizeSyncHistory);
};

// Dashboard endpoints
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await api.get('/dashboard/stats');
    return response.data;
  } catch (error) {
    const [runs, connectors, featureGroups, gdprRequests, datasets] = await Promise.all([
      getRecentRuns(50).catch(() => []),
      getConnectors().catch(() => []),
      getFeatureGroups().catch(() => []),
      getGDPRRequests().catch(() => []),
      searchDatasets().catch(() => []),
    ]);

    const completedRuns = runs.filter((run) => run.status === 'completed');
    const avgQuality =
      completedRuns.length > 0
        ? completedRuns.reduce((sum, run) => sum + (run.quality_score || 0), 0) /
          completedRuns.length
        : 0;

    return {
      total_runs: runs.length,
      avg_quality_score: avgQuality,
      total_pii_detections: runs.reduce((sum, run) => sum + (run.pii_detections || 0), 0),
      active_connectors: connectors.filter((c) => c.status === 'active').length,
      recent_runs: runs.slice(0, 10),
      total_feature_groups: featureGroups.length,
      pending_gdpr_requests: gdprRequests.filter((r) => r.status === 'pending').length,
      catalog_datasets: datasets.length,
      avg_lineage_depth: 0,
    };
  }
};

// Export utilities
export const downloadReport = async (runId: string, format: 'json' | 'pdf' = 'json') => {
  let payload: BlobPart;

  try {
    const response = await api.get(`/reports/${runId}`, {
      params: { format },
      responseType: 'blob',
    });
    payload = response.data;
  } catch (error) {
    const [quality, pii] = await Promise.all([
      getQualityMetrics(runId).catch(() => null),
      getPIIReport(runId).catch(() => null),
    ]);
    payload = JSON.stringify(
      {
        run_id: runId,
        quality,
        pii,
      },
      null,
      2
    );
  }

  const url = window.URL.createObjectURL(new Blob([payload]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `quality-report-${runId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

// Data Catalog endpoints
export const searchDatasets = async (query?: string, tags?: string[]) => {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  if (tags && tags.length > 0) {
    tags.forEach((tag) => params.append('tags', tag));
  }
  const response = await api.get(`/catalog/datasets${params.toString() ? `?${params.toString()}` : ''}`);
  return (response.data || []).map(normalizeDataset);
};

export const getDatasetDetails = async (datasetId: string) => {
  const response = await api.get(`/catalog/dataset/${datasetId}`);
  return normalizeDataset(response.data);
};

export const getDatasetQualityHistory = async (datasetId: string) => {
  const response = await api.get(`/catalog/dataset/${datasetId}/quality`);
  return (response.data || []).map((entry: any) => ({
    timestamp: entry.timestamp,
    overall_score: entry.overall_score ?? 0,
    completeness: entry.completeness_score ?? 0,
    uniqueness: entry.uniqueness_score ?? 0,
    validity: entry.validity_score ?? 0,
  }));
};

// Feature Store endpoints
export const getFeatureGroups = async () => {
  const response = await api.get('/features/groups');
  return (response.data || []).map(normalizeFeatureGroup);
};

export const registerFeatureGroup = async (data: FormData) => {
  const response = await api.post('/features/groups', data, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getFeatureVersions = async (name: string) => {
  const response = await api.get(`/features/${name}/versions`);
  return (response.data || []).map(normalizeFeatureVersion);
};

export const exportFeatures = async (name: string, format: string, version?: string) => {
  const response = await api.post(`/features/${name}/export`, {
    format,
    version,
  }, {
    responseType: format === 'parquet' ? 'blob' : 'json',
  });

  if (format === 'parquet') {
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${name}_${version || 'latest'}.parquet`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  }

  return response.data;
};

// GDPR endpoints
export const exportSubjectData = async (identifier: string, type: string) => {
  const response = await api.post('/gdpr/export', {
    identifier,
    identifier_type: type,
  });
  return response.data;
};

export const deleteSubjectData = async (identifier: string, type: string, reason: string) => {
  const response = await api.post('/gdpr/delete', {
    identifier,
    identifier_type: type,
    reason,
  });
  return response.data;
};

export const getGDPRRequests = async (subjectId?: string) => {
  const response = await api.get('/gdpr/requests', {
    params: { subject_id: subjectId },
  });
  return (response.data || []).map(normalizeGDPRRequest);
};

// Lineage endpoints
export const getDatasetLineage = async (name: string, depth?: number) => {
  const response = await api.get(`/lineage/dataset/${name}`, {
    params: { depth },
  });
  return normalizeLineageGraph(response.data);
};

export const getRunLineage = async (runId: string) => {
  const response = await api.get(`/lineage/run/${runId}`);
  return normalizeLineageGraph(response.data);
};
