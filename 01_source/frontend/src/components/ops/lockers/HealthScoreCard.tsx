type Props = {
  score?: number | null
  status?: string | null
  lastTelemetryAt?: string | null
}

function tone(score?: number | null, status?: string | null) {
  if (status === 'CRITICO' || (score != null && score < 50)) {
    return { bar: 'bg-rose-500', text: 'text-rose-200', label: 'Crítico' }
  }
  if (status === 'ATENCAO' || (score != null && score < 80)) {
    return { bar: 'bg-amber-400', text: 'text-amber-100', label: 'Atenção' }
  }
  return { bar: 'bg-emerald-500', text: 'text-emerald-200', label: 'Saudável' }
}

export default function HealthScoreCard({ score, status, lastTelemetryAt }: Props) {
  const s = score != null && !Number.isNaN(Number(score)) ? Math.max(0, Math.min(100, Number(score))) : null
  const t = tone(s, status)

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Health score</p>
      <p className={`mt-2 text-3xl font-bold ${t.text}`}>{s != null ? s.toFixed(0) : '—'}</p>
      <p className="text-sm text-slate-400">{status ?? t.label}</p>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800">
        <div className={`h-full ${t.bar}`} style={{ width: `${s ?? 0}%` }} />
      </div>
      {lastTelemetryAt && (
        <p className="mt-2 text-xs text-slate-500">
          Última telemetria: {new Date(lastTelemetryAt).toLocaleString()}
        </p>
      )}
    </div>
  )
}
