import { useEffect, useMemo } from 'react'
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'

export type EcosystemGraphPayload = {
  nodes: {
    id: string
    code: string
    label: string
    segment: string
    integration_status: string
    readiness_score: number | null
  }[]
  edges: { from_code: string; to_code: string; relation_type: string }[]
  node_count?: number
  edge_count?: number
}

const SEGMENT_X: Record<string, number> = {
  LOCKER_NETWORK: 40,
  LOCKER_NETWORK_OPERATOR: 280,
  CARRIER_LAST_MILE: 520,
  MARKETPLACE: 760,
  COLLECTION_POINT: 1000,
  LOGISTICS_PLATFORM: 1240,
  FOOD_DELIVERY: 1480,
  PAYMENTS_FISCAL: 1720,
}

const SEGMENT_STYLE: Record<string, { bg: string; border: string }> = {
  LOCKER_NETWORK: { bg: '#1e3a5f', border: '#3b82f6' },
  MARKETPLACE: { bg: '#3d1a4a', border: '#a855f7' },
  CARRIER_LAST_MILE: { bg: '#1a3d2e', border: '#22c55e' },
  LOGISTICS_PLATFORM: { bg: '#3d2a1a', border: '#f97316' },
  PAYMENTS_FISCAL: { bg: '#3d3d1a', border: '#eab308' },
  FOOD_DELIVERY: { bg: '#4a1a2e', border: '#ec4899' },
  COLLECTION_POINT: { bg: '#1a3d3d', border: '#14b8a6' },
  LOCKER_NETWORK_OPERATOR: { bg: '#2a2a4a', border: '#6366f1' },
}

const DEFAULT_STYLE = { bg: '#1e293b', border: '#64748b' }

function layoutGraph(graph: EcosystemGraphPayload): { nodes: Node[]; edges: Edge[] } {
  const bySegment: Record<string, EcosystemGraphPayload['nodes']> = {}
  for (const n of graph.nodes) {
    const seg = n.segment || 'LOCKER_NETWORK'
    if (!bySegment[seg]) bySegment[seg] = []
    bySegment[seg].push(n)
  }

  const codeToId = new Map(graph.nodes.map((n) => [n.code, n.id]))
  const positioned: Node[] = []

  Object.entries(bySegment).forEach(([segment, list]) => {
    const x = SEGMENT_X[segment] ?? 40
    const style = SEGMENT_STYLE[segment] ?? DEFAULT_STYLE
    list.forEach((n, i) => {
      const live = n.integration_status === 'LIVE'
      positioned.push({
        id: n.id,
        data: {
          label: (
            <div className="text-center leading-tight">
              <div className="font-semibold">{n.code}</div>
              <div className="text-[10px] opacity-80">{n.label.slice(0, 22)}</div>
              {n.readiness_score != null ? (
                <div className="text-[10px] text-amber-300">r{n.readiness_score}</div>
              ) : null}
            </div>
          ),
        },
        position: { x, y: 24 + i * 76 },
        style: {
          background: style.bg,
          border: `2px solid ${live ? '#22c55e' : style.border}`,
          color: '#e2e8f0',
          fontSize: 11,
          padding: 6,
          borderRadius: 8,
          minWidth: 120,
        },
      })
    })
  })

  const edges: Edge[] = graph.edges
    .map((e, idx) => {
      const src = codeToId.get(e.from_code)
      const tgt = codeToId.get(e.to_code)
      if (!src || !tgt) return null
      return {
        id: `e-${idx}-${e.from_code}-${e.to_code}`,
        source: src,
        target: tgt,
        label: e.relation_type,
        animated: e.relation_type === 'AGGREGATES' || e.relation_type === 'CHANNEL_USES_CARRIER',
        style: { stroke: '#94a3b8' },
        labelStyle: { fill: '#cbd5e1', fontSize: 9 },
      } as Edge
    })
    .filter((e): e is Edge => e !== null)

  return { nodes: positioned, edges }
}

type Props = {
  graph: EcosystemGraphPayload | null
  loading?: boolean
  error?: string | null
  height?: number
}

export default function EcosystemGraphFlow({ graph, loading, error, height = 520 }: Props) {
  const laid = useMemo(
    () => (graph?.nodes?.length ? layoutGraph(graph) : { nodes: [], edges: [] }),
    [graph],
  )
  const [nodes, setNodes, onNodesChange] = useNodesState(laid.nodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(laid.edges)

  useEffect(() => {
    setNodes(laid.nodes)
    setEdges(laid.edges)
  }, [laid, setNodes, setEdges])

  if (loading) {
    return <p className="text-sm text-gray-500">Carregando grafo do ecossistema…</p>
  }
  if (error) {
    return <p className="text-sm text-red-600">{error}</p>
  }
  if (!graph?.nodes?.length) {
    return (
      <p className="text-sm text-gray-500">
        Sem nós no grafo. Execute Seed mundial ou cadastre players no ecossistema.
      </p>
    )
  }

  return (
    <div
      className="w-full rounded-lg border border-slate-300 dark:border-slate-600"
      style={{ height }}
      data-testid="ecosystem-graph-flow"
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        minZoom={0.2}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} color="#334155" />
        <Controls />
        <MiniMap
          nodeStrokeWidth={2}
          zoomable
          pannable
          style={{ background: '#0f172a' }}
        />
      </ReactFlow>
      <p className="border-t px-2 py-1 text-xs text-gray-500">
        {graph.node_count ?? graph.nodes.length} players · {graph.edge_count ?? graph.edges.length}{' '}
        relações · arraste para explorar
      </p>
    </div>
  )
}
