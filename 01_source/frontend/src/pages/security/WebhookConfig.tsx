import { FormEvent, useCallback, useEffect, useState } from 'react'
import { securityCrudApi, type WebhookEndpoint } from '../../api/securityCrud'

export default function WebhookConfig() {
  const [items, setItems] = useState<WebhookEndpoint[]>([])
  const [form, setForm] = useState({ id: '', url: 'https://hooks.example/ops', events: '*', active: true })
  const [secret, setSecret] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const { data } = await securityCrudApi.listWebhooks()
      setItems(data.items ?? [])
      if (data.items?.[0] && !form.id) {
        const w = data.items[0]
        setForm({ id: w.id, url: w.url, events: w.events.join(','), active: w.active })
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Falha ao carregar')
    }
  }, [form.id])

  useEffect(() => {
    void load()
  }, [load])

  const onSave = async (e: FormEvent) => {
    e.preventDefault()
    setSecret(null)
    try {
      const { data } = await securityCrudApi.webhookConfig({
        id: form.id || undefined,
        url: form.url,
        events: form.events.split(',').map((s) => s.trim()).filter(Boolean),
        active: form.active,
      })
      setSecret(data.webhook_secret ?? null)
      if (data.endpoint?.id) setForm((f) => ({ ...f, id: data.endpoint.id }))
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao salvar')
    }
  }

  return (
    <div className="space-y-4">
      <form className="max-w-xl space-y-2" onSubmit={(e) => void onSave(e)}>
        <input
          className="ellan-field w-full"
          placeholder="endpoint id (opcional)"
          value={form.id}
          onChange={(e) => setForm((f) => ({ ...f, id: e.target.value }))}
        />
        <input
          className="ellan-field w-full"
          placeholder="URL"
          required
          value={form.url}
          onChange={(e) => setForm((f) => ({ ...f, url: e.target.value }))}
        />
        <input
          className="ellan-field w-full"
          placeholder="events (vírgula)"
          value={form.events}
          onChange={(e) => setForm((f) => ({ ...f, events: e.target.value }))}
        />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={form.active} onChange={(e) => setForm((f) => ({ ...f, active: e.target.checked }))} />
          Ativo
        </label>
        <button type="submit" className="ellan-btn ellan-btn-primary">
          Salvar webhook
        </button>
      </form>
      {secret && (
        <p className="rounded bg-amber-50 border border-amber-200 p-3 text-sm break-all">
          Secret: <strong>{secret}</strong>
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}
      <ul className="text-sm space-y-1">
        {items.map((w) => (
          <li key={w.id} className="border-b py-2">
            {w.url} — {w.active ? 'ativo' : 'inativo'} ({w.events.join(', ')})
          </li>
        ))}
      </ul>
    </div>
  )
}
