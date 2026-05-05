import { useMemo, useState } from 'react'
import type { TxRow } from '../api/wallet'

export function TransactionsTable({ rows }: { rows: TxRow[] }) {
  const [from, setFrom] = useState('')
  const [to, setTo] = useState('')
  const [type, setType] = useState('')
  const [status, setStatus] = useState('')

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      const t = (r.type ?? '').toLowerCase()
      const s = (r.status ?? '').toLowerCase()
      const d = r.created_at ?? r.occurred_at ?? ''
      if (type && !t.includes(type.toLowerCase())) return false
      if (status && !s.includes(status.toLowerCase())) return false
      if (from && d && d < from) return false
      if (to && d && d > `${to}T23:59:59`) return false
      return true
    })
  }, [rows, from, to, type, status])

  return (
    <div className="overflow-hidden rounded-xl border border-slate-700">
      <div className="flex flex-wrap gap-2 border-b border-slate-800 bg-slate-900/80 p-3">
        <input
          type="date"
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-white"
        />
        <input
          type="date"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-white"
        />
        <input
          placeholder="tipo"
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-white"
        />
        <input
          placeholder="status"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-white"
        />
      </div>
      <table className="w-full text-left text-sm">
        <thead className="text-xs uppercase text-slate-500">
          <tr>
            <th className="px-3 py-2">ID</th>
            <th className="px-3 py-2">Tipo</th>
            <th className="px-3 py-2">Valor</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Data</th>
          </tr>
        </thead>
        <tbody>
          {filtered.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-3 py-8 text-center text-slate-500">
                Sem transações
              </td>
            </tr>
          ) : (
            filtered.map((r, i) => (
              <tr key={r.transaction_id ?? r.id ?? i} className="border-t border-slate-800">
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{r.transaction_id ?? r.id ?? '—'}</td>
                <td className="px-3 py-2">{r.type ?? '—'}</td>
                <td className="px-3 py-2 tabular-nums">
                  {r.amount != null ? (r.amount / 100).toFixed(2) : '—'}
                </td>
                <td className="px-3 py-2">{r.status ?? '—'}</td>
                <td className="px-3 py-2 text-xs text-slate-400">{r.created_at ?? r.occurred_at ?? '—'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
