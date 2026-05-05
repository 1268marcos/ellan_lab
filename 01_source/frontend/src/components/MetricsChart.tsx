import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type ChartType = 'line' | 'bar' | 'heatmap'

type DataPoint = Record<string, string | number | null | undefined>

export default function MetricsChart({
  title,
  type,
  data,
  xKey,
  yKey,
  color = '#6366F1',
  height = 280,
}: {
  title: string
  type: ChartType
  data: DataPoint[]
  xKey: string
  yKey: string
  color?: string
  height?: number
}) {
  const safe = Array.isArray(data) ? data : []

  const heat = (v: number) => {
    if (v < 0.25) return '#A7F3D0'
    if (v < 0.5) return '#6EE7B7'
    if (v < 0.75) return '#34D399'
    return '#10B981'
  }

  return (
    <div className="ellan-card p-4">
      <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-slate-200">{title}</h3>
      <div style={{ width: '100%', height }}>
        <ResponsiveContainer>
          {type === 'line' ? (
            <LineChart data={safe}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
              <XAxis dataKey={xKey} stroke="#64748B" />
              <YAxis stroke="#64748B" />
              <Tooltip />
              <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} dot={false} />
            </LineChart>
          ) : type === 'bar' ? (
            <BarChart data={safe}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
              <XAxis dataKey={xKey} stroke="#64748B" />
              <YAxis stroke="#64748B" />
              <Tooltip />
              <Bar dataKey={yKey} fill={color} radius={[6, 6, 0, 0]} />
            </BarChart>
          ) : (
            <BarChart data={safe}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.15} />
              <XAxis dataKey={xKey} stroke="#64748B" />
              <YAxis stroke="#64748B" />
              <Tooltip />
              <Bar dataKey={yKey} radius={[4, 4, 0, 0]}>
                {safe.map((item, idx) => {
                  const val = Number(item[yKey] ?? 0)
                  return <Cell key={`c-${idx}`} fill={heat(Number.isFinite(val) ? val : 0)} />
                })}
              </Bar>
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  )
}

