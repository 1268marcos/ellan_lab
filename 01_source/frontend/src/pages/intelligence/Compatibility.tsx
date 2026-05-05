import { useState } from 'react'
import { api } from '../../api/client'

type CompatibilityResult = {
  compatible?: boolean
  reason?: string
  recommended_slot_size?: string | null
}

export default function Compatibility() {
  const [sku, setSku] = useState('')
  const [lockerId, setLockerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CompatibilityResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function check(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const { data } = await api.post<CompatibilityResult>('/v1/products/check-compatibility', {
        product_sku: sku.trim(),
        locker_id: lockerId.trim(),
      })
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao verificar compatibilidade')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Compatibilidade</h1>
      <form onSubmit={check} className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <label className="block text-xs text-gray-600 dark:text-slate-400">
          Product SKU
          <input
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            required
          />
        </label>
        <label className="mt-3 block text-xs text-gray-600 dark:text-slate-400">
          Locker ID
          <input
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-2 py-2 text-sm dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            required
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="mt-4 rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Verificando...' : 'Verificar compatibilidade'}
        </button>
      </form>

      {error && <p className="text-sm text-red-500">{error}</p>}
      {result && (
        <div className={`rounded-xl border p-4 ${result.compatible ? 'border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/20' : 'border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/20'}`}>
          <p className="text-sm font-semibold">
            {result.compatible ? 'Compatível' : 'Incompatível'}
          </p>
          {result.reason && <p className="mt-1 text-xs text-gray-600 dark:text-slate-300">{result.reason}</p>}
          {result.recommended_slot_size && (
            <p className="mt-1 text-xs text-gray-600 dark:text-slate-300">
              Slot recomendado: {result.recommended_slot_size}
            </p>
          )}
        </div>
      )}
    </div>
  )
}

