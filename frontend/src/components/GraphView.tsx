import { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';
import { GraphNode, GraphEdge, NodeType } from '../types';

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick: (id: string, type: NodeType) => void;
  onNodeExpand: (id: string, type: NodeType) => void;
  selectedNodeId: string | null;
}

/** ラベルを最大文字数で切り詰める */
function truncateLabel(label: string, maxLen: number): string {
  if (label.length <= maxLen) return label;
  return label.slice(0, maxLen - 1) + '…';
}

export function GraphView({ nodes, edges, onNodeClick, onNodeExpand, selectedNodeId }: GraphViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const cy = cytoscape({
      container: containerRef.current,
      minZoom: 0.3,
      maxZoom: 3.0,
      wheelSensitivity: 0.3,
      style: [
        {
          selector: 'node',
          style: {
            'label': 'data(shortLabel)',
            'color': '#fff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '9px',
            'font-family': 'Inter, sans-serif',
            'font-weight': 500,
            'text-outline-width': 0,
            'text-wrap': 'wrap',
            'text-max-width': '60px',
            'text-overflow-wrap': 'anywhere',
          }
        },
        {
          selector: 'node[type = "Document"]',
          style: {
            'shape': 'round-rectangle',
            'background-color': 'rgba(0, 212, 255, 0.25)',
            'border-width': 2,
            'border-color': '#00d4ff',
            'width': 70,
            'height': 40,
            'text-max-width': '62px',
          }
        },
        {
          selector: 'node[type = "Keyword"]',
          style: {
            'shape': 'ellipse',
            'background-color': 'rgba(0, 230, 138, 0.25)',
            'border-width': 2,
            'border-color': '#00e68a',
            'width': 56,
            'height': 56,
            'font-size': '8px',
            'text-max-width': '46px',
          }
        },
        {
          selector: 'node[type = "Equipment"]',
          style: {
            'shape': 'hexagon',
            'background-color': 'rgba(255, 184, 0, 0.25)',
            'border-width': 2,
            'border-color': '#ffb800',
            'width': 52,
            'height': 52,
            'font-size': '9px',
            'text-max-width': '42px',
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'overlay-color': '#ffffff',
            'overlay-opacity': 0.1
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 1.5,
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 0.8,
            'opacity': 0.6,
          }
        },
        {
          selector: 'edge[type = "REFERENCES"]',
          style: {
            'line-color': 'rgba(0, 212, 255, 0.5)',
            'target-arrow-color': 'rgba(0, 212, 255, 0.5)',
            'line-style': 'solid'
          }
        },
        {
          selector: 'edge[type = "HAS_KEYWORD"]',
          style: {
            'line-color': 'rgba(0, 230, 138, 0.4)',
            'target-arrow-color': 'rgba(0, 230, 138, 0.4)',
            'line-style': 'dashed'
          }
        },
        {
          selector: 'edge[type = "USES_EQUIPMENT"]',
          style: {
            'line-color': 'rgba(255, 184, 0, 0.4)',
            'target-arrow-color': 'rgba(255, 184, 0, 0.4)',
            'line-style': 'dotted'
          }
        }
      ],
      layout: {
        name: 'cose',
        animate: false
      }
    });

    cy.on('tap', 'node', (e) => {
      const node = e.target;
      onNodeClick(node.id(), node.data('type') as NodeType);
    });

    cy.on('dblclick', 'node', (e) => {
      const node = e.target;
      onNodeExpand(node.id(), node.data('type') as NodeType);
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, []); // Run once on mount

  // Update elements when nodes/edges change — diff-based to avoid flickering
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    // Build sets of desired IDs
    const desiredNodeIds = new Set(nodes.map(n => n.id));
    const desiredEdgeIds = new Set(edges.map(e => e.id));

    // Build sets of current IDs in cytoscape
    const currentNodeIds = new Set(cy.nodes().map(n => n.id()));
    const currentEdgeIds = new Set(cy.edges().map(e => e.id()));

    // Remove elements no longer in the data
    let hasRemovals = false;
    cy.edges().forEach(e => {
      if (!desiredEdgeIds.has(e.id())) { e.remove(); hasRemovals = true; }
    });
    cy.nodes().forEach(n => {
      if (!desiredNodeIds.has(n.id())) { n.remove(); hasRemovals = true; }
    });

    // Add only new elements
    const elementsToAdd: cytoscape.ElementDefinition[] = [];

    for (const n of nodes) {
      if (!currentNodeIds.has(n.id)) {
        const maxLen = n.node_type === 'Document' ? 12 : 8;
        elementsToAdd.push({
          data: {
            id: n.id,
            label: n.label,
            shortLabel: truncateLabel(n.label, maxLen),
            type: n.node_type,
          }
        });
      }
    }

    for (const e of edges) {
      if (!currentEdgeIds.has(e.id)) {
        elementsToAdd.push({
          data: { id: e.id, source: e.source, target: e.target, type: e.edge_type }
        });
      }
    }

    if (elementsToAdd.length > 0) {
      cy.add(elementsToAdd);
    }

    // Re-run layout when elements changed (added or removed)
    if (elementsToAdd.length > 0 || hasRemovals) {
      cy.layout({
        name: 'cose',
        animate: true,
        animationDuration: 400,
        randomize: false,
        fit: true,
        padding: 40,
      }).run();
    }
  }, [nodes, edges]);

  // Handle selection
  useEffect(() => {
    if (!cyRef.current) return;
    const cy = cyRef.current;

    cy.nodes().removeClass('selected');
    if (selectedNodeId) {
      const node = cy.getElementById(selectedNodeId);
      node.addClass('selected');
      node.select();
    }
  }, [selectedNodeId]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} ref={containerRef} />
  );
}
