import type { Locker } from '../types'
import { useEffect, useState } from 'react'
import { opsApi } from '../api/ops'

function cellColor(o: number): string {
  if (o < 0.3) return 'bg-emerald-600/90'
  if (o < 0.7) return 'bg-amber-500/90'
  return 'bg-red-600/90'
}

export function LockerMap({ lockers }: { lockers: Locker[] }) {
  const [occupancyByLocker, setOccupancyByLocker] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    if (lockers.length === 0) {
      setOccupancyByLocker({})
      return
    }
    setLoading(true)
    setError(null)
    ;(async () => {
      try {
        const entries = await Promise.all(
          lockers.map(async (lk) => {
            const { data } = await opsApi.getLockerOccupancy(lk.id)
            const raw = data.occupancy ?? data.occupied_ratio ?? data.occupancy_ratio ?? lk.occupancy
            const value = raw > 1 ? raw / 100 : raw
            return [lk.id, Math.max(0, Math.min(1, Number(value) || 0))] as const
          }),
        )
        if (!cancelled) {
          setOccupancyByLocker(Object.fromEntries(entries))
        }
      } catch {
        if (!cancelled) setError('Falha ao carregar ocupação por locker')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [lockers])

  const cells = Array.from({ length: 16 }, (_, i) => lockers[i] ?? null)

  return (
    <>
      <div className="grid grid-cols-4 gap-2 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
        {cells.map((lk, idx) => {
          const occupancy = lk ? occupancyByLocker[lk.id] ?? lk.occupancy : 0
          return (
            <div
              key={lk?.id ?? `empty-${idx}`}
              title={lk ? `${lk.id} · ${Math.round(occupancy * 100)}%` : '—'}
              className={`flex aspect-square items-center justify-center rounded text-xs font-medium text-white shadow-inner ${
                lk ? cellColor(occupancy) : 'bg-slate-800 text-slate-500'
              } ${lk?.status === 'maintenance' ? 'ring-2 ring-violet-400' : ''}`}
            >
              {lk ? `${Math.round(occupancy * 100)}%` : '·'}
            </div>
          )
        })}
      </div>
      {loading && <p className="mt-2 text-xs text-slate-500">Carregando ocupação dos lockers...</p>}
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </>
  )
}
