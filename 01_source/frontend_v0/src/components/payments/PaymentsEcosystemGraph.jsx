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

const SEGMENT_X = {
  LOCKER_NETWORK: 40,
  LOCKER_NETWORK_OPERATOR: 280,
  CARRIER_LAST_MILE: 520,
  MARKETPLACE: 760,
  COLLECTION_POINT: 1000,
  LOGISTICS_PLATFORM: 1240,
  FOOD_DELIVERY: 1480,
  PAYMENTS_FISCAL: 1720,
};

const SEGMENT_STYLE = {
  LOCKER_NETWORK: { bg: "#1e3a5f", border: "#3b82f6" },
  MARKETPLACE: { bg: "#3d1a4a", border: "#a855f7" },
  CARRIER_LAST_MILE: { bg: "#1a3d2e", border: "#22c55e" },
  LOGISTICS_PLATFORM: { bg: "#3d2a1a", border: "#f97316" },
  PAYMENTS_FISCAL: { bg: "#3d3d1a", border: "#eab308" },
};

function layoutGraph(graph) {
  const bySegment = {};
  (graph?.nodes || []).forEach((n) => {
    const seg = n.segment || "LOCKER_NETWORK";
    if (!bySegment[seg]) bySegment[seg] = [];
    bySegment[seg].push(n);
  });
  const codeToId = new Map((graph?.nodes || []).map((n) => [n.code, n.id]));
  const nodes = [];
  Object.entries(bySegment).forEach(([segment, list]) => {
    const x = SEGMENT_X[segment] || 40;
    const style = SEGMENT_STYLE[segment] || { bg: "#1e293b", border: "#64748b" };
    list.forEach((n, i) => {
      const live = n.integration_status === "LIVE";
      nodes.push({
        id: n.id,
        data: { label: `${n.code}\n${(n.label || "").slice(0, 20)}` },
        position: { x, y: 24 + i * 76 },
        style: {
          background: style.bg,
          border: `2px solid ${live ? "#22c55e" : style.border}`,
          color: "#e2e8f0",
          fontSize: 11,
          padding: 8,
          borderRadius: 8,
          whiteSpace: "pre-line",
        },
      });
    });
  });
  const edges = (graph?.edges || [])
    .map((e, idx) => {
      const src = codeToId.get(e.from_code);
      const tgt = codeToId.get(e.to_code);
      if (!src || !tgt) return null;
      return {
        id: `e-${idx}`,
        source: src,
        target: tgt,
        label: e.relation_type,
        animated: e.relation_type === "AGGREGATES",
        style: { stroke: "#94a3b8" },
        labelStyle: { fill: "#94a3b8", fontSize: 9 },
      };
    })
    .filter(Boolean);
  return { nodes, edges };
}

export default function PaymentsEcosystemGraph({ graph, loading, error, height = 520 }) {
  const laid = useMemo(() => layoutGraph(graph), [graph]);
  const [nodes, setNodes, onNodesChange] = useNodesState(laid.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(laid.edges);

  useEffect(() => {
    setNodes(laid.nodes);
    setEdges(laid.edges);
  }, [laid, setNodes, setEdges]);

  if (loading) return <p style={{ fontSize: 13, opacity: 0.8 }}>Carregando grafo…</p>;
  if (error) return <p style={{ fontSize: 13, color: "#f87171" }}>{error}</p>;
  if (!graph?.nodes?.length) {
    return <p style={{ fontSize: 13, opacity: 0.8 }}>Sem nos — rode Seed mundial.</p>;
  }

  return (
    <div
      style={{ height, borderRadius: 8, border: "1px solid rgba(148,163,184,0.25)", marginBottom: 12 }}
      data-testid="payments-ecosystem-graph"
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
