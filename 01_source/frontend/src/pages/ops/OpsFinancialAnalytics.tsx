import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  financialAnalyticsApi,
  type FinancialDashboard,
  type LockerProfitabilityRow,
  type RealtimeKpis,
  type RefreshStatusRow,
} from '../../api/financialAnalytics'
import { useAuth } from '../../contexts/AuthContext'

const PAGE_VERSION = 'ops/analytics/financial v1.0'
const inp =
  'ellan-field w-full rounded-lg border border-slate-600/70 bg-slate-900/90 px-3 py-2 text-sm text-slate-100'

function brl(cents?: number | null) {
  if (cents == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(cents) / 100)
}

function brlFromReais(value?: number | null) {
  if (value == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value))
}

function pct(value?: number | null) {
  if (value == null) return '—'
  return `${Number(value).toFixed(1)}%`
}

export default function OpsFinancialAnalytics() {
  const { profile } = useAuth()
  const isAdmin = profile === 'admin' || profile === 'ops'

  const [lockerId, setLockerId] = useState('')
  const [month, setMonth] = useState('')
  const [profitability, setProfitability] = useState<LockerProfitabilityRow[]>([])
  const [dashboard, setDashboard] = useState<FinancialDashboard | null>(null)
  const [kpis, setKpis] = useState<RealtimeKpis | null>(null)
  const [refreshStatus, setRefreshStatus] = useState<RefreshStatusRow[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [p, d, k, s] = await Promise.all([
        financialAnalyticsApi.lockerProfitability({
          locker_id: lockerId || undefined,
          month: month || undefined,
        }),
        financialAnalyticsApi.financialDashboard(),
        financialAnalyticsApi.realtimeKpis(),
        financialAnalyticsApi.refreshStatus(),
      ])
      setProfitability(p.data.items ?? [])
      setDashboard(d.data ?? null)
      setKpis(k.data ?? null)
      setRefreshStatus(s.data.items ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar analytics financeiros')
    } finally {
      setLoading(false)
    }
  }, [lockerId, month])

  useEffect(() => {
    void load()
  }, [load])

  async function onFilter(e: FormEvent) {
    e.preventDefault()
    await load()
  }

  async function onManualRefresh() {
    if (!isAdmin) return
    setRefreshing(true)
    setMessage(null)
    setError(null)
    try {
      await financialAnalyticsApi.triggerRefresh('all')
      setMessage('Materialized views atualizadas com sucesso.')
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao disparar refresh manual')
    } finally {
      setRefreshing(false)
    }
  }

  const kpiCards = useMemo(
    () => [
      { label: 'Receita MTD', value: brlFromReais(dashboard?.revenue_mtd_brl), hint: 'Mês corrente' },
      { label: 'Lucro MTD', value: brlFromReais(dashboard?.profit_mtd_brl), hint: 'Margem consolidada' },
      { label: 'Margem MTD', value: pct(dashboard?.margin_mtd_pct), hint: 'Sobre receita do mês' },
      { label: 'Lockers ativos', value: String(dashboard?.total_active_lockers ?? '—'), hint: 'Rede operacional' },
      { label: 'Pedidos 24h', value: String(kpis?.orders_last_24h ?? '—'), hint: 'Tempo real' },
      { label: 'Receita 24h', value: brlFromReais(kpis?.revenue_last_24h), hint: 'Últimas 24 horas' },
    ],
    [dashboard, kpis],
  )

  return (
    <div className="space-y-6 p-4 md:p-6">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-500">{PAGE_VERSION}</p>
          <h1 className="text-2xl font-bold text-slate-50">Analytics financeiro</h1>
          <p className="mt-1 text-sm text-slate-400">
            Rentabilidade por locker, dashboard executivo e KPIs em tempo real.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/ops/finance/admin?tab=pnl"
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Finance PnL
          </Link>
          {isAdmin ? (
            <button
              type="button"
              onClick={() => void onManualRefresh()}
              disabled={refreshing}
              className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
            >
              {refreshing ? 'Atualizando…' : 'Refresh manual (admin)'}
            </button>
          ) : null}
        </div>
      </header>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      ) : null}
      {message ? (
        <div className="rounded-lg border border-emerald-500/40 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">
          {message}
        </div>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {kpiCards.map((card) => (
          <div key={card.label} className="rounded-xl border border-slate-600/60 bg-slate-950/80 p-4">
            <p className="text-xs font-medium text-slate-400">{card.label}</p>
            <p className="mt-1 text-2xl font-bold text-slate-50">{loading ? '…' : card.value}</p>
            <p className="mt-2 text-xs text-slate-500">{card.hint}</p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-slate-600/60 bg-slate-950/70 p-4">
        <h2 className="text-lg font-semibold text-slate-100">Status dos refreshes</h2>
        <div className="mt-3 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="px-2 py-2">View</th>
                <th className="px-2 py-2">Status</th>
                <th className="px-2 py-2">Início</th>
                <th className="px-2 py-2">Duração</th>
                <th className="px-2 py-2">Origem</th>
              </tr>
            </thead>
            <tbody>
              {refreshStatus.map((row) => (
                <tr key={row.view_name} className="border-t border-slate-700/60 text-slate-200">
                  <td className="px-2 py-2 font-mono text-xs">{row.view_name}</td>
                  <td className="px-2 py-2">{row.status}</td>
                  <td className="px-2 py-2">{row.started_at ? new Date(row.started_at).toLocaleString('pt-BR') : '—'}</td>
                  <td className="px-2 py-2">{row.duration_ms != null ? `${row.duration_ms} ms` : '—'}</td>
                  <td className="px-2 py-2">{row.triggered_by || '—'}</td>
                </tr>
              ))}
              {!loading && refreshStatus.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-2 py-4 text-slate-400">
                    Nenhum refresh registrado ainda. Execute o script SQL de agendamento.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-slate-600/60 bg-slate-950/70 p-4">
        <h2 className="text-lg font-semibold text-slate-100">Rentabilidade por locker</h2>
        <form onSubmit={onFilter} className="mt-3 grid gap-3 md:grid-cols-[1fr_180px_auto]">
          <input
            className={inp}
            placeholder="locker_id (opcional)"
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
          />
          <input
            className={inp}
            type="month"
            value={month ? month.slice(0, 7) : ''}
            onChange={(e) => setMonth(e.target.value ? `${e.target.value}-01` : '')}
          />
          <button
            type="submit"
            className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-900 hover:bg-white"
          >
            Filtrar
          </button>
        </form>
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="text-slate-400">
              <tr>
                <th className="px-2 py-2">Locker</th>
                <th className="px-2 py-2">Mês</th>
                <th className="px-2 py-2">Receita</th>
                <th className="px-2 py-2">Custos</th>
                <th className="px-2 py-2">Lucro</th>
                <th className="px-2 py-2">Margem</th>
                <th className="px-2 py-2">Pickups</th>
              </tr>
            </thead>
            <tbody>
              {profitability.map((row) => (
                <tr key={`${row.locker_id}-${row.month}`} className="border-t border-slate-700/60 text-slate-200">
                  <td className="px-2 py-2 font-mono text-xs">{row.locker_id}</td>
                  <td className="px-2 py-2">{row.month}</td>
                  <td className="px-2 py-2">{brl(row.total_revenue_cents)}</td>
                  <td className="px-2 py-2">{brl(row.total_costs_cents)}</td>
                  <td className="px-2 py-2">{brl(row.net_profit_cents)}</td>
                  <td className="px-2 py-2">{pct(row.net_margin_pct)}</td>
                  <td className="px-2 py-2">{row.total_pickups}</td>
                </tr>
              ))}
              {!loading && profitability.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-2 py-4 text-slate-400">
                    Nenhum registro encontrado para os filtros informados.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
