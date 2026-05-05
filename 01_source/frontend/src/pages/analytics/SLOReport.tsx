import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { analyticsApi, type Period } from '../../api/analytics'
import MetricsChart from '../../components/MetricsChart'

function asSeries(input: unknown): Array<{ date: string; value: number }> {
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

export default function SLOReport() {
  const [period, setPeriod] = useState<Period>('30d')
  const [partnerId, setPartnerId] = useState('')
  const [lockerId, setLockerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [errorRate, setErrorRate] = useState<Array<{ date: string; value: number }>>([])
  const [latency, setLatency] = useState<Array<{ date: string; value: number }>>([])
  const [divergence, setDivergence] = useState<Array<{ date: string; value: number }>>([])

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const params = { period, partner_id: partnerId || undefined, locker_id: lockerId || undefined }
      const [e, l, d] = await Promise.all([
        analyticsApi.getErrorRate(params),
        analyticsApi.getLatencyP95(params),
        analyticsApi.getDivergence(params),
      ])
      setErrorRate(asSeries(e.data))
      setLatency(asSeries(l.data))
      setDivergence(asSeries(d.data))
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar relatório')
    } finally {
      setLoading(false)
    }
  }

  const reportText = useMemo(() => {
    const er = Number(errorRate.at(-1)?.value ?? 0)
    const lp = Number(latency.at(-1)?.value ?? 0)
    const dv = Number(divergence.at(-1)?.value ?? 0)
    const errorPct = er > 1 ? er : er * 100
    const divPct = dv > 1 ? dv : dv * 100
    return [
      'ELLAN LAB - Relatorio SLO',
      `Periodo: ${period}`,
      `Parceiro: ${partnerId || 'todos'}`,
      `Locker: ${lockerId || 'todos'}`,
      '',
      `Error rate: ${errorPct.toFixed(4)}% (meta < 0.1%)`,
      `Latency p95: ${lp.toFixed(2)}ms (meta < baseline+10ms)`,
      `Divergence: ${divPct.toFixed(4)}% (meta < 0.01%)`,
    ].join('\n')
  }, [divergence, errorRate, latency, lockerId, partnerId, period])

  function exportPdf(mode: 'weekly' | 'monthly') {
    const content = `${reportText}\n\nTipo: ${mode.toUpperCase()}`
    const blob = new Blob([content], { type: 'application/pdf' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ellan-slo-${mode}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">SLO Report</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">Histórico de tendência últimos 30 dias</p>
        </div>
        <Link to="/analytics/dashboard" className="rounded bg-indigo-500 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-600">
          Voltar dashboard
        </Link>
      </div>

      <div className="grid gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-5">
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Período
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          >
            <option value="7d">7 dias</option>
            <option value="30d">30 dias</option>
            <option value="90d">90 dias</option>
          </select>
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Parceiro
          <input
            value={partnerId}
            onChange={(e) => setPartnerId(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <label className="text-xs text-gray-600 dark:text-slate-400">
          Locker
          <input
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 bg-white px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="self-end rounded bg-emerald-500 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-600"
        >
          Atualizar
        </button>
        <div className="self-end space-x-2">
          <button
            type="button"
            onClick={() => exportPdf('weekly')}
            className="rounded bg-indigo-500 px-3 py-2 text-xs font-medium text-white hover:bg-indigo-600"
          >
            Exportar PDF semanal
          </button>
          <button
            type="button"
            onClick={() => exportPdf('monthly')}
            className="rounded bg-indigo-700 px-3 py-2 text-xs font-medium text-white hover:bg-indigo-800"
          >
            Exportar PDF mensal
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500 dark:text-slate-400">Gerando relatório...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}

      <div className="grid gap-4 xl:grid-cols-3">
        <MetricsChart title="Error Rate (30d)" type="line" data={errorRate} xKey="date" yKey="value" color="#EF4444" />
        <MetricsChart title="Latency p95 (30d)" type="line" data={latency} xKey="date" yKey="value" color="#F59E0B" />
        <MetricsChart title="Divergence (30d)" type="line" data={divergence} xKey="date" yKey="value" color="#6366F1" />
      </div>
    </div>
  )
}

