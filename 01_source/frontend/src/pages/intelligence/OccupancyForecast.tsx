import { FormEvent, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { useAuth } from '../../AuthContext'
import { mlApi, type OccupancyAlert, type OccupancyForecastResponse } from '../../api/ml'

function formatHourLabel(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleString(undefined, { weekday: 'short', hour: '2-digit', minute: '2-digit' })
  } catch {
    return iso.slice(11, 16)
  }
}

export default function OccupancyForecast() {
  const { auth } = useAuth()
  const [lockerId, setLockerId] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<OccupancyForecastResponse | null>(null)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const lid = lockerId.trim()
    if (!lid) {
      setError('Informe o locker_id')
      setData(null)
      return
    }
    setLoading(true)
    setError(null)
    setQuery(lid)
    try {
      const res = await mlApi.getOccupancyForecast(lid, {
        hours: 24,
        ...(auth?.partnerId ? { partner_id: auth.partnerId } : {}),
      })
      setData(res)
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        (err instanceof Error ? err.message : 'Falha ao carregar forecast')
      setError(String(msg))
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  const chartRows =
    data?.forecast.map((f) => ({
      label: formatHourLabel(f.hour_start),
      pct: f.occupied_pct_slots,
    })) ?? []

  const heuristic = data?.model === 'heuristic_fallback'
  const alertPolicy = data?.alert_policy

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">Previsão de ocupação</h1>
        <p className="text-sm text-gray-600 dark:text-slate-400">
          Ocupação prevista (0–100%). Alertas quando ≥85% por 3 horas consecutivas.
        </p>
      </div>

      <form
        onSubmit={onSubmit}
        className="flex flex-wrap items-end gap-3 rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900"
      >
        <label className="block min-w-[200px] flex-1 text-xs text-gray-600 dark:text-slate-400">
          locker_id
          <input
            value={lockerId}
            onChange={(e) => setLockerId(e.target.value)}
            className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
            placeholder="ex.: LKR-001"
            autoComplete="off"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Carregando…' : 'Buscar 24h'}
        </button>
      </form>

      {error && (
        <div
          className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-100"
          role="alert"
        >
          {error}
        </div>
      )}

      {data && (
        <>
          {heuristic && (
            <div className="rounded-lg border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-950 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-100">
              <strong>Modo heurístico:</strong> modelo LSTM indisponível; valores são estimativa simplificada (fallback).
            </div>
          )}
          {!heuristic && (
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Modelo: <span className="font-mono">{data.model}</span>
              {query ? ` · locker ${query}` : ''}
            </p>
          )}

          {alertPolicy && (
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Política: {alertPolicy.description} (limite {(alertPolicy.threshold_fraction * 100).toFixed(0)}%,{' '}
              {alertPolicy.consecutive_hours}h seguidas).
            </p>
          )}

          <div className="h-80 w-full rounded-xl border border-gray-200 bg-white p-2 dark:border-slate-700 dark:bg-slate-900">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartRows} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" className="stroke-slate-200 dark:stroke-slate-700" />
                <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" angle={-35} dy={8} height={60} />
                <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} width={48} />
                <Tooltip
                  formatter={(value: number) => [`${value.toFixed(1)}%`, 'Ocupação']}
                  labelFormatter={(_, p) => (p?.[0]?.payload?.label as string) ?? ''}
                />
                <Line
                  type="monotone"
                  dataKey="pct"
                  name="Ocupação %"
                  stroke="#4f46e5"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-2 text-sm font-semibold text-slate-800 dark:text-slate-100">Alertas (&gt;85% por 3h)</h2>
            {data.alerts.length === 0 ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">Nenhum alerta nesta janela.</p>
            ) : (
              <ul className="list-inside list-disc space-y-1 text-sm text-slate-700 dark:text-slate-300">
                {data.alerts.map((a: OccupancyAlert, i: number) => (
                  <li key={i}>
                    Horas {a.from_hour_index ?? '?'}–{a.to_hour_index ?? '?'} ({a.hours}h), pico{' '}
                    {(a.peak_occupancy_fraction * 100).toFixed(1)}%
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  )
}
