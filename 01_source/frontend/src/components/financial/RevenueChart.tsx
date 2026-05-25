import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { RevenueTrendPoint } from '../../api/financialExecutive'

export default function RevenueChart({
  data,
  height = 300,
}: {
  data: RevenueTrendPoint[]
  height?: number
}) {
  const safe = Array.isArray(data) ? data : []
  return (
    <div className="rounded-xl border border-slate-600/60 bg-slate-950/80 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">Receita e lucro (mensal)</h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          <LineChart data={safe} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.35} />
            <XAxis dataKey="month" stroke="#94a3b8" tick={{ fontSize: 11 }} />
            <YAxis stroke="#94a3b8" tick={{ fontSize: 11 }} />
            <Tooltip
              contentStyle={{ background: '#0f172a', border: '1px solid #475569', borderRadius: 8 }}
            />
            <Legend />
            <Line type="monotone" dataKey="revenue_brl" name="Receita" stroke="#6366f1" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="profit_brl" name="Lucro" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
