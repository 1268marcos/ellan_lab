import { useCallback, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
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

const CEO_PRIMARY = '#1A365D'
const CEO_SECONDARY = '#2D3748'
const CEO_ACCENT = '#38A169'
const CEO_ALERT = '#E53E3E'
const CEO_GRID = '#E2E8F0'

const chartTooltip = {
  contentStyle: {
    background: '#FFFFFF',
    border: `1px solid ${CEO_GRID}`,
    borderRadius: 10,
    boxShadow: '0 4px 24px rgba(26, 54, 93, 0.08)',
    fontSize: 13,
    fontFamily: 'Inter, sans-serif',
    color: CEO_SECONDARY,
  },
  labelStyle: { color: CEO_PRIMARY, fontWeight: 600 },
}

function SkeletonBlock({ className }: { className: string }) {
  return (
    <div
      className={`rounded-xl bg-gradient-to-r from-[#EDF2F7] via-[#F7FAFC] to-[#EDF2F7] bg-[length:200%_100%] animate-ceo-shimmer ${className}`}
      aria-hidden
    />
  )
}

function DashboardSkeleton() {
  return (
    <div className="space-y-10">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonBlock key={i} className="h-[108px]" />
        ))}
      </div>
      <div className="grid gap-8 lg:grid-cols-2">
        <SkeletonBlock className="h-[320px]" />
        <SkeletonBlock className="h-[320px]" />
      </div>
      <div className="grid gap-8 lg:grid-cols-2">
        <SkeletonBlock className="h-[280px]" />
        <SkeletonBlock className="h-[280px]" />
      </div>
    </div>
  )
}

function Toast({ message, onDismiss }: { message: string; onDismiss: () => void }) {
  useEffect(() => {
    const t = window.setTimeout(onDismiss, 3200)
    return () => window.clearTimeout(t)
  }, [onDismiss])

  return (
    <div
      role="status"
      className="fixed bottom-8 right-8 z-[100] flex max-w-sm items-center gap-3 rounded-xl border border-[#E2E8F0] bg-white px-4 py-3 text-sm text-[#2D3748] shadow-ceo-card-hover animate-ceo-toast-in"
    >
      <span
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#38A169]/12 text-[#38A169]"
        aria-hidden
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="animate-ceo-check"
        >
          <path d="M20 6L9 17l-5-5" />
        </svg>
      </span>
      <p className="leading-snug">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="ml-1 rounded-md px-2 py-1 text-xs font-medium text-[#1A365D]/60 transition hover:bg-[#F7FAFC] hover:text-[#1A365D]"
      >
        OK
      </button>
    </div>
  )
}

