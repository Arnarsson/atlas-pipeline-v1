import axios from 'axios';
import type {
  PipelineRun,
  QualityMetrics,
  PIIReport,
  Connector,
  ConnectorFormData,
  SyncHistory,
  DashboardStats,
} from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
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
  return response.data;
};

export const getPIIReport = async (runId: string): Promise<PIIReport> => {
  const response = await api.get(`/quality/pii-report/${runId}`);
  return response.data;
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
