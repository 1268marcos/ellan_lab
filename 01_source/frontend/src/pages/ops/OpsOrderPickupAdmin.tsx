import { FormEvent, useCallback, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  orderPickupAdminApi,
  type EcommercePartner,
  type LogisticsPartner,
  type OrderRow,
} from '../../api/orderPickupAdmin'

type Tab = 'partners' | 'orders' | 'credits' | 'integration'
type PartnerSubTab = 'ecommerce' | 'logistics'

export default function OpsOrderPickupAdmin() {
  const [tab, setTab] = useState<Tab>('partners')
  const [partnerSubTab, setPartnerSubTab] = useState<PartnerSubTab>('ecommerce')
  const [ecItems, setEcItems] = useState<EcommercePartner[]>([])
  const [lgItems, setLgItems] = useState<LogisticsPartner[]>([])
  const [orders, setOrders] = useState<OrderRow[]>([])
  const [pickups, setPickups] = useState<unknown[]>([])
  const [credits, setCredits] = useState<unknown[]>([])
  const [outbox, setOutbox] = useState<unknown[]>([])
  const [fulfillment, setFulfillment] = useState<unknown[]>([])
  const [orderItems, setOrderItems] = useState<unknown[]>([])
  const [pickupEvents, setPickupEvents] = useState<unknown[]>([])
  const [pickupTokens, setPickupTokens] = useState<unknown[]>([])
  const [pickupAttempts, setPickupAttempts] = useState<unknown[]>([])
  const [domainOutbox, setDomainOutbox] = useState<unknown[]>([])
  const [partnerForm, setPartnerForm] = useState({ name: '', code: '' })
  const [orderForm, setOrderForm] = useState({
    amount_cents: 4990,
    ecommerce_partner_id: 'ec-ops-001',
    totem_id: 'TOTEM-OPS',
  })
  const [creditForm, setCreditForm] = useState({ order_id: 'ord-seed-demo-001', user_id: 'usr-demo', amount_cents: 500 })
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
    setMessage(null)
    try {
      const [ec, lg, ord, pk, cr, ob, ft, oi, pe, pt, pa, dom] = await Promise.all([
        orderPickupAdminApi.listEcommerce(),
        orderPickupAdminApi.listLogistics(),
        orderPickupAdminApi.listOrders(),
        orderPickupAdminApi.listPickups(),
        orderPickupAdminApi.listCredits(),
        orderPickupAdminApi.listOutbox(),
        orderPickupAdminApi.listFulfillment(),
        orderPickupAdminApi.listOrderItems(),
        orderPickupAdminApi.listPickupEvents(),
        orderPickupAdminApi.listPickupTokens(),
        orderPickupAdminApi.listPickupAttempts(),
        orderPickupAdminApi.listDomainOutbox(),
      ])
      setEcItems(ec.data.partners ?? [])
      setLgItems(lg.data.partners ?? [])
      setOrders(ord.data.items ?? [])
      setPickups(pk.data.items ?? [])
      setCredits(cr.data.items ?? [])
      setOutbox(ob.data.items ?? [])
      setFulfillment(ft.data.items ?? [])
      setOrderItems(oi.data.items ?? [])
      setPickupEvents(pe.data.items ?? [])
      setPickupTokens(pt.data.items ?? [])
      setPickupAttempts(pa.data.items ?? [])
      setDomainOutbox(dom.data.items ?? [])
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

  const onCreatePartner = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const api =
        partnerSubTab === 'ecommerce' ? orderPickupAdminApi.createEcommerce : orderPickupAdminApi.createLogistics
      const body =
        partnerSubTab === 'ecommerce'
          ? { ...partnerForm, integration_type: 'REST', status: 'ACTIVE' }
          : { ...partnerForm, integration_type: 'REST' }
      const { data } = await api(body)
      setMessage(`Parceiro ${data.code} criado.`)
      setSelectedId(data.id)
      setPartnerType(partnerSubTab === 'ecommerce' ? 'ECOMMERCE' : 'LOGISTICS')
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

  const onCreateCredit = async (e: FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await orderPickupAdminApi.createCredit({
        ...creditForm,
        type: 'GOODWILL',
        currency: 'BRL',
        status: 'AVAILABLE',
      })
      setMessage('Crédito criado.')
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha ao criar crédito')
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

  const onReplayPartner = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupAdminApi.replayOutbox(id)
      setMessage(`Outbox parceiro ${id} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no replay')
    } finally {
      setLoading(false)
    }
  }

  const onReplayDomain = async (id: string) => {
    setLoading(true)
    try {
      await orderPickupAdminApi.replayDomainOutbox(id)
      setMessage(`Domain outbox ${id} reenfileirado.`)
      await load()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Falha no replay domain')
    } finally {
      setLoading(false)
    }
  }

  const partnerItems = partnerType === 'ECOMMERCE' ? ecItems : lgItems

  const tableRows =
    tab === 'partners'
      ? [
          ...ecItems.map((p) => ({ key: `ec-${p.id}`, tipo: 'EC', id: p.code, detalhe: `${p.name} · ${p.status}` })),
          ...lgItems.map((p) => ({ key: `lg-${p.id}`, tipo: 'LG', id: p.code, detalhe: p.name })),
        ]
      : tab === 'orders'
        ? [
            ...orders.map((o) => ({
              key: `ord-${o.id}`,
              tipo: 'order',
              id: o.id,
              detalhe: `${o.status}/${o.payment_status} · R$ ${(o.amount_cents / 100).toFixed(2)}`,
            })),
            ...pickups.map((p) => {
              const row = p as { id: string; order_id: string; status: string; lifecycle_stage: string }
              return {
                key: `pkp-${row.id}`,
                tipo: 'pickup',
                id: row.id,
                detalhe: `${row.status} · ${row.lifecycle_stage} · order ${row.order_id}`,
              }
            }),
            ...orderItems.map((i) => {
              const row = i as { id: string; order_id: string; sku_id: string; quantity: number }
              return {
                key: `oi-${row.id}`,
                tipo: 'item',
                id: row.sku_id,
                detalhe: `order ${row.order_id} · qty ${row.quantity}`,
              }
            }),
          ]
        : tab === 'credits'
          ? credits.map((c) => {
              const row = c as { id: string; order_id: string; amount_cents: number; status: string; type: string }
              return {
                key: `crd-${row.id}`,
                tipo: 'credit',
                id: row.id,
                detalhe: `${row.type} · ${row.status} · R$ ${(row.amount_cents / 100).toFixed(2)} · order ${row.order_id}`,
              }
            })
          : [
              ...outbox.map((x) => {
                const row = x as { id: string; event_type: string; status: string; order_id: string }
                return {
                  key: `pob-${row.id}`,
                  tipo: 'partner_outbox',
                  id: row.id,
                  detalhe: `${row.event_type} · ${row.status} · ${row.order_id}`,
                  replay: () => onReplayPartner(row.id),
                }
              }),
              ...domainOutbox.map((x) => {
                const row = x as { id: string; event_name?: string; status: string; aggregate_id?: string }
                return {
                  key: `dob-${row.id}`,
                  tipo: 'domain_outbox',
                  id: row.id,
                  detalhe: `${row.event_name ?? '—'} · ${row.status} · ${row.aggregate_id ?? '—'}`,
                  replay: () => onReplayDomain(row.id),
                }
              }),
              ...pickupEvents.map((x) => {
                const row = x as { id: string; pickup_id: string; event_type: string }
                return { key: `pe-${row.id}`, tipo: 'pickup_event', id: row.id, detalhe: `${row.event_type} · ${row.pickup_id}` }
              }),
              ...pickupTokens.map((x) => {
                const row = x as { id: string; order_id: string; is_active: boolean }
                return {
                  key: `pt-${row.id}`,
                  tipo: 'token',
                  id: row.id,
                  detalhe: `order ${row.order_id} · ${row.is_active ? 'ativo' : 'inativo'}`,
                }
              }),
              ...pickupAttempts.map((x) => {
                const row = x as { id: string; order_id: string; ok: boolean }
                return {
                  key: `pa-${row.id}`,
                  tipo: 'attempt',
                  id: row.id,
                  detalhe: `order ${row.order_id} · ${row.ok ? 'ok' : 'fail'}`,
                }
              }),
              ...fulfillment.map((x) => {
                const row = x as { id: string; order_id: string; status: string }
                return { key: `ft-${row.id}`, tipo: 'fulfillment', id: row.order_id, detalhe: row.status }
              }),
            ]

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap justify-end gap-2 text-sm">
        <Link to="/ops/tenants/admin" className="text-indigo-600 hover:underline">
          Tenants
        </Link>
        <Link to="/ops/partners/admin" className="text-indigo-600 hover:underline">
          Parceiros
        </Link>
        <Link to="/ops/payment-gateway/admin" className="text-indigo-600 hover:underline">
          Payment Gateway
        </Link>
      </div>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-slate-100">OPS · Order Pickup</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            Parceiros, pedidos, pickups, créditos, itens, eventos, tokens, outbox parceiro/domain e fulfillment.
          </p>
        </div>
        <div className="flex gap-2">
          <button type="button" onClick={() => void onSeed()} className="ellan-btn-outline">
            Seed
          </button>
          <button
            type="button"
            onClick={() => void load()}
            className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            {loading ? 'Atualizando…' : 'Listar'}
          </button>
        </div>
      </div>

      {loading && <p className="text-sm text-gray-500">Processando…</p>}
      {message && <p className="text-sm text-emerald-600">{message}</p>}
      {error && <p className="rounded border border-red-300 bg-red-50 p-2 text-sm text-red-700">{error}</p>}
      {lastApiKey && (
        <p className="rounded border border-amber-300 bg-amber-50 p-2 font-mono text-xs text-amber-900">
          API key: {lastApiKey}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        {(
          [
            ['partners', 'Parceiros'],
            ['orders', 'Pedidos'],
            ['credits', 'Créditos'],
            ['integration', 'Integração'],
          ] as const
        ).map(([t, label]) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm ${tab === t ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === 'partners' && (
        <section className="space-y-4 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPartnerSubTab('ecommerce')}
              className={`rounded px-3 py-1 text-sm ${partnerSubTab === 'ecommerce' ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
            >
              E-commerce
            </button>
            <button
              type="button"
              onClick={() => setPartnerSubTab('logistics')}
              className={`rounded px-3 py-1 text-sm ${partnerSubTab === 'logistics' ? 'bg-indigo-600 text-white' : 'border border-slate-600 bg-slate-800 text-slate-200 hover:bg-slate-700'}`}
            >
              Logística
            </button>
          </div>
          <form onSubmit={onCreatePartner} className="grid gap-3 md:grid-cols-3">
            <input
              className="ellan-field"
              placeholder="Nome"
              required
              value={partnerForm.name}
              onChange={(e) => setPartnerForm((f) => ({ ...f, name: e.target.value }))}
            />
            <input
              className="ellan-field"
              placeholder="Código"
              required
              value={partnerForm.code}
              onChange={(e) => setPartnerForm((f) => ({ ...f, code: e.target.value }))}
            />
            <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
              Criar {partnerSubTab === 'ecommerce' ? 'e-commerce' : 'logística'}
            </button>
          </form>
          <div className="flex flex-wrap gap-2">
            <select
              className="ellan-field"
              value={partnerType}
              onChange={(e) => setPartnerType(e.target.value)}
            >
              <option value="ECOMMERCE">ECOMMERCE</option>
              <option value="LOGISTICS">LOGISTICS</option>
            </select>
            <select
              className="ellan-field"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
            >
              <option value="">Parceiro</option>
              {partnerItems.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.code}
                </option>
              ))}
            </select>
            <input
              className="min-w-[14rem] flex-1 ellan-field"
              placeholder="Webhook URL"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
            />
            <button type="button" onClick={() => void onWebhook()} className="rounded bg-slate-700 px-3 py-1 text-sm text-white">
              Salvar webhook
            </button>
            <button type="button" onClick={() => void onRotateKey()} className="rounded bg-amber-600 px-3 py-1 text-sm text-white">
              Rotacionar API key
            </button>
          </div>
        </section>
      )}

      {tab === 'orders' && (
        <form onSubmit={onCreateOrder} className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input
            type="number"
            className="w-32 ellan-field"
            value={orderForm.amount_cents}
            onChange={(e) => setOrderForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
          />
          <input
            className="ellan-field"
            placeholder="ecommerce_partner_id"
            value={orderForm.ecommerce_partner_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, ecommerce_partner_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="totem_id"
            value={orderForm.totem_id}
            onChange={(e) => setOrderForm((f) => ({ ...f, totem_id: e.target.value }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar pedido
          </button>
        </form>
      )}

      {tab === 'credits' && (
        <form onSubmit={onCreateCredit} className="flex flex-wrap gap-2 rounded-xl border border-slate-600/70 bg-slate-900/90 p-4 dark:border-slate-700 dark:bg-slate-900">
          <input
            className="ellan-field"
            placeholder="order_id"
            value={creditForm.order_id}
            onChange={(e) => setCreditForm((f) => ({ ...f, order_id: e.target.value }))}
          />
          <input
            className="ellan-field"
            placeholder="user_id"
            value={creditForm.user_id}
            onChange={(e) => setCreditForm((f) => ({ ...f, user_id: e.target.value }))}
          />
          <input
            type="number"
            className="w-28 ellan-field"
            value={creditForm.amount_cents}
            onChange={(e) => setCreditForm((f) => ({ ...f, amount_cents: Number(e.target.value) }))}
          />
          <button type="submit" className="rounded bg-emerald-600 px-4 py-2 text-sm text-white">
            Criar crédito
          </button>
        </form>
      )}

      {tableRows.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-slate-600/70 bg-slate-900/90 dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs uppercase dark:bg-slate-800">
              <tr>
                <th className="px-3 py-2">tipo</th>
                <th className="px-3 py-2">id</th>
                <th className="px-3 py-2">detalhe</th>
                {tab === 'integration' ? <th className="px-3 py-2">ação</th> : null}
              </tr>
            </thead>
            <tbody>
              {tableRows.map((row) => (
                <tr key={row.key} className="border-t dark:border-slate-800">
                  <td className="px-3 py-2">{row.tipo}</td>
                  <td className="px-3 py-2 font-mono text-xs">{row.id}</td>
                  <td className="px-3 py-2">{row.detalhe}</td>
                  {tab === 'integration' ? (
                    <td className="px-3 py-2">
                      {'replay' in row && row.replay ? (
                        <button type="button" className="text-xs text-indigo-600" onClick={() => void row.replay?.()}>
                          Replay
                        </button>
                      ) : (
                        '—'
                      )}
                    </td>
                  ) : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-gray-500">Nenhum registro. Use Listar ou Seed.</p>
      )}
    </div>
  )
}
