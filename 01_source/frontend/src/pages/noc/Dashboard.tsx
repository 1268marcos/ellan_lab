import { useCallback, useEffect, useMemo, useState } from 'react'

const runtimeBaseUrl = import.meta.env.VITE_RUNTIME_BASE_URL ?? 'http://localhost:8200'
const lifecycleBaseUrl = import.meta.env.VITE_ORDER_LIFECYCLE_BASE_URL ?? 'http://localhost:8010'
const POLL_INTERVAL_SECONDS = 30

type RuntimeSummary = {
  status?: string
  mode?: string
  lockers?: {
    total: number
    operational: number
    degraded: number
    offline: number
  }
  incidents?: {
    open: number
    acknowledged: number
    critical: number
  }
  generated_at?: string
}

type LifecycleDashboard = {
  lockers_total?: number
  lockers_online?: number
  incidents_active?: number
  last_updated?: string
}

type Snapshot = {
  at: string
  lockersTotal: number
  lockersOnline: number
  incidentsOpen: number
  health: HealthState
}

type HealthState = 'operational' | 'degraded' | 'critical' | 'unknown'

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function NOCDashboard() {
  const [runtimeSummary, setRuntimeSummary] = useState<RuntimeSummary | null>(null)
  const [lifecycleDashboard, setLifecycleDashboard] = useState<LifecycleDashboard | null>(null)
  const [ackResult, setAckResult] = useState<unknown>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)
  const [pollingEnabled, setPollingEnabled] = useState(true)
  const [secondsUntilRefresh, setSecondsUntilRefresh] = useState(POLL_INTERVAL_SECONDS)
  const [history, setHistory] = useState<Snapshot[]>([])

  const load = useCallback(async (options?: { silent?: boolean }) => {
    if (!options?.silent) {
      setLoading(true)
    }
    setError(null)
    try {
      const [runtimePayload, lifecyclePayload] = await Promise.all([
        fetchJson<RuntimeSummary>(`${runtimeBaseUrl}/api/v1/noc/simt/summary`),
        fetchJson<LifecycleDashboard>(`${lifecycleBaseUrl}/api/v1/noc/dashboard`),
      ])
      setRuntimeSummary(runtimePayload)
      setLifecycleDashboard(lifecyclePayload)
      const now = new Date().toISOString()
      setLastUpdatedAt(now)
      setSecondsUntilRefresh(POLL_INTERVAL_SECONDS)
      setHistory((current) => {
        const snapshot = buildSnapshot(runtimePayload, lifecyclePayload, now)
        return [snapshot, ...current].slice(0, 6)
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar NOC.')
      setRuntimeSummary(null)
      setLifecycleDashboard(null)
    } finally {
      setLoading(false)
    }
  }, [])

  const acknowledgeIncident = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${runtimeBaseUrl}/api/v1/noc/incidents/ack`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: 'INC-MVP-001',
          acknowledged_by: 'noc_operator',
        }),
      })
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      setAckResult(await response.json())
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao reconhecer incidente.')
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!pollingEnabled) {
      return undefined
    }
    const refreshTimer = window.setInterval(() => {
      void load({ silent: true })
    }, POLL_INTERVAL_SECONDS * 1000)
    const countdownTimer = window.setInterval(() => {
      setSecondsUntilRefresh((current) => (current <= 1 ? POLL_INTERVAL_SECONDS : current - 1))
    }, 1000)
    return () => {
      window.clearInterval(refreshTimer)
      window.clearInterval(countdownTimer)
    }
  }, [load, pollingEnabled])

  const lockersTotal = runtimeSummary?.lockers?.total ?? lifecycleDashboard?.lockers_total ?? 0
  const lockersOnline = runtimeSummary?.lockers?.operational ?? lifecycleDashboard?.lockers_online ?? 0
  const incidentsOpen = runtimeSummary?.incidents?.open ?? lifecycleDashboard?.incidents_active ?? 0
  const healthState = useMemo(
    () => deriveHealthState(runtimeSummary, lifecycleDashboard),
    [runtimeSummary, lifecycleDashboard],
  )

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-300">
            Sprint 2 MVP
          </p>
          <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">NOC / SIMT Dashboard</h1>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Painel polling-based com resumo do runtime e lifecycle para operação 24/7.
          </p>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span className={healthBadgeClass(healthState)}>Saúde: {healthLabel(healthState)}</span>
            <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-700">
              Polling: {pollingEnabled ? `ativo (${secondsUntilRefresh}s)` : 'pausado'}
            </span>
            <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-700">
              Última atualização: {lastUpdatedAt ? new Date(lastUpdatedAt).toLocaleTimeString() : '—'}
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {loading ? 'Atualizando...' : 'Atualizar'}
          </button>
          <button
            type="button"
            onClick={() => setPollingEnabled((current) => !current)}
            className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {pollingEnabled ? 'Pausar polling' : 'Retomar polling'}
          </button>
          <button
            type="button"
            onClick={() => void acknowledgeIncident()}
            disabled={loading}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            Ack incidente demo
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard label="Lockers total" value={lockersTotal} />
        <MetricCard label="Lockers online" value={lockersOnline} />
        <MetricCard label="Incidentes abertos" value={incidentsOpen} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">Histórico de polling</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500 dark:text-slate-400">
              <tr>
                <th className="px-2 py-2">Hora</th>
                <th className="px-2 py-2">Saúde</th>
                <th className="px-2 py-2">Online</th>
                <th className="px-2 py-2">Total</th>
                <th className="px-2 py-2">Incidentes</th>
              </tr>
            </thead>
            <tbody>
              {history.map((item) => (
                <tr key={item.at} className="border-t border-slate-100 dark:border-slate-800">
                  <td className="px-2 py-2 font-mono text-xs">{new Date(item.at).toLocaleTimeString()}</td>
                  <td className="px-2 py-2">{healthLabel(item.health)}</td>
                  <td className="px-2 py-2">{item.lockersOnline}</td>
                  <td className="px-2 py-2">{item.lockersTotal}</td>
                  <td className="px-2 py-2">{item.incidentsOpen}</td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr>
                  <td className="px-2 py-4 text-slate-500 dark:text-slate-400" colSpan={5}>
                    Sem snapshots ainda.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <PayloadCard title="Runtime SIMT" payload={runtimeSummary} />
        <PayloadCard title="Lifecycle Dashboard" payload={lifecycleDashboard} />
        <PayloadCard title="Ack Result" payload={ackResult} />
      </div>
    </div>
  )
}

export default NOCDashboard

function buildSnapshot(
  runtimeSummary: RuntimeSummary,
  lifecycleDashboard: LifecycleDashboard,
  at: string,
): Snapshot {
  const lockersTotal = runtimeSummary.lockers?.total ?? lifecycleDashboard.lockers_total ?? 0
  const lockersOnline = runtimeSummary.lockers?.operational ?? lifecycleDashboard.lockers_online ?? 0
  const incidentsOpen = runtimeSummary.incidents?.open ?? lifecycleDashboard.incidents_active ?? 0
  return {
    at,
    lockersTotal,
    lockersOnline,
    incidentsOpen,
    health: deriveHealthState(runtimeSummary, lifecycleDashboard),
  }
}

function deriveHealthState(
  runtimeSummary: RuntimeSummary | null,
  lifecycleDashboard: LifecycleDashboard | null,
): HealthState {
  if (!runtimeSummary && !lifecycleDashboard) {
    return 'unknown'
  }
  const critical = runtimeSummary?.incidents?.critical ?? 0
  const offline = runtimeSummary?.lockers?.offline ?? 0
  const activeIncidents = runtimeSummary?.incidents?.open ?? lifecycleDashboard?.incidents_active ?? 0
  if (critical > 0 || offline > 0) {
    return 'critical'
  }
  if (activeIncidents > 0 || (runtimeSummary?.lockers?.degraded ?? 0) > 0) {
    return 'degraded'
  }
  return 'operational'
}

function healthLabel(state: HealthState): string {
  const labels: Record<HealthState, string> = {
    operational: 'Operacional',
    degraded: 'Degradado',
    critical: 'Crítico',
    unknown: 'Desconhecido',
  }
  return labels[state]
}

function healthBadgeClass(state: HealthState): string {
  const base = 'rounded-full px-3 py-1 font-medium'
  if (state === 'operational') {
    return `${base} bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200`
  }
  if (state === 'degraded') {
    return `${base} bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-200`
  }
  if (state === 'critical') {
    return `${base} bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-200`
  }
  return `${base} bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200`
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-slate-50">{value}</p>
    </div>
  )
}

function PayloadCard({ title, payload }: { title: string; payload: unknown }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{title}</h2>
      <pre className="mt-3 max-h-80 overflow-auto rounded bg-slate-50 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-200">
        {payload ? JSON.stringify(payload, null, 2) : 'Sem dados ainda.'}
      </pre>
    </div>
  )
}
