import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchOpsMonitoringSummary, type OpsMonitoringSummary } from '../../api/opsMonitoring'
import { useAuth } from '../../contexts/AuthContext'

function fmtAge(sec: unknown) {
  const n = Number(sec || 0)
  if (n < 60) return `${n}s`
  if (n < 3600) return `${Math.round(n / 60)}min`
  return `${(n / 3600).toFixed(1)}h`
}

export default function OpsMonitoringDashboard() {
  const { token } = useAuth()
  const [summary, setSummary] = useState<OpsMonitoringSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setSummary(await fetchOpsMonitoringSummary(token))
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar monitoramento OPS.')
      setSummary(null)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => {
    void load()
  }, [load])

  const credits = (summary?.credits_health || {}) as Record<string, unknown>
  const recon = (summary?.reconciliation_lag || {}) as Record<string, unknown>
  const runtime = (summary?.runtime_deadlocks || {}) as Record<string, unknown>

  const statusDistribution = useMemo(() => {
    const dist = (recon.status_distribution || {}) as Record<string, number>
    return Object.entries(dist).sort((a, b) => b[1] - a[1])
  }, [recon.status_distribution])

  return (
    <div className="p-6 text-slate-100" data-testid="ops-monitoring-dashboard">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Monitoramento OPS</h1>
          <p className="text-sm text-slate-400">
            Créditos · reconciliação · alocações presas (order_pickup_service)
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="ellan-btn" onClick={() => void load()} disabled={loading}>
            {loading ? 'Atualizando…' : 'Atualizar'}
          </button>
          <Link className="ellan-btn-secondary" to="/ops/orders/admin?tab=reconciliation">
            Reconciliação
          </Link>
          <Link className="ellan-btn-secondary" to="/runtime/slots">
            Runtime slots
          </Link>
        </div>
      </div>

      {error ? (
        <div className="mb-4 rounded-lg border border-red-500/50 bg-red-950/40 p-4 text-red-200">{error}</div>
      ) : null}

      {summary ? (
        <>
          <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className={`rounded-xl border p-4 ${summary.ok ? 'border-slate-700 bg-slate-900' : 'border-red-500/60 bg-red-950/30'}`}>
              <div className="text-xs uppercase text-slate-400">Status geral</div>
              <div className="text-2xl font-bold">{summary.ok ? 'OK' : 'ALERTA'}</div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <div className="text-xs uppercase text-slate-400">Créditos</div>
              <div className="text-2xl font-bold">{String(credits.total_credits ?? '—')}</div>
              <div className="text-xs text-slate-400">USED hoje: {String(credits.used_today ?? 0)}</div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <div className="text-xs uppercase text-slate-400">Reconciliação aberta</div>
              <div className="text-2xl font-bold">{String(recon.open_pending_count ?? 0)}</div>
              <div className="text-xs text-slate-400">máx {fmtAge(recon.max_pending_age_sec)}</div>
            </div>
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <div className="text-xs uppercase text-slate-400">Alocações presas</div>
              <div className="text-2xl font-bold">{String(runtime.stuck_count ?? 0)}</div>
            </div>
          </div>

          {summary.alerts?.length ? (
            <div className="mb-4 rounded-xl border border-amber-500/40 bg-amber-950/20 p-4">
              <h2 className="mb-2 font-semibold">Alertas</h2>
              <ul className="list-disc pl-5 text-sm">
                {summary.alerts.map((a) => (
                  <li key={a.code}>
                    <strong>{a.severity}</strong> — {a.message}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <div className="grid gap-4 lg:grid-cols-3">
            <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <h2 className="mb-2 font-semibold">Créditos</h2>
              <p className="text-sm text-slate-400">Expirados hoje: {String(credits.expired_today ?? 0)}</p>
            </section>
            <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <h2 className="mb-2 font-semibold">Reconciliação</h2>
              {statusDistribution.map(([status, count]) => (
                <div key={status} className="flex justify-between text-sm">
                  <span>{status}</span>
                  <span>{count}</span>
                </div>
              ))}
            </section>
            <section className="rounded-xl border border-slate-700 bg-slate-900 p-4">
              <h2 className="mb-2 font-semibold">Runtime</h2>
              <p className="text-sm text-slate-400">Alocações ativas sem progresso &gt; 1h.</p>
            </section>
          </div>
        </>
      ) : null}
    </div>
  )
}
