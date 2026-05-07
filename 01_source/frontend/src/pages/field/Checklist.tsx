import { FormEvent, useEffect, useState } from 'react'
import {
  getPendingChecklistCount,
  saveChecklistOffline,
  syncOfflineChecklists,
} from '../../utils/offlineStorage'

const runtimeBaseUrl = import.meta.env.VITE_RUNTIME_BASE_URL ?? 'http://localhost:8200'

type FieldHealth = {
  status?: string
  service?: string
}

type ChecklistResponse = {
  status?: string
  item?: {
    locker_id: string
    task: string
    status: string
    timestamp?: string | null
  }
}

type OfflineSyncResult = {
  synced: number
  failed: number
}

type LockerStatus = {
  locker_id: string
  status: string
  slots_free: number
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function FieldChecklist() {
  const [lockerId, setLockerId] = useState('SP-ALPHAVILLE-SHOP-LK-001')
  const [task, setTask] = useState('check_power')
  const [status, setStatus] = useState('completed')
  const [loading, setLoading] = useState(false)
  const [health, setHealth] = useState<FieldHealth | null>(null)
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null)
  const [locker, setLocker] = useState<LockerStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [offlinePending, setOfflinePending] = useState(0)
  const [offlineMessage, setOfflineMessage] = useState<string | null>(null)

  const refreshOfflinePending = async () => {
    const count = await getPendingChecklistCount()
    setOfflinePending(count)
  }

  useEffect(() => {
    void refreshOfflinePending()
  }, [])

  const runSmoke = async () => {
    setLoading(true)
    setError(null)
    try {
      const [healthPayload, lockerPayload] = await Promise.all([
        fetchJson<FieldHealth>(`${runtimeBaseUrl}/api/v1/field/health`),
        fetchJson<LockerStatus>(
          `${runtimeBaseUrl}/api/v1/field/locker/${encodeURIComponent(lockerId)}/status`,
        ),
      ])
      setHealth(healthPayload)
      setLocker(lockerPayload)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha no smoke do App Campo.')
    } finally {
      setLoading(false)
    }
  }

  const submitChecklist = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setOfflineMessage(null)
    const checklistPayload = {
      locker_id: lockerId,
      task,
      status,
      timestamp: new Date().toISOString(),
    }
    try {
      const payload = await fetchJson<ChecklistResponse>(`${runtimeBaseUrl}/api/v1/field/checklist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(checklistPayload),
      })
      setChecklist(payload)
      await runSmoke()
    } catch (err) {
      const saved = await saveChecklistOffline(checklistPayload)
      await refreshOfflinePending()
      setChecklist({
        status: 'offline_saved',
        item: saved,
      })
      setOfflineMessage('Checklist salvo offline. Sincronize quando a conexão com o runtime voltar.')
      setError(err instanceof Error ? err.message : 'Falha ao enviar checklist.')
      setLoading(false)
    }
  }

  const syncPending = async () => {
    setLoading(true)
    setError(null)
    setOfflineMessage(null)
    try {
      const result: OfflineSyncResult = await syncOfflineChecklists(runtimeBaseUrl)
      await refreshOfflinePending()
      setOfflineMessage(`Sincronização concluída: ${result.synced} enviados, ${result.failed} falharam.`)
      if (result.failed > 0) {
        setError('Ainda há checklists pendentes para sincronizar.')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Falha ao sincronizar checklists offline.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600 dark:text-indigo-300">
          Sprint 2 MVP
        </p>
        <h1 className="mt-1 text-2xl font-bold text-slate-900 dark:text-slate-50">App Campo / Checklist</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Fluxo operacional mínimo: validar saúde do serviço, registrar checklist, consultar status do locker e manter fila offline.
        </p>
        <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-500 dark:text-slate-400">
          <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-700">
            Offline pendente: {offlinePending}
          </span>
          <span className="rounded-full border border-slate-200 px-3 py-1 dark:border-slate-700">
            Conexão navegador: {navigator.onLine ? 'online' : 'offline'}
          </span>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <form className="grid gap-4 md:grid-cols-3" onSubmit={submitChecklist}>
          <label className="text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-200">Locker ID</span>
            <input
              className="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
              value={lockerId}
              onChange={(event) => setLockerId(event.target.value)}
            />
          </label>
          <label className="text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-200">Tarefa</span>
            <input
              className="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
              value={task}
              onChange={(event) => setTask(event.target.value)}
            />
          </label>
          <label className="text-sm">
            <span className="font-medium text-slate-700 dark:text-slate-200">Status</span>
            <select
              className="mt-1 w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950"
              value={status}
              onChange={(event) => setStatus(event.target.value)}
            >
              <option value="pending">pending</option>
              <option value="completed">completed</option>
            </select>
          </label>
          <div className="flex gap-2 md:col-span-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Enviando...' : 'Enviar checklist'}
            </button>
            <button
              type="button"
              onClick={() => void runSmoke()}
              disabled={loading}
              className="rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Rodar smoke
            </button>
            <button
              type="button"
              onClick={() => void syncPending()}
              disabled={loading || offlinePending === 0}
              className="rounded border border-emerald-300 px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50 disabled:opacity-50 dark:border-emerald-700 dark:text-emerald-200 dark:hover:bg-emerald-950/40"
            >
              Sincronizar offline
            </button>
          </div>
        </form>
      </div>

      {offlineMessage && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-100">
          {offlineMessage}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          {error}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <ResultCard title="Health" data={health} />
        <ResultCard title="Checklist" data={checklist} />
        <ResultCard title="Locker" data={locker} />
      </div>
    </div>
  )
}

export default FieldChecklist

function ResultCard({ title, data }: { title: string; data: unknown }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
      <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-100">{title}</h2>
      <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-50 p-3 text-xs text-slate-700 dark:bg-slate-950 dark:text-slate-200">
        {data ? JSON.stringify(data, null, 2) : 'Sem dados ainda.'}
      </pre>
    </div>
  )
}
