import { useEffect, useState } from 'react'
import { api } from '../../api/client'

type Locker = {
  id: string
  status?: string
  occupancy?: number
}

export default function Lockers() {
  const [rows, setRows] = useState<Locker[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const { data } = await api.get<Locker[]>('/v1/inventory/lockers')
        if (!cancelled) setRows(Array.isArray(data) ? data : [])
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Erro ao carregar lockers')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Lockers</h1>
      {loading && <p className="text-sm text-gray-500 dark:text-slate-400">Carregando...</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-slate-700 dark:bg-slate-900">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500 dark:bg-slate-800 dark:text-slate-400">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Ocupação</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ? (
              <tr>
                <td className="px-3 py-8 text-center text-gray-500 dark:text-slate-400" colSpan={3}>
                  Sem dados
                </td>
              </tr>
            ) : (
              rows.map((l) => (
                <tr key={l.id} className="border-t border-gray-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs">{l.id}</td>
                  <td className="px-3 py-2">{l.status ?? '—'}</td>
                  <td className="px-3 py-2">{typeof l.occupancy === 'number' ? `${(l.occupancy > 1 ? l.occupancy : l.occupancy * 100).toFixed(1)}%` : '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

