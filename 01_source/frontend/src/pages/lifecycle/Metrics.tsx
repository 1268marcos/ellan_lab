import { Component, type ErrorInfo, type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { isAxiosError } from 'axios'
import MetricsChart from '../../components/MetricsChart'
import { lifecycleApi } from '../../api/lifecycle'

export type PickupMetricsResponse = {
  window_start: string | null
  window_end: string | null
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
  filters: Record<string, unknown>
}

function parsePickupMetrics(raw: unknown): PickupMetricsResponse | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.total_terminal_pickups !== 'number') return null
  return {
    window_start: typeof o.window_start === 'string' ? o.window_start : null,
    window_end: typeof o.window_end === 'string' ? o.window_end : null,
    total_terminal_pickups: o.total_terminal_pickups,
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
  return 'Falha ao carregar métricas'
}

class LifecycleErrorBoundary extends Component<{ children: ReactNode }, { message: string | null }> {
  state: { message: string | null } = { message: null }

  static getDerivedStateFromError(err: Error): { message: string } {
    return { message: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo): void {
    console.error('[lifecycle/metrics]', err, info.componentStack)
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

function MetricsBody() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<PickupMetricsResponse | null>(null)
  const [region, setRegion] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await lifecycleApi.getMetrics(region ? { region } : undefined)
      const parsed = parsePickupMetrics(res.data)
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
  }, [region])

  useEffect(() => {
    void load()
  }, [load])

  const rateChart = useMemo(() => {
    if (!data) return []
    return [
      { label: 'Redemption %', value: data.redemption_rate },
      { label: 'Expiration %', value: data.expiration_rate },
      { label: 'Cancellation %', value: data.cancellation_rate },
    ]
  }, [data])

  const volumeChart = useMemo(() => {
    if (!data) return []
    return [
      { label: 'Redeemed', value: data.redeemed_pickups },
      { label: 'Expired', value: data.expired_pickups },
      { label: 'Cancelled', value: data.cancelled_pickups },
    ]
  }, [data])

  const rows = useMemo(() => {
    if (!data) return []
    return [
      ['Janela início', data.window_start ?? '—'],
      ['Janela fim', data.window_end ?? '—'],
      ['Total terminais', String(data.total_terminal_pickups)],
      ['Redeemed', String(data.redeemed_pickups)],
      ['Expired', String(data.expired_pickups)],
      ['Cancelled', String(data.cancelled_pickups)],
      ['Redemption rate %', data.redemption_rate.toFixed(3)],
      ['Expiration rate %', data.expiration_rate.toFixed(3)],
      ['Cancellation rate %', data.cancellation_rate.toFixed(3)],
      ['Avg min created→ready', data.avg_minutes_created_to_ready?.toFixed(3) ?? '—'],
      ['Avg min ready→redeemed', data.avg_minutes_ready_to_redeemed?.toFixed(3) ?? '—'],
      ['Avg min door→redeemed', data.avg_minutes_door_opened_to_redeemed?.toFixed(3) ?? '—'],
      ['Avg min door open→closed', data.avg_minutes_door_opened_to_door_closed?.toFixed(3) ?? '—'],
    ] as const
  }, [data])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Ciclo de vida — Métricas</h1>
        <p className="text-sm text-gray-500 dark:text-slate-400">PickupMetricsResponse (/internal/analytics/pickup-metrics)</p>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Região (opcional)
          <input
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            className="mt-1 block w-48 rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            placeholder="ex: SP"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
        >
          Atualizar
        </button>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"
            aria-hidden
          />
          Carregando métricas…
        </div>
      )}

      {error && !loading && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <MetricsChart title="Taxas (%)" type="bar" data={rateChart} xKey="label" yKey="value" color="#6366F1" />
            <MetricsChart title="Volumes terminais" type="bar" data={volumeChart} xKey="label" yKey="value" color="#10B981" />
          </div>

          <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-2">Campo</th>
                  <th className="px-4 py-2">Valor</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
                {rows.map(([k, v]) => (
                  <tr key={k} className="dark:text-slate-200">
                    <td className="px-4 py-2 font-medium text-gray-700 dark:text-slate-300">{k}</td>
                    <td className="px-4 py-2 text-gray-900 dark:text-slate-100">{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {Object.keys(data.filters).length > 0 && (
            <details className="rounded-lg border border-gray-200 p-3 text-xs dark:border-slate-700 dark:text-slate-300">
              <summary className="cursor-pointer font-medium">Filtros (JSON)</summary>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-all">{JSON.stringify(data.filters, null, 2)}</pre>
            </details>
          )}
        </>
      )}

      {!loading && !error && !data && <p className="text-sm text-slate-500">Sem dados.</p>}
    </div>
  )
}

export default function Metrics() {
  return (
    <LifecycleErrorBoundary>
      <MetricsBody />
    </LifecycleErrorBoundary>
  )
}
