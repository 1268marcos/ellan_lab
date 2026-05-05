import { useCallback, useEffect, useMemo, useState } from 'react'
import { billingApi } from '../../api/billing'
import { loadAuth } from '../../api/auth'
import { useAuth } from '../../contexts/AuthContext'

type PartnerInvoiceStatus =
  | 'DRAFT'
  | 'ISSUED'
  | 'SENT'
  | 'VIEWED'
  | 'PAID'
  | 'OVERDUE'
  | 'DISPUTED'
  | 'CANCELLED'

type PartnerInvoiceRow = {
  id?: string
  invoice_id?: string
  invoice_number?: string
  issued_at?: string
  amount_cents?: number
  status?: PartnerInvoiceStatus | string
}

function invoiceStatusBadgeClasses(status: string): string {
  const base = 'inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1'
  const s = status.toUpperCase()
  switch (s as PartnerInvoiceStatus) {
    case 'DRAFT':
      return `${base} bg-slate-600/40 text-slate-300 ring-slate-500/40`
    case 'ISSUED':
      return `${base} bg-emerald-500/20 text-emerald-300 ring-emerald-500/35`
    case 'SENT':
      return `${base} bg-blue-500/20 text-blue-300 ring-blue-500/35`
    case 'VIEWED':
      return `${base} bg-cyan-500/20 text-cyan-300 ring-cyan-500/35`
    case 'PAID':
      return `${base} bg-green-500/20 text-green-300 ring-green-500/35`
    case 'OVERDUE':
      return `${base} bg-red-500/20 text-red-300 ring-red-500/35`
    case 'DISPUTED':
      return `${base} bg-orange-500/20 text-orange-300 ring-orange-500/35`
    case 'CANCELLED':
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/40`
    default:
      return `${base} bg-slate-600/40 text-slate-400 ring-slate-500/30`
  }
}

function formatCents(cents: number | undefined): string {
  if (cents == null || Number.isNaN(cents)) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(cents / 100)
}

function normalizeInvoices(payload: unknown): PartnerInvoiceRow[] {
  if (Array.isArray(payload)) return payload as PartnerInvoiceRow[]
  if (payload && typeof payload === 'object' && 'items' in payload && Array.isArray((payload as { items: unknown }).items)) {
    return (payload as { items: PartnerInvoiceRow[] }).items
  }
  if (payload && typeof payload === 'object' && 'invoices' in payload && Array.isArray((payload as { invoices: unknown }).invoices)) {
    return (payload as { invoices: PartnerInvoiceRow[] }).invoices
  }
  if (payload && typeof payload === 'object' && 'data' in payload && Array.isArray((payload as { data: unknown }).data)) {
    return (payload as { data: PartnerInvoiceRow[] }).data
  }
  return []
}

function invoiceRowId(row: PartnerInvoiceRow): string | undefined {
  return row.invoice_id ?? row.id
}

async function downloadPartnerInvoice(partnerId: string, invoiceId: string, format: 'pdf' | 'xml'): Promise<void> {
  const auth = loadAuth()
  const headers: Record<string, string> = {}
  if (auth?.apiKey) {
    headers['X-API-Key'] = auth.apiKey
    headers.Authorization = `Bearer ${auth.token || auth.apiKey}`
  }
  const q = new URLSearchParams({ format })
  const url = `/api/billing-svc/v1/partners/${encodeURIComponent(partnerId)}/invoices/${encodeURIComponent(invoiceId)}/download?${q}`
  const res = await fetch(url, { headers })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(text || `Download falhou (${res.status})`)
  }
  const blob = await res.blob()
  const ext = format === 'pdf' ? 'pdf' : 'xml'
  const cd = res.headers.get('Content-Disposition')
  let filename = `invoice-${invoiceId}.${ext}`
  const m = cd?.match(/filename\*?=(?:UTF-8'')?["']?([^";\n]+)/i)
  if (m?.[1]) filename = decodeURIComponent(m[1].replace(/["']/g, ''))
  const a = document.createElement('a')
  const objectUrl = URL.createObjectURL(blob)
  a.href = objectUrl
  a.download = filename
  a.click()
  URL.revokeObjectURL(objectUrl)
}

export default function PartnerInvoices() {
  const { auth } = useAuth()
  const [rows, setRows] = useState<PartnerInvoiceRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [downloadBusy, setDownloadBusy] = useState<string | null>(null)

  const partnerId = auth?.partnerId ?? ''

  const periodParams = useMemo(
    () => ({
      ...(dateStart ? { date_start: dateStart } : {}),
      ...(dateEnd ? { date_end: dateEnd } : {}),
    }),
    [dateStart, dateEnd],
  )

  const load = useCallback(async () => {
    if (!partnerId) {
      setRows([])
      setError('Sem parceiro autenticado.')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await billingApi.getInvoices(partnerId, periodParams)
      setRows(normalizeInvoices(data))
    } catch (e: unknown) {
      setRows([])
      setError(e instanceof Error ? e.message : 'Falha ao carregar notas')
    } finally {
      setLoading(false)
    }
  }, [partnerId, periodParams])

  useEffect(() => {
    void load()
  }, [load])

  async function onDownload(row: PartnerInvoiceRow, format: 'pdf' | 'xml') {
    const invId = invoiceRowId(row)
    if (!partnerId || !invId) return
    const key = `${invId}-${format}`
    setDownloadBusy(key)
    setError(null)
    try {
      await downloadPartnerInvoice(partnerId, invId, format)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Download falhou')
    } finally {
      setDownloadBusy(null)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div>
        <h1 className="text-2xl font-semibold text-white">Notas fiscais (B2B)</h1>
        <p className="text-sm text-slate-400">Parceiro: {partnerId || '—'}</p>
      </div>

      <div className="flex flex-wrap items-end gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <label className="text-xs text-slate-400">
          Período — início
          <input
            type="date"
            value={dateStart}
            onChange={(e) => setDateStart(e.target.value)}
            className="mt-1 block rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <label className="text-xs text-slate-400">
          Período — fim
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
          Filtrar período
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Carregando notas...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-x-auto rounded-xl border border-slate-700 bg-slate-900/60">
        <table className="min-w-full divide-y divide-slate-700 text-left text-sm">
          <thead className="bg-slate-950/80 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">invoice_number</th>
              <th className="px-4 py-3">issued_at</th>
              <th className="px-4 py-3">amount_cents</th>
              <th className="px-4 py-3">status</th>
              <th className="px-4 py-3">actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800 text-slate-200">
            {rows.length === 0 && !loading ? (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                  Nenhuma nota encontrada.
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => {
                const invId = invoiceRowId(row)
                const key = invId ?? `row-${idx}`
                const st = String(row.status ?? '—')
                return (
                  <tr key={key} className="hover:bg-slate-800/40">
                    <td className="px-4 py-3 font-mono text-xs">{row.invoice_number ?? '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">{row.issued_at ?? '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs">
                      {row.amount_cents != null ? `${row.amount_cents} (${formatCents(row.amount_cents)})` : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={invoiceStatusBadgeClasses(st)}>{st}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          disabled={!invId || downloadBusy === `${invId}-pdf`}
                          onClick={() => void onDownload(row, 'pdf')}
                          className="rounded bg-red-700/90 px-2 py-1 text-xs font-medium text-white hover:bg-red-600 disabled:opacity-40"
                        >
                          PDF
                        </button>
                        <button
                          type="button"
                          disabled={!invId || downloadBusy === `${invId}-xml`}
                          onClick={() => void onDownload(row, 'xml')}
                          className="rounded bg-slate-600 px-2 py-1 text-xs font-medium text-white hover:bg-slate-500 disabled:opacity-40"
                        >
                          XML
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
    </div>
  )
}
