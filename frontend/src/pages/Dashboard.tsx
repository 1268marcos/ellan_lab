import { useEffect, useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'
import { LockerMap } from '../components/LockerMap'
import type { Locker, OpsDashboardSummary } from '../types'

const MOCK: OpsDashboardSummary = {
  lockersAtivos: 42,
  pickupsHoje: 128,
  slaPercent: 97.4,
  lockers: Array.from({ length: 16 }, (_, i) => ({
    id: `LK-${String(i + 1).padStart(2, '0')}`,
    occupancy: [0.12, 0.45, 0.82, 0.25, 0.66, 0.18, 0.91, 0.33, 0.05, 0.72, 0.4, 0.88, 0.22, 0.58, 0.15, 0.77][i] ?? 0.5,
    status: i === 5 ? 'maintenance' : 'active',
  })) as Locker[],
}

export default function Dashboard() {
  const [data, setData] = useState<OpsDashboardSummary>(MOCK)
  const slaSeries = useMemo(
    () => [
      { h: '06', v: data.slaPercent - 2 },
      { h: '09', v: data.slaPercent - 0.5 },
      { h: '12', v: data.slaPercent },
      { h: '15', v: data.slaPercent - 0.3 },
      { h: '18', v: data.slaPercent },
    ],
    [data.slaPercent],
  )

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const { data: d } = await api.get<OpsDashboardSummary>('/ops/dashboard')
        if (!cancelled && d) setData({ ...MOCK, ...d, lockers: d.lockers?.length ? d.lockers : MOCK.lockers })
      } catch {
        if (!cancelled) setData(MOCK)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <header>
        <h1 className="text-2xl font-semibold tracking-tight text-white">Dashboard OPS</h1>
        <p className="mt-1 text-sm text-slate-400">Resumo operacional · lockers e pickups</p>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Lockers ativos" value={data.lockersAtivos} />
        <MetricCard label="Pickups hoje" value={data.pickupsHoje} />
        <MetricCard label="SLA %" value={data.slaPercent} suffix="%" decimals />
      </div>

      <section className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
        <h2 className="mb-2 text-sm font-medium text-slate-300">SLA % (tendência)</h2>
        <div className="h-40 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={slaSeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <XAxis dataKey="h" stroke="#64748b" fontSize={11} />
              <YAxis domain={['auto', 'auto']} stroke="#64748b" fontSize={11} width={36} />
              <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #334155' }} />
              <Line type="monotone" dataKey="v" stroke="#34d399" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section>
        <h2 className="mb-3 text-lg font-medium text-slate-200">Mapa de ocupação (4×4)</h2>
        <LockerMap lockers={data.lockers} />
        <p className="mt-2 text-xs text-slate-500">
          Verde &lt;30% · Amarelo &lt;70% · Vermelho ≥70% · anel violeta = manutenção
        </p>
      </section>
    </div>
  )
}

function MetricCard({
  label,
  value,
  suffix = '',
  decimals,
}: {
  label: string
  value: number
  suffix?: string
  decimals?: boolean
}) {
  const shown = decimals ? value.toFixed(1) : String(value)
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/60 p-5 shadow-lg">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-3xl font-bold tabular-nums text-white">
        {shown}
        {suffix && <span className="text-lg font-semibold text-slate-400">{suffix}</span>}
      </p>
    </div>
  )
}
