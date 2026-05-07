import { FormEvent, useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

const orderPickupBaseUrl = import.meta.env.VITE_ORDER_PICKUP_BASE_URL ?? 'http://localhost:8003'

type TimelineEvent = {
  event?: string
  kind?: string
  status?: string | null
  timestamp?: string | null
  detail?: Record<string, unknown>
}

type SupportLookupPayload = {
  order_id: string
  status?: string
  next_action?: string
  timeline?: TimelineEvent[]
  summary?: {
    order_status?: string | null
    allocation_state?: string | null
    pickup_status?: string | null
    next_action?: string | null
  }
  events?: TimelineEvent[]
}

type LookupHistoryItem = {
  orderId: string
  status: string
  nextAction: string
  checkedAt: string
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

function normalizeEvents(payload: SupportLookupPayload | null): TimelineEvent[] {
  if (!payload) {
    return []
  }
  if (Array.isArray(payload.events) && payload.events.length > 0) {
    return payload.events
  }
  return payload.timeline ?? []
}

export function OrderLookup() {
  const params = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [orderId, setOrderId] = useState(params.id ?? 'ORDER-MVP-001')
  const [payload, setPayload] = useState<SupportLookupPayload | null>(null)
  const [history, setHistory] = useState<LookupHistoryItem[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const events = useMemo(() => normalizeEvents(payload), [payload])
  const status = payload?.status ?? payload?.summary?.order_status ?? '—'
  const nextAction = payload?.next_action ?? payload?.summary?.next_action ?? '—'

  const load = async (id: string) => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchJson<SupportLookupPayload>(
        `${orderPickupBaseUrl}/api/v1/support/order/${encodeURIComponent(id)}`,
      )
      setPayload(data)
      setHistory((current) => [
        {
          orderId: data.order_id,
          status: data.status ?? data.summary?.order_status ?? 'unknown',
          nextAction: data.next_action ?? data.summary?.next_action ?? 'review',
          checkedAt: new Date().toISOString(),
        },
        ...current.filter((item) => item.orderId !== data.order_id),
      ].slice(0, 6))
    } catch (err) {
      setPayload(null)
      setError(err instanceof Error ? err.message : 'Falha ao consultar pedido.')
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const id = orderId.trim()
    if (!id) {
      setError('Informe um order_id.')
      return
    }
    navigate(`/support/order/${encodeURIComponent(id)}`)
    void load(id)
  }

  useEffect(() => {
    const id = params.id ?? 'ORDER-MVP-001'
    setOrderId(id)
    void load(id)
  }, [params.id])

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-300">
            Sprint 2 MVP+
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">Suporte N1/N2 / Busca por Pedido</h1>
          <p className="mt-2 max-w-3xl text-sm text-slate-600 dark:text-slate-400">
            Console de atendimento para localizar um pedido, ler a timeline operacional e orientar a próxima ação.
          </p>
        </div>
        <Link
          to="/support"
          className="rounded border border-slate-300 px-3 py-2 text-sm text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Central de suporte
        </Link>
      </div>

      <form className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900" onSubmit={submit}>
        <input
          className="min-w-72 flex-1 rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
          value={orderId}
          onChange={(event) => setOrderId(event.target.value)}
          placeholder="Order ID"
          aria-label="Order ID"
        />
        <button
          type="submit"
          disabled={loading}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Consultando...' : 'Buscar pedido'}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <p className="font-semibold">Falha na consulta</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard label="Order ID" value={payload?.order_id ?? orderId} />
        <SummaryCard label="Status" value={String(status)} />
        <SummaryCard label="Próxima ação" value={String(nextAction)} />
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Timeline operacional</h2>
          <div className="mt-4 space-y-3">
            {events.map((event, index) => (
              <div key={`${event.event ?? event.kind ?? 'event'}-${index}`} className="rounded-lg border border-slate-100 p-3 dark:border-slate-800">
                <div className="flex flex-wrap justify-between gap-2">
                  <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                    {event.event ?? event.kind ?? 'evento'}
                  </p>
                  <p className="font-mono text-xs text-slate-500 dark:text-slate-400">
                    {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'sem timestamp'}
                  </p>
                </div>
                {event.status && (
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">status: {event.status}</p>
                )}
              </div>
            ))}
            {events.length === 0 && (
              <p className="rounded-lg bg-slate-50 p-4 text-sm text-slate-500 dark:bg-slate-950 dark:text-slate-400">
                Nenhum evento carregado.
              </p>
            )}
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Histórico local</h2>
            <div className="mt-3 space-y-2">
              {history.map((item) => (
                <button
                  key={item.orderId}
                  type="button"
                  onClick={() => {
                    setOrderId(item.orderId)
                    navigate(`/support/order/${encodeURIComponent(item.orderId)}`)
                    void load(item.orderId)
                  }}
                  className="block w-full rounded border border-slate-100 p-2 text-left text-xs hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
                >
                  <span className="font-mono">{item.orderId}</span>
                  <span className="ml-2 text-slate-500">{item.status}</span>
                </button>
              ))}
              {history.length === 0 && <p className="text-sm text-slate-500">Sem consultas recentes.</p>}
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Payload técnico</h2>
            <pre className="mt-3 max-h-80 overflow-auto rounded bg-slate-50 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-200">
              {payload ? JSON.stringify(payload, null, 2) : 'Sem payload.'}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}

export default OrderLookup

function SummaryCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-2 break-all font-mono text-lg font-semibold text-slate-900 dark:text-slate-50">{value}</p>
    </div>
  )
}
