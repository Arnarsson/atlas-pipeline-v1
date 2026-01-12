import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  GitBranch,
  Database,
  ArrowRight,
  ChevronRight,
  ChevronDown,
  Layers,
} from 'lucide-react';
import { getDatasetLineage, searchDatasets } from '@/api/client';
import type { LineageGraph, Dataset } from '@/types';
import { Card, CardContent } from '@/components/ui/card';

export default function Lineage() {
  const [selectedDataset, setSelectedDataset] = useState('');
  const [depth, setDepth] = useState(3);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());

  const { data: datasets } = useQuery({
    queryKey: ['datasets-list'],
    queryFn: () => searchDatasets(),
  });

  const { data: lineage, isLoading } = useQuery({
    queryKey: ['lineage', selectedDataset, depth],
    queryFn: () => getDatasetLineage(selectedDataset, depth),
    enabled: !!selectedDataset,
  });

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedNodes(newExpanded);
  };

  const getLayerStyle = (layer?: string) => {
    switch (layer) {
      case 'explore':
        return 'bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] border-[hsl(var(--border))]';
      case 'chart':
        return 'bg-green-500/10 text-green-700 border-green-500/30';
      case 'navigate':
        return 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] border-[hsl(var(--border))]';
      default:
        return 'bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] border-[hsl(var(--border))]';
    }
  };

  const buildTreeStructure = (graph: LineageGraph) => {
    if (!graph || !graph.nodes || !graph.edges) return null;

    // Find root nodes (nodes with no incoming edges)
    const incomingEdges = new Set(graph.edges.map((e) => e.target));
    const rootNodes = graph.nodes.filter((n) => !incomingEdges.has(n.id));

    const renderNode = (node: any, level: number = 0) => {
      const outgoingEdges = graph.edges.filter((e) => e.source === node.id);
      const hasChildren = outgoingEdges.length > 0;
      const isExpanded = expandedNodes.has(node.id);

      return (
        <div key={node.id} className="relative">
          <div
            className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all hover:shadow-sm ${getLayerStyle(
              node.layer
            )} ${level > 0 ? 'ml-8' : ''}`}
            style={{ marginLeft: level > 0 ? `${level * 2}rem` : 0 }}
          >
            {hasChildren && (
              <button
                onClick={() => toggleNode(node.id)}
                className="flex-shrink-0 text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
              >
                {isExpanded ? (
                  <ChevronDown className="h-5 w-5" />
                ) : (
                  <ChevronRight className="h-5 w-5" />
                )}
              </button>
            )}
            {!hasChildren && <div className="w-5" />}

            <Database className="h-5 w-5" />
            <div className="flex-1">
              <div className="font-medium">{node.name}</div>
              <div className="text-xs opacity-75">{node.type}</div>
            </div>
            {node.layer && (
              <span className="px-2 py-1 text-xs font-medium rounded bg-[hsl(var(--background))] border border-[hsl(var(--border))]">
                {node.layer}
              </span>
            )}
          </div>

          {hasChildren && isExpanded && (
            <div className="mt-2 space-y-2 relative">
              {/* Connecting line */}
              <div
                className="absolute left-4 top-0 bottom-0 w-px bg-[hsl(var(--border))]"
                style={{ left: `${level * 2 + 1}rem` }}
              />

              {outgoingEdges.map((edge) => {
                const targetNode = graph.nodes.find((n) => n.id === edge.target);
                if (!targetNode) return null;

                return (
                  <div key={edge.target} className="relative">
                    <div
                      className="absolute top-1/2 bg-[hsl(var(--border))]"
                      style={{
                        left: `${level * 2 + 1}rem`,
                        width: '1rem',
                        height: '1px',
                      }}
                    />
                    <div
                      className="text-xs text-[hsl(var(--muted-foreground))] italic px-3 py-1"
                      style={{ marginLeft: `${(level + 1) * 2}rem` }}
                    >
                      {edge.operation}
                    </div>
                    {renderNode(targetNode, level + 1)}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      );
    };

    return (
      <div className="space-y-4">
        {rootNodes.map((node) => renderNode(node))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[hsl(var(--foreground))]">Data Lineage</h1>
        <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
          Track data transformations across pipeline layers
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Select Dataset
              </label>
              <select
                value={selectedDataset}
                onChange={(e) => setSelectedDataset(e.target.value)}
                className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
              >
                <option value="">Choose a dataset...</option>
                {datasets &&
                  datasets.map((dataset: Dataset) => (
                    <option key={dataset.id} value={dataset.name}>
                      {dataset.name} ({dataset.layer})
                    </option>
                  ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-[hsl(var(--foreground))] mb-2">
                Lineage Depth
              </label>
              <select
                value={depth}
                onChange={(e) => setDepth(Number(e.target.value))}
                className="w-full px-3 py-2 border border-[hsl(var(--input))] rounded-md bg-[hsl(var(--background))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
              >
                <option value={1}>1 level</option>
                <option value={2}>2 levels</option>
                <option value={3}>3 levels</option>
                <option value={5}>5 levels (full)</option>
              </select>
            </div>
          </div>

          {/* Legend */}
          <div className="mt-4 pt-4 border-t border-[hsl(var(--border))]">
            <div className="flex items-center gap-2 mb-2">
              <Layers className="h-4 w-4 text-[hsl(var(--muted-foreground))]" />
              <span className="text-sm font-medium text-[hsl(var(--foreground))]">Pipeline Layers:</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="flex items-center gap-2 px-3 py-1 rounded border bg-[hsl(var(--secondary))] text-[hsl(var(--foreground))] border-[hsl(var(--border))]">
                <div className="w-2 h-2 bg-[hsl(var(--foreground)/0.5)] rounded-full" />
                <span className="text-sm font-medium">Explore (Raw)</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded border bg-green-500/10 text-green-700 border-green-500/30">
                <div className="w-2 h-2 bg-green-600 rounded-full" />
                <span className="text-sm font-medium">Chart (Validated)</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded border bg-[hsl(var(--secondary))] text-[hsl(var(--muted-foreground))] border-[hsl(var(--border))]">
                <div className="w-2 h-2 bg-[hsl(var(--muted-foreground)/0.5)] rounded-full" />
                <span className="text-sm font-medium">Navigate (Business)</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lineage Visualization */}
      {!selectedDataset ? (
        <Card>
          <CardContent className="p-12 text-center">
            <GitBranch className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
            <h3 className="mt-2 text-sm font-medium text-[hsl(var(--foreground))]">No dataset selected</h3>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              Select a dataset above to view its lineage graph
            </p>
          </CardContent>
        </Card>
      ) : isLoading ? (
        <Card>
          <CardContent className="p-12 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-2 border-[hsl(var(--foreground))] border-t-transparent mx-auto" />
            <p className="mt-4 text-sm text-[hsl(var(--muted-foreground))]">Loading lineage...</p>
          </CardContent>
        </Card>
      ) : lineage && lineage.nodes && lineage.nodes.length > 0 ? (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-[hsl(var(--foreground))]">Lineage Graph</h2>
              <div className="flex items-center gap-2 text-sm text-[hsl(var(--muted-foreground))]">
                <Database className="h-4 w-4" />
                <span>{lineage.nodes.length} datasets</span>
                <ArrowRight className="h-4 w-4 ml-2" />
                <span>{lineage.edges.length} transformations</span>
              </div>
            </div>

            {/* Tree Structure */}
            {buildTreeStructure(lineage)}
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-12 text-center">
            <GitBranch className="mx-auto h-12 w-12 text-[hsl(var(--muted-foreground))]" />
            <h3 className="mt-2 text-sm font-medium text-[hsl(var(--foreground))]">No lineage data available</h3>
            <p className="mt-1 text-sm text-[hsl(var(--muted-foreground))]">
              This dataset doesn't have lineage information yet
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
