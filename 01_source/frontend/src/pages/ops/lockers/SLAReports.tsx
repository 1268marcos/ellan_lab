import { useCallback, useEffect, useState } from 'react'
import { lockersOpsApi, type NocAlert } from '../../../api/lockersOps'

export default function SLAReports() {
  const [sla, setSla] = useState<NocAlert[]>([])
  const [err, setErr] = useState<string | null>(null)

  const load = useCallback(async () => {
    setErr(null)
    try {
      const { data } = await lockersOpsApi.getAlerts({ alert_type: 'SLA_BREACH', limit: 500 })
      setSla(data.items ?? [])
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  const open = sla.filter((a) => !a.resolved_at)

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <h1 className="text-2xl font-semibold text-slate-100">SLA Reports</h1>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
          <p className="text-xs text-slate-400">Breaches (7d)</p>
          <p className="text-3xl font-bold text-slate-100">{sla.length}</p>
        </div>
        <div className="rounded-xl border border-rose-900/50 bg-rose-950/30 p-4">
          <p className="text-xs text-rose-300">Abertos</p>
          <p className="text-3xl font-bold text-rose-100">{open.length}</p>
        </div>
        <div className="rounded-xl border border-emerald-900/50 bg-emerald-950/30 p-4">
          <p className="text-xs text-emerald-300">Resolvidos</p>
          <p className="text-3xl font-bold text-emerald-100">{sla.length - open.length}</p>
        </div>
      </div>
      <table className="w-full text-sm text-slate-200">
        <thead className="bg-slate-800 text-xs uppercase text-slate-400">
          <tr>
            <th className="px-3 py-2">Severidade</th>
            <th className="px-3 py-2">Locker</th>
            <th className="px-3 py-2">Tipo</th>
            <th className="px-3 py-2">Detectado</th>
          </tr>
        </thead>
        <tbody>
          {sla.map((a) => (
            <tr key={a.alert_id} className="border-t border-slate-800">
              <td className="px-3 py-2">{a.severity}</td>
              <td className="px-3 py-2">{a.locker_display_name}</td>
              <td className="px-3 py-2">{a.breach_type}</td>
              <td className="px-3 py-2">{new Date(a.detected_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
