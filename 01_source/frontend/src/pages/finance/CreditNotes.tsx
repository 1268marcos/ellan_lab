import { useCallback, useEffect, useState } from 'react'
import { billingApi } from '../../api/billing'
import { useAuth } from '../../contexts/AuthContext'

type CreditNoteStatus = 'PENDING' | 'APPROVED' | 'APPLIED' | 'REFUNDED' | 'EXPIRED' | 'CANCELLED'

type CreditNoteRow = {
  id?: string
  credit_note_id?: string
  reason_code?: string
  description?: string
  amount_cents?: number
  status?: CreditNoteStatus | string
  expires_at?: string
}

function creditNoteStatusBadgeClasses(status: string): string {
  const base = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1'
  const s = status.toUpperCase()
  switch (s as CreditNoteStatus) {
    case 'PENDING':
      return `${base} bg-yellow-500/20 text-yellow-300 ring-yellow-500/35`
    case 'APPROVED':
      return `${base} bg-blue-500/20 text-blue-300 ring-blue-500/35`
    case 'APPLIED':
      return `${base} bg-green-500/20 text-green-300 ring-green-500/35`
    case 'REFUNDED':
      return `${base} bg-emerald-500/20 text-emerald-300 ring-emerald-500/35`
    case 'EXPIRED':
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/40`
    case 'CANCELLED':
      return `${base} bg-red-500/20 text-red-300 ring-red-500/35`
    default:
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/30`
  }
}

function formatCents(cents: number | undefined): string {
  if (cents == null || Number.isNaN(cents)) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

function normalizeCreditNotes(payload: unknown): CreditNoteRow[] {
  if (Array.isArray(payload)) return payload as CreditNoteRow[]
  if (payload && typeof payload === 'object' && 'items' in payload && Array.isArray((payload as { items: unknown }).items)) {
    return (payload as { items: CreditNoteRow[] }).items
  }
  if (
    payload &&
    typeof payload === 'object' &&
    'credit_notes' in payload &&
    Array.isArray((payload as { credit_notes: unknown }).credit_notes)
  ) {
    return (payload as { credit_notes: CreditNoteRow[] }).credit_notes
  }
  if (payload && typeof payload === 'object' && 'data' in payload && Array.isArray((payload as { data: unknown }).data)) {
    return (payload as { data: CreditNoteRow[] }).data
  }
  return []
}

function rowId(row: CreditNoteRow): string | undefined {
  return row.credit_note_id ?? row.id
}

export default function CreditNotes() {
  const { auth } = useAuth()
  const [rows, setRows] = useState<CreditNoteRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [cycleId, setCycleId] = useState('')
  const [applyBusy, setApplyBusy] = useState<string | null>(null)

  const partnerId = auth?.partnerId ?? ''

  const load = useCallback(async () => {
    if (!partnerId) {
      setRows([])
      setError('Sem parceiro autenticado.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await billingApi.getCreditNotes(partnerId)
      setRows(normalizeCreditNotes(data))
    } catch (e: unknown) {
      setRows([])
      setError(e instanceof Error ? e.message : 'Falha ao carregar notas de crédito')
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  async function onApply(row: CreditNoteRow) {
    const id = rowId(row)
    const cid = cycleId.trim()
    if (!id || !cid) return
    setApplyBusy(id)
    setError(null)
    try {
      await billingApi.applyCreditNote(id, cid)
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao aplicar nota de crédito')
    } finally {
      setApplyBusy(null)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">Notas de crédito</h1>
        <p className="text-sm text-slate-400">Parceiro: {partnerId || '—'}</p>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <label className="block min-w-[14rem] text-xs text-slate-400">
          Ciclo (ID) — aplicar notas neste ciclo
          <input
            value={cycleId}
            onChange={(e) => setCycleId(e.target.value)}
            placeholder="cycle-uuid ou id interno"
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 font-mono text-sm text-white"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-md bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
        >
          Atualizar lista
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Carregando...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-900/60">
        <table className="min-w-full divide-y divide-slate-700 text-left text-sm">
          <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">reason_code</th>
              <th className="px-4 py-3">description</th>
              <th className="px-4 py-3">amount_cents</th>
              <th className="px-4 py-3">status</th>
              <th className="px-4 py-3">expires_at</th>
              <th className="px-4 py-3">actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-200">
            {rows.length === 0 && !loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  Nenhuma nota de crédito.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => {
                const id = rowId(row)
                const key = id ?? `row-${idx}`
                const st = String(row.status ?? '—')
                const canApply = Boolean(cycleId.trim() && id)
                return (
                  <tr key={key} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-mono text-xs">{row.reason_code ?? '—'}</td>
                    <td className="max-w-xs truncate px-4 py-3 text-xs" title={row.description}>
                      {row.description ?? '—'}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {row.amount_cents != null ? `${row.amount_cents} (${formatCents(row.amount_cents)})` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={creditNoteStatusBadgeClasses(st)}>{st}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{row.expires_at ?? '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        disabled={!canApply || applyBusy === id}
                        onClick={() => void onApply(row)}
                        className="rounded bg-emerald-600 px-2 py-1 text-xs font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
                      >
                        {applyBusy === id ? '...' : 'Aplicar no ciclo'}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
