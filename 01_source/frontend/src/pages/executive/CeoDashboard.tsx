import { useCallback, useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  executiveApi,
  type ExecutiveExpansion,
  type ExecutiveForecast,
  type ExecutiveGlobalKpis,
  type ExecutiveMrr,
  type ExecutivePartners,
} from '../../api/executive'

function Card({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">{title}</h2>
      {subtitle && <p className="text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

export default function CeoDashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [kpis, setKpis] = useState<ExecutiveGlobalKpis | null>(null)
  const [mrr, setMrr] = useState<ExecutiveMrr | null>(null)
  const [forecast, setForecast] = useState<ExecutiveForecast | null>(null)
  const [expansion, setExpansion] = useState<ExecutiveExpansion | null>(null)
  const [partners, setPartners] = useState<ExecutivePartners | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [k, m, f, e, p] = await Promise.all([
        executiveApi.getGlobalKpis(),
        executiveApi.getMrr(),
        executiveApi.getForecast(),
        executiveApi.getExpansion(),
        executiveApi.getTopPartners(10),
      ])
      setKpis(k.data)
      setMrr(m.data)
      setForecast(f.data)
      setExpansion(e.data)
      setPartners(p.data)
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : typeof detail === 'object' && detail !== null && 'message' in detail
            ? String((detail as { message?: string }).message)
            : err instanceof Error
              ? err.message
              : 'Falha ao carregar dashboard executivo.'
      setError(msg)
      setKpis(null)
      setMrr(null)
      setForecast(null)
      setExpansion(null)
      setPartners(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const forecastSeries =
    forecast != null
      ? [
          ...forecast.historical.map((h) => ({
            month: h.month,
            historical: h.revenue,
            projected: null as number | null,
          })),
          ...forecast.forecast.map((x) => ({
            month: x.month,
            historical: null as number | null,
            projected: x.forecast_revenue,
          })),
        ]
      : []

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-400">
            Portal 5180 · CEO
          </p>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-slate-50">
            Visão 360° estratégica
          </h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            KPIs globais, finanças, expansão e parceiros · dados consolidados do order pickup
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {loading ? 'Atualizando…' : 'Atualizar'}
        </button>
      </header>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200">
          {error}
        </div>
      )}

      {kpis && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          <div className="rounded-xl border border-slate-200 bg-gradient-to-br from-indigo-600 to-violet-700 p-4 text-white shadow">
            <p className="text-xs uppercase opacity-90">Receita MTD</p>
            <p className="mt-1 text-xl font-semibold">{kpis.total_revenue_mtd_formatted}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs uppercase text-slate-500">Ocupação rede</p>
            <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{kpis.occupancy_rate}%</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs uppercase text-slate-500">NPS</p>
            <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{kpis.nps}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs uppercase text-slate-500">Incidentes críticos</p>
            <p className="mt-1 text-xl font-semibold text-amber-700 dark:text-amber-400">{kpis.critical_incidents}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs uppercase text-slate-500">Lockers expansão</p>
            <p className="mt-1 text-xl font-semibold text-slate-900 dark:text-slate-100">{kpis.expanding_lockers}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <p className="text-xs uppercase text-slate-500">Referência</p>
            <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">{kpis.as_of}</p>
          </div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="MRR por região" subtitle={mrr?.total_mrr_formatted}>
          {mrr && mrr.by_region.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mrr.by_region} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                  <XAxis dataKey="region" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v: number) => [`R$ ${v.toFixed(2)}`, 'MRR']} />
                  <Bar dataKey="mrr" fill="#6366f1" name="MRR (R$)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Sem dados de MRR no período.</p>
          )}
        </Card>

        <Card title="Forecast de receita" subtitle="Histórico mensal + projeção linear (5% a.m.)">
          {forecastSeries.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={forecastSeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="historical" stroke="#22c55e" dot={false} strokeWidth={2} />
                  <Line type="monotone" dataKey="projected" stroke="#a855f7" strokeDasharray="4 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Sem série histórica suficiente.</p>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Expansão de rede" subtitle="Pipeline e ROI por local (meta opcional em locker)">
          {expansion ? (
            <div className="space-y-3 text-sm">
              <div className="flex gap-6">
                <div>
                  <p className="text-xs uppercase text-slate-500">Pipeline</p>
                  <p className="text-lg font-semibold">{expansion.pipeline_count}</p>
                </div>
                <div>
                  <p className="text-xs uppercase text-slate-500">Em análise</p>
                  <p className="text-lg font-semibold">{expansion.pending_approvals}</p>
                </div>
              </div>
              {expansion.roi_by_location.length === 0 ? (
                <p className="text-slate-500">Sem ROI calculável (custo de instalação em metadata).</p>
              ) : (
                <ul className="max-h-56 space-y-2 overflow-auto">
                  {expansion.roi_by_location.map((row, i) => (
                    <li
                      key={`${row.city}-${row.region}-${i}`}
                      className="flex justify-between rounded-md bg-slate-50 px-3 py-2 dark:bg-slate-800"
                    >
                      <span>
                        {row.city || '—'} · {row.region}
                      </span>
                      <span className="font-medium text-indigo-600 dark:text-indigo-400">{row.roi_percent}% ROI</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-500">—</p>
          )}
        </Card>

        <Card title="Parceiros" subtitle="Liquidações pagas no mês + saúde">
          {partners ? (
            <div className="space-y-4 text-sm">
              <div className="flex gap-6">
                <div>
                  <p className="text-xs uppercase text-slate-500">Churn</p>
                  <p className="text-lg font-semibold">{partners.partner_churn_rate}%</p>
                </div>
                <div>
                  <p className="text-xs uppercase text-slate-500">SLA médio</p>
                  <p className="text-lg font-semibold">{partners.sla_compliance}%</p>
                </div>
              </div>
              {partners.top_partners.length === 0 ? (
                <p className="text-slate-500">Nenhuma liquidação paga no mês.</p>
              ) : (
                <ul className="space-y-2">
                  {partners.top_partners.map((tp) => (
                    <li
                      key={tp.name}
                      className="flex justify-between rounded-md border border-slate-100 px-3 py-2 dark:border-slate-800"
                    >
                      <span>{tp.name}</span>
                      <span>R$ {tp.total_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : (
            <p className="text-sm text-slate-500">—</p>
          )}
        </Card>
      </div>
    </div>
  )
}
