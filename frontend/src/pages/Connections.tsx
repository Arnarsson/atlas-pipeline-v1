import { useState, useMemo } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Database,
  Plus,
  Search,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronRight,
  ChevronDown,
  Trash2,
  Play,
  Pause,
  MoreVertical,
  Zap,
  AlertTriangle,
  Calendar,
  Eye,
  Download,
  X,
  Check,
  TrendingUp,
  ExternalLink,
  Terminal,
  Save,
} from 'lucide-react';
import toast from 'react-hot-toast';

// ============================================================================
// TYPES
// ============================================================================

interface Connection {
  id: string;
  name: string;
  connector_type: string;
  connector_icon: string;
  status: 'active' | 'paused' | 'error' | 'syncing' | 'pending';
  destination: string;
  last_sync: string | null;
  next_sync: string | null;
  sync_frequency: string;
  records_synced: number;
  schema_change: boolean;
  error_message?: string;
  streams: StreamConfig[];
  created_at: string;
}

interface StreamConfig {
  name: string;
  sync_mode: 'full_refresh' | 'incremental' | 'cdc';
  destination_sync_mode: 'overwrite' | 'append' | 'append_dedup';
  cursor_field?: string;
  primary_key?: string[];
  enabled: boolean;
  records: number;
  last_sync?: string;
}

interface Connector {
  id: string;
  name: string;
  icon: string;
  category: string;
  description: string;
  auth_type: 'oauth' | 'api_key' | 'basic' | 'service_account';
  docs_url: string;
  popular: boolean;
}

interface SyncRun {
  id: string;
  connection_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  records_synced: number;
  bytes_synced: number;
  error?: string;
  streams: { name: string; records: number; status: string }[];
}

interface UsageMetrics {
  total_records: number;
  total_connections: number;
  active_connections: number;
  failed_syncs_24h: number;
  records_today: number;
  records_this_month: number;
  api_calls_today: number;
  sync_time_today_minutes: number;
}

// ============================================================================
// DEMO DATA
// ============================================================================

