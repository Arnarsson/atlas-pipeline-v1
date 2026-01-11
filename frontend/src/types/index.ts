// API Response Types
export interface PipelineRun {
  run_id: string;
  dataset_name: string;
  status: 'queued' | 'pending' | 'running' | 'completed' | 'failed' | 'error' | 'unknown';
  created_at?: string;
  completed_at?: string;
  current_step?: string | null;
  filename?: string;
  quality_score?: number; // 0-1
  pii_detections?: number;
}

export interface QualityMetrics {
  run_id: string;
  overall_score: number; // 0-1
  dimensions: {
    completeness: DimensionMetrics;
    uniqueness: DimensionMetrics;
    validity: DimensionMetrics;
    consistency: DimensionMetrics;
    accuracy: DimensionMetrics;
    timeliness: DimensionMetrics;
  };
  column_metrics: Record<string, ColumnMetrics>;
  details?: Record<string, any>;
}

export interface DimensionMetrics {
  score: number; // 0-1
  threshold: number; // 0-1
  passed: boolean;
  details: Record<string, any>;
}

export interface ColumnMetrics {
  completeness: number; // 0-1
  uniqueness: number; // 0-1
  validity: number; // 0-1
  data_type: string;
  null_count: number;
  unique_count: number;
}

export interface PIIDetection {
  entity_type: string;
  location: {
    row?: number;
    column?: string;
  };
  confidence?: number;
  matched_text?: string;
  start?: number;
  end?: number;
}

export interface PIIReport {
  run_id: string;
  dataset_name?: string;
  total_detections: number;
  detections_by_type: Record<string, number>;
  detections: PIIDetection[];
  compliance_status: 'compliant' | 'warning' | 'violation';
  recommendations: string[];
}

export interface Connector {
  id: string;
  name: string;
  type: 'postgresql' | 'mysql' | 'rest_api' | 'csv' | 'json';
  config?: ConnectorConfig;
  schedule?: string | null;
  status: 'active' | 'inactive' | 'error';
  last_sync?: string | null;
  created_at?: string;
}

export interface ConnectorConfig {
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  url?: string;
  headers?: Record<string, string>;
  query?: string;
}

export interface SyncHistory {
  id: string;
  connector_id: string;
  started_at: string;
  completed_at?: string;
  status: 'running' | 'completed' | 'failed';
  records_processed: number;
  error_message?: string;
}

// Form Types
export interface UploadFormData {
  file: File;
  dataset_name: string;
}

export interface ConnectorFormData {
  name: string;
  type: Connector['type'];
  config: ConnectorConfig;
  schedule?: string;
}

// Dashboard Stats
export interface DashboardStats {
  total_runs: number;
  avg_quality_score: number; // 0-1
  total_pii_detections: number;
  active_connectors: number;
  recent_runs: PipelineRun[];
  total_feature_groups?: number;
  pending_gdpr_requests?: number;
  catalog_datasets?: number;
  avg_lineage_depth?: number;
}

// Data Catalog Types
export interface Dataset {
  id: string;
  name: string;
  description?: string;
  layer: 'explore' | 'chart' | 'navigate' | 'unknown';
  schema: DatasetSchema[];
  row_count_estimate?: number;
  quality_score?: number; // 0-1
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface DatasetSchema {
  column_name: string;
  data_type: string;
  nullable: boolean;
  description?: string;
}

export interface QualityHistory {
  timestamp: string;
  overall_score: number; // 0-1
  completeness: number; // 0-1
  uniqueness: number; // 0-1
  validity: number; // 0-1
}

// Feature Store Types
export interface FeatureGroup {
  id: string;
  name: string;
  description?: string;
  version: string;
  created_at: string;
  updated_at: string;
  feature_count: number;
  features: Feature[];
}

export interface Feature {
  name: string;
  data_type: string;
  description?: string;
  importance?: number;
  null_percentage: number;
  unique_percentage: number;
}

export interface FeatureVersion {
  version: string;
  created_at: string;
  feature_count: number;
  row_count: number;
}

// GDPR Types
export interface GDPRRequest {
  id: string;
  subject_identifier: string;
  identifier_type?: 'email' | 'phone' | 'ssn' | 'customer_id' | 'unknown';
  request_type: 'export' | 'delete' | 'rectify';
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'warning';
  created_at: string;
  completed_at?: string;
  reason?: string;
  result?: GDPRResult;
}

export interface GDPRResult {
  records_found?: number;
  records_deleted?: number;
  data_export?: any;
  layers_processed?: string[];
}

// Lineage Types
export interface LineageNode {
  id: string;
  name: string;
  type: 'dataset' | 'transformation' | 'source';
  layer?: 'explore' | 'chart' | 'navigate';
  metadata?: Record<string, any>;
}

export interface LineageEdge {
  source: string;
  target: string;
  operation: string;
  created_at?: string;
}

export interface LineageGraph {
  nodes: LineageNode[];
  edges: LineageEdge[];
}
