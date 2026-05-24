import { useState } from 'react'
import { paymentsAdminApi, type RoutingRule } from '../../api/paymentsAdmin'

type Props = {
  rows: RoutingRule[]
  onSaved: () => void
  onMessage: (msg: string) => void
  onError: (msg: string) => void
}

const emptyForm = {
  rule_code: '',
  country_code: 'BR',
  payment_method: 'PIX',
  sales_channel: '',
  primary_player_code: 'MERCADOPAGO',
  fallback_player_code: '',
  priority: '100',
  rationale: '',
  is_active: true,
}

export default function RoutingRuleCrudPanel({ rows, onSaved, onMessage, onError }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [busy, setBusy] = useState(false)

  const startEdit = (row: RoutingRule) => {
    setEditingId(row.id)
    setForm({
      rule_code: row.rule_code,
      country_code: row.country_code,
      payment_method: row.payment_method,
      sales_channel: row.sales_channel || '',
      primary_player_code: row.primary_player_code,
      fallback_player_code: row.fallback_player_code || '',
      priority: String(row.priority),
      rationale: row.rationale || '',
      is_active: row.is_active,
    })
  }

  const reset = () => {
    setEditingId(null)
    setForm(emptyForm)
  }

  const submit = async () => {
    if (!form.rule_code.trim() && !editingId) {
      onError('rule_code obrigatório')
      return
    }
    setBusy(true)
    try {
      if (editingId) {
        await paymentsAdminApi.updateRoutingRule(editingId, {
          country_code: form.country_code.toUpperCase(),
          payment_method: form.payment_method.toUpperCase(),
          primary_player_code: form.primary_player_code.toUpperCase(),
          fallback_player_code: form.fallback_player_code
            ? form.fallback_player_code.toUpperCase()
            : null,
          sales_channel: form.sales_channel ? form.sales_channel.toUpperCase() : null,
          priority: Number(form.priority),
          rationale: form.rationale || undefined,
          is_active: form.is_active,
        })
        onMessage('Regra atualizada.')
      } else {
        await paymentsAdminApi.createRoutingRule({
          rule_code: form.rule_code.toUpperCase(),
          country_code: form.country_code.toUpperCase(),
          payment_method: form.payment_method.toUpperCase(),
          primary_player_code: form.primary_player_code.toUpperCase(),
          fallback_player_code: form.fallback_player_code
            ? form.fallback_player_code.toUpperCase()
            : undefined,
          sales_channel: form.sales_channel ? form.sales_channel.toUpperCase() : undefined,
          priority: Number(form.priority),
          rationale: form.rationale || undefined,
          is_active: form.is_active,
        })
        onMessage('Regra criada.')
      }
      reset()
      onSaved()
    } catch (e: unknown) {
      onError(e instanceof Error ? e.message : 'Falha ao salvar regra')
    } finally {
      setBusy(false)
    }
  }

  const remove = async (id: string) => {
    if (!window.confirm('Excluir esta regra?')) return
    setBusy(true)
    try {
      await paymentsAdminApi.deleteRoutingRule(id)
      onMessage('Regra excluída.')
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
        {editingId ? 'Editar regra de roteamento' : 'Nova regra de roteamento'}
      </h3>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        <label className="text-xs">
          rule_code
          <input
            value={form.rule_code}
            onChange={(e) => setForm({ ...form, rule_code: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
            disabled={!!editingId}
            placeholder="BR-PIX-LOCKER"
          />
        </label>
        <label className="text-xs">
          país
          <input
            value={form.country_code}
            onChange={(e) => setForm({ ...form, country_code: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
            maxLength={2}
          />
        </label>
        <label className="text-xs">
          método
          <input
            value={form.payment_method}
            onChange={(e) => setForm({ ...form, payment_method: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs">
          canal
          <input
            value={form.sales_channel}
            onChange={(e) => setForm({ ...form, sales_channel: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
            placeholder="MARKETPLACE"
          />
        </label>
        <label className="text-xs">
          PSP primário
          <input
            value={form.primary_player_code}
            onChange={(e) => setForm({ ...form, primary_player_code: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs">
          fallback
          <input
            value={form.fallback_player_code}
            onChange={(e) => setForm({ ...form, fallback_player_code: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs">
          prioridade
          <input
            type="number"
            value={form.priority}
            onChange={(e) => setForm({ ...form, priority: e.target.value })}
            className="mt-0.5 w-full rounded border px-2 py-1 dark:bg-slate-900"
          />
        </label>
        <label className="text-xs flex items-end gap-2 pb-1">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
          />
          ativa
        </label>
        <label className="text-xs sm:col-span-2 lg:col-span-4">
          rationale
          <input
            value={form.rationale}
            onChange={(e) => setForm({ ...form, rationale: e.target.value })}
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
              {r.rule_code} · {r.country_code}+{r.payment_method} → {r.primary_player_code}
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
