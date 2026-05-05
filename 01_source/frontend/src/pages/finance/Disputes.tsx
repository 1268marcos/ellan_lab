import { useCallback, useEffect, useState } from 'react'
import { billingApi } from '../../api/billing'
import { useAuth } from '../../contexts/AuthContext'

type DisputeStatus = 'OPEN' | 'UNDER_REVIEW' | 'ACCEPTED' | 'REJECTED' | 'CLOSED'

type DisputeRow = {
  id?: string
  dispute_id?: string
  invoice_id?: string
  reason?: string
  status?: DisputeStatus | string
  created_at?: string
  resolved_at?: string
  history?: unknown
  events?: unknown
}

function disputeStatusBadgeClasses(status: string): string {
  const base = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1'
  const s = status.toUpperCase().replace(/\s+/g, '_')
  switch (s as DisputeStatus) {
    case 'OPEN':
      return `${base} bg-red-500/20 text-red-300 ring-red-500/35`
    case 'UNDER_REVIEW':
      return `${base} bg-orange-500/20 text-orange-300 ring-orange-500/35`
    case 'ACCEPTED':
      return `${base} bg-green-500/20 text-green-300 ring-green-500/35`
    case 'REJECTED':
      return `${base} bg-red-600/25 text-red-200 ring-red-500/40`
    case 'CLOSED':
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/40`
    default:
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/30`
  }
}

function normalizeDisputes(payload: unknown): DisputeRow[] {
  if (Array.isArray(payload)) return payload as DisputeRow[]
  if (payload && typeof payload === 'object' && 'items' in payload && Array.isArray((payload as { items: unknown }).items)) {
    return (payload as { items: DisputeRow[] }).items
  }
  if (payload && typeof payload === 'object' && 'disputes' in payload && Array.isArray((payload as { disputes: unknown }).disputes)) {
    return (payload as { disputes: DisputeRow[] }).disputes
  }
  if (payload && typeof payload === 'object' && 'data' in payload && Array.isArray((payload as { data: unknown }).data)) {
    return (payload as { data: DisputeRow[] }).data
  }
  return []
}

function rowId(row: DisputeRow): string | undefined {
  return row.dispute_id ?? row.id
}

function formatHistory(row: DisputeRow): string {
  const raw = row.history ?? row.events
  if (raw == null) return '—'
  try {
    return JSON.stringify(raw, null, 2)
  } catch {
    return String(raw)
  }
}

export default function Disputes() {
  const { auth } = useAuth()
  const [rows, setRows] = useState<DisputeRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [modalRow, setModalRow] = useState<DisputeRow | null>(null)
  const [responseText, setResponseText] = useState('')
  const [submitBusy, setSubmitBusy] = useState(false)

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
      const { data } = await billingApi.getDisputes(partnerId)
      setRows(normalizeDisputes(data))
    } catch (e: unknown) {
      setRows([])
      setError(e instanceof Error ? e.message : 'Falha ao carregar disputas')
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  function openRespond(row: DisputeRow) {
    setError(null)
    setModalRow(row)
    setResponseText('')
  }

  function closeModal() {
    setModalRow(null)
    setResponseText('')
  }

  async function submitResponse() {
    const id = modalRow ? rowId(modalRow) : undefined
    const text = responseText.trim()
    if (!id || !text) return
    setSubmitBusy(true)
    setError(null)
    try {
      await billingApi.respondDispute(id, text)
      closeModal()
      await load()
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao enviar resposta')
    } finally {
      setSubmitBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Disputas de faturamento</h1>
          <p className="text-sm text-slate-400">Parceiro: {partnerId || '—'}</p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded-md bg-slate-700 px-3 py-2 text-sm text-white hover:bg-slate-600"
        >
          Atualizar
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Carregando...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-900/60">
        <table className="min-w-full divide-y divide-slate-700 text-left text-sm">
          <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">invoice_id</th>
              <th className="px-4 py-3">reason</th>
              <th className="px-4 py-3">status</th>
              <th className="px-4 py-3">created_at</th>
              <th className="px-4 py-3">resolved_at</th>
              <th className="px-4 py-3">actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-200">
            {rows.length === 0 && !loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-slate-500">
                  Nenhuma disputa.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => {
                const id = rowId(row)
                const key = id ?? `row-${idx}`
                const st = String(row.status ?? '—')
                return (
                  <tr key={key} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-mono text-xs">{row.invoice_id ?? '—'}</td>
                    <td className="max-w-xs truncate px-4 py-3 text-xs" title={row.reason}>
                      {row.reason ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={disputeStatusBadgeClasses(st)}>{st}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs">{row.created_at ?? '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{row.resolved_at ?? '—'}</td>
                    <td className="px-4 py-3">
                      <button
                        type="button"
                        disabled={!id}
                        onClick={() => openRespond(row)}
                        className="rounded bg-blue-600 px-2 py-1 text-xs font-medium text-white hover:bg-blue-500 disabled:opacity-40"
                      >
                        Responder
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {modalRow && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true">
          <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-slate-600 bg-slate-900 p-4 shadow-xl">
            <h2 className="text-lg font-semibold text-white">Responder disputa</h2>
            <p className="mt-1 font-mono text-xs text-slate-400">ID: {rowId(modalRow) ?? '—'}</p>
            {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
            <section className="mt-4">
              <h3 className="text-xs font-semibold uppercase text-slate-500">Histórico</h3>
              <pre className="mt-1 max-h-40 overflow-auto rounded bg-slate-950 p-2 text-[11px] text-slate-400">
                {formatHistory(modalRow)}
              </pre>
            </section>
            <label className="mt-4 block text-xs text-slate-400">
              Sua resposta
              <textarea
                value={responseText}
                onChange={(e) => setResponseText(e.target.value)}
                rows={5}
                className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-2 text-sm text-white"
                placeholder="Descreva a resposta ou evidências..."
              />
            </label>
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" onClick={closeModal} className="rounded px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">
                Cancelar
              </button>
              <button
                type="button"
                disabled={submitBusy || !responseText.trim()}
                onClick={() => void submitResponse()}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
              >
                {submitBusy ? 'Enviando...' : 'Enviar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
