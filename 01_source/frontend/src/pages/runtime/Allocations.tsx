import { useCallback, useEffect, useState } from 'react'

import { fetchInventoryAllocations, type InventoryAllocationsResponse } from '../../api/runtime'
import { useAuth } from '../../AuthContext'

export default function RuntimeAllocations() {
  const { auth } = useAuth()
  const partnerId = auth?.partnerId ?? ''

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [payload, setPayload] = useState<InventoryAllocationsResponse | null>(null)

  const load = useCallback(async () => {
    if (!partnerId) {
      setError('Sessão sem partnerId.')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await fetchInventoryAllocations(partnerId)
      setPayload(data)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Falha ao carregar alocações.'
      setError(msg)
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  const rows = payload?.data?.allocations ?? []

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Runtime / Alocações</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">Lista via BFF (placeholder).</p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Atualizando…' : 'Tentar novamente'}
        </button>
      </div>

      {loading && !payload && (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          Carregando alocações…
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      {payload && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
            <thead className="bg-slate-50 dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-200">ID</th>
                <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-200">Pedido</th>
                <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-200">Locker</th>
                <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-200">Slot</th>
                <th className="px-3 py-2 text-left font-medium text-slate-700 dark:text-slate-200">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-slate-500 dark:text-slate-400">
                    Nenhuma alocação retornada.
                  </td>
                </tr>
              ) : (
                rows.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/60">
                    <td className="px-3 py-2 font-mono text-xs text-slate-800 dark:text-slate-100">{r.id}</td>
                    <td className="px-3 py-2 font-mono text-xs">{r.order_id}</td>
                    <td className="px-3 py-2 font-mono text-xs">{r.locker_id}</td>
                    <td className="px-3 py-2">{r.slot}</td>
                    <td className="px-3 py-2">{r.state}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
