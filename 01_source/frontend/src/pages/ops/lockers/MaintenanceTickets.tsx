import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { lockersOpsApi, type MaintenanceTicket, type OpsLocker } from '../../../api/lockersOps'

const COLUMNS = ['OPEN', 'IN_PROGRESS', 'WAITING_PARTS', 'RESOLVED'] as const

export default function MaintenanceTickets() {
  const [lockers, setLockers] = useState<OpsLocker[]>([])
  const [byLocker, setByLocker] = useState<Record<string, MaintenanceTicket[]>>({})
  const [err, setErr] = useState<string | null>(null)

  const load = useCallback(async () => {
    setErr(null)
    try {
      const { data } = await lockersOpsApi.listLockers({ limit: 100 })
      const items = data.items ?? []
      setLockers(items)
      const map: Record<string, MaintenanceTicket[]> = {}
      await Promise.all(
        items.slice(0, 40).map(async (lk) => {
          const r = await lockersOpsApi.getMaintenance(lk.id)
          map[lk.id] = r.data.items ?? []
        }),
      )
      setByLocker(map)
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const allTickets = useMemo(() => Object.values(byLocker).flat(), [byLocker])

  const columnTickets = (status: string) =>
    allTickets.filter((t) => t.status === status)

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <h1 className="text-2xl font-semibold text-slate-100">Maintenance</h1>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      <button
        type="button"
        onClick={load}
        className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white"
      >
        Atualizar
      </button>
      <div className="grid gap-3 md:grid-cols-4">
        {COLUMNS.map((col) => (
          <div key={col} className="rounded-xl border border-slate-700 bg-slate-900/50 p-3">
            <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{col}</h2>
            <ul className="space-y-2">
              {columnTickets(col).map((t) => (
                <li key={t.id} className="rounded-lg border border-slate-600 bg-slate-800/80 p-2 text-sm">
                  <p className="font-medium text-slate-100">{t.title}</p>
                  <Link
                    to={`/ops/lockers/${t.locker_id}?tab=maintenance`}
                    className="text-xs text-indigo-300 hover:underline"
                  >
                    {t.locker_id.slice(0, 8)}…
                  </Link>
                  <p className="text-xs text-slate-500">{t.priority}</p>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <p className="text-xs text-slate-500">{lockers.length} lockers consultados</p>
    </div>
  )
}
