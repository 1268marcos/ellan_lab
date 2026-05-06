import { useEffect, useMemo, useState } from 'react'
import { partnersApi, type ActivePickupItem } from '../../api/partners'
import { useAuth } from '../../contexts/AuthContext'

type PickupView = ActivePickupItem & {
  flow_status: 'ACTIVE' | 'IN_PROGRESS'
  remaining_label: string
}

function toRemainingLabel(expiresAt?: string | null): string {
  if (!expiresAt) return 'Sem prazo'
  const expires = new Date(expiresAt).getTime()
  if (Number.isNaN(expires)) return 'Sem prazo'
  const diffMs = expires - Date.now()
  if (diffMs <= 0) return 'Expirado'
  const totalMinutes = Math.floor(diffMs / 60000)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

function normalizeStatus(item: ActivePickupItem): 'ACTIVE' | 'IN_PROGRESS' {
  const stage = String(item.lifecycle_stage || '').toUpperCase()
  if (stage === 'DOOR_OPENED' || stage === 'ITEM_REMOVED' || stage === 'DOOR_CLOSED') {
    return 'IN_PROGRESS'
  }
  return 'ACTIVE'
}

export default function OpsPickupFlow() {
  const { auth } = useAuth()
  const partnerId = auth?.partnerId || (import.meta.env.VITE_PARTNER_ID as string) || ''
  const [items, setItems] = useState<PickupView[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)

  async function load() {
    if (!partnerId) {
      setItems([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const { data } = await partnersApi.getActivePickups(partnerId, 100)
      const normalized = (data.items || []).map((item) => ({
        ...item,
        flow_status: normalizeStatus(item),
        remaining_label: toRemainingLabel(item.expires_at),
      }))
      setItems(normalized)
      setLastUpdated(new Date().toLocaleTimeString('pt-BR'))
    } catch (err: unknown) {
      setItems([])
      setError(err instanceof Error ? err.message : 'Erro ao carregar pickups.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    const timer = window.setInterval(() => {
      void load()
    }, 30000)
    return () => window.clearInterval(timer)
  }, [partnerId])

  const counters = useMemo(() => {
    const active = items.filter((item) => item.flow_status === 'ACTIVE').length
    const inProgress = items.filter((item) => item.flow_status === 'IN_PROGRESS').length
    return { active, inProgress, total: items.length }
  }, [items])

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Operacional · Pickups</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Fluxo ativo com refresh automatico a cada 30 segundos.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {lastUpdated && (
            <span className="rounded-md bg-slate-100 px-2 py-1 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              Atualizado {lastUpdated}
            </span>
          )}
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
          >
            {loading ? 'Atualizando...' : 'Atualizar'}
          </button>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900/60">
          <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Total</p>
          <p className="mt-1 text-2xl font-semibold text-slate-900 dark:text-slate-100">{counters.total}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900/40 dark:bg-emerald-950/40">
          <p className="text-xs uppercase tracking-wide text-emerald-700 dark:text-emerald-300">ACTIVE</p>
          <p className="mt-1 text-2xl font-semibold text-emerald-700 dark:text-emerald-300">{counters.active}</p>
        </div>
        <div className="rounded-xl border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900/40 dark:bg-yellow-950/40">
          <p className="text-xs uppercase tracking-wide text-yellow-700 dark:text-yellow-300">IN_PROGRESS</p>
          <p className="mt-1 text-2xl font-semibold text-yellow-700 dark:text-yellow-300">{counters.inProgress}</p>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          Carregando pickups ativos...
        </div>
      )}

      {!loading && items.length === 0 && !error && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          Nenhum pickup ativo no momento.
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900/60">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500 dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-400">
              <tr>
                <th className="px-3 py-2">Pickup</th>
                <th className="px-3 py-2">Order</th>
                <th className="px-3 py-2">Locker</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Tempo restante</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.pickup_id} className="border-b border-slate-100 dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs text-slate-700 dark:text-slate-300">{item.pickup_id}</td>
                  <td className="px-3 py-2 font-mono text-xs text-slate-700 dark:text-slate-300">{item.order_id}</td>
                  <td className="px-3 py-2 text-slate-700 dark:text-slate-300">
                    {item.locker_id || '-'} {item.slot ? `· Slot ${item.slot}` : ''}
                  </td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-semibold ${
                        item.flow_status === 'IN_PROGRESS'
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
                          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300'
                      }`}
                    >
                      {item.flow_status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-700 dark:text-slate-300">{item.remaining_label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
