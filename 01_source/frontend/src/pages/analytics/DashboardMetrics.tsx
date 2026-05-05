import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import MetricsChart from '../../components/MetricsChart'
import { analyticsApi, type Period, type QueryFilter } from '../../api/analytics'

type SLOCard = {
  label: string
  value: number
  unit: string
  ok: boolean
  meta: string
}

function normalizeSeries(input: unknown): Array<{ date: string; value: number }> {
  if (Array.isArray(input)) {
    return input.map((p, i) => ({
      date: String((p as { date?: string }).date ?? i + 1),
      value: Number((p as { value?: number; percent?: number; rate?: number }).value ?? (p as { percent?: number }).percent ?? (p as { rate?: number }).rate ?? 0),
    }))
  }
  if (input && typeof input === 'object' && Array.isArray((input as { history?: unknown[] }).history)) {
    return ((input as { history: unknown[] }).history ?? []).map((p, i) => ({
      date: String((p as { date?: string }).date ?? i + 1),
      value: Number((p as { value?: number; percent?: number; rate?: number }).value ?? (p as { percent?: number }).percent ?? (p as { rate?: number }).rate ?? 0),
    }))
  }
  return []
}

export default function DashboardMetrics() {
  const [period, setPeriod] = useState<Period>('30d')
  const [partnerId, setPartnerId] = useState('')
  const [lockerId, setLockerId] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [errorRate, setErrorRate] = useState<Array<{ date: string; value: number }>>([])
  const [latency, setLatency] = useState<Array<{ date: string; value: number }>>([])
  const [divergence, setDivergence] = useState<Array<{ date: string; value: number }>>([])
  const [pickupsByHour, setPickupsByHour] = useState<Array<{ hour: string; pickups: number }>>([])
  const [turnover, setTurnover] = useState<Array<{ locker_id: string; turnover: number }>>([])
  const [slaCompliance, setSlaCompliance] = useState<Array<{ partner_id: string; compliance: number }>>([])

  async function load() {
    setLoading(true)
    setError(null)
    const params: QueryFilter = {
      period,
      partner_id: partnerId || undefined,
      locker_id: lockerId || undefined,
    }
    try {
      const [e, l, d, p, t, s] = await Promise.all([
        analyticsApi.getErrorRate(params),
        analyticsApi.getLatencyP95(params),
        analyticsApi.getDivergence(params),
        analyticsApi.getPickupsByHour(params),
        analyticsApi.getInventoryTurnover(params),
        analyticsApi.getLogisticsSlaCompliance(params),
      ])
      setErrorRate(normalizeSeries(e.data))
      setLatency(normalizeSeries(l.data))
      setDivergence(normalizeSeries(d.data))
      setPickupsByHour((Array.isArray(p.data) ? p.data : []).map((x) => ({ hour: String((x as { hour: string | number }).hour), pickups: Number((x as { pickups: number }).pickups ?? 0) })))
      setTurnover((Array.isArray(t.data) ? t.data : []).map((x) => ({ locker_id: String((x as { locker_id: string }).locker_id), turnover: Number((x as { turnover: number }).turnover ?? 0) })))
      setSlaCompliance((Array.isArray(s.data) ? s.data : []).map((x) => ({ partner_id: String((x as { partner_id: string }).partner_id), compliance: Number((x as { compliance: number }).compliance ?? 0) })))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [period])

  const cards = useMemo<SLOCard[]>(() => {
    const er = Number(errorRate.at(-1)?.value ?? 0)
    const lp = Number(latency.at(-1)?.value ?? 0)
    const dv = Number(divergence.at(-1)?.value ?? 0)
    const errorPct = er > 1 ? er : er * 100
    const divPct = dv > 1 ? dv : dv * 100
    return [
      { label: 'Error Rate', value: errorPct, unit: '%', ok: errorPct < 0.1, meta: 'meta < 0.1%' },
      { label: 'Latency p95', value: lp, unit: 'ms', ok: lp < 155, meta: 'meta < baseline+10ms' },
      { label: 'Divergence', value: divPct, unit: '%', ok: divPct < 0.01, meta: 'meta < 0.01%' },
    ]
  }, [divergence, errorRate, latency])

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Analytics Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">SLOs + métricas operacionais</p>
        </div>
        <Link to="/analytics/slo-report" className="rounded bg-indigo-500 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-600">
          Relatório SLO
        </Link>
      </div>

      <div className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-4">
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Período
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          >
            <option value="7d">Últimos 7 dias</option>
            <option value="30d">Últimos 30 dias</option>
            <option value="90d">Últimos 90 dias</option>
          </select>
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Parceiro
          <input
            value={partnerId}
            onChange={(e) => setPartnerId(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            placeholder="partner_id"
          />
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Locker
          <input
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            placeholder="locker_id"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="self-end rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
        >
          Filtrar
        </button>
      </div>

      {loading && <p className="text-sm text-gray-500 dark:text-slate-400">Carregando métricas...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="grid gap-4 md:grid-cols-3">
        {cards.map((card) => (
          <div key={card.label} className={`rounded-xl border p-4 ${card.ok ? 'border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/20' : 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20'}`}>
            <p className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-slate-400">{card.label}</p>
            <p className={`mt-2 text-2xl font-bold ${card.ok ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              {card.value.toFixed(3)}
              {card.unit}
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-slate-400">{card.meta}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <MetricsChart title="Error Rate" type="line" data={errorRate} xKey="date" yKey="value" color="#EF4444" />
        <MetricsChart title="Latency p95" type="line" data={latency} xKey="date" yKey="value" color="#F59E0B" />
        <MetricsChart title="Divergence" type="line" data={divergence} xKey="date" yKey="value" color="#6366F1" />
        <MetricsChart title="Pickups por hora" type="heatmap" data={pickupsByHour} xKey="hour" yKey="pickups" color="#10B981" />
        <MetricsChart title="Turnover por locker" type="bar" data={turnover} xKey="locker_id" yKey="turnover" color="#10B981" />
        <MetricsChart title="SLA compliance por parceiro" type="bar" data={slaCompliance} xKey="partner_id" yKey="compliance" color="#6366F1" />
      </div>
    </div>
  )
}

