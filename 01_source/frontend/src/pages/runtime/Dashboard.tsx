import { useCallback, useEffect, useState } from 'react'

import { runtimeApi, type InventoryRuntimeResponse } from '../../api/runtime'
import { useAuth } from '../../AuthContext'

export default function RuntimeDashboard() {
  const { auth } = useAuth()
  const partnerId = auth?.partnerId ?? ''

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [payload, setPayload] = useState<InventoryRuntimeResponse | null>(null)

  const load = useCallback(async () => {
    if (!partnerId) {
      setError('Sessão sem partnerId.')
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await runtimeApi.getRuntimeInventory(partnerId)
      setPayload(data)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Falha ao carregar inventário runtime.'
      setError(msg)
      setPayload(null)
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="space-y-6 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">Runtime / Slots</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Inventário operacional (BFF). Parceiro: <span className="font-mono text-xs">{partnerId || '—'}</span>
          </p>
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
          Carregando dados do runtime…
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <p className="font-medium">Erro</p>
          <p className="mt-1">{error}</p>
        </div>
      )}

      {payload && (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Resumo</h2>
            <dl className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <div className="flex justify-between">
                <dt>Lockers</dt>
                <dd className="font-mono">{payload.data?.lockers.length ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Linhas de slots</dt>
                <dd className="font-mono">{payload.data?.occupancy.total_runtime_slot_rows ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Slots runtime ativos</dt>
                <dd className="font-mono">{payload.data?.occupancy.active_runtime_slots ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Catálogo disponível</dt>
                <dd className="font-mono">{payload.data?.occupancy.catalog_available_slots ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Resposta em cache (BFF)</dt>
                <dd className="font-mono">{payload.cached ? 'sim' : 'não'}</dd>
              </div>
            </dl>
          </div>
          <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="text-sm font-semibold text-slate-700 dark:text-slate-200">Meta</h2>
            <pre className="mt-2 max-h-48 overflow-auto rounded bg-slate-50 p-2 text-xs text-slate-700 dark:bg-slate-800 dark:text-slate-200">
              {JSON.stringify(payload.meta, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
