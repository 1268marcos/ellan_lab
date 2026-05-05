import { useState } from 'react'
import { partnersApi } from '../api/partners'

export function CompatibilityChecker({ partnerId }: { partnerId: string }) {
  const [sku, setSku] = useState('')
  const [lockerId, setLockerId] = useState('')
  const [loading, setLoading] = useState(false)
  const [ok, setOk] = useState<boolean | null>(null)
  const [reason, setReason] = useState<string | null>(null)
  const [slot, setSlot] = useState<string | null>(null)

  async function run() {
    setLoading(true)
    setOk(null)
    setReason(null)
    setSlot(null)
    try {
      const { data } = await partnersApi.checkCompatibility(partnerId, sku.trim(), lockerId.trim())
      setOk(data.compatible)
      setReason(data.reason ?? null)
      setSlot(data.recommended_slot_size ?? null)
    } catch {
      setOk(false)
      setReason('Erro na chamada ao serviço')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
      <h3 className="text-sm font-semibold text-slate-200">Compatibilidade produto × locker</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block text-xs text-slate-400">
          Partner SKU
          <input
            value={sku}
            onChange={(e) => setSku(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
            placeholder="SKU parceiro"
          />
        </label>
        <label className="block text-xs text-slate-400">
          Locker ID
          <input
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
            placeholder="BR-XXX-LK-001"
          />
        </label>
      </div>
      <button
        type="button"
        disabled={loading || !sku.trim() || !lockerId.trim()}
        onClick={run}
        className="mt-3 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
      >
        {loading ? 'Verificando…' : 'Verificar'}
      </button>
      {ok !== null && (
        <div
          className={`mt-4 rounded-lg border px-3 py-2 text-sm ${
            ok
              ? 'border-emerald-700 bg-emerald-950/50 text-emerald-200'
              : 'border-red-800 bg-red-950/40 text-red-200'
          }`}
        >
          <p className="font-medium">{ok ? 'Compatível' : 'Incompatível'}</p>
          {reason && <p className="mt-1 text-xs opacity-90">{reason}</p>}
          {slot && <p className="mt-1 text-xs">Slot sugerido: {slot}</p>}
        </div>
      )}
    </div>
  )
}
