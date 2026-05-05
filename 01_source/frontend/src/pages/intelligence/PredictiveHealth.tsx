import { useCallback, useEffect, useMemo, useState } from 'react'
import { Line, LineChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import { useAuth } from '../../AuthContext'
import { mlApi, type AtRiskRow } from '../../api/ml'

function doorFailures7d(row: AtRiskRow): number | null {
  const ext = row as AtRiskRow & { door_failures_7d?: number | null }
  if (ext.door_failures_7d != null) return ext.door_failures_7d
  return row.door_failures_70d
}

function healthTone(score: number | null): 'green' | 'yellow' | 'red' | 'neutral' {
  if (score == null || Number.isNaN(score)) return 'neutral'
  if (score > 60) return 'green'
  if (score >= 30) return 'yellow'
  return 'red'
}

function healthBadgeClasses(tone: ReturnType<typeof healthTone>): string {
  switch (tone) {
    case 'green':
      return 'bg-emerald-100 text-emerald-800 ring-emerald-600/20 dark:bg-emerald-900/40 dark:text-emerald-200'
    case 'yellow':
      return 'bg-amber-100 text-amber-900 ring-amber-600/20 dark:bg-amber-900/40 dark:text-amber-100'
    case 'red':
      return 'bg-rose-100 text-rose-800 ring-rose-600/20 dark:bg-rose-900/40 dark:text-rose-100'
    default:
      return 'bg-slate-100 text-slate-600 ring-slate-500/10 dark:bg-slate-800 dark:text-slate-300'
  }
}

function healthBadgeLabel(score: number | null): string {
  const t = healthTone(score)
  if (t === 'neutral') return 'N/D'
  if (t === 'green') return 'Saudável'
  if (t === 'yellow') return 'Atenção'
  return 'Crítico'
}

function scoreCellClass(score: number | null): string {
  const t = healthTone(score)
  if (t === 'green') return 'font-semibold text-emerald-700 dark:text-emerald-300'
  if (t === 'yellow') return 'font-semibold text-amber-700 dark:text-amber-200'
  if (t === 'red') return 'font-semibold text-rose-700 dark:text-rose-300'
  return 'text-slate-500 dark:text-slate-400'
}

function MiniSparkline({ healthScore }: { healthScore: number | null }) {
  if (healthScore == null || Number.isNaN(healthScore)) {
    return <span className="text-xs text-slate-400">—</span>
  }
  const h = Math.max(0, Math.min(100, healthScore))
  const data = [
    { i: 0, v: Math.max(0, h - 10) },
    { i: 1, v: h },
    { i: 2, v: Math.min(100, h + 6) },
  ]
  const tone = healthTone(healthScore)
  const stroke = tone === 'green' ? '#059669' : tone === 'yellow' ? '#d97706' : '#e11d48'
  return (
    <div className="h-8 w-[72px]" aria-hidden>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 2, right: 2, left: 2, bottom: 2 }}>
          <XAxis dataKey="i" type="number" hide />
          <YAxis domain={[0, 100]} hide />
          <Line
            type="monotone"
            dataKey="v"
            stroke={stroke}
            strokeWidth={1.5}
            dot={false}
            isAnimationActive={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function PredictiveHealth() {
  const { auth } = useAuth()
  const [rows, setRows] = useState<AtRiskRow[]>([])
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [pageSize] = useState(50)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await mlApi.getAtRisk({
        page_size: pageSize,
        page,
        ...(auth?.partnerId ? { partner_id: auth.partnerId } : {}),
      })
      setRows(data.rows)
      setTotal(data.total)
    } catch (e: unknown) {
      const msg =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (e instanceof Error ? e.message : 'Falha ao carregar')
      setError(String(msg))
      setRows([])
      setTotal(0)
    } finally {
      setLoading(false)
    }
  }, [auth?.partnerId, page, pageSize])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Saúde preditiva</h1>
        <p className="text-sm text-gray-600 dark:text-slate-400">
          Lockers em risco (health score). Verde &gt;60, amarelo 30–60, vermelho &lt;30.
        </p>
      </div>

      {loading && (
        <p className="text-sm text-slate-500 dark:text-slate-400" role="status">
          Carregando…
        </p>
      )}
      {error && !loading && (
        <div
          className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-100"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
                <tr>
                  <th className="px-3 py-2">locker_id</th>
                  <th className="px-3 py-2">health_score</th>
                  <th className="px-3 py-2">failure_probability</th>
                  <th className="px-3 py-2">battery_min</th>
                  <th className="px-3 py-2">door_failures_7d</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Tendência</th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-slate-500 dark:text-slate-400">
                      Nenhum registro nesta página.
                    </td>
                  </tr>
                ) : (
                  rows.map((r) => {
                    const tone = healthTone(r.health_score)
                    const df = doorFailures7d(r)
                    return (
                      <tr
                        key={r.locker_id}
                        className="border-b border-gray-100 last:border-0 dark:border-slate-800"
                      >
                        <td className="px-3 py-2 font-mono text-xs text-slate-800 dark:text-slate-200">
                          {r.locker_id}
                        </td>
                        <td className={`px-3 py-2 tabular-nums ${scoreCellClass(r.health_score)}`}>
                          {r.health_score ?? '—'}
                        </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-slate-300">
                          {r.failure_probability != null ? r.failure_probability.toFixed(3) : '—'}
                        </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-slate-300">
                          {r.battery_min ?? '—'}
                        </td>
                        <td className="px-3 py-2 tabular-nums text-slate-700 dark:text-slate-300">
                          {df ?? '—'}
                        </td>
                        <td className="px-3 py-2">
                          <span
                            className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${healthBadgeClasses(tone)}`}
                          >
                            {healthBadgeLabel(r.health_score)}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <MiniSparkline healthScore={r.health_score} />
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
            <span className="text-slate-600 dark:text-slate-400">
              Página {page} de {totalPages} · {total} lockers
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-700 enabled:hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:enabled:hover:bg-slate-700"
              >
                Anterior
              </button>
              <button
                type="button"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-slate-700 enabled:hover:bg-slate-50 disabled:opacity-40 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:enabled:hover:bg-slate-700"
              >
                Próxima
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
