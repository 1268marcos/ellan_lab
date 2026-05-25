import { useCallback, useEffect, useMemo, useState } from 'react'
import RevenueChart from '../../components/financial/RevenueChart'
import ROICards from '../../components/financial/ROICards'
import {
  financialExecutiveApi,
  type FinancialKpis,
  type LockerRoiRow,
  type RevenueTrendPoint,
} from '../../api/financialExecutive'
import { loadAuth } from '../../api/auth'

const REFRESH_MS = 5 * 60 * 1000

function brl(value?: number | null) {
  if (value == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value))
}

function pct(value?: number | null) {
  if (value == null) return '—'
  return `${Number(value).toFixed(1)}%`
}

export default function ExecutiveDashboard() {
  const [kpis, setKpis] = useState<FinancialKpis | null>(null)
  const [trend, setTrend] = useState<RevenueTrendPoint[]>([])
  const [roi, setRoi] = useState<LockerRoiRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const [k, t, r] = await Promise.all([
        financialExecutiveApi.kpis(),
        financialExecutiveApi.revenueTrend(12),
        financialExecutiveApi.lockerRoi({ viability: 'HIGH_PERFORMANCE' }),
      ])
      setKpis(k.data)
      setTrend(t.data.items ?? [])
      setRoi(r.data.items ?? [])
    } catch (err) {
      const ax = err as { response?: { status?: number; data?: { detail?: string; error?: string } } }
      const detail = ax.response?.data?.detail || ax.response?.data?.error
      const status = ax.response?.status
      setError(
        detail
          ? `${detail}${status ? ` (HTTP ${status})` : ''}`
          : err instanceof Error
            ? err.message
            : 'Falha ao carregar KPIs',
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const id = window.setInterval(() => void load(), REFRESH_MS)
    return () => window.clearInterval(id)
  }, [load])

  const cards = useMemo(
    () => [
      { label: 'Receita MTD', value: brl(kpis?.revenue_mtd_brl) },
      { label: 'Lucro MTD', value: brl(kpis?.profit_mtd_brl) },
      { label: 'Margem MTD', value: pct(kpis?.margin_mtd_pct) },
      { label: 'Receita LTM', value: brl(kpis?.revenue_ltm_brl) },
      { label: 'Lockers ativos', value: String(kpis?.total_active_lockers ?? '—') },
      { label: 'Underperforming', value: pct(kpis?.pct_underperforming) },
    ],
    [kpis],
  )

  function exportFile(format: 'csv' | 'pdf') {
    const auth = loadAuth()
    const url = financialExecutiveApi.exportUrl(format, 'kpis')
    const headers: Record<string, string> = {}
    if (auth?.apiKey) {
      headers['X-API-Key'] = auth.apiKey
      headers.Authorization = `Bearer ${auth.token || auth.apiKey}`
    }
    fetch(url, { headers })
      .then((res) => res.blob())
      .then((blob) => {
        const a = document.createElement('a')
        a.href = URL.createObjectURL(blob)
        a.download = `financial-kpis.${format}`
        a.click()
        URL.revokeObjectURL(a.href)
      })
      .catch(() => setError('Falha na exportação'))
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-slate-400">
          Atualização automática a cada 5 min · cache Redis · views pg_cron
        </p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => exportFile('csv')}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Export CSV
          </button>
          <button
            type="button"
            onClick={() => exportFile('pdf')}
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Export PDF
          </button>
        </div>
      </div>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {cards.map((c) => (
          <div key={c.label} className="rounded-xl border border-slate-600/60 bg-slate-950/80 p-4">
            <p className="text-xs font-medium text-slate-400">{c.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-50">{loading ? '…' : c.value}</p>
          </div>
        ))}
      </section>

      <RevenueChart data={trend} />
      <section>
        <h2 className="mb-3 text-lg font-semibold text-slate-100">Top ROI — alta performance</h2>
        <ROICards items={roi} limit={6} />
      </section>
    </div>
  )
}
