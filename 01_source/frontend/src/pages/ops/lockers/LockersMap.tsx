import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { lockersOpsApi, type OpsLocker } from '../../../api/lockersOps'
import { useOpsLockersWs } from '../../../hooks/useOpsLockersWs'

const markerColors: Record<string, string> = {
  healthy: '#22c55e',
  warning: '#f59e0b',
  critical: '#ef4444',
  offline: '#64748b',
  unknown: '#94a3b8',
}

function markerIcon(status?: string) {
  const c = markerColors[status ?? 'unknown'] ?? markerColors.unknown
  return L.divIcon({
    className: '',
    html: `<span style="display:block;width:14px;height:14px;border-radius:50%;background:${c};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4)"></span>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

export default function LockersMap() {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInst = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)
  const [rows, setRows] = useState<OpsLocker[]>([])
  const [region, setRegion] = useState('')
  const [q, setQ] = useState('')
  const [err, setErr] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const { payload: live } = useOpsLockersWs<{
    type: string
    items: { locker_id: string; battery_pct?: number; temperature_celsius?: number }[]
  }>({ path: '/ws/ops/realtime' })

  const load = useCallback(async () => {
    setLoading(true)
    setErr(null)
    try {
      const params: Record<string, string> = {}
      if (region) params.region = region
      if (q) params.q = q
      const { data } = await lockersOpsApi.listLockers(params)
      setRows(data.items ?? [])
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : 'Erro ao carregar')
    } finally {
      setLoading(false)
    }
  }, [region, q])

  useEffect(() => {
    load()
  }, [load])

  const withCoords = useMemo(
    () => rows.filter((r) => r.latitude != null && r.longitude != null),
    [rows],
  )

  useEffect(() => {
    if (!mapRef.current || !withCoords.length) return undefined
    if (mapInst.current) {
      mapInst.current.remove()
      mapInst.current = null
    }
    const lats = withCoords.map((r) => r.latitude!)
    const lons = withCoords.map((r) => r.longitude!)
    const map = L.map(mapRef.current).setView(
      [(Math.min(...lats) + Math.max(...lats)) / 2, (Math.min(...lons) + Math.max(...lons)) / 2],
      11,
    )
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
    }).addTo(map)
    const layer = L.layerGroup().addTo(map)
    withCoords.forEach((lk) => {
      const m = L.marker([lk.latitude!, lk.longitude!], {
        icon: markerIcon(lk.ops_status),
      }).bindPopup(
        `<strong>${lk.display_name ?? lk.id}</strong><br/>${lk.city ?? ''}<br/><a href="/v1/ops/lockers/${lk.id}">Detalhe</a>`,
      )
      layer.addLayer(m)
    })
    map.fitBounds(
      L.latLngBounds(withCoords.map((r) => [r.latitude!, r.longitude!] as [number, number])),
      { padding: [24, 24] },
    )
    mapInst.current = map
    layerRef.current = layer
    return () => {
      map.remove()
      mapInst.current = null
    }
  }, [withCoords])

  const liveCount = live?.items?.length ?? 0

  return (
    <div className="mx-auto max-w-7xl space-y-4 p-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Lockers Map</h1>
          <p className="text-sm text-slate-400">
            {withCoords.length} no mapa · {liveCount} telemetrias live
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/ops/maintenance"
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            Manutenção
          </Link>
          <Link
            to="/ops/noc-alerts"
            className="rounded-lg border border-slate-600 px-3 py-2 text-sm text-slate-200 hover:bg-slate-800"
          >
            NOC Alerts
          </Link>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        <input
          className="rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
          placeholder="Região"
          value={region}
          onChange={(e) => setRegion(e.target.value)}
        />
        <input
          className="min-w-[200px] rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100"
          placeholder="Buscar"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <button
          type="button"
          onClick={load}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Filtrar
        </button>
      </div>
      {err && <p className="text-sm text-rose-400">{err}</p>}
      {loading && <p className="text-sm text-slate-400">Carregando…</p>}
      <div ref={mapRef} className="h-[520px] w-full rounded-xl border border-slate-700" />
      <div className="overflow-x-auto rounded-xl border border-slate-700">
        <table className="w-full text-left text-sm text-slate-200">
          <thead className="bg-slate-800 text-xs uppercase text-slate-400">
            <tr>
              <th className="px-3 py-2">Locker</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Ocupação</th>
              <th className="px-3 py-2">Health</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-slate-800">
                <td className="px-3 py-2">
                  <Link className="text-indigo-300 hover:underline" to={`/ops/lockers/${r.id}`}>
                    {r.display_name ?? r.id}
                  </Link>
                </td>
                <td className="px-3 py-2">{r.ops_status}</td>
                <td className="px-3 py-2">
                  {r.occupancy_pct != null ? `${Number(r.occupancy_pct).toFixed(1)}%` : '—'}
                </td>
                <td className="px-3 py-2">{r.health_score != null ? r.health_score.toFixed(0) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
