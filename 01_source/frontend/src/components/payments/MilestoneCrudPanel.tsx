import { useState } from 'react'
import { paymentsAdminApi, type IntegrationMilestone } from '../../api/paymentsAdmin'

const PHASES = ['DISCOVERY', 'SANDBOX', 'CERTIFICATION', 'PILOT', 'PRODUCTION', 'OPTIMIZATION']
const STATUSES = ['PLANNED', 'IN_PROGRESS', 'DONE', 'BLOCKED', 'CANCELLED']

type Props = {
  rows: IntegrationMilestone[]
  onSaved: () => void
  onMessage: (msg: string) => void
  onError: (msg: string) => void
}

const emptyForm = {
  player_code: 'INPOST',
  phase: 'PILOT',
  title: '',
  status: 'PLANNED',
  owner_team: 'platform-integrations',
  target_date: '',
}

export default function MilestoneCrudPanel({ rows, onSaved, onMessage, onError }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [busy, setBusy] = useState(false)

  const startEdit = (row: IntegrationMilestone) => {
    setEditingId(row.id)
    setForm({
      player_code: row.player_code,
      phase: row.phase,
      title: row.title,
      status: row.status,
      owner_team: row.owner_team || '',
      target_date: row.target_date || '',
    })
  }

  const reset = () => {
    setEditingId(null)
    setForm(emptyForm)
  }

  const submit = async () => {
    if (!form.title.trim()) {
      onError('Título obrigatório')
      return
    }
    setBusy(true)
    try {
      const payload = {
        player_code: form.player_code.toUpperCase(),
        phase: form.phase,
        title: form.title.trim(),
        status: form.status,
        owner_team: form.owner_team || undefined,
        target_date: form.target_date || undefined,
      }
      if (editingId) {
        await paymentsAdminApi.updateIntegrationMilestone(editingId, {
          phase: payload.phase,
          title: payload.title,
          status: payload.status,
          owner_team: payload.owner_team,
          target_date: payload.target_date || null,
        })
        onMessage('Marco atualizado.')
      } else {
        await paymentsAdminApi.createIntegrationMilestone(payload)
        onMessage('Marco criado.')
      }
      reset()
      onSaved()
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : 'Falha ao salvar marco')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id: string) => {
    if (!window.confirm('Excluir este marco?')) return
    setBusy(true)
    try {
      await paymentsAdminApi.deleteIntegrationMilestone(id)
      onMessage('Marco excluído.')
      if (editingId === id) reset()
      onSaved()
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : 'Falha ao excluir')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3 rounded-lg border bg-slate-50 p-4 dark:bg-slate-900/50">
      <h3 className="text-sm font-semibold">
        {editingId ? 'Editar marco' : 'Novo marco de integração'}
      </h3>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <label className="text-xs">
          player
          <input
            value={form.player_code}
            onChange={(e) => setForm({ ...form, player_code: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
            disabled={!!editingId}
          />
        </label>
        <label className="text-xs">
          fase
          <select
            value={form.phase}
            onChange={(e) => setForm({ ...form, phase: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          >
            {PHASES.map((p) => (
              <option key={p} value={p}>
                {p}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs">
          status
          <select
            value={form.status}
            onChange={(e) => setForm({ ...form, status: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs sm:col-span-2">
          título
          <input
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs">
          owner
          <input
            value={form.owner_team}
            onChange={(e) => setForm({ ...form, owner_team: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs">
          target_date
          <input
            type="date"
            value={form.target_date}
            onChange={(e) => setForm({ ...form, target_date: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy}
          onClick={() => void submit()}
          className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-white"
        >
          {editingId ? 'Salvar' : 'Criar'}
        </button>
        {editingId ? (
          <button type="button" onClick={reset} className="rounded-lg border px-3 py-1.5 text-xs">
            Cancelar
          </button>
        ) : null}
      </div>
      <div className="max-h-32 overflow-y-auto text-xs">
        {rows.slice(0, 8).map((r) => (
          <div key={r.id} className="flex items-center justify-between gap-2 border-t py-1">
            <span>
              {r.player_code} · {r.phase} · {r.title.slice(0, 40)}
            </span>
            <span className="shrink-0">
              <button type="button" className="text-blue-600 underline" onClick={() => startEdit(r)}>
                editar
              </button>
              {' · '}
              <button
                type="button"
                className="text-red-600 underline"
                onClick={() => void remove(r.id)}
              >
                excluir
              </button>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
