import React, { useEffect, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

const NODE_COLORS = {
  PROCESSING_ACTIVITY: { bg: "#1e3a5f", border: "#3b82f6" },
  DATA_CATEGORY: { bg: "#1a3d2e", border: "#22c55e" },
  PROCESSOR: { bg: "#3d2a1a", border: "#f97316" },
};

function layoutNodes(rawNodes, rawEdges) {
  const byType = { PROCESSING_ACTIVITY: [], DATA_CATEGORY: [], PROCESSOR: [] };
  rawNodes.forEach((n) => {
    const t = byType[n.node_type] ? n.node_type : "PROCESSING_ACTIVITY";
    (byType[t] || byType.PROCESSING_ACTIVITY).push(n);
  });
  const positioned = [];
  let yOff = 0;
  Object.entries(byType).forEach(([type, list]) => {
    list.forEach((n, i) => {
      positioned.push({
        id: n.id,
        data: { label: n.label },
        position: { x: type === "PROCESSING_ACTIVITY" ? 280 : type === "DATA_CATEGORY" ? 40 : 520, y: yOff + i * 72 },
        style: {
          background: NODE_COLORS[type]?.bg || "#1e293b",
          border: `1px solid ${NODE_COLORS[type]?.border || "#64748b"}`,
          color: "#e2e8f0",
          fontSize: 12,
          padding: 8,
          borderRadius: 8,
          minWidth: 140,
        },
      });
    });
    yOff += Math.max(list.length, 1) * 72 + 24;
  });
  const edges = (rawEdges || []).map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    label: e.edge_type,
    animated: e.edge_type === "PROCESSES",
    style: { stroke: "#94a3b8" },
    labelStyle: { fill: "#94a3b8", fontSize: 10 },
  }));
  return { nodes: positioned, edges };
}

export default function RopaFlowGraph({ graph, loading, error }) {
  const laid = useMemo(
    () => (graph?.nodes?.length ? layoutNodes(graph.nodes, graph.edges) : { nodes: [], edges: [] }),
    [graph],
  );
  const [nodes, setNodes, onNodesChange] = useNodesState(laid.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(laid.edges);

  useEffect(() => {
    setNodes(laid.nodes);
    setEdges(laid.edges);
  }, [laid, setNodes, setEdges]);

  if (loading) return <p style={{ fontSize: 13, opacity: 0.8 }}>Carregando grafo ROPA…</p>;
  if (error) return <p style={{ fontSize: 13, color: "#f87171" }}>{error}</p>;
  if (!graph?.nodes?.length) {
    return <p style={{ fontSize: 13, opacity: 0.8 }}>Sem nos ROPA para este marco. Rode Seed ou cadastre atividades.</p>;
  }

  return (
    <div
      style={{ height: 420, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)", marginBottom: 12 }}
      data-testid="ropa-flow-graph"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} color="#334155" />
        <Controls />
        <MiniMap nodeStrokeWidth={2} zoomable pannable />
      </ReactFlow>
    </div>
  );
}
