import { useEffect, useState, useCallback, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
} from 'reactflow'
import type { Node, Edge, NodeMouseHandler } from 'reactflow'
import 'reactflow/dist/style.css'
import {
  Loader2, ArrowLeft, X, FlaskConical,
  FileText, Lightbulb, BookOpen,
} from 'lucide-react'
import { getGraph, type GraphData } from '../api'
import EmptyState from '../components/EmptyState'

// Color per node kind
const KIND_STYLE: Record<string, { bg: string; border: string; text: string }> = {
  project:    { bg: '#eef2ff', border: '#6366f1', text: '#312e81' },
  paper:      { bg: '#dcfce7', border: '#22c55e', text: '#14532d' },
  claim:      { bg: '#f1f5f9', border: '#94a3b8', text: '#334155' },
  gap:        { bg: '#fef3c7', border: '#f59e0b', text: '#78350f' },
  hypothesis: { bg: '#ede9fe', border: '#8b5cf6', text: '#4c1d95' },
}

const ICON_BY_KIND: Record<string, React.ReactNode> = {
  project:    <BookOpen size={14} />,
  paper:      <FileText size={14} />,
  claim:      <div className="w-3 h-3 rounded-full bg-slate-400" />,
  gap:        <FlaskConical size={14} />,
  hypothesis: <Lightbulb size={14} />,
}

export default function KnowledgeGraph() {
  const { id } = useParams()
  const projectId = Number(id)

  const [graph, setGraph] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Node | null>(null)

  useEffect(() => {
    if (isNaN(projectId)) return
    setLoading(true)
    getGraph(projectId)
      .then(setGraph)
      .catch(() => setGraph({ nodes: [], edges: [] }))
      .finally(() => setLoading(false))
  }, [projectId])

  // Convert backend nodes → React Flow nodes with custom styling
  const nodes: Node[] = useMemo(() => {
    if (!graph) return []
    return graph.nodes.map(n => {
      const style = KIND_STYLE[n.data.kind] || KIND_STYLE.claim
      return {
        id: n.id,
        position: n.position,
        data: { ...n.data },
        type: n.type,
        style: {
          background: style.bg,
          color: style.text,
          border: `2px solid ${style.border}`,
          borderRadius: 12,
          padding: '8px 12px',
          fontWeight: 500,
          fontSize: 12,
          maxWidth: 220,
          textAlign: 'center',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        },
      } as Node
    })
  }, [graph])

  const edges: Edge[] = useMemo(() => {
    if (!graph) return []
    return graph.edges.map(e => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: e.animated || false,
      style: e.style || { stroke: '#cbd5e1', strokeWidth: 1.5 },
      markerEnd: {
        type: 'arrowclosed' as any,
        color: e.style?.stroke || '#cbd5e1',
      },
    }))
  }, [graph])

  const onNodeClick: NodeMouseHandler = useCallback((_evt, node) => {
    setSelected(node)
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 text-slate-500">
        <Loader2 className="animate-spin mr-2" /> Loading knowledge graph…
      </div>
    )
  }

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="space-y-6">
        <header>
          <Link
            to={`/projects/${projectId}`}
            className="text-sm text-brand-600 hover:underline inline-flex items-center gap-1 mb-2"
          >
            <ArrowLeft size={14} /> Back to project
          </Link>
          <h2 className="text-3xl font-bold text-slate-900">Knowledge Graph</h2>
        </header>
        <EmptyState
          icon={FlaskConical}
          title="Nothing to visualize yet"
          description="Upload papers and run analysis to build the knowledge graph."
          action={{ label: 'Back to project', to: `/projects/${projectId}` }}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <header className="flex items-start justify-between">
        <div>
          <Link
            to={`/projects/${projectId}`}
            className="text-sm text-brand-600 hover:underline inline-flex items-center gap-1 mb-2"
          >
            <ArrowLeft size={14} /> Back to project
          </Link>
          <h2 className="text-3xl font-bold text-slate-900">Knowledge Graph</h2>
          <p className="text-slate-500 mt-1 text-sm">
            {graph.nodes.length} nodes · {graph.edges.length} edges
          </p>
        </div>

        <div className="hidden md:flex flex-col gap-1.5 text-xs bg-white border border-slate-200 rounded-lg p-3">
          {(['project', 'paper', 'claim', 'gap', 'hypothesis'] as const).map(k => (
            <div key={k} className="flex items-center gap-2">
              <span
                className="inline-block w-3 h-3 rounded"
                style={{
                  background: KIND_STYLE[k].bg,
                  border: `2px solid ${KIND_STYLE[k].border}`,
                }}
              />
              <span className="text-slate-600 capitalize">{k}</span>
            </div>
          ))}
        </div>
      </header>

      <div
        className="bg-white border border-slate-200 rounded-xl overflow-hidden"
        style={{ height: 640 }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.15}
          maxZoom={2}
        >
          <Background gap={16} size={1} color="#e2e8f0" />
          <Controls />
          <MiniMap
            pannable
            zoomable
            nodeColor={(n: any) => KIND_STYLE[n.data?.kind]?.border || '#94a3b8'}
            style={{ background: '#f8fafc' }}
          />
          <Panel
            position="top-right"
            className="text-xs text-slate-500 bg-white/80 px-2 py-1 rounded"
          >
            Click any node for details
          </Panel>
        </ReactFlow>
      </div>

      {selected && (
        <div className="fixed top-0 right-0 h-full w-96 bg-white border-l border-slate-200 shadow-xl z-50 overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              {ICON_BY_KIND[selected.data.kind]}
              <span className="font-semibold text-slate-900 capitalize">
                {selected.data.kind}
              </span>
            </div>
            <button
              onClick={() => setSelected(null)}
              className="p-1 rounded hover:bg-slate-100"
            >
              <X size={18} />
            </button>
          </div>

          <div className="p-5 space-y-4">
            <div>
              <div className="text-xs uppercase text-slate-500 mb-1">Label</div>
              <div className="text-slate-900">{selected.data.label}</div>
            </div>

            {selected.data.detail && (
              <div>
                <div className="text-xs uppercase text-slate-500 mb-1">Details</div>
                <div className="text-sm text-slate-700 whitespace-pre-wrap">
                  {selected.data.detail}
                </div>
              </div>
            )}

            {selected.data.gap_type && (
              <div>
                <div className="text-xs uppercase text-slate-500 mb-1">Gap type</div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 uppercase">
                  {selected.data.gap_type}
                </span>
              </div>
            )}

            {selected.data.claim_type && (
              <div>
                <div className="text-xs uppercase text-slate-500 mb-1">Claim type</div>
                <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 uppercase">
                  {selected.data.claim_type}
                </span>
              </div>
            )}

            {typeof selected.data.score === 'number' && (
              <div>
                <div className="text-xs uppercase text-slate-500 mb-1">Score</div>
                <div className="text-2xl font-bold text-brand-600">
                  {selected.data.score.toFixed(0)}
                </div>
              </div>
            )}

            {selected.data.paper_id && (
              <div>
                <div className="text-xs uppercase text-slate-500 mb-1">Paper</div>
                <div className="text-sm text-slate-600">#{selected.data.paper_id}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}