import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Box,
  Upload,
  Download,
  TrendingUp,
  X,
  Calendar,
} from 'lucide-react';
import {
  getFeatureGroups,
  registerFeatureGroup,
  getFeatureVersions,
  exportFeatures,
} from '@/api/client';
import type { FeatureGroup, FeatureVersion } from '@/types';
import { toast } from 'react-hot-toast';

export default function FeatureStore() {
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [selectedGroup, setSelectedGroup] = useState<FeatureGroup | null>(null);
  const [showVersions, setShowVersions] = useState(false);

  const queryClient = useQueryClient();

  const { data: featureGroups, isLoading } = useQuery({
    queryKey: ['feature-groups'],
    queryFn: getFeatureGroups,
  });

  const { data: versions } = useQuery({
    queryKey: ['feature-versions', selectedGroup?.name],
    queryFn: () => getFeatureVersions(selectedGroup!.name),
    enabled: !!selectedGroup && showVersions,
  });

  const registerMutation = useMutation({
    mutationFn: registerFeatureGroup,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature-groups'] });
      setShowRegisterModal(false);
      toast.success('Feature group registered successfully');
    },
    onError: () => {
      toast.error('Failed to register feature group');
    },
  });

  const exportMutation = useMutation({
    mutationFn: ({ name, format, version }: { name: string; format: string; version?: string }) =>
      exportFeatures(name, format, version),
    onSuccess: () => {
      toast.success('Features exported successfully');
      setShowExportModal(false);
    },
    onError: () => {
      toast.error('Failed to export features');
    },
  });

  const handleRegister = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    registerMutation.mutate(formData);
  };

  const handleExport = (format: string, version?: string) => {
    if (selectedGroup) {
      exportMutation.mutate({ name: selectedGroup.name, format, version });
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Feature Store</h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage ML features with versioning and export capabilities
          </p>
        </div>
        <button
          onClick={() => setShowRegisterModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
        >
          <Upload className="h-5 w-5" />
          Register Feature Group
        </button>
      </div>

      {/* Feature Groups Grid */}
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
      ) : featureGroups && featureGroups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureGroups.map((group: FeatureGroup) => (
            <div
              key={group.id}
              className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-all"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Box className="h-5 w-5 text-primary-600" />
                  <h3 className="font-semibold text-gray-900">{group.name}</h3>
                </div>
                <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                  v{group.version}
                </span>
              </div>

              {group.description && (
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">{group.description}</p>
              )}

              <div className="space-y-2 text-sm mb-4">
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Features:</span>
                  <span className="font-medium text-gray-900">{group.feature_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Created:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(group.created_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-gray-500">Updated:</span>
                  <span className="font-medium text-gray-900">
                    {new Date(group.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setSelectedGroup(group);
                    setShowVersions(true);
                  }}
                  className="flex-1 px-3 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200 transition-colors"
                >
                  View Details
                </button>
                <button
                  onClick={() => {
                    setSelectedGroup(group);
                    setShowExportModal(true);
                  }}
                  className="flex-1 px-3 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors flex items-center justify-center gap-1"
                >
                  <Download className="h-4 w-4" />
                  Export
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <Box className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No feature groups</h3>
          <p className="mt-1 text-sm text-gray-500">
            Get started by registering your first feature group
          </p>
          <button
            onClick={() => setShowRegisterModal(true)}
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <Upload className="h-4 w-4" />
            Register Feature Group
          </button>
        </div>
      )}

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-bold text-gray-900">Register Feature Group</h2>
            </div>
            <form onSubmit={handleRegister} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Feature Group Name
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="customer_features"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="Customer demographic and behavioral features"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Upload CSV
                </label>
                <input
                  type="file"
                  name="file"
                  accept=".csv"
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={registerMutation.isPending}
                  className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  {registerMutation.isPending ? 'Registering...' : 'Register'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Export Features</h2>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-4">
                  Export <strong>{selectedGroup.name}</strong> in your preferred format
                </p>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => handleExport('parquet', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all disabled:opacity-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Parquet</span>
                    <span className="text-sm text-blue-100">Optimized for ML</span>
                  </div>
                </button>
                <button
                  onClick={() => handleExport('csv', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-gradient-to-r from-green-600 to-green-700 text-white rounded-lg hover:from-green-700 hover:to-green-800 transition-all disabled:opacity-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">CSV</span>
                    <span className="text-sm text-green-100">Universal format</span>
                  </div>
                </button>
                <button
                  onClick={() => handleExport('json', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-lg hover:from-purple-700 hover:to-purple-800 transition-all disabled:opacity-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">JSON</span>
                    <span className="text-sm text-purple-100">API integration</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feature Details Modal */}
      {showVersions && selectedGroup && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">{selectedGroup.name}</h2>
              <button
                onClick={() => {
                  setShowVersions(false);
                  setSelectedGroup(null);
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Version History */}
              {versions && versions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Version History</h3>
                  <div className="space-y-2">
                    {versions.map((version: FeatureVersion, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Calendar className="h-5 w-5 text-gray-400" />
                          <div>
                            <div className="font-medium text-gray-900">v{version.version}</div>
                            <div className="text-sm text-gray-500">
                              {new Date(version.created_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div>
                            <span className="text-gray-500">Features: </span>
                            <span className="font-medium text-gray-900">
                              {version.feature_count}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-500">Rows: </span>
                            <span className="font-medium text-gray-900">
                              {version.row_count.toLocaleString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Features Table */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Features</h3>
                <div className="border border-gray-200 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Null %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Unique %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                          Importance
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedGroup.features.map((feature, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {feature.name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-600">
                            {feature.data_type}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-orange-500 h-2 rounded-full"
                                  style={{ width: `${feature.null_percentage}%` }}
                                />
                              </div>
                              <span className="text-gray-600">
                                {feature.null_percentage.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-gray-200 rounded-full h-2">
                                <div
                                  className="bg-blue-500 h-2 rounded-full"
                                  style={{ width: `${feature.unique_percentage}%` }}
                                />
                              </div>
                              <span className="text-gray-600">
                                {feature.unique_percentage.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {feature.importance !== undefined ? (
                              <div className="flex items-center gap-2">
                                <TrendingUp className="h-4 w-4 text-green-600" />
                                <span className="font-medium text-gray-900">
                                  {(feature.importance * 100).toFixed(1)}%
                                </span>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
