import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { walletApi, type BalanceOut, type TxRow } from '../../api/wallet'
import { BalanceCard } from '../../components/BalanceCard'
import { TransactionsTable } from '../../components/TransactionsTable'

const DEFAULT_ID =
  (typeof import.meta.env.VITE_WALLET_USER_ID === 'string' && import.meta.env.VITE_WALLET_USER_ID) ||
  'user-demo-001'

export default function Wallet() {
  const [partnerId, setPartnerId] = useState(DEFAULT_ID)
  const [balance, setBalance] = useState<BalanceOut | null>(null)
  const prevBal = useRef<number | null>(null)
  const [deltaPct, setDeltaPct] = useState<number | null>(null)
  const [txs, setTxs] = useState<TxRow[]>([])
  const [expired, setExpired] = useState<unknown>(null)
  const [amount, setAmount] = useState('1000')
  const [orderId, setOrderId] = useState('order-manual-1')
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState<string | null>(null)

  const load = useCallback(async () => {
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
      const { data } = await walletApi.getTransactions(partnerId, {})
      setTxs(Array.isArray(data) ? data : [])
    } catch {
      setTxs([])
    }
    try {
      const { data } = await walletApi.getExpiredCredits(partnerId)
      setExpired(data)
    } catch {
      setExpired(null)
    }
  }, [partnerId])

  useEffect(() => {
    prevBal.current = null
    setDeltaPct(null)
    void load()
  }, [partnerId, load])

  async function apply(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    setMsg(null)
    try {
      await walletApi.applyCredit(partnerId, Number(amount), orderId)
      setMsg('Crédito aplicado / oferta criada.')
      await load()
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
          <h1 className="text-2xl font-semibold text-white">Wallet</h1>
          <p className="text-sm text-slate-400">Saldo · transações · créditos expirados</p>
        </div>
        <Link to="/finance/reconcile" className="text-sm text-emerald-400 hover:underline">
          Reconciliação →
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

      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-200">Transações</h2>
        <TransactionsTable rows={txs} />
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Créditos expirados (JSON)</h2>
        <pre className="mt-2 max-h-40 overflow-auto rounded bg-slate-950 p-3 text-xs text-slate-400">
          {expired != null ? JSON.stringify(expired, null, 2) : '—'}
        </pre>
      </section>

      <form onSubmit={apply} className="space-y-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Aplicar crédito manual</h2>
        <input
          type="number"
          min={1}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          className="w-full max-w-xs rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
        />
        <input
          value={orderId}
          onChange={(e) => setOrderId(e.target.value)}
          placeholder="order_id"
          className="w-full max-w-md rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? 'Enviando…' : 'POST apply-credit'}
        </button>
        {msg && <p className="text-xs text-slate-400">{msg}</p>}
      </form>
    </div>
  )
}
