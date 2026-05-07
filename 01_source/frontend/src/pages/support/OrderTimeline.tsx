import { FormEvent, useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

const orderPickupBaseUrl = import.meta.env.VITE_ORDER_PICKUP_BASE_URL ?? 'http://localhost:8003'

type SupportTimeline = {
  order_id: string
  status?: string
  next_action?: string
  timeline?: Array<{ event: string; timestamp: string }>
  summary?: Record<string, unknown>
  events?: unknown[]
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export default function SupportOrderTimelinePage() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [orderId, setOrderId] = useState(params.id ?? 'ORDER-MVP-001')
  const [payload, setPayload] = useState<SupportTimeline | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchJson<SupportTimeline>(
        `${orderPickupBaseUrl}/api/v1/support/order/${encodeURIComponent(id)}`,
      )
      setPayload(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao consultar suporte.')
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    navigate(`/support/order/${encodeURIComponent(orderId)}`)
    void load(orderId)
  }

  useEffect(() => {
    const id = params.id ?? 'ORDER-MVP-001'
    setOrderId(id)
    void load(id)
  }, [params.id])

  return (
    <div className="space-y-6 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-300">
          Sprint 2 MVP
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">Suporte N1/N2 / Timeline</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Consulta operacional por pedido para orientar atendimento, runbook e escalonamento.
        </p>
      </div>

      <form className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900" onSubmit={submit}>
        <input
          className="min-w-72 flex-1 rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
          value={orderId}
          onChange={(event) => setOrderId(event.target.value)}
          aria-label="Order ID"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Consultando...' : 'Consultar'}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Resumo</h2>
          <dl className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <Row label="Order ID" value={payload?.order_id ?? orderId} />
            <Row label="Status" value={payload?.status ?? String(payload?.summary?.order_status ?? '—')} />
            <Row label="Próxima ação" value={payload?.next_action ?? String(payload?.summary?.next_action ?? '—')} />
          </dl>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Payload</h2>
          <pre className="mt-3 max-h-96 overflow-auto rounded bg-slate-50 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-200">
            {payload ? JSON.stringify(payload, null, 2) : 'Sem dados ainda.'}
          </pre>
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-3">
      <dt>{label}</dt>
      <dd className="break-all font-mono text-slate-900 dark:text-slate-100">{value}</dd>
    </div>
  )
}
