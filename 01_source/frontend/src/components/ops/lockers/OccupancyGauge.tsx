type Props = {
  pct?: number | null
  level?: string | null
  label?: string
}

function tone(level?: string | null, pct?: number | null) {
  const p = pct ?? 0
  if (level === 'HIGH' || p >= 80) return { ring: 'stroke-rose-500', text: 'text-rose-300', bg: 'bg-rose-500/20' }
  if (level === 'MEDIUM' || p >= 50) return { ring: 'stroke-amber-400', text: 'text-amber-200', bg: 'bg-amber-500/20' }
  return { ring: 'stroke-emerald-400', text: 'text-emerald-200', bg: 'bg-emerald-500/20' }
}

export default function OccupancyGauge({ pct, level, label = 'Ocupação' }: Props) {
  const value = pct != null && !Number.isNaN(Number(pct)) ? Math.max(0, Math.min(100, Number(pct))) : null
  const t = tone(level, value)
  const r = 44
  const c = 2 * Math.PI * r
  const dash = value != null ? (value / 100) * c : 0

  return (
    <div className={`rounded-xl border border-slate-700 p-4 ${t.bg}`}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <div className="mt-3 flex items-center gap-4">
        <svg width="100" height="100" className="-rotate-90">
          <circle cx="50" cy="50" r={r} fill="none" stroke="#1e293b" strokeWidth="10" />
          <circle
            cx="50"
            cy="50"
            r={r}
            fill="none"
            className={t.ring}
            strokeWidth="10"
            strokeDasharray={`${dash} ${c}`}
            strokeLinecap="round"
          />
        </svg>
        <div>
          <p className={`text-3xl font-bold ${t.text}`}>{value != null ? `${value.toFixed(1)}%` : '—'}</p>
          <p className="text-sm text-slate-400">{level ?? 'N/D'}</p>
        </div>
      </div>
    </div>
  )
}
