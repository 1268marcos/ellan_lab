import type { LockerRoiRow } from '../../api/financialExecutive'

const VIABILITY_STYLES: Record<string, string> = {
  HIGH_PERFORMANCE: 'border-emerald-500/50 bg-emerald-950/40 text-emerald-200',
  MODERATE: 'border-sky-500/50 bg-sky-950/40 text-sky-200',
  LOW_PERFORMANCE: 'border-amber-500/50 bg-amber-950/40 text-amber-200',
  UNDERPERFORMING: 'border-orange-500/50 bg-orange-950/40 text-orange-200',
  INVIABLE: 'border-red-500/50 bg-red-950/40 text-red-200',
}

function brl(value?: number | null) {
  if (value == null) return '—'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(Number(value))
}

export default function ROICards({ items, limit = 6 }: { items: LockerRoiRow[]; limit?: number }) {
  const rows = (items || []).slice(0, limit)
  if (!rows.length) {
    return <p className="text-sm text-slate-500">Sem dados de ROI.</p>
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {rows.map((row) => {
        const cls = VIABILITY_STYLES[row.viability_classification || ''] || 'border-slate-600/60 bg-slate-950/80'
        return (
          <article key={row.locker_id} className={`rounded-xl border p-4 ${cls}`}>
            <p className="text-xs font-medium uppercase tracking-wide opacity-80">
              {row.viability_classification || 'N/A'}
            </p>
            <h4 className="mt-1 truncate text-base font-semibold">{row.display_name || row.locker_id}</h4>
            <p className="text-xs text-slate-400">
              {row.city || '—'} · {row.region || '—'}
            </p>
            <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
              <div>
                <dt className="text-xs opacity-70">ROI anual</dt>
                <dd className="font-semibold">{row.annual_roi_pct != null ? `${row.annual_roi_pct}%` : '—'}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Payback</dt>
                <dd className="font-semibold">{row.payback_months != null ? `${row.payback_months} m` : '—'}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Lucro médio/mês</dt>
                <dd>{brl(row.avg_monthly_profit_brl)}</dd>
              </div>
              <div>
                <dt className="text-xs opacity-70">Investimento</dt>
                <dd>{brl(row.total_investment_brl)}</dd>
              </div>
            </dl>
            <p className="mt-2 text-xs opacity-90">{row.recommendation}</p>
          </article>
        )
      })}
    </div>
  )
}
