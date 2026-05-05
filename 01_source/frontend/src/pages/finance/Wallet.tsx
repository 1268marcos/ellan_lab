import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { walletApi, type BalanceOut, type DivergenceRow } from '../../api/wallet'
import { BalanceCard } from '../../components/BalanceCard'

const DEFAULT_ID =
  (typeof import.meta.env.VITE_WALLET_USER_ID === 'string' && import.meta.env.VITE_WALLET_USER_ID) ||
  'user-demo-001'

export default function Wallet() {
  const [partnerId, setPartnerId] = useState(DEFAULT_ID)
  const [balance, setBalance] = useState<BalanceOut | null>(null)
  const prevBal = useRef<number | null>(null)
  const [deltaPct, setDeltaPct] = useState<number | null>(null)
  const [expired, setExpired] = useState<unknown>(null)
  const [divergences, setDivergences] = useState<DivergenceRow[]>([])
  const [loading, setLoading] = useState(false)
  const [reconcileBusy, setReconcileBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setMsg(null)
    try {
      const { data } = await walletApi.getBalance(partnerId)
      const b = data.balance ?? 0
      const prev = prevBal.current
      if (prev != null && prev !== 0) setDeltaPct(((b - prev) / Math.abs(prev)) * 100)
      else setDeltaPct(null)
      prevBal.current = b
      setBalance({ ...data, balance: b })
    } catch {
      setBalance({ balance: 0, version: 0 })
      setDeltaPct(null)
    }
    try {
      const { data } = await walletApi.getExpiredCredits(partnerId)
      setExpired(data)
    } catch {
      setExpired(null)
    }
    try {
      const { data } = await walletApi.getDivergences()
      setDivergences(Array.isArray(data) ? data : [])
    } catch {
      setDivergences([])
    } finally {
      setLoading(false)
    }
  }, [partnerId])

  useEffect(() => {
    prevBal.current = null
    setDeltaPct(null)
    void load()
  }, [partnerId, load])

  const maxDivergence = divergences.reduce((acc, row) => {
    const raw = row.divergence_percent ?? row.percent ?? row.divergence_ratio ?? 0
    const percent = raw > 1 ? raw : raw * 100
    return Math.max(acc, percent)
  }, 0)

  async function runReconcile() {
    setReconcileBusy(true)
    setMsg(null)
    try {
      await walletApi.reconcile()
      setMsg('Reconciliação manual executada.')
      await load()
    } catch (err: unknown) {
      setMsg(err instanceof Error ? err.message : 'Falha ao reconciliar')
    } finally {
      setReconcileBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Wallet</h1>
          <p className="text-sm text-slate-400">Saldo · créditos expirados · reconciliação manual</p>
        </div>
        <Link to="/finance/transactions" className="text-sm text-emerald-400 hover:underline">
          Ver transações →
        </Link>
      </div>

      <label className="block max-w-xl text-xs text-slate-400">
        Parceiro / user_id
        <input
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value.trim())}
          onBlur={() => void load()}
          className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 font-mono text-sm text-white"
        />
      </label>

      {balance && <BalanceCard label="Saldo" balanceCents={balance.balance} pctChange={deltaPct} />}

      {loading && <p className="text-sm text-slate-400">Carregando painel financeiro...</p>}

      {maxDivergence > 0.01 && (
        <div className="rounded border border-red-800 bg-red-950/30 px-3 py-2 text-sm text-red-300">
          Alerta: divergência acima de 0.01% detectada ({maxDivergence.toFixed(4)}%).
        </div>
      )}

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Créditos expirados (JSON)</h2>
        <pre className="mt-2 max-h-40 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-400">
          {expired != null ? JSON.stringify(expired, null, 2) : '—'}
        </pre>
      </section>

      <section className="space-y-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Reconciliação manual (admin)</h2>
        <button
          type="button"
          onClick={() => void runReconcile()}
          disabled={reconcileBusy}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {reconcileBusy ? 'Executando...' : 'POST /api/v1/wallet/reconcile'}
        </button>
        {msg && <p className="text-xs text-slate-400">{msg}</p>}
      </section>
    </div>
  )
}
