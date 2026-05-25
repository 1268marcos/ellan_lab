import { Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Bar, BarChart } from 'recharts'
import type { LockerPnlRow } from '../../api/financialExecutive'

function heatColor(margin: number) {
  if (margin >= 35) return '#10b981'
  if (margin >= 20) return '#34d399'
  if (margin >= 10) return '#fbbf24'
  if (margin >= 0) return '#f97316'
  return '#ef4444'
}

export default function ProfitabilityHeatmap({ rows }: { rows: LockerPnlRow[] }) {
  const byLocker = new Map<string, { locker_id: string; margin: number; label: string }>()
  for (const r of rows) {
    const prev = byLocker.get(r.locker_id)
    const margin = Number(r.margin_pct) || 0
    if (!prev || margin < prev.margin) {
      byLocker.set(r.locker_id, {
        locker_id: r.locker_id,
        margin,
        label: r.locker_id.length > 12 ? `${r.locker_id.slice(0, 10)}…` : r.locker_id,
      })
    }
  }
  const data = [...byLocker.values()]
    .sort((a, b) => b.margin - a.margin)
    .slice(0, 24)

  if (!data.length) {
    return <p className="text-sm text-slate-500">Sem dados para heatmap.</p>
  }

  return (
    <div className="rounded-xl border border-slate-600/60 bg-slate-950/80 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">Margem por locker (último período)</h3>
      <div style={{ width: '100%', height: Math.max(220, data.length * 22) }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
            <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" tickFormatter={(v) => `${v}%`} />
            <YAxis type="category" dataKey="label" width={100} stroke="#94a3b8" tick={{ fontSize: 10 }} />
            <Tooltip
              formatter={(v: number) => [`${Number(v).toFixed(1)}%`, 'Margem']}
              contentStyle={{ background: '#0f172a', border: '1px solid #475569', borderRadius: 8 }}
            />
            <Bar dataKey="margin" radius={[0, 4, 4, 0]}>
              {data.map((entry) => (
                <Cell key={entry.locker_id} fill={heatColor(entry.margin)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
