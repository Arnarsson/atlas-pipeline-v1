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
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

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
          <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Feature Store</h1>
          <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
            Manage ML features with versioning and export capabilities
          </p>
        </div>
        <Button onClick={() => setShowRegisterModal(true)}>
          <Upload className="h-4 w-4 mr-2" />
          Register Feature Group
        </Button>
      </div>

      {/* Feature Groups Grid */}
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
      ) : featureGroups && featureGroups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureGroups.map((group: FeatureGroup) => (
            <Card key={group.id} className="hover:border-[hsl(var(--foreground)/0.2)] transition-colors">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Box className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                    <h3 className="font-semibold text-[hsl(var(--foreground))]">{group.name}</h3>
                  </div>
                  <span className="px-2 py-1 text-xs font-medium bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] rounded">
                    v{group.version}
                  </span>
                </div>

                {group.description && (
                  <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4 line-clamp-2">{group.description}</p>
                )}

                <div className="space-y-2 text-sm mb-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">Features:</span>
                    <span className="font-medium text-[hsl(var(--foreground))]">{group.feature_count}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">Created:</span>
                    <span className="font-medium text-[hsl(var(--foreground))]">
                      {new Date(group.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-[hsl(var(--muted-foreground))]">Updated:</span>
                    <span className="font-medium text-[hsl(var(--foreground))]">
                      {new Date(group.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      setSelectedGroup(group);
                      setShowVersions(true);
                    }}
                  >
                    View Details
                  </Button>
                  <Button
                    size="sm"
                    className="flex-1"
                    onClick={() => {
                      setSelectedGroup(group);
                      setShowExportModal(true);
                    }}
                  >
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <Box className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
            <h3 className="mt-2 text-sm font-medium text-[hsl(var(--foreground))]">No feature groups</h3>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              Get started by registering your first feature group
            </p>
            <Button onClick={() => setShowRegisterModal(true)} className="mt-4">
              <Upload className="h-4 w-4 mr-2" />
              Register Feature Group
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Register Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-[hsl(var(--card))] rounded-lg max-w-md w-full border border-[hsl(var(--border))]">
            <div className="px-6 py-4 border-b border-[hsl(var(--border))]">
              <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">Register Feature Group</h2>
            </div>
            <form onSubmit={handleRegister} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Feature Group Name
                </label>
                <input
                  type="text"
                  name="name"
                  required
                  className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                  placeholder="customer_features"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Description
                </label>
                <textarea
                  name="description"
                  rows={3}
                  className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                  placeholder="Customer demographic and behavioral features"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-1">
                  Upload CSV
                </label>
                <input
                  type="file"
                  name="file"
                  accept=".csv"
                  required
                  className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => setShowRegisterModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  disabled={registerMutation.isPending}
                >
                  {registerMutation.isPending ? 'Registering...' : 'Register'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Export Modal */}
      {showExportModal && selectedGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-[hsl(var(--card))] rounded-lg max-w-md w-full border border-[hsl(var(--border))]">
            <div className="px-6 py-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
              <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">Export Features</h2>
              <button
                onClick={() => setShowExportModal(false)}
                className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-[hsl(var(--muted-foreground))] mb-4">
                  Export <strong className="text-[hsl(var(--foreground))]">{selectedGroup.name}</strong> in your preferred format
                </p>
              </div>
              <div className="space-y-2">
                <button
                  onClick={() => handleExport('parquet', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] rounded-lg hover:bg-[hsl(var(--secondary)/0.8)] transition-all disabled:opacity-50 border border-[hsl(var(--border))]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">Parquet</span>
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">Optimized for ML</span>
                  </div>
                </button>
                <button
                  onClick={() => handleExport('csv', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] rounded-lg hover:bg-[hsl(var(--secondary)/0.8)] transition-all disabled:opacity-50 border border-[hsl(var(--border))]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">CSV</span>
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">Universal format</span>
                  </div>
                </button>
                <button
                  onClick={() => handleExport('json', selectedGroup.version)}
                  disabled={exportMutation.isPending}
                  className="w-full px-4 py-3 bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] rounded-lg hover:bg-[hsl(var(--secondary)/0.8)] transition-all disabled:opacity-50 border border-[hsl(var(--border))]"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">JSON</span>
                    <span className="text-sm text-[hsl(var(--muted-foreground))]">API integration</span>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feature Details Modal */}
      {showVersions && selectedGroup && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
          <div className="bg-[hsl(var(--card))] rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto border border-[hsl(var(--border))]">
            <div className="sticky top-0 bg-[hsl(var(--card))] border-b border-[hsl(var(--border))] px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-[hsl(var(--foreground))]">{selectedGroup.name}</h2>
              <button
                onClick={() => {
                  setShowVersions(false);
                  setSelectedGroup(null);
                }}
                className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
              >
                <X className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {/* Version History */}
              {versions && versions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-3">Version History</h3>
                  <div className="space-y-2">
                    {versions.map((version: FeatureVersion, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-4 bg-[hsl(var(--secondary))] rounded-lg"
                      >
                        <div className="flex items-center gap-3">
                          <Calendar className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                          <div>
                            <div className="font-medium text-[hsl(var(--foreground))]">v{version.version}</div>
                            <div className="text-sm text-[hsl(var(--muted-foreground))]">
                              {new Date(version.created_at).toLocaleString()}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-6 text-sm">
                          <div>
                            <span className="text-[hsl(var(--muted-foreground))]">Features: </span>
                            <span className="font-medium text-[hsl(var(--foreground))]">
                              {version.feature_count}
                            </span>
                          </div>
                          <div>
                            <span className="text-[hsl(var(--muted-foreground))]">Rows: </span>
                            <span className="font-medium text-[hsl(var(--foreground))]">
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
                <h3 className="text-lg font-semibold text-[hsl(var(--foreground))] mb-3">Features</h3>
                <div className="border border-[hsl(var(--border))] rounded-lg overflow-hidden">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-[hsl(var(--border))] bg-[hsl(var(--secondary))]">
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Null %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Unique %
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase">
                          Importance
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[hsl(var(--border))]">
                      {selectedGroup.features.map((feature, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-sm font-medium text-[hsl(var(--foreground))]">
                            {feature.name}
                          </td>
                          <td className="px-4 py-3 text-sm text-[hsl(var(--muted-foreground))]">
                            {feature.data_type}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-[hsl(var(--secondary))] rounded-full h-2">
                                <div
                                  className="bg-[hsl(var(--foreground)/0.5)] h-2 rounded-full"
                                  style={{ width: `${feature.null_percentage}%` }}
                                />
                              </div>
                              <span className="text-[hsl(var(--muted-foreground))]">
                                {feature.null_percentage.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <div className="flex items-center gap-2">
                              <div className="w-16 bg-[hsl(var(--secondary))] rounded-full h-2">
                                <div
                                  className="bg-[hsl(var(--foreground)/0.5)] h-2 rounded-full"
                                  style={{ width: `${feature.unique_percentage}%` }}
                                />
                              </div>
                              <span className="text-[hsl(var(--muted-foreground))]">
                                {feature.unique_percentage.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {feature.importance !== undefined ? (
                              <div className="flex items-center gap-2">
                                <TrendingUp className="h-4 w-4 text-green-600" />
                                <span className="font-medium text-[hsl(var(--foreground))]">
                                  {(feature.importance * 100).toFixed(1)}%
                                </span>
                              </div>
                            ) : (
                              <span className="text-[hsl(var(--muted-foreground))]">-</span>
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
