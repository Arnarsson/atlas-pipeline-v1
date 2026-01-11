import axios from 'axios';
import type {
  PipelineRun,
  QualityMetrics,
  PIIReport,
  Connector,
  ConnectorFormData,
  SyncHistory,
  DashboardStats,
  DimensionMetrics,
  ColumnMetrics,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const QUALITY_THRESHOLDS: Record<keyof QualityMetrics['dimensions'], number> = {
  completeness: 0.95,
  uniqueness: 0.98,
  validity: 0.9,
  consistency: 0.9,
  accuracy: 0.9,
  timeliness: 0.8,
};

const normalizeDimension = (
  raw: any,
  key: keyof QualityMetrics['dimensions'],
  fallbackScore: number
): DimensionMetrics => {
  const score =
    typeof raw?.score === 'number' ? raw.score : typeof raw === 'number' ? raw : fallbackScore;
  const threshold =
    typeof raw?.threshold === 'number' ? raw.threshold : QUALITY_THRESHOLDS[key] ?? 0;
  const passed = typeof raw?.passed === 'boolean' ? raw.passed : score >= threshold;
  const details = raw?.details && typeof raw.details === 'object' ? raw.details : {};

  return { score, threshold, passed, details };
};

const normalizeColumnMetrics = (rawQuality: any): Record<string, ColumnMetrics> => {
  if (rawQuality?.column_metrics && typeof rawQuality.column_metrics === 'object') {
    return rawQuality.column_metrics;
  }

  const details = rawQuality?.details || {};
  const allDimensions = details.all_dimensions || {};
  const columns: Record<string, ColumnMetrics> = {};

  // Try week 3 format
  for (const dimension of ['completeness', 'uniqueness', 'validity']) {
    const dimDetails = allDimensions[dimension]?.details || {};
    const columnKey = `column_${dimension}`;
    if (dimDetails[columnKey]) {
      for (const [col, colData] of Object.entries(dimDetails[columnKey]) as [string, any][]) {
        if (!columns[col]) {
          columns[col] = {
            completeness: 1,
            uniqueness: 1,
            validity: 1,
            data_type: 'unknown',
            null_count: 0,
            unique_count: 0,
          };
        }
        if (dimension === 'completeness') {
          columns[col].completeness = (colData as any)?.completeness ?? columns[col].completeness;
          columns[col].null_count = (colData as any)?.missing_count ?? columns[col].null_count;
        } else if (dimension === 'uniqueness') {
          columns[col].uniqueness = (colData as any)?.uniqueness ?? columns[col].uniqueness;
          columns[col].unique_count = (colData as any)?.unique_count ?? columns[col].unique_count;
        } else if (dimension === 'validity') {
          columns[col].validity = (colData as any)?.validity ?? columns[col].validity;
        }
      }
    }
  }

  // Week 2 fallback
  const basicColumns = details.column_details || {};
  for (const [col, colData] of Object.entries(basicColumns) as [string, any][]) {
    if (!columns[col]) {
      columns[col] = {
        completeness: 1,
        uniqueness: 1,
        validity: 1,
        data_type: String((colData as any)?.dtype ?? 'unknown'),
        null_count: 0,
        unique_count: 0,
      };
    }
    const data = colData as any;
    if (typeof data?.missing_percentage === 'number') {
      columns[col].completeness = Math.max(0, Math.min(1, 1 - data.missing_percentage));
    }
    if (typeof data?.missing_count === 'number') {
      columns[col].null_count = data.missing_count;
    }
    if (typeof data?.unique_percentage === 'number') {
      columns[col].uniqueness = Math.max(0, Math.min(1, data.unique_percentage));
    }
    if (typeof data?.unique_count === 'number') {
      columns[col].unique_count = data.unique_count;
    }
  }

  return columns;
};

const normalizeQualityMetrics = (raw: any): QualityMetrics => {
  const dimensionsRaw =
    raw?.dimensions ||
    raw?.details?.all_dimensions || {
      completeness: raw?.completeness_score,
      uniqueness: raw?.uniqueness_score,
      validity: raw?.validity_score,
      consistency: raw?.consistency_score,
      accuracy: raw?.accuracy_score,
      timeliness: raw?.timeliness_score,
    };

  const dimensions = {
    completeness: normalizeDimension(dimensionsRaw?.completeness, 'completeness', raw?.completeness_score ?? 0),
    uniqueness: normalizeDimension(dimensionsRaw?.uniqueness, 'uniqueness', raw?.uniqueness_score ?? 0),
    validity: normalizeDimension(dimensionsRaw?.validity, 'validity', raw?.validity_score ?? 0),
    consistency: normalizeDimension(dimensionsRaw?.consistency, 'consistency', raw?.consistency_score ?? 0),
    accuracy: normalizeDimension(dimensionsRaw?.accuracy, 'accuracy', raw?.accuracy_score ?? 0),
    timeliness: normalizeDimension(dimensionsRaw?.timeliness, 'timeliness', raw?.timeliness_score ?? 0),
  };

  return {
    run_id: raw?.run_id,
    dataset_name: raw?.dataset_name,
    overall_score: raw?.overall_score ?? 0,
    dimensions,
    column_metrics: normalizeColumnMetrics(raw),
  };
};

const normalizePIIReport = (raw: any): PIIReport => ({
  run_id: raw?.run_id,
  dataset_name: raw?.dataset_name || 'unknown',
  total_detections: raw?.total_detections ?? 0,
  detections_by_type: raw?.detections_by_type || {},
  detections: raw?.detections || [],
  compliance_status: raw?.compliance_status || 'compliant',
  recommendations: raw?.recommendations || [],
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
  return response.data;
};

export const getRecentRuns = async (limit: number = 10): Promise<PipelineRun[]> => {
  const response = await api.get('/pipeline/runs', { params: { limit } });
  return response.data;
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
  return response.data;
};

export const getConnector = async (id: string): Promise<Connector> => {
  const response = await api.get(`/connectors/${id}`);
  return response.data;
};

export const createConnector = async (data: ConnectorFormData): Promise<Connector> => {
  const response = await api.post('/connectors/', data);
  return response.data;
};

export const updateConnector = async (id: string, data: Partial<ConnectorFormData>): Promise<Connector> => {
  const response = await api.put(`/connectors/${id}`, data);
  return response.data;
};

export const deleteConnector = async (id: string): Promise<void> => {
  await api.delete(`/connectors/${id}`);
};

export const testConnection = async (config: ConnectorFormData): Promise<{ success: boolean; message: string }> => {
  const response = await api.post('/connectors/test', config);
  return response.data;
};

export const triggerSync = async (connectorId: string): Promise<{ sync_id: string }> => {
  const response = await api.post(`/connectors/${connectorId}/sync`);
  return response.data;
};

export const getSyncHistory = async (connectorId: string): Promise<SyncHistory[]> => {
  const response = await api.get(`/connectors/${connectorId}/history`);
  return response.data;
};

// Dashboard endpoints
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

// Export utilities
export const downloadReport = async (runId: string, format: 'json' | 'pdf' = 'json') => {
  const response = await api.get(`/reports/${runId}`, {
    params: { format },
    responseType: 'blob',
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `quality-report-${runId}.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
};

// Data Catalog endpoints
export const searchDatasets = async (query?: string, tags?: string[]) => {
  const response = await api.get('/catalog/datasets', {
    params: {
      query,
      tags: tags?.join(','),
    },
  });
  return response.data;
};

export const getDatasetDetails = async (datasetId: string) => {
  const response = await api.get(`/catalog/dataset/${datasetId}`);
  return response.data;
};

export const getDatasetQualityHistory = async (datasetId: string) => {
  const response = await api.get(`/catalog/dataset/${datasetId}/quality`);
  return response.data;
};

// Feature Store endpoints
export const getFeatureGroups = async () => {
  const response = await api.get('/features/groups');
  return response.data;
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
  return response.data;
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
  return response.data;
};

// Lineage endpoints
export const getDatasetLineage = async (name: string, depth?: number) => {
  const response = await api.get(`/lineage/dataset/${name}`, {
    params: { depth },
  });
  return response.data;
};

export const getRunLineage = async (runId: string) => {
  const response = await api.get(`/lineage/run/${runId}`);
  return response.data;
};