function SectionCard({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="ceo-detail-card rounded-2xl border border-[#E2E8F0]/90 bg-white p-6 shadow-ceo-card transition-all duration-200 hover:shadow-ceo-card-hover hover:-translate-y-0.5">
      <h2 className="text-lg font-semibold leading-tight tracking-tight text-[#1A365D]">{title}</h2>
      {subtitle && (
        <p className="mt-1 text-base leading-relaxed text-[#2D3748]/75">{subtitle}</p>
      )}
      <div className="mt-5">{children}</div>
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
  const [toast, setToast] = useState<string | null>(null)
  const dismissToast = useCallback(() => setToast(null), [])

  const load = useCallback(async (opts?: { successToast?: boolean }) => {
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
      if (opts?.successToast) {
        setToast('Indicadores atualizados com sucesso.')
      }
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail
      const msg =
        typeof detail === 'string'
          ? detail
          : typeof detail === 'object' && detail !== null && 'message' in detail
            ? String((detail as { message?: string }).message)
            : err instanceof Error
              ? err.message
              : 'Falha ao carregar o painel executivo.'
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
    <div className="space-y-10 text-[#2D3748]">
      {toast && <Toast message={toast} onDismiss={dismissToast} />}

      <header className="flex flex-wrap items-end justify-between gap-6 border-b border-[#E2E8F0] pb-8">
        <div className="max-w-3xl space-y-2">
          <h1 className="text-[clamp(1.5rem,2.5vw,2rem)] font-semibold leading-tight tracking-tight text-[#1A365D]">
            Visão 360° estratégica
          </h1>
          <p className="max-w-2xl text-base leading-relaxed text-[#2D3748]/85">
            KPIs consolidados, tendência de receita e saúde da rede — dados orientados a decisão, sem ruído
            visual.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load({ successToast: true })}
          disabled={loading}
          className="shrink-0 rounded-xl bg-[#1A365D] px-5 py-2.5 text-sm font-semibold text-white shadow-ceo-card transition hover:bg-[#152a4a] hover:shadow-ceo-card-hover disabled:pointer-events-none disabled:opacity-50"
        >
          {loading ? 'Atualizando…' : 'Atualizar dados'}
        </button>
      </header>

      {loading && !kpis && <DashboardSkeleton />}

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-[#FED7D7] bg-[#FFF5F5] px-5 py-4 text-base leading-relaxed text-[#742A2A]"
          style={{ borderLeftWidth: 4, borderLeftColor: CEO_ALERT }}
        >
          {error}
        </div>
      )}

      {kpis && (
        <section aria-label="Indicadores principais" className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.12em] text-[#1A365D]/55">
            Indicadores principais
          </p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
            <div className="rounded-2xl bg-[#1A365D] p-5 text-white shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-white/70">Receita MTD</p>
              <p className="mt-2 font-mono text-lg font-semibold tracking-tight tabular-nums sm:text-xl">
                {kpis.total_revenue_mtd_formatted}
              </p>
            </div>

            <div className="rounded-2xl border border-[#E2E8F0]/90 bg-white p-5 shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">
                Ocupação da rede
              </p>
              <p className="mt-2 font-mono text-lg font-semibold tabular-nums text-[#1A365D] sm:text-xl">
                {kpis.occupancy_rate}%
              </p>
            </div>

            <div className="rounded-2xl border border-[#E2E8F0]/90 bg-white p-5 shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">NPS</p>
              <p className="mt-2 font-mono text-lg font-semibold tabular-nums text-[#38A169] sm:text-xl">{kpis.nps}</p>
            </div>

            <div className="rounded-2xl border border-[#E2E8F0]/90 bg-white p-5 shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">
                Incidentes críticos
              </p>
              <p
                className="mt-2 font-mono text-lg font-semibold tabular-nums sm:text-xl"
                style={{ color: kpis.critical_incidents > 0 ? CEO_ALERT : CEO_PRIMARY }}
              >
                {kpis.critical_incidents}
              </p>
            </div>

            <div className="rounded-2xl border border-[#E2E8F0]/90 bg-white p-5 shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">
                Lockers em expansão
              </p>
              <p className="mt-2 font-mono text-lg font-semibold tabular-nums text-[#1A365D] sm:text-xl">
                {kpis.expanding_lockers}
              </p>
            </div>

            <div className="rounded-2xl border border-[#E2E8F0]/90 bg-white p-5 shadow-ceo-card transition hover:shadow-ceo-card-hover hover:-translate-y-0.5">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">
                Snapshot
              </p>
              <p className="mt-2 font-mono text-xs leading-snug text-[#2D3748]/80">{kpis.as_of}</p>
            </div>
          </div>
        </section>
      )}

      {!loading || kpis ? (
        <div className="grid gap-8 lg:grid-cols-2">
          <SectionCard title="MRR por região" subtitle={mrr?.total_mrr_formatted}>
            {mrr && mrr.by_region.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={mrr.by_region} margin={{ top: 8, right: 8, left: 4, bottom: 4 }}>
                    <CartesianGrid stroke={CEO_GRID} strokeDasharray="4 4" vertical={false} />
                    <XAxis dataKey="region" tick={{ fill: CEO_SECONDARY, fontSize: 12 }} axisLine={{ stroke: CEO_GRID }} />
                    <YAxis tick={{ fill: CEO_SECONDARY, fontSize: 12 }} axisLine={{ stroke: CEO_GRID }} />
                    <Tooltip
                      {...chartTooltip}
                      formatter={(v: number) => [`R$ ${v.toFixed(2)}`, 'MRR']}
                    />
                    <Bar dataKey="mrr" fill={CEO_PRIMARY} name="MRR (R$)" radius={[6, 6, 0, 0]} maxBarSize={48} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-base leading-relaxed text-[#2D3748]/65">Sem dados de MRR no período.</p>
            )}
          </SectionCard>

          <SectionCard
            title="Forecast de receita"
            subtitle="Histórico mensal e tendência projetada (premissa +5% a.m.)"
          >
            {forecastSeries.length > 0 ? (
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={forecastSeries} margin={{ top: 8, right: 12, left: 4, bottom: 4 }}>
                    <CartesianGrid stroke={CEO_GRID} strokeDasharray="4 4" />
                    <XAxis dataKey="month" tick={{ fill: CEO_SECONDARY, fontSize: 11 }} axisLine={{ stroke: CEO_GRID }} />
                    <YAxis tick={{ fill: CEO_SECONDARY, fontSize: 11 }} axisLine={{ stroke: CEO_GRID }} />
                    <Tooltip {...chartTooltip} />
                    <Legend
                      wrapperStyle={{ fontFamily: 'Inter, sans-serif', fontSize: 13, color: CEO_SECONDARY }}
                    />
                    <Line
                      type="monotone"
                      dataKey="historical"
                      name="Realizado"
                      stroke={CEO_ACCENT}
                      strokeWidth={2.25}
                      dot={false}
                      activeDot={{ r: 4, fill: CEO_ACCENT }}
                    />
                    <Line
                      type="monotone"
                      dataKey="projected"
                      name="Projetado"
                      stroke={CEO_SECONDARY}
                      strokeWidth={2}
                      strokeDasharray="6 5"
                      dot={false}
                      opacity={0.85}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <p className="text-base leading-relaxed text-[#2D3748]/65">Série histórica insuficiente.</p>
            )}
          </SectionCard>
        </div>
      ) : null}

      {!loading || kpis ? (
        <div className="grid gap-8 lg:grid-cols-2">
          <SectionCard title="Expansão de rede" subtitle="Pipeline e retorno por local (custos via metadata do locker)">
            {expansion ? (
              <div className="space-y-5 text-base leading-relaxed">
                <div className="flex flex-wrap gap-10">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">Pipeline</p>
                    <p className="mt-1 font-mono text-xl font-semibold text-[#1A365D] tabular-nums">
                      {expansion.pipeline_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">Em análise</p>
                    <p className="mt-1 font-mono text-xl font-semibold text-[#1A365D] tabular-nums">
                      {expansion.pending_approvals}
                    </p>
                  </div>
                </div>
                {expansion.roi_by_location.length === 0 ? (
                  <p className="text-[#2D3748]/65">
                    Sem ROI calculável: informe `installation_cost` ou `installation_cost_cents` no metadata do locker.
                  </p>
                ) : (
                  <ul className="max-h-56 space-y-2 overflow-auto pr-1">
                    {expansion.roi_by_location.map((row, i) => (
                      <li
                        key={`${row.city}-${row.region}-${i}`}
                        className="flex items-center justify-between gap-3 rounded-xl border border-[#F7FAFC] bg-[#F7FAFC]/80 px-4 py-3 transition hover:border-[#E2E8F0] hover:shadow-sm"
                      >
                        <span className="text-[#2D3748]">
                          {row.city || '—'} · <span className="text-[#2D3748]/75">{row.region}</span>
                        </span>
                        <span className="font-mono text-sm font-semibold tabular-nums text-[#38A169]">
                          {row.roi_percent}% ROI
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-[#2D3748]/65">—</p>
            )}
          </SectionCard>

          <SectionCard title="Parceiros" subtitle="Liquidações pagas no mês e indicadores de relacionamento">
            {partners ? (
              <div className="space-y-5 text-base leading-relaxed">
                <div className="flex flex-wrap gap-10">
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">Churn</p>
                    <p className="mt-1 font-mono text-xl font-semibold tabular-nums text-[#1A365D]">
                      {partners.partner_churn_rate}%
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-wide text-[#2D3748]/55">
                      SLA médio
                    </p>
                    <p className="mt-1 font-mono text-xl font-semibold tabular-nums text-[#38A169]">
                      {partners.sla_compliance}%
                    </p>
                  </div>
                </div>
                {partners.top_partners.length === 0 ? (
                  <p className="text-[#2D3748]/65">Nenhuma liquidação marcada como paga no mês corrente.</p>
                ) : (
                  <ul className="space-y-2">
                    {partners.top_partners.map((tp) => (
                      <li
                        key={tp.name}
                        className="flex justify-between gap-3 rounded-xl border border-[#E2E8F0]/60 px-4 py-3 transition hover:bg-[#F7FAFC]"
                      >
                        <span className="font-medium text-[#2D3748]">{tp.name}</span>
                        <span className="font-mono text-sm tabular-nums text-[#1A365D]">
                          R$ {tp.total_revenue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-[#2D3748]/65">—</p>
            )}
          </SectionCard>
        </div>
      ) : null}
    </div>
  )
}
