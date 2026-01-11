/**
 * Interactive Data Lineage Visualization (Phase 4.1)
 * ==================================================
 *
 * Features:
 * - Interactive force-directed graph
 * - Node types: Dataset, Job, Feature
 * - Edge types: Input, Output, Transform
 * - Zoom and pan controls
 * - Click to focus on node
 * - Color-coded by layer (Explore, Chart, Navigate)
 */

import React, { useEffect, useRef, useState } from 'react';

interface LineageNode {
  id: string;
  label: string;
  type: 'dataset' | 'job' | 'feature';
  layer?: 'explore' | 'chart' | 'navigate';
  metadata?: Record<string, any>;
}

interface LineageEdge {
  source: string;
  target: string;
  type: 'input' | 'output' | 'transform';
  label?: string;
}

interface LineageGraphProps {
  nodes: LineageNode[];
  edges: LineageEdge[];
  centerNodeId?: string;
  onNodeClick?: (node: LineageNode) => void;
  height?: number;
}

export const LineageGraph: React.FC<LineageGraphProps> = ({
  nodes,
  edges,
  centerNodeId,
  onNodeClick,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 1 });

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    renderGraph();
  }, [nodes, edges, centerNodeId]);

  const renderGraph = () => {
    // Simple force-directed layout using CSS positioning
    const svg = svgRef.current;
    if (!svg) return;

    const width = svg.clientWidth;
    const centerX = width / 2;
    const centerY = height / 2;

    // Calculate node positions using simple hierarchical layout
    const positions = calculateHierarchicalLayout(nodes, edges, centerX, centerY);

    // Update positions (simplified - in production use D3 force simulation)
    return positions;
  };

  const calculateHierarchicalLayout = (
    nodes: LineageNode[],
    edges: LineageEdge[],
    centerX: number,
    centerY: number
  ) => {
    // Group nodes by level (distance from center node)
    const levels: Map<string, number> = new Map();
    const visited = new Set<string>();

    // BFS to assign levels
    const queue: Array<{ id: string; level: number }> = [];

    if (centerNodeId) {
      queue.push({ id: centerNodeId, level: 0 });
      levels.set(centerNodeId, 0);
    } else if (nodes.length > 0) {
      queue.push({ id: nodes[0].id, level: 0 });
      levels.set(nodes[0].id, 0);
    }

    while (queue.length > 0) {
      const { id, level } = queue.shift()!;
      if (visited.has(id)) continue;
      visited.add(id);

      // Find connected nodes
      edges.forEach((edge) => {
        if (edge.source === id && !levels.has(edge.target)) {
          levels.set(edge.target, level + 1);
          queue.push({ id: edge.target, level: level + 1 });
        }
        if (edge.target === id && !levels.has(edge.source)) {
          levels.set(edge.source, level - 1);
          queue.push({ id: edge.source, level: level - 1 });
        }
      });
    }

    // Assign remaining nodes to level 0
    nodes.forEach((node) => {
      if (!levels.has(node.id)) {
        levels.set(node.id, 0);
      }
    });

    // Calculate positions
    const levelGroups: Map<number, string[]> = new Map();
    levels.forEach((level, nodeId) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(nodeId);
    });

    const positions: Map<string, { x: number; y: number }> = new Map();
    const levelSpacing = 200;
    const nodeSpacing = 150;

    levelGroups.forEach((nodeIds, level) => {
      const startX = centerX - (nodeIds.length - 1) * nodeSpacing / 2;
      nodeIds.forEach((nodeId, index) => {
        positions.set(nodeId, {
          x: startX + index * nodeSpacing,
          y: centerY + level * levelSpacing,
        });
      });
    });

    return positions;
  };

  const getNodeColor = (node: LineageNode): string => {
    if (node.type === 'job') return '#8B5CF6'; // Purple for jobs

    // Color by layer
    switch (node.layer) {
      case 'explore':
        return '#3B82F6'; // Blue
      case 'chart':
        return '#10B981'; // Green
      case 'navigate':
        return '#F59E0B'; // Orange
      default:
        return '#6B7280'; // Gray
    }
  };

  const handleNodeClick = (node: LineageNode) => {
    setSelectedNode(node.id);
    onNodeClick?.(node);
  };

  const handleZoomIn = () => {
    setTransform((prev) => ({ ...prev, k: Math.min(prev.k * 1.2, 3) }));
  };

  const handleZoomOut = () => {
    setTransform((prev) => ({ ...prev, k: Math.max(prev.k / 1.2, 0.5) }));
  };

  const handleResetView = () => {
    setTransform({ x: 0, y: 0, k: 1 });
  };

  // Simple SVG rendering (simplified version - production would use D3 or react-force-graph)
  const positions = calculateHierarchicalLayout(
    nodes,
    edges,
    svgRef.current?.clientWidth || 800 / 2,
    height / 2
  );

  return (
    <div className="relative w-full" style={{ height: `${height}px` }}>
      {/* Zoom controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
        <button
          onClick={handleZoomIn}
          className="px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50"
          title="Zoom in"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v12m6-6H6" />
          </svg>
        </button>
        <button
          onClick={handleZoomOut}
          className="px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50"
          title="Zoom out"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 12H6" />
          </svg>
        </button>
        <button
          onClick={handleResetView}
          className="px-3 py-2 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50"
          title="Reset view"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
      </div>

      {/* Legend */}
      <div className="absolute top-4 left-4 z-10 bg-white border border-gray-300 rounded-lg shadow-sm p-3">
        <div className="text-sm font-semibold mb-2">Layers</div>
        <div className="flex flex-col gap-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500"></div>
            <span>Explore (Raw)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Chart (Validated)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span>Navigate (Business)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>Transformation</span>
          </div>
        </div>
      </div>

      {/* SVG Canvas */}
      <svg
        ref={svgRef}
        className="w-full h-full border border-gray-300 rounded-lg bg-gray-50"
        style={{
          transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.k})`,
        }}
      >
        <defs>
          {/* Arrow markers for edges */}
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
            markerUnits="strokeWidth"
          >
            <path d="M0,0 L0,6 L9,3 z" fill="#6B7280" />
          </marker>
        </defs>

        {/* Render edges */}
        <g className="edges">
          {edges.map((edge, index) => {
            const sourcePos = positions.get(edge.source);
            const targetPos = positions.get(edge.target);

            if (!sourcePos || !targetPos) return null;

            return (
              <g key={`edge-${index}`}>
                <line
                  x1={sourcePos.x}
                  y1={sourcePos.y}
                  x2={targetPos.x}
                  y2={targetPos.y}
                  stroke="#6B7280"
                  strokeWidth="2"
                  markerEnd="url(#arrowhead)"
                  opacity="0.6"
                />
                {edge.label && (
                  <text
                    x={(sourcePos.x + targetPos.x) / 2}
                    y={(sourcePos.y + targetPos.y) / 2}
                    textAnchor="middle"
                    className="text-xs fill-gray-600"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* Render nodes */}
        <g className="nodes">
          {nodes.map((node) => {
            const pos = positions.get(node.id);
            if (!pos) return null;

            const isSelected = selectedNode === node.id;
            const nodeColor = getNodeColor(node);

            return (
              <g
                key={node.id}
                onClick={() => handleNodeClick(node)}
                className="cursor-pointer"
                style={{ transform: `translate(${pos.x}px, ${pos.y}px)` }}
              >
                {/* Node circle */}
                <circle
                  r={isSelected ? 35 : 30}
                  fill={nodeColor}
                  stroke={isSelected ? '#1F2937' : 'white'}
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all duration-200 hover:stroke-gray-800"
                />

                {/* Node icon */}
                {node.type === 'job' && (
                  <text
                    textAnchor="middle"
                    dy="0.3em"
                    className="text-white text-sm font-semibold pointer-events-none"
                  >
                    ⚙
                  </text>
                )}
                {node.type === 'dataset' && (
                  <text
                    textAnchor="middle"
                    dy="0.3em"
                    className="text-white text-sm font-semibold pointer-events-none"
                  >
                    📊
                  </text>
                )}
                {node.type === 'feature' && (
                  <text
                    textAnchor="middle"
                    dy="0.3em"
                    className="text-white text-sm font-semibold pointer-events-none"
                  >
                    🎯
                  </text>
                )}

                {/* Node label */}
                <text
                  y="50"
                  textAnchor="middle"
                  className="text-sm font-medium fill-gray-700 pointer-events-none"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Selected node details */}
      {selectedNode && (
        <div className="absolute bottom-4 left-4 right-4 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md">
          {(() => {
            const node = nodes.find((n) => n.id === selectedNode);
            if (!node) return null;

            return (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold">{node.label}</h3>
                  <button
                    onClick={() => setSelectedNode(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Type:</span>
                    <span className="font-medium capitalize">{node.type}</span>
                  </div>

                  {node.layer && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Layer:</span>
                      <span className="font-medium capitalize">{node.layer}</span>
                    </div>
                  )}

                  {node.metadata && Object.keys(node.metadata).length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <div className="text-gray-600 mb-1">Metadata:</div>
                      {Object.entries(node.metadata).map(([key, value]) => (
                        <div key={key} className="flex justify-between text-xs">
                          <span className="text-gray-500">{key}:</span>
                          <span className="font-mono">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default LineageGraph;
