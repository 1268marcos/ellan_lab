import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import {
  lockersOpsApi,
  type MaintenanceTicket,
  type OpsLocker,
  type TelemetryPoint,
} from '../../../api/lockersOps'
import HealthScoreCard from '../../../components/ops/lockers/HealthScoreCard'
import OccupancyGauge from '../../../components/ops/lockers/OccupancyGauge'
import TelemetryChart from '../../../components/ops/lockers/TelemetryChart'
import { useOpsLockersWs } from '../../../hooks/useOpsLockersWs'

const TABS = ['overview', 'telemetry', 'maintenance', 'pickups'] as const

export default function LockerDetail() {
  const { id = '' } = useParams()
  const [search, setSearch] = useSearchParams()
  const tab = (TABS.includes(search.get('tab') as (typeof TABS)[number])
    ? search.get('tab')
    : 'overview') as (typeof TABS)[number]

  const [locker, setLocker] = useState<OpsLocker | null>(null)
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([])
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([])
  const [pickups, setPickups] = useState<Record<string, unknown>[]>([])
  const [err, setErr] = useState<string | null>(null)
  const [title, setTitle] = useState('')
  const [desc, setDesc] = useState('')

  const { payload: live } = useOpsLockersWs<{
    items: { locker_id: string; battery_pct?: number; temperature_celsius?: number; occurred_at: string }[]
  }>({ path: '/ws/ops/realtime', subscribeLockerIds: id ? [id] : [], enabled: !!id })

  const load = useCallback(async () => {
    if (!id) return
    setErr(null)
    try {
      const [lk, tel, maint, pick] = await Promise.all([
        lockersOpsApi.getLocker(id),
        lockersOpsApi.getTelemetry(id, 48),
        lockersOpsApi.getMaintenance(id),
        lockersOpsApi.getPickups(id),
      ])
      setLocker(lk.data)
      setTelemetry(tel.data.items ?? [])
      setTickets(maint.data.items ?? [])
      setPickups(pick.data.items ?? [])
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro')
    }
  }, [id])

  useEffect(() => {
    load()
  }, [load])

  const setTab = (t: (typeof TABS)[number]) => {
    const next = new URLSearchParams(search)
    next.set('tab', t)
    setSearch(next)
  }

  const createTicket = async () => {
    if (!title.trim() || !id) return
    await lockersOpsApi.createMaintenance(id, { title: title.trim(), description: desc || undefined })
    setTitle('')
    setDesc('')
    const { data } = await lockersOpsApi.getMaintenance(id)
    setTickets(data.items ?? [])
  }

  const livePoint = live?.items?.find((i) => i.locker_id === id)

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4">
      <Link to="/ops/lockers/map" className="text-sm text-indigo-300 hover:underline">
        ← Mapa
      </Link>
      <h1 className="text-2xl font-semibold text-slate-100">{locker?.display_name ?? id}</h1>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              tab === t ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>
      {tab === 'overview' && locker && (
        <div className="grid gap-4 md:grid-cols-2">
          <HealthScoreCard
            score={locker.health_score}
            status={locker.health_status}
            lastTelemetryAt={locker.last_telemetry_at}
          />
          <OccupancyGauge pct={locker.occupancy_pct} level={locker.occupancy_level} />
          <div className="md:col-span-2 rounded-xl border border-slate-700 bg-slate-900/60 p-4 text-sm text-slate-300">
            <p>{locker.address_line}</p>
            <p>
              {locker.city} · {locker.region}
            </p>
            {livePoint && (
              <p className="mt-2 text-emerald-300">
                Live: {livePoint.temperature_celsius ?? '—'}°C · bateria{' '}
                {livePoint.battery_pct ?? '—'}%
              </p>
            )}
          </div>
        </div>
      )}
      {tab === 'telemetry' && <TelemetryChart points={telemetry} hours={48} />}
      {tab === 'maintenance' && (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <input
              className="flex-1 rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              placeholder="Título do ticket"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
            <input
              className="flex-[2] rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              placeholder="Descrição"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
            />
            <button
              type="button"
              onClick={createTicket}
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white"
            >
              Abrir ticket
            </button>
          </div>
          <ul className="space-y-2">
            {tickets.map((t) => (
              <li key={t.id} className="rounded-lg border border-slate-700 bg-slate-900/80 px-3 py-2 text-sm">
                <span className="font-medium text-slate-100">{t.title}</span>
                <span className="ml-2 text-xs text-slate-400">
                  {t.status} · {t.priority}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {tab === 'pickups' && (
        <table className="w-full text-sm text-slate-200">
          <thead className="bg-slate-800 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-3 py-2">Order</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Slot</th>
              <th className="px-3 py-2">Deadline</th>
            </tr>
          </thead>
          <tbody>
            {pickups.map((p) => (
              <tr key={String(p.order_id)} className="border-t border-slate-800">
                <td className="px-3 py-2 font-mono text-xs">{String(p.order_id)}</td>
                <td className="px-3 py-2">{String(p.status)}</td>
                <td className="px-3 py-2">{String(p.slot_label ?? '—')}</td>
                <td className="px-3 py-2">
                  {p.pickup_deadline_at
                    ? new Date(String(p.pickup_deadline_at)).toLocaleString()
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}