const DEMO_CONNECTIONS: Connection[] = [
  {
    id: 'conn_1',
    name: 'Production PostgreSQL',
    connector_type: 'postgresql',
    connector_icon: '🐘',
    status: 'active',
    destination: 'Atlas Data Warehouse',
    last_sync: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    next_sync: new Date(Date.now() + 1000 * 60 * 45).toISOString(),
    sync_frequency: 'Every hour',
    records_synced: 2847392,
    schema_change: false,
    streams: [
      { name: 'users', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'updated_at', primary_key: ['id'], enabled: true, records: 124500, last_sync: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
      { name: 'orders', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'created_at', primary_key: ['id'], enabled: true, records: 892341, last_sync: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
      { name: 'products', sync_mode: 'full_refresh', destination_sync_mode: 'overwrite', enabled: true, records: 15420, last_sync: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
      { name: 'inventory', sync_mode: 'cdc', destination_sync_mode: 'append_dedup', primary_key: ['sku'], enabled: true, records: 45231, last_sync: new Date(Date.now() - 1000 * 60 * 15).toISOString() },
    ],
    created_at: '2024-06-15T10:00:00Z',
  },
  {
    id: 'conn_2',
    name: 'Stripe Payments',
    connector_type: 'stripe',
    connector_icon: '💳',
    status: 'syncing',
    destination: 'Atlas Data Warehouse',
    last_sync: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    next_sync: null,
    sync_frequency: 'Every 6 hours',
    records_synced: 543289,
    schema_change: true,
    streams: [
      { name: 'charges', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'created', enabled: true, records: 234521 },
      { name: 'customers', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'created', primary_key: ['id'], enabled: true, records: 89234 },
      { name: 'subscriptions', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'current_period_start', primary_key: ['id'], enabled: true, records: 12453 },
      { name: 'invoices', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'created', enabled: true, records: 156234 },
      { name: 'refunds', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'created', enabled: false, records: 0 },
    ],
    created_at: '2024-08-20T14:30:00Z',
  },
  {
    id: 'conn_3',
    name: 'Salesforce CRM',
    connector_type: 'salesforce',
    connector_icon: '☁️',
    status: 'error',
    destination: 'Atlas Data Warehouse',
    last_sync: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    next_sync: null,
    sync_frequency: 'Every 12 hours',
    records_synced: 1234567,
    schema_change: false,
    error_message: 'Authentication failed: OAuth token expired. Please re-authenticate.',
    streams: [
      { name: 'Account', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'LastModifiedDate', primary_key: ['Id'], enabled: true, records: 45234 },
      { name: 'Contact', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'LastModifiedDate', primary_key: ['Id'], enabled: true, records: 123456 },
      { name: 'Opportunity', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'LastModifiedDate', primary_key: ['Id'], enabled: true, records: 34521 },
      { name: 'Lead', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'LastModifiedDate', primary_key: ['Id'], enabled: true, records: 89123 },
    ],
    created_at: '2024-05-10T09:00:00Z',
  },
  {
    id: 'conn_4',
    name: 'HubSpot Marketing',
    connector_type: 'hubspot',
    connector_icon: '🧡',
    status: 'active',
    destination: 'Atlas Data Warehouse',
    last_sync: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    next_sync: new Date(Date.now() + 1000 * 60 * 90).toISOString(),
    sync_frequency: 'Every 2 hours',
    records_synced: 892341,
    schema_change: false,
    streams: [
      { name: 'contacts', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'updatedAt', primary_key: ['id'], enabled: true, records: 234521 },
      { name: 'companies', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'updatedAt', primary_key: ['id'], enabled: true, records: 12453 },
      { name: 'deals', sync_mode: 'incremental', destination_sync_mode: 'append_dedup', cursor_field: 'updatedAt', primary_key: ['id'], enabled: true, records: 45234 },
      { name: 'email_events', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'created', enabled: true, records: 456234 },
    ],
    created_at: '2024-07-01T11:00:00Z',
  },
  {
    id: 'conn_5',
    name: 'Google Analytics',
    connector_type: 'google_analytics',
    connector_icon: '📊',
    status: 'paused',
    destination: 'Atlas Data Warehouse',
    last_sync: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
    next_sync: null,
    sync_frequency: 'Daily at 6 AM',
    records_synced: 4523891,
    schema_change: false,
    streams: [
      { name: 'sessions', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'date', enabled: true, records: 2345123 },
      { name: 'pageviews', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'date', enabled: true, records: 1234567 },
      { name: 'events', sync_mode: 'incremental', destination_sync_mode: 'append', cursor_field: 'date', enabled: false, records: 0 },
    ],
    created_at: '2024-04-20T08:00:00Z',
  },
];

const DEMO_CONNECTORS: Connector[] = [
  // Databases
  { id: 'postgresql', name: 'PostgreSQL', icon: '🐘', category: 'Database', description: 'Open-source relational database', auth_type: 'basic', docs_url: '#', popular: true },
  { id: 'mysql', name: 'MySQL', icon: '🐬', category: 'Database', description: 'Popular open-source database', auth_type: 'basic', docs_url: '#', popular: true },
  { id: 'mongodb', name: 'MongoDB', icon: '🍃', category: 'Database', description: 'NoSQL document database', auth_type: 'basic', docs_url: '#', popular: true },
  { id: 'snowflake', name: 'Snowflake', icon: '❄️', category: 'Database', description: 'Cloud data warehouse', auth_type: 'basic', docs_url: '#', popular: true },
  { id: 'bigquery', name: 'BigQuery', icon: '🔷', category: 'Database', description: 'Google cloud data warehouse', auth_type: 'service_account', docs_url: '#', popular: true },
  { id: 'redshift', name: 'Redshift', icon: '🔴', category: 'Database', description: 'AWS data warehouse', auth_type: 'basic', docs_url: '#', popular: false },
  { id: 'mssql', name: 'SQL Server', icon: '🗄️', category: 'Database', description: 'Microsoft SQL Server', auth_type: 'basic', docs_url: '#', popular: false },
  // CRM
  { id: 'salesforce', name: 'Salesforce', icon: '☁️', category: 'CRM', description: 'Enterprise CRM platform', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'hubspot', name: 'HubSpot', icon: '🧡', category: 'CRM', description: 'Marketing and sales platform', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'pipedrive', name: 'Pipedrive', icon: '🎯', category: 'CRM', description: 'Sales CRM and pipeline', auth_type: 'api_key', docs_url: '#', popular: false },
  { id: 'zoho_crm', name: 'Zoho CRM', icon: '📘', category: 'CRM', description: 'Business CRM solution', auth_type: 'oauth', docs_url: '#', popular: false },
  // Payments
  { id: 'stripe', name: 'Stripe', icon: '💳', category: 'Payments', description: 'Payment processing', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 'paypal', name: 'PayPal', icon: '💰', category: 'Payments', description: 'Online payments', auth_type: 'oauth', docs_url: '#', popular: false },
  { id: 'square', name: 'Square', icon: '⬛', category: 'Payments', description: 'Point of sale payments', auth_type: 'oauth', docs_url: '#', popular: false },
  // Analytics
  { id: 'google_analytics', name: 'Google Analytics', icon: '📊', category: 'Analytics', description: 'Web analytics service', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'mixpanel', name: 'Mixpanel', icon: '📈', category: 'Analytics', description: 'Product analytics', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 'amplitude', name: 'Amplitude', icon: '📉', category: 'Analytics', description: 'Digital analytics platform', auth_type: 'api_key', docs_url: '#', popular: false },
  { id: 'segment', name: 'Segment', icon: '🟢', category: 'Analytics', description: 'Customer data platform', auth_type: 'api_key', docs_url: '#', popular: true },
  // Marketing
  { id: 'mailchimp', name: 'Mailchimp', icon: '🐵', category: 'Marketing', description: 'Email marketing platform', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'sendgrid', name: 'SendGrid', icon: '📧', category: 'Marketing', description: 'Email delivery service', auth_type: 'api_key', docs_url: '#', popular: false },
  { id: 'facebook_ads', name: 'Facebook Ads', icon: '📘', category: 'Marketing', description: 'Social media advertising', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'google_ads', name: 'Google Ads', icon: '🔍', category: 'Marketing', description: 'Search advertising', auth_type: 'oauth', docs_url: '#', popular: true },
  // E-commerce
  { id: 'shopify', name: 'Shopify', icon: '🛍️', category: 'E-commerce', description: 'E-commerce platform', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'woocommerce', name: 'WooCommerce', icon: '🛒', category: 'E-commerce', description: 'WordPress e-commerce', auth_type: 'api_key', docs_url: '#', popular: false },
  { id: 'amazon_seller', name: 'Amazon Seller', icon: '📦', category: 'E-commerce', description: 'Amazon marketplace', auth_type: 'oauth', docs_url: '#', popular: false },
  // Project Management
  { id: 'jira', name: 'Jira', icon: '🔵', category: 'Project Management', description: 'Issue tracking', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'asana', name: 'Asana', icon: '🎯', category: 'Project Management', description: 'Work management', auth_type: 'oauth', docs_url: '#', popular: false },
  { id: 'linear', name: 'Linear', icon: '📐', category: 'Project Management', description: 'Modern issue tracking', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 'notion', name: 'Notion', icon: '📝', category: 'Project Management', description: 'All-in-one workspace', auth_type: 'oauth', docs_url: '#', popular: true },
  // Support
  { id: 'zendesk', name: 'Zendesk', icon: '🎧', category: 'Support', description: 'Customer service platform', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'intercom', name: 'Intercom', icon: '💬', category: 'Support', description: 'Customer messaging', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 'freshdesk', name: 'Freshdesk', icon: '🌿', category: 'Support', description: 'Help desk software', auth_type: 'api_key', docs_url: '#', popular: false },
  // Files
  { id: 'google_sheets', name: 'Google Sheets', icon: '📗', category: 'Files', description: 'Spreadsheet application', auth_type: 'oauth', docs_url: '#', popular: true },
  { id: 'airtable', name: 'Airtable', icon: '📋', category: 'Files', description: 'Spreadsheet-database hybrid', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 's3', name: 'Amazon S3', icon: '🪣', category: 'Files', description: 'Cloud object storage', auth_type: 'api_key', docs_url: '#', popular: true },
  { id: 'gcs', name: 'Google Cloud Storage', icon: '☁️', category: 'Files', description: 'Cloud storage service', auth_type: 'service_account', docs_url: '#', popular: false },
];

const DEMO_SYNC_HISTORY: SyncRun[] = [
  {
    id: 'run_1',
    connection_id: 'conn_1',
    status: 'completed',
    started_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    records_synced: 15234,
    bytes_synced: 2500000,
    streams: [
      { name: 'users', records: 234, status: 'completed' },
      { name: 'orders', records: 12500, status: 'completed' },
      { name: 'products', records: 0, status: 'skipped' },
      { name: 'inventory', records: 2500, status: 'completed' },
    ],
  },
  {
    id: 'run_2',
    connection_id: 'conn_1',
    status: 'completed',
    started_at: new Date(Date.now() - 1000 * 60 * 75).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 72).toISOString(),
    records_synced: 8921,
    bytes_synced: 1800000,
    streams: [
      { name: 'users', records: 121, status: 'completed' },
      { name: 'orders', records: 8000, status: 'completed' },
      { name: 'products', records: 0, status: 'skipped' },
      { name: 'inventory', records: 800, status: 'completed' },
    ],
  },
  {
    id: 'run_3',
    connection_id: 'conn_2',
    status: 'running',
    started_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    records_synced: 45234,
    bytes_synced: 8500000,
    streams: [
      { name: 'charges', records: 25234, status: 'completed' },
      { name: 'customers', records: 15000, status: 'running' },
      { name: 'subscriptions', records: 5000, status: 'pending' },
      { name: 'invoices', records: 0, status: 'pending' },
    ],
  },
  {
    id: 'run_4',
    connection_id: 'conn_3',
    status: 'failed',
    started_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
    completed_at: new Date(Date.now() - 1000 * 60 * 60 * 24 + 1000 * 60 * 2).toISOString(),
    records_synced: 0,
    bytes_synced: 0,
    error: 'Authentication failed: OAuth token expired. Please re-authenticate.',
    streams: [],
  },
];

const DEMO_METRICS: UsageMetrics = {
  total_records: 10_543_289,
  total_connections: 5,
  active_connections: 3,
  failed_syncs_24h: 1,
  records_today: 234_521,
  records_this_month: 4_523_891,
  api_calls_today: 12_453,
  sync_time_today_minutes: 45,
};

const CATEGORIES = ['All', 'Database', 'CRM', 'Payments', 'Analytics', 'Marketing', 'E-commerce', 'Project Management', 'Support', 'Files'];

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}

function formatBytes(bytes: number): string {
  if (bytes >= 1_000_000_000) return `${(bytes / 1_000_000_000).toFixed(1)} GB`;
  if (bytes >= 1_000_000) return `${(bytes / 1_000_000).toFixed(1)} MB`;
  if (bytes >= 1_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${bytes} B`;
}

function timeAgo(date: string): string {
  const seconds = Math.floor((Date.now() - new Date(date).getTime()) / 1000);
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function getStatusColor(status: string): { bg: string; text: string; icon: React.ReactNode } {
  switch (status) {
    case 'active':
    case 'completed':
      return { bg: 'bg-green-500/10', text: 'text-green-600', icon: <CheckCircle2 className="w-4 h-4" /> };
    case 'syncing':
    case 'running':
      return { bg: 'bg-blue-500/10', text: 'text-blue-600', icon: <RefreshCw className="w-4 h-4 animate-spin" /> };
    case 'paused':
    case 'pending':
      return { bg: 'bg-yellow-500/10', text: 'text-yellow-600', icon: <Pause className="w-4 h-4" /> };
    case 'error':
    case 'failed':
      return { bg: 'bg-red-500/10', text: 'text-red-600', icon: <XCircle className="w-4 h-4" /> };
    default:
      return { bg: 'bg-gray-500/10', text: 'text-gray-600', icon: <Clock className="w-4 h-4" /> };
  }
}

// ============================================================================
// COMPONENTS
// ============================================================================

function MetricCard({ title, value, subtitle, icon, trend }: { title: string; value: string | number; subtitle?: string; icon: React.ReactNode; trend?: { value: number; positive: boolean } }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-[hsl(var(--muted-foreground))]">{title}</p>
            <p className="text-2xl font-semibold text-[hsl(var(--foreground))] mt-1">
              {typeof value === 'number' ? formatNumber(value) : value}
            </p>
            {subtitle && (
              <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">{subtitle}</p>
            )}
            {trend && (
              <div className={`flex items-center gap-1 mt-2 text-xs ${trend.positive ? 'text-green-600' : 'text-red-600'}`}>
                <TrendingUp className={`w-3 h-3 ${!trend.positive && 'rotate-180'}`} />
                <span>{trend.value}% vs last week</span>
              </div>
            )}
          </div>
          <div className="p-2 rounded-lg bg-[hsl(var(--secondary))]">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ConnectionCard({ connection, onClick, onSync, onPause }: { connection: Connection; onClick: () => void; onSync: () => void; onPause: () => void }) {
  const status = getStatusColor(connection.status);
  const enabledStreams = connection.streams.filter(s => s.enabled).length;

  return (
    <Card className="hover:border-[hsl(var(--foreground)/0.2)] transition-all cursor-pointer group">
      <CardContent className="p-0">
        <div className="p-4" onClick={onClick}>
          {/* Header */}
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center gap-3">
              <div className="text-2xl">{connection.connector_icon}</div>
              <div>
                <h3 className="font-semibold text-[hsl(var(--foreground))]">{connection.name}</h3>
                <p className="text-xs text-[hsl(var(--muted-foreground))] capitalize">{connection.connector_type.replace(/_/g, ' ')}</p>
              </div>
            </div>
            <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${status.bg} ${status.text}`}>
              {status.icon}
              <span className="capitalize">{connection.status}</span>
            </div>
          </div>

          {/* Schema Change Alert */}
          {connection.schema_change && (
            <div className="mb-3 p-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-600" />
              <span className="text-xs text-yellow-600">Schema change detected</span>
            </div>
          )}

          {/* Error Message */}
          {connection.error_message && (
            <div className="mb-3 p-2 rounded-lg bg-red-500/10 border border-red-500/20">
              <p className="text-xs text-red-600 line-clamp-2">{connection.error_message}</p>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Records</p>
              <p className="text-sm font-semibold text-[hsl(var(--foreground))]">{formatNumber(connection.records_synced)}</p>
            </div>
            <div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Streams</p>
              <p className="text-sm font-semibold text-[hsl(var(--foreground))]">{enabledStreams}/{connection.streams.length}</p>
            </div>
            <div>
              <p className="text-xs text-[hsl(var(--muted-foreground))]">Frequency</p>
              <p className="text-sm font-semibold text-[hsl(var(--foreground))] truncate">{connection.sync_frequency}</p>
            </div>
          </div>

          {/* Last Sync */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1 text-[hsl(var(--muted-foreground))]">
              <Clock className="w-3 h-3" />
              <span>Last sync: {connection.last_sync ? timeAgo(connection.last_sync) : 'Never'}</span>
            </div>
            {connection.next_sync && (
              <span className="text-[hsl(var(--muted-foreground))]">
                Next: {timeAgo(connection.next_sync).replace(' ago', '')}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="border-t border-[hsl(var(--border))] px-4 py-2 flex items-center justify-between bg-[hsl(var(--secondary)/0.3)]">
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => { e.stopPropagation(); onSync(); }}
              disabled={connection.status === 'syncing'}
              className="h-7 text-xs"
            >
              <Play className="w-3 h-3 mr-1" />
              Sync Now
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={(e) => { e.stopPropagation(); onPause(); }}
              className="h-7 text-xs"
            >
              {connection.status === 'paused' ? (
                <>
                  <Play className="w-3 h-3 mr-1" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="w-3 h-3 mr-1" />
                  Pause
                </>
              )}
            </Button>
          </div>
          <Button size="sm" variant="ghost" className="h-7 w-7 p-0" onClick={(e) => e.stopPropagation()}>
            <MoreVertical className="w-4 h-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function ConnectorCard({ connector, onSelect }: { connector: Connector; onSelect: () => void }) {
  return (
    <Card
      className="hover:border-[hsl(var(--foreground)/0.2)] transition-all cursor-pointer group"
      onClick={onSelect}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-3">
          <div className="text-2xl">{connector.icon}</div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-[hsl(var(--foreground))]">{connector.name}</h3>
              {connector.popular && (
                <span className="px-1.5 py-0.5 text-[10px] rounded bg-blue-500/10 text-blue-600 font-medium">Popular</span>
              )}
            </div>
            <p className="text-xs text-[hsl(var(--muted-foreground))] mt-0.5 line-clamp-1">{connector.description}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 text-[10px] rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]">
                {connector.category}
              </span>
              <span className="px-2 py-0.5 text-[10px] rounded bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] capitalize">
                {connector.auth_type.replace('_', ' ')}
              </span>
            </div>
          </div>
          <ChevronRight className="w-4 h-4 text-[hsl(var(--muted-foreground))] opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>
      </CardContent>
    </Card>
  );
}

function SyncHistoryRow({ run }: { run: SyncRun }) {
  const [expanded, setExpanded] = useState(false);
  const status = getStatusColor(run.status);
  const duration = run.completed_at
    ? Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000 / 60)
    : null;

  return (
    <div className="border-b border-[hsl(var(--border))] last:border-0">
      <div
        className="p-3 flex items-center gap-4 hover:bg-[hsl(var(--secondary)/0.5)] cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className={`p-1.5 rounded ${status.bg}`}>
          {status.icon}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-sm font-medium capitalize ${status.text}`}>{run.status}</span>
            <span className="text-xs text-[hsl(var(--muted-foreground))]">
              {timeAgo(run.started_at)}
            </span>
          </div>
          {run.error && (
            <p className="text-xs text-red-600 mt-0.5 truncate">{run.error}</p>
          )}
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-[hsl(var(--foreground))]">{formatNumber(run.records_synced)} records</p>
          <p className="text-xs text-[hsl(var(--muted-foreground))]">
            {formatBytes(run.bytes_synced)} • {duration ? `${duration}m` : 'Running...'}
          </p>
        </div>
        <ChevronDown className={`w-4 h-4 text-[hsl(var(--muted-foreground))] transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </div>

      {expanded && run.streams.length > 0 && (
        <div className="px-4 pb-3 pt-1 bg-[hsl(var(--secondary)/0.3)]">
          <div className="grid grid-cols-3 gap-2 text-xs font-medium text-[hsl(var(--muted-foreground))] mb-2 px-2">
            <span>Stream</span>
            <span>Records</span>
            <span>Status</span>
          </div>
          {run.streams.map((stream, idx) => {
            const streamStatus = getStatusColor(stream.status);
            return (
              <div key={idx} className="grid grid-cols-3 gap-2 text-xs py-1.5 px-2 rounded hover:bg-[hsl(var(--secondary))]">
                <span className="font-medium text-[hsl(var(--foreground))]">{stream.name}</span>
                <span className="text-[hsl(var(--muted-foreground))]">{formatNumber(stream.records)}</span>
                <span className={`capitalize ${streamStatus.text}`}>{stream.status}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StreamConfigRow({ stream, onChange }: { stream: StreamConfig; onChange: (updates: Partial<StreamConfig>) => void }) {
  return (
    <div className={`grid grid-cols-12 gap-3 items-center py-3 px-4 border-b border-[hsl(var(--border))] last:border-0 ${!stream.enabled ? 'opacity-50' : ''}`}>
      <div className="col-span-1">
        <input
          type="checkbox"
          checked={stream.enabled}
          onChange={(e) => onChange({ enabled: e.target.checked })}
          className="w-4 h-4 rounded border-[hsl(var(--border))]"
        />
      </div>
      <div className="col-span-3">
        <p className="font-medium text-sm text-[hsl(var(--foreground))]">{stream.name}</p>
        {stream.records > 0 && (
          <p className="text-xs text-[hsl(var(--muted-foreground))]">{formatNumber(stream.records)} rows</p>
        )}
      </div>
      <div className="col-span-3">
        <select
          value={stream.sync_mode}
          onChange={(e) => onChange({ sync_mode: e.target.value as StreamConfig['sync_mode'] })}
          disabled={!stream.enabled}
          className="w-full px-2 py-1 text-xs border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
        >
          <option value="full_refresh">Full Refresh</option>
          <option value="incremental">Incremental</option>
          <option value="cdc">CDC (Change Data Capture)</option>
        </select>
      </div>
      <div className="col-span-3">
        <select
          value={stream.destination_sync_mode}
          onChange={(e) => onChange({ destination_sync_mode: e.target.value as StreamConfig['destination_sync_mode'] })}
          disabled={!stream.enabled}
          className="w-full px-2 py-1 text-xs border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
        >
          <option value="overwrite">Overwrite</option>
          <option value="append">Append</option>
          <option value="append_dedup">Append + Dedup</option>
        </select>
      </div>
      <div className="col-span-2 text-right">
        {stream.cursor_field && (
          <span className="text-xs text-[hsl(var(--muted-foreground))]">
            Cursor: {stream.cursor_field}
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// CONNECTION DETAIL MODAL
// ============================================================================

function ConnectionDetailModal({ connection, onClose }: { connection: Connection; onClose: () => void }) {
  const [activeTab, setActiveTab] = useState<'overview' | 'streams' | 'history' | 'settings'>('overview');
  const [streams, setStreams] = useState(connection.streams);
  const history = DEMO_SYNC_HISTORY.filter(r => r.connection_id === connection.id);
  const status = getStatusColor(connection.status);

  const handleStreamChange = (index: number, updates: Partial<StreamConfig>) => {
    const newStreams = [...streams];
    newStreams[index] = { ...newStreams[index], ...updates };
    setStreams(newStreams);
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-8 pb-8 overflow-y-auto">
      <div className="bg-[hsl(var(--card))] rounded-lg w-full max-w-4xl border border-[hsl(var(--border))] shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-[hsl(var(--border))] sticky top-0 bg-[hsl(var(--card))] rounded-t-lg z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-3xl">{connection.connector_icon}</div>
              <div>
                <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">{connection.name}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${status.bg} ${status.text}`}>
                    {status.icon}
                    <span className="capitalize">{connection.status}</span>
                  </span>
                  <span className="text-xs text-[hsl(var(--muted-foreground))]">
                    {connection.connector_type} → {connection.destination}
                  </span>
                </div>
              </div>
            </div>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4">
            {(['overview', 'streams', 'history', 'settings'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors capitalize ${
                  activeTab === tab
                    ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                    : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary))]'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Error Alert */}
              {connection.error_message && (
                <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                  <div className="flex items-start gap-3">
                    <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-red-600">Sync Error</h4>
                      <p className="text-sm text-red-600 mt-1">{connection.error_message}</p>
                      <Button size="sm" className="mt-3 bg-red-600 hover:bg-red-700 text-white">
                        Re-authenticate
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Stats Grid */}
              <div className="grid grid-cols-4 gap-4">
                <div className="p-4 rounded-lg bg-[hsl(var(--secondary))]">
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Total Records</p>
                  <p className="text-2xl font-semibold text-[hsl(var(--foreground))] mt-1">{formatNumber(connection.records_synced)}</p>
                </div>
                <div className="p-4 rounded-lg bg-[hsl(var(--secondary))]">
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Active Streams</p>
                  <p className="text-2xl font-semibold text-[hsl(var(--foreground))] mt-1">
                    {streams.filter(s => s.enabled).length}/{streams.length}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-[hsl(var(--secondary))]">
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Last Sync</p>
                  <p className="text-2xl font-semibold text-[hsl(var(--foreground))] mt-1">
                    {connection.last_sync ? timeAgo(connection.last_sync) : 'Never'}
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-[hsl(var(--secondary))]">
                  <p className="text-xs text-[hsl(var(--muted-foreground))]">Sync Frequency</p>
                  <p className="text-lg font-semibold text-[hsl(var(--foreground))] mt-1">{connection.sync_frequency}</p>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="flex gap-3">
                <Button disabled={connection.status === 'syncing'}>
                  <Play className="w-4 h-4 mr-2" />
                  Sync Now
                </Button>
                <Button variant="outline">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh Schema
                </Button>
                <Button variant="outline">
                  <Eye className="w-4 h-4 mr-2" />
                  Preview Data
                </Button>
                <Button variant="outline">
                  <Terminal className="w-4 h-4 mr-2" />
                  View Logs
                </Button>
              </div>

              {/* Recent Syncs */}
              <div>
                <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">Recent Syncs</h3>
                <Card>
                  <CardContent className="p-0">
                    {history.length > 0 ? (
                      history.slice(0, 3).map((run) => <SyncHistoryRow key={run.id} run={run} />)
                    ) : (
                      <div className="p-8 text-center text-[hsl(var(--muted-foreground))]">
                        <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p>No sync history yet</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'streams' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-[hsl(var(--foreground))]">Stream Configuration</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    Select which streams to sync and configure sync modes
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm">
                    <Check className="w-4 h-4 mr-2" />
                    Select All
                  </Button>
                  <Button size="sm">
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </Button>
                </div>
              </div>

              <Card>
                <CardContent className="p-0">
                  {/* Header */}
                  <div className="grid grid-cols-12 gap-3 items-center py-2 px-4 bg-[hsl(var(--secondary))] text-xs font-medium text-[hsl(var(--muted-foreground))] border-b border-[hsl(var(--border))]">
                    <div className="col-span-1">Sync</div>
                    <div className="col-span-3">Stream</div>
                    <div className="col-span-3">Sync Mode</div>
                    <div className="col-span-3">Destination Mode</div>
                    <div className="col-span-2 text-right">Cursor</div>
                  </div>
                  {/* Rows */}
                  {streams.map((stream, idx) => (
                    <StreamConfigRow
                      key={stream.name}
                      stream={stream}
                      onChange={(updates) => handleStreamChange(idx, updates)}
                    />
                  ))}
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'history' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-[hsl(var(--foreground))]">Sync History</h3>
                <Button variant="outline" size="sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export Logs
                </Button>
              </div>

              <Card>
                <CardContent className="p-0">
                  {history.length > 0 ? (
                    history.map((run) => <SyncHistoryRow key={run.id} run={run} />)
                  ) : (
                    <div className="p-12 text-center text-[hsl(var(--muted-foreground))]">
                      <Calendar className="w-12 h-12 mx-auto mb-3 opacity-50" />
                      <h4 className="font-medium text-[hsl(var(--foreground))]">No sync history</h4>
                      <p className="text-sm mt-1">Run your first sync to see history here</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-6">
              <Card>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-4">Sync Schedule</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Frequency</label>
                      <select className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                        <option>Every 15 minutes</option>
                        <option>Every 30 minutes</option>
                        <option selected>Every hour</option>
                        <option>Every 2 hours</option>
                        <option>Every 6 hours</option>
                        <option>Every 12 hours</option>
                        <option>Daily</option>
                        <option>Weekly</option>
                        <option>Manual</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Timezone</label>
                      <select className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                        <option>UTC</option>
                        <option>America/New_York</option>
                        <option>America/Los_Angeles</option>
                        <option selected>Europe/London</option>
                        <option>Europe/Paris</option>
                        <option>Asia/Tokyo</option>
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-4">Connection Settings</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Connection Name</label>
                      <input
                        type="text"
                        defaultValue={connection.name}
                        className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                      />
                    </div>
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Destination Schema</label>
                      <input
                        type="text"
                        defaultValue={`atlas_${connection.connector_type}`}
                        className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-red-500/20">
                <CardContent className="p-4">
                  <h3 className="font-semibold text-red-600 mb-2">Danger Zone</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                    These actions are destructive and cannot be undone.
                  </p>
                  <div className="flex gap-3">
                    <Button variant="outline" className="text-red-600 border-red-600 hover:bg-red-50">
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Reset Connection
                    </Button>
                    <Button variant="outline" className="text-red-600 border-red-600 hover:bg-red-50">
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete Connection
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// NEW CONNECTION WIZARD
// ============================================================================

function NewConnectionWizard({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(1);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');
  const [selectedConnector, setSelectedConnector] = useState<Connector | null>(null);

  const filteredConnectors = useMemo(() => {
    return DEMO_CONNECTORS.filter((c) => {
      const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
                           c.description.toLowerCase().includes(search.toLowerCase());
      const matchesCategory = category === 'All' || c.category === category;
      return matchesSearch && matchesCategory;
    });
  }, [search, category]);

  const popularConnectors = DEMO_CONNECTORS.filter(c => c.popular).slice(0, 8);

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-start justify-center pt-8 pb-8 overflow-y-auto">
      <div className="bg-[hsl(var(--card))] rounded-lg w-full max-w-4xl border border-[hsl(var(--border))] shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">
              {step === 1 && 'Select a Data Source'}
              {step === 2 && `Configure ${selectedConnector?.name}`}
              {step === 3 && 'Select Streams'}
              {step === 4 && 'Review & Create'}
            </h2>
            <p className="text-sm text-[hsl(var(--muted-foreground))] mt-1">
              {step === 1 && 'Choose from 150+ pre-built connectors'}
              {step === 2 && 'Enter your credentials to connect'}
              {step === 3 && 'Choose which data to sync'}
              {step === 4 && 'Confirm your connection settings'}
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Progress */}
        <div className="px-4 py-3 bg-[hsl(var(--secondary)/0.3)] border-b border-[hsl(var(--border))]">
          <div className="flex items-center gap-2">
            {[1, 2, 3, 4].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  s < step ? 'bg-green-600 text-white' :
                  s === step ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]' :
                  'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]'
                }`}>
                  {s < step ? <Check className="w-4 h-4" /> : s}
                </div>
                {s < 4 && (
                  <div className={`w-16 h-0.5 mx-2 ${s < step ? 'bg-green-600' : 'bg-[hsl(var(--border))]'}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          {step === 1 && (
            <div className="space-y-6">
              {/* Search */}
              <div className="flex gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--muted-foreground))]" />
                  <input
                    type="text"
                    placeholder="Search connectors..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                  />
                </div>
              </div>

              {/* Categories */}
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategory(cat)}
                    className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                      category === cat
                        ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                        : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--border))]'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>

              {/* Popular (only show when not searching) */}
              {!search && category === 'All' && (
                <div>
                  <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">Popular Connectors</h3>
                  <div className="grid grid-cols-4 gap-3">
                    {popularConnectors.map((connector) => (
                      <button
                        key={connector.id}
                        onClick={() => { setSelectedConnector(connector); setStep(2); }}
                        className="p-3 rounded-lg border border-[hsl(var(--border))] hover:border-[hsl(var(--foreground)/0.3)] transition-colors text-left"
                      >
                        <div className="text-2xl mb-1">{connector.icon}</div>
                        <p className="font-medium text-sm text-[hsl(var(--foreground))]">{connector.name}</p>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* All Connectors */}
              <div>
                <h3 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">
                  {search || category !== 'All' ? 'Search Results' : 'All Connectors'} ({filteredConnectors.length})
                </h3>
                <div className="grid grid-cols-2 gap-3 max-h-[400px] overflow-y-auto">
                  {filteredConnectors.map((connector) => (
                    <ConnectorCard
                      key={connector.id}
                      connector={connector}
                      onSelect={() => { setSelectedConnector(connector); setStep(2); }}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {step === 2 && selectedConnector && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 p-4 rounded-lg bg-[hsl(var(--secondary))]">
                <div className="text-3xl">{selectedConnector.icon}</div>
                <div>
                  <h3 className="font-semibold text-[hsl(var(--foreground))]">{selectedConnector.name}</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">{selectedConnector.description}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-[hsl(var(--foreground))]">Connection Name</label>
                  <input
                    type="text"
                    placeholder={`My ${selectedConnector.name} Connection`}
                    className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                  />
                </div>

                {selectedConnector.auth_type === 'oauth' && (
                  <div className="p-4 rounded-lg border border-[hsl(var(--border))] bg-[hsl(var(--secondary)/0.3)]">
                    <p className="text-sm text-[hsl(var(--muted-foreground))] mb-3">
                      Click the button below to authenticate with {selectedConnector.name}
                    </p>
                    <Button>
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Connect with {selectedConnector.name}
                    </Button>
                  </div>
                )}

                {selectedConnector.auth_type === 'api_key' && (
                  <div>
                    <label className="text-sm font-medium text-[hsl(var(--foreground))]">API Key</label>
                    <input
                      type="password"
                      placeholder="Enter your API key"
                      className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                    />
                    <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
                      Find your API key in your {selectedConnector.name} account settings
                    </p>
                  </div>
                )}

                {selectedConnector.auth_type === 'basic' && (
                  <>
                    <div>
                      <label className="text-sm font-medium text-[hsl(var(--foreground))]">Host</label>
                      <input
                        type="text"
                        placeholder="your-database.example.com"
                        className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-[hsl(var(--foreground))]">Port</label>
                        <input
                          type="text"
                          placeholder="5432"
                          className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium text-[hsl(var(--foreground))]">Database</label>
                        <input
                          type="text"
                          placeholder="mydb"
                          className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-[hsl(var(--foreground))]">Username</label>
                        <input
                          type="text"
                          placeholder="username"
                          className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                        />
                      </div>
                      <div>
                        <label className="text-sm font-medium text-[hsl(var(--foreground))]">Password</label>
                        <input
                          type="password"
                          placeholder="••••••••"
                          className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
                        />
                      </div>
                    </div>
                  </>
                )}
              </div>

              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setStep(1)}>
                  Back
                </Button>
                <Button variant="outline">
                  Test Connection
                </Button>
                <Button onClick={() => setStep(3)}>
                  Continue
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-[hsl(var(--foreground))]">Select Streams to Sync</h3>
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">
                    Choose which tables/streams you want to sync
                  </p>
                </div>
                <Button variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh Schema
                </Button>
              </div>

              <Card>
                <CardContent className="p-0">
                  <div className="grid grid-cols-12 gap-3 items-center py-2 px-4 bg-[hsl(var(--secondary))] text-xs font-medium text-[hsl(var(--muted-foreground))] border-b border-[hsl(var(--border))]">
                    <div className="col-span-1">
                      <input type="checkbox" className="w-4 h-4" />
                    </div>
                    <div className="col-span-3">Stream</div>
                    <div className="col-span-3">Sync Mode</div>
                    <div className="col-span-3">Destination Mode</div>
                    <div className="col-span-2 text-right">Estimated Rows</div>
                  </div>
                  {/* Sample streams */}
                  {['users', 'orders', 'products', 'customers', 'transactions', 'events'].map((stream, idx) => (
                    <div key={stream} className="grid grid-cols-12 gap-3 items-center py-3 px-4 border-b border-[hsl(var(--border))] last:border-0 hover:bg-[hsl(var(--secondary)/0.3)]">
                      <div className="col-span-1">
                        <input type="checkbox" defaultChecked={idx < 4} className="w-4 h-4" />
                      </div>
                      <div className="col-span-3">
                        <p className="font-medium text-sm text-[hsl(var(--foreground))]">{stream}</p>
                      </div>
                      <div className="col-span-3">
                        <select className="w-full px-2 py-1 text-xs border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                          <option>Incremental</option>
                          <option>Full Refresh</option>
                          <option>CDC</option>
                        </select>
                      </div>
                      <div className="col-span-3">
                        <select className="w-full px-2 py-1 text-xs border border-[hsl(var(--border))] rounded bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                          <option>Append + Dedup</option>
                          <option>Append</option>
                          <option>Overwrite</option>
                        </select>
                      </div>
                      <div className="col-span-2 text-right text-sm text-[hsl(var(--muted-foreground))]">
                        {formatNumber(Math.floor(Math.random() * 500000) + 1000)}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Back
                </Button>
                <Button onClick={() => setStep(4)}>
                  Continue
                  <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </div>
          )}

          {step === 4 && selectedConnector && (
            <div className="space-y-6">
              <Card>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-4">Connection Summary</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-lg bg-[hsl(var(--secondary))]">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Source</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-xl">{selectedConnector.icon}</span>
                        <span className="font-medium text-[hsl(var(--foreground))]">{selectedConnector.name}</span>
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-[hsl(var(--secondary))]">
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Destination</p>
                      <div className="flex items-center gap-2 mt-1">
                        <Database className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />
                        <span className="font-medium text-[hsl(var(--foreground))]">Atlas Data Warehouse</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 grid grid-cols-3 gap-4">
                    <div className="text-center p-3 rounded-lg bg-[hsl(var(--secondary))]">
                      <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">4</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Streams Selected</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-[hsl(var(--secondary))]">
                      <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">~500K</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Estimated Rows</p>
                    </div>
                    <div className="text-center p-3 rounded-lg bg-[hsl(var(--secondary))]">
                      <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">1h</p>
                      <p className="text-xs text-[hsl(var(--muted-foreground))]">Sync Frequency</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-[hsl(var(--foreground))] mb-4">Sync Schedule</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Frequency</label>
                      <select className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                        <option>Every 15 minutes</option>
                        <option>Every 30 minutes</option>
                        <option selected>Every hour</option>
                        <option>Every 2 hours</option>
                        <option>Every 6 hours</option>
                        <option>Daily</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-sm text-[hsl(var(--muted-foreground))]">Start Sync</label>
                      <select className="w-full mt-1 px-3 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
                        <option selected>Immediately after creation</option>
                        <option>Wait for manual trigger</option>
                        <option>Schedule for later</option>
                      </select>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-3 pt-4">
                <Button variant="outline" onClick={() => setStep(3)}>
                  Back
                </Button>
                <Button onClick={() => { toast.success('Connection created successfully!'); onClose(); }}>
                  <Check className="w-4 h-4 mr-2" />
                  Create Connection
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function Connections() {
  const [showNewConnection, setShowNewConnection] = useState(false);
  const [selectedConnection, setSelectedConnection] = useState<Connection | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredConnections = useMemo(() => {
    return DEMO_CONNECTIONS.filter((conn) => {
      const matchesStatus = statusFilter === 'all' || conn.status === statusFilter;
      const matchesSearch = conn.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           conn.connector_type.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesStatus && matchesSearch;
    });
  }, [statusFilter, searchQuery]);

  const handleSync = (_connId: string) => {
    toast.success(`Sync started for connection`);
  };

  const handlePause = (_connId: string) => {
    toast.success(`Connection paused`);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Connections</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage your data integrations and sync pipelines
          </p>
        </div>
        <Button onClick={() => setShowNewConnection(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Connection
        </Button>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-4 gap-4">
        <MetricCard
          title="Total Records Synced"
          value={DEMO_METRICS.total_records}
          subtitle="All time"
          icon={<Database className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />}
          trend={{ value: 12, positive: true }}
        />
        <MetricCard
          title="Active Connections"
          value={`${DEMO_METRICS.active_connections}/${DEMO_METRICS.total_connections}`}
          subtitle={`${DEMO_METRICS.failed_syncs_24h} failed in 24h`}
          icon={<Zap className="w-5 h-5 text-green-600" />}
        />
        <MetricCard
          title="Records Today"
          value={DEMO_METRICS.records_today}
          subtitle={`${DEMO_METRICS.api_calls_today.toLocaleString()} API calls`}
          icon={<TrendingUp className="w-5 h-5 text-blue-600" />}
          trend={{ value: 8, positive: true }}
        />
        <MetricCard
          title="Sync Time Today"
          value={`${DEMO_METRICS.sync_time_today_minutes}m`}
          subtitle={`${DEMO_METRICS.records_this_month.toLocaleString()} this month`}
          icon={<Clock className="w-5 h-5 text-[hsl(var(--muted-foreground))]" />}
        />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[hsl(var(--muted-foreground))]" />
          <input
            type="text"
            placeholder="Search connections..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--background))] text-[hsl(var(--foreground))]"
          />
        </div>
        <div className="flex gap-2">
          {['all', 'active', 'syncing', 'paused', 'error'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-sm rounded-lg transition-colors capitalize ${
                statusFilter === status
                  ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                  : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--border))]'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Connections Grid */}
      {filteredConnections.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredConnections.map((connection) => (
            <ConnectionCard
              key={connection.id}
              connection={connection}
              onClick={() => setSelectedConnection(connection)}
              onSync={() => handleSync(connection.id)}
              onPause={() => handlePause(connection.id)}
            />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <Database className="w-12 h-12 mx-auto text-[hsl(var(--muted-foreground))] mb-4" />
            <h3 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-2">No connections found</h3>
            <p className="text-[hsl(var(--muted-foreground))] mb-4">
              {searchQuery || statusFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first connection to start syncing data'}
            </p>
            <Button onClick={() => setShowNewConnection(true)}>
              <Plus className="w-4 h-4 mr-2" />
              New Connection
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Modals */}
      {showNewConnection && (
        <NewConnectionWizard onClose={() => setShowNewConnection(false)} />
      )}

      {selectedConnection && (
        <ConnectionDetailModal
          connection={selectedConnection}
          onClose={() => setSelectedConnection(null)}
        />
      )}
    </div>
  );
}
