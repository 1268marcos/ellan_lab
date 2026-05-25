import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { lockersOpsApi, type NocAlert } from '../../../api/lockersOps'
import { useOpsLockersWs } from '../../../hooks/useOpsLockersWs'

export default function NOCAlerts() {
  const [items, setItems] = useState<NocAlert[]>([])
  const [err, setErr] = useState<string | null>(null)

  const { payload: live, connected } = useOpsLockersWs<{
    type: string
    items: NocAlert[]
  }>({ path: '/ws/ops/alerts' })

  const load = useCallback(async () => {
    setErr(null)
    try {
      const { data } = await lockersOpsApi.getAlerts({ limit: 200 })
      setItems(data.items ?? [])
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (live?.type === 'alerts_critical' && live.items?.length) {
      setItems((prev) => {
        const ids = new Set(live.items.map((a) => a.alert_id))
        const rest = prev.filter((p) => !ids.has(p.alert_id))
        return [...live.items, ...rest].slice(0, 200)
      })
    }
  }, [live])

  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-100">NOC Alerts</h1>
        <span
          className={`rounded-full px-2 py-0.5 text-xs ${connected ? 'bg-emerald-500/20 text-emerald-200' : 'bg-slate-700 text-slate-400'}`}
        >
          {connected ? 'Live' : 'Offline'}
        </span>
      </div>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      <ul className="space-y-2">
        {items.map((a) => (
          <li
            key={`${a.alert_type}-${a.alert_id}`}
            className="rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-3"
          >
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-rose-500/20 px-2 py-0.5 text-xs font-semibold text-rose-200">
                {a.severity}
              </span>
              <span className="text-xs text-slate-400">{a.alert_type}</span>
              <span className="text-xs text-slate-500">
                {new Date(a.detected_at).toLocaleString()}
              </span>
            </div>
            <p className="mt-1 font-medium text-slate-100">{a.locker_display_name ?? a.reference_id}</p>
            <p className="text-sm text-slate-400">{a.breach_type}</p>
            {a.reference_id && (
              <Link
                to={`/ops/lockers/${a.reference_id}`}
                className="mt-1 inline-block text-xs text-indigo-300 hover:underline"
              >
                Ver locker
              </Link>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
