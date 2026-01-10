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

  const getLayerColor = (layer?: string) => {
    switch (layer) {
      case 'explore':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'chart':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'navigate':
        return 'bg-purple-100 text-purple-800 border-purple-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
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
            className={`flex items-center gap-3 p-3 rounded-lg border-2 transition-all hover:shadow-md ${getLayerColor(
              node.layer
            )} ${level > 0 ? 'ml-8' : ''}`}
            style={{ marginLeft: level > 0 ? `${level * 2}rem` : 0 }}
          >
            {hasChildren && (
              <button
                onClick={() => toggleNode(node.id)}
                className="flex-shrink-0 text-gray-600 hover:text-gray-900"
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
              <span className="px-2 py-1 text-xs font-medium rounded bg-white bg-opacity-50">
                {node.layer}
              </span>
            )}
          </div>

          {hasChildren && isExpanded && (
            <div className="mt-2 space-y-2 relative">
              {/* Connecting line */}
              <div
                className="absolute left-4 top-0 bottom-0 w-px bg-gray-300"
                style={{ left: `${level * 2 + 1}rem` }}
              />

              {outgoingEdges.map((edge) => {
                const targetNode = graph.nodes.find((n) => n.id === edge.target);
                if (!targetNode) return null;

                return (
                  <div key={edge.target} className="relative">
                    <div
                      className="absolute top-1/2 bg-gray-300"
                      style={{
                        left: `${level * 2 + 1}rem`,
                        width: '1rem',
                        height: '1px',
                      }}
                    />
                    <div
                      className="text-xs text-gray-500 italic px-3 py-1"
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

  // Alternative simple list view (commented out, using tree view instead)
  // const renderSimpleList = (graph: LineageGraph) => {
  //   if (!graph || !graph.nodes || !graph.edges) return null;
  //   return (
  //     <div className="space-y-4">
  //       {graph.nodes.map((node) => {
  //         const outgoingEdges = graph.edges.filter((e) => e.source === node.id);
  //         return (
  //           <div key={node.id}>
  //             <div className={`flex items-center gap-3 p-4 rounded-lg border-2 ${getLayerColor(node.layer)}`}>
  //               <Database className="h-6 w-6" />
  //               <div className="flex-1">
  //                 <div className="font-semibold text-lg">{node.name}</div>
  //                 <div className="text-sm opacity-75">{node.type}</div>
  //               </div>
  //               {node.layer && <span className="px-3 py-1 text-sm font-medium rounded bg-white bg-opacity-50">{node.layer} layer</span>}
  //             </div>
  //             {outgoingEdges.length > 0 && outgoingEdges.map((edge, edgeIdx) => {
  //               const targetNode = graph.nodes.find((n) => n.id === edge.target);
  //               if (!targetNode) return null;
  //               return (
  //                 <div key={edgeIdx} className="ml-8 mt-2 flex items-center gap-2">
  //                   <ArrowRight className="h-4 w-4 text-gray-400" />
  //                   <span className="text-sm text-gray-600 italic">{edge.operation}</span>
  //                 </div>
  //               );
  //             })}
  //           </div>
  //         );
  //       })}
  //     </div>
  //   );
  // };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Data Lineage</h1>
        <p className="mt-2 text-sm text-gray-600">
          Track data transformations across pipeline layers
        </p>
      </div>

      {/* Controls */}
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Dataset
            </label>
            <select
              value={selectedDataset}
              onChange={(e) => setSelectedDataset(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Lineage Depth
            </label>
            <select
              value={depth}
              onChange={(e) => setDepth(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
            >
              <option value={1}>1 level</option>
              <option value={2}>2 levels</option>
              <option value={3}>3 levels</option>
              <option value={5}>5 levels (full)</option>
            </select>
          </div>
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center gap-2 mb-2">
            <Layers className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">Pipeline Layers:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="flex items-center gap-2 px-3 py-1 rounded border-2 bg-blue-100 text-blue-800 border-blue-300">
              <div className="w-2 h-2 bg-blue-600 rounded-full" />
              <span className="text-sm font-medium">Explore (Raw)</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded border-2 bg-green-100 text-green-800 border-green-300">
              <div className="w-2 h-2 bg-green-600 rounded-full" />
              <span className="text-sm font-medium">Chart (Validated)</span>
            </div>
            <div className="flex items-center gap-2 px-3 py-1 rounded border-2 bg-purple-100 text-purple-800 border-purple-300">
              <div className="w-2 h-2 bg-purple-600 rounded-full" />
              <span className="text-sm font-medium">Navigate (Business)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Lineage Visualization */}
      {!selectedDataset ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <GitBranch className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No dataset selected</h3>
          <p className="mt-1 text-sm text-gray-500">
            Select a dataset above to view its lineage graph
          </p>
        </div>
      ) : isLoading ? (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" />
          <p className="mt-4 text-sm text-gray-500">Loading lineage...</p>
        </div>
      ) : lineage && lineage.nodes && lineage.nodes.length > 0 ? (
        <div className="bg-white shadow-md rounded-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">Lineage Graph</h2>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <Database className="h-4 w-4" />
              <span>{lineage.nodes.length} datasets</span>
              <ArrowRight className="h-4 w-4 ml-2" />
              <span>{lineage.edges.length} transformations</span>
            </div>
          </div>

          {/* Tree Structure */}
          {buildTreeStructure(lineage)}

          {/* Alternative: Simple List View */}
          {/* {renderSimpleList(lineage)} */}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-12 text-center">
          <GitBranch className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No lineage data available</h3>
          <p className="mt-1 text-sm text-gray-500">
            This dataset doesn't have lineage information yet
          </p>
        </div>
      )}
    </div>
  );
}
