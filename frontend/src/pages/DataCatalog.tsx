import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search,
  Database,
  Tag,
  TrendingUp,
  Calendar,
  FileText,
  Download,
  X,
  Package,
  Upload,
  Filter,
} from 'lucide-react';
import { searchDatasets, getDatasetQualityHistory } from '@/api/client';
import type { Dataset, QualityHistory } from '@/types';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const AVAILABLE_TAGS = [
  'PII',
  'GDPR',
  'Finance',
  'Marketing',
  'Customer',
  'Sales',
  'Product',
  'Analytics',
];

const SOURCE_TYPES = [
  { value: 'all', label: 'All Sources', icon: Database },
  { value: 'csv', label: 'CSV Uploads', icon: Upload },
  { value: 'atlas', label: 'AtlasIntelligence Syncs', icon: Package },
];

export default function DataCatalog() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedSourceType, setSelectedSourceType] = useState<string>('all');
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets', searchQuery, selectedTags],
    queryFn: () => searchDatasets(searchQuery || undefined, selectedTags),
  });

  const { data: qualityHistory } = useQuery({
    queryKey: ['quality-history', selectedDataset?.id],
    queryFn: () => getDatasetQualityHistory(selectedDataset!.id),
    enabled: !!selectedDataset,
  });

  const toggleTag = (tag: string) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const getLayerBadge = (layer: string) => {
    const styles = {
      explore: 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))]',
      chart: 'bg-green-500/10 text-green-600',
      navigate: 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]',
    };
    return styles[layer as keyof typeof styles] || 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]';
  };

  const getSourceTypeBadge = (sourceType: string) => {
    if (sourceType === 'atlas' || sourceType?.includes('atlas')) {
      return { label: 'AtlasIntelligence', color: 'bg-blue-500/10 text-blue-600', icon: Package };
    }
    return { label: 'CSV', color: 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))]', icon: Upload };
  };

  // Filter datasets by source type
  const filteredDatasets = datasets?.filter((dataset: Dataset) => {
    if (selectedSourceType === 'all') return true;
    const datasetSource = dataset.name?.toLowerCase().includes('atlas') ||
                         dataset.description?.toLowerCase().includes('atlas') ? 'atlas' : 'csv';
    return datasetSource === selectedSourceType;
  });

  const downloadSchema = (dataset: Dataset) => {
    const dataStr = JSON.stringify(dataset.schema, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${dataset.name}_schema.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Data Catalog</h1>
        <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
          Browse and search all datasets in the Atlas pipeline
        </p>
      </div>

      {/* Search Bar */}
      <Card>
        <CardContent className="p-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-[hsl(var(--muted-foreground))]" />
            <input
              type="search"
              data-testid="search-input"
              placeholder="Search datasets by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            />
          </div>

          {/* Source Type Filter */}
          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <Filter className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <span className="text-sm font-medium text-[hsl(var(--foreground))]">Source type:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {SOURCE_TYPES.map((sourceType) => {
                const Icon = sourceType.icon;
                return (
                  <button
                    key={sourceType.value}
                    onClick={() => setSelectedSourceType(sourceType.value)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors flex items-center gap-1.5 ${
                      selectedSourceType === sourceType.value
                        ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                        : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.8)]'
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {sourceType.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Tag Filters */}
          <div className="mt-4">
            <div className="flex items-center gap-2 mb-2">
              <Tag className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <span className="text-sm font-medium text-[hsl(var(--foreground))]">Filter by tags:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_TAGS.map((tag) => (
                <button
                  key={tag}
                  onClick={() => toggleTag(tag)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    selectedTags.includes(tag)
                      ? 'bg-[hsl(var(--foreground))] text-[hsl(var(--background))]'
                      : 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--secondary)/0.8)]'
                  }`}
                >
                  {tag}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Dataset Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-6 bg-[hsl(var(--secondary))] rounded w-3/4 mb-4 animate-pulse" />
                <div className="h-4 bg-[hsl(var(--secondary))] rounded w-full mb-2 animate-pulse" />
                <div className="h-4 bg-[hsl(var(--secondary))] rounded w-5/6 animate-pulse" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredDatasets && filteredDatasets.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredDatasets.map((dataset: Dataset) => {
            const sourceType = dataset.name?.toLowerCase().includes('atlas') ||
                              dataset.description?.toLowerCase().includes('atlas') ? 'atlas' : 'csv';
            const sourceBadge = getSourceTypeBadge(sourceType);
            const SourceIcon = sourceBadge.icon;

            return (
              <Card
                key={dataset.id}
                className="cursor-pointer hover:border-[hsl(var(--foreground)/0.2)] transition-colors"
                onClick={() => setSelectedDataset(dataset)}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Database className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                      <h3 className="font-semibold text-[hsl(var(--foreground))]">{dataset.name}</h3>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getLayerBadge(dataset.layer)}`}>
                      {dataset.layer}
                    </span>
                  </div>

                  {/* Source Type Badge */}
                  <div className="mb-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded ${sourceBadge.color}`}>
                      <SourceIcon className="h-3 w-3" />
                      {sourceBadge.label}
                    </span>
                  </div>

                {dataset.description && (
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4 line-clamp-2">
                    {dataset.description}
                  </p>
                )}

                <div className="space-y-2 text-sm">
                  {dataset.row_count_estimate !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-[hsl(var(--muted-foreground))]">Rows:</span>
                      <span className="font-medium text-[hsl(var(--foreground))]">
                        {dataset.row_count_estimate.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {dataset.quality_score !== undefined && (
                    <div className="flex items-center justify-between">
                      <span className="text-[hsl(var(--muted-foreground))]">Quality:</span>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="h-4 w-4 text-green-600" />
                        <span className="font-medium text-[hsl(var(--foreground))]">
                          {Math.round(dataset.quality_score * 100)}%
                        </span>
                      </div>
                    </div>
                  )}
                  <div className="flex items-center justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">Updated:</span>
                    <span className="font-medium text-[hsl(var(--foreground))]">
                      {new Date(dataset.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                {dataset.tags.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-1">
                    {dataset.tags.map((tag) => (
                      <span
                        key={tag}
                        className="px-2 py-1 text-xs bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <Database className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
            <h3 className="mt-2 text-sm font-medium text-[hsl(var(--foreground))]">No datasets found</h3>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              Try adjusting your search or filter criteria
            </p>
          </CardContent>
        </Card>
      )}

      {/* Dataset Details Modal */}
      {selectedDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-[hsl(var(--card))] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-[hsl(var(--border))]">
            {/* Modal Header */}
            <div className="sticky top-0 bg-[hsl(var(--card))] border-b border-[hsl(var(--border))] px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">{selectedDataset.name}</h2>
                <span className={`inline-block mt-2 px-3 py-1 text-sm font-medium rounded ${getLayerBadge(selectedDataset.layer)}`}>
                  {selectedDataset.layer} layer
                </span>
              </div>
              <button
                onClick={() => setSelectedDataset(null)}
                className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Description */}
              {selectedDataset.description && (
                <div>
                  <h3 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-2">Description</h3>
                  <p className="text-[hsl(var(--muted-foreground))]">{selectedDataset.description}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[hsl(var(--secondary))] p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">Total Rows</span>
                  </div>
                  <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                    {selectedDataset.row_count_estimate?.toLocaleString() || 'N/A'}
                  </p>
                </div>
                <div className="bg-[hsl(var(--secondary))] p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">Quality Score</span>
                  </div>
                  <p className="text-2xl font-semibold text-[hsl(var(--foreground))]">
                    {selectedDataset.quality_score !== undefined
                      ? `${Math.round(selectedDataset.quality_score * 100)}%`
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Schema Table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Schema</h3>
                  <Button
                    onClick={() => downloadSchema(selectedDataset)}
                    size="sm"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download JSON
                  </Button>
                </div>
                <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-[hsl(var(--border))] bg-[hsl(var(--secondary))]">
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Column
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Nullable
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[hsl(var(--border))]">
                      {selectedDataset.schema.map((col, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-sm font-medium text-[hsl(var(--foreground))]">
                            {col.column_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-[hsl(var(--muted-foreground))]">{col.data_type}</td>
                          <td className="px-4 py-3 text-sm">
                            {col.nullable ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-[hsl(var(--muted-foreground))]">
                            {col.description || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Quality History Chart */}
              {qualityHistory && qualityHistory.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-3">
                    Quality History
                  </h3>
                  <div className="bg-[hsl(var(--secondary))] p-4 rounded-lg">
                    <div className="space-y-2">
                      {qualityHistory.slice(0, 5).map((history: QualityHistory, idx: number) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
                            <span className="text-sm text-[hsl(var(--muted-foreground))]">
                              {new Date(history.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-[hsl(var(--muted-foreground))]">
                              Overall: <strong className="text-[hsl(var(--foreground))]">{Math.round(history.overall_score * 100)}%</strong>
                            </span>
                            <span className="text-[hsl(var(--muted-foreground))]">
                              Complete: <strong className="text-[hsl(var(--foreground))]">{Math.round(history.completeness * 100)}%</strong>
                            </span>
                            <span className="text-[hsl(var(--muted-foreground))]">
                              Valid: <strong className="text-[hsl(var(--foreground))]">{Math.round(history.validity * 100)}%</strong>
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
