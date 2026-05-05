import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { partnersApi, type WebhookDeliveryRow } from '../../api/partners'

const DEFAULT_PARTNER =
  (typeof import.meta.env.VITE_PARTNER_ID === 'string' && import.meta.env.VITE_PARTNER_ID) ||
  '00000000-0000-0000-0000-000000000001'

export default function Webhooks() {
  const [partnerId, setPartnerId] = useState(DEFAULT_PARTNER)
  const [subs, setSubs] = useState<{ id: string; url: string; events: string[]; is_active: boolean }[]>([])
  const [deliveries, setDeliveries] = useState<WebhookDeliveryRow[]>([])
  const [url, setUrl] = useState('https://example.com/hook')
  const [events, setEvents] = useState('*')
  const [busy, setBusy] = useState(false)
  const [note, setNote] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setNote(null)
    try {
      const { data } = await partnersApi.getWebhooks(partnerId)
      if (Array.isArray(data)) {
        setSubs(data as { id: string; url: string; events: string[]; is_active: boolean }[])
      } else {
        setSubs([])
      }
    } catch {
      setSubs([])
      setNote('GET /webhooks não exposto — use criação abaixo e entregas.')
    }
    try {
      const { data } = await partnersApi.getDeliveries(partnerId)
      setDeliveries(Array.isArray(data) ? data : [])
    } catch {
      setDeliveries([])
    }
  }, [partnerId])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function createWebhook(e: React.FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      const ev = events
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
      await partnersApi.createWebhook(partnerId, url, ev.length ? ev : ['*'])
      setNote('Webhook configurado.')
      await refresh()
    } catch (err: unknown) {
      setNote(err instanceof Error ? err.message : 'Erro ao criar webhook')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-white">Webhooks parceiro</h1>
          <p className="text-sm text-slate-400">Configuração e log de entregas</p>
        </div>
        <Link to="/partners/catalog" className="text-sm text-emerald-400 hover:underline">
          ← Catálogo
        </Link>
      </div>

      <label className="block max-w-xl text-xs text-slate-400">
        Partner ID
        <input
          value={partnerId}
          onChange={(e) => setPartnerId(e.target.value.trim())}
          onBlur={() => void refresh()}
          className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 font-mono text-sm text-white"
        />
      </label>

      {note && <p className="text-sm text-amber-400">{note}</p>}

      <section className="rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Assinaturas</h2>
        {subs.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">Nenhuma listagem disponível</p>
        ) : (
          <ul className="mt-2 space-y-2 text-sm">
            {subs.map((s) => (
              <li key={s.id} className="rounded border border-slate-800 bg-slate-950/50 px-3 py-2">
                <span className="font-mono text-xs text-slate-400">{s.id}</span>
                <p className="text-slate-200">{s.url}</p>
                <p className="text-xs text-slate-500">{JSON.stringify(s.events)}</p>
              </li>
            ))}
          </ul>
        )}
      </section>

      <form onSubmit={createWebhook} className="space-y-3 rounded-xl border border-slate-700 bg-slate-900/60 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Criar / atualizar webhook</h2>
        <input
          required
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
        />
        <input
          placeholder="eventos separados por vírgula (* default)"
          value={events}
          onChange={(e) => setEvents(e.target.value)}
          className="w-full rounded border border-slate-600 bg-slate-950 px-2 py-1.5 text-sm text-white"
        />
        <button
          type="submit"
          disabled={busy}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          {busy ? 'Enviando…' : 'POST /webhooks'}
        </button>
      </form>

      <section className="overflow-hidden rounded-xl border border-slate-700">
        <h2 className="border-b border-slate-700 bg-slate-900/80 px-3 py-2 text-sm font-semibold text-slate-200">
          Entregas (GET /webhooks/deliveries)
        </h2>
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Evento</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Tentativas</th>
              <th className="px-3 py-2">Erro</th>
            </tr>
          </thead>
          <tbody>
            {deliveries.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-6 text-center text-slate-500">
                  Sem entregas
                </td>
              </tr>
            ) : (
              deliveries.map((d) => (
                <tr key={d.id} className="border-t border-slate-800">
                  <td className="px-3 py-2 text-slate-300">{d.event_type}</td>
                  <td className="px-3 py-2">{d.status}</td>
                  <td className="px-3 py-2">{d.attempts}</td>
                  <td className="px-3 py-2 text-xs text-red-300">{d.last_error ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
