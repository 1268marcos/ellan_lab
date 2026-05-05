export function BalanceCard({
  label,
  balanceCents,
  pctChange,
}: {
  label: string
  balanceCents: number
  pctChange?: number | null
}) {
  const brl = (balanceCents / 100).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
  const arrow = pctChange == null ? '' : pctChange >= 0 ? '↑' : '↓'
  const pct =
    pctChange == null
      ? null
      : `${arrow} ${Math.abs(pctChange).toFixed(2)}%`

  return (
    <div className="rounded-xl border border-slate-700 bg-gradient-to-br from-slate-900 to-slate-950 p-6 shadow-lg">
      <div className="flex items-center gap-2">
        <span className="text-lg">💼</span>
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      </div>
      <p className="mt-2 text-3xl font-bold tabular-nums text-white">{brl}</p>
      {pct != null && (
        <p className={`mt-2 text-sm font-medium ${pctChange! >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{pct}</p>
      )}
    </div>
  )
}
