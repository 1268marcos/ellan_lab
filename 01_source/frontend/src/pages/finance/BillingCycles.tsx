import { useCallback, useEffect, useMemo, useState } from 'react'
import { billingApi } from '../../api/billing'
import { useAuth } from '../../contexts/AuthContext'
import type { BillingCycle, BillingCycleStatus } from '../../types'

function statusBadgeClasses(status: string): string {
  const base = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1'
  const s = status.toUpperCase()
  switch (s as BillingCycleStatus) {
    case 'OPEN':
      return `${base} bg-sky-500/20 text-sky-300 ring-sky-500/35`
    case 'COMPUTING':
      return `${base} bg-amber-500/20 text-amber-300 ring-amber-500/35`
    case 'APPROVED':
      return `${base} bg-green-500/20 text-green-300 ring-green-500/35`
    case 'INVOICED':
      return `${base} bg-blue-500/20 text-blue-300 ring-blue-500/35`
    case 'PAID':
      return `${base} bg-emerald-500/20 text-emerald-300 ring-emerald-500/35`
    case 'DISPUTED':
      return `${base} bg-red-500/20 text-red-300 ring-red-500/35`
    case 'CANCELLED':
      return `${base} bg-slate-600/40 text-slate-300 ring-slate-500/40`
    default:
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/30`
  }
}

function formatCents(cents: number | undefined): string {
  if (cents == null || Number.isNaN(cents)) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

function normalizeCycles(payload: unknown): BillingCycle[] {
  if (Array.isArray(payload)) return payload as BillingCycle[]
  if (payload && typeof payload === 'object' && 'items' in payload && Array.isArray((payload as { items: unknown }).items)) {
    return (payload as { items: BillingCycle[] }).items
  }
  if (payload && typeof payload === 'object' && 'cycles' in payload && Array.isArray((payload as { cycles: unknown }).cycles)) {
    return (payload as { cycles: BillingCycle[] }).cycles
  }
  if (payload && typeof payload === 'object' && 'data' in payload && Array.isArray((payload as { data: unknown }).data)) {
    return (payload as { data: BillingCycle[] }).data
  }
  return []
}

export default function BillingCycles() {
  const { auth } = useAuth()
  const [cycles, setCycles] = useState<BillingCycle[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [selected, setSelected] = useState<BillingCycle | null>(null)
  const [computeBusyId, setComputeBusyId] = useState<string | null>(null)

  const partnerId = auth?.partnerId ?? ''

  const filterParams = useMemo(
    () => ({
      ...(dateStart ? { date_start: dateStart } : {}),
      ...(dateEnd ? { date_end: dateEnd } : {}),
      ...(statusFilter ? { status: statusFilter } : {}),
    }),
    [dateStart, dateEnd, statusFilter],
  )

  const load = useCallback(async () => {
    if (!partnerId) {
      setCycles([])
      setError('Sem parceiro autenticado.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await billingApi.getCycles(partnerId, filterParams)
      setCycles(normalizeCycles(data))
    } catch (e: unknown) {
      setCycles([])
      setError(e instanceof Error ? e.message : 'Falha ao carregar ciclos')
    } finally {
      setLoading(false)
    }
  }, [partnerId, filterParams])

  useEffect(() => {
    void load()
  }, [load])

  async function onCompute(row: BillingCycle) {
    if (!partnerId || !row.period_start || !row.period_end) return
    const id = row.id ?? `${row.period_start}-${row.period_end}`
    setComputeBusyId(id)
    setError(null)
    try {
      await billingApi.computeCycle({
        partner_id: partnerId,
        date_start: row.period_start,
        date_end: row.period_end,
      })
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao computar ciclo')
    } finally {
      setComputeBusyId(null)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">Ciclos de faturamento</h1>
        <p className="text-sm text-slate-400">Parceiro: {partnerId || '—'}</p>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <label className="text-xs text-slate-400">
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="mt-1 block rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          >
            <option value="">Todos</option>
            <option value="OPEN">OPEN</option>
            <option value="COMPUTING">COMPUTING</option>
            <option value="APPROVED">APPROVED</option>
            <option value="INVOICED">INVOICED</option>
            <option value="PAID">PAID</option>
            <option value="DISPUTED">DISPUTED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>
        </label>
        <label className="text-xs text-slate-400">
          Início
          <input
            type="date"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
            className="mt-1 block rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <label className="text-xs text-slate-400">
          Fim
          <input
            type="date"
            value={dateEnd}
            onChange={(e) => setDateEnd(e.target.value)}
            className="mt-1 block rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-md bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
        >
          Aplicar filtros
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Carregando ciclos...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-900/60">
        <table className="min-w-full divide-y divide-slate-700 text-left text-sm">
          <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">period_start</th>
              <th className="px-4 py-3">period_end</th>
              <th className="px-4 py-3">status</th>
              <th className="px-4 py-3">total_amount_cents</th>
              <th className="px-4 py-3">actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-200">
            {cycles.length === 0 && !loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  Nenhum ciclo encontrado.
                </td>
              </tr>
            ) : (
              cycles.map((row, idx) => {
                const key = row.id ?? `${row.period_start ?? ''}-${row.period_end ?? ''}-${idx}`
                const st = String(row.status ?? '—')
                const busy = computeBusyId === (row.id ?? `${row.period_start}-${row.period_end}`)
                return (
                  <tr key={key} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-mono text-xs">{row.period_start ?? '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{row.period_end ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className={statusBadgeClasses(st)}>{st}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {row.total_amount_cents != null ? `${row.total_amount_cents} (${formatCents(row.total_amount_cents)})` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={busy || !row.period_start || !row.period_end}
                          onClick={() => void onCompute(row)}
                          className="rounded bg-amber-600/90 px-2 py-1 text-xs font-medium text-white hover:bg-amber-500 disabled:opacity-40"
                        >
                          {busy ? '...' : 'compute'}
                        </button>
                        <button
                          type="button"
                          onClick={() => setSelected(row)}
                          className="rounded bg-slate-600 px-2 py-1 text-xs font-medium text-white hover:bg-slate-500"
                        >
                          view
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {selected && (
        <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-200">Detalhe do ciclo</h2>
            <button type="button" onClick={() => setSelected(null)} className="text-xs text-slate-400 hover:text-white">
              fechar
            </button>
          </div>
          <pre className="max-h-64 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-400">{JSON.stringify(selected, null, 2)}</pre>
        </section>
      )}
    </div>
  )
}
