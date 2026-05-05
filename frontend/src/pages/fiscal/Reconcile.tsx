import { useState } from 'react'
import { api } from '../../api/client'

export default function Reconcile() {
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<unknown>(null)
  const [error, setError] = useState<string | null>(null)

  async function run() {
    setRunning(true)
    setError(null)
    try {
      const { data } = await api.post('/v1/wallet/reconcile')
      setResult(data)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha na reconciliação')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Reconciliação Fiscal</h1>
      <button
        type="button"
        onClick={() => void run()}
        disabled={running}
        className="rounded bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 disabled:opacity-50"
      >
        {running ? 'Executando...' : 'Executar reconciliação'}
      </button>
      {error && <p className="text-sm text-red-500">{error}</p>}
      <pre className="rounded-xl border border-gray-200 bg-white p-4 text-xs text-gray-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">
        {result ? JSON.stringify(result, null, 2) : 'Sem execução'}
      </pre>
    </div>
  )
}

