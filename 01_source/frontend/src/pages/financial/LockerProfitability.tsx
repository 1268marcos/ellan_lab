import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import ProfitabilityHeatmap from '../../components/financial/ProfitabilityHeatmap'
import { financialExecutiveApi, type LockerPnlRow } from '../../api/financialExecutive'
import { loadAuth } from '../../api/auth'

const inp =
  'w-full rounded-lg border border-slate-600/70 bg-slate-900/90 px-3 py-2 text-sm text-slate-100'

type SortKey = 'month_ref' | 'locker_id' | 'revenue_cents' | 'net_profit_cents' | 'margin_pct'

function brlCents(cents?: number | null) {
  if (cents == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(cents) / 100)
}

export default function LockerProfitability() {
  const [lockerId, setLockerId] = useState('')
  const [monthFrom, setMonthFrom] = useState('')
  const [monthTo, setMonthTo] = useState('')
  const [sort, setSort] = useState<SortKey>('month_ref')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')
  const [rows, setRows] = useState<LockerPnlRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await financialExecutiveApi.lockerPnl({
        locker_id: lockerId || undefined,
        month_from: monthFrom || undefined,
        month_to: monthTo || undefined,
        sort,
        order,
      })
      setRows(res.data.items ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar P&L')
    } finally {
      setLoading(false)
    }
  }, [lockerId, monthFrom, monthTo, sort, order])

  useEffect(() => {
    void load()
  }, [load])

  function onFilter(e: FormEvent) {
    e.preventDefault()
    void load()
  }

  function toggleSort(key: SortKey) {
    if (sort === key) setOrder((o) => (o === 'asc' ? 'desc' : 'asc'))
    else {
      setSort(key)
      setOrder('desc')
    }
  }

  const thBtn = (key: SortKey, label: string) => (
    <button type="button" onClick={() => toggleSort(key)} className="font-semibold hover:text-indigo-300">
      {label}
      {sort === key ? (order === 'asc' ? ' ↑' : ' ↓') : ''}
    </button>
  )

  const exportFile = useMemo(
    () => (format: 'csv' | 'pdf') => {
      const auth = loadAuth()
      const url = financialExecutiveApi.exportUrl(format, 'locker-pnl')
      const headers: Record<string, string> = {}
      if (auth?.apiKey) {
        headers['X-API-Key'] = auth.apiKey
        headers.Authorization = `Bearer ${auth.token || auth.apiKey}`
      }
      fetch(url, { headers })
        .then((r) => r.blob())
        .then((blob) => {
          const a = document.createElement('a')
          a.href = URL.createObjectURL(blob)
          a.download = `locker-pnl.${format}`
          a.click()
          URL.revokeObjectURL(a.href)
        })
    },
    [],
  )

  return (
    <div className="space-y-6">
      <form onSubmit={onFilter} className="flex flex-wrap items-end gap-3">
        <label className="min-w-[140px] flex-1 text-sm">
          <span className="mb-1 block text-slate-400">Locker ID</span>
          <input className={inp} value={lockerId} onChange={(e) => setLockerId(e.target.value)} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Mês de</span>
          <input type="date" className={inp} value={monthFrom} onChange={(e) => setMonthFrom(e.target.value)} />
        </label>
        <label className="text-sm">
          <span className="mb-1 block text-slate-400">Mês até</span>
          <input type="date" className={inp} value={monthTo} onChange={(e) => setMonthTo(e.target.value)} />
        </label>
        <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500">
          Filtrar
        </button>
        <button type="button" onClick={() => exportFile('csv')} className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200">
          CSV
        </button>
        <button type="button" onClick={() => exportFile('pdf')} className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200">
          PDF
        </button>
      </form>

      {error ? (
        <div className="rounded-lg border border-red-500/40 bg-red-950/40 px-4 py-3 text-sm text-red-200">{error}</div>
      ) : null}

      <ProfitabilityHeatmap rows={rows} />

      <div className="overflow-x-auto rounded-xl border border-slate-600/60">
        <table className="min-w-full text-left text-sm text-slate-200">
          <thead className="bg-slate-900/90 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-3 py-2">{thBtn('month_ref', 'Mês')}</th>
              <th className="px-3 py-2">{thBtn('locker_id', 'Locker')}</th>
              <th className="px-3 py-2">{thBtn('revenue_cents', 'Receita')}</th>
              <th className="px-3 py-2">Opex</th>
              <th className="px-3 py-2">Deprec.</th>
              <th className="px-3 py-2">{thBtn('net_profit_cents', 'Lucro')}</th>
              <th className="px-3 py-2">{thBtn('margin_pct', 'Margem')}</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                  Carregando…
                </td>
              </tr>
            ) : rows.length ? (
              rows.map((r) => (
                <tr key={`${r.month_ref}-${r.locker_id}`} className="border-t border-slate-700/50">
                  <td className="px-3 py-2">{String(r.month_ref).slice(0, 10)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{r.locker_id}</td>
                  <td className="px-3 py-2">{brlCents(r.revenue_cents)}</td>
                  <td className="px-3 py-2">{brlCents(r.opex_cents)}</td>
                  <td className="px-3 py-2">{brlCents(r.depreciation_cents)}</td>
                  <td className="px-3 py-2">{brlCents(r.net_profit_cents)}</td>
                  <td className="px-3 py-2">{Number(r.margin_pct).toFixed(1)}%</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-500">
                  Nenhum registro.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
