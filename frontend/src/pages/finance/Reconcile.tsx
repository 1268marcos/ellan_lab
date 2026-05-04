import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { walletApi } from '../../api/wallet'

export default function Reconcile() {
  const [divs, setDivs] = useState<unknown>(null)
  const [hist, setHist] = useState<unknown>(null)
  const [rep, setRep] = useState<unknown>(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    try {
      const { data } = await walletApi.getDivergences()
      setDivs(data)
    } catch {
      setDivs([])
    }
    try {
      const { data } = await walletApi.getReconcileHistory()
      setHist(data)
    } catch {
      setHist([])
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function runReconcile() {
    setBusy(true)
    setMsg(null)
    try {
      const { data } = await walletApi.reconcile()
      setRep(data)
      setMsg('Reconciliação executada.')
      await refresh()
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : 'Erro')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Reconciliação</h1>
          <p className="text-sm text-slate-400">Job manual · divergências · histórico</p>
        </div>
        <Link to="/finance/wallet" className="text-sm text-emerald-400 hover:underline">
          ← Wallet
        </Link>
      </div>

      <button
        type="button"
        disabled={busy}
        onClick={runReconcile}
        className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
      >
        {busy ? 'Executando…' : 'POST /wallet/reconcile'}
      </button>
      {msg && <p className="text-sm text-slate-400">{msg}</p>}

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Relatório (última execução)</h2>
        <pre className="mt-2 max-h-48 overflow-auto text-xs text-slate-400">
          {rep != null ? JSON.stringify(rep, null, 2) : '—'}
        </pre>
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Divergências</h2>
        <pre className="mt-2 max-h-48 overflow-auto text-xs text-slate-400">
          {JSON.stringify(divs, null, 2)}
        </pre>
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Histórico</h2>
        <pre className="mt-2 max-h-48 overflow-auto text-xs text-slate-400">
          {JSON.stringify(hist, null, 2)}
        </pre>
      </section>
    </div>
  )
}
