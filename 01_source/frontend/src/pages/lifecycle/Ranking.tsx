import { Component, type ErrorInfo, type ReactNode, useCallback, useEffect, useState } from 'react'
import { isAxiosError } from 'axios'
import { lifecycleApi } from '../../api/lifecycle'

export type PickupRankingItem = {
  rank: number
  dimension_value: string | null
  metric: string
  metric_value: number
  total_terminal_pickups: number
  redeemed_pickups: number
  expired_pickups: number
  cancelled_pickups: number
  redemption_rate: number
  expiration_rate: number
  cancellation_rate: number
  avg_minutes_created_to_ready: number | null
  avg_minutes_ready_to_redeemed: number | null
  avg_minutes_door_opened_to_redeemed: number | null
  avg_minutes_door_opened_to_door_closed: number | null
}

export type PickupRankingResponse = {
  category: string
  metric: string
  dimension: string
  direction: string
  limit: number
  window_start: string | null
  window_end: string | null
  items: PickupRankingItem[]
  filters: Record<string, unknown>
}

function parseItem(raw: unknown): PickupRankingItem | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.rank !== 'number' || typeof o.metric !== 'string' || typeof o.metric_value !== 'number') return null
  return {
    rank: o.rank,
    dimension_value:
      o.dimension_value === null || o.dimension_value === undefined
        ? null
        : String(o.dimension_value),
    metric: o.metric,
    metric_value: o.metric_value,
    total_terminal_pickups: typeof o.total_terminal_pickups === 'number' ? o.total_terminal_pickups : 0,
    redeemed_pickups: typeof o.redeemed_pickups === 'number' ? o.redeemed_pickups : 0,
    expired_pickups: typeof o.expired_pickups === 'number' ? o.expired_pickups : 0,
    cancelled_pickups: typeof o.cancelled_pickups === 'number' ? o.cancelled_pickups : 0,
    redemption_rate: typeof o.redemption_rate === 'number' ? o.redemption_rate : 0,
    expiration_rate: typeof o.expiration_rate === 'number' ? o.expiration_rate : 0,
    cancellation_rate: typeof o.cancellation_rate === 'number' ? o.cancellation_rate : 0,
    avg_minutes_created_to_ready: typeof o.avg_minutes_created_to_ready === 'number' ? o.avg_minutes_created_to_ready : null,
    avg_minutes_ready_to_redeemed: typeof o.avg_minutes_ready_to_redeemed === 'number' ? o.avg_minutes_ready_to_redeemed : null,
    avg_minutes_door_opened_to_redeemed:
      typeof o.avg_minutes_door_opened_to_redeemed === 'number' ? o.avg_minutes_door_opened_to_redeemed : null,
    avg_minutes_door_opened_to_door_closed:
      typeof o.avg_minutes_door_opened_to_door_closed === 'number' ? o.avg_minutes_door_opened_to_door_closed : null,
  }
}

function parsePickupRanking(raw: unknown): PickupRankingResponse | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.category !== 'string' || typeof o.metric !== 'string' || typeof o.dimension !== 'string') return null
  const itemsRaw = o.items
  if (!Array.isArray(itemsRaw)) return null
  const items: PickupRankingItem[] = []
  for (const row of itemsRaw) {
    const it = parseItem(row)
    if (it) items.push(it)
  }
  return {
    category: o.category,
    metric: o.metric,
    dimension: o.dimension,
    direction: typeof o.direction === 'string' ? o.direction : 'desc',
    limit: typeof o.limit === 'number' ? o.limit : items.length,
    window_start: typeof o.window_start === 'string' ? o.window_start : null,
    window_end: typeof o.window_end === 'string' ? o.window_end : null,
    items,
    filters: o.filters && typeof o.filters === 'object' ? (o.filters as Record<string, unknown>) : {},
  }
}

