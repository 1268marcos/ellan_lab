import { useEffect, useMemo, useState } from 'react'
import { partnersApi, type LockerSummaryResponse } from '../../api/partners'
import { useAuth } from '../../contexts/AuthContext'

const DEFAULT_LOCKERS = 'SP-ALPHAVILLE-SHOP-LK-001'

type HealthBadge = {
  label: 'OK' | 'Error' | 'Maintenance'
  className: string
}

function getHealthBadge(row: LockerSummaryResponse): HealthBadge {
  if (!row.active) {
    return {
      label: 'Error',
      className: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
    }
  }
  if (row.slots_available <= 0) {
    return {
      label: 'Maintenance',
      className: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    }
  }
  return {
    label: 'OK',
    className: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300',
  }
}

export default function OpsLockerStatus() {
  const { auth } = useAuth()
  const partnerId = auth?.partnerId || (import.meta.env.VITE_PARTNER_ID as string) || ''
  const [lockerIdsInput, setLockerIdsInput] = useState(DEFAULT_LOCKERS)
  const [rows, setRows] = useState<LockerSummaryResponse[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const lockerIds = useMemo(
    () =>
      lockerIdsInput
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
    [lockerIdsInput],
  )

  async function load() {
    if (!partnerId || lockerIds.length === 0) {
      setRows([])
      return
    }
    setLoading(true)
    setError(null)
    try {
      const responses = await Promise.all(
        lockerIds.map((lockerId) => partnersApi.getLockerSummary(lockerId, partnerId)),
      )
      setRows(responses.map((resp) => resp.data))
    } catch (err: unknown) {
      setRows([])
      setError(err instanceof Error ? err.message : 'Erro ao carregar status de lockers.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Operacional · Lockers</h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Ocupacao, slots disponiveis e saude operacional.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-60"
        >
          {loading ? 'Atualizando...' : 'Atualizar'}
        </button>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900/60">
        <label className="block text-xs text-slate-500 dark:text-slate-400">
          Locker IDs (separados por virgula)
          <input
            value={lockerIdsInput}
            onChange={(e) => setLockerIdsInput(e.target.value)}
            className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1.5 font-mono text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-white"
            placeholder="SP-ALPHAVILLE-SHOP-LK-001, SP-CENTER-LK-002"
          />
        </label>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {loading && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          Carregando status dos lockers...
        </div>
      )}

      {!loading && rows.length === 0 && !error && (
        <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
          Nenhum locker encontrado para os parametros informados.
        </div>
      )}

      {!loading && rows.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {rows.map((row) => {
            const health = getHealthBadge(row)
            const occupied = Math.max(0, row.slots_count - row.slots_available)
            const occupancyRate = row.slots_count > 0 ? Math.round((occupied / row.slots_count) * 100) : 0
            return (
              <article
                key={row.locker_id}
                className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/60"
              >
                <div className="mb-3 flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                      {row.region || 'REGIAO'}
                    </p>
                    <h2 className="font-mono text-sm font-semibold text-slate-900 dark:text-slate-100">
                      {row.locker_id}
                    </h2>
                    <p className="text-sm text-slate-600 dark:text-slate-300">{row.display_name || 'Sem nome'}</p>
                  </div>
                  <span className={`rounded-full px-2 py-1 text-xs font-semibold ${health.className}`}>
                    {health.label}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>Disponiveis</span>
                    <span className="font-semibold">{row.slots_available}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>Ocupados</span>
                    <span className="font-semibold">{occupied}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-600 dark:text-slate-300">
                    <span>Ativos no fluxo</span>
                    <span className="font-semibold">{row.active_pickups}</span>
                  </div>
                </div>

                <div className="mt-3">
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>Ocupacao</span>
                    <span>{occupancyRate}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                    <div
                      className="h-2 rounded-full bg-indigo-500"
                      style={{ width: `${Math.max(4, occupancyRate)}%` }}
                    />
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
