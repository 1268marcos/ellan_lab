import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { walletApi, type TransactionsFilter, type TxRow } from '../../api/wallet'

const DEFAULT_ID =
  (typeof import.meta.env.VITE_WALLET_USER_ID === 'string' && import.meta.env.VITE_WALLET_USER_ID) ||
  'user-demo-001'

export default function Transactions() {
  const [partnerId, setPartnerId] = useState(DEFAULT_ID)
  const [rows, setRows] = useState<TxRow[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<TransactionsFilter>({
    date_start: '',
    date_end: '',
    type: '',
    status: '',
  })

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const { data } = await walletApi.getTransactions(partnerId, filters)
      setRows(Array.isArray(data) ? data : [])
    } catch (err: unknown) {
      setRows([])
      setError(err instanceof Error ? err.message : 'Erro ao carregar transações')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Transações Wallet</h1>
          <p className="text-sm text-slate-400">Filtros por período, tipo e status</p>
        </div>
        <Link to="/finance/wallet" className="text-sm text-emerald-400 hover:underline">
          ← Voltar para Wallet
        </Link>
      </div>

      <div className="grid gap-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4 sm:grid-cols-2 lg:grid-cols-5">
        <label className="text-xs text-slate-400">
          Partner ID
          <input
            value={partnerId}
            onChange={(e) => setPartnerId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <label className="text-xs text-slate-400">
          Data início
          <input
            type="date"
            value={filters.date_start}
            onChange={(e) => setFilters((f) => ({ ...f, date_start: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <label className="text-xs text-slate-400">
          Data fim
          <input
            type="date"
            value={filters.date_end}
            onChange={(e) => setFilters((f) => ({ ...f, date_end: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          />
        </label>
        <label className="text-xs text-slate-400">
          Tipo
          <select
            value={filters.type}
            onChange={(e) => setFilters((f) => ({ ...f, type: e.target.value as TransactionsFilter['type'] }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
          >
            <option value="">todos</option>
            <option value="credit">crédito</option>
            <option value="debit">débito</option>
          </select>
        </label>
        <label className="text-xs text-slate-400">
          Status
          <input
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
            placeholder="pending/success/failed"
          />
        </label>
        <button
          type="button"
          onClick={() => void load()}
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 sm:col-span-2 lg:col-span-1"
        >
          Aplicar filtros
        </button>
      </div>

      {loading && <p className="text-sm text-slate-400">Carregando transações...</p>}
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="overflow-hidden rounded-xl border border-slate-700">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">TX</th>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Valor</th>
              <th className="px-3 py-2">Data</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-slate-500">
                  Nenhuma transação encontrada
                </td>
              </tr>
            ) : (
              rows.map((row, idx) => (
                <tr key={row.transaction_id ?? row.id ?? idx} className="border-t border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs text-slate-300">{row.transaction_id ?? row.id ?? '—'}</td>
                  <td className="px-3 py-2 text-slate-300">{row.type ?? '—'}</td>
                  <td className="px-3 py-2 text-slate-300">{row.status ?? '—'}</td>
                  <td className="px-3 py-2 tabular-nums text-slate-300">
                    {typeof row.amount === 'number' ? (row.amount / 100).toFixed(2) : '—'}
                  </td>
                  <td className="px-3 py-2 text-slate-400">{row.created_at ?? row.occurred_at ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
