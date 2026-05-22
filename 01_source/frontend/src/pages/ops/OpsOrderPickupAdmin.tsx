import { FormEvent, useCallback, useState } from 'react'
import { orderPickupAdminApi, type EcommercePartner, type OrderRow } from '../../api/orderPickupAdmin'

type Tab = 'partners' | 'orders' | 'integration'

export default function OpsOrderPickupAdmin() {
  const [tab, setTab] = useState<Tab>('partners')
  const [ecItems, setEcItems] = useState<EcommercePartner[]>([])
  const [orders, setOrders] = useState<OrderRow[]>([])
  const [pickups, setPickups] = useState<unknown[]>([])
  const [outbox, setOutbox] = useState<unknown[]>([])
  const [fulfillment, setFulfillment] = useState<unknown[]>([])
  const [ecForm, setEcForm] = useState({ name: '', code: '', integration_type: 'REST', status: 'ACTIVE' })
  const [orderForm, setOrderForm] = useState({ amount_cents: 1000, ecommerce_partner_id: 'ec-ops-001' })
  const [selectedId, setSelectedId] = useState('')
  const [partnerType, setPartnerType] = useState('ECOMMERCE')
  const [webhookUrl, setWebhookUrl] = useState('')
  const [webhookSecret, setWebhookSecret] = useState('')
  const [lastApiKey, setLastApiKey] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [ec, ord, pk, ob, ft] = await Promise.all([
        orderPickupAdminApi.listEcommerce(),
        orderPickupAdminApi.listOrders(),
        orderPickupAdminApi.listPickups(),
        orderPickupAdminApi.listOutbox(),
        orderPickupAdminApi.listFulfillment(),
      ])
      setEcItems(ec.data.partners ?? [])
      setOrders(ord.data.items ?? [])
      setPickups(pk.data.items ?? [])
      setOutbox(ob.data.items ?? [])
      setFulfillment(ft.data.items ?? [])
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao carregar')
    } finally {
      setLoading(false)
    }
  }, [])

  const onSeed = async () => {
    setLoading(true)
    try {
      await orderPickupAdminApi.seed()
      setMessage('Seed aplicado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no seed')
    } finally {
      setLoading(false)
    }
  }

  const onCreateEc = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.createEcommerce(ecForm)
      setMessage(`Parceiro ${data.code} criado.`)
      setSelectedId(data.id)
      setPartnerType('ECOMMERCE')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar parceiro')
    } finally {
      setLoading(false)
    }
  }

  const onCreateOrder = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.createOrder({
        ...orderForm,
        channel: 'KIOSK',
        region: 'BR',
        totem_id: 'TOTEM-OPS',
        status: 'PENDING',
        payment_status: 'PENDING',
      })
      setMessage(`Pedido ${data.id} criado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar pedido')
    } finally {
      setLoading(false)
    }
  }

  const onWebhook = async () => {
    if (!selectedId || !webhookUrl) return
    setLoading(true)
    try {
      await orderPickupAdminApi.configureWebhook(selectedId, partnerType, {
        url: webhookUrl,
        secret: webhookSecret || undefined,
        events: ['ORDER_PAID', 'ORDER_PICKED_UP'],
      })
      setMessage('Webhook configurado.')
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no webhook')
    } finally {
      setLoading(false)
    }
  }

  const onRotateKey = async () => {
    if (!selectedId) return
    setLoading(true)
    try {
      const { data } = await orderPickupAdminApi.rotateApiKey(selectedId, partnerType)
      setLastApiKey(data.api_key)
      setMessage(`Nova API key (${data.key_prefix}…).`)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao rotacionar chave')
    } finally {
      setLoading(false)
    }
  }

  const onReplay = async (outboxId: string) => {
    setLoading(true)
    try {
      await orderPickupAdminApi.replayOutbox(outboxId)
      setMessage(`Outbox ${outboxId} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no replay')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Order Pickup</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Parceiros, pedidos, pickups, créditos, outbox de integração e fulfillment.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="rounded-lg border px-3 py-2 text-sm">
            Seed
          </button>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Atualizar
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="text-sm text-red-500">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      <div className="flex gap-2">
        {(['partners', 'orders', 'integration'] as Tab[]).map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border'}`}
          >
            {t === 'partners' ? 'Parceiros' : t === 'orders' ? 'Pedidos / Pickups' : 'Integração'}
          </button>
        ))}
      </div>

      {tab === 'partners' && (
        <>
          <form onSubmit={onCreateEc} className="grid gap-3 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900 md:grid-cols-3">
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Nome"
              required
              value={ecForm.name}
              onChange={(e) => setEcForm((f) => ({ ...f, name: e.target.value }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="Código"
              required
              value={ecForm.code}
              onChange={(e) => setEcForm((f) => ({ ...f, code: e.target.value }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar e-commerce
            </button>
          </form>
          <section className="rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <div className="flex flex-wrap gap-2">
              <select
                className="rounded border px-2 py-1 text-sm"
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
              >
                <option value="">Parceiro</option>
                {ecItems.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <select
                className="rounded border px-2 py-1 text-sm"
                value={partnerType}
                onChange={(e) => setPartnerType(e.target.value)}
              >
                <option value="ECOMMERCE">ECOMMERCE</option>
                <option value="LOGISTICS">LOGISTICS</option>
              </select>
              <input
                className="min-w-[14rem] flex-1 rounded border px-2 py-1 text-sm"
                placeholder="Webhook URL"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
              />
              <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
                Webhook
              </button>
              <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
                Rotacionar API key
              </button>
            </div>
          </section>
          <table className="w-full text-left text-sm">
            <tbody>
              {ecItems.map((p) => (
                <tr key={p.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs">{p.code}</td>
                  <td className="px-3 py-2">{p.name}</td>
                  <td className="px-3 py-2">{p.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {tab === 'orders' && (
        <>
          <form onSubmit={onCreateOrder} className="flex flex-wrap gap-2 rounded-xl border bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
            <input
              type="number"
              className="w-32 rounded border px-2 py-1 text-sm"
              value={orderForm.amount_cents}
              onChange={(e) => setOrderForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
            />
            <input
              className="rounded border px-2 py-1 text-sm"
              placeholder="partner_id"
              value={orderForm.ecommerce_partner_id}
              onChange={(e) => setOrderForm((f) => ({ ...f, ecommerce_partner_id: e.target.value }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar pedido demo
            </button>
          </form>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Pedido</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Valor</th>
              </tr>
            </thead>
            <tbody>
              {orders.map((o) => (
                <tr key={o.id} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2 font-mono text-xs">{o.id}</td>
                  <td className="px-3 py-2">
                    {o.status} / {o.payment_status}
                  </td>
                  <td className="px-3 py-2">{(o.amount_cents / 100).toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-xs text-gray-500">Pickups: {pickups.length}</p>
        </>
      )}

      {tab === 'integration' && (
        <>
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">Outbox</th>
                <th className="px-3 py-2">Evento</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2" />
              </tr>
            </thead>
            <tbody>
              {outbox.map((row) => {
                const item = row as { id: string; order_id: string; event_type: string; status: string }
                return (
                  <tr key={item.id} className="border-t dark:border-slate-800">
                    <td className="px-3 py-2 font-mono text-xs">{item.id}</td>
                    <td className="px-3 py-2">{item.event_type}</td>
                    <td className="px-3 py-2">{item.status}</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        className="text-xs text-indigo-600"
                        onClick={() => void onReplay(item.id)}
                      >
                        Replay
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <p className="text-xs text-gray-500">Fulfillment tracking: {fulfillment.length}</p>
        </>
      )}
    </div>
  )
}
