import { Component, type ErrorInfo, type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { isAxiosError } from 'axios'
import MetricsChart from '../../components/MetricsChart'
import { lifecycleApi } from '../../api/lifecycle'

export type HealthResponse = {
  status: string
  database: string
}

function parseHealthResponse(raw: unknown): HealthResponse | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  if (typeof o.status !== 'string' || typeof o.database !== 'string') return null
  return { status: o.status, database: o.database }
}

type PickupHealthSummary = {
  total_entities?: number
  healthy_count?: number
  attention_count?: number
  warning_count?: number
  critical_count?: number
  collapsed_count?: number
}

function parsePickupHealthSummary(raw: unknown): PickupHealthSummary | null {
  if (!raw || typeof raw !== 'object') return null
  const o = raw as Record<string, unknown>
  const s = o.summary
  if (!s || typeof s !== 'object') return null
  return s as PickupHealthSummary
}

function parsePickupHealthRows(raw: unknown): Array<Record<string, unknown>> {
  if (!raw || typeof raw !== 'object') return []
  const o = raw as Record<string, unknown>
  const ranking = o.ranking
  if (!Array.isArray(ranking)) return []
  return ranking.filter((x): x is Record<string, unknown> => !!x && typeof x === 'object') as Array<Record<string, unknown>>
}

function axiosDetail(err: unknown): string {
  if (isAxiosError(err)) {
    const d = err.response?.data as { detail?: string } | undefined
    if (d?.detail) return d.detail
    return err.message
  }
  if (err instanceof Error) return err.message
  return 'Falha ao carregar saúde'
}

class LifecycleErrorBoundary extends Component<{ children: ReactNode }, { message: string | null }> {
  state: { message: string | null } = { message: null }

  static getDerivedStateFromError(err: Error): { message: string } {
    return { message: err.message }
  }

  componentDidCatch(err: Error, info: ErrorInfo): void {
    console.error('[lifecycle/health]', err, info.componentStack)
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

function HealthBody() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [pickupErr, setPickupErr] = useState<string | null>(null)
  const [pickupSummary, setPickupSummary] = useState<PickupHealthSummary | null>(null)
  const [pickupRows, setPickupRows] = useState<Array<Record<string, unknown>>>([])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    setPickupErr(null)
    try {
      const h = await lifecycleApi.getHealth()
      const hp = parseHealthResponse(h.data)
      if (!hp) {
        setError('Resposta /health inválida')
        setHealth(null)
      } else {
        setHealth(hp)
      }
    } catch (e: unknown) {
      setError(axiosDetail(e))
      setHealth(null)
    }

    try {
      const ph = await lifecycleApi.getPickupHealth({
        entity_type: 'all',
        ranking_limit: 15,
        trend_days_window: 7,
        include_alerts: true,
      })
      setPickupSummary(parsePickupHealthSummary(ph.data))
      setPickupRows(parsePickupHealthRows(ph.data))
    } catch (e: unknown) {
      setPickupErr(axiosDetail(e))
      setPickupSummary(null)
      setPickupRows([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const summaryChart = useMemo(() => {
    if (!pickupSummary) return []
    return [
      { label: 'Saudáveis', value: Number(pickupSummary.healthy_count ?? 0) },
      { label: 'Atenção', value: Number(pickupSummary.attention_count ?? 0) },
      { label: 'Alerta', value: Number(pickupSummary.warning_count ?? 0) },
      { label: 'Crítico', value: Number(pickupSummary.critical_count ?? 0) },
      { label: 'Colapsado', value: Number(pickupSummary.collapsed_count ?? 0) },
    ]
  }, [pickupSummary])

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Ciclo de vida — Saúde</h1>
        <p className="text-sm text-gray-500 dark:text-slate-400">HealthResponse + pickup-health (resumo)</p>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <span
            className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"
            aria-hidden
          />
          Carregando…
        </div>
      )}

      {error && !loading && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-200">
          {error}
        </div>
      )}

      {!loading && health && (
        <div className="overflow-hidden rounded-xl border border-gray-200 dark:border-slate-700">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-4 py-2">Campo</th>
                <th className="px-4 py-2">Valor</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
              <tr className="dark:text-slate-200">
                <td className="px-4 py-2 font-medium">status</td>
                <td className="px-4 py-2">{health.status}</td>
              </tr>
              <tr className="dark:text-slate-200">
                <td className="px-4 py-2 font-medium">database</td>
                <td className="px-4 py-2">{health.database}</td>
              </tr>
            </tbody>
          </table>
        </div>
      )}

      {pickupErr && !loading && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
          Pickup health: {pickupErr}
        </div>
      )}

      {!pickupErr && pickupSummary && summaryChart.some((x) => x.value > 0) && (
        <MetricsChart title="Entidades por classificação (summary)" type="bar" data={summaryChart} xKey="label" yKey="value" color="#F59E0B" />
      )}

      {!pickupErr && pickupRows.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-slate-700">
          <table className="w-full min-w-[720px] text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
              <tr>
                <th className="px-3 py-2">Entidade</th>
                <th className="px-3 py-2">Health</th>
                <th className="px-3 py-2">Classificação</th>
                <th className="px-3 py-2">Ação</th>
                <th className="px-3 py-2">Pickups term.</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
              {pickupRows.slice(0, 25).map((row, idx) => {
                const id = String(row.entity_id ?? row.locker_id ?? row.machine_id ?? row.site_id ?? row.region ?? idx)
                const score = typeof row.health_score === 'number' ? row.health_score.toFixed(1) : '—'
                const cls = typeof row.classification === 'string' ? row.classification : '—'
                const action = typeof row.recommended_action === 'string' ? row.recommended_action : '—'
                const metrics = row.metrics as Record<string, unknown> | undefined
                const total =
                  metrics && typeof metrics.total_terminal_pickups === 'number' ? metrics.total_terminal_pickups : '—'
                return (
                  <tr key={`${id}-${idx}`} className="dark:text-slate-200">
                    <td className="px-3 py-2">{id}</td>
                    <td className="px-3 py-2">{score}</td>
                    <td className="px-3 py-2">{cls}</td>
                    <td className="px-3 py-2 max-w-xs truncate" title={action}>
                      {action}
                    </td>
                    <td className="px-3 py-2">{String(total)}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {!loading && !pickupErr && pickupRows.length === 0 && health && (
        <p className="text-sm text-slate-500">Sem linhas em pickup-health (ou resposta vazia).</p>
      )}

      <button
        type="button"
        onClick={() => void load()}
        className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
      >
        Recarregar
      </button>
    </div>
  )
}

export default function Health() {
  return (
    <LifecycleErrorBoundary>
      <HealthBody />
    </LifecycleErrorBoundary>
  )
}