function axiosDetail(err: unknown): string {
  if (isAxiosError(err)) {
    const d = err.response?.data as { detail?: string } | undefined
    if (d?.detail) return d.detail
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Falha ao carregar ranking'
}

class LifecycleErrorBoundary extends Component<{ children: ReactNode }, { message: string | null }> {
  state: { message: string | null } = { message: null }

  static getDerivedStateFromError(err: Error): { message: string } {
    return { message: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo): void {
    console.error('[lifecycle/ranking]', err, info.componentStack)
  }

  render(): ReactNode {
    if (this.state.message) {
      return (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">
          Erro na interface: {this.state.message}
        </div>
      )
    }
    return this.props.children
  }
}

function RankingBody() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<PickupRankingResponse | null>(null)
  const [category, setCategory] = useState('efficiency')
  const [metric, setMetric] = useState('redemption_rate')
  const [dimension, setDimension] = useState('region')
  const [limit, setLimit] = useState(10)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await lifecycleApi.getRanking({
        category,
        metric,
        dimension,
        limit,
      })
      const parsed = parsePickupRanking(res.data)
      if (!parsed) {
        setError('Resposta inválida do serviço')
        setData(null)
        return
      }
      setData(parsed)
    } catch (e: unknown) {
      setError(axiosDetail(e))
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [category, dimension, limit, metric])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Ciclo de vida — Ranking</h1>
        <p className="text-sm text-gray-500 dark:text-slate-400">PickupRankingResponse (/internal/analytics/pickup-ranking)</p>
      </div>

      <div className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4">
        <label className="text-xs text-gray-600 dark:text-slate-400">
          category
          <input
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          metric
          <input
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          dimension
          <input
            value={dimension}
            onChange={(e) => setDimension(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          limit
          <input
            type="number"
            min={1}
            max={100}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 10)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 md:col-span-4"
        >
          Carregar ranking
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"
            aria-hidden
          />
          Carregando ranking…
        </div>
      )}

      {error && !loading && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {!loading && !error && data && data.items.length === 0 && (
        <p className="text-sm text-slate-500">Nenhuma linha no ranking para os filtros atuais.</p>
      )}

      {!loading && !error && data && data.items.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-slate-700">
          <table className="w-full min-w-[960px] text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-3 py-2">#</th>
                <th className="px-3 py-2">Dimensão</th>
                <th className="px-3 py-2">Métrica</th>
                <th className="px-3 py-2">Valor</th>
                <th className="px-3 py-2">Total term.</th>
                <th className="px-3 py-2">Redeem %</th>
                <th className="px-3 py-2">Exp %</th>
                <th className="px-3 py-2">Cancel %</th>
                <th className="px-3 py-2">Avg ready→redeemed</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
              {data.items.map((row) => (
                <tr key={`${row.rank}-${row.dimension_value ?? 'null'}`} className="dark:text-slate-200">
                  <td className="px-3 py-2">{row.rank}</td>
                  <td className="px-3 py-2">{row.dimension_value ?? '—'}</td>
                  <td className="px-3 py-2">{row.metric}</td>
                  <td className="px-3 py-2">{row.metric_value.toFixed(3)}</td>
                  <td className="px-3 py-2">{row.total_terminal_pickups}</td>
                  <td className="px-3 py-2">{row.redemption_rate.toFixed(3)}</td>
                  <td className="px-3 py-2">{row.expiration_rate.toFixed(3)}</td>
                  <td className="px-3 py-2">{row.cancellation_rate.toFixed(3)}</td>
                  <td className="px-3 py-2">{row.avg_minutes_ready_to_redeemed?.toFixed(3) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !error && data && (
        <p className="text-xs text-slate-500">
          {data.category} / {data.metric} / {data.dimension} — {data.direction} — limite {data.limit}
          {data.window_start ? ` — ${data.window_start}` : ''}
          {data.window_end ? ` → ${data.window_end}` : ''}
        </p>
      )}
    </div>
  )
}

export default function Ranking() {
  return (
    <LifecycleErrorBoundary>
      <RankingBody />
    </LifecycleErrorBoundary>
  )
}
