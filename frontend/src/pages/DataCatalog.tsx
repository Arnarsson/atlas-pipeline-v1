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
} from 'lucide-react';
import { searchDatasets, getDatasetQualityHistory } from '@/api/client';
import type { Dataset, QualityHistory } from '@/types';

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

export default function DataCatalog() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);

  const { data: datasets, isLoading } = useQuery({
    queryKey: ['datasets', searchQuery, selectedTags],
    queryFn: () => searchDatasets(searchQuery || undefined, selectedTags),
  });

  // Uncomment when backend supports detailed dataset info
  // const { data: datasetDetails } = useQuery({
  //   queryKey: ['dataset-details', selectedDataset?.id],
  //   queryFn: () => getDatasetDetails(selectedDataset!.id),
  //   enabled: !!selectedDataset,
  // });

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

  const getLayerColor = (layer: string) => {
    switch (layer) {
      case 'explore':
        return 'bg-blue-100 text-blue-800';
      case 'chart':
        return 'bg-green-100 text-green-800';
      case 'navigate':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

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
        <h1 className="text-3xl font-bold text-gray-900">Data Catalog</h1>
        <p className="mt-2 text-sm text-gray-600">
          Browse and search all datasets in the Atlas pipeline
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="search"
            data-testid="search-input"
            placeholder="Search datasets by name or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
        </div>

        {/* Tag Filters */}
        <div className="mt-4">
          <div className="flex items-center gap-2 mb-2">
            <Tag className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Filter by tags:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {AVAILABLE_TAGS.map((tag) => (
              <button
                key={tag}
                onClick={() => toggleTag(tag)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  selectedTags.includes(tag)
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Dataset Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-3/4 mb-4" />
              <div className="h-4 bg-gray-200 rounded w-full mb-2" />
              <div className="h-4 bg-gray-200 rounded w-5/6" />
            </div>
          ))}
        </div>
      ) : datasets && datasets.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {datasets.map((dataset: Dataset) => (
            <div
              key={dataset.id}
              onClick={() => setSelectedDataset(dataset)}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-all cursor-pointer hover:-translate-y-1"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Database className="h-5 w-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900">{dataset.name}</h3>
                </div>
                <span
                  className={`px-2 py-1 text-xs font-medium rounded ${getLayerColor(
                    dataset.layer
                  )}`}
                >
                  {dataset.layer}
                </span>
              </div>

              {dataset.description && (
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">
                  {dataset.description}
                </p>
              )}

              <div className="space-y-2 text-sm">
                {dataset.row_count_estimate !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Rows:</span>
                    <span className="font-medium text-gray-900">
                      {dataset.row_count_estimate.toLocaleString()}
                    </span>
                  </div>
                )}
                {dataset.quality_score !== undefined && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-500">Quality:</span>
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                      <span className="font-medium text-gray-900">
                        {Math.round(dataset.quality_score * 100)}%
                      </span>
                    </div>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Updated:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(dataset.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              {dataset.tags.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1">
                  {dataset.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Database className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No datasets found</h3>
          <p className="mt-1 text-sm text-gray-500">
            Try adjusting your search or filter criteria
          </p>
        </div>
      )}

      {/* Dataset Details Modal */}
      {selectedDataset && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">{selectedDataset.name}</h2>
                <span
                  className={`inline-block mt-2 px-3 py-1 text-sm font-medium rounded ${getLayerColor(
                    selectedDataset.layer
                  )}`}
                >
                  {selectedDataset.layer} layer
                </span>
              </div>
              <button
                onClick={() => setSelectedDataset(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 space-y-6">
              {/* Description */}
              {selectedDataset.description && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                  <p className="text-gray-600">{selectedDataset.description}</p>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-500">Total Rows</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">
                    {selectedDataset.row_count_estimate?.toLocaleString() || 'N/A'}
                  </p>
                </div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-gray-500" />
                    <span className="text-sm text-gray-500">Quality Score</span>
                  </div>
                  <p className="text-2xl font-bold text-gray-900">
                    {selectedDataset.quality_score !== undefined
                      ? `${Math.round(selectedDataset.quality_score * 100)}%`
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Schema Table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-gray-900">Schema</h3>
                  <button
                    onClick={() => downloadSchema(selectedDataset)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    <Download className="h-4 w-4" />
                    Download JSON
                  </button>
                </div>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Column
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Nullable
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Description
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedDataset.schema.map((col, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {col.column_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">{col.data_type}</td>
                          <td className="px-4 py-3 text-sm">
                            {col.nullable ? (
                              <span className="text-green-600">Yes</span>
                            ) : (
                              <span className="text-red-600">No</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
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
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">
                    Quality History
                  </h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="space-y-2">
                      {qualityHistory.slice(0, 5).map((history: QualityHistory, idx: number) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-gray-400" />
                            <span className="text-sm text-gray-600">
                              {new Date(history.timestamp).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex items-center gap-4 text-sm">
                            <span className="text-gray-600">
                              Overall: <strong>{Math.round(history.overall_score * 100)}%</strong>
                            </span>
                            <span className="text-gray-600">
                              Complete: <strong>{Math.round(history.completeness * 100)}%</strong>
                            </span>
                            <span className="text-gray-600">
                              Valid: <strong>{Math.round(history.validity * 100)}%</strong>
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
