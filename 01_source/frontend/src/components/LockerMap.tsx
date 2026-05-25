import type { Locker } from '../types'

function cellColor(o: number): string {
  if (o < 0.3) return 'bg-emerald-600/90'
  if (o < 0.7) return 'bg-amber-500/90'
  return 'bg-red-600/90'
}

export function LockerMap({ lockers }: { lockers: Locker[] }) {
  const cells = Array.from({ length: 16 }, (_, i) => lockers[i] ?? null)

  return (
    <>
      <div className="grid grid-cols-4 gap-2 rounded-lg border border-slate-700 bg-slate-900/80 p-3">
        {cells.map((lk, idx) => {
          const raw = lk ? Number(lk.occupancy) : 0
          const occupancy = raw > 1 ? raw / 100 : raw
          const safe = Math.max(0, Math.min(1, occupancy))
          return (
            <div
              key={lk?.id ?? `empty-${idx}`}
              title={lk ? `${lk.id} · ${Math.round(safe * 100)}%` : '—'}
              className={`flex aspect-square items-center justify-center rounded text-xs font-medium text-white shadow-inner ${
                lk ? cellColor(safe) : 'bg-slate-800 text-slate-500'
              } ${lk?.status === 'maintenance' ? 'ring-2 ring-violet-400' : ''}`}
            >
              {lk ? `${Math.round(safe * 100)}%` : '·'}
            </div>
          )
        })}
      </div>
    </>
  )
}
